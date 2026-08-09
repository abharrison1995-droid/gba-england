using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Win95 chrome: flat greys, 2 px bevel edges, navy title bar.
    /// Built from pure uGUI primitives — no sprite assets. Shared by the scene rebuild tools
    /// (Editor/InventoryWin95Builder, TitleScreenWin95Builder, CharacterCreatorWin95Builder)
    /// and the buttons built at runtime, so every window draws the same skin.
    ///
    /// EKVibe keeps the parchment palette for the rest of the game; this skin covers the
    /// inventory, title screen and character creator windows.
    /// </summary>
    public static class Win95Skin
    {
        public static readonly Color Face = Hex("C0C0C0");
        public static readonly Color FacePressed = Hex("A8A8A8");
        public static readonly Color Highlight = Color.white;
        public static readonly Color Shadow = Hex("808080");
        public static readonly Color TitleBar = Hex("000080");
        public static readonly Color TitleText = Color.white;
        public static readonly Color SlotFill = Hex("9C9C9C");
        public static readonly Color HeaderYellow = Hex("FFF100");
        public static readonly Color FieldText = Color.black;
        public static readonly Color NameBox = Color.black;

        public const float BevelWidth = 2f;

        private static Color Hex(string h)
        {
            ColorUtility.TryParseHtmlString("#" + h, out Color c);
            return c;
        }

        /// <summary>Window face: grey fill with a raised outer bevel.</summary>
        public static void StyleWindow(Image img)
        {
            if (img == null) return;
            img.color = Face;
            AddBevel((RectTransform)img.transform, sunken: false);
        }

        /// <summary>Recessed field: mid-grey fill, bevel flipped so it reads as carved in.</summary>
        public static void StyleSunken(Image img)
        {
            if (img == null) return;
            img.color = SlotFill;
            AddBevel((RectTransform)img.transform, sunken: true);
        }

        /// <summary>
        /// Navy title bar across the top of a window: white bold caption on the left, inert
        /// min/max/close buttons on the right (window management does not exist — they are
        /// chrome only, matching the inventory bar). Idempotent — children are found by name
        /// on re-run. Sits inside the window's raised bevel, so call StyleWindow first.
        /// Returns the bar so callers can hang extra chrome off it.
        /// </summary>
        public static RectTransform AddTitleBar(RectTransform window, string caption, float barHeight = 30f)
        {
            if (window == null) return null;

            Transform existing = window.Find("TitleBar");
            RectTransform bar;
            if (existing != null)
            {
                bar = (RectTransform)existing;
            }
            else
            {
                var go = new GameObject("TitleBar", typeof(RectTransform));
                bar = (RectTransform)go.transform;
                bar.SetParent(window, false);
            }

            bar.anchorMin = new Vector2(0f, 1f);
            bar.anchorMax = new Vector2(1f, 1f);
            bar.pivot = new Vector2(0.5f, 1f);
            bar.offsetMin = new Vector2(3f, -barHeight - 3f);
            bar.offsetMax = new Vector2(-3f, -3f);

            Image barImg = bar.GetComponent<Image>();
            if (barImg == null) barImg = bar.gameObject.AddComponent<Image>();
            barImg.color = TitleBar;
            barImg.raycastTarget = false;

            TextMeshProUGUI title = FindOrCreateTmp(bar, "TitleText");
            title.text = caption;
            title.color = TitleText;
            title.fontStyle = FontStyles.Bold;
            title.alignment = TextAlignmentOptions.Left;
            title.raycastTarget = false;
            RectTransform titleRt = (RectTransform)title.transform;
            titleRt.anchorMin = Vector2.zero;
            titleRt.anchorMax = Vector2.one;
            titleRt.offsetMin = new Vector2(10f, 0f);
            titleRt.offsetMax = new Vector2(-130f, 0f);

            TitleButton(bar, "CloseButton", "X", -6f, barHeight);
            TitleButton(bar, "TitleMaxButton", "[]", -46f, barHeight);
            TitleButton(bar, "TitleMinButton", "_", -86f, barHeight);
            return bar;
        }

        /// <summary>Small raised grey square on the title bar. No listener — decoration only.</summary>
        private static void TitleButton(RectTransform bar, string name, string glyph, float rightOffset, float barHeight)
        {
            Transform existing = bar.Find(name);
            RectTransform rt;
            Button btn;
            if (existing != null)
            {
                rt = (RectTransform)existing;
                btn = rt.GetComponent<Button>();
            }
            else
            {
                var go = new GameObject(name, typeof(RectTransform));
                rt = (RectTransform)go.transform;
                rt.SetParent(bar, false);
                go.AddComponent<Image>();
                btn = go.AddComponent<Button>();
            }

            rt.anchorMin = rt.anchorMax = new Vector2(1f, 0.5f);
            rt.pivot = new Vector2(1f, 0.5f);
            rt.sizeDelta = new Vector2(34f, Mathf.Max(18f, barHeight - 8f));
            rt.anchoredPosition = new Vector2(rightOffset, 0f);

            TextMeshProUGUI label = FindOrCreateTmp(rt, "Label");
            label.text = glyph;
            label.alignment = TextAlignmentOptions.Center;
            RectTransform labelRt = (RectTransform)label.transform;
            labelRt.anchorMin = Vector2.zero;
            labelRt.anchorMax = Vector2.one;
            labelRt.offsetMin = Vector2.zero;
            labelRt.offsetMax = Vector2.zero;

            StyleButtonWithLabel(btn);
        }

        private static TextMeshProUGUI FindOrCreateTmp(Transform parent, string name)
        {
            Transform existing = parent.Find(name);
            GameObject go;
            if (existing != null)
            {
                go = existing.gameObject;
            }
            else
            {
                go = new GameObject(name, typeof(RectTransform));
                go.transform.SetParent(parent, false);
            }

            TextMeshProUGUI tmp = go.GetComponent<TextMeshProUGUI>();
            if (tmp == null) tmp = go.AddComponent<TextMeshProUGUI>();
            return tmp;
        }

        /// <summary>
        /// Solid colored frame of uniform width on all four edges — the mock's per-slot outline
        /// colors on the paper doll. Stacked on top of any bevel; centre stays untouched.
        /// </summary>
        public static void AddColorFrame(RectTransform rt, Color color, float width = 5f)
        {
            if (rt == null) return;
            Edge(rt, "FrameTop", color,
                new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0f, -width), Vector2.zero);
            Edge(rt, "FrameBottom", color,
                Vector2.zero, new Vector2(1f, 0f), Vector2.zero, new Vector2(0f, width));
            Edge(rt, "FrameLeft", color,
                Vector2.zero, new Vector2(0f, 1f), Vector2.zero, new Vector2(width, 0f));
            Edge(rt, "FrameRight", color,
                new Vector2(1f, 0f), Vector2.one, new Vector2(-width, 0f), Vector2.zero);
        }

        /// <summary>Raised grey push button. Text is styled separately with StyleLabel.</summary>
        public static void StyleButton(Button btn)
        {
            if (btn == null) return;

            Image img = btn.GetComponent<Image>();
            if (img != null) img.color = Face;

            btn.transition = Selectable.Transition.ColorTint;
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = Color.white;
            cb.pressedColor = new Color(0.82f, 0.82f, 0.82f, 1f);
            cb.selectedColor = Color.white;
            cb.disabledColor = new Color(1f, 1f, 1f, 0.5f);
            cb.colorMultiplier = 1f;
            btn.colors = cb;

            AddBevel((RectTransform)btn.transform, sunken: false);
        }

        /// <summary>Black label for grey Win95 surfaces; never eats raycasts meant for its button.</summary>
        public static void StyleLabel(TextMeshProUGUI tmp)
        {
            if (tmp == null) return;
            tmp.color = FieldText;
            tmp.raycastTarget = false;
        }

        /// <summary>StyleButton plus a styled child TMP label, if the button has one. Null-safe.</summary>
        public static void StyleButtonWithLabel(Button btn)
        {
            if (btn == null) return;
            StyleButton(btn);
            var label = btn.GetComponentInChildren<TextMeshProUGUI>(true);
            StyleLabel(label);
        }

        /// <summary>
        /// Four 2 px edge strips faking the classic bevel: light top/left and dark bottom/right
        /// when raised, flipped when sunken. Idempotent — strips are found by name on re-run.
        /// </summary>
        public static void AddBevel(RectTransform rt, bool sunken)
        {
            if (rt == null) return;

            Color topLeft = sunken ? Shadow : Highlight;
            Color bottomRight = sunken ? Highlight : Shadow;

            Edge(rt, "BevelTop", topLeft,
                new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(0f, -BevelWidth), Vector2.zero);
            Edge(rt, "BevelBottom", bottomRight,
                Vector2.zero, new Vector2(1f, 0f), Vector2.zero, new Vector2(0f, BevelWidth));
            Edge(rt, "BevelLeft", topLeft,
                Vector2.zero, new Vector2(0f, 1f), Vector2.zero, new Vector2(BevelWidth, 0f));
            Edge(rt, "BevelRight", bottomRight,
                new Vector2(1f, 0f), Vector2.one, new Vector2(-BevelWidth, 0f), Vector2.zero);
        }

        private static void Edge(RectTransform parent, string name, Color color,
            Vector2 anchorMin, Vector2 anchorMax, Vector2 offsetMin, Vector2 offsetMax)
        {
            Transform existing = parent.Find(name);
            GameObject go;
            if (existing != null)
            {
                go = existing.gameObject;
            }
            else
            {
                go = new GameObject(name, typeof(RectTransform));
                go.transform.SetParent(parent, false);
            }

            var rt = (RectTransform)go.transform;
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = offsetMin;
            rt.offsetMax = offsetMax;

            Image img = go.GetComponent<Image>();
            if (img == null) img = go.AddComponent<Image>();
            img.color = color;
            img.raycastTarget = false;
        }
    }
}
