using System;
using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    [Serializable]
    public class MerchantStockEntry
    {
        public ItemData Item;

        [Tooltip("Shelf price in pounds. 0 uses the item's canonical Value.")]
        public int PriceOverride;
    }

    /// <summary>
    /// Reusable shop definition. Stock is unlimited in the first shop pass, so this asset holds
    /// catalogue and pricing only and introduces no save state.
    /// </summary>
    [CreateAssetMenu(fileName = "NewMerchantData", menuName = "ExiledAlvaston/Data/Merchant Data")]
    public class MerchantData : ScriptableObject
    {
        public const int ResalePercent = 30;

        public string MerchantName;
        public List<MerchantStockEntry> Stock = new List<MerchantStockEntry>();

        [Header("Items This Merchant Buys")]
        [Tooltip("Item types accepted from the player. Quest items are always refused.")]
        public ItemType[] AcceptedTypes;

        public int PurchasePrice(MerchantStockEntry entry)
        {
            if (entry == null || entry.Item == null) return 0;
            return entry.PriceOverride > 0 ? entry.PriceOverride : Mathf.Max(0, entry.Item.Value);
        }

        public static int ResalePrice(ItemData item)
        {
            if (item == null || !item.Tradeable || item.Type == ItemType.Quest || item.Value <= 0) return 0;
            return Mathf.FloorToInt(item.Value * (ResalePercent / 100f));
        }

        public bool Accepts(ItemData item)
        {
            if (item == null || !item.Tradeable || item.Type == ItemType.Quest || ResalePrice(item) <= 0) return false;
            if (AcceptedTypes == null) return false;

            for (int i = 0; i < AcceptedTypes.Length; i++)
                if (AcceptedTypes[i] == item.Type) return true;

            return false;
        }
    }
}
