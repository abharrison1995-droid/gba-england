using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Quests;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Center-screen "New Quest" popup. Shown automatically when QuestManager starts a
    /// brand-new quest; if a dialogue is open the popup waits until the chat ends.
    /// Dismiss via the X, clicking outside the box, or E on desktop; the Journal button
    /// opens the full quest log instead. Entirely code-built, pauses while open.
    /// </summary>
    public class QuestPopupUI : MonoBehaviour
    {
        private static QuestPopupUI _instance;
        private static readonly Queue<QuestProgress> _pending = new Queue<QuestProgress>();

        private GameObject _root;
        private TextMeshProUGUI _titleText;
        private TextMeshProUGUI _bodyText;

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        public static void Show(QuestProgress quest)
        {
            if (quest == null) return;

            // Mid-conversation grants wait for the dialogue panel to close. Queued (not a single
            // slot) so a conversation that grants more than one quest doesn't drop all but the last.
            if (Dialogue.DialogueManager.IsDialogueOpen || IsOpen)
            {
                _pending.Enqueue(quest);
                return;
            }

            if (_instance == null)
            {
                var go = new GameObject("QuestPopupUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<QuestPopupUI>();
                _instance.BuildUI();
            }
            _instance.Open(quest);
        }

        /// <summary>Called by DialogueManager when a conversation ends.</summary>
        public static void ShowPendingIfAny()
        {
            if (_pending.Count == 0) return;
            Show(_pending.Dequeue());
        }

        private void Open(QuestProgress quest)
        {
            if (IsOpen) return;
            _titleText.text = quest.Title;
            _bodyText.text = quest.Objective;
            _root.SetActive(true);
            Systems.PauseManager.Push();
        }

        private void Close()
        {
            CloseInternal();
            ShowPendingIfAny();
        }

        private void CloseInternal()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            Systems.PauseManager.Pop();
        }

        private void OpenJournal()
        {
            // Skip ShowPendingIfAny here — jumping straight to the full journal shouldn't pop
            // another quest notice on top of it; any queued one shows next time this popup closes.
            CloseInternal();
            QuestJournalUI.Open();
        }

        private void Update()
        {
#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            if (IsOpen && Input.GetKeyDown(KeyCode.E))
                Close();
#endif
        }

        private void BuildUI()
        {
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "QuestPopupCanvas", 550);

            GameObject dim = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.45f));
            QuestUIBuilder.Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);
            _root = dim;

            GameObject panel = QuestUIBuilder.CreateImage("QuestPopup", dim.transform, EKVibe.ParchmentPanel);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.55f);
            prt.sizeDelta = new Vector2(560, 320);

            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, EKVibe.ParchmentDark);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0, 1);
            hrt.anchorMax = Vector2.one;
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0, 52);

            var headerLabel = QuestUIBuilder.CreateTMP("HeaderLabel", header.transform, "NEW QUEST",
                EKVibe.XpBar, 24, TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(headerLabel.gameObject, Vector2.zero, Vector2.one);

            QuestUIBuilder.CreateCloseX(header.transform, Close);

            _titleText = QuestUIBuilder.CreateTMP("QuestTitle", panel.transform, "", EKVibe.TextDark, 30,
                TextAlignmentOptions.Center, FontStyles.Bold);
            var trt = _titleText.GetComponent<RectTransform>();
            trt.anchorMin = new Vector2(0, 1);
            trt.anchorMax = Vector2.one;
            trt.pivot = new Vector2(0.5f, 1f);
            trt.anchoredPosition = new Vector2(0, -64);
            trt.sizeDelta = new Vector2(-40, 40);

            _bodyText = QuestUIBuilder.CreateTMP("QuestBody", panel.transform, "", EKVibe.TextDark, 21,
                TextAlignmentOptions.Top, FontStyles.Normal);
            var brt = _bodyText.GetComponent<RectTransform>();
            brt.anchorMin = new Vector2(0, 0);
            brt.anchorMax = Vector2.one;
            brt.offsetMin = new Vector2(30, 78);
            brt.offsetMax = new Vector2(-30, -112);

            GameObject journalBtn = QuestUIBuilder.CreateButton("JournalButton", panel.transform, "JOURNAL", OpenJournal);
            var jrt = journalBtn.GetComponent<RectTransform>();
            jrt.anchorMin = jrt.anchorMax = new Vector2(0.5f, 0f);
            jrt.pivot = new Vector2(0.5f, 0f);
            jrt.anchoredPosition = new Vector2(0, 18);
            jrt.sizeDelta = new Vector2(220, 52);

            _root.SetActive(false);
        }
    }

    /// <summary>
    /// Full quest log: active quests with their current objective, then resolved quests.
    /// Same dismissal rules as the popup (X, click outside, E). Code-built, pauses while open.
    /// </summary>
    public class QuestJournalUI : MonoBehaviour
    {
        private static QuestJournalUI _instance;

        private GameObject _root;
        private Transform _listContainer;
        private GameObject _listView;      // the scrollable quest list
        private GameObject _detailView;    // single-quest detail page
        private ScrollRect _scroll;
        private RectTransform _content;    // rows are placed manually inside this
        private float _cursorY;            // running top-down offset while filling the list
        private TextMeshProUGUI _dTitle, _dStatus, _dGiver, _dLocation, _dNext;

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        /// <summary>HUD button / J hotkey: close if open, open if closed (unless something else has the game paused).</summary>
        public static void Toggle()
        {
            if (IsOpen)
            {
                _instance.Close();
                return;
            }
            // Don't stack on top of inventory/dialogue/loot — they own the pause right now
            if (Systems.PauseManager.IsPaused) return;
            Open();
        }

        public static void Open()
        {
            if (_instance == null)
            {
                var go = new GameObject("QuestJournalUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<QuestJournalUI>();
                _instance.BuildUI();
            }
            _instance.OpenInternal();
        }

        private void OpenInternal()
        {
            if (IsOpen) return;
            BackToList();            // always open on the list, not a stale detail page
            Populate();
            _root.SetActive(true);
            if (_scroll != null) _scroll.verticalNormalizedPosition = 1f; // scrolled to top
            Systems.PauseManager.Push();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            Systems.PauseManager.Pop();
        }

        private void Update()
        {
#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            if (IsOpen && Input.GetKeyDown(KeyCode.E))
                Close();
#endif
        }

        private void Populate()
        {
            foreach (Transform child in _listContainer)
                Destroy(child.gameObject);
            _cursorY = 8f;

            var mgr = QuestManager.Instance;
            if (mgr == null || mgr.Quests.Count == 0)
            {
                AddSectionLabel("No quests yet. Go poke your nose into something.");
                FinalizeContent();
                return;
            }

            bool anyActive = false, anyResolved = false;
            foreach (QuestProgress q in mgr.Quests)
            {
                if (q.IsActive && !q.IsComplete) anyActive = true;
                if (q.IsComplete) anyResolved = true;
            }

            if (anyActive)
            {
                AddSectionLabel("ACTIVE");
                foreach (QuestProgress q in mgr.Quests)
                    if (q.IsActive && !q.IsComplete)
                        AddQuestRow(q, resolved: false);
            }
            if (anyResolved)
            {
                AddSectionLabel("RESOLVED");
                foreach (QuestProgress q in mgr.Quests)
                    if (q.IsComplete)
                        AddQuestRow(q, resolved: true);
            }

            FinalizeContent();
        }

        /// <summary>Sets the content height to fit everything placed and resets the scroll to top.</summary>
        private void FinalizeContent()
        {
            if (_content != null)
                _content.sizeDelta = new Vector2(0, _cursorY + 4f);
            if (_scroll != null)
                _scroll.verticalNormalizedPosition = 1f;
        }

        private void AddSectionLabel(string text)
        {
            var tmp = QuestUIBuilder.CreateTMP("Section", _listContainer, text,
                EKVibe.ParchmentDark, 22, TextAlignmentOptions.BottomLeft, FontStyles.Bold);
            var rt = tmp.rectTransform;
            rt.anchorMin = new Vector2(0, 1);
            rt.anchorMax = new Vector2(1, 1);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.sizeDelta = new Vector2(-48, 34);           // 24px inset each side, aligns with row text
            rt.anchoredPosition = new Vector2(0, -_cursorY);
            tmp.raycastTarget = false;
            _cursorY += 34 + 10;
        }

        private void AddQuestRow(QuestProgress q, bool resolved)
        {
            const float rowH = 108f;
            GameObject row = QuestUIBuilder.CreateImage("QuestRow", _listContainer, EKVibe.SlotFrame);
            var rrt = row.GetComponent<RectTransform>();
            rrt.anchorMin = new Vector2(0, 1);
            rrt.anchorMax = new Vector2(1, 1);
            rrt.pivot = new Vector2(0.5f, 1f);
            rrt.sizeDelta = new Vector2(-16, rowH);        // 8px inset each side; full remaining width
            rrt.anchoredPosition = new Vector2(0, -_cursorY);

            // The whole row taps through to the detail page.
            row.AddComponent<Button>().onClick.AddListener(() => ShowDetail(q));

            Color titleColor = resolved
                ? new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.6f)
                : EKVibe.TextLight;

            var titleTmp = QuestUIBuilder.CreateTMP("Title", row.transform, q.Title, titleColor, 24,
                TextAlignmentOptions.TopLeft, resolved ? FontStyles.Strikethrough | FontStyles.Bold : FontStyles.Bold);
            QuestUIBuilder.Stretch(titleTmp.gameObject, Vector2.zero, Vector2.one);
            titleTmp.rectTransform.offsetMin = new Vector2(16, 66);
            titleTmp.rectTransform.offsetMax = new Vector2(-52, -6);
            titleTmp.raycastTarget = false;

            // Quest giver, right under the name.
            string giver = string.IsNullOrEmpty(q.Giver) ? "Unknown" : q.Giver;
            var giverTmp = QuestUIBuilder.CreateTMP("Giver", row.transform, "Given by " + giver,
                new Color(EKVibe.XpBar.r, EKVibe.XpBar.g, EKVibe.XpBar.b, 1f), 17,
                TextAlignmentOptions.TopLeft, FontStyles.Italic);
            QuestUIBuilder.Stretch(giverTmp.gameObject, Vector2.zero, Vector2.one);
            giverTmp.rectTransform.offsetMin = new Vector2(16, 38);
            giverTmp.rectTransform.offsetMax = new Vector2(-52, -46);
            giverTmp.raycastTarget = false;

            // One-line objective preview (full text lives on the detail page).
            var objTmp = QuestUIBuilder.CreateTMP("Objective", row.transform, resolved ? "Resolved." : q.Objective,
                new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.7f), 16,
                TextAlignmentOptions.TopLeft, FontStyles.Normal);
            QuestUIBuilder.Stretch(objTmp.gameObject, Vector2.zero, Vector2.one);
            objTmp.rectTransform.offsetMin = new Vector2(16, 8);
            objTmp.rectTransform.offsetMax = new Vector2(-52, -74);
            objTmp.enableWordWrapping = false;
            objTmp.overflowMode = TextOverflowModes.Ellipsis;
            objTmp.raycastTarget = false;

            // Tap-through chevron.
            var chev = QuestUIBuilder.CreateTMP("Chevron", row.transform, ">",
                new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.55f), 30,
                TextAlignmentOptions.Center, FontStyles.Bold);
            var crt = chev.rectTransform;
            crt.anchorMin = new Vector2(1, 0);
            crt.anchorMax = new Vector2(1, 1);
            crt.pivot = new Vector2(1, 0.5f);
            crt.sizeDelta = new Vector2(44, 0);
            crt.anchoredPosition = new Vector2(-6, 0);
            chev.raycastTarget = false;

            _cursorY += rowH + 10;
        }

        private void BuildUI()
        {
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "QuestJournalCanvas", 560);

            GameObject dim = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            QuestUIBuilder.Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);
            _root = dim;

            GameObject panel = QuestUIBuilder.CreateImage("JournalPanel", dim.transform, EKVibe.ParchmentPanel);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(980, 800);

            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, EKVibe.ParchmentDark);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0, 1);
            hrt.anchorMax = Vector2.one;
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0, 60);

            var headerLabel = QuestUIBuilder.CreateTMP("HeaderLabel", header.transform, "JOURNAL",
                EKVibe.TextLight, 28, TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(headerLabel.gameObject, Vector2.zero, Vector2.one);

            QuestUIBuilder.CreateCloseX(header.transform, Close);

            BuildListView(panel.transform);
            BuildDetailView(panel.transform);
            _detailView.SetActive(false);

            _root.SetActive(false);
        }

        /// <summary>The scrollable quest list (default view).</summary>
        private void BuildListView(Transform panel)
        {
            _listView = QuestUIBuilder.CreateImage("ListView", panel, new Color(0f, 0f, 0f, 0f));
            var lrt = _listView.GetComponent<RectTransform>();
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = new Vector2(0, -60); // sit below the header

            GameObject viewport = QuestUIBuilder.CreateImage("Viewport", _listView.transform, new Color(0, 0, 0, 0.08f));
            var vrt = viewport.GetComponent<RectTransform>();
            vrt.anchorMin = Vector2.zero;
            vrt.anchorMax = Vector2.one;
            vrt.offsetMin = new Vector2(24, 24);
            vrt.offsetMax = new Vector2(-24, -16);
            viewport.AddComponent<RectMask2D>();

            // Rows are positioned by hand (see AddQuestRow) rather than via a layout group —
            // the layout group was what shifted the rows off the left edge of the mask.
            var contentGO = new GameObject("Content", typeof(RectTransform));
            contentGO.transform.SetParent(viewport.transform, false);
            _content = contentGO.GetComponent<RectTransform>();
            _content.anchorMin = new Vector2(0, 1);
            _content.anchorMax = new Vector2(1, 1);
            _content.pivot = new Vector2(0.5f, 1f);
            _content.anchoredPosition = Vector2.zero;
            _content.sizeDelta = Vector2.zero;
            _listContainer = contentGO.transform;

            _scroll = _listView.AddComponent<ScrollRect>();
            _scroll.viewport = vrt;
            _scroll.content = _content;
            _scroll.horizontal = false;
            _scroll.movementType = ScrollRect.MovementType.Clamped;
            _scroll.scrollSensitivity = 28f;
        }

        /// <summary>Single-quest detail page: giver, location, next step. Shown on row tap.</summary>
        private void BuildDetailView(Transform panel)
        {
            _detailView = QuestUIBuilder.CreateImage("DetailView", panel, new Color(0f, 0f, 0f, 0f));
            var rt = _detailView.GetComponent<RectTransform>();
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = new Vector2(0, -60);

            _dTitle = Field(_detailView.transform, "", 30, FontStyles.Bold, TextAlignmentOptions.TopLeft,
                EKVibe.TextDark, new Vector2(0.05f, 0.86f), new Vector2(0.72f, 0.965f));
            _dTitle.enableWordWrapping = true;

            var statusBg = QuestUIBuilder.CreateImage("StatusPill", _detailView.transform, EKVibe.ParchmentDark);
            var srt = statusBg.GetComponent<RectTransform>();
            srt.anchorMin = new Vector2(0.72f, 0.885f);
            srt.anchorMax = new Vector2(0.95f, 0.955f);
            srt.offsetMin = Vector2.zero;
            srt.offsetMax = Vector2.zero;
            _dStatus = Field(statusBg.transform, "", 20, FontStyles.Bold, TextAlignmentOptions.Center,
                EKVibe.XpBar, Vector2.zero, Vector2.one);

            var div = QuestUIBuilder.CreateImage("Divider", _detailView.transform,
                new Color(EKVibe.TextDark.r, EKVibe.TextDark.g, EKVibe.TextDark.b, 0.25f));
            var drt = div.GetComponent<RectTransform>();
            drt.anchorMin = new Vector2(0.05f, 0.83f);
            drt.anchorMax = new Vector2(0.95f, 0.837f);
            drt.offsetMin = Vector2.zero;
            drt.offsetMax = Vector2.zero;

            Color labelC = new Color(EKVibe.TextDark.r, EKVibe.TextDark.g, EKVibe.TextDark.b, 0.6f);

            Field(_detailView.transform, "QUEST GIVER", 16, FontStyles.Bold, TextAlignmentOptions.TopLeft, labelC,
                new Vector2(0.05f, 0.74f), new Vector2(0.6f, 0.80f));
            _dGiver = Field(_detailView.transform, "", 24, FontStyles.Normal, TextAlignmentOptions.TopLeft,
                EKVibe.TextDark, new Vector2(0.05f, 0.67f), new Vector2(0.95f, 0.745f));

            Field(_detailView.transform, "LOCATION", 16, FontStyles.Bold, TextAlignmentOptions.TopLeft, labelC,
                new Vector2(0.05f, 0.58f), new Vector2(0.6f, 0.64f));
            _dLocation = Field(_detailView.transform, "", 24, FontStyles.Normal, TextAlignmentOptions.TopLeft,
                EKVibe.TextDark, new Vector2(0.05f, 0.51f), new Vector2(0.95f, 0.585f));

            Field(_detailView.transform, "NEXT STEP", 16, FontStyles.Bold, TextAlignmentOptions.TopLeft, labelC,
                new Vector2(0.05f, 0.42f), new Vector2(0.6f, 0.48f));
            _dNext = Field(_detailView.transform, "", 21, FontStyles.Normal, TextAlignmentOptions.TopLeft,
                EKVibe.TextDark, new Vector2(0.05f, 0.15f), new Vector2(0.95f, 0.42f));
            _dNext.enableWordWrapping = true;

            var back = QuestUIBuilder.CreateButton("BackButton", _detailView.transform, "BACK", BackToList);
            var brt = back.GetComponent<RectTransform>();
            brt.anchorMin = new Vector2(0.34f, 0.04f);
            brt.anchorMax = new Vector2(0.66f, 0.12f);
            brt.offsetMin = Vector2.zero;
            brt.offsetMax = Vector2.zero;
        }

        private static TextMeshProUGUI Field(Transform parent, string txt, float size, FontStyles style,
            TextAlignmentOptions align, Color color, Vector2 aMin, Vector2 aMax)
        {
            var tmp = QuestUIBuilder.CreateTMP("Field", parent, txt, color, size, align, style);
            var rt = tmp.rectTransform;
            rt.anchorMin = aMin;
            rt.anchorMax = aMax;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            tmp.raycastTarget = false;
            return tmp;
        }

        private void ShowDetail(QuestProgress q)
        {
            if (q == null || _detailView == null) return;

            bool resolved = q.IsComplete;
            _dTitle.text = q.Title;
            _dTitle.fontStyle = resolved ? FontStyles.Bold | FontStyles.Strikethrough : FontStyles.Bold;
            _dStatus.text = resolved ? "RESOLVED" : "ACTIVE";
            _dStatus.color = resolved
                ? new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.7f)
                : EKVibe.XpBar;
            _dGiver.text = string.IsNullOrEmpty(q.Giver) ? "Unknown" : q.Giver;
            _dLocation.text = string.IsNullOrEmpty(q.Location) ? "Unknown" : q.Location;
            _dNext.text = resolved
                ? "This quest is complete."
                : (string.IsNullOrEmpty(q.Objective) ? "No current objective." : q.Objective);

            if (_listView != null) _listView.SetActive(false);
            _detailView.SetActive(true);
        }

        private void BackToList()
        {
            if (_detailView != null) _detailView.SetActive(false);
            if (_listView != null) _listView.SetActive(true);
        }
    }

    /// <summary>Shared UI construction helpers for the quest popup + journal.</summary>
    internal static class QuestUIBuilder
    {
        public static GameObject CreateCanvas(Transform parent, string name, int sortingOrder)
        {
            var canvasGO = new GameObject(name);
            canvasGO.transform.SetParent(parent, false);
            var canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = sortingOrder;
            var scaler = canvasGO.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            canvasGO.AddComponent<GraphicRaycaster>();
            return canvasGO;
        }

        public static void CreateCloseX(Transform header, UnityEngine.Events.UnityAction onClick)
        {
            GameObject x = CreateImage("CloseButton", header, EKVibe.ButtonBrown);
            var xrt = x.GetComponent<RectTransform>();
            xrt.anchorMin = xrt.anchorMax = new Vector2(1f, 0.5f);
            xrt.pivot = new Vector2(1f, 0.5f);
            xrt.anchoredPosition = new Vector2(-8, 0);
            xrt.sizeDelta = new Vector2(40, 40);
            x.AddComponent<Button>().onClick.AddListener(onClick);
            var label = CreateTMP("X", x.transform, "X", EKVibe.TextLight, 22,
                TextAlignmentOptions.Center, FontStyles.Bold);
            Stretch(label.gameObject, Vector2.zero, Vector2.one);
        }

        public static GameObject CreateButton(string name, Transform parent, string label, UnityEngine.Events.UnityAction onClick)
        {
            GameObject go = CreateImage(name, parent, EKVibe.ButtonBrown);
            go.AddComponent<Button>().onClick.AddListener(onClick);
            var tmp = CreateTMP("Label", go.transform, label, EKVibe.TextLight, 22,
                TextAlignmentOptions.Center, FontStyles.Bold);
            Stretch(tmp.gameObject, Vector2.zero, Vector2.one);
            return go;
        }

        public static GameObject CreateImage(string name, Transform parent, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = color;
            return go;
        }

        public static TextMeshProUGUI CreateTMP(string name, Transform parent, string text,
            Color color, float size, TextAlignmentOptions align, FontStyles style)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.color = color;
            tmp.fontSize = size;
            tmp.alignment = align;
            tmp.fontStyle = style;
            tmp.raycastTarget = false;
            return tmp;
        }

        public static void Stretch(GameObject go, Vector2 anchorMin, Vector2 anchorMax)
        {
            var rt = go.GetComponent<RectTransform>();
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }
    }
}
