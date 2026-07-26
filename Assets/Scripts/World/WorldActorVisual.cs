using UnityEngine;
using System.Collections;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Swaps primitive mesh visuals for an EK-scale sprite billboard,
    /// and plays a short procedural melee swing when attacking.
    /// </summary>
    public class WorldActorVisual : MonoBehaviour
    {
        public Sprite ActorSprite;
        public Color Tint = Color.white;
        public float Height = EKVibe.CharacterHeight;
        public float Width = EKVibe.CharacterWidth;

        [Tooltip("Untick if ActorSprite's artwork faces camera-left by default (e.g. the Bandit pack). Determines which way flipping goes.")]
        public bool SpriteFacesRightByDefault = true;

        [Header("Melee Swing")]
        public float SwingAngle = 55f;
        public float SwingDuration = 0.35f;
        public float LungeDistance = 0.22f;

        private Transform _visualRoot;
        private Transform _swingRoot;
        private SpriteRenderer _sr;
        private Coroutine _swingRoutine;
        private Vector3 _swingBaseLocalPos;
        private GameObject _slashFx;
        private Vector3 _swingFacing = Vector3.forward;

        private void Awake()
        {
            ApplyVisual();
        }

        public void ApplyVisual()
        {
            HidePrimitiveMesh();
            EnsureHierarchy();

            if (ActorSprite != null)
                _sr.sprite = ActorSprite;

            _sr.color = Tint;
            FitScaleToHeight();
            _visualRoot.localPosition = new Vector3(0f, Height * 0.5f, 0f);
            _swingRoot.localPosition = Vector3.zero;
            _swingRoot.localRotation = Quaternion.identity;
            _swingBaseLocalPos = Vector3.zero;
        }

        /// <summary>Flip sprite / remember aim based on last move facing.</summary>
        public void SetFacing(Vector3 worldFacing)
        {
            worldFacing.y = 0f;
            if (worldFacing.sqrMagnitude < 0.0001f) return;
            _swingFacing = worldFacing.normalized;

            if (_sr == null) return;
            var cam = UnityEngine.Camera.main;
            if (cam == null) return;

            // Flip when facing camera-left (reads as left/right on iso sprites)
            float side = Vector3.Dot(_swingFacing, cam.transform.right);
            bool facingCameraLeft = side < -0.05f;
            _sr.flipX = SpriteFacesRightByDefault ? facingCameraLeft : !facingCameraLeft;
        }

        public void PlayMeleeSwing()
        {
            PlayMeleeSwing(_swingFacing);
        }

        /// <summary>Short wind-up + slash in the given world facing direction.</summary>
        public void PlayMeleeSwing(Vector3 worldFacing)
        {
            EnsureHierarchy();
            if (worldFacing.sqrMagnitude > 0.0001f)
                SetFacing(worldFacing);

            if (_swingRoutine != null)
                StopCoroutine(_swingRoutine);
            _swingRoutine = StartCoroutine(MeleeSwingRoutine());
        }

        private IEnumerator MeleeSwingRoutine()
        {
            float half = SwingDuration * 0.45f;
            float recover = SwingDuration * 0.55f;
            float sideSign = (_sr != null && _sr.flipX) ? -1f : 1f;

            // Wind-up
            float t = 0f;
            while (t < half)
            {
                t += Time.deltaTime;
                float u = Mathf.Clamp01(t / half);
                float ease = u * u;
                float angle = Mathf.Lerp(0f, -SwingAngle * 0.45f * sideSign, ease);
                float lunge = Mathf.Lerp(0f, -LungeDistance * 0.35f, ease);
                ApplySwingPose(angle, lunge);
                yield return null;
            }

            SpawnSlashArc(sideSign);

            // Slash through
            t = 0f;
            while (t < recover)
            {
                t += Time.deltaTime;
                float u = Mathf.Clamp01(t / recover);
                float ease = 1f - (1f - u) * (1f - u);
                float angle = Mathf.Lerp(-SwingAngle * 0.45f * sideSign, SwingAngle * sideSign, ease);
                float lunge = Mathf.Lerp(-LungeDistance * 0.35f, LungeDistance, ease);
                ApplySwingPose(angle, lunge);
                yield return null;
            }

            // Settle
            t = 0f;
            const float settle = 0.12f;
            float startAngle = SwingAngle * sideSign;
            float startLunge = LungeDistance;
            while (t < settle)
            {
                t += Time.deltaTime;
                float u = Mathf.Clamp01(t / settle);
                ApplySwingPose(Mathf.Lerp(startAngle, 0f, u), Mathf.Lerp(startLunge, 0f, u));
                yield return null;
            }

            ApplySwingPose(0f, 0f);
            _swingRoutine = null;
        }

        private void ApplySwingPose(float zAngle, float forwardLunge)
        {
            if (_swingRoot == null || _visualRoot == null) return;

            _swingRoot.localRotation = Quaternion.Euler(0f, 0f, zAngle);

            // Lunge along last facing, expressed in billboard-local space
            Vector3 localDir = _visualRoot.InverseTransformDirection(_swingFacing);
            localDir.y = 0f;
            if (localDir.sqrMagnitude < 0.0001f)
                localDir = Vector3.right * ((_sr != null && _sr.flipX) ? -1f : 1f);
            localDir.Normalize();

            _swingRoot.localPosition = _swingBaseLocalPos + localDir * forwardLunge;
        }

        private void SpawnSlashArc(float sideSign)
        {
            if (_slashFx != null)
                Destroy(_slashFx);

            _slashFx = GameObject.CreatePrimitive(PrimitiveType.Quad);
            _slashFx.name = "SlashFX";
            Object.Destroy(_slashFx.GetComponent<Collider>());
            _slashFx.transform.SetParent(_visualRoot, false);

            Vector3 localDir = _visualRoot != null
                ? _visualRoot.InverseTransformDirection(_swingFacing)
                : Vector3.right * sideSign;
            localDir.y = 0f;
            if (localDir.sqrMagnitude < 0.0001f)
                localDir = Vector3.right * sideSign;
            localDir.Normalize();

            _slashFx.transform.localPosition = localDir * 0.7f + Vector3.up * 0.05f;
            float yaw = Mathf.Atan2(localDir.x, localDir.z) * Mathf.Rad2Deg;
            _slashFx.transform.localRotation = Quaternion.Euler(0f, yaw, -25f * sideSign);
            _slashFx.transform.localScale = new Vector3(0.85f, 0.2f, 1f);

            var r = _slashFx.GetComponent<Renderer>();
            // One material per swing so fade doesn't affect other actors; destroyed with the FX below
            Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Sprites/Default") ?? Shader.Find("Standard");
            var mat = new Material(sh);
            mat.color = new Color(1f, 0.95f, 0.75f, 0.85f);
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

            StartCoroutine(FadeSlash(_slashFx, mat, 0.18f, sideSign));
        }

        private IEnumerator FadeSlash(GameObject fx, Material mat, float life, float sideSign)
        {
            if (fx == null) yield break;
            Color c = mat != null ? mat.color : Color.white;
            float t = 0f;
            Vector3 startScale = fx.transform.localScale;
            Quaternion startRot = fx.transform.localRotation;
            while (t < life && fx != null)
            {
                t += Time.deltaTime;
                float u = Mathf.Clamp01(t / life);
                if (mat != null)
                {
                    Color faded = c;
                    faded.a = Mathf.Lerp(c.a, 0f, u);
                    mat.color = faded;
                }
                fx.transform.localScale = Vector3.Lerp(startScale, startScale * 1.35f, u);
                fx.transform.localRotation = startRot * Quaternion.Euler(0f, 0f, Mathf.Lerp(0f, 60f * sideSign, u));
                yield return null;
            }
            if (fx != null) Destroy(fx);
            if (mat != null) Destroy(mat); // renderer materials are not auto-destroyed with the GameObject
            if (_slashFx == fx) _slashFx = null;
        }

        private void EnsureHierarchy()
        {
            if (_visualRoot == null)
            {
                Transform existing = transform.Find("ActorVisual");
                if (existing != null) _visualRoot = existing;
                else
                {
                    GameObject go = new GameObject("ActorVisual");
                    go.transform.SetParent(transform, false);
                    _visualRoot = go.transform;
                    go.AddComponent<SpriteBillboard>();
                }
            }

            if (_swingRoot == null)
            {
                Transform existingSwing = _visualRoot.Find("SwingRoot");
                if (existingSwing != null) _swingRoot = existingSwing;
                else
                {
                    GameObject swing = new GameObject("SwingRoot");
                    swing.transform.SetParent(_visualRoot, false);
                    _swingRoot = swing.transform;
                }
            }

            if (_sr == null)
            {
                _sr = _swingRoot.GetComponent<SpriteRenderer>();
                if (_sr == null)
                {
                    // Migrate sprite off billboard root if an older setup left it there
                    var old = _visualRoot.GetComponent<SpriteRenderer>();
                    if (old != null)
                    {
                        _sr = _swingRoot.gameObject.AddComponent<SpriteRenderer>();
                        _sr.sprite = old.sprite;
                        _sr.color = old.color;
                        _sr.sortingOrder = old.sortingOrder;
                        Destroy(old);
                    }
                    else
                    {
                        _sr = _swingRoot.gameObject.AddComponent<SpriteRenderer>();
                        _sr.sortingOrder = 10;
                    }
                }
            }
        }

        private void FitScaleToHeight()
        {
            if (_swingRoot == null) return;

            if (_sr == null || _sr.sprite == null)
            {
                _swingRoot.localScale = new Vector3(Width, Height, 1f);
                return;
            }

            float spriteH = _sr.sprite.bounds.size.y;
            if (spriteH < 0.001f) spriteH = 1f;
            float scale = Height / spriteH;
            _swingRoot.localScale = new Vector3(scale, scale, 1f);
        }

        private void HidePrimitiveMesh()
        {
            // Keep capsule visible if no sprite is assigned (avoids invisible player).
            var mr = GetComponent<MeshRenderer>();
            if (mr != null)
                mr.enabled = ActorSprite == null;
        }
    }
}
