using UnityEngine;
using TMPro;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// The player's chosen spell name, shouted over their head with a "!" when they cast —
    /// e.g. "Spark Out!". Rises and fades like the damage numbers, billboarded to the camera.
    /// </summary>
    public class SpellShoutText : MonoBehaviour
    {
        public float Lifetime = 1.1f;
        public float RiseSpeed = 1.1f;
        public float FadeStart = 0.5f;

        private TextMeshPro _tmp;
        private float _age;
        private Color _color;

        public static void Spawn(Vector3 worldPos, string spellName)
        {
            if (string.IsNullOrWhiteSpace(spellName)) spellName = "Spark Out";

            GameObject go = new GameObject("SpellShout");
            go.transform.position = worldPos + Vector3.up * 2.1f;

            var tmp = go.AddComponent<TextMeshPro>();
            tmp.text = spellName.Trim() + "!";
            tmp.fontSize = 4.5f;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.color = new Color(0.55f, 0.85f, 1f, 1f); // electric blue
            tmp.sortingOrder = 120;

            var shout = go.AddComponent<SpellShoutText>();
            shout._tmp = tmp;
            shout._color = tmp.color;
        }

        private void LateUpdate()
        {
            _age += Time.deltaTime;
            transform.position += Vector3.up * RiseSpeed * Time.deltaTime;

            if (UnityEngine.Camera.main != null)
                transform.rotation = UnityEngine.Camera.main.transform.rotation;

            if (_tmp != null && _age > FadeStart)
            {
                float t = Mathf.InverseLerp(FadeStart, Lifetime, _age);
                Color c = _color;
                c.a = 1f - t;
                _tmp.color = c;
            }

            if (_age >= Lifetime)
                Destroy(gameObject);
        }
    }
}
