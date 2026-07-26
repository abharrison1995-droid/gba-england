using UnityEngine;
using TMPro;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// EK enemy chrome: red name, level badge, green HP bar.
    /// </summary>
    [RequireComponent(typeof(Health))]
    public class EnemyNameplate : MonoBehaviour
    {
        public int Level = 3;
        public float HeightOffset = 1.7f;

        private Health _health;
        private Transform _root;
        private Transform _hpFill;
        private TMPro.TextMeshPro _nameText;
        private string _shownName;

        private void Awake()
        {
            _health = GetComponent<Health>();
            Build();
        }

        private void LateUpdate()
        {
            if (_root == null) return;

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

            CreateTmp("Level", levelGo.transform, Level.ToString(), Vector3.zero, 1.6f, EKVibe.TextDark);

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
