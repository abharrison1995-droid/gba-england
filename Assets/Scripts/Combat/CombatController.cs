using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.EventSystems;
using GBHEngland.Data;
using GBHEngland.UI;
using GBHEngland.Vibe;
using GBHEngland.World;

namespace GBHEngland.Combat
{
    [RequireComponent(typeof(Rigidbody))]
    public class CombatController : MonoBehaviour
    {
        /// <summary>Cached player reference — avoids FindObjectOfType in hot paths (EnemyAI, UI).</summary>
        public static CombatController Instance { get; private set; }

        [Header("References")]
        public CharacterData PlayerData;
        public Animator PlayerAnimator;
        public Transform AttackPoint;
        public VirtualJoystick Joystick;
        private Rigidbody _rb;
        private Health _health;
        private WorldActorVisual _actorVisual;
        private PlayerHealthBar _bar;
        private RuntimeAnimatorController _animatorParamsFor;
        private bool _hasSpeedParam;
        private bool _hasCyclingParam;

        [Header("Movement")]
        [Tooltip("Base walk speed. Treat as read-only at runtime — apply temporary changes through " +
                 "SetSpeedMultiplier so two systems can't corrupt each other's idea of 'normal'.")]
        public float MovementSpeed = 5f;

        [Header("Combat Stats")]
        public int CurrentHealth;
        public int CurrentMana;
        public int CurrentStamina;

        [Header("Melee Timing")]
        [Tooltip("Seconds after the swing starts before the hitbox fires.")]
        public float MeleeHitDelay = 0.15f;
        [Tooltip("Seconds after the hitbox before you can move/attack again.")]
        public float MeleeRecovery = 0.35f;

        [Header("Melee Cleave Hitbox")]
        [Tooltip("Maximum horizontal reach in metres from player origin.")]
        public float MeleeRange = 1.95f;
        [Tooltip("Total frontal attack arc in degrees (180 = full semicircle, 120 = focused cone).")]
        [Range(60f, 360f)]
        public float MeleeArcAngle = 180f;
        [Tooltip("Radius around player where enemies are hit regardless of angle (point-blank grace).")]
        public float PointBlankRange = 0.45f;

        [Header("Dodge Roll")]
        [Tooltip("Percent of MAXIMUM stamina spent per roll. 50 means exactly two rolls from full " +
                 "at every level, because the price scales with the pool. See CurrentRollCost.")]
        public float RollStaminaPercent = 50f;
        [Tooltip("Fallback flat cost, used only before a session binds and PlayerData still points " +
                 "at the template — the title screen and the character creator. In play the " +
                 "percent above is what is charged.")]
        public int RollStaminaCost = 14;
        [Tooltip("Seconds the roll lasts.")]
        public float RollDuration = 0.40f;
        [Tooltip("Metres covered, averaging ~6 u/s against a 5 u/s walk.")]
        public float RollDistance = 2.4f;
        [Tooltip("Seconds into the roll before i-frames begin — a little startup, so a panic-tap isn't free.")]
        public float RollIFrameStart = 0.05f;
        [Tooltip("Seconds of invulnerability once they begin.")]
        public float RollIFrameDuration = 0.25f;
        [Tooltip("Seconds from the roll's START before another can begin.")]
        public float RollCooldown = 1f;

        [Header("Knockback")]
        [Tooltip("Seconds of i-frames granted as a knockback slide ends, so two enemies cannot " +
                 "chain-stun the player.")]
        public float KnockbackRecoveryIFrames = 0.4f;

        [Header("Regen")]
        // ⚠ Mana does NOT regenerate. There is deliberately no ManaRegenPerSecond field: mana comes
        // back only through items, the pub's full restore, or a heal spell once one exists. The
        // old 2.5/s field is retired, and its orphan key in c.unity is ignored on load and dropped
        // on the scene's next save. If mana regen ever returns it must be a new design decision,
        // not a quiet resurrection of the stale value.
        [Tooltip("Stamina restored per second, as a PERCENT of maximum. A percent and not a flat " +
                 "rate because the roll costs a percent too: a flat rate would make dodge recovery " +
                 "slower at every level as the pool grew. 5 repays one roll in ~10s, a full pool " +
                 "in ~20s. Scaled by the ResourceRegenPercent perk.")]
        public float StaminaRegenPercentPerSecond = 5f;

        [Header("Abilities")]
        public List<AbilityData> EquippedAbilities;

        private Dictionary<string, float> _abilityCooldowns = new Dictionary<string, float>();
        private List<string> _activeCooldownKeys = new List<string>(10);

        private bool _isAttacking;
        private bool _isRolling;
        private bool _isKnockedBack;
        private float _nextRollTime;
        private float _invulnerableUntil;
        private bool _isDead;
        private readonly Collider[] _hitResults = new Collider[32];
        private readonly HashSet<Health> _hitThisSwing = new HashSet<Health>();
        private float _staminaRegenCarry;
        /// <summary>Last non-zero move direction — melee aims this way while idle.</summary>
        private Vector3 _facingDir = Vector3.forward;

        public Vector3 FacingDirection => _facingDir;
        public bool IsDead => _isDead;

        /// <summary>
        /// True while incoming damage should be refused outright — read by <see cref="Health"/>.
        ///
        /// ⚠ Backed by a timestamp, not a bool. More than one thing will want to grant i-frames —
        /// the roll now, the recovery after a knockback next — and two coroutines setting and
        /// clearing one shared flag is exactly how a player ends up permanently invulnerable when
        /// the two overlap. Whoever wants the longer window wins by writing the later time, and
        /// nothing has to clear anything.
        /// </summary>
        public bool IsInvulnerable => Time.time < _invulnerableUntil;

        private void Awake()
        {
            Instance = this;
            _rb = GetComponent<Rigidbody>();
            _health = GetComponent<Health>();
            _actorVisual = GetComponent<WorldActorVisual>();
            // ⚠ Cached, not looked up per hit. FindObjectOfType at a damage site would scan the
            // scene on every swing; a static would be one more lifetime to get wrong. This is what
            // EnemyAI does for its own Health and WorldActorVisual.
            _bar = GetComponent<PlayerHealthBar>();
            _rb.constraints = RigidbodyConstraints.FreezeRotationX | RigidbodyConstraints.FreezeRotationZ;

            if (PlayerData != null)
            {
                CurrentHealth = PlayerData.MaxHealth;
                CurrentMana = PlayerData.MaxManaStamina;
                CurrentStamina = PlayerData.MaxManaStamina;
                if (_health != null)
                {
                    _health.MaxHealth = PlayerData.MaxHealth;
                    _health.CurrentHealth = PlayerData.MaxHealth;
                    _health.DisplayName = PlayerData.CharacterName;
                }
            }

            if (_health != null)
            {
                // GameFlow owns player death — never destroy the player object
                _health.DestroyOnDeath = false;
                _health.OnTakeDamage.AddListener(OnHealthDamaged);
                _health.OnDeath.AddListener(OnHealthDeath);
            }
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;

            var session = Flow.PlayerSession.Instance;
            if (session != null) session.OnStatsChanged -= OnSessionStatsChanged;
        }

