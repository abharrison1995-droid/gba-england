using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Data;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Bind known spells to the 4 HUD spell slots. Tap a slot to select it, tap a spell to bind
    /// it there, or Clear it. Opened from the bag. Code-built overlay; pauses while open.
    /// </summary>
    public class SpellbookUI : MonoBehaviour
    {
        private static SpellbookUI _instance;

        private GameObject _root;
        private Transform _listContainer;
        private int _selectedSlot;
        private readonly Image[] _slotBg = new Image[CombatController.SpellSlots];
        private readonly TextMeshProUGUI[] _slotText = new TextMeshProUGUI[CombatController.SpellSlots];

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        public static void Open()
        {
            if (_instance == null)
            {
                var go = new GameObject("SpellbookUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<SpellbookUI>();
                _instance.Build();
            }
            _instance.OpenInternal();
        }

        private void Build()
        {
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "SpellbookCanvas", 580);

            _root = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            QuestUIBuilder.Stretch(_root, Vector2.zero, Vector2.one);
            _root.AddComponent<Button>().onClick.AddListener(Close);

            GameObject panel = QuestUIBuilder.CreateImage("Panel", _root.transform, EKVibe.ParchmentPanel);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(760, 620);

            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, EKVibe.ParchmentDark);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0, 1); hrt.anchorMax = Vector2.one; hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero; hrt.sizeDelta = new Vector2(0, 56);
            var hl = QuestUIBuilder.CreateTMP("HL", header.transform, "SPELLBOOK", EKVibe.TextLight, 26,
                TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(hl.gameObject, Vector2.zero, Vector2.one);
            QuestUIBuilder.CreateCloseX(header.transform, Close);

            // 4 slot buttons in a row
            for (int i = 0; i < CombatController.SpellSlots; i++)
            {
                int slot = i;
                GameObject b = QuestUIBuilder.CreateImage($"Slot{i}", panel.transform, EKVibe.SlotFrame);
                var brt = b.GetComponent<RectTransform>();
                float w = 0.2f;
                brt.anchorMin = new Vector2(0.06f + i * 0.23f, 0.72f);
                brt.anchorMax = new Vector2(0.06f + i * 0.23f + w, 0.9f);
                brt.offsetMin = Vector2.zero; brt.offsetMax = Vector2.zero;
                b.AddComponent<Button>().onClick.AddListener(() => SelectSlot(slot));
                _slotBg[i] = b.GetComponent<Image>();
                var t = QuestUIBuilder.CreateTMP($"SlotTxt{i}", b.transform, "", EKVibe.TextLight, 18,
                    TextAlignmentOptions.Center, FontStyles.Bold);
                QuestUIBuilder.Stretch(t.gameObject, Vector2.zero, Vector2.one);
                t.enableWordWrapping = true;
                _slotText[i] = t;
            }

            var pick = QuestUIBuilder.CreateTMP("Pick", panel.transform, "Tap a slot, then a spell to bind it.",
                new Color(EKVibe.TextDark.r, EKVibe.TextDark.g, EKVibe.TextDark.b, 0.7f), 18,
                TextAlignmentOptions.Center, FontStyles.Italic);
            var pkrt = pick.rectTransform;
            pkrt.anchorMin = new Vector2(0.05f, 0.64f); pkrt.anchorMax = new Vector2(0.95f, 0.7f);
            pkrt.offsetMin = Vector2.zero; pkrt.offsetMax = Vector2.zero;

            GameObject clear = QuestUIBuilder.CreateButton("Clear", panel.transform, "CLEAR SLOT", ClearSelected);
            var crt = clear.GetComponent<RectTransform>();
            crt.anchorMin = new Vector2(0.7f, 0.03f); crt.anchorMax = new Vector2(0.95f, 0.1f);
            crt.offsetMin = Vector2.zero; crt.offsetMax = Vector2.zero;

            // Known-spell list
            var listGO = new GameObject("KnownSpells", typeof(RectTransform));
            listGO.transform.SetParent(panel.transform, false);
            var lrt = listGO.GetComponent<RectTransform>();
            lrt.anchorMin = new Vector2(0.05f, 0.12f); lrt.anchorMax = new Vector2(0.95f, 0.62f);
            lrt.offsetMin = Vector2.zero; lrt.offsetMax = Vector2.zero;
            var layout = listGO.AddComponent<VerticalLayoutGroup>();
            layout.spacing = 8; layout.childAlignment = TextAnchor.UpperCenter;
            layout.childControlWidth = true; layout.childForceExpandWidth = true;
            layout.childControlHeight = false; layout.childForceExpandHeight = false;
            _listContainer = listGO.transform;

            _root.SetActive(false);
        }

        private void OpenInternal()
        {
            if (IsOpen) return;
            _selectedSlot = 0;
            Refresh();
            _root.SetActive(true);
            Systems.PauseManager.Push();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            Systems.PauseManager.Pop();
        }

        private void SelectSlot(int slot)
        {
            _selectedSlot = slot;
            Refresh();
        }

        private void BindSpell(AbilityData ability)
        {
            var combat = CombatController.Instance;
            if (combat != null) combat.AssignToSlot(ability, _selectedSlot);
            Refresh();
        }

        private void ClearSelected()
        {
            var combat = CombatController.Instance;
            if (combat != null) combat.ClearSlot(_selectedSlot);
            Refresh();
        }

        private void Refresh()
        {
            var combat = CombatController.Instance;

            for (int i = 0; i < CombatController.SpellSlots; i++)
            {
                AbilityData a = (combat != null && combat.EquippedAbilities != null && i < combat.EquippedAbilities.Count)
                    ? combat.EquippedAbilities[i] : null;
                _slotText[i].text = a != null
                    ? $"Slot {i + 1}\n{Glyph(a)} {a.AbilityName}"
                    : $"Slot {i + 1}\n(empty)";
                _slotBg[i].color = i == _selectedSlot ? EKVibe.ButtonBrown : EKVibe.SlotFrame;
            }

            foreach (Transform c in _listContainer) Destroy(c.gameObject);

            if (combat == null || combat.KnownSpells.Count == 0)
            {
                AddRowLabel("No spells learned yet.");
                return;
            }
            foreach (AbilityData a in combat.KnownSpells)
            {
                AbilityData spell = a;
                GameObject row = QuestUIBuilder.CreateImage("SpellRow", _listContainer, EKVibe.SlotFrame);
                row.GetComponent<RectTransform>().sizeDelta = new Vector2(0, 56);
                row.AddComponent<Button>().onClick.AddListener(() => BindSpell(spell));
                var t = QuestUIBuilder.CreateTMP("T", row.transform, $"{Glyph(a)}  {a.AbilityName}",
                    EKVibe.TextLight, 22, TextAlignmentOptions.Left, FontStyles.Bold);
                QuestUIBuilder.Stretch(t.gameObject, Vector2.zero, Vector2.one);
                t.rectTransform.offsetMin = new Vector2(18, 0);
                t.raycastTarget = false;
            }
        }

        private void AddRowLabel(string text)
        {
            var t = QuestUIBuilder.CreateTMP("Empty", _listContainer, text, EKVibe.ParchmentDark, 20,
                TextAlignmentOptions.Center, FontStyles.Italic);
            t.rectTransform.sizeDelta = new Vector2(0, 40);
        }

        private static string Glyph(AbilityData a)
        {
            if (a == null) return "";
            if (!string.IsNullOrEmpty(a.IconGlyph)) return a.IconGlyph;
            return string.IsNullOrEmpty(a.AbilityName) ? "*" : a.AbilityName.Substring(0, 1);
        }
    }
}
