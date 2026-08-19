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

        private Rigidbody _rb;
        private Vector3 _fleeDirection;
        private float _fleeUntil;
        private bool _canDespawn;

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

            // Face travel direction
            transform.rotation = Quaternion.LookRotation(_fleeDirection, Vector3.up);

            Vector3 step = _fleeDirection * (FleeSpeed * Time.fixedDeltaTime);
            if (_rb != null)
                _rb.MovePosition(transform.position + step);
            else
                transform.position += step;
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
