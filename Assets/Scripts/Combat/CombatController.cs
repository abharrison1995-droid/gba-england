using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.EventSystems;
using ExiledAlvaston.Data;
using ExiledAlvaston.UI;
using ExiledAlvaston.Vibe;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Combat
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

        [Header("Movement")]
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

        [Header("Regen")]
        [Tooltip("Mana restored per second — slow, spells should feel budgeted.")]
        public float ManaRegenPerSecond = 2.5f;
        [Tooltip("Stamina restored per second — fast, physical skills cycle often.")]
        public float StaminaRegenPerSecond = 7f;

        [Header("Abilities")]
        public List<AbilityData> EquippedAbilities;

        private Dictionary<string, float> _abilityCooldowns = new Dictionary<string, float>();
        private List<string> _activeCooldownKeys = new List<string>(10);

        private bool _isAttacking;
        private bool _isDead;
        private readonly Collider[] _hitResults = new Collider[10];
        private readonly HashSet<Health> _hitThisSwing = new HashSet<Health>();
        private float _manaRegenCarry;
        private float _staminaRegenCarry;
        /// <summary>Last non-zero move direction — melee aims this way while idle.</summary>
        private Vector3 _facingDir = Vector3.forward;

        public Vector3 FacingDirection => _facingDir;
        public bool IsDead => _isDead;

        private void Awake()
        {
            Instance = this;
            _rb = GetComponent<Rigidbody>();
            _health = GetComponent<Health>();
            _actorVisual = GetComponent<WorldActorVisual>();
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
        }

        private void Start()
        {
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
        }

        /// <summary>False on Title/Creator — the player must not move, attack, or regen there.</summary>
        private static bool IsFlowPlaying()
        {
            var flow = ExiledAlvaston.Flow.GameFlowController.Instance;
            return flow == null || flow.State == ExiledAlvaston.Flow.GameFlowState.Playing;
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

            if (!_isAttacking && !_isDead)
                HandleMovement();
        }

        private void RegenResources()
        {
            int max = PlayerData != null ? PlayerData.MaxManaStamina : 50;

            _manaRegenCarry += ManaRegenPerSecond * Time.deltaTime;
            if (_manaRegenCarry >= 1f)
            {
                int whole = Mathf.FloorToInt(_manaRegenCarry);
                _manaRegenCarry -= whole;
                CurrentMana = Mathf.Min(max, CurrentMana + whole);
            }

            _staminaRegenCarry += StaminaRegenPerSecond * Time.deltaTime;
            if (_staminaRegenCarry >= 1f)
            {
                int whole = Mathf.FloorToInt(_staminaRegenCarry);
                _staminaRegenCarry -= whole;
                CurrentStamina = Mathf.Min(max, CurrentStamina + whole);
            }
        }

        private void PushHud()
        {
            if (UIManager.Instance == null) return;

            int hp = _health != null ? _health.CurrentHealth : CurrentHealth;
            int hpMax = _health != null ? _health.MaxHealth : (PlayerData != null ? PlayerData.MaxHealth : 100);
            CurrentHealth = hp;

            UIManager.Instance.UpdatePlayerHealth(hp, hpMax);
            UIManager.Instance.UpdatePlayerMana(CurrentMana, PlayerData != null ? PlayerData.MaxManaStamina : 50);
        }

        private void HandleInput()
        {
#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            // Desktop fallback only — mobile uses HUD ATK button.
            // Skip clicks that land on UI so HUD taps don't also swing.
            if (Input.GetButtonDown("Fire1") && !_isAttacking && !IsPointerOverUI())
                PerformMeleeAttack();
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

        private void HandleMovement()
        {
            Vector2 input = ReadMoveInput();
            if (input.sqrMagnitude < 0.0001f)
            {
                if (PlayerAnimator != null) PlayerAnimator.SetFloat("Speed", 0f);
                return;
            }

            if (input.sqrMagnitude > 1f)
                input.Normalize();

            Vector3 moveDir = GetScreenRelativeMoveDirection(input);
            if (moveDir.sqrMagnitude < 0.0001f) return;

            SetFacing(moveDir);
            _rb.MovePosition(_rb.position + moveDir * (MovementSpeed * input.magnitude * Time.fixedDeltaTime));

            if (PlayerAnimator != null) PlayerAnimator.SetFloat("Speed", input.magnitude);
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
        private Vector2 ReadMoveInput()
        {
            Vector2 keyboard = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
            Vector2 stick = Joystick != null ? Joystick.InputVector : Vector2.zero;

            if (stick.sqrMagnitude > 0.01f && keyboard.sqrMagnitude > 0.01f)
                return Vector2.ClampMagnitude(stick + keyboard, 1f);
            if (stick.sqrMagnitude > 0.01f)
                return stick;
            return keyboard;
        }

        private static Vector3 GetScreenRelativeMoveDirection(Vector2 input)
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

            _isAttacking = true;

            // Lock body to last faced direction for this swing
            if (_facingDir.sqrMagnitude > 0.001f)
                SetFacing(_facingDir);

            if (PlayerAnimator != null)
                PlayerAnimator.SetTrigger("MeleeAttack");

            if (_actorVisual == null)
                _actorVisual = GetComponent<WorldActorVisual>();
            if (_actorVisual != null)
                _actorVisual.PlayMeleeSwing(_facingDir);

            _rb.velocity = Vector3.zero;
            StartCoroutine(MeleeHitboxRoutine(MeleeHitDelay, MeleeRecovery));
        }

        private IEnumerator MeleeHitboxRoutine(float delay, float attackDuration)
        {
            yield return new WaitForSeconds(delay);

            Vector3 facing = _facingDir.sqrMagnitude > 0.001f ? _facingDir.normalized : transform.forward;
            facing.y = 0f;
            if (facing.sqrMagnitude < 0.001f) facing = Vector3.forward;
            facing.Normalize();

            float hitRadius = 1.15f;
            float hitReach = 1.35f;
            // Always aim from last facing — ignore a stale AttackPoint that doesn't follow aim
            Vector3 hitCenter = transform.position + facing * hitReach;
            if (AttackPoint != null)
                hitCenter = transform.position + facing * Vector3.Distance(transform.position, AttackPoint.position);

            int hitCount = Physics.OverlapSphereNonAlloc(hitCenter, hitRadius, _hitResults);
            int damage = PlayerData != null ? PlayerData.BaseTraits.Strength * 2 + 5 : 10;

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

                // Must be roughly in front of the facing direction
                Vector3 toTarget = targetHealth.transform.position - transform.position;
                toTarget.y = 0f;
                if (toTarget.sqrMagnitude > 0.01f)
                {
                    float ahead = Vector3.Dot(toTarget.normalized, facing);
                    if (ahead < 0.15f) continue; // behind / beside — ignore
                }

                string foeName = string.IsNullOrEmpty(targetHealth.DisplayName)
                    ? targetHealth.name.Replace("(Clone)", "").Trim()
                    : targetHealth.DisplayName;
                targetHealth.TakeDamage(damage, "you", foeName);
            }

            yield return new WaitForSeconds(attackDuration);
            _isAttacking = false;
        }

        private void OnDrawGizmosSelected()
        {
            Vector3 facing = Application.isPlaying && _facingDir.sqrMagnitude > 0.001f
                ? _facingDir
                : transform.forward;
            facing.y = 0f;
            if (facing.sqrMagnitude < 0.001f) facing = Vector3.forward;
            facing.Normalize();

            Gizmos.color = Color.red;
            Vector3 center = transform.position + facing * 1.35f;
            Gizmos.DrawWireSphere(center, 1.15f);
            Gizmos.DrawLine(transform.position, transform.position + facing * 2f);
        }
        #endregion

        #region Health & Damage
        /// <summary>Legacy entry point — routes through Health so death/feedback stay unified.</summary>
        public void TakeDamage(int damage)
        {
            if (_health != null)
            {
                _health.TakeDamage(damage, "Enemy", "you");
                CurrentHealth = _health.CurrentHealth;
            }
            else
            {
                CurrentHealth -= damage;
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat($"Something hits you, {damage}");
            }
        }

        private void OnHealthDamaged(int damage)
        {
            CurrentHealth = _health.CurrentHealth;
            if (PlayerAnimator != null) PlayerAnimator.SetTrigger("Hit");
        }

        private void OnHealthDeath()
        {
            if (_isDead) return;
            _isDead = true;
            _isAttacking = false;
            _rb.velocity = Vector3.zero;
            if (PlayerAnimator != null) PlayerAnimator.SetFloat("Speed", 0f);

            if (ExiledAlvaston.Flow.GameFlowController.Instance != null)
                ExiledAlvaston.Flow.GameFlowController.Instance.HandlePlayerDeath();
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

            if (PlayerAnimator != null) PlayerAnimator.SetTrigger("CastSpell");

            // Shout the (player-named) spell overhead as you cast: "Spark Out!"
            string shout = IsMagic(ability) && Flow.PlayerSession.Instance != null
                ? Flow.PlayerSession.Instance.SpellName
                : ability.AbilityName;
            UI.SpellShoutText.Spawn(transform.position, shout);

            yield return new WaitForSeconds(ability.CastTime);

            // Zap the nearest enemy in range; otherwise the bolt just cracks off into the air.
            Vector3 origin = transform.position;
            Health target = FindSpellTarget(ability.Range);
            if (target != null)
            {
                LightningBolt.Spawn(origin, target.transform.position);
                if (ability.BaseDamage > 0)
                    target.TakeDamage(ability.BaseDamage, shout, target.DisplayName);
            }
            else
            {
                LightningBolt.Spawn(origin, origin + FacingDirection * Mathf.Max(2f, ability.Range * 0.6f));
            }

            if (ability.EffectPrefab != null)
                Instantiate(ability.EffectPrefab, origin + FacingDirection * 1.2f, transform.rotation);

            _isAttacking = false;
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
                float sq = (h.transform.position - transform.position).sqrMagnitude;
                if (sq < bestSq) { bestSq = sq; best = h; }
            }
            return best;
        }

        // ---- Magic: learning the first spell ----

        public const int SpellSlots = 4;
        public bool KnowsSpark => _sparkAbility != null;
        private AbilityData _sparkAbility;

        /// <summary>Every spell the player has learned (a superset of the 4 equipped slots).</summary>
        public List<AbilityData> KnownSpells { get; } = new List<AbilityData>();

        /// <summary>Grants the Spark spell. Called by the magic tutorial when Daniel teaches it.</summary>
        public void LearnSpark()
        {
            if (_sparkAbility != null) return;

            _sparkAbility = ScriptableObject.CreateInstance<AbilityData>();
            _sparkAbility.AbilityID = "spark";
            _sparkAbility.AbilityName = "Spark";
            _sparkAbility.IconGlyph = "⚡"; // ⚡ placeholder
            _sparkAbility.CooldownTime = 1.25f;
            _sparkAbility.CastTime = 0.28f;
            _sparkAbility.Range = 8f;
            _sparkAbility.ResourceType = AbilityResourceType.Mana;
            _sparkAbility.ResourceCost = 12;
            _sparkAbility.BaseDamage = 30;

            LearnAbility(_sparkAbility);

            if (Flow.PlayerSession.Instance != null) Flow.PlayerSession.Instance.KnowsSpark = true;
            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("You can feel the spark now — cast it with the spell button.");
        }

        /// <summary>Adds a spell to the spellbook and drops it into the first open spell slot.</summary>
        public void LearnAbility(AbilityData ability)
        {
            if (ability == null) return;
            EnsureSlots();
            if (!KnownSpells.Contains(ability)) KnownSpells.Add(ability);

            if (EquippedAbilities.Contains(ability)) return; // already slotted
            for (int i = 0; i < SpellSlots; i++)
                if (EquippedAbilities[i] == null) { EquippedAbilities[i] = ability; return; }
        }

        /// <summary>Binds a known spell to a slot (spellbook). Clears it from any other slot first.</summary>
        public void AssignToSlot(AbilityData ability, int slot)
        {
            if (slot < 0 || slot >= SpellSlots) return;
            EnsureSlots();
            if (ability != null)
            {
                for (int i = 0; i < SpellSlots; i++)
                    if (EquippedAbilities[i] == ability) EquippedAbilities[i] = null;
                if (!KnownSpells.Contains(ability)) KnownSpells.Add(ability);
            }
            EquippedAbilities[slot] = ability;
        }

        public void ClearSlot(int slot)
        {
            if (slot < 0 || slot >= SpellSlots) return;
            EnsureSlots();
            EquippedAbilities[slot] = null;
        }

        private void EnsureSlots()
        {
            if (EquippedAbilities == null) EquippedAbilities = new List<AbilityData>(SpellSlots);
            while (EquippedAbilities.Count < SpellSlots) EquippedAbilities.Add(null);
        }
        #endregion
    }
}
