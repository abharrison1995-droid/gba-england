using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.Systems;
using ExiledAlvaston.UI;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// One ambient car driving a <see cref="TrafficRoute"/>. Lives on the car prefab root beside a
    /// dormant <see cref="VehicleController"/> + <see cref="Interactable"/> + kinematic
    /// <see cref="Rigidbody"/> + <see cref="BoxCollider"/>.
    ///
    /// Drives the route's waypoints in FixedUpdate, brakes for the player with a pure-math check
    /// (no physics queries, no per-frame allocation), and — while stopped — offers the hotwire
    /// minigame. On success it converts into a normal rideable vehicle and auto-mounts the player;
    /// on timeout it raises the alarm and drives on, hotwire-locked for a cooldown.
    ///
    /// The Interactable is owned here, not by the tool: Awake clears any authored listener and
    /// subscribes TryHotwire, and conversion swaps it to VehicleController.Toggle. This is the
    /// PickpocketInteractable pattern — self-subscribing is the only route that survives, and
    /// owning the event means the swap is unambiguous. (The persistent Toggle call the builder
    /// tool wires is therefore removed at runtime; it is dead wiring, kept only so the prefab
    /// shows a sensible default in the Inspector.)
    /// </summary>
    public class TrafficCar : MonoBehaviour
    {
        [Tooltip("How far ahead of the car the player must be (in the lane) for it to brake.")]
        public float BrakeDistance = EKVibe.TrafficBrakeDistance;

        [Tooltip("Half the lane width. A player inside this and ahead of the car stops it.")]
        public float LaneHalfWidth = EKVibe.TrafficLaneHalfWidth;

        [Tooltip("How long a stopped car waits after the player clears before driving on.")]
        public float ResumeDelay = EKVibe.TrafficResumeDelay;

        [Tooltip("Minimum gap between honk toasts while a car is blocked.")]
        public float HonkInterval = EKVibe.HonkIntervalSeconds;

        private TrafficRoute _route;
        private VehicleController _vehicle;
        private Interactable _interactable;
        private Rigidbody _rb;

        private int _waypointIndex;
        private float _cruiseSpeed;
        private int _hotwireWires;
        private float _hotwireSeconds;
        private string _vehicleName;

        private bool _isHeld;          // stopped for the player (blocked, or in the resume window)
        private float _resumeAt;
        private float _nextHonkAt;
        private bool _converted;       // now a player vehicle; TrafficCar no longer drives it
        private bool _hotwireLocked;
        private float _lockoutUntil;
        private bool _hotwiring;       // the minigame is open; the car must not move

        private void Awake()
        {
            _vehicle = GetComponent<VehicleController>();
            _interactable = GetComponent<Interactable>();
            _rb = GetComponent<Rigidbody>();

            // Own the interactable. RemoveAllListeners guarantees exactly one listener — ours —
            // whatever the builder tool may have wired, so a double-fire is impossible.
            if (_interactable != null)
            {
                _interactable.OnInteract.RemoveAllListeners();
                _interactable.OnInteract.AddListener(TryHotwire);
                _interactable.enabled = false;   // not interactable while driving
            }
        }

        /// <summary>
        /// Called by <see cref="TrafficRoute"/> right after Instantiate. Applies the VehicleData
        /// (name, speed, nickability, prompt, model-visible flag) and caches the traffic tuning.
        /// </summary>
        public void Configure(VehicleData data, TrafficRoute route)
        {
            _route = route;
            if (data == null)
            {
                // A car with no data must still move, or it parks forever at spawn and occupies a
                // MaxAlive slot. Fall back to the default cruise speed and a generic name.
                _cruiseSpeed = 7f;
                _hotwireWires = 3;
                _hotwireSeconds = 6f;
                _vehicleName = "car";
                return;
            }

            _cruiseSpeed = data.TrafficSpeed;
            _hotwireWires = Mathf.Max(1, data.HotwireWires);
            _hotwireSeconds = Mathf.Max(1f, data.HotwireSeconds);
            _vehicleName = string.IsNullOrEmpty(data.VehicleName) ? "car" : data.VehicleName;

            if (_vehicle != null)
                _vehicle.Apply(data);
        }

        private void FixedUpdate()
        {
            if (_converted) return;   // VehicleController owns it now

            // While the hotwire minigame is open the car is frozen, whatever the player does with
            // their feet — sidestepping out of the lane must not let it drive off mid-attempt.
            if (_hotwiring) return;

            // A hotwire-locked car drives straight through — it got away.
            if (_hotwireLocked && Time.time < _lockoutUntil)
            {
                Drive();
                return;
            }

            bool blocked = PlayerInLane();

            if (_isHeld)
            {
                if (blocked)
                {
                    _resumeAt = 0f;
                    HonkIfDue();
                }
                else if (_resumeAt == 0f)
                {
                    _resumeAt = Time.time + ResumeDelay;
                }

                if (_resumeAt > 0f && Time.time >= _resumeAt)
                {
                    _isHeld = false;
                    _resumeAt = 0f;
                    SetInteractable(false);
                }
            }
            else if (blocked)
            {
                _isHeld = true;
                _resumeAt = 0f;
                SetInteractable(true);
                HonkIfDue();
            }
            else
            {
                Drive();
            }
        }

        private void Drive()
        {
            if (_route == null || _route.Waypoints == null || _route.Waypoints.Count == 0) return;

            // Advance past any waypoint we have reached.
            while (_waypointIndex < _route.Waypoints.Count
                   && _route.Waypoints[_waypointIndex] != null
                   && Reached(_route.Waypoints[_waypointIndex].position))
            {
                _waypointIndex++;
            }

            if (_waypointIndex >= _route.Waypoints.Count)
            {
                Destroy(gameObject);   // route end — despawn
                return;
            }

            Vector3 target = _route.Waypoints[_waypointIndex].position;
            Vector3 toTarget = target - transform.position;
            toTarget.y = 0f;

            if (toTarget.sqrMagnitude < 0.0001f)
            {
                _waypointIndex++;
                return;
            }

            // Face travel direction. The model child is authored nose-forward (+Z).
            transform.rotation = Quaternion.LookRotation(toTarget.normalized, Vector3.up);

            Vector3 step = toTarget.normalized * (_cruiseSpeed * Time.fixedDeltaTime);
            if (step.sqrMagnitude > toTarget.sqrMagnitude)
                step = toTarget;   // don't overshoot the waypoint

            if (_rb != null)
                _rb.MovePosition(transform.position + step);
            else
                transform.position += step;
        }

        private bool Reached(Vector3 waypoint)
        {
            Vector3 d = waypoint - transform.position;
            d.y = 0f;
            return d.sqrMagnitude < 0.25f;   // within 0.5 m
        }

        /// <summary>
        /// Pure-math braking check: is the player ahead of the car and inside the lane? No physics
        /// queries, no allocation — the isometric world moves on X/Z, so the check is a single
        /// InverseTransformPoint against the car's forward.
        /// </summary>
        private bool PlayerInLane()
        {
            var player = CombatController.Instance;
            if (player == null) return false;

            Vector3 local = transform.InverseTransformPoint(player.transform.position);
            // local.z is distance ahead (positive = in front), local.x is lateral offset.
            return local.z > 0f && local.z < BrakeDistance && Mathf.Abs(local.x) < LaneHalfWidth;
        }

        private void HonkIfDue()
        {
            if (Time.time < _nextHonkAt) return;
            _nextHonkAt = Time.time + HonkInterval;
            UIManager.Instance?.ShowToast("Beep beep! Get out the road!", 1.5f);
        }

        private void SetInteractable(bool on)
        {
            if (_interactable == null) return;
            _interactable.enabled = on;
        }

        /// <summary>Wired to the Interactable while the car is stopped. Opens the hotwire minigame.</summary>
        public void TryHotwire()
        {
            if (_converted) return;
            if (MountController.IsPlayerRiding)
            {
                UIManager.Instance?.ShowToast("Get off the vehicle first.");
                return;
            }
            if (_hotwireLocked && Time.time < _lockoutUntil)
            {
                UIManager.Instance?.ShowToast("Still hot — the alarm's ringing. Give it a minute.");
                return;
            }

            // Freeze the car for the duration of the attempt, whatever the player does with their
            // feet. The menu's own proximity check closes it if they walk off.
            _hotwiring = true;
            HotwireMenuUI.Show(_vehicleName, _hotwireWires, _hotwireSeconds, transform, OnHotwireClosed);
        }

        private void OnHotwireClosed(bool completed, bool expired)
        {
            _hotwiring = false;

            if (completed)
            {
                ConvertToPlayerVehicle();
                return;
            }

            if (expired)
            {
                // Alarm: attempted theft. One knife, and the car gets away.
                UIManager.Instance?.ShowToast("The alarm's going off! The Fuzz is on to you.", 2.5f);
                WantedManager.Instance?.SpikeKnives();
                _hotwireLocked = true;
                _lockoutUntil = Time.time + EKVibe.HotwireRetryLockoutSeconds;
            }
            // Abandoned (CLOSE / walked off): clean getaway, no knives. The car just drives on.
        }

        /// <summary>
        /// The theft succeeded. The car becomes a normal rideable vehicle and the player is
        /// mounted on it; a random driver villager hops out and wanders off; two knives are
        /// spiked (two officers). From here the existing vehicle stack owns everything.
        /// </summary>
        private void ConvertToPlayerVehicle()
        {
            if (_converted) return;
            _converted = true;

            // Swap the interactable to the standard vehicle entry point.
            if (_interactable != null)
            {
                _interactable.OnInteract.RemoveAllListeners();
                if (_vehicle != null)
                    _interactable.OnInteract.AddListener(_vehicle.Toggle);
                _interactable.enabled = true;
            }

            if (_vehicle == null) return;

            // It's yours now — clear ownership so OnMounted does not spike a third knife, and the
            // dismount prompt reads "Ride the ..." rather than "Nick the ...".
            _vehicle.IsOwnedByNPC = false;
            _vehicle.MarkChunkOwned();

            SpawnFleeingDriver();

            // Witnessed theft: instant 2 knives = two officers (PCSO then Bobby).
            WantedManager.Instance?.SpikeKnives();
            WantedManager.Instance?.SpikeKnives();
            UIManager.Instance?.ShowToast($"Nicked a {_vehicleName}! The Fuzz is on to you.", 2.5f);

            MountController.Get()?.Mount(_vehicle);
        }

        private void SpawnFleeingDriver()
        {
            if (_route == null) return;
            PlacementPreset preset = _route.PickDriver();
            if (preset == null) return;

            // Hop out the side of the car, parented to the live chunk so the driver dies with it.
            Vector3 doorPos = transform.position + transform.right * 1.5f;
            Transform chunk = ChunkManager.Instance != null
                ? ChunkManager.Instance.CurrentChunkInstance?.transform
                : null;

            NpcFactory.Build(preset, doorPos, chunk);
        }
    }
}