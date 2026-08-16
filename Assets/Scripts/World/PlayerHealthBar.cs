using UnityEngine;
using TMPro;
using GBHEngland.Combat;
using GBHEngland.Vibe;

namespace GBHEngland.World
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
        private TextMeshPro _levelText;
        private float _hideAt;

        /// <summary>
        /// The level currently painted into the badge; -1 until the first paint.
        ///
        /// ⚠ Unlike an enemy's, the player's level changes at runtime, so the badge cannot be
        /// written once in Build. It is polled rather than subscribed for the same reason
        /// UIManager polls: PlayerSession is a DontDestroyOnLoad singleton that need not exist when
        /// this Awake runs, and a missed unsubscribe would keep a destroyed bar receiving events
        /// across a reload. The int compare is the point — ToString() allocates, and writing it
        /// every frame would put a per-frame allocation on a mobile hot path.
        /// </summary>
        private int _shownLevel = -1;

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
            Ping();
        }

        /// <summary>
        /// Raise the bar and restart its timer. Called on taking damage, and by CombatController
        /// when the player deals damage or an enemy takes aggro on them.
        /// </summary>
        public void Ping()
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

            // Behind the activeSelf return on purpose: costs nothing at all while the bar is down.
            var session = Flow.PlayerSession.Instance;
            if (session != null && session.Level != _shownLevel)
            {
                _shownLevel = session.Level;
                if (_levelText != null) _levelText.text = _shownLevel.ToString();
            }

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

            // Left of the track, never over the fill. Modelled on EnemyNameplate's badge and
            // deliberately sized to match it, so the player's level reads like an enemy's.
            // CreateTmp there is private to another class; six copied lines beat making it public
            // for two billboards with slightly different needs — this file already duplicates
            // SetUnlit for the same reason.
            GameObject badge = GameObject.CreatePrimitive(PrimitiveType.Quad);
            badge.name = "LevelBadge";
            Object.Destroy(badge.GetComponent<Collider>());
            badge.transform.SetParent(root.transform, false);
            badge.transform.localPosition = new Vector3(-0.56f, 0f, 0f);
            badge.transform.localScale = new Vector3(0.28f, 0.28f, 1f);
            SetUnlit(badge, EKVibe.LevelBadge);

            var textGo = new GameObject("LevelText");
            textGo.transform.SetParent(badge.transform, false);
            textGo.transform.localPosition = Vector3.zero;
            _levelText = textGo.AddComponent<TextMeshPro>();
            _levelText.text = "";
            _levelText.fontSize = 1.6f;
            _levelText.color = EKVibe.TextDark;
            _levelText.alignment = TextAlignmentOptions.Center;
            _levelText.rectTransform.sizeDelta = new Vector2(2f, 0.5f);
        }

        private static Material _sharedTrackMat;
        private static Material _sharedFillMat;
        private static Material _sharedBadgeMat;

        private static void SetUnlit(GameObject go, Color color)
        {
            var r = go.GetComponent<Renderer>();
            Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Standard");

            // Three colors ever used here (track/fill/badge) — share materials instead of leaking
            // one per player. ⚠ Each has its own branch keyed by colour: with a single fallback
            // branch the badge would take whichever colour reached it first and come out the
            // track's near-black, with nothing to say why.
            if (color == EKVibe.HealthBar)
            {
                if (_sharedFillMat == null) _sharedFillMat = new Material(sh) { color = color };
                r.sharedMaterial = _sharedFillMat;
            }
            else if (color == EKVibe.LevelBadge)
            {
                if (_sharedBadgeMat == null) _sharedBadgeMat = new Material(sh) { color = color };
                r.sharedMaterial = _sharedBadgeMat;
            }
            else
            {
                if (_sharedTrackMat == null) _sharedTrackMat = new Material(sh) { color = color };
                r.sharedMaterial = _sharedTrackMat;
            }
        }
    }
}
