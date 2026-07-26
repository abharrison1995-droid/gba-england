using UnityEngine;
using TMPro;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Red popup numbers over combatants (EK hit feedback).
    /// </summary>
    public class FloatingDamageText : MonoBehaviour
    {
        public float Lifetime = 0.9f;
        public float RiseSpeed = 1.4f;
        public float FadeStart = 0.4f;

        private TextMeshPro _tmp;
        private float _age;
        private Color _color;

        public static void Spawn(Vector3 worldPos, int amount, Color? color = null)
        {
            GameObject go = new GameObject("FloatingDamage");
            go.transform.position = worldPos + Vector3.up * 1.6f;

            TextMeshPro tmp = go.AddComponent<TextMeshPro>();
            tmp.text = amount.ToString();
            tmp.fontSize = 4f;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.color = color ?? EKVibe.DamageFloat;
            tmp.sortingOrder = 100;

            FloatingDamageText fdt = go.AddComponent<FloatingDamageText>();
            fdt._tmp = tmp;
            fdt._color = tmp.color;
        }

        private void LateUpdate()
        {
            _age += Time.deltaTime;
            transform.position += Vector3.up * RiseSpeed * Time.deltaTime;

            // Billboard toward main camera
            if (UnityEngine.Camera.main != null)
            {
                transform.rotation = UnityEngine.Camera.main.transform.rotation;
            }

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
