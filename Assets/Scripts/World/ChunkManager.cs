using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using GBHEngland.Data;
using GBHEngland.Vibe;

namespace GBHEngland.World
{
    public enum Direction
    {
        North,
        South,
        East,
        West
    }

    /// <summary>
    /// How the player got from one chunk to the next. Passed to
    /// <see cref="GBHEngland.Systems.WantedManager.OnChunkTransition"/>, which treats the two
    /// differently: walking out of town can shake the police, walking through a door cannot.
    ///
    /// Not serialized anywhere — it is a method parameter only — so the append-only rule that
    /// governs the project's other enums (CLAUDE.md §3) does not apply to it. It is deliberately a
    /// required parameter with no default: a third transition path that wants to notify the wanted
    /// system has to state which kind it is rather than inheriting whichever was convenient.
    /// </summary>
    public enum ChunkTravelKind
    {
        /// <summary>Walked over a chunk edge into an adjacent overworld chunk.</summary>
        EdgeCrossing,
        /// <summary>Used a <see cref="DungeonPortal"/> — a door into an interior or a dungeon.</summary>
        Portal
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

        /// <summary>
        /// The chunk whose prefab is being instantiated right now, or null outside that window.
        ///
        /// ⚠ This exists because <see cref="TravelRoutine"/> builds the destination and inspects it
        /// for the arrival marker BEFORE committing anything — deliberately, so a broken marker id
        /// leaves the world untouched. Every Awake in the new chunk runs synchronously inside that
        /// Instantiate, so content reading <see cref="CurrentChunkData"/> during Awake sees the
        /// chunk the player just LEFT. Moving the assignment earlier would destroy the abort
        /// safety, so the answer is a second field and a resolver that prefers it.
        ///
        /// A property, not a serialized field: it is per-frame transient state with no business
        /// being authorable, and a public field here would write an orphan key into c.unity.
        /// </summary>
        public MapChunkData ChunkBeingBuilt { get; private set; }

        /// <summary>
        /// The chunk that content instantiated right now belongs to. This is what anything running
        /// in Awake must ask — never <see cref="CurrentChunkData"/> directly, which is only correct
        /// on six of the seven paths that build a chunk.
        /// </summary>
        public string ContentChunkName =>
            ChunkBeingBuilt != null ? ChunkBeingBuilt.ChunkName
            : CurrentChunkData != null ? CurrentChunkData.ChunkName
            : null;

        // ── Container cooldowns and the seven instantiate paths ─────────────────────────
        // Seven code paths build a chunk. Only the two here count as "a visit" for a restockable
        // container, and the other five are silent on purpose:
        //
        //   TransitionToChunkRoutine (edge)   ticks — the canonical left-and-came-back
        //   TravelRoutine (portal)            ticks — with a give-back on the abort branch
        //   ChunkManager.Start (cold boot)    no — debug autoload; does not even write CurrentChunkData
        //   SaveGameManager.LoadWorld         no — a reload must not advance a cooldown, or
        //                                          reload-spam becomes the fastest way to farm
        //   DeathScreenUI.OnNewGame fallback  no — dying is not a visit
        //   GameFlowController.EnterManorCellars      no — one-shot; the arrest path lands here
        //   GameFlowController.LoadLondonAtWestGates  no — one-shot tutorial exit
        //
        // Adding an eighth path means deciding which of those two groups it joins.

        [Header("Save / Load")]
        [Tooltip("Every chunk that Save/Load needs to be able to find by name. A chunk missing from this list cannot be loaded even if the save names it.")]
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
        public bool IsTransitioning => _isTransitioning;
        private float _nextEdgeTriggerAllowedAt = 0f;

        // ChunkEdge re-offers a crossing every physics tick via OnTriggerStay, so anything that
        // declines one needs its own throttle or the warning re-shows continuously.
        private float _nextDeadEndWarningAt = 0f;
        private const float DeadEndWarningCooldown = 3f;

        // Arrival lands 3.5 units clear of the perimeter (at ±106.5) — well inside the
        // ±109.8 trigger face — so this grace only needs to cover the teleport itself and
        // any residual physics overlap from the frame of arrival.
        private const float EdgeTriggerGrace = 0.25f;

