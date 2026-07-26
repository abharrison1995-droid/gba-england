using UnityEngine;
using UnityEngine.AI;
using System.Collections;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Quests;
using ExiledAlvaston.UI;
using ExiledAlvaston.Vibe;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Flow
{
    /// <summary>
    /// Staged Manor Cellars tutorial: move → kill the bandit → loot the chest → reach the gate.
    /// Spawned at runtime by GameFlowController, parented to the chunk instance so it dies
    /// with the chunk (respawn/death re-creates a fresh sequence).
    /// </summary>
    public class TutorialSequence : MonoBehaviour
    {
        public static TutorialSequence Instance { get; private set; }

        public enum Stage
        {
            Move,
            Kill,
            Loot,
            Exit
        }

        public Stage CurrentStage { get; private set; } = Stage.Move;
        public bool ReadyToExit => CurrentStage == Stage.Exit;

        private const float MoveDistanceRequired = 4f;

        private Sprite _banditSprite;
        private GameObject _chestPrefab;
        private float _movedDistance;
        private Vector3 _lastPlayerPos;
        private bool _hasLastPos;
        private Health _banditHealth;
        private float _nextGateNudgeAt;

        private void Awake()
        {
            Instance = this;
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
            if (_banditHealth != null)
                _banditHealth.OnDeath.RemoveListener(OnBanditKilled);
        }

        public void Begin(Sprite banditSprite, GameObject chestPrefab = null)
        {
            _banditSprite = banditSprite;
            _chestPrefab = chestPrefab;
            SetObjective("Get your bearings — use the stick to move around the cellar.");
        }

        private void Update()
        {
            if (CurrentStage != Stage.Move) return;

            var player = CombatController.Instance;
            if (player == null || player.IsDead) return;

            Vector3 pos = player.transform.position;
            if (_hasLastPos)
            {
                Vector3 delta = pos - _lastPlayerPos;
                delta.y = 0f;
                // Cap per-frame distance so teleports don't count as walking
                _movedDistance += Mathf.Min(delta.magnitude, 1f);
            }
            _lastPlayerPos = pos;
            _hasLastPos = true;

            if (_movedDistance >= MoveDistanceRequired)
                AdvanceToKill();
        }

        /// <summary>Called by TutorialExitGate while the gate is still barred.</summary>
        public void NudgeLockedGate()
        {
            if (Time.unscaledTime < _nextGateNudgeAt) return;
            _nextGateNudgeAt = Time.unscaledTime + 3f;

            if (UIManager.Instance == null) return;
            switch (CurrentStage)
            {
                case Stage.Move:
                    UIManager.Instance.LogCombat("The gate is barred. Get your bearings first.");
                    break;
                case Stage.Kill:
                    UIManager.Instance.LogCombat("The gate is barred. Deal with the bandit first.");
                    break;
                case Stage.Loot:
                    UIManager.Instance.LogCombat("The gate is barred. Search the supply chest first.");
                    break;
            }
        }

        private void AdvanceToKill()
        {
            CurrentStage = Stage.Kill;
            SpawnBandit();
            SetObjective("A bandit lurks in the hall — kill him. Tap ATK when close.");
            Log("Something stirs in the dark ahead...");
        }

        private void OnBanditKilled()
        {
            if (CurrentStage != Stage.Kill) return;
            CurrentStage = Stage.Loot;
            SpawnChest();
            SetObjective("Search the supply chest in the east corridor.");
            Log("The bandit drops. A chest sits in the corridor east.");
        }

        /// <summary>Called by the spawned TutorialChest once the loot menu closes after the loot was taken.</summary>
        public void OnChestLooted()
        {
            if (CurrentStage != Stage.Loot) return;
            CurrentStage = Stage.Exit;

            SetObjective("Find the manor gate and get out.");
            Log("Nothing else in the chest. The gate can't be far.");
        }

        private void SpawnBandit()
        {
            // Start hall is the 14x10 room centered at (0, -10)
            Vector3 spawnPos = new Vector3(3.5f, 0f, -12f);
            if (NavMesh.SamplePosition(spawnPos, out NavMeshHit navHit, 10f, NavMesh.AllAreas))
                spawnPos = navHit.position;

            GameObject bandit = new GameObject("TutorialBandit");
            bandit.transform.SetParent(transform, false);
            bandit.transform.position = spawnPos;

            var col = bandit.AddComponent<CapsuleCollider>();
            col.height = EKVibe.CharacterHeight;
            col.radius = 0.28f;
            col.center = new Vector3(0f, EKVibe.CharacterHeight * 0.5f, 0f);

            _banditHealth = bandit.AddComponent<Health>();
            _banditHealth.MaxHealth = 30;
            _banditHealth.CurrentHealth = 30;
            _banditHealth.DisplayName = "Cellar Bandit";
            _banditHealth.OnDeath.AddListener(OnBanditKilled);

            var agent = bandit.AddComponent<NavMeshAgent>();
            agent.height = EKVibe.CharacterHeight;
            agent.radius = 0.28f;

            // Visual must exist before EnemyAI — EnemyAI.Awake caches it via GetComponent
            var visual = bandit.AddComponent<WorldActorVisual>();
            visual.ActorSprite = _banditSprite;
            visual.Height = EKVibe.CharacterHeight;
            visual.Width = EKVibe.CharacterWidth;
            visual.ApplyVisual();

            var ai = bandit.AddComponent<EnemyAI>();
            ai.Damage = 4;
            ai.SightRadius = 14f;
            ai.AttackRange = 1.6f;
            ai.MoveSpeed = 3.2f;

            if (_banditSprite == null)
                AddFallbackCapsuleVisual(bandit.transform);

            var plate = bandit.AddComponent<EnemyNameplate>();
            plate.Level = 1;

            int enemyLayer = LayerMask.NameToLayer("Enemy");
            if (enemyLayer >= 0)
                bandit.layer = enemyLayer;
        }

        private static void AddFallbackCapsuleVisual(Transform parent)
        {
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = "FallbackBody";
            Destroy(body.GetComponent<Collider>());
            body.transform.SetParent(parent, false);
            float h = EKVibe.CharacterHeight;
            body.transform.localPosition = new Vector3(0f, h * 0.5f, 0f);
            body.transform.localScale = new Vector3(0.5f, h * 0.5f, 0.5f);

            var r = body.GetComponent<Renderer>();
            Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Standard");
            r.sharedMaterial = new Material(sh) { color = new Color(0.5f, 0.15f, 0.12f) };
        }

        private void SpawnChest()
        {
            // Chest lands on the "ChestSpawn" marker in the Manor prefab — drag that marker to
            // move/raise the chest. Falls back to the east corridor room (10x6 centered at (12,-10)).
            GameObject chunk = ChunkManager.Instance != null ? ChunkManager.Instance.CurrentChunkInstance : null;
            if (chunk == null && transform.parent != null) chunk = transform.parent.gameObject;
            Vector3 chestPos = SceneMarker.ResolveWorldPosition(chunk, "ChestSpawn", new Vector3(12f, 0f, -12f));

            GameObject chest = new GameObject("TutorialChest");
            chest.transform.SetParent(transform, false);
            chest.transform.position = chestPos;

            // Wider trigger than the visual chest so the player can walk up and press Interact
            // from a sensible distance, not just when overlapping the model's own solid collider.
            var box = chest.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.center = new Vector3(0f, 0.6f, 0f);
            box.size = new Vector3(3f, 2f, 3f);

            var tutorialChest = chest.AddComponent<TutorialChest>();

            if (_chestPrefab != null)
            {
                GameObject visual = Instantiate(_chestPrefab, chest.transform);
                visual.transform.localPosition = Vector3.zero;
                visual.transform.localRotation = Quaternion.identity;
                tutorialChest.ChestAnimation = visual.GetComponentInChildren<Animation>();
            }
            else
            {
                BuildFallbackChestVisual(chest.transform, tutorialChest);
            }

            var interactable = chest.AddComponent<Interactable>();
            interactable.Prompt = "Open Chest";
            // Stays usable until the loot is actually taken — closing the menu empty-handed
            // must not lock the player out of the tutorial. TutorialChest disables it after.
            interactable.Reusable = true;
            interactable.InteractRange = 2.75f;
            interactable.OnInteract.AddListener(tutorialChest.Open);
            tutorialChest.ChestInteractable = interactable;
        }

        /// <summary>Plain animated box+lid — used only if TutorialChestPrefab isn't wired up.</summary>
        private static void BuildFallbackChestVisual(Transform parent, TutorialChest tutorialChest)
        {
            Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Standard");
            var bodyMat = new Material(sh) { color = new Color(0.55f, 0.38f, 0.15f) };

            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.name = "ChestBody";
            Destroy(body.GetComponent<Collider>());
            body.transform.SetParent(parent, false);
            body.transform.localPosition = new Vector3(0f, 0.2f, 0f);
            body.transform.localScale = new Vector3(1f, 0.4f, 0.7f);
            body.GetComponent<Renderer>().sharedMaterial = bodyMat;

            // Lid pivots from a hinge point at its back-bottom edge so it swings open like a real lid.
            GameObject hinge = new GameObject("LidHinge");
            hinge.transform.SetParent(parent, false);
            hinge.transform.localPosition = new Vector3(0f, 0.4f, -0.35f);

            GameObject lid = GameObject.CreatePrimitive(PrimitiveType.Cube);
            lid.name = "ChestLid";
            Destroy(lid.GetComponent<Collider>());
            lid.transform.SetParent(hinge.transform, false);
            lid.transform.localPosition = new Vector3(0f, 0.075f, 0.35f);
            lid.transform.localScale = new Vector3(1f, 0.15f, 0.7f);
            lid.GetComponent<Renderer>().sharedMaterial = bodyMat;

            tutorialChest.Lid = hinge.transform;
        }

        private static void SetObjective(string objective)
        {
            if (QuestManager.Instance != null)
                QuestManager.Instance.UpdateObjective(GameFlowController.EscapeManorQuestId, objective);
        }

        private static void Log(string message)
        {
            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat(message);
        }
    }

    /// <summary>
    /// Chest spawned by TutorialSequence — the Interact button opens the lid and a loot
    /// menu. Taking the draught heals; closing the menu after taking it advances the
    /// tutorial. Closing empty-handed leaves the chest usable.
    /// </summary>
    public class TutorialChest : MonoBehaviour
    {
        /// <summary>Set when using the real Animated Chest prefab — its own opening clip plays instead of the fallback hinge.</summary>
        public Animation ChestAnimation;
        /// <summary>Only used by the procedural fallback visual (no chest prefab wired up).</summary>
        public Transform Lid;
        /// <summary>Disabled once the loot has been taken so the empty chest stops prompting.</summary>
        public Interactable ChestInteractable;

        private bool _lidOpened;
        private bool _looted;
        private System.Collections.Generic.List<UI.LootEntry> _loot;

        /// <summary>Wired to Interactable.OnInteract in TutorialSequence.SpawnChest.</summary>
        public void Open()
        {
            if (!_lidOpened)
            {
                _lidOpened = true;
                if (ChestAnimation != null)
                    ChestAnimation.Play();
                else
                    StartCoroutine(OpenLidRoutine());
            }

            if (_loot == null)
            {
                _loot = new System.Collections.Generic.List<UI.LootEntry>
                {
                    new UI.LootEntry
                    {
                        Name = "Healing Draught",
                        Description = "A stoppered vial of bitter red liquid. Restores 20 health.",
                        OnTaken = TakeHealingDraught
                    }
                };
            }

            UI.LootMenuUI.Show("Supply Chest", _loot, OnLootMenuClosed);
        }

        private void TakeHealingDraught()
        {
            _looted = true;

            var player = CombatController.Instance;
            if (player != null)
            {
                Health hp = player.GetComponent<Health>();
                if (hp != null)
                {
                    hp.Heal(20);
                    player.CurrentHealth = hp.CurrentHealth;
                }
            }

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("You drink the healing draught. (+20 health)");
        }

        private void OnLootMenuClosed()
        {
            if (!_looted) return;

            if (ChestInteractable != null)
                ChestInteractable.enabled = false;

            if (TutorialSequence.Instance != null)
                TutorialSequence.Instance.OnChestLooted();
        }

        private IEnumerator OpenLidRoutine()
        {
            if (Lid == null) yield break;

            Quaternion start = Lid.localRotation;
            Quaternion end = Quaternion.Euler(-100f, 0f, 0f) * start;
            float duration = 0.4f;
            float t = 0f;

            while (t < duration)
            {
                t += Time.deltaTime;
                Lid.localRotation = Quaternion.Slerp(start, end, Mathf.Clamp01(t / duration));
                yield return null;
            }
            Lid.localRotation = end;
        }
    }
}
