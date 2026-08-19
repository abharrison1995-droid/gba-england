using UnityEngine;
using GBHEngland.Combat;
using GBHEngland.Data;
using GBHEngland.Systems;
using GBHEngland.UI;

namespace GBHEngland.World
{
    /// <summary>
    /// Handles the "Grand Theft E-Bike" logic. When the player mounts, they get a speed boost.
    /// If they steal it, the law gets involved.
    ///
    /// Whether the player is riding is owned by <see cref="MountController"/>, not by a bool here.
    /// This component describes the vehicle and applies its own effects when told to.
    /// </summary>
    public class VehicleController : MonoBehaviour
    {
        public string VehicleName = "Vauxhall Corsa";
        public float SpeedMultiplier = 2.0f;
        public bool IsOwnedByNPC = true;

        [Tooltip("The visual model of the parked vehicle to hide when mounted.")]
        public GameObject ParkedModel;

        [Tooltip("Sprite layered over the player while riding. Left empty, whatever the " +
                 "ParkedModel renders is used, so the parked and ridden vehicle always match.")]
        public Sprite VehicleSprite;

        [Tooltip("Left wherever you drop it while you stay in that chunk. Leave the chunk — by " +
                 "edge, door, portal, load or death — and it turns up back where it started.")]
        public bool ReturnsHomeOnChunkChange = true;

        [Tooltip("For a 3D car: keep the model visible while mounted and hide the rider's sprite " +
                 "instead. The e-bike layers a sprite over the rider, so it stays false. Never " +
                 "deactivates the vehicle root — see the SetActive(false) rule.")]
        public bool KeepModelVisibleWhileMounted = false;

        // ── 3D Driveable Physics Tuning ──────────────────────────────────────────────────────
        [Header("3D Driveable Physics")]
        [Tooltip("When true, the vehicle uses its own dynamic Rigidbody and arcade driving physics on X/Z.")]
        public bool IsDriveablePhysics = false;

        public float DriveForce = 45f;
        public float TopSpeed = 16f;
        public float ReverseSpeed = 6f;
        public float BrakeForce = 35f;
        public float SteeringTorque = 12f;
        public float TireGrip = 8f;
        public float HandbrakeDriftSlip = 0.35f;

        [Header("Custom Prompts")]
        public string EnterPrompt = "Get in";
        public string ExitPrompt = "Get out";

        private Interactable _interactable;
        private string _parkedPrompt;

        private Vector3 _homePosition;
        private Quaternion _homeRotation;
        private MapChunkData _parkedChunk;
        private bool _displaced;
        private bool _chunkOwned;

        private Rigidbody _rb;
        private Collider _playerCollider;
        private float _dismountCooldownUntil;

        /// <summary>True while this specific vehicle is the one under the player.</summary>
        public bool IsRidden => MountController.Current != null
                                && MountController.Current.CurrentVehicle == this;

        /// <summary>True when this vehicle controls its own movement rather than relying on player walking sweeps.</summary>
        public bool DrivesItself => IsDriveablePhysics && IsRidden;

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            _parkedPrompt = _interactable != null ? _interactable.Prompt : null;

            _homePosition = transform.position;
            _homeRotation = transform.rotation;

            _rb = GetComponent<Rigidbody>();
        }

        // Polls the live chunk rather than subscribing to a transition event, deliberately.
        // CurrentChunkData is a public serialized field written from seven places across six
        // files — both ChunkManager routines, GameFlowController twice, SaveGameManager,
        // DeathScreenUI and two editor tools — so hooking any one transition path would miss the
        // other three, and converting the field to a property to raise an event would stop Unity
        // serialising the scene's authored starting chunk. A reference compare costs nothing and
        // catches every path, including load-game and the arrest return.
        private void Update()
        {
            // If driven via 3D physics, movement is handled in FixedUpdate.
            // For simple sprite mounts (e.g. e-bike), slave-follow the player transform.
            if (IsRidden)
            {
                if (!IsDriveablePhysics)
                {
                    var rider = CombatController.Instance;
                    if (rider != null)
                    {
                        transform.position = rider.transform.position;
                        transform.rotation = rider.transform.rotation;
                    }
                }
                return;
            }

            // Post-dismount priority recovery
            if (_dismountCooldownUntil > 0f && Time.unscaledTime >= _dismountCooldownUntil)
            {
                _dismountCooldownUntil = 0f;
                if (_interactable != null)
                    _interactable.LowPriority = false;
            }

            if (!ReturnsHomeOnChunkChange || !_displaced) return;

            var chunks = ChunkManager.Instance;
            if (chunks == null || chunks.CurrentChunkData == _parkedChunk) return;

            ReturnHome();
        }

