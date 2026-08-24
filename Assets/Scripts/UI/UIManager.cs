using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using System.Collections.Generic;
using GBHEngland.Data;
using GBHEngland.Vibe;

namespace GBHEngland.UI
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
        [Tooltip("Built at runtime by EnsureStaminaBar — there is nothing to wire in the scene.")]
        public Image PlayerStaminaFill;
        [Tooltip("Numeric \"current / max\" readouts drawn over the bars. Auto-built at runtime if left empty.")]
        public TextMeshProUGUI PlayerHealthText;
        public TextMeshProUGUI PlayerManaText;
        public TextMeshProUGUI PlayerConcealmentText;
        public TextMeshProUGUI PlayerStaminaText;
        public TextMeshProUGUI LevelText;
        public TextMeshProUGUI LocationTimeText;

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

        [Header("Wanted meter")]
        [Tooltip("The single knife glyph the 5-icon wanted meter is built from. Wired by hand in " +
                 "the Inspector — with no sprite the meter is not built at all.")]
        public Sprite WantedKnifeIcon;

        private readonly Queue<string> _logLines = new Queue<string>();
        private float _playerHpMax = 100f;
        private float _playerMpMax = 50f;
        private float _playerConcealmentMax = 100f;

        /// <summary>The 4 spell-slot button backgrounds + labels, refreshed to show bound spells.</summary>
        private readonly Image[] _spellSlotImages = new Image[4];
        private readonly TextMeshProUGUI[] _spellSlotLabels = new TextMeshProUGUI[4];
        private readonly AbilityData[] _cachedEquippedAbilities = new AbilityData[4];
        private bool _spellSlotsInitialized;

        /// <summary>
        /// The SPN and DSH button backgrounds + labels, and what they were last painted from.
        /// ⚠ Repainted from Update like the spell slots, so the cache and the early-out are what
        /// keep a per-frame allocation off a mobile hot path. The class is cached alongside the
        /// assets because availability is a class gate, and PlayerSession can be created after
        /// this HUD has been built.
        /// </summary>
        private readonly Image[] _specialSlotImages = new Image[Combat.CombatController.SpecialSlots];
        private readonly TextMeshProUGUI[] _specialSlotLabels = new TextMeshProUGUI[Combat.CombatController.SpecialSlots];
        private readonly AbilityData[] _cachedSpecials = new AbilityData[Combat.CombatController.SpecialSlots];
        private PlayerClass _cachedSpecialClass = PlayerClass.YoungDriller;
        private bool _specialSlotsInitialized;

        /// <summary>Placeholder glyphs for the two special buttons, held in a static array so the
        /// repaint never builds a string. Replaced by the asset's IconGlyph once the owner sets
        /// one, exactly as RefreshSpellSlots does for a bound spell.</summary>
        private static readonly string[] SpecialPlaceholders = { "SPN", "DSH" };

        /// <summary>The 5 knife icons of the wanted meter, left to right. Null until
        /// <see cref="EnsureWantedMeter"/> has run, and left null entirely if it bailed.</summary>
        private readonly Image[] _wantedKnifeIcons = new Image[5];

        /// <summary>
        /// The crouch button's background and label. Unlike the spell slots these are not polled
        /// every frame — IsCrouched only ever changes inside StealthController.ToggleStealth, which
        /// calls RefreshCrouchButton itself, so both the button and the C key keep it in step.
        /// </summary>
        private Image _crouchButtonImage;
        private TextMeshProUGUI _crouchButtonLabel;
        private Sprite _shownPlayerPortrait;
        private bool _playerPortraitPainted;

        // Driving cluster references
        private GameObject _actionButtonsPanel;
        private GameObject _drivingButtonsPanel;
        private UITouchHoldButton _gasPedal;
        private UITouchHoldButton _brakePedal;
        private UITouchHoldButton _driftButton;
        private TextMeshProUGUI _exitVehicleLabel;

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void Start()
        {
            EnsureJournalButton();
            EnsureWantedMeter();
            EnsureStaminaBar();
            RetireConcealmentBar();
            BuildActionButtons();
            BuildDrivingButtons();
            RestyleSceneHudButtons();
            PreparePlayerPortraitFrame();
            RefreshPlayerPortrait();
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
            RefreshSpecialSlots();
            RefreshPlayerPortrait();

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

        /// <summary>
        /// Turns the scene's old brown placeholder into the same sunken grey slot used by the
        /// Win95 inventory and dialogue windows. The bevel stays visible over the eventual image.
        /// </summary>
        private void PreparePlayerPortraitFrame()
        {
            if (PlayerPortrait == null) return;
            PlayerPortrait.preserveAspect = true;
            PlayerPortrait.raycastTarget = false;
            Win95Skin.StyleSunken(PlayerPortrait);

            // StyleSunken appends four Win95Skin.Edge strips as children, and children draw in
            // sibling order — so the bevel lands on top of LevelBadge, which the scene authored
            // first, and a grey line crosses the badge. Push the badge back to the end. Nothing is
            // moved or resized: this is purely draw order, and the badge's own rect is untouched.
            Transform badge = PlayerPortrait.transform.Find("LevelBadge");
            if (badge != null) badge.SetAsLastSibling();
        }

        /// <summary>
        /// PlayerSession can appear after this HUD's Start (title screen -> creator -> game), so
        /// portrait binding is a cheap reference poll rather than an Awake-order dependency.
        /// No per-frame allocation: the Image is only repainted when its Sprite reference changes.
        /// </summary>
        private void RefreshPlayerPortrait()
        {
            if (PlayerPortrait == null) return;

            CharacterData data = Flow.PlayerSession.Instance != null
                ? Flow.PlayerSession.Instance.RuntimeStats
                : (Combat.CombatController.Instance != null
                    ? Combat.CombatController.Instance.PlayerData
                    : null);
            Sprite portrait = data != null ? data.Portrait : null;
            if (_playerPortraitPainted && portrait == _shownPlayerPortrait) return;

            _playerPortraitPainted = true;
            _shownPlayerPortrait = portrait;
            PlayerPortrait.sprite = portrait;
            PlayerPortrait.color = portrait != null ? Color.white : Win95Skin.SlotFill;
            PlayerPortrait.preserveAspect = true;
            PlayerPortrait.enabled = true;
        }

        private int _shownHp = -1;
        private int _shownHpMax = -1;

        public void UpdatePlayerHealth(int current, int max)
        {
            if (current == _shownHp && max == _shownHpMax) return;
            _shownHp = current;
            _shownHpMax = max;

            _playerHpMax = Mathf.Max(1, max);
            SetBarFill(PlayerHealthFill, (float)current / _playerHpMax);

            EnsureBarLabel(ref PlayerHealthText, PlayerHealthFill, "HPText");
            if (PlayerHealthText != null)
                PlayerHealthText.text = $"{Mathf.Max(0, current)} / {(int)_playerHpMax}";
        }

        private int _shownMp = -1;
        private int _shownMpMax = -1;

        public void UpdatePlayerMana(int current, int max)
        {
            if (current == _shownMp && max == _shownMpMax) return;
            _shownMp = current;
            _shownMpMax = max;

            _playerMpMax = Mathf.Max(1, max);
            SetBarFill(PlayerManaFill, (float)current / _playerMpMax);

            EnsureBarLabel(ref PlayerManaText, PlayerManaFill, "MPText");
            if (PlayerManaText != null)
                PlayerManaText.text = $"{Mathf.Max(0, current)} / {(int)_playerMpMax}";
        }

        /// <summary>The stamina last painted, and the max it was painted against; -1 until first
        /// paint. ⚠ The int compare is the point, exactly as for <see cref="_shownLevel"/>: this is
        /// called from CombatController's Update every frame, and the interpolated string below
        /// allocates. Stamina only moves when a roll is spent or the regen carry rolls over, so
        /// most frames do nothing at all.</summary>
        private int _shownStamina = -1;
        private int _shownStaminaMax = -1;

        public void UpdatePlayerStamina(int current, int max)
        {
            if (PlayerStaminaFill == null) return;
            if (current == _shownStamina && max == _shownStaminaMax) return;

            _shownStamina = current;
            _shownStaminaMax = max;

            float safeMax = Mathf.Max(1, max);
            SetBarFill(PlayerStaminaFill, current / safeMax);

            if (PlayerStaminaText != null)
                PlayerStaminaText.text = $"{Mathf.Max(0, current)} / {(int)safeMax}";
        }

        /// <summary>
        /// Builds the stamina bar under the mana bar at runtime, so no scene wiring is needed and
        /// the bar cannot go missing on a scene that predates it.
        ///
        /// ⚠ The fill gets a track of its own that holds nothing else, and the readout is built
        /// here and assigned rather than left to <see cref="EnsureBarLabel"/> — SPText is a sibling
        /// of StaminaFillTrack, not of StaminaFill itself, so the fill's own parent never gains a
        /// second child no matter how many times this runs. <see cref="EnsureDedicatedTrack"/> now
        /// decides a fill needs wrapping by the parent's name rather than its child count, which
        /// fixed the equivalent trap for HPFill and MPFill too — see the note there — but this
        /// bar was built to avoid ever needing that fix in the first place.
        /// </summary>
        private void EnsureStaminaBar()
        {
            if (PlayerStaminaFill != null) return;          // idempotent

            if (PlayerManaFill == null || PlayerManaFill.transform.parent == null)
            {
                Debug.LogWarning("UIManager: no PlayerManaFill to place the stamina bar against — " +
                                 "the stamina bar was not built.");
                return;
            }

            var mpTrack = PlayerManaFill.transform.parent as RectTransform;
            var cluster = mpTrack != null ? mpTrack.parent as RectTransform : null;
            if (mpTrack == null || cluster == null) return;

            // One bar pitch below the mana bar. HPTrack is authored at y -22 and MPTrack at -58, so
            // the cluster's real pitch is 36, and -36 puts stamina at -94: HP, MP and SP equally
            // spaced down the same column. The panel is 116 tall and the bar is 28, so -94 still
            // sits inside it — which is why nothing here grows the panel any more.
            //
            // ⚠ The inactive ConcealmentBar is authored at -86 in the same column and would overlap
            // this. It is switched off in c.unity, so nothing is drawn over anything today, but
            // whoever brings stealth back has to place it rather than assume a slot is waiting.
            const float BarPitch = 36f;

            var track = new GameObject("StaminaTrack", typeof(RectTransform), typeof(Image));
            var trackRt = (RectTransform)track.transform;
            trackRt.SetParent(cluster, false);
            trackRt.SetSiblingIndex(mpTrack.GetSiblingIndex() + 1);
            trackRt.anchorMin = mpTrack.anchorMin;
            trackRt.anchorMax = mpTrack.anchorMax;
            trackRt.pivot = mpTrack.pivot;
            trackRt.sizeDelta = mpTrack.sizeDelta;
            trackRt.anchoredPosition = mpTrack.anchoredPosition + new Vector2(0f, -BarPitch);

            var trackImage = track.GetComponent<Image>();
            // The empty channel behind the fill: the same amber darkened, alpha kept at 1 — a plain
            // Color multiply would scale alpha too and leave the track see-through.
            Color amber = EKVibe.StaminaBar;
            trackImage.color = new Color(amber.r * 0.3f, amber.g * 0.3f, amber.b * 0.3f, 1f);
            trackImage.raycastTarget = false;

            // The fill's own parent, which will only ever hold the fill — see the summary above.
            var fillTrack = new GameObject("StaminaFillTrack", typeof(RectTransform));
            var fillTrackRt = (RectTransform)fillTrack.transform;
            fillTrackRt.SetParent(trackRt, false);
            StretchToParent(fillTrackRt);

            var fill = new GameObject("StaminaFill", typeof(RectTransform), typeof(Image));
            var fillRt = (RectTransform)fill.transform;
            fillRt.SetParent(fillTrackRt, false);
            StretchToParent(fillRt);

            var fillImage = fill.GetComponent<Image>();
            fillImage.color = EKVibe.StaminaBar;
            fillImage.raycastTarget = false;
            PlayerStaminaFill = fillImage;

            // Added after the fill track, so it renders over the bar rather than under it.
            var labelGo = new GameObject("SPText", typeof(RectTransform));
            var labelRt = (RectTransform)labelGo.transform;
            labelRt.SetParent(trackRt, false);
            StretchToParent(labelRt);

            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.enableAutoSizing = false;
            tmp.fontSize = 18;
            tmp.fontStyle = FontStyles.Bold;
            tmp.color = EKVibe.TextLight;
            tmp.raycastTarget = false;
            tmp.enableWordWrapping = false;
            tmp.overflowMode = TextOverflowModes.Overflow;
            PlayerStaminaText = tmp;
        }

        private static void StretchToParent(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        /// <summary>
        /// Deactivates the legacy 100/100 ConcealmentBar from the HUD. The wanted level is now
        /// exclusively represented by the 5-knives meter (EnsureWantedMeter / UpdateKnivesUI).
        /// </summary>
        private void RetireConcealmentBar()
        {
            if (PlayerConcealmentFill != null)
            {
                if (PlayerConcealmentFill.transform.parent != null &&
                    PlayerConcealmentFill.transform.parent.name.Contains("Concealment"))
                {
                    PlayerConcealmentFill.transform.parent.gameObject.SetActive(false);
                }
                PlayerConcealmentFill.gameObject.SetActive(false);
            }
            if (PlayerConcealmentText != null)
                PlayerConcealmentText.gameObject.SetActive(false);

            Transform concealmentBar = FindChildRecursive(transform, "ConcealmentBar");
            if (concealmentBar != null)
                concealmentBar.gameObject.SetActive(false);
        }

        /// <summary>
        /// Legacy wanted/concealment meter update. The wanted meter is now represented by the
        /// knives meter (UpdateKnivesUI). This is a no-op to preserve caller signatures.
        /// </summary>
        public void UpdatePlayerConcealment(float current, float max)
        {
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
        /// fill is an only child of its new track, so every later call sees that track's name and
        /// returns at the first check.
        ///
        /// ⚠ **Fixed defect, worth knowing the shape of.** This used to test
        /// `parent.childCount == 1` rather than the parent's name. <see cref="EnsureBarLabel"/>
        /// adds the readout as a sibling of the fill after its first paint, taking that count from
        /// 1 to 2 — so the SECOND call here saw a track that already existed and wrapped it again
        /// anyway, inheriting the anchors the fill happened to be showing at that moment as the new
        /// track's permanent width. If that first paint was not full, the bar was capped at that
        /// fraction forever. HPFill and MPFill both took this path; it was invisible in the common
        /// case because the first paint is a full bar (anchorMax.x = 1), and it would show as "the
        /// health bar tops out at a third" after loading a save at low health. The name check below
        /// is immune to what <see cref="EnsureBarLabel"/> does, because every track this method or
        /// <see cref="EnsureStaminaBar"/> creates is suffixed "Track" and the scene's own HPTrack
        /// and MPTrack already were, so nothing here depends on how many children live inside one.
        /// </summary>
        private static void EnsureDedicatedTrack(Image fill)
        {
            Transform parent = fill.transform.parent;
            if (parent == null || parent.name.EndsWith("Track")) return;   // already a dedicated track

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

        /// <summary>
        /// Builds the 5-icon wanted meter across the top-centre of the HUD. Replaces a
        /// "Knives: n" label that was never wired in c.unity, so the wanted level — the single
        /// most consequential number in the GTA layer — had no readout at all.
        ///
        /// Idempotent by name, the same way <see cref="EnsureJournalButton"/> is: a second call
        /// finds the container and returns.
        ///
        /// ⚠ No sprite means no meter. There is deliberately no blank-square fallback — five grey
        /// boxes across the top of the screen read as a layout bug rather than as a missing
        /// assignment, and the warning below is the only thing that would say otherwise.
        /// </summary>
        private void EnsureWantedMeter()
        {
            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;
            if (parent.Find("WantedMeter") != null) return;      // idempotent

            if (WantedKnifeIcon == null)
            {
                Debug.LogWarning("UIManager: WantedKnifeIcon is unassigned — the wanted meter was " +
                                 "not built. Assign Assets/Art/Generated/ui/spr_ui_wanted_knife.png " +
                                 "to UIManager.WantedKnifeIcon in the Inspector.");
                return;
            }

            const float IconSize = 72f, IconPitch = 86f;

            var meter = new GameObject("WantedMeter", typeof(RectTransform));
            meter.transform.SetParent(parent, false);
            var mrt = (RectTransform)meter.transform;
            mrt.anchorMin = mrt.anchorMax = new Vector2(0.5f, 1f);
            mrt.pivot = new Vector2(0.5f, 1f);
            mrt.anchoredPosition = new Vector2(0f, -10f);
            mrt.sizeDelta = new Vector2(IconPitch * 4f + IconSize, IconSize);

            for (int i = 0; i < _wantedKnifeIcons.Length; i++)
            {
                var iconGo = new GameObject("WantedKnife" + i, typeof(RectTransform));
                iconGo.transform.SetParent(mrt, false);
                var irt = (RectTransform)iconGo.transform;
                irt.anchorMin = irt.anchorMax = new Vector2(0f, 1f);
                irt.pivot = new Vector2(0f, 1f);
                irt.sizeDelta = new Vector2(IconSize, IconSize);
                irt.anchoredPosition = new Vector2(i * IconPitch, 0f);

                var img = iconGo.AddComponent<Image>();
                img.sprite = WantedKnifeIcon;
                img.preserveAspect = true;
                img.raycastTarget = false;
                _wantedKnifeIcons[i] = img;
            }

            // WantedManager may or may not exist yet; either way the meter must not start blank-
            // looking-but-actually-unpainted, so paint the current level (or 0) once here.
            UpdateKnivesUI(Systems.WantedManager.Instance != null
                ? Systems.WantedManager.Instance.CurrentKnives
                : 0);

            // The combat log is authored at (0,-12) under the same top-centre anchor, which is
            // exactly where the meter now sits. Moving it here — rather than in the scene — keeps
            // the two coordinated in one place, so resizing the meter above can't silently start
            // overlapping the log again.
            if (CombatLogPanel != null)
                CombatLogPanel.anchoredPosition = new Vector2(0f, -144f);
        }

        /// <summary>
        /// Paints the wanted meter. Unlit knives are dimmed rather than hidden, so a wanted level
        /// of 2 still reads as "2 of 5" instead of "2 of however many there are".
        /// </summary>
        public void UpdateKnivesUI(int knives)
        {
            knives = Mathf.Clamp(knives, 0, _wantedKnifeIcons.Length);
            for (int i = 0; i < _wantedKnifeIcons.Length; i++)
            {
                if (_wantedKnifeIcons[i] == null) continue;
                _wantedKnifeIcons[i].color = i < knives ? Color.white : new Color(1f, 1f, 1f, 0.18f);
            }
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
            // 0.72, not 0.8: the combat log now sits at y -144 under the top-centre anchor, and a
            // toast at 0.8 lands on its last line.
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.72f);
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
        public void OnDodgePressed()
        {
            var combat = Combat.CombatController.Instance;
            if (combat != null)
                combat.PerformDodge();
        }

        /// <summary>
        /// SPN / DSH. <paramref name="index"/> is the position in CombatController.SpecialAttacks:
        /// 0 is the spin, 1 is the dash. Every gate — the cooldown, the stamina cost, the class
        /// gate, the riding refusal — lives in TrySpecialAttack, so this is only the route in.
        /// </summary>
        public void OnSpecialAttackPressed(int index)
        {
            var combat = Combat.CombatController.Instance;
            if (combat != null)
                combat.TrySpecialAttack(index);
        }

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
        /// Small always-visible HUD button that opens the quest journal. Built at runtime; sits
        /// inside HUDPanel so it hides with the HUD.
        ///
        /// Top-<i>left</i>, below the portrait cluster — not top-right, where it used to sit. The
        /// wanted meter now runs across the top centre and the right-hand column is the action
        /// cluster's, so the left edge under the bars is the only place left that isn't a thumb
        /// rest during play.
        /// </summary>
        private void EnsureJournalButton()
        {
            Transform parent = FindChildRecursive(transform, "HUDPanel") ?? transform;
            if (parent.Find("JournalButton") != null) return;

            var btn = new GameObject("JournalButton", typeof(RectTransform));
            btn.transform.SetParent(parent, false);
            var rt = (RectTransform)btn.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = new Vector2(16, -216);
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
        ///
        /// ⚠ The panel is a full stretch, not a zero-size rect pinned to the bottom-right corner.
        /// It has to be: CRO now anchors to the bottom-<i>left</i> so it can sit over the joystick,
        /// and a child can only anchor to a corner its parent actually has.
        /// </summary>
        private void BuildActionButtons()
        {
            Transform hud = FindChildRecursive(transform, "HUDPanel") ?? transform;

            // Retire the old scene controls.
            if (RightActionPanel != null) RightActionPanel.gameObject.SetActive(false);
            if (BottomCenterQuickSlotPanel != null) BottomCenterQuickSlotPanel.gameObject.SetActive(false);

            var panel = new GameObject("ActionButtons", typeof(RectTransform));
            panel.transform.SetParent(hud, false);
            _actionButtonsPanel = panel;
            var prt = (RectTransform)panel.transform;
            prt.anchorMin = Vector2.zero;
            prt.anchorMax = Vector2.one;
            prt.pivot = new Vector2(0.5f, 0.5f);
            prt.offsetMin = Vector2.zero;
            prt.offsetMax = Vector2.zero;

            var rightEdge = new Vector2(1f, 0f);

            // ATK — big melee button, bottom-right.
            CreateActionButton(panel.transform, "ATK", HUDActionButton.ActionKind.Attack, 0,
                new Vector2(165f, 165f), new Vector2(-24f, 30f), rightEdge);

            // 4 spell slots, vertical column above ATK, right-aligned.
            const float size = 125f, gap = 12f, baseY = 215f;
            for (int i = 0; i < 4; i++)
            {
                float y = baseY + i * (size + gap);
                var b = CreateActionButton(panel.transform, (i + 1).ToString(),
                    HUDActionButton.ActionKind.Ability, i, new Vector2(size, size),
                    new Vector2(-24f, y), rightEdge);
                _spellSlotImages[i] = b.GetComponent<Image>();
                _spellSlotLabels[i] = b.GetComponentInChildren<TextMeshProUGUI>();
            }

            // CRO — crouch toggle, moved to the left thumb, centred directly above the joystick.
            // Permanently visible, unlike USE, which hides with its prompt.
            var crouch = CreateActionButton(panel.transform, "CRO", HUDActionButton.ActionKind.Crouch, 0,
                new Vector2(130f, 130f), CrouchButtonPosition(130f), new Vector2(0f, 0f));
            _crouchButtonImage = crouch.GetComponent<Image>();
            _crouchButtonLabel = crouch.GetComponentInChildren<TextMeshProUGUI>();
            RefreshCrouchButton();

            // DGE — dodge roll, immediately left of USE in the bottom-right row: ATK, USE, DGE
            // reading right to left. 361 = USE's 205 + its 140 width + a 16 px gap.
            CreateActionButton(panel.transform, "DGE", HUDActionButton.ActionKind.Dodge, 0,
                new Vector2(140f, 140f), new Vector2(-361f, 40f), rightEdge);

            // SPN / DSH — the row continues leftward: ATK, USE, DGE, SPN, DSH reading right to
            // left. 517 = DGE's 361 + its 140 width + a 16 px gap. 673 = 517 + 140 + 16.
            // ⚠ Parented to panel.transform like the rest of the row, deliberately:
            // SetDrivingMode hides this panel, so a special button parented anywhere else would
            // stay on screen while driving, where BlockedByRiding refuses it a toast at a time.
            var spin = CreateActionButton(panel.transform, SpecialPlaceholders[0],
                HUDActionButton.ActionKind.Special, 0,
                new Vector2(140f, 140f), new Vector2(-517f, 40f), rightEdge);
            _specialSlotImages[0] = spin.GetComponent<Image>();
            _specialSlotLabels[0] = spin.GetComponentInChildren<TextMeshProUGUI>();

            var dash = CreateActionButton(panel.transform, SpecialPlaceholders[1],
                HUDActionButton.ActionKind.Special, 1,
                new Vector2(140f, 140f), new Vector2(-673f, 40f), rightEdge);
            _specialSlotImages[1] = dash.GetComponent<Image>();
            _specialSlotLabels[1] = dash.GetComponentInChildren<TextMeshProUGUI>();

            RepositionInteractButton();
        }

        /// <summary>
        /// Builds the mobile vehicle driving cluster: GAS, BRAKE, DRIFT, and EXIT buttons.
        /// Kept inactive until MountController triggers driving mode.
        /// </summary>
        private void BuildDrivingButtons()
        {
            Transform hud = FindChildRecursive(transform, "HUDPanel") ?? transform;

            var panel = new GameObject("DrivingButtons", typeof(RectTransform));
            panel.transform.SetParent(hud, false);
            _drivingButtonsPanel = panel;
            var prt = (RectTransform)panel.transform;
            prt.anchorMin = Vector2.zero;
            prt.anchorMax = Vector2.one;
            prt.pivot = new Vector2(0.5f, 0.5f);
            prt.offsetMin = Vector2.zero;
            prt.offsetMax = Vector2.zero;

            var rightEdge = new Vector2(1f, 0f);

            // GAS / ACCEL Pedal — Large vertical target bottom-right
            var gasGo = CreateHoldPedal(panel.transform, "GAS", new Vector2(160f, 180f), new Vector2(-24f, 30f), rightEdge, 28f);
            _gasPedal = gasGo.GetComponent<UITouchHoldButton>();

            // BRAKE / REVERSE Pedal — Left of Gas
            var brakeGo = CreateHoldPedal(panel.transform, "BRAKE", new Vector2(140f, 160f), new Vector2(-204f, 30f), rightEdge, 24f);
            _brakePedal = brakeGo.GetComponent<UITouchHoldButton>();

            // DRIFT / HANDBRAKE — Directly above Gas
            var driftGo = CreateHoldPedal(panel.transform, "DRIFT", new Vector2(130f, 110f), new Vector2(-24f, 230f), rightEdge, 22f);
            _driftButton = driftGo.GetComponent<UITouchHoldButton>();

            // EXIT / GET OUT — Upper left of the driving cluster
            var exitGo = CreateActionButton(panel.transform, "EXIT", HUDActionButton.ActionKind.Interact, 0,
                new Vector2(110f, 90f), new Vector2(-174f, 210f), rightEdge);
            var exitBtn = exitGo.GetComponent<Button>();
            exitBtn.onClick.RemoveAllListeners();
            exitBtn.onClick.AddListener(OnVehicleExitPressed);
            _exitVehicleLabel = exitGo.GetComponentInChildren<TextMeshProUGUI>();
            if (_exitVehicleLabel != null) _exitVehicleLabel.fontSize = 20f;

            _drivingButtonsPanel.SetActive(false);
        }

        private GameObject CreateHoldPedal(Transform parent, string label, Vector2 size, Vector2 pos, Vector2 anchor, float fontSize)
        {
            var go = new GameObject(label + "Pedal", typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = anchor;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;

            var img = go.AddComponent<Image>();
            img.color = Win95Skin.Face;
            Win95Skin.AddBevel(rt, sunken: false);
            go.AddComponent<UITouchHoldButton>();

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false);
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.text = label;
            tmp.fontSize = fontSize;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            Win95Skin.StyleLabel(tmp);
            return go;
        }

        public void SetDrivingMode(bool isDriving, World.VehicleController vehicle)
        {
            if (_actionButtonsPanel != null) _actionButtonsPanel.SetActive(!isDriving);
            if (_drivingButtonsPanel != null)
            {
                _drivingButtonsPanel.SetActive(isDriving);
                if (!isDriving)
                {
                    _gasPedal?.ResetState();
                    _brakePedal?.ResetState();
                    _driftButton?.ResetState();
                }
            }
            if (InteractButtonRoot != null) InteractButtonRoot.SetActive(!isDriving);
        }

        public float TouchThrottle => (_gasPedal != null && _drivingButtonsPanel != null && _drivingButtonsPanel.activeSelf) ? _gasPedal.Value : 0f;
        public float TouchBrake => (_brakePedal != null && _drivingButtonsPanel != null && _drivingButtonsPanel.activeSelf) ? _brakePedal.Value : 0f;
        public bool TouchDrift => (_driftButton != null && _drivingButtonsPanel != null && _drivingButtonsPanel.activeSelf) && _driftButton.IsPressed;

        public void OnVehicleExitPressed()
        {
            World.MountController.Current?.Dismount();
        }

        /// <summary>
        /// Where CRO goes: horizontally centred over the joystick, 24 px above its top edge.
        ///
        /// Computed from the joystick's live rect rather than hardcoded, because the joystick's
        /// size is authored in c.unity and is the kind of thing that gets retuned in the Inspector
        /// — a literal here would drift off it silently the first time that happened. Both rects
        /// use anchor and pivot (0,0), so the joystick's anchoredPosition is its bottom-left corner
        /// and no pivot correction is needed.
        ///
        /// The fallback matches a 280 px joystick at (40,40), which is what the scene holds.
        /// </summary>
        private Vector2 CrouchButtonPosition(float buttonSize)
        {
            var joyRt = Joystick != null ? Joystick.GetComponent<RectTransform>() : null;
            if (joyRt == null) return new Vector2(120f, 344f);

            Vector2 joyPos = joyRt.anchoredPosition;
            Vector2 joySize = joyRt.sizeDelta;
            return new Vector2(joyPos.x + (joySize.x - buttonSize) * 0.5f,
                               joyPos.y + joySize.y + 24f);
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

        /// <summary>
        /// Builds one action button. <paramref name="anchor"/> is required rather than defaulted to
        /// the old bottom-right, and drives both the anchors and the pivot, so a caller cannot
        /// place a button against one corner while measuring it from another.
        /// </summary>
        private GameObject CreateActionButton(Transform parent, string label, HUDActionButton.ActionKind kind,
            int abilityIndex, Vector2 size, Vector2 pos, Vector2 anchor)
        {
            var go = new GameObject(kind == HUDActionButton.ActionKind.Ability ? $"Spell{abilityIndex}" : label,
                typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = anchor;
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

        /// <summary>Moves USE in line with ATK, immediately to its left, a touch smaller.</summary>
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
                    rt.sizeDelta = new Vector2(140f, 140f);
                    rt.anchoredPosition = new Vector2(-205f, 40f);
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
                    prt.anchoredPosition = new Vector2(-160f, 200f); // just above USE
                    InteractPromptText.alignment = TextAlignmentOptions.Center;
                }
            }
        }

        /// <summary>Shows each bound spell's glyph and dims empty slots.</summary>
        private void RefreshSpellSlots()
        {
            var combat = Combat.CombatController.Instance;
            bool changed = !_spellSlotsInitialized;
            for (int i = 0; i < _spellSlotImages.Length; i++)
            {
                AbilityData ability = null;
                if (combat != null && combat.EquippedAbilities != null && i < combat.EquippedAbilities.Count)
                    ability = combat.EquippedAbilities[i];

                if (_cachedEquippedAbilities[i] != ability)
                {
                    _cachedEquippedAbilities[i] = ability;
                    changed = true;
                }
            }

            if (!changed) return;
            _spellSlotsInitialized = true;

            for (int i = 0; i < _spellSlotImages.Length; i++)
            {
                AbilityData ability = _cachedEquippedAbilities[i];
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

        /// <summary>
        /// Paints the two special buttons: full face when the slot holds a special this class may
        /// use, dimmed when the slot is empty or the class is gated out. Polled from Update like
        /// RefreshSpellSlots and early-outs the same way — the cache compare is the whole reason
        /// this is safe to call every frame.
        ///
        /// Win95Skin.Face deliberately, not the EKVibe.ButtonBrown the spell column repaints
        /// itself with: these two sit in the ATK / USE / DGE row and match that row.
        /// </summary>
        private void RefreshSpecialSlots()
        {
            var combat = Combat.CombatController.Instance;
            var session = Flow.PlayerSession.Instance;
            PlayerClass playerClass = session != null ? session.Class : PlayerClass.YoungDriller;

            bool changed = !_specialSlotsInitialized || playerClass != _cachedSpecialClass;
            _cachedSpecialClass = playerClass;

            for (int i = 0; i < _cachedSpecials.Length; i++)
            {
                AbilityData ability = combat != null ? combat.GetSpecial(i) : null;
                if (_cachedSpecials[i] != ability)
                {
                    _cachedSpecials[i] = ability;
                    changed = true;
                }
            }

            if (!changed) return;
            _specialSlotsInitialized = true;

            for (int i = 0; i < _specialSlotImages.Length; i++)
            {
                AbilityData ability = _cachedSpecials[i];
                bool available = ability != null && ability.CanBeUsedBy(_cachedSpecialClass);

                if (_specialSlotImages[i] != null)
                {
                    Color c = Win95Skin.Face;
                    if (!available) c.a = 0.35f;
                    _specialSlotImages[i].color = c;
                }

                if (_specialSlotLabels[i] != null)
                {
                    string placeholder = i < SpecialPlaceholders.Length ? SpecialPlaceholders[i] : "SPC";
                    _specialSlotLabels[i].text = available && !string.IsNullOrEmpty(ability.IconGlyph)
                        ? ability.IconGlyph
                        : placeholder;
                    _specialSlotLabels[i].color = available
                        ? EKVibe.TextLight
                        : new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.5f);
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
