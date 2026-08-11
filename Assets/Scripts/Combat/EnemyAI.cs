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

        [Header("Knockback")]
        [Tooltip("Metres the target is shoved when this enemy's hit lands. 0 = no knockback. " +
                 "Defaults to 0 so every existing prefab behaves exactly as before — which enemies " +
                 "shove is an Inspector pass, not a code change.")]
        public float KnockbackDistance = 0f;
        [Range(0f, 1f)]
        [Tooltip("Probability a landed hit shoves, rolled per attack. 1 = every hit, 0.35 = about " +
                 "a third. Only consulted when Knockback Distance is above 0.")]
        public float KnockbackChance = 1f;

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
        private bool _isKnockedBack;
        private readonly RaycastHit[] _losHits = new RaycastHit[8];

        /// <summary>May legitimately be null — a hand-built enemy need not carry a nameplate.</summary>
        private EnemyNameplate _plate;

        /// <summary>
        /// Whether the player was inside <see cref="SightRadius"/> at the last perception tick,
        /// regardless of line of sight. Written by <see cref="TryAcquireTarget"/>, which already
        /// computes the distance, so this costs nothing extra.
        /// </summary>
        private bool _playerInSight;

        /// <summary>True while this enemy is chasing something.</summary>
        public bool HasAggro => _target != null;

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
            _agent.radius = 0.28f;   // deliberately uniform: a wider agent gets stuck in doorways

            // Was hardcoded to 1.35, which quietly overrode whatever the prefab said — so an Orc
            // authored with a 2.16 agent under a 2.16 collider still walked around as a 1.35 one.
            // Take the actor's real height when it has a visual, and fall back to whatever the
            // prefab was authored with rather than to a constant, so a hand-tuned agent survives.
            if (_visual != null && _visual.Height > 0f)
                _agent.height = _visual.Height;
            _agent.obstacleAvoidanceType = ObstacleAvoidanceType.HighQualityObstacleAvoidance;
            _agent.updateRotation = true;
        }

        private void Start()
        {
            // ⚠ Resolved here rather than in Awake. AddComponent runs Awake synchronously, and
            // TutorialSequence builds its bandit by adding the EnemyAI *before* the nameplate — an
            // Awake lookup would cache null and that bandit's plate would never be pushed to.
            // Start runs after every component added in the same frame.
            _plate = GetComponent<EnemyNameplate>();

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
            SetAnimatorTrigger("Hit");
        }

        private void OnDied()
        {
            SetAnimatorTrigger("Death");
        }

        /// <summary>
        /// SetTrigger on a controller that lacks the parameter logs an error every call — the same
        /// guard CombatController has, and for the same reason: enemy controllers are authored per
        /// prefab and may not define every trigger (Knockback exists on none of them yet).
        /// </summary>
        private void SetAnimatorTrigger(string trigger)
        {
            if (Animator == null) return;
            foreach (var p in Animator.parameters)
            {
                if (p.type == AnimatorControllerParameterType.Trigger && p.name == trigger)
                {
                    Animator.SetTrigger(trigger);
                    return;
                }
            }
        }

        private void Update()
        {
            if (Animator != null)
                Animator.SetFloat("Speed", _agent != null ? _agent.velocity.magnitude / Mathf.Max(0.01f, MoveSpeed) : 0f);

            if (_target == null || _isAttacking || _isKnockedBack) return;
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
                Debug.LogWarning($"{name}: No NavMesh nearby. Bake with Tools/World/Bake Navigation Mesh after loading a chunk.");
            }
        }

        /// <summary>
        /// Aggro and proximity, re-evaluated five times a second — and, at the end of each tick,
        /// pushed to this enemy's nameplate.
        ///
        /// ⚠ A push, not a poll. Nothing is added to any Update or LateUpdate: this routine already
        /// exists, already runs at 0.2 s and already does the distance maths, so the gate costs a
        /// nameplate nothing per frame. It is also deliberately not a static aggro counter — a
        /// counter has to be decremented in OnDestroy, and a chunk teardown that destroys thirty
        /// aggroed enemies in one frame is exactly where such a counter drifts and never recovers.
        /// This coroutine is a while(true) on the enemy, so it dies with the object: no
        /// unsubscribe, no static state, nothing to leak across a chunk transition.
        /// </summary>
        private IEnumerator PerceptionRoutine()
        {
            var wait = new WaitForSeconds(0.2f);
            while (true)
            {
                if (_target == null)
                {
                    _playerInSight = false;
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

                // Aggro OR proximity: the plate appears as the player comes within sight radius,
                // so a fight can be judged before it is taken rather than learned from the first
                // hit. Dropping the second term is a one-word change if it proves too noisy.
                if (_plate != null)
                    _plate.SetEngaged(_target != null || _playerInSight);

                // Same push, the other way: the player's own bar stays up for the whole fight and
                // fades a few seconds after the last enemy loses interest.
                if (_target != null && CombatController.Instance != null
                    && _target == CombatController.Instance.transform)
                    CombatController.Instance.PingHealthBar();

                yield return wait;
            }
        }

        private void TryAcquireTarget()
        {
            var player = CombatController.Instance;
            if (player == null || player.IsDead) return;

            float dist = Vector3.Distance(transform.position, player.transform.position);
            if (dist > SightRadius) return;

            // Set before the line-of-sight test on purpose: the nameplate gate is about how close
            // the player is, not about whether this enemy can see them round a corner.
            _playerInSight = true;

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
            // Facing follows the intent, not the slide — and a wall-slide deliberately turns
            // nothing, exactly as before the cast was factored out.
            if (!TryStep(dir, step, out bool slid) || slid) return;

            Quaternion look = Quaternion.LookRotation(dir, Vector3.up);
            transform.rotation = Quaternion.Slerp(transform.rotation, look, Time.deltaTime * TurnSpeed);
            if (_visual != null)
                _visual.SetFacing(dir);
        }

        /// <summary>
        /// Moves the transform up to <paramref name="step"/> metres along <paramref name="dir"/>,
        /// capsule-casting first because an enemy is NOT moved by a Rigidbody — a bare
        /// transform.position += punches straight through geometry. Returns false only when even
        /// the wall-slide was blocked. ⚠ This is the one place in the knockback work where the
        /// capsule cast is essential; the PLAYER's knockback deliberately uses MovePosition
        /// instead, because that Rigidbody is non-kinematic and sweeps for free. The asymmetry is
        /// intentional, not drift.
        /// </summary>
        private bool TryStep(Vector3 dir, float step, out bool slid)
        {
            slid = false;
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
                        slid = true;
                        return true;
                    }
                    return false;
                }
            }

            transform.position += dir * step;
            return true;
        }

        private void PerformAttack()
        {
            _nextAttackTime = Time.time + AttackCooldown;
            _isAttacking = true;

            SetAnimatorTrigger("MeleeAttack");

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
                        // Both branches gate the shove on the hit LANDING. TakeDamage returns false
                        // when the player is in i-frames, which is the whole point of the return
                        // value: without it a dodged hit still knocks the player back.
                        if (!playerHp.IsDead && playerHp.TakeDamage(Damage, foe, "you", gameObject))
                            TryKnockback(toTarget);
                    }
                    else
                    {
                        var combat = _target.GetComponent<CombatController>();
                        if (combat != null && combat.TakeDamage(Damage))
                            TryKnockback(toTarget);
                    }
                }
            }

            // Brief follow-through before the enemy can move again
            yield return new WaitForSeconds(0.15f);
            _isAttacking = false;
        }

        /// <summary>
        /// Shoves the target if this enemy shoves at all, and if the per-attack roll comes up.
        ///
        /// Called only when the hit LANDED — a hit refused by the player's i-frames never reaches
        /// here — so the chance is a chance to shove, not a chance to hit. The two must not be
        /// conflated: rolling here does not affect damage, and a dodged hit is already gone.
        ///
        /// ⚠ Default is 1, not 0. Appending a field defaulted to 0 would have silently switched
        /// off every knockback the moment it landed, because no prefab on disk carries the key yet
        /// and a missing key reads back as the field initialiser. 1 means "distance alone still
        /// means always", which is what the existing tuning notes assume.
        /// </summary>
        private void TryKnockback(Vector3 toTarget)
        {
            if (KnockbackDistance <= 0f || toTarget.sqrMagnitude <= 0.001f) return;

            // The >= 1 short-circuit is not a micro-optimisation: Random.value is inclusive of 1,
            // so a bare `Random.value < KnockbackChance` would refuse roughly one hit in ten
            // million at a chance of exactly 1. Rare enough to never be reproduced, and exactly
            // the kind of thing that gets blamed on something else.
            if (KnockbackChance < 1f && Random.value >= KnockbackChance) return;

            var cc = _target.GetComponentInParent<CombatController>();
            if (cc != null) cc.ApplyKnockback(toTarget.normalized, KnockbackDistance);
        }

        /// <summary>Seconds the slide lasts — mirrors the player's fixed feel value.</summary>
        private const float KnockbackSlideDuration = 0.22f;

        /// <summary>
        /// Shoves this enemy <paramref name="distance"/> metres along <paramref name="dir"/>. Called
        /// by the player's melee site only when the hit landed AND the enemy is still alive —
        /// Health.Die has already disabled this component on a kill, and sliding a corpse would
        /// fight the destroy delay.
        ///
        /// ⚠ The agent is never disabled (agent.enabled stays true throughout): if the enemy dies
        /// mid-slide, Health.Die disables this whole component, and whether a stopped coroutine's
        /// finally runs is not something this repo can verify — a disabled agent could be left on a
        /// corpse forever. updatePosition = false achieves the same "stop fighting the transform"
        /// without that hazard.
        /// </summary>
        public void ApplyKnockback(Vector3 dir, float distance)
        {
            if (_selfHealth != null && _selfHealth.IsDead) return;
            dir.y = 0f;
            if (dir.sqrMagnitude < 0.0001f || distance <= 0f) return;
            StartCoroutine(KnockbackRoutine(dir.normalized, distance));
        }

        private IEnumerator KnockbackRoutine(Vector3 dir, float distance)
        {
            _isKnockedBack = true;   // Update is gated on this, so ChaseAndAttack cannot repath
                                     // against the slide every frame and fight it.
            try
            {
                // Guarded, unlike the raw SetTrigger calls this class used to make: no enemy
                // controller defines Knockback yet (Phase 3 art), and an undefined trigger logs
                // an error every call.
                SetAnimatorTrigger("Knockback");

                if (_agent != null)
                {
                    if (_agent.isOnNavMesh)
                    {
                        _agent.isStopped = true;
                        _agent.ResetPath();
                    }
                    _agent.updatePosition = false;
                }

                float elapsed = 0f;
                while (elapsed < KnockbackSlideDuration)
                {
                    // Death mid-slide bails here; the finally still resyncs the agent.
                    if (_selfHealth != null && _selfHealth.IsDead) yield break;

                    // Same fast-out/slow-in shape as the player's slide — integral 1 over [0,1],
                    // so the slide covers exactly the distance it was given.
                    float speed = distance / KnockbackSlideDuration *
                                  (1.5f - elapsed / KnockbackSlideDuration);

                    // Per FRAME (yield null), not per physics step: an enemy moves by transform,
                    // not Rigidbody — the same convention TryCollideMove uses. And it moves
                    // through TryStep's capsule cast, because transform.position += would punch
                    // straight through walls. The player's knockback does the exact opposite on
                    // purpose; see the comment on CombatController.KnockbackRoutine.
                    TryStep(dir, speed * Time.deltaTime, out _);

                    elapsed += Time.deltaTime;
                    yield return null;
                }
            }
            finally
            {
                // Only a LIVING enemy gets its agent back. If the slide was cut short by death,
                // Health.Die has already disabled the agent and this component on purpose — and
                // SnapToNavMesh re-enables the agent, so running it here would resurrect a
                // corpse's navigation.
                if (_agent != null && (_selfHealth == null || !_selfHealth.IsDead))
                {
                    _agent.updatePosition = true;
                    // Resync the agent's internal position to where the slide left the body...
                    _agent.Warp(transform.position);
                    // ...then re-snap in case the slide ended off the mesh.
                    SnapToNavMesh();
                }
                _isKnockedBack = false;
            }
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
