using UnityEngine;

namespace ExiledAlvaston.Combat
{
    /// <summary>
    /// Cheap procedural lightning VFX — a jagged electric-blue LineRenderer from caster to target
    /// plus a quick point-light flash, then self-destructs. No art assets required; swap in the
    /// Lightning sprite sheet later if you want a fancier look.
    /// </summary>
    public class LightningBolt : MonoBehaviour
    {
        private float _life = 0.18f;
        private float _age;
        private LineRenderer _lr;

        public static void Spawn(Vector3 from, Vector3 to)
        {
            var go = new GameObject("LightningBolt");
            var bolt = go.AddComponent<LightningBolt>();
            bolt.Build(from + Vector3.up * 1f, to + Vector3.up * 1f);
        }

        private void Build(Vector3 from, Vector3 to)
        {
            _lr = gameObject.AddComponent<LineRenderer>();
            _lr.useWorldSpace = true;
            _lr.widthMultiplier = 0.12f;
            _lr.numCapVertices = 2;
            _lr.material = new Material(Shader.Find("Sprites/Default") ?? Shader.Find("Unlit/Color"));
            var col = new Color(0.6f, 0.85f, 1f, 1f);
            _lr.startColor = _lr.endColor = col;

            int segments = 8;
            _lr.positionCount = segments + 1;
            Vector3 dir = to - from;
            Vector3 side = Vector3.Cross(dir.normalized, Vector3.up);
            for (int i = 0; i <= segments; i++)
            {
                float t = i / (float)segments;
                Vector3 p = Vector3.Lerp(from, to, t);
                if (i != 0 && i != segments)
                    p += side * Random.Range(-0.35f, 0.35f) + Vector3.up * Random.Range(-0.25f, 0.25f);
                _lr.SetPosition(i, p);
            }

            var lightGo = new GameObject("Flash");
            lightGo.transform.SetParent(transform, false);
            lightGo.transform.position = to + Vector3.up * 1f;
            var light = lightGo.AddComponent<Light>();
            light.color = col;
            light.range = 6f;
            light.intensity = 4f;
        }

        private void Update()
        {
            _age += Time.deltaTime;
            if (_lr != null)
            {
                Color c = _lr.startColor;
                c.a = 1f - Mathf.Clamp01(_age / _life);
                _lr.startColor = _lr.endColor = c;
            }
            if (_age >= _life)
            {
                // The LineRenderer's runtime Material instance isn't freed just by destroying
                // the GameObject that owned it — every cast would otherwise leak one.
                if (_lr != null && _lr.material != null)
                    Destroy(_lr.material);
                Destroy(gameObject);
            }
        }
    }
}