        private struct VehicleInputState
        {
            public float Throttle;
            public float Brake;
            public float SteerAxis;
            public bool HasDirectionalHeading;
            public Vector3 DirectionalHeading;
            public bool Handbrake;
            public bool ExitRequested;
        }

        private VehicleInputState SampleVehicleInputs(CombatController player)
        {
            var state = new VehicleInputState();

            // 1. Desktop Keyboard & Input Axes
            float kbdThrottle = (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) ? 1f : 0f;
            float kbdBrake = (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) ? 1f : 0f;
            float kbdSteer = Input.GetAxisRaw("Horizontal");
            bool kbdHandbrake = Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.LeftShift);
            bool kbdExit = Input.GetKeyDown(KeyCode.E) || Input.GetKeyDown(KeyCode.F);

            // 2. Mobile Touch Pedals from UIManager
            float touchThrottle = UIManager.Instance != null ? UIManager.Instance.TouchThrottle : 0f;
            float touchBrake = UIManager.Instance != null ? UIManager.Instance.TouchBrake : 0f;
            bool touchDrift = UIManager.Instance != null && UIManager.Instance.TouchDrift;

            // 3. Unified Throttle / Brake / Drift Ingestion
            state.Throttle = Mathf.Clamp01(Mathf.Max(kbdThrottle, touchThrottle));
            state.Brake = Mathf.Clamp01(Mathf.Max(kbdBrake, touchBrake));
            state.Handbrake = kbdHandbrake || touchDrift;
            state.ExitRequested = kbdExit;
            state.SteerAxis = kbdSteer;

            // 4. Virtual Joystick Steering / Directional Heading
            Vector2 stickInput = player.ReadMoveInput();
            if (stickInput.sqrMagnitude > 0.01f)
            {
                Vector3 moveDir = CombatController.GetScreenRelativeMoveDirection(stickInput);
                if (moveDir.sqrMagnitude > 0.01f)
                {
                    state.HasDirectionalHeading = true;
                    state.DirectionalHeading = moveDir;

                    // Hybrid single-stick fallback (if player navigates with joystick only without pressing pedals)
                    if (state.Throttle < 0.01f && state.Brake < 0.01f)
                    {
                        float alignment = Vector3.Dot(transform.forward, moveDir);
                        if (alignment >= 0f)
                            state.Throttle = Mathf.Clamp01(stickInput.magnitude * alignment);
                        else if (alignment < -0.2f)
                            state.Brake = Mathf.Clamp01(stickInput.magnitude * -alignment);
                    }
                }
            }

