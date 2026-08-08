using UnityEngine;

namespace ExiledAlvaston.Data
{
    public enum ItemType
    {
        Weapon,
        Shield,
        Head,
        Chest,
        Cloak,
        Ring,
        Boots,
        Consumable,
        Quest
    }

    /// <summary>
    /// Base configuration for Items, suitable for Inventory Paper Doll mapping.
    /// </summary>
    [CreateAssetMenu(fileName = "NewItemData", menuName = "ExiledAlvaston/Data/Item Data")]
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

        /// <summary>Can go in a paper-doll slot. Consumables are used, quests are carried.</summary>
        public bool IsEquippable => Type != ItemType.Consumable && Type != ItemType.Quest;

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
