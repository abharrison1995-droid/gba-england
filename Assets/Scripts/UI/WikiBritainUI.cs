using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// The single funnel for granting WIKIBRITAIN entries. Every trigger — chunk arrivals,
    /// NPC conversations, future quest rewards — goes through here, so they all get the same
    /// behaviour: PlayerSession records the unlock by EntryID (a save key), and a genuinely
    /// new, non-silent unlock pops the toast.
    ///
    /// Silent vs toast is the caller's call: live arrivals by the player's own feet toast;
    /// world-build paths (save load, new-game start, respawns, arrests) grant silently.
    /// </summary>
    public static class WikiUnlock
    {
        /// <summary>Grants an entry. Returns true if this call newly unlocked it.</summary>
        public static bool Grant(WikiEntryData entry, bool silent = false)
        {
            if (entry == null || string.IsNullOrEmpty(entry.EntryID)) return false;
            var session = PlayerSession.Instance;
            if (session == null || !session.UnlockWikiEntry(entry.EntryID)) return false;
            if (!silent) WikiEntryToastUI.Show(entry);
            return true;
        }

        /// <summary>Grants the location entry linked to the named chunk, if one exists.</summary>
        public static void GrantForChunk(string chunkName, bool silent)
        {
            WikiEntryData entry = WikiDatabase.FindForChunk(chunkName);
            if (entry != null) Grant(entry, silent);
        }
    }

    /// <summary>
    /// The "NEW WIKIBRITAIN ENTRY" toast: a small top-centre note, like the quest popup but
    /// smaller and — crucially — NON-pausing. Because the game keeps running, it cannot wait
    /// for a click: it auto-dismisses after a few seconds (unscaled time, so a loading-screen
    /// pause can't freeze it open), and tapping it only dismisses it early — it never opens
    /// the wiki, since that would pause the player mid-fight. Multiple unlocks queue.
    /// </summary>
    public class WikiEntryToastUI : MonoBehaviour
    {
        private static WikiEntryToastUI _instance;
        private static readonly Queue<WikiEntryData> _pending = new Queue<WikiEntryData>();

        private const float ShowSeconds = 3.5f;

        private GameObject _root;
        private TextMeshProUGUI _titleText;
        private float _dismissAt;

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        public static void Show(WikiEntryData entry)
        {
            if (entry == null) return;

            if (IsOpen)
            {
                _pending.Enqueue(entry);
                return;
            }

            if (_instance == null)
            {
                var go = new GameObject("WikiEntryToastUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<WikiEntryToastUI>();
                _instance.BuildUI();
            }
            _instance.Open(entry);
        }

        private void Open(WikiEntryData entry)
        {
            _titleText.text = entry.Title;
            _root.SetActive(true);
            _dismissAt = Time.unscaledTime + ShowSeconds;
        }

        private void Dismiss()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            if (_pending.Count > 0)
                Show(_pending.Dequeue());
        }

        private void Update()
        {
            if (IsOpen && Time.unscaledTime >= _dismissAt)
                Dismiss();
        }

        private void BuildUI()
        {
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "WikiToastCanvas", 610);

            // No dimmer: the toast never pauses, so it must not eat taps meant for the world.
            GameObject panel = QuestUIBuilder.CreateImage("Toast", canvasGO.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            _root = panel;
            var prt = (RectTransform)panel.transform;
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 1f);
            prt.pivot = new Vector2(0.5f, 1f);
            prt.anchoredPosition = new Vector2(0f, -80f); // just under the HUD location bar
            prt.sizeDelta = new Vector2(460f, 130f);

            // Tap = dismiss early, nothing else (see class doc).
            panel.AddComponent<Button>().onClick.AddListener(Dismiss);

            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, Win95Skin.TitleBar);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0f, 1f);
            hrt.anchorMax = Vector2.one;
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0f, 40f);

            var headerLabel = QuestUIBuilder.CreateTMP("HeaderLabel", header.transform, "NEW WIKIBRITAIN ENTRY",
                Win95Skin.TitleText, 18, TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(headerLabel.gameObject, Vector2.zero, Vector2.one);

            _titleText = QuestUIBuilder.CreateTMP("EntryTitle", panel.transform, "",
                Win95Skin.FieldText, 24, TextAlignmentOptions.Center, FontStyles.Bold);
            var trt = _titleText.rectTransform;
            trt.anchorMin = new Vector2(0f, 0f);
            trt.anchorMax = new Vector2(1f, 1f);
            trt.offsetMin = new Vector2(12f, 10f);
            trt.offsetMax = new Vector2(-12f, -48f);
            _titleText.raycastTarget = false;

            _root.SetActive(false);
        }
    }

    /// <summary>
    /// WIKIBRITAIN — the encyclopedia window, opened from the bag's rail button. Two panes:
    /// a scrollable entry list on the left grouped by category (locked entries read "???" and
    /// don't open), and a detail pane on the right with a fixed image banner across the top
    /// (placeholder until art is assigned), the title under it, and the body in a scroll field.
    ///
    /// Pauses while open. BACK returns to the bag; X / dimmer / E / W close to gameplay.
    /// Entirely code-built from the shared QuestUIBuilder/Win95Skin primitives.
    /// </summary>
    public class WikiBritainUI : MonoBehaviour
    {
        private static WikiBritainUI _instance;

        private GameObject _root;
        private Transform _listContainer;
        private RectTransform _listContent;
        private ScrollRect _listScroll;
        private float _cursorY;

        private Image _bannerImage;
        private GameObject _bannerPlaceholder;
        private TextMeshProUGUI _dTitle;
        private TextMeshProUGUI _dBody;
        private ScrollRect _bodyScroll;
        private TextMeshProUGUI _countText;

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        public static void Open()
        {
            if (_instance == null)
            {
                var go = new GameObject("WikiBritainUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<WikiBritainUI>();
                _instance.BuildUI();
            }
            _instance.OpenInternal();
        }

        /// <summary>Hotkey-style toggle, matching the journal/map: refuses to stack on another paused menu.</summary>
        public static void Toggle()
        {
            if (IsOpen)
            {
                _instance.Close();
                return;
            }
            if (Systems.PauseManager.IsPaused) return;
            Open();
        }

        private void OpenInternal()
        {
            if (IsOpen) return;
            PopulateList();
            ShowFirstUnlockedOrHint();
            _root.SetActive(true);
            Systems.PauseManager.Push();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            Systems.PauseManager.Pop();
        }

        /// <summary>BACK returns to the bag the wiki was opened from — the map's exact pause-balanced hand-off.</summary>
        private void Back()
        {
            Close();
            var inv = FindObjectOfType<InventoryController>(true);
            if (inv != null && !inv.IsOpen)
                inv.ToggleInventory();
        }

        private void Update()
        {
#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            if (IsOpen && (Input.GetKeyDown(KeyCode.E) || Input.GetKeyDown(KeyCode.W)))
                Close();
#endif
        }

        // ── Entry list ──────────────────────────────────────────────────────────────────

        private static bool IsUnlocked(WikiEntryData entry)
        {
            var session = PlayerSession.Instance;
            return session != null && session.IsWikiEntryUnlocked(entry.EntryID);
        }

        private void PopulateList()
        {
            foreach (Transform child in _listContainer)
                Destroy(child.gameObject);
            _cursorY = 8f;

            IReadOnlyList<WikiEntryData> entries = WikiDatabase.All;
            int total = 0, unlocked = 0;

            // Enum order is append-only, so categories always group in a stable order.
            foreach (WikiCategory cat in Enum.GetValues(typeof(WikiCategory)))
            {
                bool headerShown = false;
                foreach (WikiEntryData entry in entries)
                {
                    if (entry == null || entry.Category != cat) continue;
                    total++;
                    if (!headerShown)
                    {
                        AddSectionLabel(cat.ToString().ToUpperInvariant());
                        headerShown = true;
                    }
                    bool isUnlocked = IsUnlocked(entry);
                    if (isUnlocked) unlocked++;
                    AddEntryRow(entry, isUnlocked);
                }
            }

            if (total == 0)
                AddSectionLabel("No entries exist yet.");

            FinalizeList();
            if (_countText != null)
                _countText.text = $"{unlocked} / {total} entries";
        }

        private void FinalizeList()
        {
            if (_listContent != null)
                _listContent.sizeDelta = new Vector2(0f, _cursorY + 4f);
            if (_listScroll != null)
                _listScroll.verticalNormalizedPosition = 1f;
        }

        private void AddSectionLabel(string text)
        {
            var tmp = QuestUIBuilder.CreateTMP("Section", _listContainer, text,
                Win95Skin.TitleBar, 18, TextAlignmentOptions.BottomLeft, FontStyles.Bold);
            var rt = tmp.rectTransform;
            rt.anchorMin = new Vector2(0f, 1f);
            rt.anchorMax = new Vector2(1f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.sizeDelta = new Vector2(-20f, 30f);
            rt.anchoredPosition = new Vector2(0f, -_cursorY);
            tmp.raycastTarget = false;
            _cursorY += 30f + 8f;
        }

        private void AddEntryRow(WikiEntryData entry, bool isUnlocked)
        {
            const float rowH = 52f;
            GameObject row = QuestUIBuilder.CreateImage("EntryRow", _listContainer,
                isUnlocked ? Win95Skin.SlotFill : Win95Skin.Shadow);
            Win95Skin.AddBevel((RectTransform)row.transform, sunken: true);
            var rrt = row.GetComponent<RectTransform>();
            rrt.anchorMin = new Vector2(0f, 1f);
            rrt.anchorMax = new Vector2(1f, 1f);
            rrt.pivot = new Vector2(0.5f, 1f);
            rrt.sizeDelta = new Vector2(-8f, rowH);
            rrt.anchoredPosition = new Vector2(0f, -_cursorY);

            // Locked rows are deliberately not clickable — "???" is all you get until discovery.
            if (isUnlocked)
                row.AddComponent<Button>().onClick.AddListener(() => ShowDetail(entry));

            var label = QuestUIBuilder.CreateTMP("Label", row.transform,
                isUnlocked ? entry.Title : "???",
                isUnlocked ? Win95Skin.FieldText : Win95Skin.Face,
                19, TextAlignmentOptions.Left, isUnlocked ? FontStyles.Bold : FontStyles.Normal);
            QuestUIBuilder.Stretch(label.gameObject, Vector2.zero, Vector2.one);
            label.rectTransform.offsetMin = new Vector2(12f, 0f);
            label.rectTransform.offsetMax = new Vector2(-8f, 0f);
            label.raycastTarget = false;

            _cursorY += rowH + 6f;
        }

        // ── Detail pane ─────────────────────────────────────────────────────────────────

        private void ShowDetail(WikiEntryData entry)
        {
            if (entry == null) return;

            _dTitle.text = entry.Title;
            _dBody.text = string.IsNullOrEmpty(entry.Body) ? "(nothing written yet)" : entry.Body;

            bool hasImage = entry.Image != null;
            _bannerImage.sprite = entry.Image;
            _bannerImage.enabled = hasImage;
            _bannerPlaceholder.SetActive(!hasImage);

            if (_bodyScroll != null)
                _bodyScroll.verticalNormalizedPosition = 1f;
        }

        /// <summary>Opening state: the first unlocked entry, or a hint when the wiki is still empty.</summary>
        private void ShowFirstUnlockedOrHint()
        {
            foreach (WikiEntryData entry in WikiDatabase.All)
            {
                if (entry != null && IsUnlocked(entry))
                {
                    ShowDetail(entry);
                    return;
                }
            }

            _dTitle.text = "WIKIBRITAIN";
            _dBody.text = "Nothing in here yet. Get out there — new places and new people write new entries.";
            _bannerImage.enabled = false;
            _bannerPlaceholder.SetActive(true);
        }

        // ── Chrome ──────────────────────────────────────────────────────────────────────

        private void BuildUI()
        {
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "WikiBritainCanvas", 565);

            GameObject dim = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            QuestUIBuilder.Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);
            _root = dim;

            GameObject panel = QuestUIBuilder.CreateImage("WikiPanel", dim.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            var prt = panel.GetComponent<RectTransform>();
            // Near-fullscreen like the bag window — a thin screen margin on every side, so the
            // window fills a phone display instead of floating as a 980x800 box in the middle.
            // Interior panes are pinned by offsets, so they redistribute on their own.
            prt.anchorMin = new Vector2(0.01f, 0.02f);
            prt.anchorMax = new Vector2(0.99f, 0.98f);
            prt.offsetMin = Vector2.zero;
            prt.offsetMax = Vector2.zero;

            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, Win95Skin.TitleBar);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0f, 1f);
            hrt.anchorMax = Vector2.one;
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0f, 60f);

            var headerLabel = QuestUIBuilder.CreateTMP("HeaderLabel", header.transform, "WIKIBRITAIN",
                Win95Skin.TitleText, 28, TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(headerLabel.gameObject, Vector2.zero, Vector2.one);

            QuestUIBuilder.CreateCloseX(header.transform, Close);

            BuildListPane(panel.transform);
            BuildDetailPane(panel.transform);

            // Bottom strip: BACK to the bag on the left, unlock count on the right.
            GameObject back = QuestUIBuilder.CreateButton("BackButton", panel.transform, "BACK", Back);
            var brt = back.GetComponent<RectTransform>();
            brt.anchorMin = brt.anchorMax = new Vector2(0f, 0f);
            brt.pivot = new Vector2(0f, 0f);
            brt.anchoredPosition = new Vector2(16f, 12f);
            brt.sizeDelta = new Vector2(160f, 40f);

            _countText = QuestUIBuilder.CreateTMP("Count", panel.transform, "",
                new Color(0f, 0f, 0f, 0.65f), 16, TextAlignmentOptions.Right, FontStyles.Normal);
            var crt = _countText.rectTransform;
            crt.anchorMin = crt.anchorMax = new Vector2(1f, 0f);
            crt.pivot = new Vector2(1f, 0f);
            crt.anchoredPosition = new Vector2(-16f, 12f);
            crt.sizeDelta = new Vector2(240f, 40f);
            _countText.raycastTarget = false;

            _root.SetActive(false);
        }

        private void BuildListPane(Transform panel)
        {
            GameObject pane = QuestUIBuilder.CreateImage("ListPane", panel, Win95Skin.SlotFill);
            Win95Skin.AddBevel((RectTransform)pane.transform, sunken: true);
            var prt = pane.GetComponent<RectTransform>();
            prt.anchorMin = new Vector2(0f, 0f);
            prt.anchorMax = new Vector2(0f, 1f);
            prt.offsetMin = new Vector2(16f, 64f);
            prt.offsetMax = new Vector2(332f, -68f); // fixed 316 px wide on the left

            GameObject viewport = QuestUIBuilder.CreateImage("Viewport", pane.transform, new Color(0f, 0f, 0f, 0.08f));
            var vrt = viewport.GetComponent<RectTransform>();
            vrt.anchorMin = Vector2.zero;
            vrt.anchorMax = Vector2.one;
            vrt.offsetMin = new Vector2(8f, 8f);
            vrt.offsetMax = new Vector2(-8f, -8f);
            viewport.AddComponent<RectMask2D>();

            // Rows positioned by hand (the journal's hard-won lesson: no layout group in a mask).
            var contentGO = new GameObject("Content", typeof(RectTransform));
            contentGO.transform.SetParent(viewport.transform, false);
            _listContent = contentGO.GetComponent<RectTransform>();
            _listContent.anchorMin = new Vector2(0f, 1f);
            _listContent.anchorMax = new Vector2(1f, 1f);
            _listContent.pivot = new Vector2(0.5f, 1f);
            _listContent.anchoredPosition = Vector2.zero;
            _listContent.sizeDelta = Vector2.zero;
            _listContainer = contentGO.transform;

            _listScroll = pane.AddComponent<ScrollRect>();
            _listScroll.viewport = vrt;
            _listScroll.content = _listContent;
            _listScroll.horizontal = false;
            _listScroll.movementType = ScrollRect.MovementType.Clamped;
            _listScroll.scrollSensitivity = 28f;
        }

        private void BuildDetailPane(Transform panel)
        {
            GameObject pane = QuestUIBuilder.CreateImage("DetailPane", panel, Win95Skin.SlotFill);
            Win95Skin.AddBevel((RectTransform)pane.transform, sunken: true);
            var prt = pane.GetComponent<RectTransform>();
            prt.anchorMin = new Vector2(0f, 0f);
            prt.anchorMax = new Vector2(1f, 1f);
            prt.offsetMin = new Vector2(348f, 64f);
            prt.offsetMax = new Vector2(-16f, -68f);

            // Image banner across the top — a fixed slot, so the layout never jumps when art
            // arrives; until then the placeholder says so.
            GameObject banner = QuestUIBuilder.CreateImage("Banner", pane.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)banner.transform, sunken: true);
            var brt = banner.GetComponent<RectTransform>();
            brt.anchorMin = new Vector2(0f, 1f);
            brt.anchorMax = new Vector2(1f, 1f);
            brt.pivot = new Vector2(0.5f, 1f);
            brt.anchoredPosition = new Vector2(0f, -12f);
            brt.sizeDelta = new Vector2(-24f, 220f);
            banner.GetComponent<Image>().raycastTarget = false;

            var artGO = new GameObject("Art", typeof(RectTransform));
            artGO.transform.SetParent(banner.transform, false);
            _bannerImage = artGO.AddComponent<Image>();
            _bannerImage.preserveAspect = true;
            _bannerImage.raycastTarget = false;
            QuestUIBuilder.Stretch(artGO, Vector2.zero, Vector2.one);
            var art = (RectTransform)artGO.transform;
            art.offsetMin = new Vector2(4f, 4f);
            art.offsetMax = new Vector2(-4f, -4f);

            _bannerPlaceholder = QuestUIBuilder.CreateTMP("Placeholder", banner.transform, "NO IMAGE YET",
                new Color(0f, 0f, 0f, 0.45f), 20, TextAlignmentOptions.Center, FontStyles.Bold).gameObject;
            QuestUIBuilder.Stretch(_bannerPlaceholder, Vector2.zero, Vector2.one);

            _dTitle = QuestUIBuilder.CreateTMP("Title", pane.transform, "",
                Win95Skin.FieldText, 28, TextAlignmentOptions.Left, FontStyles.Bold);
            var trt = _dTitle.rectTransform;
            trt.anchorMin = new Vector2(0f, 1f);
            trt.anchorMax = new Vector2(1f, 1f);
            trt.pivot = new Vector2(0.5f, 1f);
            trt.anchoredPosition = new Vector2(0f, -244f);
            trt.sizeDelta = new Vector2(-28f, 44f);
            _dTitle.raycastTarget = false;

            // Body: a plain text scroll, long entries included. ContentSizeFitter on the text
            // itself — no layout group, per the journal's mask lesson.
            GameObject bodyView = QuestUIBuilder.CreateImage("BodyViewport", pane.transform, new Color(0f, 0f, 0f, 0.06f));
            var bvrt = bodyView.GetComponent<RectTransform>();
            bvrt.anchorMin = new Vector2(0f, 0f);
            bvrt.anchorMax = new Vector2(1f, 1f);
            bvrt.offsetMin = new Vector2(12f, 12f);
            bvrt.offsetMax = new Vector2(-12f, -300f);
            bodyView.AddComponent<RectMask2D>();

            var bodyGO = new GameObject("Body", typeof(RectTransform));
            bodyGO.transform.SetParent(bodyView.transform, false);
            var brt2 = bodyGO.GetComponent<RectTransform>();
            brt2.anchorMin = new Vector2(0f, 1f);
            brt2.anchorMax = new Vector2(1f, 1f);
            brt2.pivot = new Vector2(0.5f, 1f);
            brt2.anchoredPosition = Vector2.zero;
            brt2.sizeDelta = Vector2.zero;

            _dBody = bodyGO.AddComponent<TextMeshProUGUI>();
            _dBody.color = Win95Skin.FieldText;
            _dBody.fontSize = 20;
            _dBody.alignment = TextAlignmentOptions.TopLeft;
            _dBody.enableWordWrapping = true;
            _dBody.raycastTarget = false;

            var fitter = bodyGO.AddComponent<ContentSizeFitter>();
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            _bodyScroll = pane.AddComponent<ScrollRect>();
            _bodyScroll.viewport = bvrt;
            _bodyScroll.content = brt2;
            _bodyScroll.horizontal = false;
            _bodyScroll.movementType = ScrollRect.MovementType.Clamped;
            _bodyScroll.scrollSensitivity = 28f;
        }
    }
}
