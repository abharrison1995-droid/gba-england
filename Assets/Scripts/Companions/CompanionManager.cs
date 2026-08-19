using UnityEngine;
using GBHEngland.AI;
using GBHEngland.Combat;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.World;

namespace GBHEngland.Companions
{
    /// <summary>
    /// Owns the single active companion contract: which companion is hired, the scene-root follower
    /// instance, and its rejoin discipline across every chunk transition.
    ///
    /// The active companion is a SCENE-ROOT object, never parented under the chunk root - every
    /// transition destroys that root (seven paths across the codebase; see CLAUDE.md). Repositioning
    /// only happens once the destination chunk AND the player's arrival are valid, which is why the
    /// chunk is POLLED (reference compare) rather than hooked: CurrentChunkData/Instance are written
    /// from many places and a single event would miss most of them. Same pattern as
    /// QuestConditionWatcher and VehicleSpawner.
    ///
    /// Bootstrap is automatic (RuntimeInitializeOnLoadMethod), so nothing needs placing in the scene.
    /// </summary>
    public class CompanionManager : MonoBehaviour
    {
        public static CompanionManager Instance { get; private set; }

        /// <summary>The id of the active companion, or null/empty when nobody is hired.</summary>
        public string CurrentCompanionId { get; private set; }

        /// <summary>True while a companion is hired and following.</summary>
        public bool HasActiveCompanion => !string.IsNullOrEmpty(CurrentCompanionId);

        public CompanionDefinition ActiveDefinition { get; private set; }
        public GameObject Follower { get; private set; }
        public CompanionAI FollowerAI { get; private set; }

        /// <summary>
        /// Fired whenever a contract begins or fully ends (despawn included). CompanionHomePresence
        /// listens so the home figure hides the moment the hire lands and reappears when the
        /// contract is over, instead of only re-checking when its chunk reloads.
        /// </summary>
        public event System.Action ContractChanged;

        // Follower lifetime bookkeeping.
        private float _knockoutDespawnAt = -1f;

        // Rejoin state: the chunk pair we last rejoined against, so we do not re-warp every frame.
        private MapChunkData _joinedChunkData;
        private GameObject _joinedChunkInstance;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (Instance != null) return;
            var go = new GameObject("~CompanionManager");
            DontDestroyOnLoad(go);
            go.AddComponent<CompanionManager>();
        }

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        private void Update()
        {
            PollChunkRejoin();
            PollKnockoutDespawn();
        }

        // ----- contract API (C7: also used by quest-bound logic and dialogue) -----

        /// <summary>
        /// Starts a contract for <paramref name="companionId"/>. <paramref name="free"/> skips the
        /// pound charge - used by a restored save (never re-charge) and by machinery that joins a
        /// companion via quest state. A Paid hire that cannot afford the price is refused here and
        /// returns false WITHOUT changing state; the caller (the hire interaction) decides whether to
        /// surface that as a message.
        /// </summary>
        public bool BeginContract(string companionId, bool free = false)
        {
            if (string.IsNullOrEmpty(companionId)) return false;
            if (HasActiveCompanion) return false; // one at a time

            CompanionDefinition def = CompanionDatabase.Find(companionId);
            if (def == null)
            {
                Debug.LogError($"CompanionManager: no CompanionDefinition for id '{companionId}' under Resources/Companions.");
                return false;
            }

            if (!free && def.ContractType == CompanionContractType.Paid)
            {
                PlayerSession session = PlayerSession.Instance;
                if (session == null || !session.SpendPounds(def.PricePounds))
                    return false; // insufficient funds - nothing changed
            }

            CurrentCompanionId = def.Id;
            ActiveDefinition = def;
            SpawnFollower();
            _joinedChunkData = null; // force a rejoin next poll
            _joinedChunkInstance = null;
            ContractChanged?.Invoke();
            return true;
        }

        /// <summary>
        /// Ends the contract. <paramref name="knockedOut"/> controls the follower's send-off: a
        /// knockout leaves the Death pose in place and lets PollKnockoutDespawn finish the teardown a
        /// beat later; a dismissal (false) despawns immediately and cleanly.
        /// </summary>
        public void EndContract(bool knockedOut = false)
        {
            if (knockedOut && Follower != null)
            {
                // The KO pose plays via CompanionAI.OnCompanionDied; despawn it a moment later.
                _knockoutDespawnAt = Time.time + 2.2f;
                return;
            }

            DespawnFollower();
            ClearContract();
        }

