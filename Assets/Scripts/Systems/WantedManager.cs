using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.World;

namespace GBHEngland.Systems
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

        [Header("Decay")]
        [Tooltip("Seconds of no fresh offense before one Knife fades, GTA-star style. Resets to 0 every time SpikeKnives fires, so re-offending restarts the countdown.")]
        public float KnifeDecayInterval = 60f;
        private float _knifeDecayTimer;

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

            if (CurrentKnives > 0)
            {
                _knifeDecayTimer += Time.deltaTime;
                if (_knifeDecayTimer >= KnifeDecayInterval)
                {
                    _knifeDecayTimer = 0f;
                    CurrentKnives--;
                    UpdateUIIndicator();

                    // The police already spawned via SpikeKnives don't vanish on their own — without
                    // this, the meter reads "not wanted" while officers spawned earlier are still
                    // hunting the player. ClearWanted() despawns them for the instant-clear paths;
                    // decay reaching 0 needs the same, since it's read the same way by the player.
                    if (CurrentKnives == 0)
                        DespawnPolice();
                }
            }
        }

        public void DrainConcealment(float amount)
        {
            CurrentConcealment -= amount;
            if (CurrentConcealment <= 0)
            {
                CurrentConcealment = MaxConcealment; // reset after being busted
                SpikeKnives();
                if (GBHEngland.UI.UIManager.Instance != null)
                {
                    GBHEngland.UI.UIManager.Instance.ShowToast("Busted! The police have been alerted.", 2.5f);
                }
            }
            UpdateConcealmentUI();
        }

        private void UpdateConcealmentUI()
        {
            if (GBHEngland.UI.UIManager.Instance != null)
                GBHEngland.UI.UIManager.Instance.UpdatePlayerConcealment(CurrentConcealment, MaxConcealment);
        }

        /// <summary>
        /// Raises the Knives level by one (capped at 5) and refreshes the HUD. Used when the
        /// player does something the law frowns on — e.g. slinging magic in the city.
        /// </summary>
        public void SpikeKnives()
        {
            _knifeDecayTimer = 0f;

            if (CurrentKnives < 5)
            {
                CurrentKnives++;
                UpdateUIIndicator();
                SpawnPlod();
            }
        }

        /// <summary>
        /// Wipes the wanted level, restores concealment, refreshes both HUD readouts, and
        /// despawns the police already on the scene. That last step is not optional: SpawnPlod
        /// instantiates officers unparented at the scene root, so they outlive a chunk
        /// transition, and clearing the meters alone leaves Armed Response hunting a player the
        /// HUD has just declared clean.
        ///
        /// The reusable version of what <c>GameFlowController.ArrestRoutine</c> does inline —
        /// that routine is deliberately left alone, since rerouting the arrest path is a separate
        /// change needing its own play-test.
        /// </summary>
        public void ClearWanted()
        {
            CurrentKnives = 0;
            CurrentConcealment = MaxConcealment;
            UpdateUIIndicator();
            UpdateConcealmentUI();
            DespawnPolice();
        }

        /// <summary>
        /// Destroys every police officer in the scene. FindObjectsOfType allocates and walks the
        /// whole hierarchy, so this belongs to one-shot events only — never an Update path (§4).
        /// </summary>
        public void DespawnPolice()
        {
            foreach (var enemy in FindObjectsOfType<GBHEngland.Combat.EnemyAI>())
            {
                if (enemy != null && enemy.IsPolice)
                    Destroy(enemy.gameObject);
            }
        }

        private void SpawnPlod()
        {
            if (PolicePrefabs == null || PolicePrefabs.Length == 0) return;
            
            int index = Mathf.Clamp(CurrentKnives - 1, 0, PolicePrefabs.Length - 1);
            GameObject prefab = PolicePrefabs[index];
            if (prefab == null) return;
            
            var player = GBHEngland.Combat.CombatController.Instance;
            if (player == null) return;

            // Randomly spawn around the player, then snap to the NavMesh — the same pattern
            // CompanionManager uses to place a companion beside the player. A random offset alone
            // can land inside geometry; falling back to the player's own position (rather than
            // the unsampled point) keeps a failed sample from spawning an officer in a wall.
            Vector3 randomOffset = Random.insideUnitSphere * SpawnRadius;
            randomOffset.y = 0;
            Vector3 spawnPos = player.transform.position + randomOffset;
            if (UnityEngine.AI.NavMesh.SamplePosition(spawnPos, out UnityEngine.AI.NavMeshHit navHit, 4f, UnityEngine.AI.NavMesh.AllAreas))
                spawnPos = navHit.position;
            else
                spawnPos = player.transform.position;

            Transform parent = ChunkManager.Instance != null && ChunkManager.Instance.CurrentChunkInstance != null
                ? ChunkManager.Instance.CurrentChunkInstance.transform
                : null;
            Instantiate(prefab, spawnPos, Quaternion.identity, parent);
            
            if (GBHEngland.UI.UIManager.Instance != null)
            {
                string message = CurrentKnives switch
                {
                    1 => "PCSOs deployed. Oi! You can't do magic 'ere!",
                    2 => "The Bobbies are onto you!",
                    3 => "Armed Police! Drop the wand!",
                    4 => "Ministry of Occult deployed.",
                    _ => "It's all kicked off now!"
                };
                GBHEngland.UI.UIManager.Instance.ShowToast(message, 3f);
            }
        }

        /// <summary>
        /// Hook called by the ChunkManager when the player transitions between chunks.
        /// Evaluates evasion logic.
        ///
        /// ⚠ <paramref name="travelKind"/> is what stops a doorway laundering the wanted level.
        /// Getting away from the police means getting out of town — which is an edge crossing and
        /// nothing else. See <see cref="ChunkTravelKind"/>; the parameter is deliberately required.
        /// </summary>
        public void OnChunkTransition(MapChunkData previousChunk, MapChunkData newChunk,
                                      ChunkTravelKind travelKind)
        {
            if (previousChunk == null || newChunk == null) return;
            if (CurrentKnives == 0) return; // Not wanted

            // If escaping a City into a Wilderness chunk
            if (previousChunk.IsCity && !newChunk.IsCity)
            {
                // A door is not an escape. Interiors and dungeons are off the overworld grid and
                // all carry IsCity: 0, so testing IsCity alone would mean the player could rob
                // London, step into a shop, and step back out with a clean sheet — and land a
                // police cooldown on London for their trouble, since the branch below applies one.
                //
                // Gating on the travel kind rather than on a per-chunk flag means every interior
                // added from here on is covered the moment it exists, with nothing to remember to
                // tick. A portal that is genuinely meant to be an escape route can be given its
                // own kind later, deliberately.
                if (travelKind != ChunkTravelKind.EdgeCrossing)
                {
                    Debug.Log($"Slipped indoors ('{newChunk.ChunkName}') while wanted — " +
                              "the law is still outside. Wanted level kept.");
                    return;
                }

                Debug.Log("Evaded Police by entering a wilderness chunk!");

                // Apply cooldown to the city chunk we just left
                float cooldown = CurrentKnives * CooldownPerKnife;
                ChunkManager.Instance.ApplyCityLockout(previousChunk, cooldown);

                // Clear wanted level
                ClearWanted();
            }
            // If entering a new City while already wanted, notoriety persists.
            else if (!previousChunk.IsCity && newChunk.IsCity)
            {
                Debug.Log("Entered a city while still wanted. Re-initiating pursuit.");
            }
        }

        private void UpdateUIIndicator()
        {
            if (GBHEngland.UI.UIManager.Instance != null)
                GBHEngland.UI.UIManager.Instance.UpdateKnivesUI(CurrentKnives);
        }

    }
}