        public void BindSessionStats(Flow.PlayerSession session)
        {
            if (session == null) return;
            session.OnStatsChanged -= OnSessionStatsChanged;
            session.OnStatsChanged += OnSessionStatsChanged;
            OnSessionStatsChanged();
        }

        private void Start()
        {
            // Bind to session if it exists at Start; GameFlowController.BindPlayerToSession also binds explicitly.
            BindSessionStats(Flow.PlayerSession.Instance);

            if (Joystick == null && UIManager.Instance != null)
                Joystick = UIManager.Instance.Joystick;

            // Default face "down-screen" / camera-forward so first attack isn't arbitrary world +Z
            Vector3 initial = GetScreenRelativeMoveDirection(Vector2.up);
            if (initial.sqrMagnitude > 0.001f)
                SetFacing(initial);

            PushHud();
        }

        private void OnDisable()
        {
            _isAttacking = false;
            _isRolling = false;
            _isKnockedBack = false;
            _invulnerableUntil = 0f;
        }

        /// <summary>False on Title/Creator — the player must not move, attack, or regen there.</summary>
        private static bool IsFlowPlaying()
        {
            var flow = GBHEngland.Flow.GameFlowController.Instance;
            return flow == null || flow.State == GBHEngland.Flow.GameFlowState.Playing;
        }

        private void Update()
        {
            if (!IsFlowPlaying()) return;
            // Time.timeScale=0 during a paused menu/dialogue doesn't stop Update() — without this,
            // spell/attack input still fires (and mana/cooldowns still get spent) while a menu is open.
            if (Systems.PauseManager.IsPaused) return;

            ProcessCooldowns();
            if (!_isDead)
            {
                RegenResources();
                HandleInput();
            }
            PushHud();
        }

        private void FixedUpdate()
        {
            if (!IsFlowPlaying()) return;

            // The roll and the knockback slide drive the body themselves, so normal movement must
            // not fight them for the Rigidbody during those frames.
            if (!_isAttacking && !_isRolling && !_isKnockedBack && !_isDead)
                HandleMovement();
        }

        /// <summary>
        /// Stamina only. ⚠ Mana is deliberately absent and must stay absent — it is replenished by
        /// items, the pub's full restore and (once one exists) a heal spell, never by a tick. That
        /// is the whole point of the survival-pressure pass; re-adding a mana tick here silently
        /// undoes it.
        /// </summary>
        private void RegenResources()
        {
            int max = PlayerData != null ? PlayerData.MaxManaStamina : 50;

            // The perk multiplier is read here rather than baked into the rate field at
            // OnSessionStatsChanged, because the rate is now a percent of a maximum that itself
            // moves with level and perks — there is no longer a stable "authored rate" worth
            // remembering separately, and multiplying the live field would compound per recompute.
            // One static-property read and three multiplies; no allocation, which this Update path
            // requires.
            var session = Flow.PlayerSession.Instance;
            float multiplier = session != null ? session.ResourceRegenMultiplier : 1f;

            // The integer carry is what makes a fractional rate work against an int pool — 5% of
            // 55 is 2.75/s, which would otherwise floor to 2 every second and quietly lose 27%.
            _staminaRegenCarry += StaminaRegenPercentPerSecond * multiplier * max / 100f * Time.deltaTime;
            if (_staminaRegenCarry >= 1f)
            {
                int whole = Mathf.FloorToInt(_staminaRegenCarry);
                _staminaRegenCarry -= whole;
                CurrentStamina = Mathf.Min(max, CurrentStamina + whole);
            }
        }

        /// <summary>
        /// Pushes the session's freshly derived stats onto the running player. Fires on every
        /// <see cref="Flow.PlayerSession.OnStatsChanged"/> — new game, load, level-up, perk spend.
        /// </summary>
        private void OnSessionStatsChanged()
        {
            var session = Flow.PlayerSession.Instance;
            if (session == null) return;

            var stats = session.RuntimeStats;
            if (stats != null)
            {
                if (_health != null)
                {
                    int newMax = stats.MaxHealth;
                    int delta = newMax - _health.MaxHealth;
                    _health.MaxHealth = newMax;

                    // Levelling GRANTS the new hit points rather than being a free full heal. That
                    // is a design choice, not an oversight — do not "fix" it into a full heal.
                    // Skipped while dead so a kill landing on the same frame as death cannot put a
                    // corpse back above zero behind the death screen's back.
                    if (delta > 0 && _health.CurrentHealth > 0)
                        _health.CurrentHealth = Mathf.Min(newMax, _health.CurrentHealth + delta);
                    else if (_health.CurrentHealth > newMax)
                        _health.CurrentHealth = newMax;

                    CurrentHealth = _health.CurrentHealth;
                }

                // Both are clamped against MaxManaStamina wherever they are spent or regenerated,
                // so a lowered maximum must not leave them reading over it.
                CurrentMana = Mathf.Min(CurrentMana, stats.MaxManaStamina);
                CurrentStamina = Mathf.Min(CurrentStamina, stats.MaxManaStamina);
            }

            // ⚠ Through the modifier system, never by writing MovementSpeed — that field is the
            // authored baseline crouching and vehicles compose against, and overwriting it is
            // exactly the bug _speedModifiers exists to prevent. Keyed by the session, so this
            // replaces its own previous entry instead of stacking a new one each level.
            SetSpeedMultiplier(session, session.MoveSpeedMultiplier);

            PushHud();
        }

        private void PushHud()
        {
            if (UIManager.Instance == null) return;

            int hp = _health != null ? _health.CurrentHealth : CurrentHealth;
            int hpMax = _health != null ? _health.MaxHealth : (PlayerData != null ? PlayerData.MaxHealth : 100);
            CurrentHealth = hp;

            UIManager.Instance.UpdatePlayerHealth(hp, hpMax);
            UIManager.Instance.UpdatePlayerMana(CurrentMana, PlayerData != null ? PlayerData.MaxManaStamina : 50);
            UIManager.Instance.UpdatePlayerStamina(CurrentStamina, PlayerData != null ? PlayerData.MaxManaStamina : 50);
        }

        private void HandleInput()
        {
#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            // Desktop fallback only — mobile uses HUD ATK button.
            // Skip clicks that land on UI so HUD taps don't also swing.
            if (Input.GetButtonDown("Fire1") && !_isAttacking && !IsPointerOverUI())
                PerformMeleeAttack();

            // Desktop fallback only — mobile uses the HUD DGE button.
            if (Input.GetKeyDown(KeyCode.Space) && !IsPointerOverUI())
                PerformDodge();
#endif
            if (Input.GetKeyDown(KeyCode.Alpha1)) TryCastAbility(0);
            if (Input.GetKeyDown(KeyCode.Alpha2)) TryCastAbility(1);
            if (Input.GetKeyDown(KeyCode.Alpha3)) TryCastAbility(2);
            if (Input.GetKeyDown(KeyCode.Alpha4)) TryCastAbility(3);
#if UNITY_EDITOR
            // Dev shortcut: learn Spark and name it (the quest does this properly later). Cast with 1.
            if (Input.GetKeyDown(KeyCode.M))
            {
                if (!KnowsSpark) LearnSpark();
                UI.SpellNamingUI.Show();
            }
#endif
        }