            return state;
        }

        private void FixedUpdate()
        {
            if (!IsRidden || !IsDriveablePhysics) return;

            var player = CombatController.Instance;
            if (player == null) return;

            if (_rb == null)
            {
                _rb = GetComponent<Rigidbody>();
                if (_rb == null) return;
            }

            // Keep Rigidbody constrained to ground plane on X/Z
            _rb.constraints = RigidbodyConstraints.FreezeRotationX |
                              RigidbodyConstraints.FreezeRotationZ |
                              RigidbodyConstraints.FreezePositionY;

            VehicleInputState inputs = SampleVehicleInputs(player);
            if (inputs.ExitRequested)
            {
                Unmount();
                return;
            }

            Vector3 vel = _rb.velocity;
            float vFwd = Vector3.Dot(vel, transform.forward);
            float vLat = Vector3.Dot(vel, transform.right);

            // ── 1. Decoupled Steering ────────────────────────────────────────────────────────
            float steerFactor = 0f;
            if (inputs.HasDirectionalHeading)
            {
                float targetAngle = Vector3.SignedAngle(transform.forward, inputs.DirectionalHeading, Vector3.up);
                steerFactor = Mathf.Clamp(targetAngle / 45f, -1f, 1f);
            }
            else if (Mathf.Abs(inputs.SteerAxis) > 0.01f)
            {
                steerFactor = inputs.SteerAxis;
            }

            if (Mathf.Abs(steerFactor) > 0.01f)
            {
                // Speed-scaled steering rate (maneuverable at low speed, stable at high speed)
                float speedTurnScale = Mathf.Clamp01(Mathf.Abs(vFwd) / 2.0f);
                if (Mathf.Abs(vFwd) < 0.5f && (inputs.Throttle > 0.1f || inputs.Brake > 0.1f))
                    speedTurnScale = 0.45f; // Low-speed parking assist

                // Reverse gear inverts steering response
                if (vFwd < -0.5f) steerFactor = -steerFactor;

                float steerTorque = steerFactor * SteeringTorque * speedTurnScale;
                _rb.AddTorque(Vector3.up * steerTorque, ForceMode.Acceleration);
            }
            else
            {
                _rb.angularVelocity = Vector3.MoveTowards(_rb.angularVelocity, Vector3.zero, 12f * Time.fixedDeltaTime);
            }

            // ── 2. Decoupled Forward Drive Force ─────────────────────────────────────────────
            if (inputs.Throttle > 0.01f)
            {
                float speedRatio = Mathf.Clamp01(Mathf.Max(0f, vFwd) / TopSpeed);
                float forceFactor = Mathf.Pow(1f - speedRatio, 1.6f);
                float driveForce = inputs.Throttle * DriveForce * forceFactor;
                _rb.AddForce(transform.forward * driveForce, ForceMode.Acceleration);
            }

            // ── 3. Decoupled Active Braking & Reverse Gear ────────────────────────────────────
            if (inputs.Brake > 0.01f)
            {
                if (vFwd > 0.5f)
                {
                    // Active counter-force braking
                    _rb.AddForce(-transform.forward * (inputs.Brake * BrakeForce), ForceMode.Acceleration);
                }
                else
                {
                    // Reverse gear propulsion
                    float revRatio = Mathf.Clamp01(Mathf.Max(0f, -vFwd) / ReverseSpeed);
                    float revFactor = 1f - revRatio;
                    float revForce = inputs.Brake * (DriveForce * 0.65f) * revFactor;
                    _rb.AddForce(-transform.forward * revForce, ForceMode.Acceleration);
                }
            }

            // ── 4. Coasting & Rolling Resistance ──────────────────────────────────────────────
            if (inputs.Throttle <= 0.01f && inputs.Brake <= 0.01f)
            {
                if (Mathf.Abs(vFwd) > 0.05f)
                    _rb.AddForce(-transform.forward * (vFwd * 3.0f), ForceMode.Acceleration);
                else
                    _rb.velocity = new Vector3(0f, _rb.velocity.y, 0f);
            }

            // ── 5. Lateral Tire Friction & Handbrake Drift ────────────────────────────────────
            float effectiveGrip = inputs.Handbrake ? (TireGrip * Mathf.Clamp01(HandbrakeDriftSlip)) : TireGrip;
            _rb.AddForce(-transform.right * (vLat * effectiveGrip), ForceMode.Acceleration);

            if (inputs.Handbrake && Mathf.Abs(vFwd) > 1.5f)
                _rb.AddForce(-transform.forward * (BrakeForce * 0.35f), ForceMode.Acceleration);

            // Sync player transform to vehicle
            player.transform.position = transform.position;
            player.transform.rotation = transform.rotation;
        }

        /// <summary>
        /// Configures this instance from a VehicleData asset. Called by VehicleSpawner right after
        /// Instantiate, so it runs after Awake and has to refresh the cached parked prompt too.
        /// </summary>
        public void Apply(VehicleData data)
        {
            if (data == null) return;

            VehicleName     = string.IsNullOrEmpty(data.VehicleName) ? VehicleName : data.VehicleName;
            SpeedMultiplier = data.SpeedMultiplier;
            IsOwnedByNPC    = data.IsNickable;
            KeepModelVisibleWhileMounted = data.KeepModelVisibleWhileMounted;

            IsDriveablePhysics = data.IsDriveablePhysics;
            DriveForce         = data.DriveForce;
            TopSpeed           = data.TopSpeed;
            ReverseSpeed       = data.ReverseSpeed;
            BrakeForce         = data.BrakeForce;
            SteeringTorque     = data.SteeringTorque;
            TireGrip           = data.TireGrip;
            HandbrakeDriftSlip = data.HandbrakeDriftSlip;
            EnterPrompt        = string.IsNullOrEmpty(data.EnterPrompt) ? EnterPrompt : data.EnterPrompt;
            ExitPrompt         = string.IsNullOrEmpty(data.ExitPrompt) ? ExitPrompt : data.ExitPrompt;

            if (data.VehicleSprite != null)
            {
                VehicleSprite = data.VehicleSprite;
                ApplyParkedArt(data.VehicleSprite, data.ParkedHeight);
            }

            if (_interactable != null && !string.IsNullOrEmpty(data.ParkedPrompt))
            {
                _parkedPrompt = data.ParkedPrompt;
                _interactable.Prompt = data.ParkedPrompt;
            }
        }

        private void ApplyParkedArt(Sprite sprite, float parkedHeight)
        {
            if (ParkedModel == null) return;

            var sr = ParkedModel.GetComponentInChildren<SpriteRenderer>(true);
            if (sr == null) return;

            sr.sprite = sprite;

            float spriteH = sprite.bounds.size.y;
            if (spriteH < 0.001f || parkedHeight <= 0f) return;

            sr.transform.localScale = Vector3.one * (parkedHeight / spriteH);
            sr.transform.localPosition = new Vector3(0f, parkedHeight * 0.5f, 0f);
        }

        /// <summary>
        /// Marks this instance as belonging to the chunk that spawned it: it dies with that chunk
        /// and is respawned from the chunk's data next visit, so it needs no homing of its own.
        /// Hand-placed vehicles left in the scene are not chunk-owned and keep ReturnHome.
        /// </summary>
        public void MarkChunkOwned()
        {
            _chunkOwned = true;
        }

        /// <summary>Back to where it was standing when the scene loaded.</summary>
        public void ReturnHome()
        {
            transform.position = _homePosition;
            transform.rotation = _homeRotation;
            _parkedChunk = null;
            _displaced = false;
        }

        /// <summary>
        /// Gating check hook before mounting. Subclasses or future perk/lockpick systems can override this.
        /// </summary>
        public virtual bool CanMount(CombatController player, out string reason)
        {
            reason = null;
            return true;
        }

        /// <summary>
        /// Interact entry point, wired to Interactable.OnInteract. Mounts when parked and gets you
        /// off when you are already on it, so one prompt covers both.
        /// </summary>
        public void Toggle()
        {
            var mount = MountController.Get();
            if (mount == null) return;

            if (mount.CurrentVehicle == this)
            {
                mount.Dismount();
            }
            else if (!mount.IsMounted)
            {
                if (!CanMount(CombatController.Instance, out string reason))
                {
                    if (!string.IsNullOrEmpty(reason))
                        UIManager.Instance?.ShowToast(reason);
                    return;
                }
                mount.Mount(this);
            }
            else
            {
                UIManager.Instance?.ShowToast($"Get out of the {mount.CurrentVehicle.VehicleName} first.");
            }
        }

        public void Mount()
        {
            MountController.Get()?.Mount(this);
        }

        /// <summary>Step off: drops the vehicle where the player is standing and gives back their speed.</summary>
        public void Unmount()
        {
            var mount = MountController.Current;
            if (mount != null && mount.CurrentVehicle == this)
                mount.Dismount();
        }

        /// <summary>Applies this vehicle's effects. Called by MountController, which owns the state.</summary>
        public void OnMounted(CombatController player)
        {
            if (IsOwnedByNPC)
            {
                // Grand Theft Auto!
                WantedManager.Instance?.SpikeKnives();
                UIManager.Instance?.ShowToast($"Nicked a {VehicleName}! The Fuzz is on to you.");
                IsOwnedByNPC = false; // it's yours now
            }
            else
            {
                string boardVerb = KeepModelVisibleWhileMounted ? "Got into" : "Hopped onto";
                UIManager.Instance?.ShowToast($"{boardVerb} the {VehicleName}.");
            }

            // Resolved before the model is hidden, so the ridden sprite always matches the parked one.
            Sprite ridden = ResolveVehicleSprite();

            if (KeepModelVisibleWhileMounted)
            {
                // A 3D car: the model is the bodywork, so it stays up and the rider's billboard is
                // hidden instead. Never SetActive the root — that fires OnDisable below, and the
                // vehicle would cancel its own boost the instant it was mounted.
                if (player != null)
                    player.GetComponent<WorldActorVisual>()?.SetRiderHidden(true);
            }
            else
            {
                // Hide the parked model only. Never SetActive the root: that fires OnDisable below,
                // and the vehicle would cancel its own boost the instant it was mounted.
                if (ParkedModel != null && ParkedModel != gameObject)
                    ParkedModel.SetActive(false);
            }

            if (player != null)
            {
                if (IsDriveablePhysics)
                {
                    // Disable player capsule collider and set Rigidbody kinematic to avoid physics conflicts
                    _playerCollider = player.GetComponent<Collider>();
                    if (_playerCollider != null)
                        _playerCollider.enabled = false;

                    var playerRb = player.GetComponent<Rigidbody>();
                    if (playerRb != null)
                        playerRb.isKinematic = true;

                    if (_rb != null)
                    {
                        _rb.isKinematic = false;
                        _rb.useGravity = false;
                    }
                }
                else
                {
                    player.SetSpeedMultiplier(this, SpeedMultiplier);
                    player.GetComponent<WorldActorVisual>()?.SetMounted(true, ridden);
                }
            }

            // A chunk-owned vehicle is a child of the chunk instance, which a transition destroys.
            // Riding out from under yourself is not the intent, so it leaves the chunk while ridden
            // and rejoins one on dismount.
            if (_chunkOwned)
                transform.SetParent(null, true);

            ApplyPrompt(true);
        }

        /// <summary>Undoes <see cref="OnMounted"/>. Called by MountController, which owns the state.</summary>
        public void OnDismounted(CombatController player)
        {
            if (player != null)
            {
                if (IsDriveablePhysics)
                {
                    // Stop car motion
                    if (_rb != null)
                    {
                        _rb.velocity = Vector3.zero;
                        _rb.angularVelocity = Vector3.zero;
                    }

                    // Calculate safe lateral exit position beside the car
                    Vector3 exitPos = ResolveDismountPosition(player.transform.position);
                    player.transform.position = exitPos;

                    var playerRb = player.GetComponent<Rigidbody>();
                    if (playerRb != null)
                    {
                        playerRb.isKinematic = false;
                        playerRb.velocity = Vector3.zero;
                    }

                    if (_playerCollider != null)
                    {
                        _playerCollider.enabled = true;
                        _playerCollider = null;
                    }
                }
                else
                {
                    player.ClearSpeedMultiplier(this);
                    player.GetComponent<WorldActorVisual>()?.SetMounted(false, null);
                    transform.position = player.transform.position;
                }

                var chunks = ChunkManager.Instance;
                if (_chunkOwned)
                {
                    // Hand it to whichever chunk you abandoned it in. It dies with that chunk and
                    // the spawner puts a fresh one at its authored spot next visit — which is the
                    // "back where it started" behaviour, without anything having to teleport.
                    if (chunks != null && chunks.CurrentChunkInstance != null)
                        transform.SetParent(chunks.CurrentChunkInstance.transform, true);
                }
                else
                {
                    // Hand-placed in the scene: nothing will destroy it, so it homes itself.
                    _parkedChunk = chunks != null ? chunks.CurrentChunkData : null;
                    _displaced = true;
                }
            }

            if (KeepModelVisibleWhileMounted)
            {
                // Bring the rider back — the model never left.
                if (player != null)
                    player.GetComponent<WorldActorVisual>()?.SetRiderHidden(false);
            }
            else if (ParkedModel != null && ParkedModel != gameObject)
            {
                ParkedModel.SetActive(true);
            }

            ApplyPrompt(false);

            // Temporary low-priority cooldown on stationary car to avoid prompt masking
            if (_interactable != null)
            {
                _interactable.LowPriority = true;
                _dismountCooldownUntil = Time.unscaledTime + 1.2f;
            }

            string exitVerb = KeepModelVisibleWhileMounted ? "Got out of" : "Hopped off";
            UIManager.Instance?.ShowToast($"{exitVerb} the {VehicleName}.");
        }

        private static readonly Collider[] _dismountOverlapBuffer = new Collider[16];

        /// <summary>
        /// Calculates a safe exit position beside the car using overlap checks.
        /// </summary>
        private Vector3 ResolveDismountPosition(Vector3 carPosition)
        {
            float sideOffset = 1.6f;
            Vector3 rightCandidate = carPosition + transform.right * sideOffset;
            Vector3 leftCandidate = carPosition - transform.right * sideOffset;

            // Check right side clearance
            if (IsDismountPositionClear(rightCandidate))
                return rightCandidate;

            // Check left side clearance
            if (IsDismountPositionClear(leftCandidate))
                return leftCandidate;

            // Fallback: behind the car
            Vector3 rearCandidate = carPosition - transform.forward * 2.2f;
            if (IsDismountPositionClear(rearCandidate))
                return rearCandidate;

            // Fallback: in front of the car
            Vector3 frontCandidate = carPosition + transform.forward * 2.2f;
            if (IsDismountPositionClear(frontCandidate))
                return frontCandidate;

            return rightCandidate;
        }

        private bool IsDismountPositionClear(Vector3 position)
        {
            int count = Physics.OverlapSphereNonAlloc(
                position + Vector3.up * 0.5f,
                0.35f,
                _dismountOverlapBuffer,
                Physics.AllLayers,
                QueryTriggerInteraction.Ignore);

            CombatController player = CombatController.Instance;
            Transform playerTransform = player != null ? player.transform : null;

            for (int i = 0; i < count; i++)
            {
                Collider col = _dismountOverlapBuffer[i];
                if (col == null) continue;

                // Ignore vehicle colliders
                if (col.transform == transform || col.transform.IsChildOf(transform))
                    continue;

                // Ignore player colliders
                if (col == _playerCollider || (playerTransform != null && (col.transform == playerTransform || col.transform.IsChildOf(playerTransform))))
                    continue;

                // Hit a real external obstacle
                return false;
            }

            return true;
        }

        /// <summary>The sprite to draw over the rider. Reads the parked model's own art by default.</summary>
        private Sprite ResolveVehicleSprite()
        {
            if (VehicleSprite != null) return VehicleSprite;
            if (ParkedModel == null) return null;

            var sr = ParkedModel.GetComponentInChildren<SpriteRenderer>(true);
            return sr != null ? sr.sprite : null;
        }

        private void ApplyPrompt(bool mounted)
        {
            if (_interactable == null) return;

            if (mounted)
            {
                _interactable.Prompt = KeepModelVisibleWhileMounted ? $"{ExitPrompt} the {VehicleName}" : $"Get off the {VehicleName}";
                // Rides at distance zero, so without this it masks every pub, door and NPC.
                _interactable.LowPriority = true;
            }
            else
            {
                if (IsOwnedByNPC)
                {
                    _interactable.Prompt = _parkedPrompt;
                }
                else
                {
                    _interactable.Prompt = KeepModelVisibleWhileMounted ? $"{EnterPrompt} the {VehicleName}" : $"Ride the {VehicleName}";
                }
                _interactable.LowPriority = false;
            }
        }

        // Without this the boost outlives the vehicle: chunk transitions destroy the whole chunk,
        // so a mounted vehicle would vanish with its multiplier still registered. The ride state is
        // dropped too — leaving it set made the vehicle permanently half-mounted if it came back.
        private void OnDisable()
        {
            // During scene teardown the singletons may already be gone. The cleanup
            // is unnecessary anyway — the entire scene is being torn down.
            if (!gameObject.scene.isLoaded) return;

            if (!IsRidden) return;

            var player = CombatController.Instance;
            if (player != null)
            {
                player.ClearSpeedMultiplier(this);
                player.GetComponent<WorldActorVisual>()?.SetMounted(false, null);
                // A 3D car hides the rider, not the model — so the rider must come back here too,
                // or a chunk transition would leave the player invisible.
                player.GetComponent<WorldActorVisual>()?.SetRiderHidden(false);

                if (_playerCollider != null)
                {
                    _playerCollider.enabled = true;
                    _playerCollider = null;
                }

                var playerRb = player.GetComponent<Rigidbody>();
                if (playerRb != null)
                    playerRb.isKinematic = false;
            }

            if (ParkedModel != null && ParkedModel != gameObject)
                ParkedModel.SetActive(true);

            ApplyPrompt(false);
            MountController.Current?.ForgetVehicle(this);
        }
    }
}