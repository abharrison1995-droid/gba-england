using UnityEngine;

namespace GBHEngland.AI
{
    /// <summary>
    /// Moves an NPC directly away from a target (the player / the stolen car) at run speed,
    /// then self-destructs once off-camera. Used for the fleeing driver on a successful car theft.
    /// </summary>
    public class NPCFlee : MonoBehaviour
    {
        [Tooltip("How fast the NPC runs away, in m/s.")]
        public float FleeSpeed = 5f;

        [Tooltip("How long the NPC runs before checking visibility for despawn.")]
        public float MinFleeSeconds = 3f;

        /// <summary>Same probe shape as NPCWander's Blocked() — chest-height SphereCast, triggers ignored.</summary>
        private const float ProbeRadius = 0.35f;
        private const float ProbeAhead  = 0.6f;
        private const float ProbeHeight = 0.6f;

        private Rigidbody _rb;
        private Vector3 _fleeDirection;
        private float _fleeUntil;
        private bool _canDespawn;
        private RaycastHit _probeHit;   // reused by Blocked()/Redirect() — no per-call allocation

        private void Awake()
        {
            _rb = GetComponent<Rigidbody>();
        }

        /// <summary>
        /// Call once after AddComponent. The NPC will run directly away from
        /// <paramref name="fleeFrom"/> until it is off-camera, then self-destruct.
        /// </summary>
        public void Begin(Vector3 fleeFrom)
        {
            Vector3 away = transform.position - fleeFrom;
            away.y = 0f;
            _fleeDirection = away.sqrMagnitude > 0.01f ? away.normalized : Vector3.forward;
            _fleeUntil = Time.time + MinFleeSeconds;
        }

        private void FixedUpdate()
        {
            if (_fleeDirection.sqrMagnitude < 0.0001f) return;

            // The flee direction is fixed at Begin() and never re-aimed at anything — a wall in
            // the way must deflect it, or the NPC runs on the spot against the wall for the whole
            // MinFleeSeconds window while it is still on camera.
            if (Blocked(_fleeDirection))
                Redirect();

            // Face travel direction
            transform.rotation = Quaternion.LookRotation(_fleeDirection, Vector3.up);

            Vector3 step = _fleeDirection * (FleeSpeed * Time.fixedDeltaTime);
            if (_rb != null)
                _rb.MovePosition(transform.position + step);
            else
                transform.position += step;
        }

        /// <summary>
        /// Something solid within a short step ahead. Mirrors NPCWander.Blocked(): a chest-height
        /// SphereCast, triggers ignored so chunk edges and interact volumes never redirect a flee.
        /// </summary>
        private bool Blocked(Vector3 direction)
        {
            var probe = new Ray(transform.position + Vector3.up * ProbeHeight, direction);
            if (Physics.SphereCast(probe, ProbeRadius, out _probeHit, ProbeAhead, ~0, QueryTriggerInteraction.Ignore))
            {
                if (_probeHit.collider != null
                    && (_probeHit.collider.transform == transform || _probeHit.collider.transform.IsChildOf(transform)))
                    return false;
                return true;
            }
            return false;
        }

        /// <summary>
        /// Deflects along the wall instead of stopping — a fleeing NPC has nowhere to dwell and
        /// think better of it the way NPCWander does, so it slides past the obstacle instead.
        /// Falls back to reversing course if the wall is hit near head-on, where the slide
        /// component collapses to near zero.
        /// </summary>
        private void Redirect()
        {
            Vector3 slide = Vector3.ProjectOnPlane(_fleeDirection, _probeHit.normal);
            _fleeDirection = slide.sqrMagnitude > 0.01f ? slide.normalized : -_fleeDirection;
        }

        private void Update()
        {
            // After minimum flee time, despawn once off-camera
            if (Time.time >= _fleeUntil)
                _canDespawn = true;

            if (_canDespawn && !IsVisibleToMainCamera())
                Destroy(gameObject);
        }

        private bool IsVisibleToMainCamera()
        {
            Camera cam = Camera.main;
            if (cam == null) return false;

            Vector3 vp = cam.WorldToViewportPoint(transform.position);
            return vp.x > -0.1f && vp.x < 1.1f && vp.z > 0f
                && vp.y > -0.1f && vp.y < 1.1f;
        }
    }
}
