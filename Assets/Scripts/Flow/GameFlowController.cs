using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;
using ExiledAlvaston.Combat;
using ExiledAlvaston.UI;
using ExiledAlvaston.Quests;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.Flow
{
    public enum GameFlowState
    {
        Title,
        CharacterCreator,
        Playing
    }

    /// <summary>
    /// Discover England bootstrap: Title → Creator → Manor Cellars → London gates.
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
        [Tooltip("Sprite for the tutorial bandit. Wire via Tools/Discover England/Wire Tutorial Bandit Sprite; falls back to a capsule if empty.")]
        public Sprite TutorialBanditSprite;
        [Tooltip("Prefab for the tutorial supply chest. Wire via Tools/Discover England/Wire Tutorial Chest Prefab; falls back to a plain box if empty.")]
        public GameObject TutorialChestPrefab;

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

            ExiledAlvaston.Systems.PauseManager.Reset();
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
            PlayerSession.Instance.RestoreInventory(data.Inventory);
            BindPlayerToSession(existing);

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

            if (UIManager.Instance != null)
            {
                UIManager.Instance.LogCombat("Released from custody. Fined 50 quid.");
                UIManager.Instance.ShowToast("Released from custody. Don't let it happen again.", 3f);
            }

            // TODO: Deduct gold from player inventory once raw gold tracking is in
            // PlayerSession.Instance.Inventory.RemoveGold(50);
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

            // Kick off the first magic quest (Daniel Pauls) in London. Parented to the chunk so it
            // dies with it; resumes from quest state on re-entry.
            if (MagicTutorial.Instance == null && ChunkManager.CurrentChunkInstance != null)
            {
                var magicGo = new GameObject("MagicTutorial");
                magicGo.transform.SetParent(ChunkManager.CurrentChunkInstance.transform, false);
                magicGo.AddComponent<MagicTutorial>().Begin(TutorialBanditSprite);
            }

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