        private static bool IsPointerOverUI()
        {
            return EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
        }

        #region Movement speed modifiers
        // Crouching and vehicles both want to scale move speed. When each one multiplied
        // MovementSpeed in place and cached its own "original", mounting a moped while crouched
        // wrote the boosted value back as the new normal. Modifiers are keyed by source instead,
        // so they compose and unregister cleanly in any order.
        private readonly Dictionary<Object, float> _speedModifiers = new Dictionary<Object, float>();
        private float _speedProduct = 1f;

        // Temporary armour uses the same source-keyed composition as movement speed. Iron Skin
        // must never write PlayerSession's permanent equipment/perk values in place.
        private readonly Dictionary<Object, int> _temporaryArmour = new Dictionary<Object, int>();
        private int _temporaryArmourTotal;

        /// <summary>Base speed with every registered modifier applied.</summary>
        public float EffectiveMovementSpeed => MovementSpeed * _speedProduct;

        /// <summary>Temporary spell armour added to PlayerSession.EffectiveArmour at hit time.</summary>
        public int TemporaryArmourBonus => _temporaryArmourTotal;

        /// <summary>Register or replace <paramref name="source"/>'s speed multiplier.</summary>
        public void SetSpeedMultiplier(Object source, float multiplier)
        {
            if (source == null) return;
            _speedModifiers[source] = multiplier;
            RecomputeSpeedProduct();
        }

        /// <summary>Remove <paramref name="source"/>'s multiplier, if it had one.</summary>
        public void ClearSpeedMultiplier(Object source)
        {
            if (source == null) return;
            if (_speedModifiers.Remove(source))
                RecomputeSpeedProduct();
        }

        public void SetTemporaryArmour(Object source, int bonus)
        {
            if (source == null) return;
            _temporaryArmour[source] = Mathf.Max(0, bonus);
            RecomputeTemporaryArmour();
        }

        public void ClearTemporaryArmour(Object source)
        {
            if (source == null) return;
            if (_temporaryArmour.Remove(source))
                RecomputeTemporaryArmour();
        }

        // Cached rather than recomputed per FixedUpdate — the dictionary walk would allocate an
        // enumerator every physics step, and this project keeps hot paths allocation-free.
        private void RecomputeSpeedProduct()
        {
            float product = 1f;
            foreach (var kv in _speedModifiers)
                product *= kv.Value;
            _speedProduct = product;
        }

        private void RecomputeTemporaryArmour()
        {
            int total = 0;
            foreach (var kv in _temporaryArmour)
                total += kv.Value;
            _temporaryArmourTotal = Mathf.Max(0, total);
        }
        #endregion

        private void HandleMovement()
        {
            if (MountController.Current != null && MountController.Current.CurrentVehicle != null && MountController.Current.CurrentVehicle.DrivesItself)
            {
                ApplyLocomotionAnimation(0f);
                return;
            }

            Vector2 input = ReadMoveInput();
            if (input.sqrMagnitude < 0.0001f)
            {
                ApplyLocomotionAnimation(0f);
                return;
            }

            if (input.sqrMagnitude > 1f)
                input.Normalize();

            Vector3 moveDir = GetScreenRelativeMoveDirection(input);
            if (moveDir.sqrMagnitude < 0.0001f) return;

            SetFacing(moveDir);
            _rb.MovePosition(_rb.position + moveDir * (EffectiveMovementSpeed * input.magnitude * Time.fixedDeltaTime));

            ApplyLocomotionAnimation(input.magnitude);
        }

        /// <summary>
        /// Drives the locomotion parameters. Riding holds Speed at zero and raises Cycling, so a
        /// controller with a Cycle state plays it and one without simply idles rather than running
        /// on the spot.
        /// </summary>
        private void ApplyLocomotionAnimation(float speed)
        {
            if (PlayerAnimator == null) return;
            RefreshAnimatorParameters();

            bool riding = MountController.IsPlayerRiding;
            if (_hasSpeedParam) PlayerAnimator.SetFloat("Speed", riding ? 0f : speed);
            if (_hasCyclingParam) PlayerAnimator.SetBool("Cycling", riding);
        }

        // Animator.parameters allocates an array per access, and this runs every physics step, so
        // presence is resolved once per controller instead. Keyed on the controller because it can
        // change at runtime — the art importer assigns one when the player's sheets land.
        private void RefreshAnimatorParameters()
        {
            RuntimeAnimatorController controller = PlayerAnimator.runtimeAnimatorController;
            if (controller == _animatorParamsFor) return;

            _animatorParamsFor = controller;
            _hasSpeedParam = false;
            _hasCyclingParam = false;

            foreach (var p in PlayerAnimator.parameters)
            {
                if (p.name == "Speed" && p.type == AnimatorControllerParameterType.Float)
                    _hasSpeedParam = true;
                else if (p.name == "Cycling" && p.type == AnimatorControllerParameterType.Bool)
                    _hasCyclingParam = true;
            }
        }

        /// <summary>
        /// Turns the player to face a world direction, sprite included. For anything that places
        /// the player without them having walked there — arriving at a portal's spawn marker, a
        /// scripted beat — where writing <c>transform.rotation</c> directly would be reverted by
        /// the next input and would not flip the billboarded sprite at all.
        /// </summary>
        public void FaceTowards(Vector3 worldDirection)
        {
            SetFacing(worldDirection);
        }

        private void SetFacing(Vector3 dir)
        {
            dir.y = 0f;
            if (dir.sqrMagnitude < 0.0001f) return;
            _facingDir = dir.normalized;

            Quaternion lookRot = Quaternion.LookRotation(_facingDir, Vector3.up);
            _rb.MoveRotation(lookRot);

            if (_actorVisual == null)
                _actorVisual = GetComponent<WorldActorVisual>();
            if (_actorVisual != null)
                _actorVisual.SetFacing(_facingDir);
        }

        /// <summary>
        /// Joystick and WASD share the same screen-space axes:
        /// up = toward top of screen, left = toward left of screen.
        /// </summary>
        public Vector2 ReadMoveInput()
        {
            Vector2 keyboard = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
            Vector2 stick = Joystick != null ? Joystick.InputVector : Vector2.zero;

            if (stick.sqrMagnitude > 0.01f && keyboard.sqrMagnitude > 0.01f)
                return Vector2.ClampMagnitude(stick + keyboard, 1f);
            if (stick.sqrMagnitude > 0.01f)
                return stick;
            return keyboard;
        }

