using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace ExiledAlvaston.Combat
{
    /// <summary>
    /// Evaluates an imported sprite AnimationClip without needing a dedicated AnimatorController.
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
        private PlayableGraph _graph;
        private AnimationClipPlayable _playable;
        private bool _useDirectSampler;

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
            player.Initialise(clip, renderer, loop, lifetime, follow, followOffset);
            return player;
        }

        private void Initialise(AnimationClip clip, SpriteRenderer renderer, bool loop,
            float lifetime, Transform follow, Vector3 followOffset)
        {
            _clip = clip;
            _renderer = renderer;
            _follow = follow;
            _followOffset = followOffset;
            _loop = loop;
            _startedAt = Time.time;
            _lifetime = lifetime > 0f ? lifetime : Mathf.Max(0.02f, clip.length);

            // These imported clips are Mecanim clips (m_Legacy = false). Drive them through an
            // Animator-backed PlayableGraph so their SpriteRenderer binding is evaluated by the
            // same runtime animation system as actor clips, without generating ten one-state
            // AnimatorControllers just for transient effects.
            var animator = gameObject.AddComponent<Animator>();
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            _graph = PlayableGraph.Create($"SpellFX_{clip.name}");
            _graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
            _playable = AnimationClipPlayable.Create(_graph, clip);
            AnimationPlayableOutput output = AnimationPlayableOutput.Create(_graph, "Spell FX", animator);
            output.SetSourcePlayable(_playable);
            _graph.Play();
            Sample(0f);

            // Keep direct sampling as a compatibility fallback. It also makes the failure explicit
            // in the Console if an imported clip ever stops targeting a root SpriteRenderer.
            if (_renderer.sprite == null)
            {
                clip.SampleAnimation(gameObject, 0f);
                _useDirectSampler = _renderer.sprite != null;
            }
            if (_renderer.sprite == null)
                Debug.LogWarning($"SpellFxPlayer: clip '{clip.name}' did not bind a sprite to its root SpriteRenderer.");
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
            Sample(sample);

            if (elapsed >= _lifetime)
                Destroy(gameObject);
        }

        private void LateUpdate()
        {
            if (_follow != null)
                transform.position = _follow.position + _followOffset;

            Camera cam = Camera.main;
            if (cam == null) return;
            // FX are screen-facing rather than merely yaw-facing. This keeps their full area
            // visible under the fixed 30-degree isometric pitch; the roll then aligns a stretched
            // projectile with its two screen-space endpoints.
            transform.rotation = cam.transform.rotation
                               * Quaternion.AngleAxis(_screenAngle, Vector3.forward);
        }

        private void Sample(float time)
        {
            if (_useDirectSampler)
            {
                _clip.SampleAnimation(gameObject, time);
                return;
            }
            if (!_graph.IsValid()) return;
            _playable.SetTime(time);
            _graph.Evaluate(0f);
        }

        private void OnDestroy()
        {
            if (_graph.IsValid())
                _graph.Destroy();
        }
    }
}
