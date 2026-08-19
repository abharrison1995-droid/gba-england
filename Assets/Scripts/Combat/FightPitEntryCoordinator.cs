using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.Systems;
using GBHEngland.World;
using GBHEngland.UI;
using GBHEngland.Companions;

namespace GBHEngland.Combat
{
    /// <summary>
    /// Validates tournament entry, captures/restores player vital snapshots, freezes level offset,
    /// and orchestrates travel to the Castle Fight Arena.
    /// </summary>
    public class FightPitEntryCoordinator : MonoBehaviour
    {
        public static FightPitEntryCoordinator Instance { get; private set; }

        public int SnapshotHealth { get; private set; }
        public int SnapshotMana { get; private set; }
        public int SnapshotStamina { get; private set; }
        public int PlayerLevelOffset { get; private set; }

        private float _nextUseAt;

        public static FightPitEntryCoordinator Ensure()
        {
            if (Instance == null)
            {
                var go = new GameObject("FightPitEntryCoordinator");
                DontDestroyOnLoad(go);
                go.AddComponent<FightPitEntryCoordinator>();
            }
            return Instance;
        }

        private void Awake()
        {
            if (Instance == null)
            {
                Instance = this;
                DontDestroyOnLoad(gameObject);
            }
            else if (Instance != this)
            {
                Destroy(gameObject);
            }
        }

        private void OnDestroy()
        {
            if (Instance == this)
                Instance = null;
        }

        /// <summary>
        /// Validates prerequisites and transitions the player into the Castle Fight Arena.
        /// </summary>
        public bool TryEnterPit()
        {
            if (Time.unscaledTime < _nextUseAt) return false;

            if (ChunkManager.Instance == null || ChunkManager.Instance.IsTransitioning)
                return false;

            if (WantedManager.Instance != null && WantedManager.Instance.CurrentKnives > 0)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("Can't enter the fight pit while wanted by police.", 2.5f);
                return false;
            }

            if (MountController.IsPlayerRiding || (MountController.Current != null && MountController.Current.IsMounted))
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("Get out of the vehicle first.", 2.5f);
                return false;
            }

            if (CompanionManager.Instance != null && CompanionManager.Instance.HasActiveCompanion)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("Companions are not allowed in the pit.", 2.5f);
                return false;
            }

            FightPitConfig config = FightPitConfig.Load();
            if (config == null || config.Rounds == null || config.Rounds.Count == 0)
            {
                Debug.LogError("FightPitEntryCoordinator: FightPitConfig asset not found or has no rounds.");
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("The fight pit is not available.", 2.5f);
                return false;
            }

            MapChunkData arenaChunk = ChunkManager.Instance.FindChunkByName("Castle Fight Arena");
            if (arenaChunk == null || arenaChunk.ChunkPrefab == null)
            {
                Debug.LogError("FightPitEntryCoordinator: 'Castle Fight Arena' chunk or prefab not found.");
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("The fight pit is closed.", 2.5f);
                return false;
            }

            _nextUseAt = Time.unscaledTime + 1.5f;

            // Snapshot vitals before entering the arena
            var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
            var hp = player != null ? player.GetComponent<Health>() : null;
            SnapshotHealth = hp != null ? hp.CurrentHealth : (player != null ? player.CurrentHealth : 100);
            SnapshotMana = player != null ? player.CurrentMana : 50;
            SnapshotStamina = player != null ? player.CurrentStamina : 50;

            // Freeze player level scaling offset for this run
            int playerLevel = PlayerSession.Instance != null ? PlayerSession.Instance.Level : 1;
            PlayerLevelOffset = Mathf.Max(0, playerLevel - 1);

            // Safe checkpoint in Home London before transitioning
            SaveGameManager.Save();

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("Entering the Castle Fight Pit...");

            ChunkManager.Instance.TravelTo(arenaChunk, "arena_player", Vector3.zero);
            return true;
        }

        /// <summary>
        /// Restores player health, mana, stamina, and colliders to the captured entry snapshot.
        /// </summary>
        public void RestoreVitalsToPlayer(CombatController player)
        {
            if (player == null) return;

            player.ReviveFull();

            Health hp = player.GetComponent<Health>();
            int restoreHealth = Mathf.Max(1, SnapshotHealth);
            if (hp != null)
            {
                hp.Revive(restoreHealth);
                player.CurrentHealth = hp.CurrentHealth;
            }
            else
            {
                player.CurrentHealth = restoreHealth;
            }

            player.CurrentMana = SnapshotMana;
            player.CurrentStamina = SnapshotStamina;

            foreach (var col in player.GetComponentsInChildren<Collider>())
                col.enabled = true;
        }
    }
}
