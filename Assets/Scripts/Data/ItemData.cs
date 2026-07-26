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
