using UnityEngine;
using UnityEngine.AI;
using System.Collections;
using ExiledAlvaston.UI;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Combat
{
    /// <summary>
    /// NavMesh pathfinding chase AI with physics collision and wall line-of-sight.
    /// </summary>
    [RequireComponent(typeof(Health))]
    [RequireComponent(typeof(NavMeshAgent))]
    public class EnemyAI : MonoBehaviour
    {
        [Header("Aggro")]
        public float SightRadius = 12f;
        public float AttackRange = 1.6f;
        public float AttackCooldown = 1.2f;
        public int Damage = 5;
        [Tooltip("If true, this enemy zaps the target with a lightning bolt from AttackRange instead of meleeing (set AttackRange high, e.g. 7).")]
        public bool RangedCaster = false;
        public float EyeHeight = 0.95f;
        [Tooltip("Seconds between swing start and damage — stepping out of range dodges the hit.")]
        public float AttackWindup = 0.3f;
        [Tooltip("If true, this enemy is law enforcement. Killing the player triggers arrest instead of death.")]
        public bool IsPolice = false;

        [Header("Movement")]
        public float MoveSpeed = 3.6f;
        public float TurnSpeed = 10f;

        [Header("Animation")]
        [Tooltip("Optional — drives Speed (float, 0-1) and MeleeAttack (trigger), same parameter names as CombatController.PlayerAnimator.")]
        public Animator Animator;

        private Health _selfHealth;
        private WorldActorVisual _visual;
        private NavMeshAgent _agent;
        private Transform _target;
        private float _nextAttackTime;
        private bool _isAttacking;
        private readonly RaycastHit[] _losHits = new RaycastHit[8];

        private void Awake()
        {
            _selfHealth = GetComponent<Health>();
            _visual = GetComponent<WorldActorVisual>();
            _agent = GetComponent<NavMeshAgent>();

            if (_selfHealth != null)
            {
                _selfHealth.OnTakeDamage.AddListener(OnDamaged);
                _selfHealth.OnDeath.AddListener(OnDied);
            }

            _agent.speed = MoveSpeed;
            _agent.angularSpeed = 360f;
            _agent.acceleration = 12f;
            _agent.stoppingDistance = Mathf.Max(0.05f, AttackRange * 0.85f);
            _agent.radius = 0.28f;
            _agent.height = 1.35f;
            _agent.obstacleAvoidanceType = ObstacleAvoidanceType.HighQualityObstacleAvoidance;
            _agent.updateRotation = true;
        }

        private void Start()
        {
            SnapToNavMesh();
            StartCoroutine(PerceptionRoutine());
        }

        private void OnDestroy()
        {
            if (_selfHealth != null)
            {
                _selfHealth.OnTakeDamage.RemoveListener(OnDamaged);
                _selfHealth.OnDeath.RemoveListener(OnDied);
            }
        }

        private void OnDamaged(int amount)
        {
            if (Animator != null)
                Animator.SetTrigger("Hit");
        }

        private void OnDied()
        {
            if (Animator != null)
                Animator.SetTrigger("Death");
        }

        private void Update()
        {
            if (Animator != null)
                Animator.SetFloat("Speed", _agent != null ? _agent.velocity.magnitude / Mathf.Max(0.01f, MoveSpeed) : 0f);

            if (_target == null || _isAttacking) return;
            ChaseAndAttack();
        }

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
                Debug.LogWarning($"{name}: No NavMesh nearby. Bake with Tools/Bake Navigation Mesh after loading a chunk.");
            }
        }

        private IEnumerator PerceptionRoutine()
        {
            var wait = new WaitForSeconds(0.2f);
            while (true)
            {
                if (_target == null)
                {
                    TryAcquireTarget();
                }
                else
                {
                    float dist = Vector3.Distance(transform.position, _target.position);
                    bool lostRange = dist > SightRadius * 1.4f;
                    bool blocked = !HasLineOfSight(_target);
                    bool targetDead = CombatController.Instance != null
                        && _target == CombatController.Instance.transform
                        && CombatController.Instance.IsDead;

                    // Drop aggro if they die, leave range, or duck fully behind cover
                    if (targetDead || lostRange || (blocked && dist > AttackRange))
                    {
                        _target = null;
                        if (_agent != null && _agent.isOnNavMesh)
                            _agent.ResetPath();
                    }
                }

                yield return wait;
            }
        }

        private void TryAcquireTarget()
        {
            var player = CombatController.Instance;
            if (player == null || player.IsDead) return;

            float dist = Vector3.Distance(transform.position, player.transform.position);
            if (dist > SightRadius) return;
            if (!HasLineOfSight(player.transform)) return;

            _target = player.transform;
        }

        /// <summary>
        /// True if nothing with EnvironmentBlocker (walls/buildings) sits between eyes.
        /// </summary>
        public bool HasLineOfSight(Transform target)
        {
            if (target == null) return false;

            Vector3 origin = transform.position + Vector3.up * EyeHeight;
            Vector3 dest = target.position + Vector3.up * EyeHeight;
            Vector3 delta = dest - origin;
            float dist = delta.magnitude;
            if (dist < 0.05f) return true;

            Vector3 dir = delta / dist;
            int count = Physics.RaycastNonAlloc(origin, dir, _losHits, dist, ~0, QueryTriggerInteraction.Ignore);

            float nearestBlock = float.PositiveInfinity;
            float nearestPlayer = float.PositiveInfinity;

            for (int i = 0; i < count; i++)
            {
                Collider col = _losHits[i].collider;
                if (col == null) continue;
                if (col.transform == transform || col.transform.IsChildOf(transform)) continue;

                float d = _losHits[i].distance;

                if (IsPlayerCollider(col, target))
                {
                    if (d < nearestPlayer) nearestPlayer = d;
                    continue;
                }

                if (IsEnvironmentBlock(col))
                {
                    if (d < nearestBlock) nearestBlock = d;
                }
            }

            // Clear LOS if we reach the player before any wall
            if (nearestPlayer < float.PositiveInfinity)
                return nearestPlayer <= nearestBlock;

            // No player hit (layer quirks) — blocked only if a wall is closer than target
            return nearestBlock > dist - 0.05f;
        }

        private static bool IsPlayerCollider(Collider col, Transform target)
        {
            if (col.transform == target || col.transform.IsChildOf(target)) return true;
            if (col.GetComponentInParent<CombatController>() != null) return true;
            return col.CompareTag("Player");
        }

        private static bool IsEnvironmentBlock(Collider col)
        {
            if (col.GetComponentInParent<EnvironmentBlocker>() != null) return true;
            // Fallback for older scenes without the component
            string n = col.gameObject.name;
            return n == "Wall" || n.StartsWith("Wall") || n == "Body" || n == "Roof" || n == "Beam" || n == "DungeonProp";
        }

        private void ChaseAndAttack()
        {
            if (_target == null) return;

            Vector3 toTarget = _target.position - transform.position;
            toTarget.y = 0f;
            float dist = toTarget.magnitude;

            if (dist <= AttackRange && HasLineOfSight(_target))
            {
                if (_agent != null && _agent.isOnNavMesh)
                {
                    _agent.isStopped = true;
                    _agent.ResetPath();
                }

                if (toTarget.sqrMagnitude > 0.001f)
                {
                    Quaternion look = Quaternion.LookRotation(toTarget.normalized, Vector3.up);
                    transform.rotation = Quaternion.Slerp(transform.rotation, look, Time.deltaTime * TurnSpeed);
                    if (_visual != null)
                        _visual.SetFacing(toTarget);
                }

                if (Time.time >= _nextAttackTime)
                    PerformAttack();
                return;
            }

            // Pathfind around walls
            if (_agent != null && _agent.isOnNavMesh)
            {
                _agent.isStopped = false;
                _agent.speed = MoveSpeed;
                if (!_agent.hasPath || (_agent.destination - _target.position).sqrMagnitude > 0.5f)
                    _agent.SetDestination(_target.position);
                if (_visual != null && _agent.velocity.sqrMagnitude > 0.01f)
                    _visual.SetFacing(_agent.velocity);
            }
            else
            {
                // Fallback: collide-aware step if NavMesh missing
                TryCollideMove(toTarget.normalized);
            }
        }

        private void TryCollideMove(Vector3 dir)
        {
            if (dir.sqrMagnitude < 0.001f) return;

            float step = MoveSpeed * Time.deltaTime;
            Vector3 origin = transform.position + Vector3.up * 0.5f;
            if (Physics.CapsuleCast(origin + Vector3.up * 0.2f, origin + Vector3.up * 0.9f, 0.25f, dir, out RaycastHit hit, step + 0.05f))
            {
                if (IsEnvironmentBlock(hit.collider))
                {
                    // Slide along wall
                    Vector3 slide = Vector3.ProjectOnPlane(dir, hit.normal).normalized;
                    if (slide.sqrMagnitude > 0.01f &&
                        !Physics.CapsuleCast(origin + Vector3.up * 0.2f, origin + Vector3.up * 0.9f, 0.25f, slide, step))
                    {
                        transform.position += slide * step;
                    }
                    return;
                }
            }

            transform.position += dir * step;
            if (dir.sqrMagnitude > 0.001f)
            {
                Quaternion look = Quaternion.LookRotation(dir, Vector3.up);
                transform.rotation = Quaternion.Slerp(transform.rotation, look, Time.deltaTime * TurnSpeed);
                if (_visual != null)
                    _visual.SetFacing(dir);
            }
        }

        private void PerformAttack()
        {
            _nextAttackTime = Time.time + AttackCooldown;
            _isAttacking = true;

            if (Animator != null)
                Animator.SetTrigger("MeleeAttack");

            if (_visual != null)
                _visual.PlayMeleeSwing();

            StartCoroutine(AttackRoutine());
        }

        private IEnumerator AttackRoutine()
        {
            // Windup: swing is already animating; damage lands only if the target is still close
            yield return new WaitForSeconds(AttackWindup);

            if (_target != null && _selfHealth != null && !_selfHealth.IsDead)
            {
                Vector3 toTarget = _target.position - transform.position;
                toTarget.y = 0f;
                // Slight grace past AttackRange so grazing hits still land
                if (toTarget.magnitude <= AttackRange * 1.25f)
                {
                    string foe = _selfHealth.DisplayName;

                    if (RangedCaster)
                        LightningBolt.Spawn(transform.position, _target.position);

                    Health playerHp = _target.GetComponentInParent<Health>();
                    if (playerHp != null)
                    {
                        if (!playerHp.IsDead)
                            playerHp.TakeDamage(Damage, foe, "you", gameObject);
                    }
                    else
                    {
                        var combat = _target.GetComponent<CombatController>();
                        if (combat != null)
                            combat.TakeDamage(Damage);
                    }
                }
            }

            // Brief follow-through before the enemy can move again
            yield return new WaitForSeconds(0.15f);
            _isAttacking = false;
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(transform.position, SightRadius);
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(transform.position, AttackRange);

            if (_target != null)
            {
                Gizmos.color = HasLineOfSight(_target) ? Color.green : Color.magenta;
                Gizmos.DrawLine(transform.position + Vector3.up * EyeHeight, _target.position + Vector3.up * EyeHeight);
            }
        }
    }
}
