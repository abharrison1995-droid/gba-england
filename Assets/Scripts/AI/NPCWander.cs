using UnityEngine;
using GBHEngland.Systems;
using GBHEngland.Dialogue;
using GBHEngland.World;

namespace GBHEngland.AI
{
    /// <summary>
    /// Ambient wandering: stroll somewhere near where you were placed, stand about for a bit, do it
    /// again. Enough to stop a populated street looking like a waxwork museum, and no more.
    ///
    /// <b>Deliberately not a NavMeshAgent.</b> `EKNavMeshBaker` bakes one mesh from whichever chunk
    /// happens to be loaded in `c.unity` at the time, and all six chunks are instantiated at the
    /// same origin, so that bake is correct for exactly one of them and wrong for the other five.
    /// `RuntimeNavMeshBaker` exists to fix that but sits on no chunk prefab, and putting it on all
    /// six would buy a runtime bake on every chunk crossing — on a mobile-first game — to make
    /// pedestrians walk round corners slightly better. A short probe ahead is the honest trade.
    ///
    /// Owns its own speed. The player's `MovementSpeed` has one owner and a modifier stack, and
    /// nothing here goes anywhere near it.
    /// </summary>
    public class NPCWander : MonoBehaviour
    {
        [Tooltip("How far from the spot it was placed this NPC will stray.")]
        public float WanderRadius = 6f;

        [Tooltip("Units per second. Slower than the player on purpose — an NPC that keeps pace " +
                 "reads as following you.")]
        public float MoveSpeed = 1.2f;

        [Tooltip("Seconds spent standing still between strolls, picked at random from this range.")]
        public float PauseMin = 2f;
        public float PauseMax = 6f;

        /// <summary>Matches the transition thresholds the art importer builds into every controller.</summary>
        private static readonly int SpeedHash = Animator.StringToHash("Speed");

        private const float ArriveDistance = 0.25f;
        private const float ProbeRadius    = 0.35f;
        private const float ProbeAhead     = 0.6f;
        private const float ProbeHeight    = 0.6f;

        private Vector3 _home;
        private Vector3 _target;
        private bool _moving;
        private float _dwellUntil;

        private WorldActorVisual _visual;
        private Animator _animator;
        private bool _hasSpeedParam;

        private void Start()
        {
            // Where it was placed, not where it currently is — so a wanderer always drifts back
            // towards its post rather than random-walking across the chunk over a long session.
            _home = transform.position;
            _visual = GetComponent<WorldActorVisual>();

            CacheAnimator();
            Dwell();
        }

        /// <summary>
        /// The Animator sits on ActorVisual/SwingRoot, beside the SpriteRenderer, because that is
        /// where the generated clips bind. Searching children is safe here in a way it is not for
        /// the player: an NPC has no layered vehicle sprite to pick up by mistake (CLAUDE.md §11).
        /// </summary>
        private void CacheAnimator()
        {
            _animator = GetComponentInChildren<Animator>(true);
            if (_animator == null) return;   // no art yet — it will slide, visibly, which is the point

            foreach (AnimatorControllerParameter p in _animator.parameters)
            {
                if (p.nameHash != SpeedHash || p.type != AnimatorControllerParameterType.Float) continue;
                _hasSpeedParam = true;
                return;
            }

            Debug.LogWarning(
                $"NPCWander on '{name}': the Animator has no Speed float, so this NPC will glide " +
                "in whatever pose it is holding. Controllers built by the art importer define it; " +
                "an older hand-made one may not.", this);
        }

        private void Update()
        {
            if (PauseManager.IsPaused) return;

            // Everyone stops while anyone is talking. Coarser than freezing only the NPC being
            // spoken to, but nothing exposes who that is, and a street carrying on behind a
            // conversation is not worth the plumbing to find out.
            if (DialogueManager.IsDialogueOpen)
            {
                SetAnimatorSpeed(0f);
                return;
            }

            if (!_moving)
            {
                if (Time.time < _dwellUntil) return;
                PickTarget();
            }

            Step();
        }

        private void Step()
        {
            Vector3 delta = _target - transform.position;
            delta.y = 0f;

            if (delta.sqrMagnitude <= ArriveDistance * ArriveDistance)
            {
                Dwell();
                return;
            }

            Vector3 direction = delta.normalized;

            // Walking into something ends the stroll rather than sliding along it. An NPC that
            // grinds against a wall for four seconds looks far worse than one that stops and
            // thinks better of it.
            if (Blocked(direction))
            {
                Dwell();
                return;
            }

            transform.position += direction * (MoveSpeed * Time.deltaTime);

            // Without this the sprite keeps whatever flip it was left with, so half of every
            // wander is walked backwards.
            if (_visual != null) _visual.SetFacing(direction);

            SetAnimatorSpeed(MoveSpeed);
        }

        /// <summary>
        /// Something solid within a short step ahead. Cast from chest height because a probe along
        /// the floor catches the ground itself on any slope, and triggers are ignored because the
        /// world is full of them — chunk edges, interact ranges, pickup volumes — and none of them
        /// are walls.
        /// </summary>
        private bool Blocked(Vector3 direction)
        {
            var probe = new Ray(transform.position + Vector3.up * ProbeHeight, direction);
            if (Physics.SphereCast(probe, ProbeRadius, out RaycastHit hit, ProbeAhead, ~0, QueryTriggerInteraction.Ignore))
            {
                if (hit.collider != null && (hit.collider.transform == transform || hit.collider.transform.IsChildOf(transform)))
                    return false;
                return true;
            }
            return false;
        }

        private void PickTarget()
        {
            Vector2 offset = Random.insideUnitCircle * WanderRadius;

            // Movement is on the X/Z plane; Y is up, and is left exactly where the NPC already
            // stands rather than being taken from _home, which would sink anyone placed on a slope.
            _target = new Vector3(_home.x + offset.x, transform.position.y, _home.z + offset.y);
            _moving = true;
        }

        private void Dwell()
        {
            _moving = false;
            _dwellUntil = Time.time + Random.Range(PauseMin, PauseMax);
            SetAnimatorSpeed(0f);
        }

        private void SetAnimatorSpeed(float speed)
        {
            if (!_hasSpeedParam) return;
            _animator.SetFloat(SpeedHash, speed);
        }
    }
}
