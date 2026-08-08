using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using System.Collections.Generic;
using ExiledAlvaston.Data;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// EK-style HUD: portrait + bars, combat log, location/time, joystick, action cluster.
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        public static UIManager Instance { get; private set; }

        [Header("HUD Panels")]
        public RectTransform TopLeftPortraitPanel;
        public RectTransform BottomCenterQuickSlotPanel;
        public RectTransform RightActionPanel;
        public RectTransform CombatLogPanel;
        public VirtualJoystick Joystick;

        [Header("Player HUD")]
        public Image PlayerPortrait;
        public Image PlayerHealthFill;
        public Image PlayerManaFill;
        public Image PlayerConcealmentFill;
        [Tooltip("Numeric \"current / max\" readouts drawn over the bars. Auto-built at runtime if left empty.")]
        public TextMeshProUGUI PlayerHealthText;
        public TextMeshProUGUI PlayerManaText;
        public TextMeshProUGUI PlayerConcealmentText;
        public TextMeshProUGUI LevelText;
        public TextMeshProUGUI LocationTimeText;
        public TextMeshProUGUI WantedKnivesText;

        [Header("Combat Log")]
        public TextMeshProUGUI CombatLogText;
        public int MaxCombatLogLines = 5;

        [Header("Companion HUD")]
        public GameObject CompanionHUDTemplate;
        public Transform CompanionHUDContainer;

        [Header("Interact")]
        [Tooltip("Small label showing what's interactable nearby, e.g. 'Open Chest'.")]
        public TextMeshProUGUI InteractPromptText;
        [Tooltip("The Interact HUD button itself — disabled/hidden when nothing is in range.")]
        public GameObject InteractButtonRoot;

        private readonly Queue<string> _logLines = new Queue<string>();
        private float _playerHpMax = 100f;
        private float _playerMpMax = 50f;
        private float _playerConcealmentMax = 100f;

        /// <summary>The 4 spell-slot button backgrounds + labels, refreshed to show bound spells.</summary>
        private readonly Image[] _spellSlotImages = new Image[4];
        private readonly TextMeshProUGUI[] _spellSlotLabels = new TextMeshProUGUI[4];

        /// <summary>
        /// The crouch button's background and label. Unlike the spell slots these are not polled
        /// every frame — IsCrouched only ever changes inside StealthController.ToggleStealth, which
        /// calls RefreshCrouchButton itself, so both the button and the C key keep it in step.
        /// </summary>
        private Image _crouchButtonImage;
        private TextMeshProUGUI _crouchButtonLabel;

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            EnsureJournalButton();
            BuildActionButtons();
            RestyleSceneHudButtons();
            ScaleHudCluster();
            EnsureHudSafeArea();
        }

        /// <summary>
        /// Keeps the whole gameplay HUD inside the device's reported safe area. There has never
        /// been a SafeAreaFitter on it — the only two in c.unity sit under the title and creator
        /// layouts — and the cluster is 16 px from the left edge, which in landscape is exactly
        /// where a notch or a rounded corner lands.
        ///
        /// HUDPanel is already a full stretch with zero offsets and zero anchoredPosition, which is
        /// what SafeAreaFitter overwrites, so it is a drop-in.
        ///
        /// ⚠ This moves the <b>whole</b> HUD, including the runtime-built action buttons and the
        /// joystick — wanted, since a home indicator is as much in their way as a notch is in the
        /// cluster's, but a bigger behavioural change than anything else here. ⚠ It is also
        /// invisible in a 16:9 Game view, which reports no inset: seeing nothing change there is
        /// not evidence that it works. Window → General → Device Simulator, landscape, notched
        /// device.
        /// </summary>
        private void EnsureHudSafeArea()
        {
            Transform hud = FindChildRecursive(transform, "HUDPanel");
            if (hud != null && hud.GetComponent<SafeAreaFitter>() == null)
                hud.gameObject.AddComponent<SafeAreaFitter>();
        }

        /// <summary>
        /// Grows the top-left cluster to something readable at arm's length on a phone.
        ///
        /// Scales the <b>panel</b>, never an element inside it. The four children are positioned by
        /// absolute anchoredPosition, so scaling the panel preserves the authored layout exactly,
        /// where resizing each element would mean re-deriving every offset — and would fight
        /// <see cref="EnsureDedicatedTrack"/>, which copies anchors, pivot, anchoredPosition and
        /// sizeDelta between rects. localScale touches none of those, so the two cannot interact.
        /// ⚠ That only holds while this is the one and only localScale write in the HUD.
        ///
        /// The panel's pivot and anchor are both (0,1), so it grows right and down from the screen
        /// corner and its safe-area exposure is unchanged.
        ///
        /// ⚠ Assign, never multiply. If anything ever runs this twice — a HUD rebuild, a second
        /// UIManager — an assignment is idempotent and a multiply leaves the cluster at 2.56x,
        /// which reads as a baffling layout bug rather than a double call.
        /// </summary>
        private void ScaleHudCluster()
        {
            if (TopLeftPortraitPanel != null)
                TopLeftPortraitPanel.localScale = Vector3.one * EKVibe.HudClusterScale;
        }

        /// <summary>
        /// The legacy scene buttons still visible — MapBagShortcut ("Bag") and the authored USE
        /// button — get the Win95 skin at runtime. The rest of the legacy cluster is retired by
        /// BuildActionButtons, so restyling it in the scene would paint objects nobody sees.
        /// </summary>
        private void RestyleSceneHudButtons()
        {
            Transform bag = FindChildRecursive(transform, "MapBagShortcut");
            if (bag != null)
            {
                var btn = bag.GetComponent<Button>();
                if (btn != null) Win95Skin.StyleButton(btn);

                var label = bag.GetComponentInChildren<TextMeshProUGUI>(true);
                if (label != null) Win95Skin.StyleLabel(label);
            }

            // The scene-authored USE button predates the skin, and EnsureInteractUI returns
            // early precisely because it exists — so this is the only restyle it ever gets.
            if (InteractButtonRoot != null)
            {
                var useBtn = InteractButtonRoot.GetComponent<Button>();
                if (useBtn != null) Win95Skin.StyleButton(useBtn);

                var useLabel = InteractButtonRoot.GetComponentInChildren<TextMeshProUGUI>(true);
                if (useLabel != null) Win95Skin.StyleLabel(useLabel);
            }
        }

        /// <summary>
        /// The level currently painted into the HUD badge; -1 until the first paint.
        ///
        /// Polled rather than subscribed, like RefreshSpellSlots below: PlayerSession is a
        /// DontDestroyOnLoad singleton that need not exist when this Start runs. ⚠ The int compare
        /// is the point — SetLevel calls level.ToString(), which allocates, and calling it every
        /// frame would put a per-frame allocation on a mobile hot path.
        /// </summary>
        private int _shownLevel = -1;

        private void Update()
        {
            RefreshSpellSlots();

            var session = Flow.PlayerSession.Instance;
            if (session != null && session.Level != _shownLevel)
            {
                _shownLevel = session.Level;
                SetLevel(_shownLevel);
            }

#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            if (Input.GetKeyDown(KeyCode.J))
            {
                var flow = Flow.GameFlowController.Instance;
                if (flow == null || flow.State == Flow.GameFlowState.Playing)
                    QuestJournalUI.Toggle();
            }
#endif
        }

        public void UpdatePlayerHealth(int current, int max)
        {
            _playerHpMax = Mathf.Max(1, max);
            SetBarFill(PlayerHealthFill, current / _playerHpMax);

            EnsureBarLabel(ref PlayerHealthText, PlayerHealthFill, "HPText");
            if (PlayerHealthText != null)
                PlayerHealthText.text = $"{Mathf.Max(0, current)} / {(int)_playerHpMax}";
        }

        public void UpdatePlayerMana(int current, int max)
        {
            _playerMpMax = Mathf.Max(1, max);
            SetBarFill(PlayerManaFill, current / _playerMpMax);

            EnsureBarLabel(ref PlayerManaText, PlayerManaFill, "MPText");
            if (PlayerManaText != null)
                PlayerManaText.text = $"{Mathf.Max(0, current)} / {(int)_playerMpMax}";
        }

        public void UpdatePlayerConcealment(float current, float max)
        {
            _playerConcealmentMax = Mathf.Max(1, max);
            SetBarFill(PlayerConcealmentFill, current / _playerConcealmentMax);

            EnsureBarLabel(ref PlayerConcealmentText, PlayerConcealmentFill, "ConcealmentText");
            if (PlayerConcealmentText != null)
                PlayerConcealmentText.text = $"{Mathf.Max(0, (int)current)} / {(int)_playerConcealmentMax}";
        }

        /// <summary>
        /// Sets a bar's fill to <paramref name="frac"/> (0..1) by resizing the fill rect's width.
        /// The bar fills are plain Images with no sprite, and a spriteless Image ignores
        /// <c>fillAmount</c> (it always draws the full rect) — so we drive the width via the
        /// right anchor instead. fillAmount is left at 1 so that if a sprite is ever assigned it
        /// simply fills the (already width-scaled) rect — no double scaling.
        /// </summary>
        private static void SetBarFill(Image fill, float frac)
        {
            if (fill == null) return;

            // Must run before the anchors below are touched — it needs the authored rect.
            EnsureDedicatedTrack(fill);

            frac = Mathf.Clamp01(frac);
            fill.fillAmount = 1f;

            var rt = fill.rectTransform;
            rt.anchorMin = new Vector2(0f, 0f);
            rt.anchorMax = new Vector2(frac, 1f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        /// <summary>
        /// Gives a bar fill its own parent when the scene did not, and does nothing when it already
        /// has one. Both <see cref="SetBarFill"/> and <see cref="EnsureBarLabel"/> assume the fill's
        /// parent is a track that exists purely to hold it: the former stretches the fill across
        /// that parent, the latter stretches the readout across it too.
        ///
        /// That assumption held for HPFill in HPTrack and MPFill in MPTrack, and silently did not
        /// for ConcealmentBar, whose parent in c.unity is TopLeftPortraits — the container for the
        /// whole top-left cluster. So the concealment bar stretched across every other HUD element,
        /// and its "100 / 100" readout was drawn centred over the same area, landing on top of the
        /// mana bar's own readout. It surfaced on leaving the pub only because HaveAPint is what
        /// first calls UpdatePlayerConcealment, and the label is built on first update.
        ///
        /// Wrapping rather than fixing the scene keeps this correct for any bar wired later, and
        /// costs nothing when the scene is already right. It is self-limiting: after wrapping, the
        /// fill is an only child, so every later call returns at the first check.
        /// </summary>
        private static void EnsureDedicatedTrack(Image fill)
        {
            Transform parent = fill.transform.parent;
            if (parent == null || parent.childCount == 1) return;   // already has a track of its own

            var fillRt = fill.rectTransform;

            var track = new GameObject(fill.gameObject.name + "Track", typeof(RectTransform));
            var trackRt = (RectTransform)track.transform;
            trackRt.SetParent(parent, false);
            trackRt.SetSiblingIndex(fillRt.GetSiblingIndex());

            // The track takes over the rect the fill was authored with, so the bar stays exactly
            // where the scene put it.
            trackRt.anchorMin = fillRt.anchorMin;
            trackRt.anchorMax = fillRt.anchorMax;
            trackRt.pivot = fillRt.pivot;
            trackRt.anchoredPosition = fillRt.anchoredPosition;
            trackRt.sizeDelta = fillRt.sizeDelta;

            // ...and the fill now fills the track, which is what SetBarFill goes on to shrink.
            fillRt.SetParent(trackRt, false);
            fillRt.anchorMin = Vector2.zero;
            fillRt.anchorMax = Vector2.one;
            fillRt.offsetMin = Vector2.zero;
            fillRt.offsetMax = Vector2.zero;
        }

        /// <summary>
        /// Draws a "current / max" readout centered over a bar so the fill reads as an actual
        /// amount, not just a colored strip. Built lazily over the fill's track the first time
        /// the bar updates (like the other runtime HUD bits), so no scene wiring is required.
        ///
        /// Relies on the fill having a parent that holds nothing else — see
        /// <see cref="EnsureDedicatedTrack"/>, which guarantees that.
        /// </summary>
        private void EnsureBarLabel(ref TextMeshProUGUI label, Image fill, string name)
        {
            if (label != null || fill == null) return;

            Transform track = fill.transform.parent != null ? fill.transform.parent : fill.transform;
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(track, false);       // after the fill child → renders on top
            var rt = (RectTransform)go.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;

            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.enableAutoSizing = false;
            tmp.fontSize = 18;
            tmp.fontStyle = FontStyles.Bold;
            tmp.color = EKVibe.TextLight;
            tmp.raycastTarget = false;
            tmp.enableWordWrapping = false;
            tmp.overflowMode = TextOverflowModes.Overflow;
            label = tmp;
        }

        public void SetLevel(int level)
        {
            if (LevelText != null)
                LevelText.text = level.ToString();
        }

        public void SetLocationTime(string location, int day, string clock)
        {
            if (LocationTimeText != null)
                LocationTimeText.text = $"{location}; Day {day}, {clock}";
        }

        public void UpdateKnivesUI(int knives)
        {
            if (WantedKnivesText != null)
                WantedKnivesText.text = $"Knives: {knives}";
        }

        /// <summary>EK combat log style: "> Elite Bandit hits you, 14-7=7"</summary>
        public void LogCombat(string message)
        {
            if (string.IsNullOrEmpty(message)) return;
            if (!message.StartsWith(">"))
                message = "> " + message;

            _logLines.Enqueue(message);
            while (_logLines.Count > MaxCombatLogLines)
                _logLines.Dequeue();

            if (CombatLogText != null)
                CombatLogText.text = string.Join("\n", _logLines);
        }

        /// <summary>Faint transient message near the top of the screen (e.g. the city-magic warning).</summary>
        public void ShowToast(string message, float hold = 1.8f, float fade = 0.7f)
        {
            if (string.IsNullOrEmpty(message)) return;

            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;
            var go = new GameObject("Toast", typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.8f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(960, 60);

            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = message;
            tmp.fontSize = 30;
            tmp.fontStyle = FontStyles.Italic;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.color = new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.85f);
            tmp.raycastTarget = false;

            StartCoroutine(ToastRoutine(go, tmp, hold, fade));
        }

        private IEnumerator ToastRoutine(GameObject go, TextMeshProUGUI tmp, float hold, float fade)
        {
            Color baseC = tmp.color;
            yield return new WaitForSecondsRealtime(hold);
            float t = 0f;
            while (t < fade)
            {
                t += Time.unscaledDeltaTime;
                if (tmp != null)
                {
                    Color c = baseC;
                    c.a = baseC.a * (1f - t / fade);
                    tmp.color = c;
                }
                yield return null;
            }
            if (go != null) Destroy(go);
        }

        public void OnActionButtonPressed(int abilityIndex)
        {
            var combat = Combat.CombatController.Instance;
            if (combat != null)
                combat.TryCastAbility(abilityIndex);
        }

        public void OnAttackPressed()
        {
            var combat = Combat.CombatController.Instance;
            if (combat != null)
                combat.PerformMeleeAttack();
        }

        public void OnInventoryPressed()
        {
            var inv = FindObjectOfType<InventoryController>();
            if (inv != null)
                inv.ToggleInventory();
        }

        public void OnInteractPressed()
        {
            World.PlayerInteractor.Instance?.TryInteract();
        }

        /// <summary>
        /// Crouch toggle. Until this existed, stealth was reachable only by pressing C, which on a
        /// touchscreen-first game meant stealth — and therefore pickpocketing, which requires
        /// IsCrouched — could not be used on a device at all.
        /// </summary>
        public void OnCrouchPressed()
        {
            var stealth = World.StealthController.Instance ?? FindObjectOfType<World.StealthController>();
            stealth?.ToggleStealth();
        }

        /// <summary>Called by PlayerInteractor whenever the closest in-range Interactable changes.</summary>
        public void SetInteractPrompt(string prompt)
        {
            bool has = !string.IsNullOrEmpty(prompt);

            if (has)
                EnsureInteractUI();

            if (InteractPromptText != null)
                InteractPromptText.text = has ? prompt : "";

            if (InteractButtonRoot != null)
                InteractButtonRoot.SetActive(has);
        }

        /// <summary>
        /// Small always-visible HUD button (top-right, under the location text) that opens
        /// the quest journal. Built at runtime; sits inside HUDPanel so it hides with the HUD.
        /// </summary>
        private void EnsureJournalButton()
        {
            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;
            if (parent.Find("JournalButton") != null) return;

            var btn = new GameObject("JournalButton", typeof(RectTransform));
            btn.transform.SetParent(parent, false);
            var rt = (RectTransform)btn.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(1, 1);
            rt.pivot = new Vector2(1, 1);
            rt.anchoredPosition = new Vector2(-24, -120);
            rt.sizeDelta = new Vector2(72, 56);
            btn.AddComponent<Image>();
            var bagBtn = btn.AddComponent<Button>();
            Win95Skin.StyleButton(bagBtn);
            bagBtn.onClick.AddListener(QuestJournalUI.Toggle);

            var labelGO = new GameObject("Label", typeof(RectTransform));
            labelGO.transform.SetParent(btn.transform, false);
            var lrt = (RectTransform)labelGO.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGO.AddComponent<TextMeshProUGUI>();
            tmp.text = "LOG";
            tmp.fontSize = 20;
            tmp.alignment = TextAlignmentOptions.Center;
            Win95Skin.StyleLabel(tmp);
        }

        /// <summary>
        /// Builds the USE button + prompt label at runtime if the scene doesn't have them
        /// wired (the old editor setup tool is no longer required).
        /// </summary>
        private void EnsureInteractUI()
        {
            if (InteractButtonRoot != null && InteractPromptText != null) return;

            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;

            if (InteractButtonRoot == null)
            {
                var btn = new GameObject("InteractButton", typeof(RectTransform));
                btn.transform.SetParent(parent, false);
                var rt = (RectTransform)btn.transform;
                rt.anchorMin = rt.anchorMax = new Vector2(1, 0);
                rt.pivot = new Vector2(1, 0);
                rt.anchoredPosition = new Vector2(-140, 260);
                rt.sizeDelta = new Vector2(90, 90);
                btn.AddComponent<Image>();
                var useBtn = btn.AddComponent<Button>();
                Win95Skin.StyleButton(useBtn);
                var action = btn.AddComponent<HUDActionButton>();
                action.Kind = HUDActionButton.ActionKind.Interact;

                var labelGO = new GameObject("InteractLabel", typeof(RectTransform));
                labelGO.transform.SetParent(btn.transform, false);
                var lrt = (RectTransform)labelGO.transform;
                lrt.anchorMin = Vector2.zero;
                lrt.anchorMax = Vector2.one;
                lrt.offsetMin = Vector2.zero;
                lrt.offsetMax = Vector2.zero;
                var labelTmp = labelGO.AddComponent<TextMeshProUGUI>();
                labelTmp.text = "USE";
                labelTmp.fontSize = 20;
                labelTmp.alignment = TextAlignmentOptions.Center;
                Win95Skin.StyleLabel(labelTmp);

                InteractButtonRoot = btn;
            }

            if (InteractPromptText == null)
            {
                var promptGO = new GameObject("InteractPrompt", typeof(RectTransform));
                promptGO.transform.SetParent(parent, false);
                var prt = (RectTransform)promptGO.transform;
                prt.anchorMin = prt.anchorMax = new Vector2(1, 0);
                prt.pivot = new Vector2(1, 0);
                prt.anchoredPosition = new Vector2(-30, 360);
                prt.sizeDelta = new Vector2(280, 40);
                var tmp = promptGO.AddComponent<TextMeshProUGUI>();
                tmp.text = "";
                tmp.color = EKVibe.TextLight;
                tmp.fontSize = 22;
                tmp.alignment = TextAlignmentOptions.Right;
                tmp.raycastTarget = false;

                InteractPromptText = tmp;
            }
        }

        /// <summary>
        /// Builds the bottom-right action controls in code: a vertical column of 4 spell buttons
        /// (ability slots 0-3), the big ATK melee button, and repositions USE beside ATK. Replaces
        /// the old scene cluster + quick-slot bar so the layout lives in one place and is easy to tweak.
        /// </summary>
        private void BuildActionButtons()
        {
            Transform hud = FindChildRecursive(transform, "HUDPanel") ?? transform;

            // Retire the old scene controls.
            if (RightActionPanel != null) RightActionPanel.gameObject.SetActive(false);
            if (BottomCenterQuickSlotPanel != null) BottomCenterQuickSlotPanel.gameObject.SetActive(false);

            var panel = new GameObject("ActionButtons", typeof(RectTransform));
            panel.transform.SetParent(hud, false);
            var prt = (RectTransform)panel.transform;
            prt.anchorMin = prt.anchorMax = new Vector2(1f, 0f);
            prt.pivot = new Vector2(1f, 0f);
            prt.anchoredPosition = Vector2.zero;
            prt.sizeDelta = Vector2.zero;

            // ATK — big melee button, bottom-right.
            CreateActionButton(panel.transform, "ATK", HUDActionButton.ActionKind.Attack, 0,
                new Vector2(130f, 130f), new Vector2(-24f, 30f));

            // 4 spell slots, vertical column above ATK, right-aligned.
            const float size = 100f, gap = 12f, baseY = 175f;
            for (int i = 0; i < 4; i++)
            {
                float y = baseY + i * (size + gap);
                var b = CreateActionButton(panel.transform, (i + 1).ToString(),
                    HUDActionButton.ActionKind.Ability, i, new Vector2(size, size),
                    new Vector2(-24f, y));
                _spellSlotImages[i] = b.GetComponent<Image>();
                _spellSlotLabels[i] = b.GetComponentInChildren<TextMeshProUGUI>();
            }

            // CRO — crouch toggle, third in the bottom row: ATK, USE, CRO reading right to left.
            // Same size as USE and permanently visible, unlike USE, which hides with its prompt.
            var crouch = CreateActionButton(panel.transform, "CRO", HUDActionButton.ActionKind.Crouch, 0,
                new Vector2(110f, 110f), new Vector2(-424f, 40f));
            _crouchButtonImage = crouch.GetComponent<Image>();
            _crouchButtonLabel = crouch.GetComponentInChildren<TextMeshProUGUI>();
            RefreshCrouchButton();

            RepositionInteractButton();
        }

        /// <summary>
        /// Paints the crouch button to match StealthController.IsCrouched. Called by the controller
        /// on every toggle — from the button and from the C key alike — and once at build time, so a
        /// HUD rebuilt while already crouching does not come back showing "stood up".
        /// </summary>
        public void RefreshCrouchButton()
        {
            if (_crouchButtonImage == null && _crouchButtonLabel == null) return;

            var stealth = World.StealthController.Instance;
            bool crouched = stealth != null && stealth.IsCrouched;

            // Win95 toggle: crouched reads as a pressed-in button — darker face, sunken bevel.
            if (_crouchButtonImage != null)
            {
                _crouchButtonImage.color = crouched ? Win95Skin.FacePressed : Win95Skin.Face;
                Win95Skin.AddBevel((RectTransform)_crouchButtonImage.transform, sunken: crouched);
            }

            if (_crouchButtonLabel != null)
            {
                _crouchButtonLabel.text = crouched ? "STAND" : "CRO";
                _crouchButtonLabel.fontSize = crouched ? 20 : 24;
            }
        }

        private GameObject CreateActionButton(Transform parent, string label, HUDActionButton.ActionKind kind,
            int abilityIndex, Vector2 size, Vector2 pos)
        {
            var go = new GameObject(kind == HUDActionButton.ActionKind.Ability ? $"Spell{abilityIndex}" : label,
                typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(1f, 0f);
            rt.pivot = new Vector2(1f, 0f);
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;

            go.AddComponent<Image>();
            var btn = go.AddComponent<Button>();
            Win95Skin.StyleButton(btn);
            var action = go.AddComponent<HUDActionButton>(); // wires click + cooldown sweep
            action.Kind = kind;
            action.AbilityIndex = abilityIndex;

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false); // after the cooldown overlay → on top
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.text = label;
            tmp.fontSize = kind == HUDActionButton.ActionKind.Attack ? 26 : 24;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            Win95Skin.StyleLabel(tmp);
            return go;
        }

        /// <summary>Moves USE in line with ATK, ~half an inch to its left, a touch smaller.</summary>
        private void RepositionInteractButton()
        {
            EnsureInteractUI();
            if (InteractButtonRoot != null)
            {
                var rt = InteractButtonRoot.GetComponent<RectTransform>();
                if (rt != null)
                {
                    rt.anchorMin = rt.anchorMax = new Vector2(1f, 0f);
                    rt.pivot = new Vector2(1f, 0f);
                    rt.sizeDelta = new Vector2(110f, 110f);
                    rt.anchoredPosition = new Vector2(-224f, 40f);
                }
            }
            if (InteractPromptText != null)
            {
                var prt = InteractPromptText.GetComponent<RectTransform>();
                if (prt != null)
                {
                    prt.anchorMin = prt.anchorMax = new Vector2(1f, 0f);
                    prt.pivot = new Vector2(1f, 0f);
                    prt.sizeDelta = new Vector2(260f, 36f);
                    prt.anchoredPosition = new Vector2(-149f, 158f); // just above USE
                    InteractPromptText.alignment = TextAlignmentOptions.Center;
                }
            }
        }

        /// <summary>Shows each bound spell's glyph and dims empty slots.</summary>
        private void RefreshSpellSlots()
        {
            var combat = Combat.CombatController.Instance;
            for (int i = 0; i < _spellSlotImages.Length; i++)
            {
                AbilityData ability = null;
                if (combat != null && combat.EquippedAbilities != null && i < combat.EquippedAbilities.Count)
                    ability = combat.EquippedAbilities[i];
                bool bound = ability != null;

                if (_spellSlotImages[i] != null)
                {
                    Color c = EKVibe.ButtonBrown;
                    if (!bound) c.a = 0.35f;
                    _spellSlotImages[i].color = c;
                }
                if (_spellSlotLabels[i] != null)
                {
                    if (bound)
                    {
                        string glyph = !string.IsNullOrEmpty(ability.IconGlyph) ? ability.IconGlyph
                            : (!string.IsNullOrEmpty(ability.AbilityName) ? ability.AbilityName.Substring(0, 1) : (i + 1).ToString());
                        _spellSlotLabels[i].text = glyph;
                        _spellSlotLabels[i].fontSize = 40;
                        _spellSlotLabels[i].color = EKVibe.TextLight;
                    }
                    else
                    {
                        _spellSlotLabels[i].text = (i + 1).ToString();
                        _spellSlotLabels[i].fontSize = 24;
                        _spellSlotLabels[i].color = new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.5f);
                    }
                }
            }
        }

        private static Transform FindChildRecursive(Transform root, string name)
        {
            foreach (Transform child in root)
            {
                if (child.name == name) return child;
                Transform found = FindChildRecursive(child, name);
                if (found != null) return found;
            }
            return null;
        }
    }
}
