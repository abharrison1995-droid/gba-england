using UnityEngine;
using TMPro;
using GBHEngland.Combat;
using GBHEngland.Vibe;

namespace GBHEngland.World
{
    /// <summary>
    /// EK enemy chrome: red name, level badge, green HP bar — shown only while the enemy is in
    /// combat with the player or standing close enough to be one.
    /// </summary>
    [RequireComponent(typeof(Health))]
    public class EnemyNameplate : MonoBehaviour
    {
        [Tooltip("Display-only fallback, used when the actor has no EnemyLevel component. This is " +
                 "not a real level and nothing scales off it — see EnemyLevel.")]
        public int Level = 3;
        public float HeightOffset = 1.7f;

        [Tooltip("Seconds the plate stays visible after the last time this enemy was engaged. " +
                 "Same field name and meaning as PlayerHealthBar's, so the two read alike.")]
        public float VisibleDuration = 4f;

        private Health _health;
        private Transform _root;
        private Transform _hpFill;
        private TMPro.TextMeshPro _nameText;
        private string _shownName;

        /// <summary>
        /// The plate is built on first show, not in Awake. It saves five GameObjects, two
        /// TextMeshPros and three material lookups for every enemy that never fights — and it
        /// fixes a real bug: <c>AddComponent&lt;EnemyNameplate&gt;()</c> runs Awake synchronously,
        /// so TutorialSequence's <c>plate.Level = 1</c> on the following line used to land after
        /// the badge had already been rendered with the field default of 3. Building later means
        /// the assignment always precedes the render.
        /// </summary>
        private bool _built;

        private float _hideAt;

        private void Awake()
        {
            _health = GetComponent<Health>();

            if (_health != null)
            {
                // Covers a hit from something with no aggro — a spell from out of sight. Paired
                // with the removals in OnDestroy, as EnemyAI does for the same two events.
                _health.OnTakeDamage.AddListener(OnDamaged);
                _health.OnDeath.AddListener(OnDied);
            }
        }

        /// <summary>
        /// Pushed from <see cref="EnemyAI.PerceptionRoutine"/> five times a second: true while this
        /// enemy has the player aggroed or within its sight radius.
        ///
        /// False deliberately does nothing — the plate's own timer runs out on its own, so a plate
        /// fades out after a fight rather than snapping off the instant an enemy loses interest.
        ///
        /// "Deals damage" needs no trigger of its own: an EnemyAI cannot swing without a target, so
        /// aggro strictly precedes it.
        /// </summary>
        public void SetEngaged(bool engaged)
        {
            if (!engaged) return;
            Show();
        }

        private void OnDamaged(int amount)
        {
            Show();
        }

        /// <summary>
        /// Hides at once rather than on the timer, so a corpse waiting out Health.DestroyDelay does
        /// not keep a plate floating over it.
        /// </summary>
        private void OnDied()
        {
            if (_root != null) _root.gameObject.SetActive(false);
        }

        private void Show()
        {
            // ⚠ The dead enemy's own PerceptionRoutine keeps ticking for the whole destroy delay
            // and would push SetEngaged(true) five more times, putting the plate straight back over
            // the corpse OnDied just cleared.
            if (_health != null && _health.IsDead) return;

            if (!_built)
            {
                Build();
                _built = true;
            }

            _hideAt = Time.time + VisibleDuration;
            if (_root != null && !_root.gameObject.activeSelf)
                _root.gameObject.SetActive(true);
        }

        private void Update()
        {
            if (_root != null && _root.gameObject.activeSelf && Time.time >= _hideAt)
                _root.gameObject.SetActive(false);
        }