        // Last-resort net: nothing should get under the ground plane at y=0, but a gap in a
        // chunk's geometry would otherwise drop the player forever with no way back.
        private const float VoidFloorY = -20f;

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            if (PlayerTransform == null)
            {
                var player = GBHEngland.Combat.CombatController.Instance
                    ?? FindObjectOfType<GBHEngland.Combat.CombatController>();
                if (player != null) PlayerTransform = player.transform;
            }

            // Load starting chunk if none is in the scene yet (skip during title/creator)
            bool blockAutoload = GBHEngland.Flow.GameFlowController.Instance != null
                && GBHEngland.Flow.GameFlowController.Instance.State != GBHEngland.Flow.GameFlowState.Playing;

            if (!blockAutoload
                && CurrentChunkInstance == null
                && CurrentChunkData != null
                && CurrentChunkData.ChunkPrefab != null)
            {
                CurrentChunkInstance = Instantiate(CurrentChunkData.ChunkPrefab, Vector3.zero, Quaternion.identity);
                CurrentChunkInstance.name = CurrentChunkData.ChunkPrefab.name;
                GBHEngland.Flow.PlayerSession.Instance?.MarkChunkVisited(CurrentChunkData.ChunkName);
                // Silent: the scene-autoload debug path is not a discovery.
                GBHEngland.UI.WikiUnlock.GrantForChunk(CurrentChunkData.ChunkName, silent: true);
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

            // Void catcher. Chunks are flat ground at y=0; falling well below that means the
            // player found a hole, so put them back somewhere standable in the chunk they're in.
            if (!_isTransitioning
                && PlayerTransform != null
                && PlayerTransform.position.y < VoidFloorY)
            {
                TeleportPlayer(RecoveryPoint());
                ShowWarning("You slipped. Back to solid ground.");
            }
        }

