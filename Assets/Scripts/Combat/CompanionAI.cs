using UnityEngine;
using UnityEngine.AI;
using System.Collections;
using System.Collections.Generic;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Combat
{
    /// <summary>
    /// Follower AI for an active companion. Follows the player on the X/Z plane with a NavMeshAgent,
    /// keeps out of the player's body, catches up or warps when stranded, and fights HOSTILES ALREADY
    /// FIGHTING THE PLAYER - it never initiates on civilians or police (the Alex design contract).
    ///
    /// Deliberately a separate class from EnemyAI, not a hostile turned toward the player: a companion
    /// has no aggro radius, no nameplate, stops to heal, and must keep following. Mirroring EnemyAI's
    /// NavMeshAgent shape (uniform 0.28 radius, off-mesh capsule-cast fallback) is the correct reuse;
    /// subclassing it would inherit aggro and policing semantics that do not belong to a follower.
    ///
    /// Movement is 3D physics/navigation on the X/Z plane - never Physics2D (CLAUDE.md ?2).
    /// </summary>
    [RequireComponent(typeof(Health))]
    [RequireComponent(typeof(NavMeshAgent))]
    public class CompanionAI : MonoBehaviour
    {
        [Tooltip("Assigned by CompanionManager at spawn, or set on the prefab.")]
        public CompanionDefinition Definition;

        [Header("Follow")]
        public float FollowDistance = 2.2f;
        public float KeepOutDistance = 1.1f;
        [Tooltip("Horizontal distance past which the companion stops walking and warps to the player.")]
        public float WarpDistance = 22f;
        [Tooltip("Horizontal distance at which it gives up pathing and walks straight (stuck recovery).")]
        public float StuckDistance = 3f;

        [Header("Combat")]
        public float RetargetInterval = 0.4f;

        private Health _health;
        private NavMeshAgent _agent;
        private WorldActorVisual _visual;
        private Transform _player;
        private Health _playerHealth;

        private Transform _target;
        private bool _isAttacking;
        private bool _isDodging;
        private bool _disabled; // knockout: stop everything

        private float _nextHealTime;
        private float _nextDodgeTime;

        // Reused across retarget scans so the 0.4s tick allocates nothing.
        private readonly List<EnemyAI> _enemyPool = new List<EnemyAI>(8);

        private const float DodgeSlideDuration = 0.35f;
        private const float DodgeDistance = 2.0f;

        public Health FollowerHealth => _health;

        private void Awake()
        {
            _health = GetComponent<Health>();
            _agent = GetComponent<NavMeshAgent>();
            _visual = GetComponent<WorldActorVisual>();

            // Knockout is not death: the companion must NOT spawn loot/XP and must NOT be destroyed.
            // Health.Die early-returns before its disable block when DestroyOnDeath is false, so this
            // class owns shutdown via OnDeath (see Health.cs commentary).
            _health.DestroyOnDeath = false;
            _health.OnDeath.AddListener(OnCompanionDied);

            _agent.radius = 0.28f;   // same uniform radius as EnemyAI, so it fits doorways
            _agent.height = _visual != null && _visual.Height > 0f ? _visual.Height : 1.55f;
            _agent.obstacleAvoidanceType = ObstacleAvoidanceType.HighQualityObstacleAvoidance;
        }

        private void ApplyDefinition()
        {
            if (Definition == null) return;

            _health.MaxHealth = Mathf.Max(1, Definition.MaxHealth);
            if (_health.CurrentHealth <= 0 || _health.CurrentHealth > _health.MaxHealth)
                _health.CurrentHealth = _health.MaxHealth;

            _agent.speed = Definition.MoveSpeed;
            _agent.angularSpeed = 360f;
            _agent.acceleration = 12f;
            _agent.stoppingDistance = FollowDistance;
        }

        private void Start()
        {
            ApplyDefinition();

            var player = CombatController.Instance;
            if (player != null)
            {
                _player = player.transform;
                _playerHealth = player.GetComponent<Health>();
            }

            SnapToNavMesh();

            // Prime timers so a freshly hired companion does not heal or dodge instantly.
            float now = Time.time;
            _nextHealTime = now + (Definition != null ? Definition.HealCooldown : 20f);
            _nextDodgeTime = now + (Definition != null ? Definition.DodgeCooldown : 9f);

            StartCoroutine(RetargetRoutine());
        }

        private void OnDestroy()
        {
            if (_health != null) _health.OnDeath.RemoveListener(OnCompanionDied);
        }

        /// <summary>CompanionManager listens to this to end the contract and call home.</summary>
        public event System.Action KnockedOut;
        public event System.Action<Health> HealthChanged;

        private void OnCompanionDied()
        {
            if (_disabled) return;
            _disabled = true;

            // Stop fighting and moving; leave the Death animation (the KO pose) visible.
            _agent.enabled = false;
            var ai = GetComponent<EnemyAI>();
            if (ai != null) ai.enabled = false;
            foreach (var col in GetComponentsInChildren<Collider>())
                col.enabled = false;

            SetAnimatorTrigger("Death");
            KnockedOut?.Invoke();
        }

        private void Update()
        {
            if (_disabled) return;
            if (_health != null && _health.IsDead) return;

            // Locomotion parameter: the walk sheet is driven by Speed (0-1), like EnemyAI.
            SetAnimatorFloat("Speed", _agent != null ? _agent.velocity.magnitude / Mathf.Max(0.01f, _agent.speed) : 0f);

            if (_isAttacking || _isDodging) return;

            if (_target != null)
                CombatMove(_target);
            else
                FollowMove();
        }

        // ----- follow -----

        private void FollowMove()
        {
            if (_player == null) return;

            Vector3 toPlayer = _player.position - transform.position;
            toPlayer.y = 0f;
            float dist = toPlayer.magnitude;

            // Stranded far beyond a walk's patience: warp, don't walk.
            if (dist > WarpDistance)
            {
                WarpBesidePlayer(toPlayer);
                return;
            }

            if (dist <= FollowDistance) return; // standing at the player's shoulder is fine

            if (!_agent.isOnNavMesh)
            {
                TryCollideMove(toPlayer.normalized);
                return;
            }

            _agent.isStopped = false;
            if (!_agent.hasPath || (_agent.destination - _player.position).sqrMagnitude > 1f)
                _agent.SetDestination(_player.position);
            if (_visual != null && _agent.velocity.sqrMagnitude > 0.01f)
                _visual.SetFacing(_agent.velocity);
        }

        /// <summary>Warp beside the player, not onto them - resolve against the keep-out distance.</summary>
        private void WarpBesidePlayer(Vector3 toPlayer)
        {
            Vector3 dir = toPlayer.sqrMagnitude > 0.001f ? toPlayer.normalized : Vector3.back;
            Vector3 spot = _player.position - dir * FollowDistance;
            if (NavMesh.SamplePosition(spot, out NavMeshHit hit, 3f, NavMesh.AllAreas))
                _agent.Warp(hit.position);
            else
                _agent.Warp(_player.position);
            if (_visual != null) _visual.SetFacing(-dir);
        }

        // ----- combat -----

        private void CombatMove(Transform target)
        {
            Vector3 toTarget = target.position - transform.position;
            toTarget.y = 0f;
            float dist = toTarget.magnitude;

            float range = Definition != null ? Definition.AttackRange : 1.6f;
            if (dist <= range)
            {
                if (_agent != null && _agent.isOnNavMesh)
                {
                    _agent.isStopped = true;
                    _agent.ResetPath();
                }

                if (toTarget.sqrMagnitude > 0.001f)
                {
                    Quaternion look = Quaternion.LookRotation(toTarget.normalized, Vector3.up);
                    transform.rotation = Quaternion.Slerp(transform.rotation, look, Time.deltaTime * 10f);
                    if (_visual != null) _visual.SetFacing(toTarget);
                }

                if (Time.time >= _nextAttackReadyTime)
                    PerformAttack(target, toTarget);
                return;
            }

            // Close the gap, pathing around walls.
            if (_agent != null && _agent.isOnNavMesh)
            {
                _agent.isStopped = false;
                _agent.speed = Definition != null ? Definition.MoveSpeed : 4.2f;
                Vector3 dest = target.position;
                if (!_agent.hasPath || (_agent.destination - dest).sqrMagnitude > 0.5f)
                    _agent.SetDestination(dest);
                if (_visual != null && _agent.velocity.sqrMagnitude > 0.01f)
                    _visual.SetFacing(_agent.velocity);
            }
            else
            {
                TryCollideMove(toTarget.normalized);
            }
        }

        private float _nextAttackReadyTime;

        private void PerformAttack(Transform target, Vector3 toTarget)
        {
            float cooldown = Definition != null ? Definition.AttackCooldown : 1.3f;
            _nextAttackReadyTime = Time.time + cooldown;
            _isAttacking = true;

            SetAnimatorTrigger("MeleeAttack");
            if (_visual != null) _visual.PlayMeleeSwing(toTarget);

            StartCoroutine(AttackRoutine(target));
        }

        private IEnumerator AttackRoutine(Transform target)
        {
            float windup = Definition != null ? Definition.AttackWindup : 0.3f;
            float range = Definition != null ? Definition.AttackRange : 1.6f;
            int damage = Definition != null ? Definition.Damage : 8;

            yield return new WaitForSeconds(windup);

            if (!_disabled && _health != null && !_health.IsDead && target != null)
            {
                Vector3 toTarget = target.position - transform.position;
                toTarget.y = 0f;
                if (toTarget.magnitude <= range * 1.25f)
                {
                    // Hand the player the kill attribution on land so the world behaves as if the
                    // player did it (LastAttacker matters to police/arrest logic); the attacker name
                    // shown in the combat log is the companion's display name.
                    Health targetHealth = target.GetComponentInParent<Health>();
                    if (targetHealth != null && !targetHealth.IsDead)
                    {
                        targetHealth.TakeDamage(damage, DisplayName, "you", gameObject);
                    }
                }
            }

            yield return new WaitForSeconds(0.15f);
            _isAttacking = false;
        }

        private string DisplayName => Definition != null && !string.IsNullOrEmpty(Definition.DisplayName)
            ? Definition.DisplayName
            : (gameObject.name.Replace("(Clone)", "").Trim());

        // ----- heal / dodge -----

        /// <summary>The companion's own heal cast. Called by the AI when its heal cooldown is up.</summary>
        public bool TryHeal()
        {
            if (_disabled || _health == null || _health.IsDead) return false;
            if (Time.time < _nextHealTime) return false;
            if (Definition == null) return false;

            // Decide target: the badly-injured player first, else self if the spell would top us up.
            Health target = null;
            if (_playerHealth != null && !_playerHealth.IsDead)
            {
                float frac = (float)_playerHealth.CurrentHealth / Mathf.Max(1, _playerHealth.MaxHealth);
                if (frac <= Definition.HealPlayerPriorityFraction) target = _playerHealth;
            }
            if (target == null && _health.CurrentHealth < _health.MaxHealth) target = _health;
            if (target == null) { _nextHealTime = Time.time + 2f; return false; } // nobody needs it; re-check soon

            _nextHealTime = Time.time + Definition.HealCooldown;
            target.Heal(Definition.HealAmount);

            // The cast/grounded-spell animation, toward the target or else toward the player.
            SetAnimatorTrigger("CastSpell");
            if (_visual != null && target != null)
            {
                Vector3 dir = target.transform.position - transform.position;
                dir.y = 0f;
                if (dir.sqrMagnitude > 0.001f) _visual.SetFacing(dir.normalized);
            }
            else if (_visual != null && _player != null)
            {
                Vector3 dir = _player.position - transform.position;
                dir.y = 0f;
                if (dir.sqrMagnitude > 0.001f) _visual.SetFacing(dir.normalized);
            }

            HealthChanged?.Invoke(_health);
            return true;
        }

        /// <summary>The companion's infrequent dodge roll - displacement only, no i-frames.</summary>
        public bool TryDodge()
        {
            if (_disabled || _health == null || _health.IsDead) return false;
            if (Time.time < _nextDodgeTime) return false;
            if (_isDodging || _isAttacking) return false;
            if (Definition == null) return false;

            _nextDodgeTime = Time.time + Definition.DodgeCooldown;
            SetAnimatorTrigger("Roll");
            StartCoroutine(DodgeRoutine());
            return true;
        }

        private IEnumerator DodgeRoutine()
        {
            _isDodging = true;
            try
            {
                // Roll away from the current threat, else back from the player.
                Vector3 dir = _target != null
                    ? (transform.position - _target.position)
                    : (transform.position - (_player != null ? _player.position : transform.position));
                dir.y = 0f;
                if (dir.sqrMagnitude < 0.0001f) dir = Vector3.back;
                dir.Normalize();
                if (_visual != null) _visual.SetFacing(dir);

                float elapsed = 0f;
                while (elapsed < DodgeSlideDuration)
                {
                    if (_disabled || (_health != null && _health.IsDead)) yield break;
                    float speed = DodgeDistance / DodgeSlideDuration * (1.5f - elapsed / DodgeSlideDuration);
                    TryCollideMove(dir, speed * Time.deltaTime);
                    elapsed += Time.deltaTime;
                    yield return null;
                }
            }
            finally
            {
                _isDodging = false;
            }
        }

        // ----- target selection -----

        /// <summary>
        /// Every 0.4s, find an EnemyAI that is aggroed on the player. The companion only ever fights
        /// hostiles already in combat with the player - it never picks its own fights.
        /// </summary>
        private IEnumerator RetargetRoutine()
        {
            var wait = new WaitForSeconds(RetargetInterval);
            while (true)
            {
                if (!_disabled && _health != null && !_health.IsDead)
                {
                    Retarget();

                    // Let behaviour cooldowns drive the occasional heal/dodge rather than a fixed
                    // schedule: try once per tick and the timers gate it.
                    if (_target == null && Time.time >= _nextHealTime) TryHeal();
                    if (_target != null && Time.time >= _nextDodgeTime) TryDodge();
                }

                yield return wait;
            }
        }

        private void Retarget()
        {
            // A dead/finished target drops first.
            if (_target != null)
            {
                Health th = _target.GetComponentInParent<Health>();
                bool gone = _target == null || (th != null && th.IsDead);
                if (_target == null || gone)
                {
                    _target = null;
                    if (_agent != null && _agent.isOnNavMesh) _agent.ResetPath();
                }
            }

            if (_target != null) return;

            if (_player == null) return;

            _enemyPool.Clear();
            // The companion lives at scene root; the chunk's enemies are under the live chunk instance.
            var chunk = ChunkManager.Instance;
            GameObject root = chunk != null ? chunk.CurrentChunkInstance : null;
            if (root != null)
                root.GetComponentsInChildren(false, _enemyPool);

            Transform playerT = _player;
            for (int i = 0; i < _enemyPool.Count; i++)
            {
                EnemyAI enemy = _enemyPool[i];
                if (enemy == null) continue;
                // Only hostiles already locked onto the player.
                if (enemy.AggroTarget == null) continue;
                if (enemy.AggroTarget != playerT) continue;
                if (enemy.GetComponent<Health>() != null && enemy.GetComponent<Health>().IsDead) continue;

                _target = enemy.transform;
                break;
            }
        }

        // ----- helpers -----

        private void SnapToNavMesh()
        {
            if (_agent == null) return;
            if (NavMesh.SamplePosition(transform.position, out NavMeshHit hit, 3f, NavMesh.AllAreas))
            {
                _agent.Warp(hit.position);
                _agent.enabled = true;
            }
            else
            {
                _agent.enabled = false;
                Debug.LogWarning($"{name}: no NavMesh nearby for companion. Bake the chunk's NavMesh first.");
            }
        }

        /// <summary>
        /// Moves the transform up to <paramref name="step"/> along <paramref name="dir"/>, capsule-
        /// casting first because a companion can leave the mesh (a warp-into-air moment) and must not
        /// slip through walls even then. Same convention as EnemyAI.TryStep.
        /// </summary>
        private void TryCollideMove(Vector3 dir, float step)
        {
            if (dir.sqrMagnitude < 0.001f) return;

            Vector3 origin = transform.position + Vector3.up * 0.5f;
            if (Physics.CapsuleCast(origin + Vector3.up * 0.2f, origin + Vector3.up * 0.9f, 0.25f, dir, out RaycastHit hit, step + 0.05f))
            {
                // Slide along walls like the enemy AI does, so the follower gets unstuck on its own.
                Vector3 slide = Vector3.ProjectOnPlane(dir, hit.normal).normalized;
                if (slide.sqrMagnitude > 0.01f &&
                    !Physics.CapsuleCast(origin + Vector3.up * 0.2f, origin + Vector3.up * 0.9f, 0.25f, slide, step))
                    transform.position += slide * step;
                return;
            }

            transform.position += dir * step;
        }

        private void TryCollideMove(Vector3 dir)
        {
            float step = (Definition != null ? Definition.MoveSpeed : 4.2f) * Time.deltaTime;
            TryCollideMove(dir, step);
        }

        private void SetAnimatorTrigger(string trigger)
        {
            if (_visual != null && _visual.SpriteAnimator != null)
            {
                foreach (var p in _visual.SpriteAnimator.parameters)
                {
                    if (p.type == AnimatorControllerParameterType.Trigger && p.name == trigger)
                    {
                        _visual.SpriteAnimator.SetTrigger(trigger);
                        return;
                    }
                }
            }
        }

        private void SetAnimatorFloat(string name, float value)
        {
            if (_visual != null && _visual.SpriteAnimator != null)
            {
                foreach (var p in _visual.SpriteAnimator.parameters)
                {
                    if (p.type == AnimatorControllerParameterType.Float && p.name == name)
                    {
                        _visual.SpriteAnimator.SetFloat(name, value);
                        return;
                    }
                }
            }
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireSphere(transform.position, FollowDistance);
            if (_target != null)
                Gizmos.DrawLine(transform.position, _target.position);
        }
    }
}