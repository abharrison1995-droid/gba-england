using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Systems
{
    /// <summary>
    /// Manages the "Knives" notoriety system and city evasion logic.
    /// </summary>
    public class WantedManager : MonoBehaviour
    {
        public static WantedManager Instance { get; private set; }

        [Header("Wanted State")]
        [Range(0, 5)]
        public int CurrentKnives = 0;
        
        [Header("Cooldown Config")]
        [Tooltip("Base cooldown applied to a chunk per Knife level when evading (in seconds)")]
        public float CooldownPerKnife = 60f;

        [Header("Concealment State")]
        public float MaxConcealment = 100f;
        public float CurrentConcealment = 100f;
        public float ConcealmentRecoveryRate = 5f;

        [Header("Police Escalation Setup")]
        [Tooltip("Prefabs mapped to Knives level: index 0 = Knives 1 (PCSO), index 1 = Knives 2 (Bobby), etc.")]
        public GameObject[] PolicePrefabs;
        public float SpawnRadius = 15f;

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            UpdateConcealmentUI();
        }

        private void Update()
        {
            if (CurrentConcealment < MaxConcealment)
            {
                CurrentConcealment += ConcealmentRecoveryRate * Time.deltaTime;
                if (CurrentConcealment > MaxConcealment) CurrentConcealment = MaxConcealment;
                UpdateConcealmentUI();
            }
        }

        public void DrainConcealment(float amount)
        {
            CurrentConcealment -= amount;
            if (CurrentConcealment <= 0)
            {
                CurrentConcealment = MaxConcealment; // reset after being busted
                SpikeKnives();
                if (ExiledAlvaston.UI.UIManager.Instance != null)
                {
                    ExiledAlvaston.UI.UIManager.Instance.ShowToast("Busted! The police have been alerted.", 2.5f);
                }
            }
            UpdateConcealmentUI();
        }

        private void UpdateConcealmentUI()
        {
            if (ExiledAlvaston.UI.UIManager.Instance != null)
                ExiledAlvaston.UI.UIManager.Instance.UpdatePlayerConcealment(CurrentConcealment, MaxConcealment);
        }

        /// <summary>
        /// Raises the Knives level by one (capped at 5) and refreshes the HUD. Used when the
        /// player does something the law frowns on — e.g. slinging magic in the city.
        /// </summary>
        public void SpikeKnives()
        {
            if (CurrentKnives < 5)
            {
                CurrentKnives++;
                UpdateUIIndicator();
                SpawnPlod();
            }
        }

        private void SpawnPlod()
        {
            if (PolicePrefabs == null || PolicePrefabs.Length == 0) return;
            
            int index = Mathf.Clamp(CurrentKnives - 1, 0, PolicePrefabs.Length - 1);
            GameObject prefab = PolicePrefabs[index];
            if (prefab == null) return;
            
            var player = ExiledAlvaston.Combat.CombatController.Instance;
            if (player == null) return;
            
            // Randomly spawn around player. A real implementation should use NavMesh.SamplePosition.
            Vector3 randomOffset = Random.insideUnitSphere * SpawnRadius;
            randomOffset.y = 0;
            Vector3 spawnPos = player.transform.position + randomOffset;
            
            Instantiate(prefab, spawnPos, Quaternion.identity);
            
            if (ExiledAlvaston.UI.UIManager.Instance != null)
            {
                string message = CurrentKnives switch
                {
                    1 => "PCSOs deployed. Oi! You can't do magic 'ere!",
                    2 => "The Bobbies are onto you!",
                    3 => "Armed Police! Drop the wand!",
                    4 => "Ministry of Occult deployed.",
                    _ => "It's all kicked off now!"
                };
                ExiledAlvaston.UI.UIManager.Instance.ShowToast(message, 3f);
            }
        }

        /// <summary>
        /// Hook called by the ChunkManager when the player transitions between grid chunks.
        /// Evaluates evasion logic.
        /// </summary>
        public void OnChunkTransition(MapChunkData previousChunk, MapChunkData newChunk)
        {
            if (previousChunk == null || newChunk == null) return;
            if (CurrentKnives == 0) return; // Not wanted

            // If escaping a City into a Wilderness chunk
            if (previousChunk.IsCity && !newChunk.IsCity)
            {
                Debug.Log("Evaded Police by entering a wilderness chunk!");

                // Apply cooldown to the city chunk we just left
                float cooldown = CurrentKnives * CooldownPerKnife;
                ChunkManager.Instance.ApplyCityLockout(previousChunk, cooldown);

                // Clear wanted level
                CurrentKnives = 0;
                UpdateUIIndicator();
            }
            // If entering a new City while already wanted, notoriety persists.
            else if (!previousChunk.IsCity && newChunk.IsCity)
            {
                Debug.Log("Entered a city while still wanted. Re-initiating pursuit.");
            }
        }

        private void UpdateUIIndicator()
        {
            if (ExiledAlvaston.UI.UIManager.Instance != null)
                ExiledAlvaston.UI.UIManager.Instance.UpdateKnivesUI(CurrentKnives);
        }
    }
}