        /// <summary>
        /// Where to put someone who has fallen out of the world: the chunk's own default arrival
        /// point, falling back to the origin.
        ///
        /// The origin alone was fine while chunks were empty ground. It stops being fine the moment
        /// one is built up — Home_London has houses near the middle — because recovering from a
        /// hole in the floor by being posted inside a building is not much of a recovery.
        ///
        /// One GetComponentsInChildren, on a path that only runs once someone has already fallen
        /// through the world.
        /// </summary>
        private Vector3 RecoveryPoint()
        {
            return PlayerSpawnPoint.ResolveWorldPosition(CurrentChunkInstance, Vector3.zero);
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
        /// Reads the same lockout timer <see cref="OnPlayerHitEdge"/> already consults, so any
        /// travel path — edge crossing or portal — asks one canonical question instead of each
        /// keeping its own copy of the answer.
        /// </summary>
        public bool IsCityLockedOut(MapChunkData chunk, out float remainingSeconds)
        {
            remainingSeconds = 0f;
            if (chunk == null || !chunk.IsCity) return false;
            if (!_cityLockoutTimers.TryGetValue(chunk.Coordinates, out remainingSeconds)) return false;
            return remainingSeconds > 0f;
        }

        /// <summary>
        /// Evaluates if the player is hitting an outer edge of the chunk's bounding box.
        /// </summary>
        public void OnPlayerHitEdge(Direction edgeDirection)
        {
            if (_isTransitioning) return;
            if (Time.unscaledTime < _nextEdgeTriggerAllowedAt) return;

            if (MountController.IsPlayerRiding || (MountController.Current != null && MountController.Current.IsMounted))
            {
                if (Time.unscaledTime < _nextDeadEndWarningAt) return;
                _nextDeadEndWarningAt = Time.unscaledTime + DeadEndWarningCooldown;
                ShowWarning("Get out of the vehicle first.");
                if (GBHEngland.UI.UIManager.Instance != null)
                    GBHEngland.UI.UIManager.Instance.ShowToast("Get out of the vehicle first.");
                return;
            }

            if (CurrentChunkData != null
                && CurrentChunkData.LockExitsUntilTutorialComplete
                && (GBHEngland.Flow.PlayerSession.Instance == null
                    || !GBHEngland.Flow.PlayerSession.Instance.TutorialComplete))
            {
                // Throttle: the player is now pinned against the boundary wall inside the
                // trigger volume, so OnTriggerStay re-fires every physics tick.
                if (Time.unscaledTime < _nextDeadEndWarningAt) return;
                _nextDeadEndWarningAt = Time.unscaledTime + DeadEndWarningCooldown;
                ShowWarning("The Manor Cellars exits are sealed. Clear the cellars and use the gate.");
                if (GBHEngland.UI.UIManager.Instance != null)
                    GBHEngland.UI.UIManager.Instance.LogCombat("Exits locked — find the manor gate.");
                return;
            }

            MapChunkData targetChunk = GetAdjacentChunkData(edgeDirection);

            if (targetChunk != null)
            {
                // Check if target chunk is locked out. Routes through the canonical question
                // (IsCityLockedOut) so the edge and portal paths stay in agreement, and so an
                // entry whose timer has elapsed but not yet been pruned this frame doesn't refuse
                // the crossing or print a negative countdown.
                if (IsCityLockedOut(targetChunk, out float remainingTime))
                {
                    // Throttle: same reason as tutorial lock above.
                    if (Time.unscaledTime < _nextDeadEndWarningAt) return;
                    _nextDeadEndWarningAt = Time.unscaledTime + DeadEndWarningCooldown;
                    ShowWarning($"Cannot enter {targetChunk.ChunkName}. Police activity active for {Mathf.CeilToInt(remainingTime)}s.");
                    return;
                }

                StartCoroutine(TransitionToChunkRoutine(targetChunk, edgeDirection));
            }
            else if (Time.unscaledTime >= _nextDeadEndWarningAt)
            {
                // Dead end. Outer chunks link back to Home only, so three of their four edges
                // lead nowhere — say so instead of letting the player walk into silence.
                _nextDeadEndWarningAt = Time.unscaledTime + DeadEndWarningCooldown;
                ShowWarning("There's nothing that way.");
            }
        }

        /// <summary>
        /// Portal travel to any chunk with an explicit spawn point — used by DungeonPortal
        /// for dungeon entrances/exits, unlike edge transitions which derive the spawn side.
        /// </summary>
        public void TravelTo(MapChunkData targetChunk, Vector3 spawnPosition)
        {
            if (_isTransitioning) return;
            StartCoroutine(TravelRoutine(targetChunk, null, spawnPosition));
        }

        /// <summary>
        /// Portal travel that arrives at a named <see cref="PlayerSpawnPoint"/> inside the target
        /// chunk, taking its facing as well as its position.
        ///
        /// A marker is what makes a linked door pair authorable: both ends move with the geometry
        /// they belong to, instead of being two hand-typed world coordinates that quietly stop
        /// matching the building the moment it is nudged.
        ///
        /// ⚠ A non-empty <paramref name="spawnPointId"/> that does not resolve **aborts the
        /// journey** rather than falling back to <paramref name="fallbackPosition"/>. Silently
        /// landing at a raw coordinate is how a typo'd id turns into a player standing inside a
        /// wall with nothing logged. An empty id is the legacy path and uses the position.
        /// </summary>
        public void TravelTo(MapChunkData targetChunk, string spawnPointId, Vector3 fallbackPosition)
        {
            if (_isTransitioning) return;
            StartCoroutine(TravelRoutine(targetChunk, spawnPointId, fallbackPosition));
        }

        private IEnumerator TravelRoutine(MapChunkData targetChunk, string spawnPointId, Vector3 fallbackPosition)
        {
            if (targetChunk == null || targetChunk.ChunkPrefab == null)
            {
                Debug.LogWarning($"ChunkManager: portal target '{(targetChunk != null ? targetChunk.name : "null")}' has no prefab — travel aborted.");
                yield break;
            }
            if (PlayerTransform == null)
            {
                var player = GBHEngland.Combat.CombatController.Instance;
                if (player != null) PlayerTransform = player.transform;
            }
            if (PlayerTransform == null)
            {
                Debug.LogWarning("ChunkManager: no PlayerTransform — travel aborted.");
                yield break;
            }

            // A portal leading INTO a locked-out city must refuse the same way OnPlayerHitEdge
            // already refuses an edge crossing — otherwise a door is a hole in the lockout.
            if (IsCityLockedOut(targetChunk, out float lockoutRemaining))
            {
                Debug.LogWarning($"ChunkManager: '{targetChunk.ChunkName}' is locked out for {Mathf.CeilToInt(lockoutRemaining)}s — portal travel aborted.");
                if (GBHEngland.UI.UIManager.Instance != null)
                    GBHEngland.UI.UIManager.Instance.ShowToast($"Cannot enter {targetChunk.ChunkName}. Police activity active for {Mathf.CeilToInt(lockoutRemaining)}s.", 3f);
                yield break;
            }

            _isTransitioning = true;
            GBHEngland.Systems.PauseManager.Push();
            if (LoadingScreenUI)
            {
                LoadingScreenUI.alpha = 1f;
                LoadingScreenUI.interactable = true;
                LoadingScreenUI.blocksRaycasts = true;
            }

            try
            {
                yield return new WaitForSecondsRealtime(0.15f);

                // The destination is built first and inspected before anything is committed. Every
                // observable change below — wanted state, CurrentChunkData, the visited list, the
                // encyclopedia toast, the autosave — happens only once we know the player has
                // somewhere real to land, so a broken marker id leaves the world exactly as it was.
                //
                // The cost is that an aborted journey still instantiates the whole destination for
                // a frame before destroying it again. Reading the marker off targetChunk.ChunkPrefab
                // instead would avoid that, but would then be validating something other than the
                // instance the player actually lands in — and an abort only happens on an authoring
                // error the validator already reports, so the rare path is the one paying.
                GameObject previousInstance = CurrentChunkInstance;

                // CurrentChunkData is still the origin chunk here and stays that way until the
                // marker resolves below. Content in the candidate runs its Awake inside this
                // Instantiate, so ChunkBeingBuilt is what tells it where it actually is — see the
                // field's remarks. Cleared in the finally, so an abort or an exception cannot leave
                // a stale value behind for the next thing that asks.
                ChunkBeingBuilt = targetChunk;

                // The second of the two paths that count a visit, and before the Instantiate for
                // the same reason as the edge crossing — containers read their cooldown in Awake.
                // Given back on the abort branch below, so a broken marker id costs the player
                // nothing for a journey that never happened. The exact touched-id list is kept
                // (not just the chunk name) so the give-back can't re-lock a container that was
                // already spent before this tick — see IncrementContainerCooldowns's remarks.
                List<string> decrementedContainerIds =
                    GBHEngland.Flow.PlayerSession.Instance?.DecrementContainerCooldowns(targetChunk.ChunkName);

                GameObject candidate = Instantiate(targetChunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
                candidate.name = targetChunk.ChunkPrefab.name;

                Vector3 arrivalPos = fallbackPosition;
                Quaternion? arrivalFacing = null;
                bool aborted = false;

                if (!string.IsNullOrEmpty(spawnPointId))
                {
                    // Strict lookup on purpose — see the TravelTo overload's remarks.
                    PlayerSpawnPoint marker = PlayerSpawnPoint.FindExact(candidate, spawnPointId);
                    if (marker == null)
                    {
                        Debug.LogWarning(
                            $"ChunkManager: '{targetChunk.ChunkName}' has no PlayerSpawnPoint with Id " +
                            $"'{spawnPointId}' — travel aborted, staying in " +
                            $"'{(CurrentChunkData != null ? CurrentChunkData.ChunkName : "nowhere")}'. " +
                            "Check the marker exists in the chunk's PREFAB (not just the scene) and that " +
                            "the id matches exactly, then re-run Tools > Place > Portal Placement " +
                            "> Validate All Location Links.");
                        // Give back the visit counted above: the player never arrived.
                        GBHEngland.Flow.PlayerSession.Instance?.IncrementContainerCooldowns(
                            decrementedContainerIds);
                        Destroy(candidate);
                        aborted = true;
                    }
                    else
                    {
                        arrivalPos = marker.transform.position;
                        arrivalFacing = marker.transform.rotation;
                    }
                }

                if (!aborted)
                {
                    // Read before CurrentChunkData is reassigned — it wants the pair, from and to.
                    // Portal, not EdgeCrossing: a door is not an escape from the police. Every
                    // interior and dungeon in the project carries IsCity: 0, so without this the
                    // player could rob London, step into a shop, and step back out clean.
                    GBHEngland.Systems.WantedManager.Instance?.OnChunkTransition(
                        CurrentChunkData, targetChunk, ChunkTravelKind.Portal);

                    CurrentChunkData = targetChunk;
                    GBHEngland.Flow.PlayerSession.Instance?.MarkChunkVisited(targetChunk.ChunkName);
                    // Toast: portal travel is a live arrival — a first visit is a discovery.
                    GBHEngland.UI.WikiUnlock.GrantForChunk(targetChunk.ChunkName, silent: false);
                    CurrentChunkInstance = candidate;

                    // Portal travel is given its arrival by the caller (DungeonPortal) — either a
                    // named marker resolved above, or an explicit position. Deferring to the chunk's
                    // generic PlayerSpawnPoint here would send every portal into a chunk to the same
                    // single default marker, ignoring what this specific portal was configured with.
                    TeleportPlayer(arrivalPos, arrivalFacing);

                    var camFollow = FindObjectOfType<IsometricCameraFollow>();
                    if (camFollow != null)
                        camFollow.SnapToTarget();

                    if (previousInstance != null)
                        Destroy(previousInstance);

                    _nextEdgeTriggerAllowedAt = Time.unscaledTime + EdgeTriggerGrace;

                    // Save inside the new chunk must be loadable later, so the chunk has to be
                    // findable by name even if the scene's AllChunks list predates it. This only
                    // lasts the run — MapChunkRegistry is what makes it survive a restart.
                    EnsureKnownChunk(targetChunk);
                    if (targetChunk != null && !targetChunk.SuppressCheckpointSaves)
                        GBHEngland.Flow.SaveGameManager.Save();
                }
            }
            finally
            {
                ChunkBeingBuilt = null;
                if (LoadingScreenUI)
                {
                    LoadingScreenUI.alpha = 0f;
                    LoadingScreenUI.interactable = false;
                    LoadingScreenUI.blocksRaycasts = false;
                }
                GBHEngland.Systems.PauseManager.Pop();
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

        /// <summary>
        /// Resolves a saved <see cref="MapChunkData.ChunkName"/> back to its asset.
        ///
        /// The scene's own <see cref="AllChunks"/> is consulted first so nothing already authored
        /// there changes meaning. <see cref="MapChunkRegistry"/> is the fallback, and is what lets
        /// a save made inside an interior load after the app has been closed: interiors are
        /// authored from Prefab Mode, where the scene ChunkManager is not even loaded, and
        /// <see cref="EnsureKnownChunk"/> only patches the list for the current run.
        /// </summary>
        public MapChunkData FindChunkByName(string chunkName)
        {
            if (string.IsNullOrEmpty(chunkName)) return null;

            if (AllChunks != null)
            {
                foreach (MapChunkData c in AllChunks)
                    if (c != null && c.ChunkName == chunkName) return c;
            }

            MapChunkRegistry registry = MapChunkRegistry.Load();
            return registry != null ? registry.Find(chunkName) : null;
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
                var player = GBHEngland.Combat.CombatController.Instance;
                if (player != null) PlayerTransform = player.transform;
            }
            if (PlayerTransform == null)
            {
                Debug.LogWarning("ChunkManager: no PlayerTransform — transition aborted.");
                yield break;
            }

            _isTransitioning = true;
            GBHEngland.Systems.PauseManager.Push();
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

                // Notify Wanted System of transition. EdgeCrossing is the only kind that can shake
                // the police — this is the "got out of town" path.
                GBHEngland.Systems.WantedManager.Instance?.OnChunkTransition(
                    CurrentChunkData, targetChunk, ChunkTravelKind.EdgeCrossing);

                // Instantiate the next chunk BEFORE removing the old one, so there's never a
                // frame where the player has no floor under them.
                GameObject previousInstance = CurrentChunkInstance;
                CurrentChunkData = targetChunk;
                GBHEngland.Flow.PlayerSession.Instance?.MarkChunkVisited(targetChunk.ChunkName);
                // Toast: walking across an edge is a live arrival — a first visit is a discovery.
                GBHEngland.UI.WikiUnlock.GrantForChunk(targetChunk.ChunkName, silent: false);

                // Walking in over an edge is the canonical "you left and came back", so it is one
                // of the two paths that counts a visit against a restockable container. Must happen
                // before the Instantiate below: containers read their cooldown in Awake, and a tick
                // applied afterwards would not be seen until the visit after this one.
                GBHEngland.Flow.PlayerSession.Instance?.DecrementContainerCooldowns(targetChunk.ChunkName);

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
                _nextEdgeTriggerAllowedAt = Time.unscaledTime + EdgeTriggerGrace;

                // Checkpoint: every chunk crossing is a save point.
                if (targetChunk != null && !targetChunk.SuppressCheckpointSaves)
                    GBHEngland.Flow.SaveGameManager.Save();
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
                GBHEngland.Systems.PauseManager.Pop();
                _isTransitioning = false;
            }
        }

        private void RepositionPlayerForTransition(Direction travelDir)
        {
            float mapSize = EKVibe.ChunkSize;
            // The edge triggers sit at ±110.2 (depth 0.8, inner face at ±109.8).
            // A 3.5-unit inward offset lands the player at ±106.5 — roughly three steps
            // from the perimeter, well clear of the 109.8 trigger face even accounting for
            // the player collider radius (~0.5). The 0.25 s unscaled grace period
            // (_nextEdgeTriggerAllowedAt) provides additional anti-loop cover.
            float buffer = 3.5f;
            float limit = mapSize / 2f - buffer;

            // The lateral coordinate carries over from where the player crossed, so crossing
            // near a corner could drop them inside the new chunk's *perpendicular* edge
            // trigger — a chain teleport where that neighbour exists, a dead trigger where it
            // doesn't. Clamping to the same limit keeps arrivals clear of all four edges.
            Vector3 pos = PlayerTransform.position;
            switch(travelDir)
            {
                case Direction.North: pos.z = -limit; pos.x = Mathf.Clamp(pos.x, -limit, limit); break;
                case Direction.South: pos.z =  limit; pos.x = Mathf.Clamp(pos.x, -limit, limit); break;
                case Direction.East:  pos.x = -limit; pos.z = Mathf.Clamp(pos.z, -limit, limit); break;
                case Direction.West:  pos.x =  limit; pos.z = Mathf.Clamp(pos.z, -limit, limit); break;
            }
            TeleportPlayer(pos);
        }

        /// <summary>
        /// Moves the player, keeping the Rigidbody in sync to avoid interpolation ghosting.
        ///
        /// <paramref name="facing"/> is optional and is routed through
        /// <see cref="GBHEngland.Combat.CombatController.FaceTowards"/> rather than written
        /// straight onto the transform: the controller keeps its own facing vector, and the sprite
        /// is flipped from that, so a rotation set behind its back would be reverted by the next
        /// input and would never turn the sprite at all.
        /// </summary>
        public void TeleportPlayer(Vector3 position, Quaternion? facing = null)
        {
            if (PlayerTransform == null) return;

            var rb = PlayerTransform.GetComponent<Rigidbody>();
            if (rb != null)
            {
                rb.position = position;
                rb.velocity = Vector3.zero;
                rb.angularVelocity = Vector3.zero;
            }
            PlayerTransform.position = position;

            if (MountController.IsPlayerRiding && MountController.Current != null && MountController.Current.CurrentVehicle != null)
            {
                var vehicle = MountController.Current.CurrentVehicle;
                vehicle.transform.position = position;
                var vRb = vehicle.GetComponent<Rigidbody>();
                if (vRb != null)
                {
                    vRb.position = position;
                    vRb.velocity = Vector3.zero;
                    vRb.angularVelocity = Vector3.zero;
                }
            }

            if (!facing.HasValue) return;

            Vector3 forward = facing.Value * Vector3.forward;
            forward.y = 0f;
            if (forward.sqrMagnitude < 0.0001f) return; // marker aimed straight up or down

            if (MountController.IsPlayerRiding && MountController.Current != null && MountController.Current.CurrentVehicle != null)
            {
                var vehicle = MountController.Current.CurrentVehicle;
                Quaternion vRot = Quaternion.LookRotation(forward.normalized, Vector3.up);
                var vRb = vehicle.GetComponent<Rigidbody>();
                if (vRb != null) vRb.rotation = vRot;
                vehicle.transform.rotation = vRot;
            }

            var combat = PlayerTransform.GetComponent<GBHEngland.Combat.CombatController>();
            if (combat != null)
            {
                combat.FaceTowards(forward);
            }
            else
            {
                Quaternion rot = Quaternion.LookRotation(forward.normalized, Vector3.up);
                if (rb != null) rb.rotation = rot;
                PlayerTransform.rotation = rot;
            }
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