        public static Vector3 GetScreenRelativeMoveDirection(Vector2 input)
        {
            Vector3 forward;
            Vector3 right;

            var cam = UnityEngine.Camera.main;
            if (cam != null)
            {
                forward = cam.transform.forward;
                right = cam.transform.right;
            }
            else
            {
                // Matches fixed iso camera yaw when Main Camera is missing
                Quaternion yaw = Quaternion.Euler(0f, EKVibe.CameraYaw, 0f);
                forward = yaw * Vector3.forward;
                right = yaw * Vector3.right;
            }

            forward.y = 0f;
            right.y = 0f;
            if (forward.sqrMagnitude > 0.0001f) forward.Normalize();
            if (right.sqrMagnitude > 0.0001f) right.Normalize();

            Vector3 dir = forward * input.y + right * input.x;
            return dir.sqrMagnitude > 0.0001f ? dir.normalized : Vector3.zero;
        }

        #region Melee Combat
        public void PerformMeleeAttack()
        {
            if (_isAttacking || _isDead) return;
            if (BlockedByRiding()) return;

            StartCoroutine(MeleeHitboxRoutine(MeleeHitDelay, MeleeRecovery));
        }

        /// <summary>
        /// Riding takes both hands. Reads the non-creating accessor so this stays a null check on
        /// every attack and cast for a player who has never been near a vehicle.
        /// </summary>
        private bool BlockedByRiding()
        {
            if (!MountController.IsPlayerRiding) return false;

            if (UIManager.Instance != null)
            {
                var vehicle = MountController.Current.CurrentVehicle;
                UIManager.Instance.LogCombat($"Not while you're on the {vehicle.VehicleName}.");
            }
            return true;
        }

        private IEnumerator MeleeHitboxRoutine(float delay, float attackDuration)
        {
            // _isAttacking gates every attack and cast. If this routine ever stops early without
            // clearing it, the player silently loses the ability to attack for the rest of the
            // session — so the reset lives in a finally, not on the happy path.
            //
            // Everything the swing does lives inside the try, including the setup that used to sit
            // in PerformMeleeAttack: anything throwing between raising the flag and reaching the
            // coroutine would have stuck it true with no finally to run. Unity steps a coroutine
            // synchronously up to its first yield, so the flag is still set before StartCoroutine
            // returns and a double-tap still can't fire twice. CastAbilityRoutine has this shape.
            _isAttacking = true;

            try
            {
                // Lock body to last faced direction for this swing
                if (_facingDir.sqrMagnitude > 0.001f)
                    SetFacing(_facingDir);

                SetAnimatorTrigger("MeleeAttack");

                if (_actorVisual == null)
                    _actorVisual = GetComponent<WorldActorVisual>();
                if (_actorVisual != null)
                    _actorVisual.PlayMeleeSwing(_facingDir);

                _rb.velocity = Vector3.zero;

                yield return new WaitForSeconds(delay);

                Vector3 facing = _facingDir.sqrMagnitude > 0.001f ? _facingDir.normalized : transform.forward;
                facing.y = 0f;
                if (facing.sqrMagnitude < 0.001f) facing = Vector3.forward;
                facing.Normalize();

                float reach = MeleeRange > 0f ? MeleeRange : 1.95f;
                if (AttackPoint != null)
                {
                    float distToAttackPoint = Vector3.Distance(transform.position, AttackPoint.position);
                    if (distToAttackPoint > reach) reach = distToAttackPoint;
                }

                // Origin at waist height in 3D isometric space
                Vector3 sphereCenter = transform.position + Vector3.up * (EKVibe.CharacterHeight * 0.5f);
                int hitCount = Physics.OverlapSphereNonAlloc(sphereCenter, reach, _hitResults, ~0, QueryTriggerInteraction.Ignore);
                int damage = PlayerData != null
                    ? PlayerData.BaseTraits.Strength + EKVibe.MeleeDamageStrengthOffset
                    : 6; // PlayerData unbound — 6 matches the default CoreTraits Strength (5) + the same offset.

                // Equipped weapon adds its Damage on top of the Strength roll.
                var session = Flow.PlayerSession.Instance;
                Data.ItemData weapon = session != null ? session.EquippedWeapon() : null;
                if (weapon != null) damage += weapon.Damage;
                if (session != null) damage += session.TotalAttackBonus();

                // After the weapon, so a perk multiplies the whole swing rather than the bare
                // Strength roll. A cached float, never a walk over the perk list — this is a hot
                // path and the multiplier only moves on level-up, load and perk spend.
                if (session != null)
                    damage = Mathf.RoundToInt(damage * session.MeleeDamageMultiplier);

                float arcAngle = MeleeArcAngle > 0f ? MeleeArcAngle : 180f;
                float dotThreshold = Mathf.Cos((arcAngle * 0.5f) * Mathf.Deg2Rad);
                float pointBlankSq = PointBlankRange * PointBlankRange;
                Vector3 playerPos = transform.position;

                _hitThisSwing.Clear();
                for (int i = 0; i < hitCount; i++)
                {
                    Collider enemyCol = _hitResults[i];
                    if (enemyCol == null) continue;
                    if (enemyCol.transform == transform || enemyCol.transform.IsChildOf(transform)) continue;

                    // Parent lookup so child colliders still resolve; set dedupes multi-collider enemies
                    Health targetHealth = enemyCol.GetComponentInParent<Health>();
                    if (targetHealth == null || targetHealth.IsDead) continue;
                    if (!_hitThisSwing.Add(targetHealth)) continue;

                    // Closest point on enemy collider for distance / point-blank check
                    Vector3 closest = enemyCol.ClosestPoint(playerPos);
                    Vector3 toClosest = closest - playerPos;
                    toClosest.y = 0f;

                    // Point-blank grace: overlapping / adjacent enemies hit automatically regardless of facing
                    if (pointBlankSq > 0f && toClosest.sqrMagnitude <= pointBlankSq)
                    {
                        // Inside point-blank radius, connect hit
                    }
                    else
                    {
                        // Semicircle / arc angle check relative to player position
                        Vector3 toTarget = targetHealth.transform.position - playerPos;
                        toTarget.y = 0f;
                        if (toTarget.sqrMagnitude > 0.001f)
                        {
                            float ahead = Vector3.Dot(toTarget.normalized, facing);
                            if (ahead < dotThreshold) continue; // outside attack arc
                        }
                    }

                    string foeName = string.IsNullOrEmpty(targetHealth.DisplayName)
                        ? targetHealth.name.Replace("(Clone)", "").Trim()
                        : targetHealth.DisplayName;
                    // Four-argument overload: passing gameObject is what sets Health.LastAttacker
                    // to the player. Without it the player is invisible to anything that asks who
                    // landed the killing blow — no error, just an attribution that never matches.
                    if (targetHealth.TakeDamage(damage, "you", foeName, gameObject))
                    {
                        _bar?.Ping();
                        // The knockback perk, gated on the hit LANDING and the enemy still being
                        // alive: Health.Die has already disabled the agent and the AI by now, and
                        // shoving a corpse would fight the destroy delay.
                        if (session != null && session.MeleeKnockbackDistance > 0f && !targetHealth.IsDead)
                            targetHealth.GetComponent<EnemyAI>()?.ApplyKnockback(facing, session.MeleeKnockbackDistance);
                    }
                }

                yield return new WaitForSeconds(attackDuration);
            }
            finally
            {
                _isAttacking = false;
            }
        }

