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

        [Tooltip("World height of the sprite. THIS is how you resize an actor — scaling the " +
                 "ActorVisual child instead grows the sprite about its centre and buries the " +
                 "feet, because this component positions that child at Height/2 assuming scale 1.")]
        public float Height = EKVibe.CharacterHeight;
        public float Width = EKVibe.CharacterWidth;

        [Tooltip("Nudges the sprite up or down relative to the actor's feet. Sheet cells are not " +
                 "trimmed, so a subject drawn with space below its feet floats, and a vertical " +
                 "billboard sitting exactly on the floor gets its base clipped by the ground mesh.")]
        public float GroundOffset = 0f;

        [Tooltip("Untick if ActorSprite's artwork faces camera-left by default (e.g. the Bandit pack). Determines which way flipping goes.")]
        public bool SpriteFacesRightByDefault = true;

        [Header("Melee Swing")]
        public float SwingAngle = 55f;
        public float SwingDuration = 0.35f;
        public float LungeDistance = 0.22f;

        [Header("Mounted")]
        [Tooltip("Optional bespoke 'character sat on the vehicle' artwork. When assigned it " +
                 "replaces the whole billboard while riding. Left empty, the vehicle's own sprite " +
                 "is layered under the normal actor sprite instead.")]
        public Sprite MountedSprite;

        [Tooltip("Height of the layered vehicle sprite, as a fraction of the actor's height.")]
        public float VehicleSpriteHeight = 0.62f;

        [Tooltip("Lifts the layered vehicle clear of the ground. Its base sits exactly on the " +
                 "actor's feet otherwise, which puts the bottom row of pixels level with the " +
                 "ground mesh and clips the tyres. Two pixels' worth at 48 px per unit.")]
        public float VehicleGroundClearance = 0.04f;

        private Transform _visualRoot;
        private Transform _swingRoot;
        private SpriteRenderer _sr;
        private Transform _mountRoot;
        private SpriteRenderer _mountSr;
        private Sprite _spriteBeforeMount;
        private bool _isMounted;
        private Animator _spriteAnimator;
        private bool _animatorWasEnabled;
        private Sprite _fittedTo;
        private Coroutine _swingRoutine;
        private Vector3 _swingBaseLocalPos;
        private GameObject _slashFx;
        private Vector3 _swingFacing = Vector3.forward;

        /// <summary>
        /// The name both <c>ArtImportTool</c> and <c>GeneratedEnemyPrefabTool</c> give the attack
        /// state. Capability is probed by state and not by the <c>MeleeAttack</c> parameter, because
        /// every controller either tool builds declares that parameter whether or not there is any
        /// attack art behind it.
        /// </summary>
        private static readonly int AttackStateHash = Animator.StringToHash("Attack");

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
            _visualRoot.localPosition = new Vector3(0f, Height * 0.5f + GroundOffset, 0f);
            _swingRoot.localPosition = Vector3.zero;
            _swingRoot.localRotation = Quaternion.identity;
            _swingBaseLocalPos = Vector3.zero;
        }

        /// <summary>
        /// Re-applies size and offset when they are edited, so Height and GroundOffset can be tuned
        /// in the Inspector — including in play mode — instead of needing a restart to see the
        /// result. Only ever adjusts an existing hierarchy: creating objects from OnValidate is
        /// not allowed.
        /// </summary>
        private void OnValidate()
        {
            if (_visualRoot == null || _swingRoot == null) return;

            FitScaleToHeight();
            _visualRoot.localPosition = new Vector3(0f, Height * 0.5f + GroundOffset, 0f);
        }

        /// <summary>
        /// The actor's own sprite renderer. Callers that want to tint or read the actor — crouch
        /// shading, for one — must go through this rather than GetComponentInChildren, which will
        /// happily hand back the layered vehicle sprite instead once one exists.
        /// </summary>
        public SpriteRenderer ActorRenderer
        {
            get
            {
                EnsureHierarchy();
                return _sr;
            }
        }

        /// <summary>
        /// Hides or shows the actor's own sprite renderer, leaving the rest of the hierarchy alone.
        /// Used by the 3D-car presentation: a car's bodywork is a real model that stays visible
        /// while ridden, so the rider's billboard is hidden instead of the vehicle root (which can
        /// never be deactivated — see VehicleController). The Animator is left running; it drives
        /// m_Sprite on a disabled renderer, which is harmless and keeps the state in step for when
        /// the rider is shown again.
        /// </summary>
        public void SetRiderHidden(bool hidden)
        {
            EnsureHierarchy();
            if (_sr != null)
                _sr.enabled = !hidden;
        }

        /// <summary>
        /// The Animator driving this actor's sprite, or null if it has none. It sits on
        /// <c>ActorVisual/SwingRoot</c> beside the renderer, which is not a path other components
        /// should have to know — EnemyAI wants one for its own field and would otherwise hardcode
        /// the same string this class already owns.
        /// </summary>
        public Animator SpriteAnimator
        {
            get
            {
                if (_spriteAnimator == null)
                {
                    EnsureHierarchy();
                    _spriteAnimator = _swingRoot.GetComponent<Animator>();
                }
                return _spriteAnimator;
            }
        }

        /// <summary>
        /// Puts an Animator where the generated clips expect to find it, and points it at
        /// <paramref name="controller"/>. Returns the Animator, since callers that also drive it
        /// through another component — EnemyAI, which has its own Animator field — would otherwise
        /// have to go looking for it down a path only this class knows.
        ///
        /// That path is <c>ActorVisual/SwingRoot</c>: the same GameObject as the SpriteRenderer,
        /// because the art importer binds every clip with an empty path, which means "the renderer
        /// is on the Animator's own GameObject". One level up and the clips animate nothing while
        /// looking perfectly well wired in the Inspector.
        ///
        /// Lives here rather than in the placement tooling so the editor and the game can share it.
        /// Assets/Editor/ is stripped from builds, so a copy over there is unreachable from
        /// anything that spawns an actor while the game is running.
        /// </summary>
        public Animator AttachAnimator(RuntimeAnimatorController controller)
        {
            if (controller == null) return null;

            EnsureHierarchy();

            var animator = _swingRoot.GetComponent<Animator>();
            if (animator == null) animator = _swingRoot.gameObject.AddComponent<Animator>();

            animator.runtimeAnimatorController = controller;
            // Billboards have no bones, so culling against a skinned bounds nobody ever set would
            // stop the clip updating the moment the actor left those nonexistent bounds.
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            animator.applyRootMotion = false;

            // SetMounted looks this up lazily off the renderer; caching it now keeps the mount
            // suspend/restore path in step from the moment an Animator exists.
            _spriteAnimator = animator;
            return animator;
        }

        /// <summary>
        /// Puts the actor on or off a vehicle. With a MountedSprite assigned that art takes over
        /// the billboard; otherwise <paramref name="vehicleSprite"/> is drawn over the actor's
        /// feet, so any character sprite reads as riding without bespoke art per character.
        /// </summary>
        public void SetMounted(bool mounted, Sprite vehicleSprite)
        {
            EnsureHierarchy();

            if (mounted)
            {
                if (!_isMounted)
                    _spriteBeforeMount = _sr.sprite;
                _isMounted = true;

                if (MountedSprite != null)
                {
                    // An Animator on the sprite's own GameObject rewrites m_Sprite every frame and
                    // would silently undo this. Park it for the duration rather than losing the
                    // bespoke rider art to whatever clip happens to be playing.
                    SuspendSpriteAnimator();

                    _sr.sprite = MountedSprite;
                    FitScaleToHeight();
                    ShowVehicleSprite(null);
                }
                else
                {
                    ShowVehicleSprite(vehicleSprite);
                }
            }
            else
            {
                if (_isMounted && _spriteBeforeMount != null)
                {
                    _sr.sprite = _spriteBeforeMount;
                    FitScaleToHeight();
                }
                _isMounted = false;
                RestoreSpriteAnimator();
                ShowVehicleSprite(null);
            }
        }

        private void SuspendSpriteAnimator()
        {
            if (_spriteAnimator == null && _sr != null)
                _spriteAnimator = _sr.GetComponent<Animator>();

            if (_spriteAnimator == null || !_spriteAnimator.enabled) return;

            _animatorWasEnabled = true;
            _spriteAnimator.enabled = false;
        }

        private void RestoreSpriteAnimator()
        {
            if (_spriteAnimator == null || !_animatorWasEnabled) return;

            _spriteAnimator.enabled = true;
            _animatorWasEnabled = false;
        }

        private void ShowVehicleSprite(Sprite sprite)
        {
            if (sprite == null)
            {
                if (_mountRoot != null)
                    _mountRoot.gameObject.SetActive(false);
                return;
            }

            EnsureMountHierarchy();

            _mountSr.sprite = sprite;
            // In front of the actor, so the rider's legs sit behind the bodywork.
            _mountSr.sortingOrder = _sr != null ? _sr.sortingOrder + 1 : 11;

            float spriteH = sprite.bounds.size.y;
            if (spriteH < 0.001f) spriteH = 1f;
            float targetH = Height * VehicleSpriteHeight;
            _mountRoot.localScale = Vector3.one * (targetH / spriteH);

            // _visualRoot sits at mid-height, so the actor's feet are at -Height * 0.5.
            _mountRoot.localPosition = new Vector3(
                0f,
                -Height * 0.5f + targetH * 0.5f + VehicleGroundClearance,
                0f);
            _mountRoot.gameObject.SetActive(true);
        }

        private void EnsureMountHierarchy()
        {
            if (_mountRoot == null)
            {
                Transform existing = _visualRoot.Find("MountVisual");
                if (existing != null) _mountRoot = existing;
                else
                {
                    // Parented to the billboard root rather than SwingRoot, so a melee swing can
                    // never rotate or lunge the vehicle along with the actor.
                    var go = new GameObject("MountVisual");
                    go.transform.SetParent(_visualRoot, false);
                    _mountRoot = go.transform;
                }
            }

            if (_mountSr == null)
            {
                _mountSr = _mountRoot.GetComponent<SpriteRenderer>();
                if (_mountSr == null)
                    _mountSr = _mountRoot.gameObject.AddComponent<SpriteRenderer>();
            }
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

            // The layered vehicle sprite is drawn facing the same way as the actor, so it has to
            // flip with them. Without this the rider turns left and the vehicle underneath keeps
            // pointing right. The MountedSprite path needs no special case — that art replaces
            // the actor's own sprite and flips with it.
            if (_mountSr != null) _mountSr.flipX = _sr.flipX;
        }

        public void PlayMeleeSwing()
        {
            PlayMeleeSwing(_swingFacing);
        }

        /// <summary>
        /// Faces the actor, then plays the procedural wind-up-and-slash — but only for an actor with
        /// no attack animation of its own. The sprite flip happens either way: it is how the attack
        /// clip ends up pointing the right way.
        /// </summary>
        public void PlayMeleeSwing(Vector3 worldFacing)
        {
            EnsureHierarchy();
            if (worldFacing.sqrMagnitude > 0.0001f)
                SetFacing(worldFacing);

            // The tilt-and-lunge pose and the slash quad are a placeholder from before any actor had
            // attack art, and both call sites fire the MeleeAttack trigger as well as calling this.
            // Once real art exists the two draw on top of each other: the player got a 55° tilt and
            // an opaque quad over the top of a six-frame attack clip. Real art wins, the same way
            // the importer's controller wins over placeholder wiring (CLAUDE.md §13).
            if (HasAttackAnimation())
            {
                // An Animator can arrive after the fact — NpcFactory and MagicTutorial both attach
                // one at runtime — so a procedural swing may be mid-flight. Drop it and clear the
                // pose, or the actor keeps whatever tilt it was part-way through for good.
                if (_swingRoutine != null)
                {
                    StopCoroutine(_swingRoutine);
                    _swingRoutine = null;
                    ApplySwingPose(0f, 0f);
                }
                return;
            }

            if (_swingRoutine != null)
                StopCoroutine(_swingRoutine);
            _swingRoutine = StartCoroutine(MeleeSwingRoutine());
        }

        /// <summary>
        /// True when this actor's Animator holds an Attack state to play, so the procedural swing
        /// should stand aside. False with no Animator, no controller, or a controller that never got
        /// an attack sheet — mosley and pharmacist are Idle-only today, and so is any NPC turned
        /// hostile before its sheets land.
        /// </summary>
        private bool HasAttackAnimation()
        {
            Animator anim = SpriteAnimator;
            return anim != null
                   && anim.runtimeAnimatorController != null
                   && anim.HasState(0, AttackStateHash);
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

        /// <summary>
        /// An Animator drives m_Sprite, so the sprite being displayed is not the one that was
        /// there when the scale was last worked out — and sprites of different pixel sizes or
        /// import PPUs have wildly different bounds. Fitting once at Awake against a stale
        /// ActorSprite produced a player rendered at 4.5 units instead of 1.6, buried to the
        /// waist. Refitting is a reference compare and only recalculates when the sprite changes.
        /// </summary>
        private void LateUpdate()
        {
            if (_sr == null || _sr.sprite == _fittedTo) return;
            FitScaleToHeight();
        }

        private void FitScaleToHeight()
        {
            if (_swingRoot == null) return;

            if (_sr == null || _sr.sprite == null)
            {
                _swingRoot.localScale = new Vector3(Width, Height, 1f);
                _fittedTo = null;
                return;
            }

            float spriteH = _sr.sprite.bounds.size.y;
            if (spriteH < 0.001f) spriteH = 1f;
            float scale = Height / spriteH;
            _swingRoot.localScale = new Vector3(scale, scale, 1f);
            _fittedTo = _sr.sprite;
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