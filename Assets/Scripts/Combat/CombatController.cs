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

        [Header("Special Attacks")]
        [Tooltip("Seconds the spin lasts, not counting the recovery that follows it.")]
        public float SpinDuration = 0.60f;
        [Tooltip("How many times the spin sweeps. Each tick clears the dedupe set, so standing " +
                 "inside the spin is hit once per tick.")]
        public int SpinTicks = 3;
        [Tooltip("Reach in metres. 0 falls back to MeleeRange.")]
        public float SpinRange = 2.40f;
        [Tooltip("Per-tick damage as a fraction of a plain swing.")]
        public float SpinDamageMultiplier = 0.60f;
        [Tooltip("Percent of MAXIMUM stamina spent per spin, for the reason CurrentRollCost " +
                 "spells out: a flat cost silently gets cheaper every level as the pool grows.")]
        public float SpinStaminaPercent = 35f;
        [Tooltip("Seconds the dash lunge lasts.")]
        public float DashDuration = 0.28f;
        [Tooltip("Metres covered. Only meaningful because RollSpeedCurve integrates to 1.")]
        public float DashDistance = 3.20f;
        [Tooltip("Reach in metres for the dash's per-step sweep. 0 falls back to MeleeRange.")]
        public float DashRange = 1.10f;
        [Tooltip("Frontal arc in degrees for the dash. 360 or more skips the facing test.")]
        public float DashArcAngle = 140f;
        [Tooltip("Dash damage as a fraction of a plain swing. Charged once per target per dash.")]
        public float DashDamageMultiplier = 1.25f;
        [Tooltip("Percent of MAXIMUM stamina spent per dash.")]
        public float DashStaminaPercent = 30f;

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

        [Header("Special Attacks")]
        // ⚠ Inspector-assigned, and deliberately NOT resolved by id out of Resources. A
        // special attack must never live under Resources/Abilities: SpellDatabase would load it,
        // LearnAllCurrentSpells would learn and slot it, and its AbilityID would be written into
        // savegame.json - at which point that id is a save key and can never be renamed.
        // See docs/reference/PLAYER_COMBAT.md.
        //
        // Element 0 is the SPN button, element 1 is DSH. Left unassigned, both buttons render
        // dimmed and pressing them does nothing: a visible failure mode, not a silent one, which
        // is why this is a list on the component rather than a lookup by id.
        public List<AbilityData> SpecialAttacks;

        private Dictionary<string, float> _abilityCooldowns = new Dictionary<string, float>();
        private List<string> _activeCooldownKeys = new List<string>(10);

        private bool _isAttacking;
        private bool _isRolling;
        private bool _isKnockedBack;
        private Coroutine _knockbackRoutine;
        private float _nextRollTime;
        private float _invulnerableUntil;
        /// <summary>
        /// True only during the dodge roll's own i-frame sub-window — a narrower thing than
        /// <see cref="IsInvulnerable"/>, which is also true during the passive knockback slide and
        /// its recovery. Exists purely so <see cref="Health"/> can tell "the player actively dodged
        /// that" from "the player happened to be recovering from being hit" and pick its floating
        /// text accordingly, without the invulnerability system itself needing two timestamps.
        /// </summary>
        private bool _isActivelyDodging;
        private bool _isDead;
        /// <summary>
        /// Overlap buffer for the melee sweep. 64, not 32: the sweep queries with mask ~0 and
        /// QueryTriggerInteraction.Collide, so ground, buildings and props all consume slots
        /// before any filtering runs, and OverlapSphereNonAlloc reports the overflow only by
        /// silently returning a full array. At 32 the enemy the player was aiming at could
        /// simply not be in it. Widening can only fix misses, never invent hits.
        /// </summary>
        private readonly Collider[] _hitResults = new Collider[64];
        private readonly HashSet<Health> _hitThisSwing = new HashSet<Health>();
        private float _staminaRegenCarry;
        private float _healthRegenCarry;
        private int _lastEffectiveMaxMana;
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

        /// <summary>
        /// True only inside the roll's own i-frame sub-window — read by <see cref="Health"/> to
        /// decide whether a refused hit was an actual dodge (worth a "Dodged!" toast) or just a
        /// miss during passive knockback-slide/recovery invulnerability, which is not the same
        /// player action and should not read as one.
        /// </summary>
        public bool IsActivelyDodging => _isActivelyDodging;

        /// <summary>Grants temporary invulnerability (i-frames) for the specified duration.</summary>
        public void GrantInvulnerability(float seconds)
        {
            _invulnerableUntil = Mathf.Max(_invulnerableUntil, Time.time + seconds);
        }

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
            if (session != null)
            {
                session.OnStatsChanged -= OnSessionStatsChanged;
                session.OnEquipmentChanged -= OnSessionStatsChanged;
            }
        }

        public void BindSessionStats(Flow.PlayerSession session)
        {
            if (session == null) return;
            session.OnStatsChanged -= OnSessionStatsChanged;
            session.OnStatsChanged += OnSessionStatsChanged;
            session.OnEquipmentChanged -= OnSessionStatsChanged;
            session.OnEquipmentChanged += OnSessionStatsChanged;
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
            _isActivelyDodging = false;
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

            // Passive Health Regeneration from equipped gear (e.g. Crown of Vitality: 1 HP per 6s = 0.1666f/s)
            float hpRegenRate = session != null ? session.TotalHealthRegenPerSecond() : 0f;
            if (hpRegenRate > 0f && _health != null && _health.CurrentHealth > 0 && _health.CurrentHealth < _health.MaxHealth)
            {
                _healthRegenCarry += hpRegenRate * Time.deltaTime;
                if (_healthRegenCarry >= 1f)
                {
                    int wholeHp = Mathf.FloorToInt(_healthRegenCarry);
                    _healthRegenCarry -= wholeHp;
                    _health.Heal(wholeHp);
                    CurrentHealth = _health.CurrentHealth;
                    PushHud();
                }
            }
        }

        /// <summary>
        /// Pushes the session's freshly derived stats and equipment bonuses onto the running player.
        /// Fires on every <see cref="Flow.PlayerSession.OnStatsChanged"/> and <see cref="Flow.PlayerSession.OnEquipmentChanged"/>.
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
                    int newMax = session.EffectiveMaxHealth();
                    int delta = newMax - _health.MaxHealth;
                    _health.MaxHealth = newMax;

                    // Equipping/Levelling GRANTS the new hit points rather than being a free full heal.
                    if (delta > 0 && _health.CurrentHealth > 0)
                        _health.CurrentHealth = Mathf.Min(newMax, _health.CurrentHealth + delta);
                    else if (delta < 0 && _health.CurrentHealth > 0)
                        _health.CurrentHealth = Mathf.Clamp(_health.CurrentHealth + delta, 1, newMax);
                    else if (_health.CurrentHealth > newMax)
                        _health.CurrentHealth = newMax;

                    CurrentHealth = _health.CurrentHealth;
                }

                int effectiveMaxMana = session.EffectiveMaxMana();
                if (_lastEffectiveMaxMana > 0)
                {
                    int manaDelta = effectiveMaxMana - _lastEffectiveMaxMana;
                    if (manaDelta > 0)
                        CurrentMana = Mathf.Min(effectiveMaxMana, CurrentMana + manaDelta);
                    else if (manaDelta < 0)
                        CurrentMana = Mathf.Clamp(CurrentMana + manaDelta, 0, effectiveMaxMana);
                }
                _lastEffectiveMaxMana = effectiveMaxMana;
                CurrentMana = Mathf.Min(CurrentMana, effectiveMaxMana);
                int staminaMax = stats.MaxManaStamina;
                CurrentStamina = Mathf.Min(CurrentStamina, staminaMax);
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

            var session = Flow.PlayerSession.Instance;
            int hp = _health != null ? _health.CurrentHealth : CurrentHealth;
            int hpMax = _health != null ? _health.MaxHealth : (session != null ? session.EffectiveMaxHealth() : (PlayerData != null ? PlayerData.MaxHealth : 100));
            CurrentHealth = hp;

            int manaMax = session != null ? session.EffectiveMaxMana() : (PlayerData != null ? PlayerData.MaxManaStamina : 50);
            int staminaMax = (session != null && session.RuntimeStats != null) ? session.RuntimeStats.MaxManaStamina : (PlayerData != null ? PlayerData.MaxManaStamina : 50);

            UIManager.Instance.UpdatePlayerHealth(hp, hpMax);
            UIManager.Instance.UpdatePlayerMana(CurrentMana, manaMax);
            UIManager.Instance.UpdatePlayerStamina(CurrentStamina, staminaMax);
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
            // Desktop testing only - the shipping route for these two is the HUD's SPN and DSH
            // buttons, built in UIManager.BuildActionButtons.
            if (Input.GetKeyDown(KeyCode.Alpha5)) TrySpecialAttack(0);
            if (Input.GetKeyDown(KeyCode.Alpha6)) TrySpecialAttack(1);
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
            if (_isAttacking || _isRolling || _isKnockedBack || _isDead) return;
            if (BlockedByRiding()) return;

            // Swinging a weapon is not sneaking.
            BreakStealth();

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

                if (_isDead || (_health != null && _health.IsDead)) yield break;

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

                _hitThisSwing.Clear();
                ResolveMeleeSweep(sphereCenter, facing, reach, MeleeArcAngle, ComputeMeleeDamage(1f));

                yield return new WaitForSeconds(attackDuration);
            }
            finally
            {
                _isAttacking = false;
            }
        }

        /// <summary>
        /// The swing's damage: Strength + the session's melee multiplier + equipped weapon +
        /// attack bonus, then scaled by <paramref name="moveMultiplier"/> so a special can hit
        /// harder or softer than a plain swing. Lifted unchanged from MeleeHitboxRoutine.
        /// </summary>
        private int ComputeMeleeDamage(float moveMultiplier)
        {
            int baseDamage = PlayerData != null
                ? PlayerData.BaseTraits.Strength + EKVibe.MeleeDamageStrengthOffset
                : 6; // PlayerData unbound — 6 matches the default CoreTraits Strength (5) + the same offset.

            var session = Flow.PlayerSession.Instance;
            int damage = session != null
                ? Mathf.RoundToInt(baseDamage * session.MeleeDamageMultiplier)
                : baseDamage;

            // Equipped weapon adds its Damage on top of the Strength roll.
            Data.ItemData weapon = session != null ? session.EquippedWeapon() : null;
            if (weapon != null) damage += weapon.Damage;
            if (session != null) damage += session.TotalAttackBonus();

            return Mathf.RoundToInt(damage * moveMultiplier);
        }

        /// <summary>
        /// One overlap-and-resolve pass: sphere at <paramref name="origin"/>, filter, arc test,
        /// damage, knockback. Returns how many targets took damage.
        ///
        /// ⚠ The caller owns <see cref="_hitThisSwing"/> and must clear it itself. That is
        /// deliberate, and it is the ONE thing that differs between the callers: clearing once
        /// gives one hit for the whole move however many passes it makes, clearing before every
        /// pass makes standing in the move hurt repeatedly. Hiding that behind a bool parameter
        /// would bury the only decision worth seeing at the call site.
        ///
        /// <paramref name="arcAngle"/> >= 360 skips the facing test entirely.
        /// </summary>
        private int ResolveMeleeSweep(Vector3 origin, Vector3 facing, float reach, float arcAngle, int damage)
        {
            int hitCount = Physics.OverlapSphereNonAlloc(origin, reach, _hitResults, ~0, QueryTriggerInteraction.Collide);
#if UNITY_EDITOR
            if (hitCount == _hitResults.Length)
                Debug.LogWarning($"ResolveMeleeSweep: overlap buffer saturated at {hitCount} — " +
                                 "targets beyond this were dropped. Raise _hitResults.");
#endif

            var session = Flow.PlayerSession.Instance;

            float effectiveArc = arcAngle > 0f ? arcAngle : 180f;
            bool skipArcTest = effectiveArc >= 360f;
            float dotThreshold = Mathf.Cos((effectiveArc * 0.5f) * Mathf.Deg2Rad);
            float pointBlankSq = PointBlankRange * PointBlankRange;
            // ⚠ The player's own position, NOT the waist-height sphere centre passed in as
            // origin. The two have always been different values here — the overlap is a 3D
            // sphere at waist height while the distance and arc tests are flat on X/Z — and
            // they must stay different.
            Vector3 playerPos = transform.position;
            int hits = 0;

            for (int i = 0; i < hitCount; i++)
            {
                Collider enemyCol = _hitResults[i];
                if (enemyCol == null) continue;
                if (enemyCol.transform == transform || enemyCol.transform.IsChildOf(transform)) continue;

                // Parent lookup so child colliders still resolve; set dedupes multi-collider enemies
                Health targetHealth = enemyCol.GetComponentInParent<Health>();
                if (targetHealth == null || targetHealth.IsDead) continue;
                if (targetHealth.GetComponent<CompanionAI>() != null) continue;
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
                else if (!skipArcTest)
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
                    hits++;
                    _bar?.Ping();
                    // The knockback perk, gated on the hit LANDING and the enemy still being
                    // alive: Health.Die has already disabled the agent and the AI by now, and
                    // shoving a corpse would fight the destroy delay.
                    if (session != null && session.MeleeKnockbackDistance > 0f && !targetHealth.IsDead)
                        targetHealth.GetComponent<EnemyAI>()?.ApplyKnockback(facing, session.MeleeKnockbackDistance);
                }
            }

            return hits;
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

            // Diving across the floor is not sneaking.
            BreakStealth();

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
                    bool inIFrameWindow = elapsed >= RollIFrameStart && elapsed < RollIFrameStart + RollIFrameDuration;
                    _isActivelyDodging = inIFrameWindow;
                    if (inIFrameWindow)
                        _invulnerableUntil = Mathf.Max(_invulnerableUntil,
                            Time.time + Time.fixedDeltaTime * 1.5f);

                    elapsed += Time.fixedDeltaTime;
                    yield return wait;
                }
            }
            finally
            {
                _isRolling = false;
                _isActivelyDodging = false;
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

        #region Special Attacks
        /// <summary>
        /// Runs a special attack that has already been paid for and put on cooldown by the ability
        /// path. Everything a special shares with a plain swing — the riding refusal, the cooldown,
        /// the stealth break — happens up there, so this is only the dispatch.
        /// </summary>
        private void PerformSpecialMeleeAttack(AbilityData ability)
        {
            switch (ability.SpecialKind)
            {
                case SpecialAttackKind.Spin: StartCoroutine(SpinAttackRoutine(ability)); break;
                case SpecialAttackKind.Dash: StartCoroutine(DashAttackRoutine(ability)); break;
                default:
                    // Reached only for a misauthored asset, and only after the cost has been
                    // charged — the branch that calls this deliberately mirrors the cast path's
                    // order rather than validating the kind a second time earlier.
                    Debug.LogWarning($"PerformSpecialMeleeAttack: '{ability.AbilityID}' has " +
                                     $"IsSpecialAttack set but SpecialKind None - nothing to run.");
                    break;
            }
        }

        /// <summary>
        /// A 360 degree sweep repeated <see cref="SpinTicks"/> times. Uses no new state flag:
        /// _isAttacking already suspends movement, blocks a second swing, a dodge and a cast, and is
        /// cleared defensively in OnDisable and on death. A second flag would be two more places to
        /// clear and two more ways to strand the player.
        /// </summary>
        private IEnumerator SpinAttackRoutine(AbilityData ability)
        {
            // Same discipline as MeleeHitboxRoutine and RollRoutine: a stuck _isAttacking gates
            // every attack, cast and step of movement for the rest of the session, so the reset
            // lives in a finally and the flag is raised before the first yield.
            _isAttacking = true;

            try
            {
                SetAnimatorTrigger("SpecialAttack");

                // Once, at the start. Zeroing per tick would suspend gravity for the whole spin -
                // the reason is spelled out in RollRoutine.
                _rb.velocity = Vector3.zero;

                // ⚠ Deliberately no SetFacing during the spin. The sprite is a billboard that only
                // flips left/right, so turning the facing three times would read as the character
                // twitching, not spinning. The clip sells the rotation; the facing stays put.
                Vector3 facing = _facingDir.sqrMagnitude > 0.001f ? _facingDir.normalized : transform.forward;
                facing.y = 0f;
                if (facing.sqrMagnitude < 0.001f) facing = Vector3.forward;
                facing.Normalize();

                int ticks = Mathf.Max(1, SpinTicks);
                float interval = SpinDuration / ticks;
                int damage = ComputeMeleeDamage(SpinDamageMultiplier);
                float reach = SpinRange > 0f ? SpinRange : MeleeRange;

                for (int t = 0; t < ticks; t++)
                {
                    yield return new WaitForSeconds(interval);

                    if (_isDead || (_health != null && _health.IsDead)) yield break;
                    if (_isKnockedBack) yield break;   // being hit wins, the same rule the roll uses

                    Vector3 sphereCenter = transform.position + Vector3.up * (EKVibe.CharacterHeight * 0.5f);

                    // Per tick, not per spin: standing inside the spin is meant to hurt repeatedly.
                    _hitThisSwing.Clear();
                    ResolveMeleeSweep(sphereCenter, facing, reach, 360f, damage);
                }

                yield return new WaitForSeconds(MeleeRecovery);
            }
            finally
            {
                _isAttacking = false;
                // ⚠ No player controller has a Special STATE yet, only the SpecialAttack trigger
                // parameter, so a set trigger latches forever and would fire a special animation at
                // an arbitrary moment the day a special sheet is imported.
                ClearAnimatorTrigger("SpecialAttack");
            }
        }

        /// <summary>
        /// A committed forward lunge that sweeps as it travels. Structurally the roll's twin, but it
        /// does not call it — it reuses exactly one thing, <see cref="RollSpeedCurve"/>, whose
        /// integral over [0,1] is 1 and is therefore what makes DashDistance mean metres.
        /// </summary>
        private IEnumerator DashAttackRoutine(AbilityData ability)
        {
            _isAttacking = true;

            try
            {
                // Unlike the roll, the dash faces where it goes. PerformDodge deliberately does NOT
                // SetFacing so you can roll backwards out of a fight; a dash is an attack and has
                // to commit to a direction.
                Vector3 dir = GetScreenRelativeMoveDirection(ReadMoveInput());
                if (dir.sqrMagnitude < 0.0001f) dir = _facingDir;
                dir.y = 0f;
                if (dir.sqrMagnitude < 0.0001f) dir = Vector3.forward;
                dir.Normalize();
                SetFacing(dir);

                // The dash reuses the Roll clip: SpecialAttack is the one special trigger and the
                // spin has it, and Roll is a 0.43 s lunge that reads correctly here.
                SetAnimatorTrigger("Roll");

                _rb.velocity = Vector3.zero;   // once, not per step - see RollRoutine

                int damage = ComputeMeleeDamage(DashDamageMultiplier);
                float reach = DashRange > 0f ? DashRange : MeleeRange;

                // Once for the whole dash: passing an enemy must cost them one hit, not one per
                // physics step. This is the opposite of the spin, and it is the reason the sweep
                // helper leaves the clear to its caller.
                _hitThisSwing.Clear();

                // ⚠ Snapshotted, then polled every step. CurrentChunkData is written from eight
                // places across six files, so hooking one transition would miss the others. A dash
                // into an edge trigger starts a transition, which pauses and teleports the player:
                // without this the dash resumes on the far side and drives the body away from the
                // arrival marker.
                ChunkManager chunkManager = ChunkManager.Instance;
                MapChunkData chunkAtStart = chunkManager != null ? chunkManager.CurrentChunkData : null;

                float elapsed = 0f;
                var wait = new WaitForFixedUpdate();

                while (elapsed < DashDuration)
                {
                    // Cooperative cancellation, checked before moving, as in RollRoutine.
                    if (_isDead || (_health != null && _health.IsDead)) yield break;
                    if (_isKnockedBack) yield break;
                    // Cancels rather than suspends. A pause already freezes this loop, because
                    // timeScale 0 stops FixedUpdate; this exists for the frame where a pause is
                    // pushed and popped around a teleport, and because resuming a committed lunge
                    // after the player closes their inventory is the wrong behaviour.
                    if (Systems.PauseManager.IsPaused) yield break;
                    if (chunkManager != null
                        && (chunkManager.IsTransitioning || chunkManager.CurrentChunkData != chunkAtStart))
                        yield break;

                    float speed = DashDistance / DashDuration * RollSpeedCurve(elapsed / DashDuration);

                    // ⚠ MovePosition, never a transform write: this Rigidbody is non-kinematic so
                    // MovePosition sweeps and resolves against colliders. Enemy capsules are solid,
                    // so the dash STOPS at the first enemy it reaches. That is the intended feel.
                    _rb.MovePosition(_rb.position + dir * (speed * Time.fixedDeltaTime));

                    Vector3 sphereCenter = transform.position + Vector3.up * (EKVibe.CharacterHeight * 0.5f);
                    ResolveMeleeSweep(sphereCenter, dir, reach, DashArcAngle, damage);

                    elapsed += Time.fixedDeltaTime;
                    yield return wait;
                }

                yield return new WaitForSeconds(MeleeRecovery);
            }
            finally
            {
                _isAttacking = false;
            }
        }

        /// <summary>
        /// Percent of the live maximum, floored, minimum 1 — the same shape as
        /// <see cref="CurrentRollCost"/> and for the reason its comment gives: a flat cost silently
        /// becomes cheaper every level as MaxManaStamina grows. AbilityData.ResourceCost is
        /// deliberately NOT read here, and the two assets carry ResourceType None so the generic
        /// charge on the cast path would be a no-op even if this branch were ever removed.
        /// </summary>
        private int SpecialStaminaCost(AbilityData ability)
        {
            float pct = ability.SpecialKind == SpecialAttackKind.Spin ? SpinStaminaPercent : DashStaminaPercent;
            return PlayerData != null
                ? Mathf.Max(1, Mathf.FloorToInt(PlayerData.MaxManaStamina * pct / 100f))
                : 12;
        }

        /// <summary>The class a special's class gate is tested against; the default before a session binds.</summary>
        private static PlayerClass CurrentPlayerClass()
        {
            var session = Flow.PlayerSession.Instance;
            return session != null ? session.Class : PlayerClass.YoungDriller;
        }
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

            // Defense in depth against a second landed hit starting a second slide while one is
            // already running. The slide's own i-frames (above) close the main window that let
            // that happen, but two knockback-capable enemies hitting in the same frame could still
            // both land. Mirrors EnemyAI.ApplyKnockback's own guard: stop the old routine and reset
            // its flag by hand rather than trust its finally ran first, then replace it — whichever
            // slide finishes now sets _isKnockedBack false only for the routine it actually owns.
            if (_knockbackRoutine != null)
            {
                StopCoroutine(_knockbackRoutine);
                _knockbackRoutine = null;
            }
            _isKnockedBack = false;

            _knockbackRoutine = StartCoroutine(KnockbackRoutine(dir.normalized, distance));
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

                // The slide itself is also an i-frame window, not just its aftermath. The hit that
                // triggered this knockback only landed because the player was NOT invulnerable a
                // moment ago, so without this a second attacker can land a free hit mid-slide, before
                // KnockbackRecoveryIFrames even starts. Mathf.Max so a longer window already running
                // (e.g. a roll's own i-frames) is never shortened.
                _invulnerableUntil = Mathf.Max(_invulnerableUntil, Time.time + KnockbackSlideDuration);

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
                _knockbackRoutine = null;
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
            _isActivelyDodging = false;
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
            if (_health != null)
            {
                _health.Revive(max);
            }
            else
            {
                foreach (var col in GetComponentsInChildren<Collider>(true))
                    col.enabled = true;
            }
            CurrentHealth = max;
            CurrentMana = PlayerData != null ? PlayerData.MaxManaStamina : 50;
            CurrentStamina = CurrentMana;
            _isDead = false;
            _isAttacking = false;
            _isRolling = false;
            _isKnockedBack = false;
            _isActivelyDodging = false;
            _invulnerableUntil = 0f;
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

        /// <summary>How many special-attack buttons the HUD's action row builds. Two: SPN and DSH.
        /// The Inspector list is allowed to be shorter - a missing entry paints its button dimmed
        /// rather than failing.</summary>
        public const int SpecialSlots = 2;

        /// <summary>Null-safe read of a special slot, for the HUD's availability painting.</summary>
        public AbilityData GetSpecial(int index)
        {
            if (SpecialAttacks == null || index < 0 || index >= SpecialAttacks.Count) return null;
            return SpecialAttacks[index];
        }

        /// <summary>0 = ready; otherwise seconds left on the special's cooldown, for the HUD's
        /// radial overlay. Separate from <see cref="GetCooldownRemaining"/> because that one
        /// indexes EquippedAbilities and would read the wrong list entirely.</summary>
        public float GetSpecialCooldownRemaining(int index, out float total)
        {
            total = 0f;
            AbilityData ability = GetSpecial(index);
            if (ability == null) return 0f;

            total = ability.CooldownTime;
            return _abilityCooldowns.TryGetValue(ability.AbilityID, out float remaining)
                ? Mathf.Max(0f, remaining)
                : 0f;
        }

        public void TryCastAbility(int slotIndex)
        {
            if (EquippedAbilities == null || slotIndex < 0 || slotIndex >= EquippedAbilities.Count) return;
            TryUseAbility(EquippedAbilities[slotIndex]);
        }

        /// <summary>
        /// The two special attacks, by position in <see cref="SpecialAttacks"/>: 0 is SPN, 1 is
        /// DSH. Resolved by index and never by id, because a special attack must never become
        /// something the game looks up by AbilityID - see the comment on the field.
        /// </summary>
        public void TrySpecialAttack(int index)
        {
            if (SpecialAttacks == null || index < 0 || index >= SpecialAttacks.Count) return;
            TryUseAbility(SpecialAttacks[index]);
        }

        /// <summary>
        /// One copy of everything a cast and a special share: the gates, the riding refusal, the
        /// cooldown, the stealth break. Both entry points resolve their own slot first and hand
        /// the asset down here.
        /// </summary>
        private void TryUseAbility(AbilityData ability)
        {
            if (_isAttacking || _isRolling || _isKnockedBack || _isDead) return;
            if (BlockedByRiding()) return;
            if (ability == null) return;

            if (_abilityCooldowns.ContainsKey(ability.AbilityID) && _abilityCooldowns[ability.AbilityID] > 0f)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat($"{ability.AbilityName} is on cooldown.");
                return;
            }

            if (ability.IsSpecialAttack)
            {
                // ⚠ The special branch leaves BEFORE the concealment drain below and before
                // CastAbilityRoutine's shout. A special attack is a weapon swing, not magic: it
                // must not drain Concealment and must not shout a spell name.
                if (!ability.CanBeUsedBy(CurrentPlayerClass()))
                {
                    if (UIManager.Instance != null)
                        UIManager.Instance.LogCombat("You don't know how to do that.");
                    return;
                }

                // A percent of the live maximum, not ability.ResourceCost - see SpecialStaminaCost.
                // Read once into a local so the check and the spend charge the same number even if
                // the maximum moved between them, the same rule PerformDodge follows for the roll.
                int cost = SpecialStaminaCost(ability);
                if (CurrentStamina < cost)
                {
                    if (UIManager.Instance != null)
                        UIManager.Instance.LogCombat("Not enough Stamina.");
                    return;
                }
                CurrentStamina -= cost;

                BeginAbilityCooldown(ability);
                BreakStealth();
                PerformSpecialMeleeAttack(ability);
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

            BeginAbilityCooldown(ability);

            // Magic is a secret — casting it drains your Concealment meter.
            if (IsMagic(ability) && IsInCity())
            {
                Systems.WantedManager.Instance?.DrainConcealment(34f); // 3 spells = busted
                if (UIManager.Instance != null)
                    UIManager.Instance.ShowToast("Easy with the spells there Potter, not around the plebs yeah?");
            }

            // Casting is not sneaking either.
            BreakStealth();

            StartCoroutine(CastAbilityRoutine(ability));
        }

        /// <summary>Starts an ability's cooldown and registers its key for the per-frame countdown.
        /// The parallel key list is what keeps that countdown from iterating the dictionary and
        /// allocating an enumerator every frame.</summary>
        private void BeginAbilityCooldown(AbilityData ability)
        {
            _abilityCooldowns[ability.AbilityID] = ability.CooldownTime;
            if (!_activeCooldownKeys.Contains(ability.AbilityID))
                _activeCooldownKeys.Add(ability.AbilityID);
        }

        /// <summary>
        /// Stands the player up if they were crouched. Routed through ToggleStealth rather than
        /// clearing the speed modifier here, so the sprite tint, the toast and the CRO button all
        /// come back in step - that is ToggleStealth's job, and duplicating half of it would
        /// drift. Four callers: the swing, the roll, a cast and a special attack.
        /// </summary>
        private void BreakStealth()
        {
            var stealth = StealthController.Instance;
            if (stealth != null && stealth.IsCrouched)
                stealth.ToggleStealth();
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

                if (_isDead || (_health != null && _health.IsDead)) yield break;

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
