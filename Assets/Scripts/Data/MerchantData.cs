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

    [Serializable]
    public class MerchantPurchaseRule
    {
        public ItemData Item;

        [Tooltip("Fixed payout in pounds. Ignored when RandomMax is above 0.")]
        public int FixedPrice;

        [Tooltip("Inclusive random payout range. Leave both at 0 for a fixed-price rule.")]
        public int RandomMin;
        public int RandomMax;

        [Tooltip("Optional status line used when a random payout lands from RandomMin through 3.")]
        public string LowResultMessage;
        [Tooltip("Optional status line used when a random payout lands from 4 through 6.")]
        public string MidResultMessage;
        [Tooltip("Optional status line used when a random payout lands from 7 upward.")]
        public string HighResultMessage;

        public bool IsRandom => RandomMax > 0;

        public int PreviewPrice => IsRandom ? Mathf.Max(0, RandomMin) : Mathf.Max(0, FixedPrice);
        public int MaximumPrice => IsRandom ? Mathf.Max(0, RandomMax) : Mathf.Max(0, FixedPrice);

        public int RollPrice()
        {
            if (!IsRandom) return Mathf.Max(0, FixedPrice);
            int min = Mathf.Max(1, RandomMin);
            int max = Mathf.Max(min, RandomMax);
            return UnityEngine.Random.Range(min, max + 1);
        }

        public string MessageFor(int payout)
        {
            if (payout <= 3) return LowResultMessage;
            if (payout <= 6) return MidResultMessage;
            return HighResultMessage;
        }
    }

    /// <summary>
    /// Reusable shop definition. Stock is unlimited in the first shop pass, so this asset holds
    /// catalogue and pricing only and introduces no save state.
    /// </summary>
    [CreateAssetMenu(fileName = "NewMerchantData", menuName = "GBH England/Data/Merchant Data")]
    public class MerchantData : ScriptableObject
    {
        public const int ResalePercent = 30;

        public string MerchantName;
        public List<MerchantStockEntry> Stock = new List<MerchantStockEntry>();

        [Header("Items This Merchant Buys")]
        [Tooltip("Item types accepted from the player. Quest items are always refused.")]
        public ItemType[] AcceptedTypes;

        [Tooltip("Per-item specialist payouts. These take precedence over the ordinary 30% rule.")]
        public List<MerchantPurchaseRule> PurchaseRules = new List<MerchantPurchaseRule>();

        [Tooltip("Sell-only merchants open without a BUY tab.")]
        public bool SellOnly;

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
            if (item == null || !item.Tradeable || item.Type == ItemType.Quest) return false;
            MerchantPurchaseRule rule = FindPurchaseRule(item);
            if (rule != null) return rule.PreviewPrice > 0;
            if (ResalePrice(item) <= 0) return false;
            if (AcceptedTypes == null) return false;

            for (int i = 0; i < AcceptedTypes.Length; i++)
                if (AcceptedTypes[i] == item.Type) return true;

            return false;
        }

        public MerchantPurchaseRule FindPurchaseRule(ItemData item)
        {
            if (item == null || PurchaseRules == null) return null;
            for (int i = 0; i < PurchaseRules.Count; i++)
            {
                MerchantPurchaseRule rule = PurchaseRules[i];
                if (rule != null && rule.Item == item) return rule;
            }
            return null;
        }

        public int SalePreviewPrice(ItemData item)
        {
            MerchantPurchaseRule rule = FindPurchaseRule(item);
            return rule != null ? rule.PreviewPrice : ResalePrice(item);
        }
    }
}
