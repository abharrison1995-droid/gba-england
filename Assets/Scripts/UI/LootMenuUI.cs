using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System;
using System.Collections.Generic;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>One row in the loot menu.</summary>
    public class LootEntry
    {
        public string Name;
        public string Description;
        /// <summary>Runs once when the player presses TAKE on this entry.</summary>
        public Action OnTaken;
        public bool Taken;
    }

    /// <summary>
    /// Parchment-style loot window for chests/corpses. Entirely code-built at runtime on
    /// its own overlay canvas (no scene wiring needed). Pauses the game while open.
    /// Usage: LootMenuUI.Show("Supply Chest", entries, onClosed).
    /// </summary>
    public class LootMenuUI : MonoBehaviour
    {
        private static LootMenuUI _instance;

        private GameObject _panelRoot;
        private TextMeshProUGUI _titleText;
        private Transform _rowContainer;
        private Action _onClosed;
        private List<LootEntry> _entries;

        public static bool IsOpen => _instance != null && _instance._panelRoot != null
                                     && _instance._panelRoot.activeSelf;

        public static void Show(string title, List<LootEntry> entries, Action onClosed = null)
        {
            if (_instance == null)
            {
                var go = new GameObject("LootMenuUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<LootMenuUI>();
                _instance.BuildUI();
            }
            _instance.Open(title, entries, onClosed);
        }

        private void Open(string title, List<LootEntry> entries, Action onClosed)
        {
            if (IsOpen) return;

            _entries = entries ?? new List<LootEntry>();
            _onClosed = onClosed;
            _titleText.text = title;

            foreach (Transform child in _rowContainer)
                Destroy(child.gameObject);
            foreach (LootEntry entry in _entries)
                BuildRow(entry);

            _panelRoot.SetActive(true);
            Systems.PauseManager.Push();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _panelRoot.SetActive(false);
            Systems.PauseManager.Pop();

            Action cb = _onClosed;
            _onClosed = null;
            cb?.Invoke();
        }

        private void TakeAll()
        {
            if (_entries == null) return;
            foreach (LootEntry entry in _entries)
                Take(entry, null);
            RefreshRows();
        }

        private static void Take(LootEntry entry, GameObject row)
        {
            if (entry == null || entry.Taken) return;
            entry.Taken = true;
            entry.OnTaken?.Invoke();
            if (row != null)
                MarkRowTaken(row);
        }

        private void RefreshRows()
        {
            foreach (Transform child in _rowContainer)
                MarkRowTaken(child.gameObject);
        }

        private static void MarkRowTaken(GameObject row)
        {
            var btn = row.GetComponentInChildren<Button>(true);
            if (btn != null && btn.interactable)
            {
                btn.interactable = false;
                var label = btn.GetComponentInChildren<TextMeshProUGUI>();
                if (label != null) label.text = "TAKEN";
                var img = btn.GetComponent<Image>();
                if (img != null) img.color = EKVibe.SlotEmpty;
            }
        }

        // ---------- one-time UI construction ----------

        private void BuildUI()
        {
            var canvasGO = new GameObject("LootCanvas");
            canvasGO.transform.SetParent(transform, false);
            var canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 500;
            var scaler = canvasGO.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            canvasGO.AddComponent<GraphicRaycaster>();

            // Dim the world behind the window; clicking the dimmer closes the menu.
            GameObject dim = CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);

            _panelRoot = dim;

            GameObject panel = CreateImage("LootPanel", dim.transform, EKVibe.ParchmentPanel);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(640, 480);
            // Swallow clicks so tapping the panel itself doesn't hit the dimmer's close button.
            panel.GetComponent<Image>().raycastTarget = true;

            GameObject header = CreateImage("Header", panel.transform, EKVibe.ParchmentDark);
            Stretch(header, new Vector2(0, 1), Vector2.one);
            var hrt = header.GetComponent<RectTransform>();
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0, 64);

            _titleText = CreateTMP("Title", header.transform, "Loot", EKVibe.TextLight, 30,
                TextAlignmentOptions.Center);
            Stretch(_titleText.gameObject, Vector2.zero, Vector2.one);

            var containerGO = new GameObject("Rows", typeof(RectTransform));
            containerGO.transform.SetParent(panel.transform, false);
            var crt = containerGO.GetComponent<RectTransform>();
            crt.anchorMin = new Vector2(0, 0);
            crt.anchorMax = new Vector2(1, 1);
            crt.offsetMin = new Vector2(20, 90);
            crt.offsetMax = new Vector2(-20, -74);
            var layout = containerGO.AddComponent<VerticalLayoutGroup>();
            layout.spacing = 10;
            layout.childControlHeight = false;
            layout.childControlWidth = true;
            layout.childForceExpandHeight = false;
            layout.childAlignment = TextAnchor.UpperCenter;
            _rowContainer = containerGO.transform;

            GameObject takeAllBtn = CreateButton("TakeAllButton", panel.transform, "TAKE ALL", TakeAll);
            var tart = takeAllBtn.GetComponent<RectTransform>();
            tart.anchorMin = tart.anchorMax = new Vector2(0.28f, 0f);
            tart.pivot = new Vector2(0.5f, 0f);
            tart.anchoredPosition = new Vector2(0, 16);
            tart.sizeDelta = new Vector2(240, 60);

            GameObject closeBtn = CreateButton("CloseButton", panel.transform, "CLOSE", Close);
            var clrt = closeBtn.GetComponent<RectTransform>();
            clrt.anchorMin = clrt.anchorMax = new Vector2(0.72f, 0f);
            clrt.pivot = new Vector2(0.5f, 0f);
            clrt.anchoredPosition = new Vector2(0, 16);
            clrt.sizeDelta = new Vector2(240, 60);

            _panelRoot.SetActive(false);
        }

        private void BuildRow(LootEntry entry)
        {
            GameObject row = CreateImage("LootRow", _rowContainer, EKVibe.SlotFrame);
            var rrt = row.GetComponent<RectTransform>();
            rrt.sizeDelta = new Vector2(0, 84);

            var name = CreateTMP("Name", row.transform, entry.Name, EKVibe.TextLight, 24,
                TextAlignmentOptions.TopLeft);
            Stretch(name.gameObject, Vector2.zero, Vector2.one);
            var nrt = name.GetComponent<RectTransform>();
            nrt.offsetMin = new Vector2(16, 8);
            nrt.offsetMax = new Vector2(-160, -10);

            var desc = CreateTMP("Desc", row.transform, entry.Description,
                new Color(EKVibe.TextLight.r, EKVibe.TextLight.g, EKVibe.TextLight.b, 0.75f), 17,
                TextAlignmentOptions.BottomLeft);
            Stretch(desc.gameObject, Vector2.zero, Vector2.one);
            var drt = desc.GetComponent<RectTransform>();
            drt.offsetMin = new Vector2(16, 8);
            drt.offsetMax = new Vector2(-160, -38);

            GameObject take = CreateButton("TakeButton", row.transform, "TAKE",
                () => Take(entry, row));
            var trt = take.GetComponent<RectTransform>();
            trt.anchorMin = new Vector2(1, 0.5f);
            trt.anchorMax = new Vector2(1, 0.5f);
            trt.pivot = new Vector2(1, 0.5f);
            trt.anchoredPosition = new Vector2(-12, 0);
            trt.sizeDelta = new Vector2(130, 56);

            if (entry.Taken)
                MarkRowTaken(row);
        }

        // ---------- tiny builders ----------

        private static GameObject CreateImage(string name, Transform parent, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = color;
            return go;
        }

        private static GameObject CreateButton(string name, Transform parent, string label, UnityEngine.Events.UnityAction onClick)
        {
            GameObject go = CreateImage(name, parent, EKVibe.ButtonBrown);
            var btn = go.AddComponent<Button>();
            btn.onClick.AddListener(onClick);
            var tmp = CreateTMP("Label", go.transform, label, EKVibe.TextLight, 22,
                TextAlignmentOptions.Center);
            Stretch(tmp.gameObject, Vector2.zero, Vector2.one);
            return go;
        }

        private static TextMeshProUGUI CreateTMP(string name, Transform parent, string text,
            Color color, float size, TextAlignmentOptions align)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.color = color;
            tmp.fontSize = size;
            tmp.alignment = align;
            tmp.raycastTarget = false;
            return tmp;
        }

        private static void Stretch(GameObject go, Vector2 anchorMin, Vector2 anchorMax)
        {
            var rt = go.GetComponent<RectTransform>();
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }
    }
}