        private void OnDrawGizmosSelected()
        {
            Vector3 facing = Application.isPlaying && _facingDir.sqrMagnitude > 0.001f
                ? _facingDir
                : transform.forward;
            facing.y = 0f;
            if (facing.sqrMagnitude < 0.001f) facing = Vector3.forward;
            facing.Normalize();

            Vector3 origin = transform.position;
            float reach = MeleeRange > 0f ? MeleeRange : 1.95f;
            if (AttackPoint != null)
            {
                float distToAttackPoint = Vector3.Distance(transform.position, AttackPoint.position);
                if (distToAttackPoint > reach) reach = distToAttackPoint;
            }

            float angle = MeleeArcAngle > 0f ? MeleeArcAngle : 180f;
            float halfAngle = angle * 0.5f;

            // Point-blank inner sphere
            if (PointBlankRange > 0f)
            {
                Gizmos.color = new Color(1f, 0.5f, 0f, 0.4f);
                Gizmos.DrawWireSphere(origin + Vector3.up * (EKVibe.CharacterHeight * 0.5f), PointBlankRange);
            }

            // Cleave arc rays and perimeter
            Gizmos.color = Color.red;
            Quaternion leftRot = Quaternion.Euler(0f, -halfAngle, 0f);
            Quaternion rightRot = Quaternion.Euler(0f, halfAngle, 0f);

            Vector3 leftRay = leftRot * facing * reach;
            Vector3 rightRay = rightRot * facing * reach;

            Gizmos.DrawLine(origin, origin + leftRay);
            Gizmos.DrawLine(origin, origin + rightRay);
            Gizmos.DrawLine(origin, origin + facing * reach);

            int segments = 24;
            Vector3 prevPoint = origin + leftRay;
            for (int i = 1; i <= segments; i++)
            {
                float a = -halfAngle + (angle / segments) * i;
                Vector3 currPoint = origin + Quaternion.Euler(0f, a, 0f) * facing * reach;
                Gizmos.DrawLine(prevPoint, currPoint);
                prevPoint = currPoint;
            }
        }
        #endregion

        #region Dodge Roll
        /// <summary>
        /// Rolls in the current move direction, or in the faced direction when standing still.
        /// Mirrors <see cref="PerformMeleeAttack"/>: every reason to refuse is checked here, and the
        /// coroutine only starts once the stamina has actually been paid.
        /// </summary>
        /// <summary>
        /// Stamina the next roll will cost: <see cref="RollStaminaPercent"/> of the live maximum.
        ///
        /// ⚠ **Floors, never rounds.** <see cref="PerformDodge"/> refuses on
        /// `CurrentStamina &lt; cost`, so the cost must stay at or below half the pool or the
        /// second roll is refused and the "two rolls from full" economy silently becomes one.
        /// Rounding breaks that on odd maxima — a 55 pool rounds to 28, leaving 27, which is short.
        /// Worse, Mathf.RoundToInt is banker's rounding, so it would fail on some maxima and not
        /// others as the pool grew with level, reading as an intermittent bug rather than an
        /// arithmetic one. Flooring makes `2 × cost &lt;= max` an invariant.
        ///
        /// The Max(1, …) guard is separate, and keeps a future 1-maximum perk or curse from making
        /// rolls free. PlayerData is PlayerSession.RuntimeStats once a session has bound, so this
        /// is the level-grown, perk-adjusted maximum — not the template's.
        /// </summary>
        private int CurrentRollCost =>
            PlayerData != null
                ? Mathf.Max(1, Mathf.FloorToInt(PlayerData.MaxManaStamina * RollStaminaPercent / 100f))
                : RollStaminaCost;

        public void PerformDodge()
        {
            // No rolling out of a swing. Committing to the attack is what the attack costs, and the
            // rule holds both ways — MeleeHitboxRoutine already refuses to start mid-roll via
            // _isAttacking's twin below. Cancelling into a roll would be the more action-game feel;
            // it is deliberately not the choice here.
            if (_isRolling || _isKnockedBack || _isAttacking || _isDead) return;
            if (BlockedByRiding()) return;
            if (Time.time < _nextRollTime) return;

            // Read once into a local: the check and the spend must charge the same number even if
            // the maximum moved between them (a level-up lands through OnSessionStatsChanged).
            int cost = CurrentRollCost;
            if (CurrentStamina < cost)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat("Not enough Stamina.");
                return;
            }

            // Current input if there is any, else whatever we last faced — rolling backwards out of
            // a fight has to be possible, which is also why nothing calls SetFacing below: the
            // sprite keeps looking at the enemy while the body travels the other way.
            Vector3 dir = GetScreenRelativeMoveDirection(ReadMoveInput());
            if (dir.sqrMagnitude < 0.0001f) dir = _facingDir;
            dir.y = 0f;
            if (dir.sqrMagnitude < 0.0001f) dir = Vector3.forward;
            dir.Normalize();

            CurrentStamina -= cost;
            _nextRollTime = Time.time + RollCooldown;

            // Diving across the floor is not sneaking. Routed through ToggleStealth rather than
            // clearing the speed modifier here, so the sprite tint, the toast and the CRO button
            // all come back in step — that is its job, and duplicating half of it would drift.
            var stealth = StealthController.Instance;
            if (stealth != null && stealth.IsCrouched)
                stealth.ToggleStealth();

            StartCoroutine(RollRoutine(dir));
        }

        private IEnumerator RollRoutine(Vector3 dir)
        {
            // Same discipline as MeleeHitboxRoutine, for the same reason: a stuck _isRolling gates
            // HandleMovement forever and the player never moves again. The reset lives in a finally,
            // never on the happy path.
            _isRolling = true;

            try
            {
                SetAnimatorTrigger("Roll");

                // Once, at the start — not per step. Zeroing velocity every step would suspend
                // gravity for the whole roll and leave the player hovering if they rolled off a kerb.
                _rb.velocity = Vector3.zero;

                float elapsed = 0f;
                var wait = new WaitForFixedUpdate();

                while (elapsed < RollDuration)
                {
                    // Cooperative cancellation, checked before moving: dying mid-roll must not
                    // leave a corpse sliding, and a knockback landing mid-roll always wins —
                    // the roll yields the body to it. yield break still runs the finally, which
                    // is why nothing here needs StopCoroutine — whether that runs a finally is
                    // not something this repo can verify without an editor.
                    if (_isDead || _isKnockedBack) yield break;

                    float speed = RollDistance / RollDuration * RollSpeedCurve(elapsed / RollDuration);

                    // ⚠ MovePosition, deliberately not a capsule cast. This Rigidbody is
                    // non-kinematic, so MovePosition sweeps and resolves against colliders — it is
                    // the same call HandleMovement makes and the reason walking cannot clip a wall.
                    // Knocking an ENEMY back will need the cast, because an enemy is moved by its
                    // transform and would punch straight through geometry.
                    _rb.MovePosition(_rb.position + dir * (speed * Time.fixedDeltaTime));

                    // Re-armed each step rather than set once up front, so a roll cut short leaves
                    // no invulnerability running past its end. The 1.5x margin covers the gap to the
                    // next physics step.
                    if (elapsed >= RollIFrameStart && elapsed < RollIFrameStart + RollIFrameDuration)
                        _invulnerableUntil = Mathf.Max(_invulnerableUntil,
                            Time.time + Time.fixedDeltaTime * 1.5f);

                    elapsed += Time.fixedDeltaTime;
                    yield return wait;
                }
            }
            finally
            {
                _isRolling = false;
            }
        }

