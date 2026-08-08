using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.EditorTools
{
    /// <summary>
    /// Restyles the scene-authored inventory panel (InventoryOverlay in Assets/c.unity) to the
    /// Win95 mock: navy title bar with min/max/close, grey bevelled panels, black name box,
    /// yellow tooltip header, right-hand QUEST JOURNAL / SPELLS / WIKIBRITAIN rail.
    ///
    /// Works IN PLACE: no GameObject the InventoryController references is destroyed, so every
    /// serialized fileID (TooltipPanel, BackpackGridContainer, BagSlot0..19, ...) survives.
    /// Re-runnable — everything is find-or-create by name, Undo is registered for the whole
    /// hierarchy, and the scene is only marked dirty; the human reviews and saves.
    ///
    /// Placeholder buttons (DROP, EQUIP, MAP OF BRITAIN, WIKIBRITAIN, title min/max) are
    /// created visible-but-inert; runtime systems for them do not exist yet.
    /// </summary>
    public static class InventoryWin95Builder
    {
        [MenuItem("Tools/GBH/UI/Rebuild Inventory Panel (Win95)")]
        public static void Rebuild()
        {
            InventoryController controller = FindController();
            if (controller == null || controller.InventoryUIPanel == null)
            {
                EditorUtility.DisplayDialog("Rebuild Inventory Panel",
                    "Could not find an InventoryController with an InventoryUIPanel in the active scene.\n\n" +
                    "Open Assets/c.unity and try again.", "OK");
                return;
            }

            GameObject overlay = controller.InventoryUIPanel;
            Undo.RegisterFullObjectHierarchyUndo(overlay, "Rebuild Inventory Panel (Win95)");

            Transform root = overlay.transform;
            RectTransform leftStats = (RectTransform)root.Find("LeftStats");
            RectTransform center = (RectTransform)root.Find("CenterPaperDoll");
            RectTransform tooltip = (RectTransform)root.Find("ItemTooltip");
            RectTransform backpack = (RectTransform)root.Find("RightBackpack");
            if (leftStats == null || center == null || tooltip == null || backpack == null)
            {
                EditorUtility.DisplayDialog("Rebuild Inventory Panel",
                    "InventoryOverlay is missing one of LeftStats / CenterPaperDoll / ItemTooltip / RightBackpack.\n" +
                    "Aborting without changes beyond the undo snapshot.", "OK");
                return;
            }

            StyleRoot(root);
            BuildTitleBar(root);
            StyleLeftStats(leftStats);
            StyleCenter(center);
            BindPaperDollContainer(controller, center);
            StyleTooltip(tooltip);
            StyleBackpack(backpack);
            BuildRail(root, leftStats, controller);
            StyleBottom(root);

            EditorSceneManager.MarkSceneDirty(overlay.scene);
            Selection.activeGameObject = overlay;
            EditorUtility.DisplayDialog("Rebuild Inventory Panel",
                "Inventory panel restyled to the Win95 layout.\n\n" +
                "Open the bag in Play mode (or toggle InventoryOverlay active) to review, then save the scene.\n" +
                "Undo (Ctrl+Z) reverts the whole rebuild before saving.", "OK");
            Debug.Log("InventoryWin95Builder: rebuild complete; scene marked dirty. Review and save.");
        }

        private static InventoryController FindController()
        {
            // FindObjectsOfType(Type, true) reaches the inactive UI canvas; the bag starts closed.
            foreach (Object o in Object.FindObjectsOfType(typeof(InventoryController), true))
            {
                var c = (InventoryController)o;
                if (c.InventoryUIPanel != null)
                    return c;
            }
            return null;
        }

        // ── Root window ──────────────────────────────────────────────────────────────────

        private static void StyleRoot(Transform root)
        {
            Image img = root.GetComponent<Image>();
            Win95Skin.StyleWindow(img);
        }

        private static void BuildTitleBar(Transform root)
        {
            RectTransform bar = FindOrCreate(root, "TitleBar");
            SetAnchors(bar, 0.004f, 0.955f, 0.996f, 1f);
            Image barImg = bar.GetComponent<Image>();
            if (barImg == null) barImg = bar.gameObject.AddComponent<Image>();
            barImg.color = Win95Skin.TitleBar;

            TextMeshProUGUI title = FindOrCreateTmp(bar, "TitleText");
            title.text = "Inventory";
            title.color = Win95Skin.TitleText;
            title.fontSize = 20;
            title.fontStyle = FontStyles.Bold;
            title.alignment = TextAlignmentOptions.Left;
            title.raycastTarget = false;
            RectTransform titleRt = (RectTransform)title.transform;
            titleRt.anchorMin = Vector2.zero;
            titleRt.anchorMax = Vector2.one;
            titleRt.offsetMin = new Vector2(10f, 0f);
            titleRt.offsetMax = new Vector2(-120f, 0f);

            // Close is wired at runtime (InventoryController.Awake finds "TitleBar/CloseButton").
            // Min/max are placeholders — window management does not exist.
            BuildTitleButton(bar, "CloseButton", "X", -6f);
            BuildTitleButton(bar, "TitleMaxButton", "[]", -46f);
            BuildTitleButton(bar, "TitleMinButton", "_", -86f);
        }

        private static void BuildTitleButton(RectTransform bar, string name, string glyph, float rightOffset)
        {
            Button btn = FindOrCreateButton(bar, name, glyph, 16);
            var rt = (RectTransform)btn.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(1f, 0.5f);
            rt.pivot = new Vector2(1f, 0.5f);
            rt.sizeDelta = new Vector2(34f, 24f);
            rt.anchoredPosition = new Vector2(rightOffset, 0f);
        }

        // ── Left column ─────────────────────────────────────────────────────────────────

        private static void StyleLeftStats(RectTransform leftStats)
        {
            SetAnchors(leftStats, 0.006f, 0.006f, 0.28f, 0.948f);
            Image panel = leftStats.GetComponent<Image>();
            Win95Skin.StyleWindow(panel);

            // Black name box: reparent the existing CharName TMP under it (fileID untouched).
            RectTransform nameBox = FindOrCreate(leftStats, "NameBox");
            SetAnchors(nameBox, 0.06f, 0.90f, 0.94f, 0.97f);
            Image boxImg = nameBox.GetComponent<Image>();
            if (boxImg == null) boxImg = nameBox.gameObject.AddComponent<Image>();
            boxImg.color = Win95Skin.NameBox;

            Transform charName = leftStats.Find("CharName");
            if (charName != null && charName.parent != nameBox)
                charName.SetParent(nameBox, false);
            if (charName != null)
            {
                var cnRt = (RectTransform)charName;
                cnRt.anchorMin = Vector2.zero;
                cnRt.anchorMax = Vector2.one;
                cnRt.offsetMin = new Vector2(6f, 2f);
                cnRt.offsetMax = new Vector2(-6f, -2f);
                var cn = charName.GetComponent<TextMeshProUGUI>();
                if (cn != null)
                {
                    cn.color = Color.white;
                    cn.alignment = TextAlignmentOptions.Center;
                }
            }

            // Level / XP readout — static labels for now; no XP system feeds them yet.
            TextMeshProUGUI level = FindOrCreateTmp(leftStats, "LevelXpText");
            level.text = "Player level:\n\nCurrent XP:\n\nXP to next level:";
            Win95Skin.StyleLabel(level);
            level.fontSize = 18;
            level.alignment = TextAlignmentOptions.TopLeft;
            SetAnchors((RectTransform)level.transform, 0.08f, 0.66f, 0.92f, 0.88f);

            RestyleText(leftStats, "Traits", 0.08f, 0.40f, 0.92f, 0.64f);
            RestyleText(leftStats, "Resistances", 0.08f, 0.16f, 0.92f, 0.38f);

            // Nav2 becomes MAP OF BRITAIN (placeholder); Nav3 is a spare from the old layout.
            Transform nav2 = FindAny(leftStats, "MapOfBritainButton", "Nav2");
            if (nav2 != null)
            {
                nav2.name = "MapOfBritainButton";
                Button btn = nav2.GetComponent<Button>();
                Win95Skin.StyleButton(btn);
                SetAnchors((RectTransform)nav2, 0.10f, 0.03f, 0.90f, 0.115f);
                Relabel(nav2, "MAP OF BRITAIN", 18);
            }

            Transform nav3 = FindAny(leftStats, "Nav3");
            if (nav3 != null && nav3.gameObject.activeSelf)
            {
                nav3.gameObject.SetActive(false); // fourth old-nav slot has no place in the mock
            }
        }

        // ── Center paper doll ────────────────────────────────────────────────────────────

        /// <summary>Early-Windows cornflower blue for the character backdrop, per the owner's mock.</summary>
        private static readonly Color PaperDollBlue = new Color(0.392f, 0.584f, 0.929f); // #6495ED

        /// <summary>The 7 equippable ItemTypes as mock-colored slots flanking the doll.</summary>
        private struct EquipSlotSpec
        {
            public int SlotIndex;   // EquipSlotN in the scene; its ItemType is EquipmentSlotMap.SlotOrder[SlotIndex]
            public Color Frame;
            public float X0, Y0, X1, Y1;
        }

        // Slot→ItemType order is EquipmentSlotMap.SlotOrder — keep positions/colors here only.
        private static EquipSlotSpec[] EquipLayout =>
            new[]
            {
                // Left column: Head, Chest, Boots — blue / purple / lime
                new EquipSlotSpec { SlotIndex = 0, Frame = Html("2E7CE6"), X0 = 0.04f, Y0 = 0.70f, X1 = 0.28f, Y1 = 0.92f },
                new EquipSlotSpec { SlotIndex = 1, Frame = Html("A040C0"), X0 = 0.04f, Y0 = 0.40f, X1 = 0.28f, Y1 = 0.62f },
                new EquipSlotSpec { SlotIndex = 2, Frame = Html("B8D900"), X0 = 0.04f, Y0 = 0.10f, X1 = 0.28f, Y1 = 0.32f },
                // Right column: Weapon, Shield, Cloak, Ring — cyan / red / pink / dark red
                new EquipSlotSpec { SlotIndex = 3, Frame = Html("29B7D3"), X0 = 0.71f, Y0 = 0.745f, X1 = 0.95f, Y1 = 0.945f },
                new EquipSlotSpec { SlotIndex = 4, Frame = Html("D32F2F"), X0 = 0.71f, Y0 = 0.505f, X1 = 0.95f, Y1 = 0.705f },
                new EquipSlotSpec { SlotIndex = 5, Frame = Html("F48FB1"), X0 = 0.71f, Y0 = 0.265f, X1 = 0.95f, Y1 = 0.465f },
                new EquipSlotSpec { SlotIndex = 6, Frame = Html("8B1A1A"), X0 = 0.71f, Y0 = 0.025f, X1 = 0.95f, Y1 = 0.225f },
            };

        private static Color Html(string hex)
        {
            ColorUtility.TryParseHtmlString("#" + hex, out Color c);
            return c;
        }

        private static void StyleCenter(RectTransform center)
        {
            SetAnchors(center, 0.29f, 0.36f, 0.68f, 0.948f);
            Image panel = center.GetComponent<Image>();
            if (panel != null)
            {
                panel.color = Win95Skin.Face;
                Win95Skin.AddBevel((RectTransform)panel.transform, sunken: true);
            }

            // Cornflower-blue character block. Drawn first so the sprite and slots sit on it.
            RectTransform backdrop = FindOrCreate(center, "PaperDollBackdrop");
            backdrop.SetSiblingIndex(0);
            SetAnchors(backdrop, 0.33f, 0.10f, 0.65f, 0.94f);
            Image backdropImg = backdrop.GetComponent<Image>();
            if (backdropImg == null) backdropImg = backdrop.gameObject.AddComponent<Image>();
            backdropImg.color = PaperDollBlue;
            backdropImg.raycastTarget = false;

            // CharacterSprite fills the blue block and plays the class idle preview
            // (same PlayerClassPreviewUI the character creator uses; InventoryController
            // feeds it the bound character's class on open).
            Transform charSprite = center.Find("CharacterSprite");
            if (charSprite != null)
            {
                var csRt = (RectTransform)charSprite;
                csRt.anchorMin = new Vector2(0.36f, 0.13f);
                csRt.anchorMax = new Vector2(0.62f, 0.91f);
                csRt.offsetMin = Vector2.zero;
                csRt.offsetMax = Vector2.zero;

                Image spriteImg = charSprite.GetComponent<Image>();
                if (spriteImg != null)
                {
                    Undo.RecordObject(spriteImg, "Rebuild Inventory Panel (Win95)");
                    spriteImg.preserveAspect = true;
                    spriteImg.raycastTarget = false;

                    var preview = charSprite.GetComponent<PlayerClassPreviewUI>();
                    if (preview == null)
                        preview = Undo.AddComponent<PlayerClassPreviewUI>(charSprite.gameObject);
                    Undo.RecordObject(preview, "Rebuild Inventory Panel (Win95)");
                    preview.PreviewImage = spriteImg;
                }
            }

            // 7 mock-colored slots for the 7 equippable ItemTypes; the 5 leftover slots
            // from the old 12-slot cross are deactivated, not deleted.
            foreach (EquipSlotSpec spec in EquipLayout)
            {
                Transform slot = center.Find($"EquipSlot{spec.SlotIndex}");
                if (slot == null) continue;
                slot.gameObject.SetActive(true);
                SetAnchors((RectTransform)slot, spec.X0, spec.Y0, spec.X1, spec.Y1);
                Image img = slot.GetComponent<Image>();
                if (img != null) Win95Skin.StyleSunken(img);
                Win95Skin.AddColorFrame((RectTransform)slot, spec.Frame);
            }
            for (int i = 7; i < 12; i++)
            {
                Transform slot = center.Find($"EquipSlot{i}");
                if (slot != null) slot.gameObject.SetActive(false);
            }
        }

        /// <summary>
        /// Points InventoryController.PaperDollContainer (null in the scene today) at
        /// CenterPaperDoll so RefreshUI can find the idle preview under it. Public field,
        /// previously unassigned — no existing binding is disturbed.
        /// </summary>
        private static void BindPaperDollContainer(InventoryController controller, RectTransform center)
        {
            var so = new SerializedObject(controller);
            SerializedProperty prop = so.FindProperty("PaperDollContainer");
            if (prop != null && prop.objectReferenceValue == null)
            {
                prop.objectReferenceValue = center;
                so.ApplyModifiedPropertiesWithoutUndo();
            }
        }

        // ── Tooltip ──────────────────────────────────────────────────────────────────────

        private static void StyleTooltip(RectTransform tooltip)
        {
            Image panel = tooltip.GetComponent<Image>();
            Win95Skin.StyleWindow(panel);

            // Yellow header strip behind the item name; must draw first.
            RectTransform header = FindOrCreate(tooltip, "TooltipHeader");
            header.SetSiblingIndex(0);
            SetAnchors(header, 0.01f, 0.80f, 0.99f, 0.985f);
            Image headerImg = header.GetComponent<Image>();
            if (headerImg == null) headerImg = header.gameObject.AddComponent<Image>();
            headerImg.color = Win95Skin.HeaderYellow;

            Transform title = tooltip.Find("TooltipTitle");
            if (title != null)
            {
                SetAnchors((RectTransform)title, 0.03f, 0.80f, 0.97f, 0.985f);
                var tmp = title.GetComponent<TextMeshProUGUI>();
                if (tmp != null)
                {
                    tmp.color = Win95Skin.FieldText;
                    tmp.alignment = TextAlignmentOptions.Left;
                }
            }

            Transform body = tooltip.Find("TooltipBody");
            if (body != null)
            {
                SetAnchors((RectTransform)body, 0.03f, 0.24f, 0.97f, 0.78f);
                var tmp = body.GetComponent<TextMeshProUGUI>();
                if (tmp != null)
                {
                    tmp.color = Win95Skin.FieldText;
                    tmp.alignment = TextAlignmentOptions.TopLeft;
                }
            }

            // Bottom row: USE (runtime-built, left) · DROP (placeholder, centre) · UNEQUIP /
            // EQUIP (right). EQUIP is shown by runtime only for equippable items; both it and
            // DROP are inert placeholders until those systems exist.
            Transform unequip = tooltip.Find("UnequipBtn");
            if (unequip != null)
            {
                Button btn = unequip.GetComponent<Button>();
                Win95Skin.StyleButton(btn);
                SetAnchors((RectTransform)unequip, 0.68f, 0.04f, 0.96f, 0.20f);
                Relabel(unequip, "UNEQUIP", 18);
            }

            Button drop = FindOrCreateButton(tooltip, "DropButton", "DROP", 18);
            SetAnchors((RectTransform)drop.transform, 0.36f, 0.04f, 0.66f, 0.20f);
            drop.gameObject.SetActive(false);

            Button equip = FindOrCreateButton(tooltip, "EquipButton", "EQUIP", 18);
            SetAnchors((RectTransform)equip.transform, 0.68f, 0.04f, 0.96f, 0.20f);
            equip.gameObject.SetActive(false);
        }

        // ── Backpack grid ────────────────────────────────────────────────────────────────

        /// <summary>6 columns × 6 rows of 74 px cells + 6 px spacing + 12 px padding = 498 px, centred by UpperCenter in the ~565 px panel — a visible grey margin on BOTH sides.</summary>
        private const int BagSlotTarget = 36;

        private static void StyleBackpack(RectTransform backpack)
        {
            // Pulled up to clear the title bar, bottom lifted to make room for the rail.
            // Do NOT reparent existing children or insert non-slot children here —
            // PopulateBackpack addresses slots by child index. New slots are APPENDED.
            SetAnchors(backpack, 0.685f, 0.34f, 0.994f, 0.948f);

            var grid = backpack.GetComponent<GridLayoutGroup>();
            if (grid != null)
            {
                Undo.RecordObject(grid, "Rebuild Inventory Panel (Win95)");
                // 74 px (was 78): the old 522 px grid exactly filled the ~525 px panel, so the
                // last column read as touching the window frame. 498 px leaves ~33 px per side.
                grid.cellSize = new Vector2(74f, 74f);
                grid.spacing = new Vector2(6f, 6f);
                // 12 px breathing room on every side so the slots don't bleed into the window frame.
                grid.padding = new RectOffset(12, 12, 12, 12);
                grid.childAlignment = TextAnchor.UpperCenter;
                grid.startCorner = GridLayoutGroup.Corner.UpperLeft; // fill top-left, across, wrap down
                grid.constraint = GridLayoutGroup.Constraint.FixedColumnCount;
                grid.constraintCount = 6;
            }
            else
            {
                Debug.LogWarning("InventoryWin95Builder: RightBackpack has no GridLayoutGroup; " +
                    "new slots will not be laid out.");
            }

            // Grow 20 → 36 slots. Appending keeps existing child indices stable, so the
            // runtime's GetChild(i) mapping and inventory saves are unaffected.
            for (int i = 0; i < BagSlotTarget; i++)
            {
                Transform slot = backpack.Find($"BagSlot{i}");
                if (slot == null)
                {
                    var go = new GameObject($"BagSlot{i}", typeof(RectTransform));
                    go.transform.SetParent(backpack, false);
                    go.AddComponent<Image>();
                    slot = go.transform;
                }

                Image img = slot.GetComponent<Image>();
                if (img != null)
                {
                    img.color = Win95Skin.SlotFill;
                    Win95Skin.AddBevel((RectTransform)slot, sunken: true);
                }
            }
        }

        // ── Right rail + bottom ─────────────────────────────────────────────────────────

        private static void BuildRail(Transform root, RectTransform leftStats, InventoryController controller)
        {
            // Nav0/Nav1 move from the old left-nav row to the right rail. SPELLS stays
            // runtime-built by InventoryController (BuildSpellsButton) at matching anchors.
            Transform journal = FindAny(leftStats, "QuestJournalButton", "Nav0");
            if (journal != null)
            {
                journal.name = "QuestJournalButton";
                journal.SetParent(root, false);
                Button btn = journal.GetComponent<Button>();
                Win95Skin.StyleButton(btn);
                SetAnchors((RectTransform)journal, 0.70f, 0.245f, 0.97f, 0.305f);
                Relabel(journal, "QUEST JOURNAL", 18);

                if (btn != null && btn.onClick.GetPersistentEventCount() == 0)
                    UnityEventTools.AddVoidPersistentListener(btn.onClick, controller.OnQuestJournalPressed);
            }

            Transform wiki = FindAny(leftStats, "WikiBritainButton", "Nav1");
            if (wiki != null)
            {
                wiki.name = "WikiBritainButton";
                wiki.SetParent(root, false);
                Button btn = wiki.GetComponent<Button>();
                Win95Skin.StyleButton(btn);
                SetAnchors((RectTransform)wiki, 0.70f, 0.105f, 0.97f, 0.165f);
                Relabel(wiki, "WIKIBRITAIN", 18); // placeholder — no wiki system yet
            }
        }

        private static void StyleBottom(Transform root)
        {
            Transform pounds = root.Find("PoundsText");
            if (pounds != null)
            {
                SetAnchors((RectTransform)pounds, 0.58f, 0.02f, 0.76f, 0.08f);
                var tmp = pounds.GetComponent<TextMeshProUGUI>();
                if (tmp != null)
                {
                    tmp.color = Win95Skin.FieldText;
                    tmp.alignment = TextAlignmentOptions.Right;
                }
            }

            Transform back = root.Find("BackButton");
            if (back != null)
            {
                Button btn = back.GetComponent<Button>();
                Win95Skin.StyleButton(btn);
                SetAnchors((RectTransform)back, 0.78f, 0.02f, 0.97f, 0.08f);
                Relabel(back, "Back", 18);
            }
        }

        // ── Helpers ──────────────────────────────────────────────────────────────────────

        private static RectTransform FindOrCreate(Transform parent, string name)
        {
            Transform t = parent.Find(name);
            if (t != null) return (RectTransform)t;

            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        private static Transform FindAny(Transform parent, params string[] names)
        {
            foreach (string n in names)
            {
                Transform t = parent.Find(n);
                if (t != null) return t;
            }
            return null;
        }

        private static TextMeshProUGUI FindOrCreateTmp(Transform parent, string name)
        {
            RectTransform rt = FindOrCreate(parent, name);
            var tmp = rt.GetComponent<TextMeshProUGUI>();
            if (tmp == null) tmp = rt.gameObject.AddComponent<TextMeshProUGUI>();
            return tmp;
        }

        private static Button FindOrCreateButton(Transform parent, string name, string label, int fontSize)
        {
            RectTransform rt = FindOrCreate(parent, name);
            Image img = rt.GetComponent<Image>();
            if (img == null) img = rt.gameObject.AddComponent<Image>();
            Button btn = rt.GetComponent<Button>();
            if (btn == null) btn = rt.gameObject.AddComponent<Button>();
            Win95Skin.StyleButton(btn);
            Relabel(rt, label, fontSize);
            return btn;
        }

        private static void Relabel(Transform buttonRoot, string text, int fontSize)
        {
            var tmp = buttonRoot.GetComponentInChildren<TextMeshProUGUI>(true);
            if (tmp == null)
            {
                tmp = FindOrCreateTmp(buttonRoot, "Label");
                var rt = (RectTransform)tmp.transform;
                rt.anchorMin = Vector2.zero;
                rt.anchorMax = Vector2.one;
                rt.offsetMin = Vector2.zero;
                rt.offsetMax = Vector2.zero;
            }
            tmp.text = text;
            tmp.fontSize = fontSize;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            Win95Skin.StyleLabel(tmp);
        }

        private static void RestyleText(Transform parent, string name, float x0, float y0, float x1, float y1)
        {
            Transform t = parent.Find(name);
            if (t == null) return;
            SetAnchors((RectTransform)t, x0, y0, x1, y1);
            var tmp = t.GetComponent<TextMeshProUGUI>();
            if (tmp != null)
            {
                tmp.color = Win95Skin.FieldText;
                tmp.alignment = TextAlignmentOptions.TopLeft;
            }
        }

        private static void SetAnchors(RectTransform rt, float x0, float y0, float x1, float y1)
        {
            rt.anchorMin = new Vector2(x0, y0);
            rt.anchorMax = new Vector2(x1, y1);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }
    }
}
