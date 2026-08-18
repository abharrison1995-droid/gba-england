using UnityEngine;
using UnityEngine.UI;
using TMPro;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.Vibe;
using System.Collections.Generic;

namespace GBHEngland.UI
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
        private bool _pendingPerkPointCheck;

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

            // Win95 title bar close (X) — same as Back. Created by the editor rebuild tool.
            Transform close = InventoryUIPanel.transform.Find("TitleBar/CloseButton");
            if (close != null)
            {
                Button closeBtn = close.GetComponent<Button>();
                if (closeBtn != null)
                    closeBtn.onClick.AddListener(ToggleInventory);
            }

            // MAP OF BRITAIN (left stats, built by the rebuild tool) — a placeholder in the
            // scene, so nothing persistent to preserve: just add the runtime call.
            Transform mapBtn = FindChildByName(InventoryUIPanel.transform, "MapOfBritainButton");
            if (mapBtn != null)
            {
                Button map = mapBtn.GetComponent<Button>();
                if (map != null)
                    map.onClick.AddListener(OnMapOfBritainPressed);
            }

            // WIKIBRITAIN (right rail) — same placeholder-to-runtime wiring as the map button.
            Transform wikiBtn = FindChildByName(InventoryUIPanel.transform, "WikiBritainButton");
            if (wikiBtn != null)
            {
                Button wiki = wikiBtn.GetComponent<Button>();
                if (wiki != null)
                    wiki.onClick.AddListener(OnWikiBritainPressed);
            }

            CachePlaceholderButtons();
            BuildEquipmentSlots();

            if (UnequipButton != null)
            {
                UnequipButton.onClick.AddListener(UnequipTooltipItem);
                UnequipButton.gameObject.SetActive(false); // shown only for paper-doll tooltips
            }

            BuildSpellsButton();
            BuildPerksButton();

            // The scene stores LevelText as fileID: 0 and no builder tool assigns it, so without
            // this fallback the readout the bag already reserves stays dead forever — and it would
            // look wired, because the field exists. Resolved by the name the rebuild tool creates.
            if (LevelText == null)
            {
                Transform levelXp = FindChildByName(InventoryUIPanel.transform, "LevelXpText");
                if (levelXp != null)
                    LevelText = levelXp.GetComponent<TextMeshProUGUI>();
            }

            EnsureInventorySubscription();
        }

        private void OnDestroy()
        {
            if (_subscribedToInventory && PlayerSession.Instance != null)
            {
                PlayerSession.Instance.OnInventoryChanged -= HandleInventoryChanged;
                PlayerSession.Instance.OnPoundsChanged -= HandlePoundsChanged;
                PlayerSession.Instance.OnEquipmentChanged -= HandleEquipmentChanged;
                PlayerSession.Instance.OnXPChanged -= HandleXPChanged;
                PlayerSession.Instance.OnLevelUp -= HandleLevelUp;
                PlayerSession.Instance.OnPerksChanged -= HandlePerksChanged;
            }
        }

        /// <summary>PlayerSession may not exist yet at Awake (created on new game/continue) — retried from RefreshUI too.</summary>
        private void EnsureInventorySubscription()
        {
            if (_subscribedToInventory || PlayerSession.Instance == null) return;
            PlayerSession.Instance.OnInventoryChanged += HandleInventoryChanged;
            PlayerSession.Instance.OnPoundsChanged += HandlePoundsChanged;
            PlayerSession.Instance.OnEquipmentChanged += HandleEquipmentChanged;
            PlayerSession.Instance.OnXPChanged += HandleXPChanged;
            PlayerSession.Instance.OnLevelUp += HandleLevelUp;
            PlayerSession.Instance.OnPerksChanged += HandlePerksChanged;
            _subscribedToInventory = true;
        }

        /// <summary>
        /// Forces the perk window open when a level-up actually pays a perk point.
        ///
        /// Gated on the point count moving — points come every second level, so firing on every
        /// level-up would force the window open on odd levels that the curve does not pay. The
        /// actual open is deferred to <see cref="Update"/> via <see cref="_pendingPerkPointCheck"/>
        /// rather than called directly here, so several level-ups fired in one
        /// <c>PlayerSession.GrantXP</c> call coalesce into at most one window-open.
        /// </summary>
        private void HandleLevelUp(int newLevel)
        {
            if (EKVibe.PerkPointsAtLevel(newLevel) <= EKVibe.PerkPointsAtLevel(newLevel - 1)) return;
            _pendingPerkPointCheck = true;
        }

        /// <summary>Perk spends can change the Armor line, the same way equipping a shield does.</summary>
        private void HandlePerksChanged()
        {
            if (IsOpen) RefreshUI();
        }

        private void HandleInventoryChanged()
        {
            if (IsOpen) PopulateBackpack();
        }

        private void HandleEquipmentChanged()
        {
            if (!IsOpen) return;
            RefreshEquipmentSlots();
            RefreshUI(); // the Armour line reflects the new total
        }

        /// <summary>
        /// Not gated on <see cref="IsOpen"/> like the backpack is: it is one string assignment on
        /// an event that fires a handful of times a session, and gating it means opening the bag
        /// after a payout shows the old figure until the next one.
        /// </summary>
        private void HandlePoundsChanged() => RefreshCurrency();

        /// <summary>
        /// Follows <see cref="HandlePoundsChanged"/>, not the backpack handler: refreshed whether
        /// or not the bag is open, so opening it after a kill cannot show a stale figure.
        /// </summary>
        private void HandleXPChanged() => RefreshLevel();

        /// <summary>
        /// Writes the three-line shape the rebuild tool authors into LevelXpText. A
        /// <see cref="PlayerSession.XPForNextLevel"/> of 0 means the level cap, not "nothing
        /// needed", and prints as MAX.
        /// </summary>
        private void RefreshLevel()
        {
            if (LevelText == null) return;

            var session = PlayerSession.Instance;
            int level = session != null ? session.Level : 1;
            int into = session != null ? session.XPIntoLevel : 0;
            int next = session != null ? session.XPForNextLevel : 0;

            string toNext = next > 0 ? next.ToString() : "MAX";
            LevelText.text = $"Player level: {level}\n\nCurrent XP: {into}\n\nXP to next level: {toNext}";
        }

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
            // Right rail, between QUEST JOURNAL (above) and WIKIBRITAIN (below).
            rt.anchorMin = new Vector2(0.70f, 0.175f);
            rt.anchorMax = new Vector2(0.97f, 0.235f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            go.AddComponent<Image>();
            var spellsButton = go.AddComponent<Button>();
            Win95Skin.StyleButton(spellsButton);
            spellsButton.onClick.AddListener(SpellbookUI.Open);

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false);
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.text = "SPELLS";
            tmp.fontSize = 18;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            Win95Skin.StyleLabel(tmp);
        }

        /// <summary>
        /// Adds a "PERKS" button that opens the perk window. Built at runtime in the image of
        /// <see cref="BuildSpellsButton"/>, so it needs no editor step and no rebuild-tool run —
        /// and the rebuild tool uses FindOrCreate throughout, so it never deletes this.
        ///
        /// It goes in the LEFT stats panel, not the right rail: the rail is full (the backpack
        /// occupies y 0.34-0.948, then QUEST JOURNAL, SPELLS and WIKIBRITAIN take the rest), and
        /// the left panel is already the character sheet, which is what a perk is part of.
        ///
        /// ⚠ The free band under MAP OF BRITAIN is only about 39 px tall against about 65 px for a
        /// rail button. This is the one layout number here that was reasoned about rather than
        /// looked at. If it reads cramped, raise Resistances to (0.08, 0.20)-(0.92, 0.38) in
        /// Assets/Editor/InventoryWin95Builder.cs, widen this button to 0.118-0.19, and re-run
        /// Tools > UI > Rebuild Inventory Panel (Win95) with Play mode stopped.
        /// </summary>
        private void BuildPerksButton()
        {
            Transform leftStats = FindChildByName(InventoryUIPanel.transform, "LeftStats");
            // No LeftStats means an older bag layout: skip rather than hanging the button somewhere
            // arbitrary where it would overlap the backpack.
            if (leftStats == null) return;
            if (leftStats.Find("PerksButton") != null) return;

            var go = new GameObject("PerksButton", typeof(RectTransform));
            go.transform.SetParent(leftStats, false);
            var rt = (RectTransform)go.transform;
            // The free band between MAP OF BRITAIN (top 0.115) and Resistances (bottom 0.16).
            rt.anchorMin = new Vector2(0.10f, 0.118f);
            rt.anchorMax = new Vector2(0.90f, 0.156f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            go.AddComponent<Image>();
            var perksButton = go.AddComponent<Button>();
            Win95Skin.StyleButton(perksButton);
            perksButton.onClick.AddListener(OnPerksPressed);

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false);
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            var tmp = labelGo.AddComponent<TextMeshProUGUI>();
            tmp.text = "PERKS";
            tmp.fontSize = 18;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            Win95Skin.StyleLabel(tmp);
        }

        private void Update()
        {
            // Deferred rather than opened straight from HandleLevelUp: PlayerSession.GrantXP can
            // fire OnLevelUp several times in one call for a single big XP award, and
            // PerkWindowUI.Open() has no re-entrancy guard — two opens in the same frame would
            // push PauseManager twice for one closed-once window, leaving the game permanently
            // frozen after the player closes it, silently. Checked ahead of the bag toggle below
            // so a pending forced-open wins over the player pressing I in the same frame. The
            // !PauseManager.IsPaused guard means it waits harmlessly — re-armed by any further
            // level-up — until nothing else is paused, so it never force-closes dialogue or the
            // bag itself.
            if (_pendingPerkPointCheck)
            {
                var flow = GBHEngland.Flow.GameFlowController.Instance;
                bool inGameplay = flow == null || flow.State == GBHEngland.Flow.GameFlowState.Playing;
                if (inGameplay && !GBHEngland.Systems.PauseManager.IsPaused)
                {
                    _pendingPerkPointCheck = false;
                    PerkWindowUI.Open();
                }
            }

            if (Input.GetKeyDown(KeyCode.I))
            {
                // Only in gameplay — toggling on Title/Death would strand a pushed pause
                var flow = GBHEngland.Flow.GameFlowController.Instance;
                if (flow == null || flow.State == GBHEngland.Flow.GameFlowState.Playing)
                    ToggleInventory();
            }

#if UNITY_EDITOR || DEVELOPMENT_BUILD
            if (Input.GetKeyDown(KeyCode.F8))
                GrantTestGear();
#endif
        }

        /// <summary>Debug: drops the remaining equipment test item into the bag. Editor/dev builds only.</summary>
        private static void GrantTestGear()
        {
            var session = PlayerSession.Instance;
            if (session == null) return;

            ItemData ring = ItemDatabase.Find("test_ring");
            if (ring != null) session.AddItem(ring, 1);
        }

        public bool IsOpen => InventoryUIPanel != null && InventoryUIPanel.activeSelf;

        /// <summary>Close and release the pause if open — called on flow changes (title, death).</summary>
        public void CloseIfOpen()
        {
            if (IsOpen) ToggleInventory();
        }

        /// <summary>
        /// QUEST JOURNAL rail button: close the bag first so the journal's pause push doesn't
        /// stack on top of the bag's own. Wired as a persistent call by the rebuild tool.
        /// </summary>
        public void OnQuestJournalPressed()
        {
            if (IsOpen) ToggleInventory();
            QuestJournalUI.Open();
        }

        /// <summary>MAP OF BRITAIN button: same pause-balance contract as the journal button.</summary>
        public void OnMapOfBritainPressed()
        {
            if (IsOpen) ToggleInventory();
            MapOfBritainUI.Open();
        }

        /// <summary>WIKIBRITAIN button: same pause-balance contract as the map button.</summary>
        public void OnWikiBritainPressed()
        {
            if (IsOpen) ToggleInventory();
            WikiBritainUI.Open();
        }

        /// <summary>PERKS button: same pause-balance contract as the wiki button.</summary>
        public void OnPerksPressed()
        {
            if (IsOpen) ToggleInventory();
            PerkWindowUI.Open();
        }

        /// <summary>Depth-first name search — the rebuild tool nests its buttons under LeftStats.</summary>
        private static Transform FindChildByName(Transform root, string childName)
        {
            if (root == null) return null;
            foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
                if (t.name == childName) return t;
            return null;
        }

        // ── Tooltip action buttons ──────────────────────────────────────────────────────
        // EQUIP moves the item into its paper-doll slot; DROP tosses one unit onto the
        // ground as a DroppedItemPickup that can be picked back up.

        private GameObject _dropButton;
        private GameObject _equipButton;

        /// <summary>Which paper-doll slot the open tooltip came from; null when it came from the bag.</summary>
        private ItemType? _tooltipEquipSlot;

        private void CachePlaceholderButtons()
        {
            if (TooltipPanel == null) return;
            Transform drop = TooltipPanel.transform.Find("DropButton");
            Transform equip = TooltipPanel.transform.Find("EquipButton");
            _dropButton = drop != null ? drop.gameObject : null;
            _equipButton = equip != null ? equip.gameObject : null;

            if (equip != null)
            {
                var btn = equip.GetComponent<Button>();
                if (btn != null) btn.onClick.AddListener(EquipTooltipItem);
            }
            if (drop != null)
            {
                var btn = drop.GetComponent<Button>();
                if (btn != null) btn.onClick.AddListener(DropTooltipItem);
            }
        }

        private void RefreshPlaceholderButtons(ItemData item)
        {
            bool fromDoll = _tooltipEquipSlot.HasValue;
            if (_dropButton != null) _dropButton.SetActive(item != null && !fromDoll);
            if (_equipButton != null)
                _equipButton.SetActive(item != null && !fromDoll && item.IsEquippable);
        }

        private void EquipTooltipItem()
        {
            ItemData item = _tooltipItem;
            var session = PlayerSession.Instance;
            if (item == null || session == null || !item.IsEquippable) return;

            if (session.Equip(item))
                HideTooltip();
        }

        private void UnequipTooltipItem()
        {
            if (_tooltipEquipSlot == null) return;
            PlayerSession.Instance?.Unequip(_tooltipEquipSlot.Value);
            HideTooltip();
        }

        /// <summary>
        /// Tosses one unit of the tooltip's item onto the ground at the player's feet. The
        /// removal runs first — RemoveItem is all-or-nothing, so a unit that is not there
        /// spawns nothing and loses nothing.
        /// </summary>
        private void DropTooltipItem()
        {
            ItemData item = _tooltipItem;
            var session = PlayerSession.Instance;
            var player = GBHEngland.Combat.CombatController.Instance;
            if (item == null || session == null || player == null) return;

            if (!session.RemoveItem(item, 1)) return;

            Vector3 dropAt = player.transform.position + player.FacingDirection * 0.6f;
            GBHEngland.World.DroppedItemPickup.Spawn(item, 1, dropAt);
            HideTooltip();
        }

        // ── Paper doll ──────────────────────────────────────────────────────────────────

        /// <summary>
        /// Binds the paper-doll slots the rebuild tool laid out: EquipSlot0..7 → ItemTypes per
        /// EquipmentSlotMap. Populates EquipmentSlots (dead until the doll existed) and puts a
        /// Button on each slot that opens the worn item's tooltip, where UNEQUIP lives.
        /// </summary>
        private void BuildEquipmentSlots()
        {
            EquipmentSlots.Clear();
            if (PaperDollContainer == null) return;

            for (int i = 0; i < EquipmentSlotMap.SlotCount; i++)
            {
                ItemType type = EquipmentSlotMap.SlotOrder[i];
                Transform slot = PaperDollContainer.Find($"EquipSlot{i}");
                if (slot == null) continue;

                Image img = slot.GetComponent<Image>();
                if (img != null) EquipmentSlots[type] = img;

                var btn = slot.GetComponent<Button>();
                if (btn == null) btn = slot.gameObject.AddComponent<Button>();
                btn.onClick.RemoveAllListeners();
                ItemType captured = type;
                btn.onClick.AddListener(() => ShowEquippedTooltip(captured));
            }

            RefreshEquipmentSlots();
        }

        /// <summary>Draws each slot's worn icon (white on the field) or the empty sunken grey.</summary>
        private void RefreshEquipmentSlots()
        {
            var session = PlayerSession.Instance;
            foreach (var pair in EquipmentSlots)
            {
                ItemData item = session != null ? session.EquippedIn(pair.Key) : null;
                pair.Value.sprite = item != null ? item.Icon : null;
                pair.Value.color = item != null && item.Icon != null ? Color.white : Win95Skin.SlotFill;
            }
        }

        private void ShowEquippedTooltip(ItemType type)
        {
            var session = PlayerSession.Instance;
            ItemData item = session != null ? session.EquippedIn(type) : null;
            if (item == null) return; // empty slot: nothing to show
            _tooltipEquipSlot = type;
            ShowTooltip(item);
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
            if (isActive) GBHEngland.Systems.PauseManager.Push();
            else GBHEngland.Systems.PauseManager.Pop();

            if (isActive)
                RefreshUI();
        }

        private void RefreshUI()
        {
            EnsureInventorySubscription();
            PopulateBackpack();
            RefreshEquipmentSlots();
            RefreshCurrency();
            RefreshLevel();

            if (_boundCharacter == null) return;

            RefreshPaperDollPreview();

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
                int armor = r.Physical + (PlayerSession.Instance != null ? PlayerSession.Instance.TotalArmor() : 0);
                int poison = PlayerSession.Instance != null
                    ? PlayerSession.Instance.EffectivePoisonResistance()
                    : r.Poison;
                ResistancesText.text =
                    $"Armor {armor}\nFire {r.Fire}  Cold {r.Cold}\n" +
                    $"Poison {poison}  Magic {r.Magic}";
            }
        }

        /// <summary>
        /// The idle player sprite on the paper doll's blue block: the character creator's
        /// PlayerClassPreviewUI (added to CharacterSprite by the rebuild tool) fed with the
        /// bound character's class. No-op if the tool has not been run yet.
        /// </summary>
        private void RefreshPaperDollPreview()
        {
            if (PaperDollContainer == null || _boundCharacter == null) return;
            var preview = PaperDollContainer.GetComponentInChildren<PlayerClassPreviewUI>(true);
            if (preview != null)
                preview.ShowClass(_boundCharacter.Class);
        }

        public void ShowTooltip(ItemData item)
        {
            if (TooltipPanel == null || item == null) return;

            TooltipPanel.SetActive(true);
            RefreshUseButton(item);
            RefreshPlaceholderButtons(item);
            if (UnequipButton != null)
                UnequipButton.gameObject.SetActive(_tooltipEquipSlot.HasValue);
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
                if (item.AttackBonus > 0) stats += $"+{item.AttackBonus} Attack\n";
                if (item.PoisonResistance > 0) stats += $"+{item.PoisonResistance} Poison Resistance\n";
                TooltipBody.text = $"{item.Description}\n{stats}".Trim();
            }
        }

        public void HideTooltip()
        {
            if (TooltipPanel != null)
                TooltipPanel.SetActive(false);
            _tooltipEquipSlot = null;
            if (UnequipButton != null)
                UnequipButton.gameObject.SetActive(false);
            RefreshPlaceholderButtons(null);
        }

        /// <summary>Bag-slot click: the tooltip is not from the doll, so EQUIP not UNEQUIP applies.</summary>
        private void ShowBagTooltip(ItemData item)
        {
            _tooltipEquipSlot = null;
            ShowTooltip(item);
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
            // Bottom row, left third: USE · DROP · UNEQUIP/EQUIP share the tooltip's bottom strip.
            rt.anchorMin = new Vector2(0.04f, 0.04f);
            rt.anchorMax = new Vector2(0.34f, 0.20f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            go.AddComponent<Image>();

            var button = go.AddComponent<Button>();
            Win95Skin.StyleButton(button);
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
            tmp.fontSize = 18;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.Center;
            Win95Skin.StyleLabel(tmp);

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

            var player = GBHEngland.Combat.CombatController.Instance;
            if (player != null)
            {
                if (item.HealHP > 0)
                {
                    // Health owns the clamp to MaxHealth and refuses to heal the dead;
                    // CombatController.PushHud copies its value back each frame.
                    var health = player.GetComponent<GBHEngland.Combat.Health>();
                    if (health != null) health.Heal(item.HealHP);
                    else player.CurrentHealth += item.HealHP;
                }

                if (item.HealMana > 0)
                {
                    int max = player.PlayerData != null ? player.PlayerData.MaxManaStamina : 50;
                    player.CurrentMana = Mathf.Min(max, player.CurrentMana + item.HealMana);
                }

                if (item.ManaDamage > 0)
                    player.CurrentMana = Mathf.Max(0, player.CurrentMana - item.ManaDamage);

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
        private static void PlayUseAnimation(GBHEngland.Combat.CombatController player, string trigger)
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

        /// <summary>
        /// Fills the backpack grid from PlayerSession's live inventory. The slot GameObjects
        /// (BagSlot0..35) already exist in the scene as plain framed Images — this sets each
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
                icon.color = item != null && item.Icon != null ? Color.white : Win95Skin.SlotFill;
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
                button.onClick.AddListener(() => ShowBagTooltip(item));
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
            rt.anchoredPosition = new Vector2(-2, 1);
            rt.sizeDelta = new Vector2(40, 28);

            // Big enough to read over a busy icon: white bold with a black outline.
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.color = Color.white;
            tmp.fontSize = 24;
            tmp.fontStyle = FontStyles.Bold;
            tmp.alignment = TextAlignmentOptions.BottomRight;
            tmp.raycastTarget = false;
            var outline = go.AddComponent<Outline>();
            outline.effectColor = Color.black;
            outline.effectDistance = new Vector2(2f, -2f);
            return tmp;
        }
    }
}
