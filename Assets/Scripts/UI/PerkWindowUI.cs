using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// PERKS — the perk window, opened from the bag's left stats panel. Two panes: a scrollable
    /// perk list on the left grouped by minimum level, and a detail pane on the right with the
    /// perk's title, its generated effect list, a requirements line, the owner's description and a
    /// SPEND button.
    ///
    /// Modelled on <see cref="WikiBritainUI"/>, with one deliberate difference: locked rows ARE
    /// clickable and show their real title. A wiki entry is a discovery, so hiding it behind "???"
    /// is the point; a perk is a PLAN, and a player deciding where to spend has to be able to read
    /// what is ahead of them. Only the SPEND button is disabled.
    ///
    /// ⚠ No PerkData asset exists yet. An empty list saying so is the correct shipping state, not
    /// a bug — see docs/plans/PROGRESSION_PHASE3_IMPLEMENTATION.md §10.3 check 5.
    ///
    /// Pauses while open. BACK returns to the bag; X / dimmer / E / W close to gameplay.
    /// </summary>
    public class PerkWindowUI : MonoBehaviour
    {
        private static PerkWindowUI _instance;

        private GameObject _root;
        private Transform _listContainer;
        private RectTransform _listContent;
        private ScrollRect _listScroll;
        private float _cursorY;

        private TextMeshProUGUI _dTitle;
        private TextMeshProUGUI _dEffects;
        private TextMeshProUGUI _dRequirement;
        private TextMeshProUGUI _dBody;
        private ScrollRect _bodyScroll;
        private TextMeshProUGUI _countText;
        private Button _spendButton;
        private PerkData _shown;

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        public static void Open()
        {
            if (_instance == null)
            {
                var go = new GameObject("PerkWindowUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<PerkWindowUI>();
                _instance.BuildUI();
            }
            _instance.OpenInternal();
        }

        /// <summary>Hotkey-style toggle, matching the wiki/journal/map: refuses to stack on another paused menu.</summary>
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
            ShowFirstOrHint();
            _root.SetActive(true);
            Systems.PauseManager.Push();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            Systems.PauseManager.Pop();
        }

        /// <summary>BACK returns to the bag this was opened from — the wiki's exact pause-balanced hand-off.</summary>
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

        // ── Perk list ───────────────────────────────────────────────────────────────────

        /// <summary>
        /// Perks this character could ever take, ordered by MinLevel then PerkId. Class-restricted
        /// perks belonging to someone else are left out entirely — they are not a plan this player
        /// can make.
        /// </summary>
        private static List<PerkData> ListedPerks()
        {
            var session = PlayerSession.Instance;
            var listed = new List<PerkData>();

            foreach (PerkData perk in PerkDatabase.All)
            {
                if (perk == null || string.IsNullOrEmpty(perk.PerkId)) continue;
                if (session != null && !perk.CanBeTakenBy(session.Class)) continue;
                listed.Add(perk);
            }

            listed.Sort((a, b) =>
            {
                int byLevel = a.MinLevel.CompareTo(b.MinLevel);
                return byLevel != 0 ? byLevel : string.CompareOrdinal(a.PerkId, b.PerkId);
            });
            return listed;
        }

        private void PopulateList()
        {
            foreach (Transform child in _listContainer)
                Destroy(child.gameObject);
            _cursorY = 8f;

            var session = PlayerSession.Instance;
            List<PerkData> perks = ListedPerks();

            int lastLevel = int.MinValue;
            foreach (PerkData perk in perks)
            {
                if (perk.MinLevel != lastLevel)
                {
                    // Generated, so there is no section enum to keep in step and no copy to write.
                    AddSectionLabel("LEVEL " + perk.MinLevel);
                    lastLevel = perk.MinLevel;
                }
                AddPerkRow(perk, session);
            }

            if (perks.Count == 0)
                AddSectionLabel("[no perks written yet - owner to author]");

            if (_listContent != null)
                _listContent.sizeDelta = new Vector2(0f, _cursorY + 4f);
            if (_listScroll != null)
                _listScroll.verticalNormalizedPosition = 1f;

            RefreshCount();
        }

        private void RefreshCount()
        {
            if (_countText == null) return;
            int unspent = PlayerSession.Instance != null ? PlayerSession.Instance.UnspentPerkPoints : 0;
            _countText.text = unspent == 1 ? "1 point unspent" : $"{unspent} points unspent";
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

        private void AddPerkRow(PerkData perk, PlayerSession session)
        {
            bool taken = session != null && session.HasPerk(perk.PerkId);
            bool available = !taken && session != null && session.PerkRefusalReason(perk) == null;

            const float rowH = 52f;
            GameObject row = QuestUIBuilder.CreateImage("PerkRow", _listContainer,
                taken || available ? Win95Skin.SlotFill : Win95Skin.Shadow);
            Win95Skin.AddBevel((RectTransform)row.transform, sunken: true);
            var rrt = row.GetComponent<RectTransform>();
            rrt.anchorMin = new Vector2(0f, 1f);
            rrt.anchorMax = new Vector2(1f, 1f);
            rrt.pivot = new Vector2(0.5f, 1f);
            rrt.sizeDelta = new Vector2(-8f, rowH);
            rrt.anchoredPosition = new Vector2(0f, -_cursorY);

            // Every row opens, locked ones included — see the class doc.
            row.AddComponent<Button>().onClick.AddListener(() => ShowDetail(perk));

            string title = string.IsNullOrEmpty(perk.Title) ? perk.PerkId : perk.Title;
            // ASCII marker rather than a tick glyph: TMP's default static atlases here are
            // effectively ASCII-only (the pound sign already has this problem), and a missing glyph
            // renders as a box, which reads as a fault rather than as "taken".
            var label = QuestUIBuilder.CreateTMP("Label", row.transform,
                taken ? title + "  (taken)" : title,
                taken || available ? Win95Skin.FieldText : Win95Skin.Face,
                19, TextAlignmentOptions.Left, taken ? FontStyles.Bold : FontStyles.Normal);
            QuestUIBuilder.Stretch(label.gameObject, Vector2.zero, Vector2.one);
            label.rectTransform.offsetMin = new Vector2(12f, 0f);
            label.rectTransform.offsetMax = new Vector2(-8f, 0f);
            label.raycastTarget = false;

            _cursorY += rowH + 6f;
        }

        // ── Detail pane ─────────────────────────────────────────────────────────────────

        /// <summary>
        /// One effect as a line the player can read. Machinery text, not flavour — the flavour is
        /// the owner's Description.
        /// </summary>
        private static string DescribeEffect(PerkEffect effect)
        {
            if (effect == null) return "";

            float m = effect.Magnitude;
            string signed = (m >= 0f ? "+" : "") + m.ToString("0.##");

            switch (effect.Type)
            {
                case PerkEffectType.MeleeDamagePercent: return signed + "% melee damage";
                case PerkEffectType.SpellDamagePercent: return signed + "% spell damage";
                case PerkEffectType.MaxHealthFlat: return signed + " max health";
                case PerkEffectType.MaxHealthPercent: return signed + "% max health";
                case PerkEffectType.ArmourFlat: return signed + " armour";
                case PerkEffectType.MaxResourceFlat: return signed + " max mana/stamina";
                case PerkEffectType.ResourceRegenPercent: return signed + "% mana/stamina regen";
                case PerkEffectType.MoveSpeedPercent: return signed + "% move speed";
                case PerkEffectType.ExtraLootRolls: return signed + " loot rolls from containers";
                default: return effect.Type + " " + signed;
            }
        }

        private void ShowDetail(PerkData perk)
        {
            _shown = perk;
            if (perk == null) return;

            var session = PlayerSession.Instance;

            _dTitle.text = string.IsNullOrEmpty(perk.Title) ? perk.PerkId : perk.Title;

            var effects = new System.Text.StringBuilder();
            if (perk.Effects != null)
            {
                for (int i = 0; i < perk.Effects.Count; i++)
                {
                    string line = DescribeEffect(perk.Effects[i]);
                    if (string.IsNullOrEmpty(line)) continue;
                    if (effects.Length > 0) effects.Append('\n');
                    effects.Append(line);
                }
            }
            _dEffects.text = effects.ToString();

            string refusal = session != null ? session.PerkRefusalReason(perk) : "Unavailable";
            _dRequirement.text = refusal ?? "";

            // Placeholder mirrors the wiki's: an unwritten description says so rather than
            // rendering as an empty gap that looks like a layout fault.
            _dBody.text = string.IsNullOrEmpty(perk.Description) ? "(nothing written yet)" : perk.Description;

            if (_spendButton != null)
                _spendButton.interactable = refusal == null;

            if (_bodyScroll != null)
                _bodyScroll.verticalNormalizedPosition = 1f;
        }

        /// <summary>Opening state: the first listed perk, or a hint when none have been authored.</summary>
        private void ShowFirstOrHint()
        {
            List<PerkData> perks = ListedPerks();
            if (perks.Count > 0)
            {
                ShowDetail(perks[0]);
                return;
            }

            _shown = null;
            _dTitle.text = "PERKS";
            _dEffects.text = "";
            _dRequirement.text = "";
            _dBody.text = "[no perks written yet - owner to author]";
            if (_spendButton != null) _spendButton.interactable = false;
        }

        private void OnSpendPressed()
        {
            var session = PlayerSession.Instance;
            if (session == null || _shown == null) return;
            if (!session.SpendPerkPoint(_shown)) return;

            PerkData spent = _shown;
            PopulateList();
            ShowDetail(spent);
        }

        // ── Chrome ──────────────────────────────────────────────────────────────────────

        private void BuildUI()
        {
            // 575 is free: the orders in use are 550, 560, 565, 570, 580, 600 and 610.
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "PerkWindowCanvas", 575);

            GameObject dim = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            QuestUIBuilder.Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);
            _root = dim;

            GameObject panel = QuestUIBuilder.CreateImage("PerkPanel", dim.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(980f, 800f);

            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, Win95Skin.TitleBar);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0f, 1f);
            hrt.anchorMax = Vector2.one;
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0f, 60f);

            var headerLabel = QuestUIBuilder.CreateTMP("HeaderLabel", header.transform, "PERKS",
                Win95Skin.TitleText, 28, TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(headerLabel.gameObject, Vector2.zero, Vector2.one);

            QuestUIBuilder.CreateCloseX(header.transform, Close);

            BuildListPane(panel.transform);
            BuildDetailPane(panel.transform);

            // Bottom strip: BACK to the bag on the left, unspent points on the right.
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

            // No banner slot: perks have no art, so the wiki's fixed image band would be a
            // permanent empty rectangle. The space goes to the effect list instead.
            _dTitle = QuestUIBuilder.CreateTMP("Title", pane.transform, "",
                Win95Skin.FieldText, 28, TextAlignmentOptions.Left, FontStyles.Bold);
            var trt = _dTitle.rectTransform;
            trt.anchorMin = new Vector2(0f, 1f);
            trt.anchorMax = new Vector2(1f, 1f);
            trt.pivot = new Vector2(0.5f, 1f);
            trt.anchoredPosition = new Vector2(0f, -12f);
            trt.sizeDelta = new Vector2(-28f, 44f);
            _dTitle.raycastTarget = false;

            _dEffects = QuestUIBuilder.CreateTMP("Effects", pane.transform, "",
                Win95Skin.FieldText, 20, TextAlignmentOptions.TopLeft, FontStyles.Bold);
            var ert = _dEffects.rectTransform;
            ert.anchorMin = new Vector2(0f, 1f);
            ert.anchorMax = new Vector2(1f, 1f);
            ert.pivot = new Vector2(0.5f, 1f);
            ert.anchoredPosition = new Vector2(0f, -60f);
            ert.sizeDelta = new Vector2(-28f, 120f);
            _dEffects.raycastTarget = false;

            _dRequirement = QuestUIBuilder.CreateTMP("Requirement", pane.transform, "",
                new Color(0f, 0f, 0f, 0.65f), 18, TextAlignmentOptions.TopLeft, FontStyles.Italic);
            var rrt = _dRequirement.rectTransform;
            rrt.anchorMin = new Vector2(0f, 1f);
            rrt.anchorMax = new Vector2(1f, 1f);
            rrt.pivot = new Vector2(0.5f, 1f);
            rrt.anchoredPosition = new Vector2(0f, -184f);
            rrt.sizeDelta = new Vector2(-28f, 34f);
            _dRequirement.raycastTarget = false;

            // Description: a plain text scroll, the owner's prose. ContentSizeFitter on the text
            // itself — no layout group, per the journal's mask lesson.
            GameObject bodyView = QuestUIBuilder.CreateImage("BodyViewport", pane.transform, new Color(0f, 0f, 0f, 0.06f));
            var bvrt = bodyView.GetComponent<RectTransform>();
            bvrt.anchorMin = new Vector2(0f, 0f);
            bvrt.anchorMax = new Vector2(1f, 1f);
            bvrt.offsetMin = new Vector2(12f, 64f);
            bvrt.offsetMax = new Vector2(-12f, -224f);
            bodyView.AddComponent<RectMask2D>();

            var bodyGO = new GameObject("Body", typeof(RectTransform));
            bodyGO.transform.SetParent(bodyView.transform, false);
            var brt = bodyGO.GetComponent<RectTransform>();
            brt.anchorMin = new Vector2(0f, 1f);
            brt.anchorMax = new Vector2(1f, 1f);
            brt.pivot = new Vector2(0.5f, 1f);
            brt.anchoredPosition = Vector2.zero;
            brt.sizeDelta = Vector2.zero;

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
            _bodyScroll.content = brt;
            _bodyScroll.horizontal = false;
            _bodyScroll.movementType = ScrollRect.MovementType.Clamped;
            _bodyScroll.scrollSensitivity = 28f;

            GameObject spend = QuestUIBuilder.CreateButton("SpendButton", pane.transform, "SPEND", OnSpendPressed);
            var srt = spend.GetComponent<RectTransform>();
            srt.anchorMin = srt.anchorMax = new Vector2(1f, 0f);
            srt.pivot = new Vector2(1f, 0f);
            srt.anchoredPosition = new Vector2(-12f, 12f);
            srt.sizeDelta = new Vector2(180f, 44f);
            _spendButton = spend.GetComponent<Button>();
            _spendButton.interactable = false;
        }
    }
}
