using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.Vibe;
using System.Collections.Generic;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Fullscreen parchment inventory: left stats, center paper doll + tooltip, right backpack.
    /// </summary>
    public class InventoryController : MonoBehaviour
    {
        [Header("Overlay Root")]
        public GameObject InventoryUIPanel;

        [Header("Left Panel: Stats & Identity")]
        public Image CharacterPortrait;
        public TextMeshProUGUI LevelText;
        public TextMeshProUGUI CoreTraitsText;
        public TextMeshProUGUI AttackStatsText;
        public TextMeshProUGUI ResistancesText;
        public TextMeshProUGUI CharacterNameText;

        [Header("Center Panel: Paper Doll + Tooltip")]
        public Transform PaperDollContainer;
        public Dictionary<ItemType, Image> EquipmentSlots = new Dictionary<ItemType, Image>();
        public GameObject TooltipPanel;
        public Image TooltipIcon;
        public TextMeshProUGUI TooltipTitle;
        public TextMeshProUGUI TooltipBody;
        public Button UnequipButton;

        [Header("Right Panel: Backpack")]
        public Transform BackpackGridContainer;
        public TextMeshProUGUI CurrencyText;

        private CharacterData _boundCharacter;
        private bool _subscribedToInventory;

        private void Awake()
        {
            if (InventoryUIPanel == null) return;
            Transform back = InventoryUIPanel.transform.Find("BackButton");
            if (back != null)
            {
                Button btn = back.GetComponent<Button>();
                if (btn != null)
                    btn.onClick.AddListener(ToggleInventory);
            }

            BuildSpellsButton();
            EnsureInventorySubscription();
        }

        private void OnDestroy()
        {
            if (_subscribedToInventory && PlayerSession.Instance != null)
                PlayerSession.Instance.OnInventoryChanged -= HandleInventoryChanged;
        }

        /// <summary>PlayerSession may not exist yet at Awake (created on new game/continue) — retried from RefreshUI too.</summary>
        private void EnsureInventorySubscription()
        {
            if (_subscribedToInventory || PlayerSession.Instance == null) return;
            PlayerSession.Instance.OnInventoryChanged += HandleInventoryChanged;
            _subscribedToInventory = true;
        }

        private void HandleInventoryChanged()
        {
            if (IsOpen) PopulateBackpack();
        }

        /// <summary>Adds a "SPELLS" button to the bag that opens the spellbook (bind spells to slots).</summary>
        private void BuildSpellsButton()
        {
            if (InventoryUIPanel.transform.Find("SpellsButton") != null) return;

            var go = new GameObject("SpellsButton", typeof(RectTransform));
            go.transform.SetParent(InventoryUIPanel.transform, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = new Vector2(0.56f, 0.02f);
            rt.anchorMax = new Vector2(0.75f, 0.08f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            go.AddComponent<Image>().color = EKVibe.ButtonBrown;
            go.AddComponent<Button>().onClick.AddListener(SpellbookUI.Open);

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false);
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.text = "SPELLS";
            tmp.color = EKVibe.TextLight;
            tmp.fontSize = 22;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.raycastTarget = false;
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.I))
            {
                // Only in gameplay — toggling on Title/Death would strand a pushed pause
                var flow = ExiledAlvaston.Flow.GameFlowController.Instance;
                if (flow == null || flow.State == ExiledAlvaston.Flow.GameFlowState.Playing)
                    ToggleInventory();
            }
        }

        public bool IsOpen => InventoryUIPanel != null && InventoryUIPanel.activeSelf;

        /// <summary>Close and release the pause if open — called on flow changes (title, death).</summary>
        public void CloseIfOpen()
        {
            if (IsOpen) ToggleInventory();
        }

        public void BindCharacter(CharacterData data)
        {
            _boundCharacter = data;
            if (InventoryUIPanel != null && InventoryUIPanel.activeSelf)
                RefreshUI();
        }

        public void ToggleInventory()
        {
            if (InventoryUIPanel == null) return;

            bool isActive = !InventoryUIPanel.activeSelf;
            InventoryUIPanel.SetActive(isActive);
            if (isActive) ExiledAlvaston.Systems.PauseManager.Push();
            else ExiledAlvaston.Systems.PauseManager.Pop();

            if (isActive)
                RefreshUI();
        }

        private void RefreshUI()
        {
            EnsureInventorySubscription();
            PopulateBackpack();

            if (_boundCharacter == null) return;

            if (CharacterNameText != null)
                CharacterNameText.text = _boundCharacter.CharacterName;

            if (CharacterPortrait != null && _boundCharacter.Portrait != null)
                CharacterPortrait.sprite = _boundCharacter.Portrait;

            if (CoreTraitsText != null)
            {
                var t = _boundCharacter.BaseTraits;
                CoreTraitsText.text =
                    $"STR  {t.Strength}\nEND  {t.Endurance}\nAGI  {t.Agility}\n" +
                    $"INT  {t.Intelligence}\nAWA  {t.Awareness}\nPER  {t.Perception}";
            }

            if (ResistancesText != null)
            {
                var r = _boundCharacter.BaseResistances;
                ResistancesText.text =
                    $"Armor {r.Physical}\nFire {r.Fire}  Cold {r.Cold}\n" +
                    $"Poison {r.Poison}  Magic {r.Magic}";
            }
        }

        public void ShowTooltip(ItemData item)
        {
            if (TooltipPanel == null || item == null) return;

            TooltipPanel.SetActive(true);
            if (TooltipIcon != null)
            {
                TooltipIcon.sprite = item.Icon;
                TooltipIcon.enabled = item.Icon != null;
            }
            if (TooltipTitle != null)
                TooltipTitle.text = item.ItemName;
            if (TooltipBody != null)
            {
                string stats = "";
                if (item.Armor > 0) stats += $"+{item.Armor} Armor\n";
                if (item.Damage > 0) stats += $"+{item.Damage} Damage\n";
                TooltipBody.text = $"{item.Description}\n{stats}".Trim();
            }
        }

        public void HideTooltip()
        {
            if (TooltipPanel != null)
                TooltipPanel.SetActive(false);
        }

        public void EquipItem(ItemData item)
        {
            if (item == null || !EquipmentSlots.ContainsKey(item.Type)) return;

            Image slotImage = EquipmentSlots[item.Type];
            if (slotImage != null)
            {
                slotImage.sprite = item.Icon;
                slotImage.enabled = item.Icon != null;
            }
            ShowTooltip(item);
        }

        /// <summary>
        /// Fills the backpack grid from PlayerSession's live inventory. The 20 slot GameObjects
        /// (BagSlot0..19) already exist in the scene as plain framed Images — this sets each
        /// one's icon/tint from the matching inventory stack rather than instantiating a prefab.
        /// </summary>
        public void PopulateBackpack()
        {
            if (BackpackGridContainer == null) return;

            IReadOnlyList<InventoryStack> stacks = PlayerSession.Instance != null
                ? PlayerSession.Instance.Inventory
                : null;

            int slotCount = BackpackGridContainer.childCount;
            for (int i = 0; i < slotCount; i++)
            {
                InventoryStack stack = stacks != null && i < stacks.Count ? stacks[i] : null;
                ApplySlot(BackpackGridContainer.GetChild(i), stack);
            }
        }

        private void ApplySlot(Transform slot, InventoryStack stack)
        {
            ItemData item = stack?.Item;

            Image icon = slot.GetComponent<Image>();
            if (icon != null)
            {
                icon.sprite = item != null ? item.Icon : null;
                icon.color = item != null && item.Icon != null ? Color.white : EKVibe.SlotEmpty;
            }

            TextMeshProUGUI qtyLabel = GetOrCreateQuantityLabel(slot);
            bool showQty = stack != null && stack.Quantity > 1;
            qtyLabel.gameObject.SetActive(showQty);
            if (showQty)
                qtyLabel.text = stack.Quantity.ToString();

            Button button = slot.GetComponent<Button>();
            if (button == null)
                button = slot.gameObject.AddComponent<Button>();
            button.onClick.RemoveAllListeners();
            if (item != null)
                button.onClick.AddListener(() => ShowTooltip(item));
        }

        private static TextMeshProUGUI GetOrCreateQuantityLabel(Transform slot)
        {
            Transform existing = slot.Find("Qty");
            if (existing != null)
                return existing.GetComponent<TextMeshProUGUI>();

            var go = new GameObject("Qty", typeof(RectTransform));
            go.transform.SetParent(slot, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = new Vector2(1, 0);
            rt.anchorMax = new Vector2(1, 0);
            rt.pivot = new Vector2(1, 0);
            rt.anchoredPosition = new Vector2(-4, 2);
            rt.sizeDelta = new Vector2(28, 18);

            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.color = EKVibe.TextLight;
            tmp.fontSize = 16;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.BottomRight;
            tmp.raycastTarget = false;
            return tmp;
        }
    }
}
