using UnityEngine;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Fixed isometric follow — pitch/yaw locked to EK vibe, no player zoom/tilt.
    /// </summary>
    public class IsometricCameraFollow : MonoBehaviour
    {
        public Transform Target;
        public float SmoothTime = 0.12f;
        public float OrthoSize = EKVibe.CameraOrthoSize;

        private Vector3 _velocity;
        private Vector3 _offset;

        private void Awake()
        {
            ApplyVibeLock();
            RebuildOffset();
        }

        private void LateUpdate()
        {
            if (Target == null) return;

            Vector3 desired = Target.position + _offset;
            transform.position = Vector3.SmoothDamp(transform.position, desired, ref _velocity, SmoothTime);
        }

        public void ApplyVibeLock()
        {
            var cam = GetComponent<UnityEngine.Camera>();
            if (cam != null)
            {
                cam.orthographic = true;
                cam.orthographicSize = OrthoSize;
            }

            transform.rotation = Quaternion.Euler(EKVibe.CameraPitch, EKVibe.CameraYaw, 0f);
            RebuildOffset();
        }

        private void RebuildOffset()
        {
            Vector3 dir = transform.rotation * Vector3.back;
            _offset = dir * EKVibe.CameraDistance;
        }

        public void SetTarget(Transform target)
        {
            Target = target;
            if (Target != null)
            {
                transform.position = Target.position + _offset;
            }
        }

        /// <summary>Instantly moves the camera to its follow position, skipping the smooth glide — use right after teleporting the target (e.g. a chunk transition).</summary>
        public void SnapToTarget()
        {
            if (Target == null) return;
            transform.position = Target.position + _offset;
            _velocity = Vector3.zero;
        }
    }
}
