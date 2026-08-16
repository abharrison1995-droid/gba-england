using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System;
using System.Collections.Generic;

namespace GBHEngland.UI
{
    /// <summary>One slot in the loot window.</summary>
    public class LootEntry
    {
        public string Name;
        public string Description;
        /// <summary>Optional item icon shown in the slot; slots without one show the name.</summary>
        public Sprite Icon;
        /// <summary>Runs once when the player takes this entry.</summary>
        public Action OnTaken;
        public bool Taken;
    }

    /// <summary>
    /// Win95 loot window for chests/corpses: navy title bar, sunken item slots in a small
    /// grid (same look as the bag, fewer slots). Entirely code-built at runtime on its own
    /// overlay canvas (no scene wiring needed). Pauses the game while open.
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
                BuildSlot(entry);

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
                var img = row.GetComponent<Image>();
                if (img != null) img.color = Win95Skin.Shadow;
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

            GameObject panel = CreateImage("LootPanel", dim.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(720, 620);
            // Swallow clicks so tapping the panel itself doesn't hit the dimmer's close button.
            panel.GetComponent<Image>().raycastTarget = true;

            GameObject header = CreateImage("Header", panel.transform, Win95Skin.TitleBar);
            Stretch(header, new Vector2(0, 1), Vector2.one);
            var hrt = header.GetComponent<RectTransform>();
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0, 52);

            _titleText = CreateTMP("Title", header.transform, "Loot", Win95Skin.TitleText, 24,
                TextAlignmentOptions.Left);
            Stretch(_titleText.gameObject, Vector2.zero, Vector2.one);
            _titleText.GetComponent<RectTransform>().offsetMin = new Vector2(16, 0);
            _titleText.fontStyle = FontStyles.Bold;

            QuestUIBuilder.CreateCloseX(header.transform, Close);

            // Scrollable sunken slot grid. Ordinary containers still fit without scrolling; the
            // test chest can hold the entire catalogue without rows escaping the window.
            GameObject viewport = CreateImage("SlotsViewport", panel.transform, Win95Skin.SlotFill);
            var vrt = viewport.GetComponent<RectTransform>();
            vrt.anchorMin = Vector2.zero;
            vrt.anchorMax = Vector2.one;
            vrt.offsetMin = new Vector2(20, 96);
            vrt.offsetMax = new Vector2(-20, -64);
            Win95Skin.AddBevel(vrt, sunken: true);
            var mask = viewport.AddComponent<Mask>();
            mask.showMaskGraphic = false;

            var containerGO = new GameObject("Slots", typeof(RectTransform));
            containerGO.transform.SetParent(viewport.transform, false);
            var crt = containerGO.GetComponent<RectTransform>();
            crt.anchorMin = new Vector2(0f, 1f);
            crt.anchorMax = new Vector2(1f, 1f);
            crt.pivot = new Vector2(0.5f, 1f);
            crt.anchoredPosition = Vector2.zero;
            crt.sizeDelta = Vector2.zero;
            var grid = containerGO.AddComponent<GridLayoutGroup>();
            grid.padding = new RectOffset(10, 10, 10, 10);
            grid.cellSize = new Vector2(152, 108);
            grid.spacing = new Vector2(10, 10);
            grid.startCorner = GridLayoutGroup.Corner.UpperLeft;
            grid.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
            grid.constraintCount = 4;
            grid.childAlignment = TextAnchor.UpperCenter;
            var fitter = containerGO.AddComponent<ContentSizeFitter>();
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            var scroll = viewport.AddComponent<ScrollRect>();
            scroll.viewport = vrt;
            scroll.content = crt;
            scroll.horizontal = false;
            scroll.vertical = true;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 45f;
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

        /// <summary>
        /// One lootable entry as a sunken slot: item icon when the entry carries one, the
        /// item name otherwise. Clicking the slot takes it — same Take()/OnTaken contract
        /// the row layout had, so chest/quest wiring is unchanged.
        /// </summary>
        private void BuildSlot(LootEntry entry)
        {
            GameObject slot = CreateImage("LootSlot", _rowContainer, Win95Skin.SlotFill);
            Win95Skin.AddBevel((RectTransform)slot.transform, sunken: true);

            var btn = slot.AddComponent<Button>();
            btn.onClick.AddListener(() => Take(entry, slot));

            if (entry.Icon != null)
            {
                // UI Image tint multiplies the sprite colour. Color.clear made every correctly
                // assigned item icon fully transparent, leaving only the name visible.
                GameObject icon = CreateImage("Icon", slot.transform, Color.white);
                Stretch(icon, new Vector2(0.08f, 0.30f), new Vector2(0.92f, 0.94f));
                var iconImg = icon.GetComponent<Image>();
                iconImg.sprite = entry.Icon;
                iconImg.preserveAspect = true;
                iconImg.raycastTarget = false;

                var name = CreateTMP("Name", slot.transform, entry.Name, Win95Skin.FieldText, 14,
                    TextAlignmentOptions.Center);
                Stretch(name.gameObject, Vector2.zero, new Vector2(1, 0.28f));
            }
            else
            {
                var name = CreateTMP("Name", slot.transform, entry.Name, Win95Skin.FieldText, 16,
                    TextAlignmentOptions.Center);
                Stretch(name.gameObject, Vector2.zero, Vector2.one);
                var nrt = name.GetComponent<RectTransform>();
                nrt.offsetMin = new Vector2(6, 4);
                nrt.offsetMax = new Vector2(-6, -4);
            }

            if (entry.Taken)
                MarkRowTaken(slot);
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
            GameObject go = CreateImage(name, parent, Win95Skin.Face);
            var btn = go.AddComponent<Button>();
            Win95Skin.StyleButton(btn);
            btn.onClick.AddListener(onClick);
            var tmp = CreateTMP("Label", go.transform, label, Win95Skin.FieldText, 22,
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