        /// <summary>Frees the contract state entirely (after despawn).</summary>
        private void ClearContract()
        {
            CurrentCompanionId = null;
            ActiveDefinition = null;
            Follower = null;
            FollowerAI = null;
            _joinedChunkData = null;
            _joinedChunkInstance = null;
            ContractChanged?.Invoke();
        }

        // ----- spawn / despawn -----

        /// <summary>
        /// Spawns the follower at scene root, built from the companion's PlacementPreset (which holds
        /// the Alex art C4's authoring wrote into it). Reuses NpcFactory.Build so the visual/animator
        /// recipe is identical to every other animated character.
        /// </summary>
        private void SpawnFollower()
        {
            if (ActiveDefinition == null) return;
            if (Follower != null) return;

            PlacementPreset preset = ResolveCompanionPreset(ActiveDefinition);
            GameObject root = preset != null
                ? NpcFactory.Build(preset, Vector3.zero, null) // scene-root, no parent
                : BuildFallbackFollower();
            if (root == null)
            {
                Debug.LogError($"CompanionManager: could not build the follower for '{ActiveDefinition.Id}' (no preset or art for it).");
                ClearContract();
                return;
            }

            // The follower is NOT an NPC - strip the NPC dialogue/pickpocket/wander NpcFactory adds,
            // but KEEP the Interactable so the player can talk to the follower (combat commands,
            // dismiss). LowPriority so a follower hovering at your shoulder never shadows a chest,
            // door or NPC you walk up to.
            RemoveComponent<NPCDialogueInteractable>(root);
            RemoveComponent<PickpocketInteractable>(root);
            RemoveComponent<NPCWander>(root);

            var interactable = root.GetComponent<Interactable>();
            if (interactable != null)
            {
                interactable.Prompt = "Talk to " + (ActiveDefinition != null ? ActiveDefinition.DisplayName : "Companion");
                interactable.LowPriority = true;
                interactable.Reusable = true;
            }

            // The follower conversation (Back me / Chill / Dismiss / Nevermind), authored on the
            // preset. Separate from the recruit dialogue the home presence uses.
            if (preset != null && preset.FollowerConversation != null)
            {
                var followerDialogue = root.AddComponent<CompanionFollowerDialogue>();
                followerDialogue.Conversation = preset.FollowerConversation;
            }

            // Turn the visual shell into a follower.
            root.AddComponent<Health>();
            UnityEngine.AI.NavMeshAgent agent = root.AddComponent<UnityEngine.AI.NavMeshAgent>();
            CompanionAI ai = root.AddComponent<CompanionAI>();
            ai.Definition = ActiveDefinition;
            ai.KnockedOut += OnFollowerKnockedOut;
            ai.HealthChanged += OnFollowerHealthChanged;
            Follower = root;
            FollowerAI = ai;

            // Position beside the player once they exist.
            var player = CombatController.Instance;
            if (player != null)
            {
                Vector3 targetPos = player.transform.position + Vector3.back * 2.0f;
                if (UnityEngine.AI.NavMesh.SamplePosition(targetPos, out UnityEngine.AI.NavMeshHit hit, 4.0f, UnityEngine.AI.NavMesh.AllAreas))
                    targetPos = hit.position;
                root.transform.position = targetPos;
            }
            agent.Warp(root.transform.position);
        }

        /// <summary>
        /// A definition with no preset/art yet still needs a visible follower to test with - a plain
        /// capsule with the definition's display name. The real Alex preset replaces this once C4
        /// authoring runs. Falls back when ResolveCompanionPreset returns null.
        /// </summary>
        private GameObject BuildFallbackFollower()
        {
            string name = ActiveDefinition != null && !string.IsNullOrEmpty(ActiveDefinition.DisplayName)
                ? ActiveDefinition.DisplayName
                : "Companion";
            var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            go.name = name;
            go.transform.localScale = new Vector3(0.8f, 1.6f, 0.8f);
            return go;
        }

        private void DespawnFollower()
        {
            if (Follower != null)
            {
                if (FollowerAI != null) FollowerAI.KnockedOut -= OnFollowerKnockedOut;
                if (FollowerAI != null) FollowerAI.HealthChanged -= OnFollowerHealthChanged;
                UnityEngine.Object.Destroy(Follower);
            }
        }

        private static void RemoveComponent<T>(GameObject go) where T : Component
        {
            var c = go.GetComponent<T>();
            if (c != null) UnityEngine.Object.Destroy(c);
        }

        private void OnFollowerKnockedOut()
        {
            // The pose is owned by CompanionAI; PollKnockoutDespawn finishes the teardown so the KO
            // pose stays on screen a beat.
            _knockoutDespawnAt = Time.time + 2.2f;
        }

