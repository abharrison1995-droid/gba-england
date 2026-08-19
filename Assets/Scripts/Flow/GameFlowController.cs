using UnityEngine;
using GBHEngland.Data;
using GBHEngland.World;
using GBHEngland.Combat;
using GBHEngland.UI;
using GBHEngland.Quests;
using GBHEngland.Companions;
using GBHEngland.Vibe;

namespace GBHEngland.Flow
{
    public enum GameFlowState
    {
        Title,
        CharacterCreator,
        Playing
    }

    /// <summary>
    /// GBH: England bootstrap: Title → Creator → Manor Cellars → London gates.
    /// </summary>
    public class GameFlowController : MonoBehaviour
    {
        public const string EscapeManorQuestId = "escape_manor";

        public static GameFlowController Instance { get; private set; }

        [Header("UI Roots")]
        public GameObject TitleRoot;
        public GameObject CreatorRoot;
        public GameObject HudRoot;

        [Header("World")]
        public MapChunkData ManorCellarsChunk;
        public MapChunkData LondonChunk;
        public ChunkManager ChunkManager;

        [Header("Spawn")]
        public Vector3 ManorSpawnPosition = new Vector3(0f, 0f, -8f);

        [Header("Tutorial")]
        [Tooltip("Sprite for the tutorial bandit. Assign here in the Inspector; falls back to a capsule if empty.")]
        public Sprite TutorialBanditSprite;
        [Tooltip("Prefab for the tutorial supply chest. Assign here in the Inspector; falls back to a plain box if empty.")]
        public GameObject TutorialChestPrefab;
        public PlayerClassVisualLibrary ClassVisuals;

        /// <summary>Blocks InstanceDoor briefly after exiting so spawn doesn't re-enter.</summary>
        public float InstanceDoorReadyAt { get; private set; }

        public GameFlowState State { get; private set; } = GameFlowState.Title;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        private void Start()
        {
            EnsureSession();
            EnsureQuestManager();
            ShowTitle();
        }

        private void EnsureSession()
        {
            if (PlayerSession.Instance == null)
                new GameObject("PlayerSession").AddComponent<PlayerSession>();
        }

        private void EnsureQuestManager()
        {
            if (QuestManager.Instance == null)
                new GameObject("QuestManager").AddComponent<QuestManager>();
        }

        public bool CanUseInstanceDoors => Time.unscaledTime >= InstanceDoorReadyAt;

        public void ShowTitle()
        {
            State = GameFlowState.Title;
            SetUi(title: true, creator: false, hud: false);

            // Close anything that pushed a pause before the hard reset below
            var inv = FindObjectOfType<UI.InventoryController>(true);
            if (inv != null) inv.CloseIfOpen();

            GBHEngland.Systems.PauseManager.Reset();
            SetPlayerSimulated(false);
        }

        public void ShowCreator()
        {
            State = GameFlowState.CharacterCreator;
            SetUi(title: false, creator: true, hud: false);
            SetPlayerSimulated(false);
        }

        /// <summary>
        /// Freeze the player's physics while on Title/Creator — there's no chunk under
        /// them yet, so an active Rigidbody would just fall forever.
        /// </summary>
        private void SetPlayerSimulated(bool simulated)
        {
            var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
            if (player == null) return;

            var rb = player.GetComponent<Rigidbody>();
            if (rb == null) return;

            if (simulated)
            {
                rb.isKinematic = false;
            }
            else
            {
                // Already kinematic (e.g. Title -> Creator, both calling this) — Unity
                // disallows setting velocity on a kinematic body and logs a warning for it.
                if (!rb.isKinematic)
                    rb.velocity = Vector3.zero;
                rb.isKinematic = true;
            }
        }

        public void StartNewGame(string characterName, PlayerClass playerClass)
        {
            EnsureSession();
            EnsureQuestManager();
            QuestManager.Instance.ClearAll();

            var existing = CombatController.Instance ?? FindObjectOfType<CombatController>();
            CharacterData templateData = existing != null ? existing.PlayerData : null;
            PlayerSession.Instance.BeginNewGame(characterName, playerClass, templateData);

            // A New Game in the same app session must not inherit the previous run's spellbook.
            existing?.ClearLearnedSpells();

            BindPlayerToSession(existing);

            EnterManorCellars(isTutorial: true);
        }

