using UnityEngine;

namespace ExiledAlvaston.Combat
{
    /// <summary>
    /// Samples an imported sprite AnimationClip without needing a dedicated AnimatorController.
    /// ArtImportTool binds FX clips to a SpriteRenderer at the empty path, exactly the shape this
    /// runtime object creates.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class SpellFxPlayer : MonoBehaviour
    {
        private AnimationClip _clip;
        private SpriteRenderer _renderer;
        private Transform _follow;
        private Vector3 _followOffset;
        private float _startedAt;
        private float _lifetime;
        private bool _loop;
        private float _screenAngle;

        public static SpellFxPlayer Spawn(AnimationClip clip, Vector3 position, bool loop = false,
            float lifetime = 0f, Transform follow = null,
            Vector3 followOffset = default(Vector3))
        {
            if (clip == null) return null;

            var go = new GameObject($"SpellFX_{clip.name}");
            go.transform.position = position;
            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sortingOrder = 80;
            var player = go.AddComponent<SpellFxPlayer>();
            player._clip = clip;
            player._renderer = renderer;
            player._follow = follow;
            player._followOffset = followOffset;
            player._loop = loop;
            player._startedAt = Time.time;
            player._lifetime = lifetime > 0f ? lifetime : Mathf.Max(0.02f, clip.length);
            clip.SampleAnimation(go, 0f);
            return player;
        }

        /// <summary>Stretch and rotate a horizontal effect between two world points.</summary>
        public void Span(Vector3 from, Vector3 to)
        {
            transform.position = (from + to) * 0.5f;
            float width = _renderer != null && _renderer.sprite != null
                ? Mathf.Max(0.01f, _renderer.sprite.bounds.size.x)
                : 1f;
            transform.localScale = new Vector3(Vector3.Distance(from, to) / width, 1f, 1f);

            Camera cam = Camera.main;
            if (cam == null) return;
            Vector3 a = cam.WorldToScreenPoint(from);
            Vector3 b = cam.WorldToScreenPoint(to);
            Vector2 delta = new Vector2(b.x - a.x, b.y - a.y);
            if (delta.sqrMagnitude > 0.01f)
                _screenAngle = Mathf.Atan2(delta.y, delta.x) * Mathf.Rad2Deg;
        }

        private void Update()
        {
            if (_clip == null)
            {
                Destroy(gameObject);
                return;
            }

            float elapsed = Time.time - _startedAt;
            float sample = _loop && _clip.length > 0f
                ? Mathf.Repeat(elapsed, _clip.length)
                : Mathf.Min(elapsed, _clip.length);
            _clip.SampleAnimation(gameObject, sample);

            if (elapsed >= _lifetime)
                Destroy(gameObject);
        }

        private void LateUpdate()
        {
            if (_follow != null)
                transform.position = _follow.position + _followOffset;

            Camera cam = Camera.main;
            if (cam == null) return;
            float yaw = cam.transform.rotation.eulerAngles.y;
            transform.rotation = Quaternion.Euler(0f, yaw, _screenAngle);
        }
    }
}