        /// <summary>
        /// Speed shape across the roll — quick off the mark, trailing off into recovery.
        ///
        /// ⚠ Its integral over [0,1] is exactly 1, and that is what makes the roll actually travel
        /// <see cref="RollDistance"/>. Reshape it without preserving that and the distance silently
        /// stops matching the field it is read from.
        /// </summary>
        private static float RollSpeedCurve(float t) => 1.5f - t;
        #endregion

        #region Knockback
        /// <summary>Seconds the slide lasts. A fixed feel value, not a knob — only the recovery
        /// i-frames are tuned in the Inspector.
        ///
        /// ⚠ This is deliberately SHORTER than the knockback clip, and the two are not meant to
        /// match. The physical shove is 0.22 s; the imported clip is 6 frames at 12 fps = 0.50 s
        /// (ArtImportTool's action contract). The player therefore regains control roughly 0.28 s
        /// before the tumble finishes drawing — the body has stopped, the character is still
        /// getting up. That is the intent: a half-second of hard movement lock reads as a freeze,
        /// while a recovery animation the player can act out of reads as a recovery.
        ///
        /// The consequence to know about: the Knockback state has only an exit-time return to Idle,
        /// so walking away during those 0.28 s keeps the tumble on screen until it finishes (Speed
        /// only drives Idle→Run). Attacking, casting or being hit again cuts it short through its
        /// own Any State transition, which is correct — a new action should win over a finished
        /// slide. Shortening the clip, not lengthening the slide, is the fix if the overhang ever
        /// reads badly.</summary>
        private const float KnockbackSlideDuration = 0.22f;

        /// <summary>
        /// Shoves the player <paramref name="distance"/> metres along <paramref name="dir"/>. Called
        /// by <see cref="EnemyAI.TryKnockback"/> only when a hit actually landed — a hit refused by
        /// i-frames must not reach here.
        ///
        /// Knockback always wins over a roll in progress: setting <see cref="_isKnockedBack"/> is
        /// the cooperative flag <see cref="RollRoutine"/> polls to bail out. No coroutine is ever
        /// stopped — an in-flight melee swing keeps running too, and clears its own flag in its own
        /// finally; its hitbox either already fired or fires from where the player has been shoved
        /// out of, which is the correct punish.
        /// </summary>
        public void ApplyKnockback(Vector3 dir, float distance)
        {
            if (_isDead) return;
            dir.y = 0f;
            if (dir.sqrMagnitude < 0.0001f || distance <= 0f) return;
            StartCoroutine(KnockbackRoutine(dir.normalized, distance));
        }

        private IEnumerator KnockbackRoutine(Vector3 dir, float distance)
        {
            // Same discipline as RollRoutine, for the same reason: a stuck _isKnockedBack gates
            // HandleMovement forever. The reset lives in a finally, never on the happy path.
            _isKnockedBack = true;

            try
            {
                // ⚠ Hit is cleared before Knockback is set, and the order matters. A knockback only
                // ever happens because a hit landed, so OnHealthDamaged has already fired "Hit" this
                // same frame — EnemyAI calls TakeDamage, then TryKnockback. Leaving both triggers set
                // makes the Animator take whichever Any State transition it evaluates first and hold
                // the other for the next frame, so the tumble either loses its first frame to Hurt or
                // gets cut off by it. Knockback is the more specific reaction and supersedes it.
                // Harmless when the controller has neither parameter — both helpers check first.
                ClearAnimatorTrigger("Hit");
                SetAnimatorTrigger("Knockback");

                // Once, at the start — same reasoning as RollRoutine: per-step zeroing would
                // suspend gravity and leave the player hovering off a kerb.
                _rb.velocity = Vector3.zero;

                float elapsed = 0f;
                var wait = new WaitForFixedUpdate();

                while (elapsed < KnockbackSlideDuration)
                {
                    if (_isDead) yield break;

                    // Same fast-out/slow-in shape as the roll — its integral over [0,1] is 1, so
                    // the slide covers exactly the distance it was given.
                    float speed = distance / KnockbackSlideDuration *
                                  RollSpeedCurve(elapsed / KnockbackSlideDuration);

                    // ⚠ MovePosition, deliberately not a capsule cast — the identical reasoning to
                    // RollRoutine: this Rigidbody is non-kinematic, so MovePosition sweeps and
                    // resolves against colliders. The asymmetry with EnemyAI's knockback (which
                    // MUST cast, because enemies move by transform) is intentional, not drift.
                    _rb.MovePosition(_rb.position + dir * (speed * Time.fixedDeltaTime));

                    elapsed += Time.fixedDeltaTime;
                    yield return wait;
                }

                // Recovery i-frames as the slide ends, so two enemies cannot chain-stun. Written
                // with Max against the timestamp for the same reason IsInvulnerable is a timestamp
                // at all — two systems grant i-frames and nothing may clear another's window.
                _invulnerableUntil = Mathf.Max(_invulnerableUntil, Time.time + KnockbackRecoveryIFrames);
            }
            finally
            {
                _isKnockedBack = false;
            }
        }
        #endregion

        #region Health & Damage
        /// <summary>
        /// Raises the player's floating health bar. A one-line pass-through so an enemy taking
        /// aggro can raise it without knowing what component it lives on.
        ///
        /// ⚠ Pushed from EnemyAI's 0.2 s perception tick, not polled. Asking "does anything have
        /// aggro on me?" from the player is a global question, and the two obvious answers — a
        /// static counter that leaks on chunk teardown, or a per-frame scan that allocates — are
        /// both worse than five calls a second per aggroed enemy.
        /// </summary>
        public void PingHealthBar()
        {
            _bar?.Ping();
        }