        private void OnFollowerHealthChanged(Health health)
        {
            // HUD lives on UIManager; push a badge update when the follower health moves.
            if (Instance == this) UI.CompanionHUD.Refresh(this);
        }

        private void PollKnockoutDespawn()
        {
            if (_knockoutDespawnAt <= 0f) return;
            if (Time.time < _knockoutDespawnAt) return;
            _knockoutDespawnAt = -1f;
            DespawnFollower();
            ClearContract();
        }

        // ----- chunk rejoin -----

        /// <summary>
        /// Rejoins the active companion beside the player after every chunk replacement. Polled each
        /// frame; the guard against the current chunk pair is what keeps this from becoming a warp
        /// every frame. Refuses to warp until both the destination instance and the player exist.
        /// </summary>
        private void PollChunkRejoin()
        {
            if (Follower == null) return;

            ChunkManager chunks = ChunkManager.Instance;
            MapChunkData data = chunks != null ? chunks.CurrentChunkData : null;
            GameObject instance = chunks != null ? chunks.CurrentChunkInstance : null;
            CombatController player = CombatController.Instance;
            if (data == null || instance == null || player == null) return;

            if (data == _joinedChunkData && instance == _joinedChunkInstance) return;

            _joinedChunkData = data;
            _joinedChunkInstance = instance;

            Vector3 pos = player.transform.position + Vector3.back * 2.0f;
            if (UnityEngine.AI.NavMesh.SamplePosition(pos, out UnityEngine.AI.NavMeshHit hit, 4.0f, UnityEngine.AI.NavMesh.AllAreas))
                pos = hit.position;
            Follower.transform.position = pos;
            var agent = Follower.GetComponent<UnityEngine.AI.NavMeshAgent>();
            if (agent != null) agent.Warp(pos);
        }

        // ----- preset resolution -----

        /// <summary>
        /// Finds the PlacementPreset that carries the companion's ArtSubject - the same preset the
        /// World Palette uses to author the home presence, so the follower and the home look alike.
        /// </summary>
        private static PlacementPreset ResolveCompanionPreset(CompanionDefinition def)
        {
            if (def == null || string.IsNullOrEmpty(def.ArtSubject)) return null;
            string needle = def.ArtSubject.Trim().ToLowerInvariant();

            var library = PlacementPresetLibrary.Instance;
            if (library != null)
            {
                foreach (var entry in library.Entries)
                {
                    if (entry == null || entry.Preset == null) continue;
                    if (entry.Preset.ArtSubject != null &&
                        entry.Preset.ArtSubject.Trim().ToLowerInvariant() == needle)
                        return entry.Preset;
                }
            }

            // Fallback: scan presets already loaded that carry the subject.
            foreach (PlacementPreset preset in Resources.FindObjectsOfTypeAll<PlacementPreset>())
            {
                if (preset == null) continue;
                if (preset.ArtSubject != null &&
                    preset.ArtSubject.Trim().ToLowerInvariant() == needle)
                    return preset;
            }
            return null;
        }

        // ----- save / restore (C5) -----

        /// <summary>Current health for the save file, or -1 when nobody is hired.</summary>
        public int CurrentFollowerHealth()
        {
            if (FollowerAI == null || FollowerAI.FollowerHealth == null) return -1;
            return FollowerAI.FollowerHealth.CurrentHealth;
        }

        /// <summary>
        /// Restore a saved contract after ContinueFromSave. Never charges. Spawn happens once the
        /// chunk + player are valid - the per-frame rejoin poll handles the timing, so this is safe
        /// to call the moment the session/player exists.
        /// </summary>
        public void RestoreContract(string companionId, int health)
        {
            if (string.IsNullOrEmpty(companionId)) return;
            if (HasActiveCompanion) return;

            CompanionDefinition def = CompanionDatabase.Find(companionId);
            if (def == null)
            {
                Debug.LogWarning($"CompanionManager: saved companion '{companionId}' has no definition - ignoring the saved contract.");
                return;
            }

            CurrentCompanionId = def.Id;
            ActiveDefinition = def;
            SpawnFollower();
            if (FollowerAI != null && FollowerAI.FollowerHealth != null && health > 0)
            {
                int max = Mathf.Max(1, def.MaxHealth);
                FollowerAI.FollowerHealth.CurrentHealth = Mathf.Clamp(health, 1, max);
            }
            _joinedChunkData = null;
            _joinedChunkInstance = null;
            ContractChanged?.Invoke(); // a restored contract hides the home presence too
        }

    }
}
