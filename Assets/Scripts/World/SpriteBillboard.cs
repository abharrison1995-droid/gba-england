using UnityEngine;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Keeps a upright quad facing the camera yaw (EK-style 2.5D sprites).
    /// </summary>
    public class SpriteBillboard : MonoBehaviour
    {
        public bool LockPitch = true;

        private Transform _cam;

        private void LateUpdate()
        {
            if (_cam == null)
            {
                var main = UnityEngine.Camera.main;
                if (main == null) return;
                _cam = main.transform;
            }

            if (LockPitch)
            {
                Vector3 euler = _cam.rotation.eulerAngles;
                transform.rotation = Quaternion.Euler(0f, euler.y, 0f);
            }
            else
            {
                transform.rotation = _cam.rotation;
            }
        }
    }
}