        private void LateUpdate()
        {
            // ⚠ Must stay the first statement. Hidden, this component costs one bool a frame —
            // cheaper than it was before the gate, when an idle enemy paid a Camera.main lookup, a
            // position write, a rotation write, a string compare and a health division every frame.
            if (_root == null || !_root.gameObject.activeSelf) return;

            _root.position = transform.position + Vector3.up * HeightOffset;

            // Spawners often set DisplayName after Instantiate — keep the plate in sync
            if (_nameText != null && _health != null && _health.DisplayName != _shownName)
            {
                _shownName = _health.DisplayName;
                _nameText.text = _shownName;
            }

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
            GameObject root = new GameObject("Nameplate");
            _root = root.transform;

            _shownName = _health != null ? _health.DisplayName : "Enemy";
            _nameText = CreateTmp("Name", root.transform, _shownName,
                new Vector3(0.1f, 0.22f, 0f), 2.2f, EKVibe.EnemyName);

            GameObject levelGo = GameObject.CreatePrimitive(PrimitiveType.Quad);
            levelGo.name = "LevelBadge";
            var levelCol = levelGo.GetComponent<Collider>();
            if (levelCol != null) Destroy(levelCol);
            levelGo.transform.SetParent(root.transform, false);
            levelGo.transform.localPosition = new Vector3(-0.55f, 0.22f, 0f);
            levelGo.transform.localScale = new Vector3(0.28f, 0.28f, 1f);
            SetUnlit(levelGo, EKVibe.LevelBadge);

            // The real level when the actor has one; this component's own field only as a display
            // fallback. Built once and never refreshed in LateUpdate, which is fine: an enemy's
            // level does not change at runtime.
            var enemyLevel = GetComponent<EnemyLevel>();
            int shownLevel = enemyLevel != null ? Mathf.Max(1, enemyLevel.Level) : Level;

            CreateTmp("Level", levelGo.transform, shownLevel.ToString(), Vector3.zero, 1.6f, EKVibe.TextDark);

            GameObject track = GameObject.CreatePrimitive(PrimitiveType.Quad);
            track.name = "HPTrack";
            var trackCol = track.GetComponent<Collider>();
            if (trackCol != null) Destroy(trackCol);
            track.transform.SetParent(root.transform, false);
            track.transform.localPosition = Vector3.zero;
            track.transform.localScale = new Vector3(0.7f, 0.08f, 1f);
            SetUnlit(track, new Color(0.1f, 0.1f, 0.1f, 0.85f));

            GameObject fill = GameObject.CreatePrimitive(PrimitiveType.Quad);
            fill.name = "HPFill";
            var fillCol = fill.GetComponent<Collider>();
            if (fillCol != null) Destroy(fillCol);
            fill.transform.SetParent(track.transform, false);
            fill.transform.localPosition = Vector3.zero;
            fill.transform.localScale = Vector3.one;
            SetUnlit(fill, new Color(0.25f, 0.75f, 0.2f, 1f));
            _hpFill = fill.transform;
        }

        private void OnDestroy()
        {
            if (_health != null)
            {
                _health.OnTakeDamage.RemoveListener(OnDamaged);
                _health.OnDeath.RemoveListener(OnDied);
            }

            // _root is a scene-root GameObject, never parented to this actor, so it does not die
            // with us unless it is destroyed here.
            if (_root != null)
                Destroy(_root.gameObject);
        }

        // Nameplate colors come from a tiny fixed set — share one material per color
        // across all enemies instead of leaking three new materials per spawn.
        private static readonly System.Collections.Generic.Dictionary<Color, Material> _sharedMats =
            new System.Collections.Generic.Dictionary<Color, Material>();

        private static void SetUnlit(GameObject go, Color color)
        {
            var r = go.GetComponent<Renderer>();
            if (!_sharedMats.TryGetValue(color, out Material mat) || mat == null)
            {
                Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Standard");
                mat = new Material(sh) { color = color };
                _sharedMats[color] = mat;
            }
            r.sharedMaterial = mat;
        }

        private static TextMeshPro CreateTmp(string name, Transform parent, string text, Vector3 localPos, float size, Color color)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            TextMeshPro tmp = go.AddComponent<TextMeshPro>();
            tmp.text = text;
            tmp.fontSize = size;
            tmp.color = color;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.rectTransform.sizeDelta = new Vector2(2f, 0.5f);
            return tmp;
        }
    }
}
