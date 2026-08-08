using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Win95 chrome for the inventory window: flat greys, 2 px bevel edges, navy title bar.
    /// Built from pure uGUI primitives — no sprite assets. Shared by the scene rebuild tool
    /// (Editor/InventoryWin95Builder) and the buttons InventoryController builds at runtime,
    /// so both draw the same skin.
    ///
    /// EKVibe keeps the parchment palette for the rest of the game; this skin is scoped to
    /// the inventory panel only.
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