        /// <summary>Legacy entry point — routes through Health so death/feedback stay unified.</summary>
        /// <returns>
        /// True if the hit landed, passed straight through from Health so this path can answer the
        /// same question the four-argument one does. The healthless fallback always lands: there is
        /// no Health to refuse it.
        /// </returns>
        public bool TakeDamage(int damage)
        {
            if (_health != null)
            {
                bool landed = _health.TakeDamage(damage, "Enemy", "you");
                CurrentHealth = _health.CurrentHealth;
                return landed;
            }

            CurrentHealth -= damage;
            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat($"Something hits you, {damage}");
            return true;
        }

        private void OnHealthDamaged(int damage)
        {
            CurrentHealth = _health.CurrentHealth;
            SetAnimatorTrigger("Hit");
        }

        private void OnHealthDeath()
        {
            if (_isDead) return;
            _isDead = true;
            _isAttacking = false;
            // RollRoutine and KnockbackRoutine poll _isDead and bail on their own — clearing the
            // flags here does not stop a running coroutine, so both are needed.
            _isRolling = false;
            _isKnockedBack = false;
            _invulnerableUntil = 0f;
            _rb.velocity = Vector3.zero;
            if (PlayerAnimator != null) PlayerAnimator.SetFloat("Speed", 0f);

            if (GBHEngland.Flow.GameFlowController.Instance != null)
                GBHEngland.Flow.GameFlowController.Instance.HandlePlayerDeath();
            else if (UI.DeathScreenUI.Instance != null)
                UI.DeathScreenUI.Instance.Show();
            else
                Debug.LogWarning("Player died but neither GameFlowController nor DeathScreenUI exist to handle it.");
        }

        /// <summary>Called by GameFlow on respawn — restores health and control.</summary>
        public void ReviveFull()
        {
            int max = _health != null ? _health.MaxHealth : (PlayerData != null ? PlayerData.MaxHealth : 100);
            if (_health != null) _health.Revive(max);
            CurrentHealth = max;
            CurrentMana = PlayerData != null ? PlayerData.MaxManaStamina : 50;
            CurrentStamina = CurrentMana;
            _isDead = false;
        }
        #endregion

        #region Ability System
        private void ProcessCooldowns()
        {
            for (int i = _activeCooldownKeys.Count - 1; i >= 0; i--)
            {
                string key = _activeCooldownKeys[i];
                _abilityCooldowns[key] -= Time.deltaTime;

                if (_abilityCooldowns[key] <= 0f)
                {
                    _abilityCooldowns.Remove(key);
                    _activeCooldownKeys.RemoveAt(i);
                }
            }
        }

        /// <summary>0 = ready; otherwise seconds left on the slot's cooldown. For HUD overlays.</summary>
        public float GetCooldownRemaining(int slotIndex, out float total)
        {
            total = 0f;
            if (EquippedAbilities == null || slotIndex < 0 || slotIndex >= EquippedAbilities.Count) return 0f;
            AbilityData ability = EquippedAbilities[slotIndex];
            if (ability == null) return 0f;

            total = ability.CooldownTime;
            return _abilityCooldowns.TryGetValue(ability.AbilityID, out float remaining)
                ? Mathf.Max(0f, remaining)
                : 0f;
        }

        public void TryCastAbility(int slotIndex)
        {
            if (_isAttacking || _isDead) return;
            if (BlockedByRiding()) return;
            if (EquippedAbilities == null || slotIndex < 0 || slotIndex >= EquippedAbilities.Count) return;

            AbilityData ability = EquippedAbilities[slotIndex];
            if (ability == null) return;

            if (_abilityCooldowns.ContainsKey(ability.AbilityID) && _abilityCooldowns[ability.AbilityID] > 0f)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat($"{ability.AbilityName} is on cooldown.");
                return;
            }

