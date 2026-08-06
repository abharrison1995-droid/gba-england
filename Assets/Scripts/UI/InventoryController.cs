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
            {
                PlayerSession.Instance.OnInventoryChanged -= HandleInventoryChanged;
                PlayerSession.Instance.OnPoundsChanged -= HandlePoundsChanged;
            }
        }

        /// <summary>PlayerSession may not exist yet at Awake (created on new game/continue) — retried from RefreshUI too.</summary>
        private void EnsureInventorySubscription()
        {
            if (_subscribedToInventory || PlayerSession.Instance == null) return;
            PlayerSession.Instance.OnInventoryChanged += HandleInventoryChanged;
            PlayerSession.Instance.OnPoundsChanged += HandlePoundsChanged;
            _subscribedToInventory = true;
        }

        private void HandleInventoryChanged()
        {
            if (IsOpen) PopulateBackpack();
        }

        /// <summary>
        /// Not gated on <see cref="IsOpen"/> like the backpack is: it is one string assignment on
        /// an event that fires a handful of times a session, and gating it means opening the bag
        /// after a payout shows the old figure until the next one.
        /// </summary>
        private void HandlePoundsChanged() => RefreshCurrency();

        private void RefreshCurrency()
        {
            if (CurrencyText == null) return;
            int pounds = PlayerSession.Instance != null ? PlayerSession.Instance.Pounds : 0;
            CurrencyText.text = EKVibe.FormatPounds(pounds);
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
            RefreshCurrency();

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
            RefreshUseButton(item);
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

        // ── USE ─────────────────────────────────────────────────────────────────────────────
        // The tooltip's second button, built lazily the way BuildSpellsButton builds its own: the
        // bag panel is authored in the scene and does not carry one, and a code-built button is
        // reachable by touch, which a KeyCode would not be (CLAUDE.md §2).

        private Button _useButton;
        private ItemData _tooltipItem;

        /// <summary>
        /// Shows USE for a Consumable and hides it for everything else. Hiding rather than
        /// disabling: a greyed button on every sword invites the player to keep pressing it.
        /// </summary>
        private void RefreshUseButton(ItemData item)
        {
            _tooltipItem = item;

            bool usable = item != null && item.Type == ItemType.Consumable;
            if (_useButton == null)
            {
                if (!usable) return;      // nothing to show and nothing built yet
                _useButton = BuildUseButton();
                if (_useButton == null) return;
            }

            _useButton.gameObject.SetActive(usable);
        }

        private Button BuildUseButton()
        {
            if (TooltipPanel == null) return null;

            Transform existing = TooltipPanel.transform.Find("UseButton");
            if (existing != null) return existing.GetComponent<Button>();

            var go = new GameObject("UseButton", typeof(RectTransform));
            go.transform.SetParent(TooltipPanel.transform, false);
            var rt = (RectTransform)go.transform;
            // Bottom-left of the tooltip, clear of UnequipButton, which the scene anchors right.
            rt.anchorMin = new Vector2(0.04f, 0.04f);
            rt.anchorMax = new Vector2(0.46f, 0.20f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            go.AddComponent<Image>().color = EKVibe.ButtonBrown;

            var button = go.AddComponent<Button>();
            button.onClick.AddListener(UseTooltipItem);

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false);
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.text = "USE";
            tmp.color = EKVibe.TextLight;
            tmp.fontSize = 22;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.raycastTarget = false;

            return button;
        }

        /// <summary>
        /// Consumes one of the tooltip's item: heal, then spend, then animate, then close the bag.
        ///
        /// The removal is what decides whether it worked. RemoveItem is all-or-nothing, so if the
        /// player somehow has none left nothing is healed and nothing is played — healing first and
        /// removing afterwards would pay out on a stack that was not there.
        /// </summary>
        private void UseTooltipItem()
        {
            ItemData item = _tooltipItem;
            if (item == null || item.Type != ItemType.Consumable) return;

            var session = PlayerSession.Instance;
            if (session == null || !session.RemoveItem(item, 1)) return;

            var player = ExiledAlvaston.Combat.CombatController.Instance;
            if (player != null)
            {
                if (item.HealHP > 0)
                {
                    // Health owns the clamp to MaxHealth and refuses to heal the dead;
                    // CombatController.PushHud copies its value back each frame.
                    var health = player.GetComponent<ExiledAlvaston.Combat.Health>();
                    if (health != null) health.Heal(item.HealHP);
                    else player.CurrentHealth += item.HealHP;
                }

                if (item.HealMana > 0)
                {
                    int max = player.PlayerData != null ? player.PlayerData.MaxManaStamina : 50;
                    player.CurrentMana = Mathf.Min(max, player.CurrentMana + item.HealMana);
                }

                PlayUseAnimation(player, item.UseAnimationTrigger);
            }

            HideTooltip();
            ToggleInventory();
        }

        /// <summary>
        /// Fires the item's trigger only if the player's controller actually declares it.
        ///
        /// Same guard CombatController.ApplyLocomotionAnimation uses for Speed and Cycling, and for
        /// the same reason: setting a trigger a controller does not have logs an error every time.
        /// An item naming a trigger no character has is a content gap, not a crash — most sheets do
        /// not include a drinking animation and are not going to.
        /// </summary>
        private static void PlayUseAnimation(ExiledAlvaston.Combat.CombatController player, string trigger)
        {
            if (string.IsNullOrEmpty(trigger)) return;

            Animator animator = player.PlayerAnimator;
            if (animator == null || animator.runtimeAnimatorController == null) return;

            foreach (AnimatorControllerParameter p in animator.parameters)
            {
                if (p.type == AnimatorControllerParameterType.Trigger && p.name == trigger)
                {
                    animator.SetTrigger(trigger);
                    return;
                }
            }
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

            // Stacks past the last slot are carried and invisible. Now that a non-stackable item
            // takes one entry per unit, overflowing the bag is much easier than it used to be, and
            // an item that is simply not drawn reads as a lost item.
            if (stacks != null && stacks.Count > slotCount)
            {
                Debug.LogWarning(
                    $"InventoryController: {stacks.Count} inventory stacks but only {slotCount} bag " +
                    "slots, so the overflow is carried but not drawn.", this);
            }

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
