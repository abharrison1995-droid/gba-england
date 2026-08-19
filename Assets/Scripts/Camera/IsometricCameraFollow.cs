using UnityEngine;
using GBHEngland.Vibe;

namespace GBHEngland.World
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
        private UnityEngine.Camera _cam;
        private float _currentOrthoVelocity;
        private Vector3 _lastTargetPos;
        private Vector3 _targetVelocity;
        private Coroutine _shakeCoroutine;
        private Rigidbody _targetRb;

        private void Awake()
        {
            ApplyVibeLock();
            RebuildOffset();
            if (Target != null)
            {
                _lastTargetPos = Target.position;
                _targetRb = Target.GetComponent<Rigidbody>();
            }
        }

        private void OnDestroy()
        {
            if (_shakeCoroutine != null)
            {
                StopCoroutine(_shakeCoroutine);
                _shakeCoroutine = null;
            }
        }

        private void LateUpdate()
        {
            if (Target == null) return;

            // Cache/update Rigidbody reference if target was swapped without SetTarget
            if (_targetRb == null || _targetRb.transform != Target)
                _targetRb = Target.GetComponent<Rigidbody>();

            // Speed calculation for dynamic zoom and forward lookahead
            float dt = Mathf.Max(0.0001f, Time.deltaTime);
            Vector3 rawVelocity = _targetRb != null ? _targetRb.velocity : ((Target.position - _lastTargetPos) / dt);
            _lastTargetPos = Target.position;
            _targetVelocity = Vector3.Lerp(_targetVelocity, rawVelocity, 1f - Mathf.Exp(-8f * dt));
            float speed = _targetVelocity.magnitude;

            // Dynamic OrthoSize (smoothly expands when driving fast)
            float targetOrtho = OrthoSize;
            if (MountController.IsPlayerRiding && speed > 3.5f)
            {
                float speedFactor = Mathf.Clamp01((speed - 3.5f) / 12f);
                targetOrtho = Mathf.Lerp(OrthoSize, OrthoSize * 1.38f, speedFactor);
            }

            if (_cam != null && Mathf.Abs(_cam.orthographicSize - targetOrtho) > 0.01f)
            {
                _cam.orthographicSize = Mathf.SmoothDamp(_cam.orthographicSize, targetOrtho, ref _currentOrthoVelocity, 0.25f);
            }

            // Lookahead offset along horizontal velocity vector
            Vector3 lookahead = Vector3.ClampMagnitude(new Vector3(_targetVelocity.x, 0f, _targetVelocity.z) * 0.18f, 2.5f);

            Vector3 desired = Target.position + _offset + lookahead;
            transform.position = Vector3.SmoothDamp(transform.position, desired, ref _velocity, SmoothTime);
        }

        public void ApplyVibeLock()
        {
            _cam = GetComponent<UnityEngine.Camera>();
            if (_cam != null)
            {
                _cam.orthographic = true;
                _cam.orthographicSize = OrthoSize;
            }

            transform.rotation = Quaternion.Euler(EKVibe.CameraPitch, EKVibe.CameraYaw, 0f);
            RebuildOffset();
        }

        private void RebuildOffset()
        {
            Vector3 dir = transform.rotation * Vector3.back;
            _offset = dir * EKVibe.CameraDistance;
        }

        public void Shake(float duration, float magnitude)
        {
            if (!gameObject.activeInHierarchy) return;
            if (_shakeCoroutine != null)
            {
                StopCoroutine(_shakeCoroutine);
                RebuildOffset();
                _shakeCoroutine = null;
            }
            _shakeCoroutine = StartCoroutine(ShakeRoutine(duration, magnitude));
        }

        private System.Collections.IEnumerator ShakeRoutine(float duration, float magnitude)
        {
            RebuildOffset();
            Vector3 baseOffset = _offset;
            float elapsed = 0f;
            while (elapsed < duration)
            {
                elapsed += Time.deltaTime;
                float percent = 1f - Mathf.Clamp01(elapsed / duration);
                Vector3 randomOffset = Random.insideUnitSphere * (magnitude * percent);
                _offset = baseOffset + randomOffset;
                yield return null;
            }
            RebuildOffset();
            _shakeCoroutine = null;
        }

        public void SetTarget(Transform target)
        {
            Target = target;
            if (Target != null)
            {
                _lastTargetPos = Target.position;
                _targetRb = Target.GetComponent<Rigidbody>();
                _targetVelocity = Vector3.zero;
                transform.position = Target.position + _offset;
            }
            else
            {
                _targetRb = null;
            }
        }

        /// <summary>Instantly moves the camera to its follow position, skipping the smooth glide — use right after teleporting the target (e.g. a chunk transition).</summary>
        public void SnapToTarget()
        {
            if (Target == null) return;
            _lastTargetPos = Target.position;
            _targetVelocity = Vector3.zero;
            transform.position = Target.position + _offset;
            _velocity = Vector3.zero;
        }
    }
}
