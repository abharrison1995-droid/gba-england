using System.Collections.Generic;
using System.Text;
using ExiledAlvaston.Data;
using UnityEditor;
using UnityEngine;

/// <summary>Authoring checks for merchant catalogues and their economy invariants.</summary>
public static class MerchantValidator
{
    [MenuItem("Tools/Content/Validate Merchants")]
    private static void ValidateAll()
    {
        string[] guids = AssetDatabase.FindAssets("t:MerchantData");
        int errors = 0;
        int warnings = 0;

        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            MerchantData merchant = AssetDatabase.LoadAssetAtPath<MerchantData>(path);
            if (merchant == null) continue;

            List<string> problems = Validate(merchant, out int merchantErrors);
            errors += merchantErrors;
            warnings += problems.Count - merchantErrors;
            if (problems.Count == 0) continue;

            var report = new StringBuilder("Validate Merchants — ").AppendLine(path);
            for (int i = 0; i < problems.Count; i++) report.AppendLine("  " + problems[i]);
            if (merchantErrors > 0) Debug.LogError(report.ToString().TrimEnd(), merchant);
            else Debug.LogWarning(report.ToString().TrimEnd(), merchant);
        }

        Debug.Log($"Validate Merchants: {guids.Length} asset(s) checked — " +
                  $"{errors} error(s), {warnings} warning(s).");
    }

    public static List<string> Validate(MerchantData merchant, out int errors)
    {
        var problems = new List<string>();
        errors = 0;

        if (merchant == null)
        {
            problems.Add("[Error] Merchant asset is null.");
            errors++;
            return problems;
        }

        if (string.IsNullOrWhiteSpace(merchant.MerchantName))
        {
            problems.Add("[Error] MerchantName is blank.");
            errors++;
        }

        if (merchant.Stock == null || merchant.Stock.Count == 0)
        {
            problems.Add("[Error] Stock is empty.");
            errors++;
            return problems;
        }

        var seen = new HashSet<ItemData>();
        for (int i = 0; i < merchant.Stock.Count; i++)
        {
            MerchantStockEntry entry = merchant.Stock[i];
            if (entry == null || entry.Item == null)
            {
                problems.Add($"[Error] Stock entry {i} has no item.");
                errors++;
                continue;
            }

            if (!seen.Add(entry.Item))
            {
                problems.Add($"[Error] '{entry.Item.ItemName}' appears in stock more than once.");
                errors++;
            }

            int shelf = merchant.PurchasePrice(entry);
            if (shelf <= 0)
            {
                problems.Add($"[Error] '{entry.Item.ItemName}' has no positive shelf price.");
                errors++;
            }

            if (entry.Item.Type == ItemType.Quest || !entry.Item.Tradeable)
            {
                problems.Add($"[Error] '{entry.Item.ItemName}' is a quest/non-tradeable item in stock.");
                errors++;
            }

            int resale = MerchantData.ResalePrice(entry.Item);
            if (merchant.Accepts(entry.Item) && resale >= shelf)
            {
                problems.Add($"[Error] '{entry.Item.ItemName}' sells here for {shelf} but this " +
                             $"merchant buys it for {resale}, creating a money loop.");
                errors++;
            }

            if (entry.PriceOverride > 0 && entry.PriceOverride != entry.Item.Value)
                problems.Add($"[Warning] '{entry.Item.ItemName}' overrides base value " +
                             $"{entry.Item.Value} with shelf price {entry.PriceOverride}.");
        }

        if (merchant.AcceptedTypes == null || merchant.AcceptedTypes.Length == 0)
            problems.Add("[Warning] Merchant accepts no item types from the player.");

        return problems;
    }
}