        /// <summary>The interact system needs a PlayerInteractor on the player — add it if the scene lacks one.</summary>
        private static void EnsurePlayerInteractor()
        {
            var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
            if (player != null && player.GetComponent<PlayerInteractor>() == null)
                player.gameObject.AddComponent<PlayerInteractor>();
        }

        /// <summary>Push the session's runtime stats onto the player object and inventory UI.</summary>
        private void BindPlayerToSession(CombatController existing)
        {
            if (existing != null && PlayerSession.Instance.RuntimeStats != null)
            {
                existing.PlayerData = PlayerSession.Instance.RuntimeStats;
                existing.CurrentHealth = PlayerSession.Instance.RuntimeStats.MaxHealth;
                existing.CurrentMana = PlayerSession.Instance.RuntimeStats.MaxManaStamina;
                var hp = existing.GetComponent<Health>();
                if (hp != null)
                {
                    hp.MaxHealth = PlayerSession.Instance.RuntimeStats.MaxHealth;
                    hp.CurrentHealth = hp.MaxHealth;
                    hp.DisplayName = PlayerSession.Instance.CharacterName;
                }

                // Clears _isDead — the player may be arriving here via the death screen
                existing.ReviveFull();

                // Explicitly subscribe CombatController to session stats events to eliminate Start() race conditions
                existing.BindSessionStats(PlayerSession.Instance);
            }

            if (existing != null)
            {
                if (ClassVisuals == null)
                    ClassVisuals = GetComponent<PlayerClassVisualLibrary>();
                if (ClassVisuals != null)
                    ClassVisuals.ApplyToPlayer(existing, PlayerSession.Instance.Class);
            }

            var inventory = FindObjectOfType<UI.InventoryController>(true);
            if (inventory != null)
                inventory.BindCharacter(PlayerSession.Instance.RuntimeStats);
        }