            if (ability.ResourceType == AbilityResourceType.Mana && CurrentMana < ability.ResourceCost)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat("Not enough Mana.");
                return;
            }
            if (ability.ResourceType == AbilityResourceType.Stamina && CurrentStamina < ability.ResourceCost)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat("Not enough Stamina.");
                return;
            }

            if (ability.ResourceType == AbilityResourceType.Mana) CurrentMana -= ability.ResourceCost;
            if (ability.ResourceType == AbilityResourceType.Stamina) CurrentStamina -= ability.ResourceCost;

            _abilityCooldowns[ability.AbilityID] = ability.CooldownTime;
            if (!_activeCooldownKeys.Contains(ability.AbilityID))
                _activeCooldownKeys.Add(ability.AbilityID);

            // Magic is a secret — casting it drains your Concealment meter.
            if (IsMagic(ability) && IsInCity())
            {
                Systems.WantedManager.Instance?.DrainConcealment(34f); // 3 spells = busted
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("Easy with the spells there Potter, not around the plebs yeah?");
            }

            StartCoroutine(CastAbilityRoutine(ability));
        }

        private static bool IsMagic(AbilityData a) => a != null && a.ResourceType == AbilityResourceType.Mana;

        private static bool IsInCity()
        {
            var cm = World.ChunkManager.Instance;
            return cm != null && cm.CurrentChunkData != null && cm.CurrentChunkData.IsCity;
        }

        private IEnumerator CastAbilityRoutine(AbilityData ability)
        {
            _isAttacking = true;
            _rb.velocity = Vector3.zero;

            // See MeleeHitboxRoutine: the reset must be in a finally or a single interrupted cast
            // permanently disables both spells and melee.
            try
            {
                SetAnimatorTrigger("CastSpell");

                // Hoisted rather than fetching Instance twice — the spell damage multiplier below
                // needs it too.
                var session = Flow.PlayerSession.Instance;

                // Spark alone owns the player-authored shout. Other spells keep their canonical
                // names rather than all being called "Spark Out" once the spellbook holds six.
                string shout = ability.SpellEffect == SpellEffectType.Spark && session != null
                    ? session.SpellName
                    : ability.AbilityName;
                UI.SpellShoutText.Spawn(transform.position, shout);

                yield return new WaitForSeconds(ability.CastTime);

                Health target = ability.SpellEffect == SpellEffectType.Spark
                                || ability.SpellEffect == SpellEffectType.Fireball
                                || ability.SpellEffect == SpellEffectType.SludgeBolt
                    ? FindSpellTarget(ability.Range)
                    : null;
                SpellRuntime.Execute(this, ability, target, shout);
            }
            finally
            {
                _isAttacking = false;
            }
        }

        /// <summary>
        /// SetTrigger on a controller that lacks the parameter logs an error every call. The
        /// player's controller is authored in-scene and may not define all of them, so check
        /// first rather than flooding the console (which hides real errors).
        /// </summary>
        private void SetAnimatorTrigger(string trigger)
        {
            if (HasAnimatorTrigger(trigger)) PlayerAnimator.SetTrigger(trigger);
        }

        /// <summary>
        /// Consumes a trigger that has been set but not yet taken. Same parameter check as
        /// <see cref="SetAnimatorTrigger"/>, for the same reason — ResetTrigger on a controller
        /// that lacks the parameter logs the same error SetTrigger does.
        /// </summary>
        private void ClearAnimatorTrigger(string trigger)
        {
            if (HasAnimatorTrigger(trigger)) PlayerAnimator.ResetTrigger(trigger);
        }

        private bool HasAnimatorTrigger(string trigger)
        {
            if (PlayerAnimator == null) return false;
            foreach (var p in PlayerAnimator.parameters)
                if (p.type == AnimatorControllerParameterType.Trigger && p.name == trigger)
                    return true;
            return false;
        }

        /// <summary>Closest living enemy Health within range (never the player themselves).</summary>
        private Health FindSpellTarget(float range)
        {
            var hits = Physics.OverlapSphere(transform.position, Mathf.Max(1f, range));
            Health best = null;
            float bestSq = float.MaxValue;
            foreach (var c in hits)
            {
                var h = c.GetComponentInParent<Health>();
                if (h == null || h == _health || h.IsDead) continue;
                if (h.GetComponent<EnemyAI>() == null) continue;
                float sq = (h.transform.position - transform.position).sqrMagnitude;
                if (sq < bestSq) { bestSq = sq; best = h; }
            }
            return best;
        }

        // ---- Magic: learning the first spell ----

        public const int SpellSlots = 4;
        public bool KnowsSpark => HasKnownSpell("spark");

        /// <summary>Every spell the player has learned (a superset of the 4 equipped slots).</summary>
        public List<AbilityData> KnownSpells { get; } = new List<AbilityData>();

        /// <summary>Grants the Spark spell. Called by the magic tutorial when Daniel teaches it.</summary>
        public void LearnSpark()
        {
            if (KnowsSpark) return;
            AbilityData spark = SpellDatabase.Find("spark");
            if (spark == null)
            {
                Debug.LogError("LearnSpark: Resources/Abilities has no spell with AbilityID 'spark'.");
                return;
            }

            LearnAbility(spark);

            if (Flow.PlayerSession.Instance != null) Flow.PlayerSession.Instance.KnowsSpark = true;
            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("You can feel the spark now — cast it with the spell button.");
        }

        /// <summary>Adds a spell to the spellbook and drops it into the first open spell slot.</summary>
        public void LearnAbility(AbilityData ability)
        {
            if (ability == null || string.IsNullOrWhiteSpace(ability.AbilityID)) return;
            EnsureSlots();
            AbilityData known = FindKnownSpell(ability.AbilityID);
            if (known == null)
            {
                KnownSpells.Add(ability);
                known = ability;
            }

            if (EquippedAbilities.Contains(known)) return; // already slotted
            for (int i = 0; i < SpellSlots; i++)
                if (EquippedAbilities[i] == null) { EquippedAbilities[i] = known; return; }
        }

        /// <summary>Binds a known spell to a slot (spellbook). Clears it from any other slot first.</summary>
        public void AssignToSlot(AbilityData ability, int slot)
        {
            if (slot < 0 || slot >= SpellSlots) return;
            EnsureSlots();
            if (ability != null)
            {
                AbilityData known = FindKnownSpell(ability.AbilityID);
                if (known == null) KnownSpells.Add(ability);
                else ability = known;
                for (int i = 0; i < SpellSlots; i++)
                    if (EquippedAbilities[i] == ability) EquippedAbilities[i] = null;
            }
            EquippedAbilities[slot] = ability;
        }

        public void ClearSlot(int slot)
        {
            if (slot < 0 || slot >= SpellSlots) return;
            EnsureSlots();
            EquippedAbilities[slot] = null;
        }

        /// <summary>Learn every definition currently reachable through Resources/Abilities.</summary>
        public int LearnAllCurrentSpells()
        {
            int before = KnownSpells.Count;
            foreach (string abilityId in SpellDatabase.CurrentSpellIds)
                LearnAbility(SpellDatabase.Find(abilityId));
            if (Flow.PlayerSession.Instance != null)
                Flow.PlayerSession.Instance.KnowsSpark = KnowsSpark;
            return KnownSpells.Count - before;
        }

        /// <summary>Clears known spells, slots and cooldowns. Used by New Game and the debug reset.</summary>
        public void ClearLearnedSpells()
        {
            TimedSpellStatus[] activeStatuses = GetComponentsInChildren<TimedSpellStatus>(true);
            for (int i = 0; i < activeStatuses.Length; i++)
                activeStatuses[i].Cancel();

            KnownSpells.Clear();
            EnsureSlots();
            for (int i = 0; i < EquippedAbilities.Count; i++) EquippedAbilities[i] = null;
            _abilityCooldowns.Clear();
            _activeCooldownKeys.Clear();
            if (Flow.PlayerSession.Instance != null)
                Flow.PlayerSession.Instance.KnowsSpark = false;
        }

        /// <summary>Restores stable AbilityID values from savegame.json.</summary>
        public void RestoreSpellLoadout(IReadOnlyList<string> knownIds, IReadOnlyList<string> equippedIds)
        {
            ClearLearnedSpells();

            if (knownIds != null)
            {
                foreach (string id in knownIds)
                {
                    AbilityData ability = SpellDatabase.Find(id);
                    if (ability == null)
                    {
                        if (!string.IsNullOrWhiteSpace(id))
                            Debug.LogWarning($"RestoreSpellLoadout: no AbilityData for saved id '{id}'.");
                        continue;
                    }
                    if (!HasKnownSpell(ability.AbilityID)) KnownSpells.Add(ability);
                }
            }

            EnsureSlots();
            bool restoredAnySlot = false;
            if (equippedIds != null)
            {
                int count = Mathf.Min(SpellSlots, equippedIds.Count);
                for (int i = 0; i < count; i++)
                {
                    AbilityData ability = SpellDatabase.Find(equippedIds[i]);
                    if (ability == null) continue;
                    if (!HasKnownSpell(ability.AbilityID)) KnownSpells.Add(ability);
                    EquippedAbilities[i] = ability;
                    restoredAnySlot = true;
                }
            }

            // Defensive migration for a save that knows spells but predates equipped-slot storage.
            if (!restoredAnySlot)
                for (int i = 0; i < Mathf.Min(SpellSlots, KnownSpells.Count); i++)
                    EquippedAbilities[i] = KnownSpells[i];

            if (Flow.PlayerSession.Instance != null)
                Flow.PlayerSession.Instance.KnowsSpark = KnowsSpark;
        }

        private bool HasKnownSpell(string abilityId) => FindKnownSpell(abilityId) != null;

        private AbilityData FindKnownSpell(string abilityId)
        {
            if (string.IsNullOrWhiteSpace(abilityId)) return null;
            foreach (AbilityData known in KnownSpells)
                if (known != null && string.Equals(known.AbilityID, abilityId,
                    System.StringComparison.OrdinalIgnoreCase))
                    return known;
            return null;
        }

        private void EnsureSlots()
        {
            if (EquippedAbilities == null) EquippedAbilities = new List<AbilityData>(SpellSlots);
            while (EquippedAbilities.Count < SpellSlots) EquippedAbilities.Add(null);
        }
        #endregion
    }
}
