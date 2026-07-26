using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Floating HP bar over the player's head — appears on taking damage, fades out a few
    /// seconds after the last hit. Same billboard-quad approach as EnemyNameplate.
    /// </summary>
    [RequireComponent(typeof(Health))]
    public class PlayerHealthBar : MonoBehaviour
    {
        public float HeightOffset = 1.7f;
        [Tooltip("Seconds the bar stays visible after the most recent hit before hiding again.")]
        public float VisibleDuration = 4f;

        private Health _health;
        private Transform _root;
        private Transform _hpFill;
        private float _hideAt;

        private void Awake()
        {
            _health = GetComponent<Health>();
            Build();
            _root.gameObject.SetActive(false);

            _health.OnTakeDamage.AddListener(OnDamaged);
            _health.OnDeath.AddListener(OnDied);
        }

        private void OnDestroy()
        {
            if (_health != null)
            {
                _health.OnTakeDamage.RemoveListener(OnDamaged);
                _health.OnDeath.RemoveListener(OnDied);
            }
            if (_root != null)
                Destroy(_root.gameObject);
        }

        private void OnDamaged(int amount)
        {
            _hideAt = Time.time + VisibleDuration;
            if (_root != null) _root.gameObject.SetActive(true);
        }

        private void OnDied()
        {
            if (_root != null) _root.gameObject.SetActive(false);
        }

        private void Update()
        {
            if (_root != null && _root.gameObject.activeSelf && Time.time >= _hideAt)
                _root.gameObject.SetActive(false);
        }

        private void LateUpdate()
        {
            if (_root == null || !_root.gameObject.activeSelf) return;

            _root.position = transform.position + Vector3.up * HeightOffset;

            var cam = UnityEngine.Camera.main;
            if (cam != null)
                _root.rotation = cam.transform.rotation;

            if (_hpFill != null && _health != null && _health.MaxHealth > 0)
            {
                float t = Mathf.Clamp01((float)_health.CurrentHealth / _health.MaxHealth);
                _hpFill.localScale = new Vector3(t, 1f, 1f);
                _hpFill.localPosition = new Vector3((-1f + t) * 0.5f, 0f, -0.01f);
            }
        }

        private void Build()
        {
            GameObject root = new GameObject("PlayerHealthBar");
            _root = root.transform;

            GameObject track = GameObject.CreatePrimitive(PrimitiveType.Quad);
            track.name = "HPTrack";
            Object.Destroy(track.GetComponent<Collider>());
            track.transform.SetParent(root.transform, false);
            track.transform.localPosition = Vector3.zero;
            track.transform.localScale = new Vector3(0.8f, 0.1f, 1f);
            SetUnlit(track, new Color(0.1f, 0.1f, 0.1f, 0.85f));

            GameObject fill = GameObject.CreatePrimitive(PrimitiveType.Quad);
            fill.name = "HPFill";
            Object.Destroy(fill.GetComponent<Collider>());
            fill.transform.SetParent(track.transform, false);
            fill.transform.localPosition = Vector3.zero;
            fill.transform.localScale = Vector3.one;
            SetUnlit(fill, EKVibe.HealthBar);
            _hpFill = fill.transform;
        }

        private static Material _sharedTrackMat;
        private static Material _sharedFillMat;

        private static void SetUnlit(GameObject go, Color color)
        {
            var r = go.GetComponent<Renderer>();
            Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Standard");

            // Only two colors ever used here (track/fill) — share materials instead of leaking one per player.
            if (color == EKVibe.HealthBar)
            {
                if (_sharedFillMat == null) _sharedFillMat = new Material(sh) { color = color };
                r.sharedMaterial = _sharedFillMat;
            }
            else
            {
                if (_sharedTrackMat == null) _sharedTrackMat = new Material(sh) { color = color };
                r.sharedMaterial = _sharedTrackMat;
            }
        }
    }
}
