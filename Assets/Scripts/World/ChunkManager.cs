using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using ExiledAlvaston.Data;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    public enum Direction
    {
        North,
        South,
        East,
        West
    }

    /// <summary>
    /// Manages the discrete chunk-based world structure.
    /// Handles grid-edge transitions, UI loading screens, and lockout timers.
    /// </summary>
    public class ChunkManager : MonoBehaviour
    {
        public static ChunkManager Instance { get; private set; }

        [Header("Current State")]
        public MapChunkData CurrentChunkData;
        public GameObject CurrentChunkInstance;

        [Header("Save / Load")]
        [Tooltip("Every chunk that Save/Load needs to be able to find by name. Populated by Tools/Exiled Alvaston/Setup Death Screen.")]
        public MapChunkData[] AllChunks;

        [Header("Dependencies")]
        [Tooltip("UI Canvas overlay for hard pausing during transitions.")]
        public CanvasGroup LoadingScreenUI;
        [Tooltip("UI Text prompt for warning the player they cannot enter a chunk.")]
        public TMPro.TextMeshProUGUI WarningPromptUI;
        public Transform PlayerTransform;

        // Represents the lockout timers per City chunk.
        private Dictionary<Vector2IntCoords, float> _cityLockoutTimers = new Dictionary<Vector2IntCoords, float>();
        
        // Zero-allocation parallel list for iteration
        private List<Vector2IntCoords> _activeLockoutKeys = new List<Vector2IntCoords>();

        private bool _isTransitioning = false;
        private float _nextEdgeTriggerAllowedAt = 0f;

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            if (PlayerTransform == null)
            {
                var player = ExiledAlvaston.Combat.CombatController.Instance
                    ?? FindObjectOfType<ExiledAlvaston.Combat.CombatController>();
                if (player != null) PlayerTransform = player.transform;
            }

            // Load starting chunk if none is in the scene yet (skip during title/creator)
            bool blockAutoload = ExiledAlvaston.Flow.GameFlowController.Instance != null
                && ExiledAlvaston.Flow.GameFlowController.Instance.State != ExiledAlvaston.Flow.GameFlowState.Playing;

            if (!blockAutoload
                && CurrentChunkInstance == null
                && CurrentChunkData != null
                && CurrentChunkData.ChunkPrefab != null)
            {
                CurrentChunkInstance = Instantiate(CurrentChunkData.ChunkPrefab, Vector3.zero, Quaternion.identity);
                CurrentChunkInstance.name = CurrentChunkData.ChunkPrefab.name;
            }
        }

        private void Update()
        {
            // Zero-allocation backward iteration
            for (int i = _activeLockoutKeys.Count - 1; i >= 0; i--)
            {
                var key = _activeLockoutKeys[i];
                _cityLockoutTimers[key] -= Time.deltaTime;
                
                if (_cityLockoutTimers[key] <= 0)
                {
                    _cityLockoutTimers.Remove(key);
                    _activeLockoutKeys.RemoveAt(i);
                }
            }
        }

        /// <summary>
        /// Applies a real-time cooldown timer blocking access to a specific city chunk.
        /// </summary>
        public void ApplyCityLockout(MapChunkData cityChunk, float cooldownDurationSeconds)
        {
            if (cityChunk == null || !cityChunk.IsCity) return;

            if (!_cityLockoutTimers.ContainsKey(cityChunk.Coordinates))
            {
                _cityLockoutTimers.Add(cityChunk.Coordinates, cooldownDurationSeconds);
                _activeLockoutKeys.Add(cityChunk.Coordinates);
            }
            else
            {
                _cityLockoutTimers[cityChunk.Coordinates] = cooldownDurationSeconds;
            }
        }

        /// <summary>
        /// Evaluates if the player is hitting an outer edge of the chunk's bounding box.
        /// </summary>
        public void OnPlayerHitEdge(Direction edgeDirection)
        {
            if (_isTransitioning) return;
            if (Time.unscaledTime < _nextEdgeTriggerAllowedAt) return;

            if (CurrentChunkData != null
                && CurrentChunkData.LockExitsUntilTutorialComplete
                && (ExiledAlvaston.Flow.PlayerSession.Instance == null
                    || !ExiledAlvaston.Flow.PlayerSession.Instance.TutorialComplete))
            {
                ShowWarning("The Manor Cellars exits are sealed. Clear the cellars and use the gate.");
                if (ExiledAlvaston.UI.UIManager.Instance != null)
                    ExiledAlvaston.UI.UIManager.Instance.LogCombat("Exits locked — find the manor gate.");
                return;
            }

            MapChunkData targetChunk = GetAdjacentChunkData(edgeDirection);

            if (targetChunk != null)
            {
                // Check if target chunk is locked out
                if (targetChunk.IsCity && _cityLockoutTimers.ContainsKey(targetChunk.Coordinates))
                {
                    float remainingTime = _cityLockoutTimers[targetChunk.Coordinates];
                    ShowWarning($"Cannot enter {targetChunk.ChunkName}. Police activity active for {Mathf.CeilToInt(remainingTime)}s.");
                    return;
                }

                StartCoroutine(TransitionToChunkRoutine(targetChunk, edgeDirection));
            }
        }

        /// <summary>
        /// Portal travel to any chunk with an explicit spawn point — used by DungeonPortal
        /// for dungeon entrances/exits, unlike edge transitions which derive the spawn side.
        /// </summary>
        public void TravelTo(MapChunkData targetChunk, Vector3 spawnPosition)
        {
            if (_isTransitioning) return;
            StartCoroutine(TravelRoutine(targetChunk, spawnPosition));
        }

        private IEnumerator TravelRoutine(MapChunkData targetChunk, Vector3 spawnPosition)
        {
            if (targetChunk == null || targetChunk.ChunkPrefab == null)
            {
                Debug.LogWarning($"ChunkManager: portal target '{(targetChunk != null ? targetChunk.name : "null")}' has no prefab — travel aborted.");
                yield break;
            }
            if (PlayerTransform == null)
            {
                var player = ExiledAlvaston.Combat.CombatController.Instance;
                if (player != null) PlayerTransform = player.transform;
            }
            if (PlayerTransform == null)
            {
                Debug.LogWarning("ChunkManager: no PlayerTransform — travel aborted.");
                yield break;
            }

            _isTransitioning = true;
            ExiledAlvaston.Systems.PauseManager.Push();
            if (LoadingScreenUI)
            {
                LoadingScreenUI.alpha = 1f;
                LoadingScreenUI.interactable = true;
                LoadingScreenUI.blocksRaycasts = true;
            }

            try
            {
                yield return new WaitForSecondsRealtime(0.15f);

                ExiledAlvaston.Systems.WantedManager.Instance?.OnChunkTransition(CurrentChunkData, targetChunk);

                GameObject previousInstance = CurrentChunkInstance;
                CurrentChunkData = targetChunk;
                CurrentChunkInstance = Instantiate(targetChunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
                CurrentChunkInstance.name = targetChunk.ChunkPrefab.name;

                // Portal travel is given an explicit arrival position by the caller (DungeonPortal) —
                // honor it directly. Deferring to the chunk's generic PlayerSpawnPoint here would
                // send every portal into a chunk to the same single default marker, ignoring
                // whatever position was actually configured on this specific portal.
                TeleportPlayer(spawnPosition);

                var camFollow = FindObjectOfType<IsometricCameraFollow>();
                if (camFollow != null)
                    camFollow.SnapToTarget();

                if (previousInstance != null)
                    Destroy(previousInstance);

                _nextEdgeTriggerAllowedAt = Time.unscaledTime + 1f;

                // Save inside the new chunk must be loadable later, so the chunk has to be
                // findable by name even if the scene's AllChunks list predates it.
                EnsureKnownChunk(targetChunk);
                ExiledAlvaston.Flow.SaveGameManager.Save();
            }
            finally
            {
                if (LoadingScreenUI)
                {
                    LoadingScreenUI.alpha = 0f;
                    LoadingScreenUI.interactable = false;
                    LoadingScreenUI.blocksRaycasts = false;
                }
                ExiledAlvaston.Systems.PauseManager.Pop();
                _isTransitioning = false;
            }
        }

        /// <summary>Appends a chunk to AllChunks at runtime if the scene list doesn't have it.</summary>
        public void EnsureKnownChunk(MapChunkData chunk)
        {
            if (chunk == null) return;
            if (AllChunks != null)
            {
                foreach (MapChunkData c in AllChunks)
                    if (c == chunk) return;
            }

            int oldLen = AllChunks != null ? AllChunks.Length : 0;
            var grown = new MapChunkData[oldLen + 1];
            if (oldLen > 0) System.Array.Copy(AllChunks, grown, oldLen);
            grown[oldLen] = chunk;
            AllChunks = grown;
        }

        public MapChunkData FindChunkByName(string chunkName)
        {
            if (AllChunks == null || string.IsNullOrEmpty(chunkName)) return null;
            foreach (MapChunkData c in AllChunks)
                if (c != null && c.ChunkName == chunkName) return c;
            return null;
        }

        private MapChunkData GetAdjacentChunkData(Direction dir)
        {
            if (CurrentChunkData == null) return null;

            switch (dir)
            {
                case Direction.North: return CurrentChunkData.NorthChunk;
                case Direction.South: return CurrentChunkData.SouthChunk;
                case Direction.East: return CurrentChunkData.EastChunk;
                case Direction.West: return CurrentChunkData.WestChunk;
                default: return null;
            }
        }

        private IEnumerator TransitionToChunkRoutine(MapChunkData targetChunk, Direction travelDir)
        {
            // Validate everything up front — once we pause, any exception would freeze the game
            if (targetChunk == null || targetChunk.ChunkPrefab == null)
            {
                Debug.LogWarning($"ChunkManager: target chunk '{(targetChunk != null ? targetChunk.name : "null")}' has no prefab — transition aborted.");
                yield break;
            }
            if (PlayerTransform == null)
            {
                var player = ExiledAlvaston.Combat.CombatController.Instance;
                if (player != null) PlayerTransform = player.transform;
            }
            if (PlayerTransform == null)
            {
                Debug.LogWarning("ChunkManager: no PlayerTransform — transition aborted.");
                yield break;
            }

            _isTransitioning = true;
            ExiledAlvaston.Systems.PauseManager.Push();
            if (LoadingScreenUI)
            {
                LoadingScreenUI.alpha = 1f;
                LoadingScreenUI.interactable = true;
                LoadingScreenUI.blocksRaycasts = true;
            }

            try
            {
                // Brief beat on solid ground before the cut — no loading screen is wired up,
                // so we never leave the player standing on nothing.
                yield return new WaitForSecondsRealtime(0.15f);

                // Notify Wanted System of transition
                ExiledAlvaston.Systems.WantedManager.Instance?.OnChunkTransition(CurrentChunkData, targetChunk);

                // Instantiate the next chunk BEFORE removing the old one, so there's never a
                // frame where the player has no floor under them.
                GameObject previousInstance = CurrentChunkInstance;
                CurrentChunkData = targetChunk;
                CurrentChunkInstance = Instantiate(targetChunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
                CurrentChunkInstance.name = targetChunk.ChunkPrefab.name;

                // Reposition Player to the opposite edge
                RepositionPlayerForTransition(travelDir);

                // Camera was frozen (Time.timeScale == 0) during the pause above — snap it straight
                // to the new position instead of letting it glide across the whole map to catch up.
                var camFollow = FindObjectOfType<IsometricCameraFollow>();
                if (camFollow != null)
                    camFollow.SnapToTarget();

                if (previousInstance != null)
                    Destroy(previousInstance);

                // Grace period so landing near the new chunk's own edge trigger can't instantly bounce us back.
                _nextEdgeTriggerAllowedAt = Time.unscaledTime + 1f;

                // Checkpoint: every chunk crossing is a save point.
                ExiledAlvaston.Flow.SaveGameManager.Save();
            }
            finally
            {
                // Always restore the pause + input, even if a step above threw
                if (LoadingScreenUI)
                {
                    LoadingScreenUI.alpha = 0f;
                    LoadingScreenUI.interactable = false;
                    LoadingScreenUI.blocksRaycasts = false;
                }
                ExiledAlvaston.Systems.PauseManager.Pop();
                _isTransitioning = false;
            }
        }

        private void RepositionPlayerForTransition(Direction travelDir)
        {
            float mapSize = EKVibe.ChunkSize;
            // Must clear the new chunk's own edge-trigger depth (2 units) by a wide margin,
            // or we spawn straight back inside a trigger that bounces us right back out.
            float buffer = 12f;

            Vector3 pos = PlayerTransform.position;
            switch(travelDir)
            {
                case Direction.North: pos.z = -mapSize/2 + buffer; break;
                case Direction.South: pos.z = mapSize/2 - buffer; break;
                case Direction.East:  pos.x = -mapSize/2 + buffer; break;
                case Direction.West:  pos.x = mapSize/2 - buffer; break;
            }
            TeleportPlayer(pos);
        }

        /// <summary>Moves the player, keeping the Rigidbody in sync to avoid interpolation ghosting.</summary>
        public void TeleportPlayer(Vector3 position)
        {
            if (PlayerTransform == null) return;

            var rb = PlayerTransform.GetComponent<Rigidbody>();
            if (rb != null)
            {
                rb.position = position;
                rb.velocity = Vector3.zero;
            }
            PlayerTransform.position = position;
        }

        private void ShowWarning(string message)
        {
            if (WarningPromptUI == null) return;

            WarningPromptUI.text = message;
            WarningPromptUI.gameObject.SetActive(true);
            
            // Auto hide
            CancelInvoke(nameof(HideWarning));
            Invoke(nameof(HideWarning), 3f);
        }

        private void HideWarning()
        {
            if (WarningPromptUI != null)
                WarningPromptUI.gameObject.SetActive(false);
        }
    }
}