        /// <summary>
        /// Full restore from the save file: session, quests, then world/player. Used by the
        /// title screen's Continue button and the death screen's Load Last Game.
        /// </summary>
        public bool ContinueFromSave()
        {
            SaveData data = SaveGameManager.ReadSaveData();
            if (data == null) return false;

            EnsureSession();
            EnsureQuestManager();

            var existing = CombatController.Instance ?? FindObjectOfType<CombatController>();
            CharacterData templateData = existing != null ? existing.PlayerData : null;
            PlayerSession.Instance.RestoreFromSave(
                data.CharacterName, (PlayerClass)data.PlayerClass, data.TutorialComplete, templateData);
            QuestManager.Instance.RestoreQuests(data.Quests);
            // After RestoreQuests: the focus must be validated against the restored list, so a
            // stale or completed focus clears and the tracker falls back to the first active quest.
            QuestManager.Instance.RestoreFocusedQuest(data.FocusedQuestId);
            // Restore the hired companion, if the save has one. RestoreContract is the free path
            // (never re-charges). A null/empty id or a 0/negative health is "no companion", a no-op
            // that matches a pre-companion save. The follower spawns beside the player now and
            // rejoins across the LoadWorld below via CompanionManager's chunk poll.
            if (CompanionManager.Instance != null)
                CompanionManager.Instance.RestoreContract(data.ActiveCompanionId, data.CompanionHealth);
            PlayerSession.Instance.RestoreInventory(data.Inventory);
            PlayerSession.Instance.RestoreEquipment(data.Equipment); // null in pre-equipment saves → empty doll
            PlayerSession.Instance.RestorePounds(data.Pounds);
            // Before either route that builds the world — the EnterManorCellars branch just below
            // and the LoadWorld call further down. Every SpriteContainer reads this set in its own
            // Awake, so a chunk built first would refill every bin the player had already cleared.
            PlayerSession.Instance.RestoreLootedContainers(data.LootedContainers);
            // Any time before the map is opened is fine — it is only read on open.
            PlayerSession.Instance.RestoreVisitedChunks(data.VisitedChunks);
            PlayerSession.Instance.RestoreWikiEntries(data.UnlockedWikiEntries);
            // Must be after RestoreFromSave above, which calls BeginNewGame and zeroes TotalXP.
            // No Awake-ordering dependency of the kind RestoreLootedContainers has: XP is read on
            // demand, not consumed by anything the world builds.
            PlayerSession.Instance.RestoreTotalXP(data.TotalXP);
            // After RestoreTotalXP: both end in a stat recompute, and the perk one wants the level
            // already restored. Recomputing twice is harmless — the derivation overwrites rather
            // than accumulates — and BindPlayerToSession below still runs after both, so the load
            // path pushes the final figures onto the player.
            PlayerSession.Instance.RestorePerkIds(data.PerkIds);
            // Backfill for pre-wiki saves: chunks already visited grant their location entries
            // silently, so a veteran save opens a populated encyclopedia without a toast storm.
            foreach (string chunkName in PlayerSession.Instance.VisitedChunks)
                UI.WikiUnlock.GrantForChunk(chunkName, silent: true);
            BindPlayerToSession(existing);

            PlayerSession.Instance.SpellName = PlayerSession.SanitizeSpellName(data.SpellName);
            existing?.RestoreSpellLoadout(data.KnownSpellIds, data.EquippedSpellIds);

            // Mid-tutorial saves restart the tutorial cleanly rather than resuming half-staged
            if (!data.TutorialComplete)
            {
                EnterManorCellars(isTutorial: true);
                return true;
            }

            State = GameFlowState.Playing;
            SetUi(title: false, creator: false, hud: true);
            SetPlayerSimulated(true);
            EnsurePlayerInteractor();
            InstanceDoorReadyAt = Time.unscaledTime + 1.25f;

            if (!SaveGameManager.LoadWorld(data))
            {
                Debug.LogWarning("ContinueFromSave: saved chunk unresolvable — falling back to London gates.");
                LoadLondonAtWestGates();
                return true;
            }

            if (UIManager.Instance != null)
            {
                string label = ChunkManager != null && ChunkManager.CurrentChunkData == LondonChunk
                    ? EKVibe.CapitalCity
                    : (ChunkManager != null && ChunkManager.CurrentChunkData != null
                        ? ChunkManager.CurrentChunkData.ChunkName
                        : "England");
                UIManager.Instance.SetLocationTime(label, 1, "11 PM");
                UIManager.Instance.LogCombat("You pick up where you left off.");
            }

            var tracker = FindObjectOfType<QuestTrackerUI>();
            if (tracker != null) tracker.Refresh();
            return true;
        }

        public void EnterManorCellars()
        {
            EnterManorCellars(isTutorial: true);
        }

        /// <summary>Optional revisit from London west door (post-tutorial).</summary>
        public void EnterManorCellarsOptional()
        {
            EnterManorCellars(isTutorial: false);
        }

