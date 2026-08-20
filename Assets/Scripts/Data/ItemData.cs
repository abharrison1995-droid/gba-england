using UnityEngine;

namespace GBHEngland.Data
{
    public enum ItemType
    {
        Weapon = 0,
        Shield = 1,
        Head = 2,
        Chest = 3,
        Cloak = 4,
        Ring = 5,
        Boots = 6,
        Consumable = 7,
        Quest = 8,
        Legs = 9,
        Belt = 10,
        Junk = 11
    }

    /// <summary>
    /// Base configuration for Items, suitable for Inventory Paper Doll mapping.
    /// </summary>
    [CreateAssetMenu(fileName = "NewItemData", menuName = "GBH England/Data/Item Data")]
    public class ItemData : ScriptableObject
    {
        public string ItemID;
        public string ItemName;
        [TextArea] public string Description;
        public Sprite Icon;

        public ItemType Type;

        [Header("Class Gate")]
        [Tooltip("If empty, any class can use. Otherwise only listed classes.")]
        public PlayerClass[] AllowedClasses;
        
        [Header("Stats")]
        public int Value;
        public int Damage; // For weapons
        public int Armor;  // For wearables

        // ── Stacking and use ────────────────────────────────────────────────────────────────
        // Appended, per CLAUDE.md §3: every existing ItemData .asset carries no value for these,
        // so Unity applies the field initializers below and nothing already authored changes.
        // Stackable defaults to false, which is exactly how the inventory behaved before.
        [Header("Stacking")]
        [Tooltip("Several of these share one inventory slot. Off means every one taken takes its " +
                 "own slot, which is what every item authored so far does.")]
        public bool Stackable = false;

        [Tooltip("Most that fit in one stack. 0 means unlimited. Only consulted when Stackable " +
                 "is on — a non-stackable item is always one per slot whatever this says.")]
        public int MaxStack = 0;

        [Header("Consumable")]
        [Tooltip("Health restored when used. Clamped to the player's maximum.")]
        public int HealHP;

        [Tooltip("Mana restored when used. Clamped to the player's maximum.")]
        public int HealMana;

        [Tooltip("Animator trigger fired on the player when this is used. Leave empty for none; " +
                 "a name the player's controller does not declare is ignored rather than warned " +
                 "about, the way locomotion parameters are.")]
        public string UseAnimationTrigger = "";

        // Appended: existing ItemData assets deserialize both bonuses as zero.
        [Header("Wearable Bonuses")]
        [Tooltip("Flat melee attack added while this item is equipped, regardless of slot.")]
        public int AttackBonus;

        [Tooltip("Added to the character sheet's Poison resistance while equipped.")]
        public int PoisonResistance;

        // Appended: absent in older ItemData assets, where the initializer keeps ordinary items
        // tradeable. Development/story content opts out explicitly.
        [Header("Commerce")]
        [Tooltip("Off for development or story-only items that must never appear in a sell list.")]
        public bool Tradeable = true;

        // Appended: existing ItemData assets deserialize this as zero and keep their old behaviour.
        [Header("Consumable Costs")]
        [Tooltip("Mana removed when this consumable is used, after any restoration. Clamped at zero.")]
        public int ManaDamage;

        // Appended: existing ItemData assets deserialize this as zero and keep their old behaviour.
        [Tooltip("Stamina removed when this consumable is used, after any restoration. Clamped at zero.")]
        public int StaminaDamage;

        // Appended: Crown & Royal Arena stats. Older items deserialize all as zero/false.
        [Header("Crown & Royal Stats")]
        [Tooltip("Added to the character sheet's Fire resistance while equipped.")]
        public int FireResistance;

        [Tooltip("Passive HP regenerated per second while equipped (e.g. 0.1666f for 1 HP per 6s).")]
        public float HealthRegenPerSecond;

        [Tooltip("Flat Max HP added while this item is equipped.")]
        public int MaxHealthBonus;

        [Tooltip("Flat Max Mana added while this item is equipped.")]
        public int MaxManaBonus;

        [Tooltip("Flat Magic Damage added to spells and ranged magic attacks while equipped.")]
        public int MagicDamageBonus;

        [Tooltip("If true, only ONE crown can be purchased per save file.")]
        public bool IsUniqueCrown;

        /// <summary>Can go in a visible paper-doll slot. Consumables are used, quests are carried.</summary>
        public bool IsEquippable =>
            Type != ItemType.Shield && Type != ItemType.Consumable
            && Type != ItemType.Quest && Type != ItemType.Junk;

        public bool CanBeUsedBy(PlayerClass playerClass)
        {
            if (AllowedClasses == null || AllowedClasses.Length == 0) return true;
            for (int i = 0; i < AllowedClasses.Length; i++)
            {
                if (AllowedClasses[i] == playerClass) return true;
            }
            return false;
        }
    }
}