        private void EnterManorCellars(bool isTutorial)
        {
            State = GameFlowState.Playing;
            SetUi(title: false, creator: false, hud: true);
            SetPlayerSimulated(true);
            InstanceDoorReadyAt = Time.unscaledTime + 1.25f;

            if (ChunkManager == null)
                ChunkManager = FindObjectOfType<ChunkManager>();

            if (ChunkManager != null && ManorCellarsChunk != null && ManorCellarsChunk.ChunkPrefab != null)
            {
                if (ChunkManager.CurrentChunkInstance != null)
                    Destroy(ChunkManager.CurrentChunkInstance);

                ChunkManager.CurrentChunkData = ManorCellarsChunk;
                PlayerSession.Instance?.MarkChunkVisited(ManorCellarsChunk.ChunkName);
                // Silent: the new-game wake-up, respawns and arrests land here — none are discoveries.
                UI.WikiUnlock.GrantForChunk(ManorCellarsChunk.ChunkName, silent: true);
                ChunkManager.CurrentChunkInstance = Instantiate(
                    ManorCellarsChunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
                ChunkManager.CurrentChunkInstance.name = ManorCellarsChunk.ChunkPrefab.name;

                var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
                if (player != null)
                {
                    ChunkManager.PlayerTransform = player.transform;
                    // Arrive at the Manor Cellars' PlayerSpawnPoint if it has one, else ManorSpawnPosition.
                    ChunkManager.TeleportPlayer(
                        PlayerSpawnPoint.ResolveWorldPosition(ChunkManager.CurrentChunkInstance, ManorSpawnPosition));
                }
            }

            EnsurePlayerInteractor();

            EnsureQuestManager();
            if (isTutorial)
            {
                QuestManager.Instance.StartQuest(
                    EscapeManorQuestId,
                    "Escape the Cellars",
                    "Find the manor gate and get out.",
                    giver: "",
                    location: "Manor Cellars");

                // Staged tutorial lives on the chunk instance so it resets cleanly on respawn
                var seqGo = new GameObject("TutorialSequence");
                if (ChunkManager != null && ChunkManager.CurrentChunkInstance != null)
                    seqGo.transform.SetParent(ChunkManager.CurrentChunkInstance.transform, false);
                seqGo.AddComponent<TutorialSequence>().Begin(TutorialBanditSprite, TutorialChestPrefab);
            }

            if (UIManager.Instance != null)
            {
                UIManager.Instance.SetLocationTime("Manor Cellars", 1, "11 PM");
                UIManager.Instance.LogCombat(isTutorial
                    ? "You wake in the Manor Cellars. Find a way out."
                    : "Back in the Manor Cellars. Watch the corners.");
            }

            var tracker = FindObjectOfType<QuestTrackerUI>();
            if (tracker != null) tracker.Refresh();

            // Checkpoint so Continue exists from the very start of a run
            SaveGameManager.Save();
        }

        /// <summary>
        /// Player hit 0 HP. Check if the killing blow came from law enforcement —
        /// if so, arrest them instead of killing them.
        /// </summary>
        public void HandlePlayerDeath()
        {
            // A mounted vehicle is unparented from the chunk, so it survives the
            // transition that follows. Dismounting here drops it in the current chunk
            // (where it dies with the chunk) and restores the player's speed and visuals
            // before the respawn.
            World.MountController.Current?.Dismount();

            // ── Check for arrest ──
            var player = CombatController.Instance;
            if (player != null)
            {
                var playerHealth = player.GetComponent<Health>();
                if (playerHealth != null && playerHealth.LastAttacker != null)
                {
                    var enemyAI = playerHealth.LastAttacker.GetComponent<EnemyAI>();
                    if (enemyAI != null && enemyAI.IsPolice)
                    {
                        StartCoroutine(ArrestRoutine());
                        return;
                    }
                }
            }

            // ── Normal death flow ──
            bool tutorialDone = PlayerSession.Instance != null && PlayerSession.Instance.TutorialComplete;

            // Post-tutorial, Manor Cellars is no longer "home" — use the real death screen
            // (Load Last Game / New Game / Quit) instead of auto-respawning there forever.
            if (tutorialDone && UI.DeathScreenUI.Instance != null)
            {
                UI.DeathScreenUI.Instance.Show();
                return;
            }

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("You collapse...");
            StartCoroutine(RespawnRoutine(2f));
        }

        /// <summary>
        /// "You've been nicked, mate." — arrest flow instead of death.
        /// Teleport to Manor Cellars, clear wanted level, deduct a fine, revive.
        /// </summary>
        private System.Collections.IEnumerator ArrestRoutine()
        {
            if (UIManager.Instance != null)
            {
                UIManager.Instance.ShowToast("Busted! You've been nicked, mate.", 3f);
                UIManager.Instance.LogCombat("The police wrestle you to the ground...");
            }

            yield return new WaitForSeconds(2.5f);

            var player = CombatController.Instance;
            if (player == null) yield break;

            player.ReviveFull();

            // Clear wanted level and concealment
            if (Systems.WantedManager.Instance != null)
            {
                Systems.WantedManager.Instance.CurrentKnives = 0;
                Systems.WantedManager.Instance.CurrentConcealment = Systems.WantedManager.Instance.MaxConcealment;
                if (UIManager.Instance != null)
                {
                    UIManager.Instance.UpdateKnivesUI(0);
                    UIManager.Instance.UpdatePlayerConcealment(
                        Systems.WantedManager.Instance.MaxConcealment,
                        Systems.WantedManager.Instance.MaxConcealment);
                }
            }

            // Despawn all police from the scene so they don't re-arrest you immediately
            foreach (var enemy in FindObjectsOfType<EnemyAI>())
            {
                if (enemy != null && enemy.IsPolice)
                    Destroy(enemy.gameObject);
            }

            // Teleport to Manor Cellars (the holding cell, basically)
            bool tutorialDone = PlayerSession.Instance != null && PlayerSession.Instance.TutorialComplete;
            EnterManorCellars(isTutorial: !tutorialDone);

            // A fine takes what is in the wallet, not what the player owes: SpendPounds is
            // all-or-nothing, so it is clamped first rather than quietly refusing to fine a
            // skint player. The message reports what was actually taken.
            int fine = 0;
            if (PlayerSession.Instance != null)
            {
                fine = Mathf.Min(EKVibe.ArrestFine, PlayerSession.Instance.Pounds);
                PlayerSession.Instance.SpendPounds(fine);
            }

            if (UIManager.Instance != null)
            {
                UIManager.Instance.LogCombat(fine > 0
                    ? $"Released from custody. Fined {EKVibe.FormatPounds(fine)}."
                    : "Released from custody. Nothing on you worth fining.");
                UIManager.Instance.ShowToast("Released from custody. Don't let it happen again.", 3f);
            }
        }

        private System.Collections.IEnumerator RespawnRoutine(float delay)
        {
            yield return new WaitForSeconds(delay);

            var player = CombatController.Instance;
            if (player == null) yield break;

            player.ReviveFull();

            bool tutorialDone = PlayerSession.Instance != null && PlayerSession.Instance.TutorialComplete;
            EnterManorCellars(isTutorial: !tutorialDone);

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("You wake in the Manor Cellars, sore but alive.");
        }

        /// <summary>Exit Manor Cellars to London's west gates (tutorial or revisit).</summary>
        public void OnTutorialExitToGates()
        {
            EnsureQuestManager();
            if (!QuestManager.Instance.IsComplete(EscapeManorQuestId))
                QuestManager.Instance.CompleteQuest(EscapeManorQuestId);

            if (PlayerSession.Instance != null && !PlayerSession.Instance.TutorialComplete)
                PlayerSession.Instance.CompleteTutorial();

            LoadLondonAtWestGates();
        }

        private void LoadLondonAtWestGates()
        {
            InstanceDoorReadyAt = Time.unscaledTime + 1.5f;

            if (ChunkManager == null)
                ChunkManager = FindObjectOfType<ChunkManager>();

            if (ChunkManager == null || LondonChunk == null || LondonChunk.ChunkPrefab == null)
            {
                Debug.LogWarning("London chunk not wired — tutorial marked complete anyway.");
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat("You step out through the manor gates.");
                return;
            }

            if (ChunkManager.CurrentChunkInstance != null)
                Destroy(ChunkManager.CurrentChunkInstance);

            ChunkManager.CurrentChunkData = LondonChunk;
            PlayerSession.Instance?.MarkChunkVisited(LondonChunk.ChunkName);
            // Toast: stepping out of the manor gates into London for the first time IS a discovery.
            UI.WikiUnlock.GrantForChunk(LondonChunk.ChunkName, silent: false);
            ChunkManager.CurrentChunkInstance = Instantiate(LondonChunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
            ChunkManager.CurrentChunkInstance.name = LondonChunk.ChunkPrefab.name;

            // Bake a NavMesh at runtime so enemies path around London's buildings/props.
            if (ChunkManager.CurrentChunkInstance.GetComponent<RuntimeNavMeshBaker>() == null)
                ChunkManager.CurrentChunkInstance.AddComponent<RuntimeNavMeshBaker>();

            float half = EKVibe.ChunkSize * 0.5f;
            // Arrive at the London chunk's PlayerSpawnPoint (placeable in the prefab); falls back
            // east of the manor door if the chunk has no spawn point.
            Vector3 fallback = new Vector3(-half + 14f, 0f, 0f);
            ChunkManager.TeleportPlayer(
                PlayerSpawnPoint.ResolveWorldPosition(ChunkManager.CurrentChunkInstance, fallback));

            EnsureManorEntranceOnCurrentLondon();

            if (UIManager.Instance != null)
            {
                UIManager.Instance.SetLocationTime("London", 1, "11 PM");
                UIManager.Instance.LogCombat("Outside the Manor Cellars gates. London lies ahead.");
            }

            var tracker = FindObjectOfType<QuestTrackerUI>();
            if (tracker != null) tracker.Refresh();

            // The first magic quest used to be spawned here, by a MagicTutorial component parented
            // to the chunk. It is now spark_of_talent, authored in quests/spark_of_talent.quest and
            // driven by QuestConditionWatcher like every other quest — Daniel Pauls and the geezer
            // are placed content in Home_London_Prefab, so nothing needs kicking off.
            //
            // Removing this fixed a real defect as a side effect: the old component was created
            // only on this one code path and died with the chunk, so loading a save directly into
            // London produced no Daniel Pauls and no geezer at all.

            // Checkpoint: tutorial completion must survive an app restart
            SaveGameManager.Save();
        }


        /// <summary>Places / refreshes the west-path door back into Manor Cellars.</summary>
        public void EnsureManorEntranceOnCurrentLondon()
        {
            if (ChunkManager == null || ChunkManager.CurrentChunkInstance == null) return;

            var existing = ChunkManager.CurrentChunkInstance.GetComponentInChildren<InstanceDoor>();
            if (existing != null) return;

            float half = EKVibe.ChunkSize * 0.5f;
            GameObject door = new GameObject("ManorCellarsEntrance");
            door.transform.SetParent(ChunkManager.CurrentChunkInstance.transform, false);
            door.transform.localPosition = new Vector3(-half + 4f, 1.2f, 0f);

            var box = door.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.size = new Vector3(3.5f, 3f, 4f);

            var inst = door.AddComponent<InstanceDoor>();
            inst.Target = InstanceDoor.Destination.ManorCellars;
            inst.Prompt = "Enter Manor Cellars";
            inst.RequireTutorialComplete = true;

            GameObject visual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            visual.name = "DoorVisual";
            visual.transform.SetParent(door.transform, false);
            visual.transform.localPosition = Vector3.zero;
            visual.transform.localScale = new Vector3(0.5f, 2.6f, 3.2f);
            Object.Destroy(visual.GetComponent<Collider>());
            var r = visual.GetComponent<Renderer>();
            r.sharedMaterial = GetDoorMaterial();
        }

        private static Material _doorMaterial;

        private static Material GetDoorMaterial()
        {
            if (_doorMaterial == null)
            {
                Shader sh = Shader.Find("Unlit/Color")
                            ?? Shader.Find("Sprites/Default")
                            ?? Shader.Find("Standard");
                _doorMaterial = new Material(sh) { color = new Color(0.35f, 0.22f, 0.12f) };
            }
            return _doorMaterial;
        }

        private void SetUi(bool title, bool creator, bool hud)
        {
            if (TitleRoot != null) TitleRoot.SetActive(title);
            else
            {
                var t = GameObject.Find("TitleScreen");
                if (t != null) t.SetActive(title);
            }

            if (CreatorRoot != null) CreatorRoot.SetActive(creator);
            else
            {
                var c = GameObject.Find("CharacterCreator");
                if (c != null) c.SetActive(creator);
            }

            if (HudRoot != null) HudRoot.SetActive(hud);
        }
    }
}
