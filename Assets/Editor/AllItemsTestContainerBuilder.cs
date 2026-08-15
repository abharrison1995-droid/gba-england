using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

/// <summary>
/// Builds a reusable World Palette test chest containing one of every ItemData under
/// Resources/Items. Re-running edits the existing prefab and preset in place, preserving GUIDs.
/// </summary>
public static class AllItemsTestContainerBuilder
{
    private const string ItemsFolder = "Assets/Resources/Items";
    private const string PrefabFolder = "Assets/Prefabs/ModernBritain/Containers";
    private const string PrefabPath = PrefabFolder + "/Container_AllItems_Test.prefab";
    private const string PresetPath = "Assets/Data/Presets/Preset_Container_AllItems_Test.asset";
    private const string VisualPrefabPath = "Assets/3DModels/Animated Chest/OldChest/Chest.prefab";

    [MenuItem("Tools/Content/Build All-Items Test Container")]
    public static void Build()
    {
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        EnsureFolder(PrefabFolder);

        List<ItemData> items = FindItems();
        if (items.Count == 0)
        {
            EditorUtility.DisplayDialog("Build All-Items Test Container",
                $"No ItemData assets were found under {ItemsFolder}.", "OK");
            return;
        }

        bool prefabExisted = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath) != null;
        GameObject root = prefabExisted
            ? PrefabUtility.LoadPrefabContents(PrefabPath)
            : new GameObject("Container_AllItems_Test");

        try
        {
            ConfigurePrefab(root, items);
            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
        }
        finally
        {
            if (prefabExisted) PrefabUtility.UnloadPrefabContents(root);
            else UnityEngine.Object.DestroyImmediate(root);
        }

        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
        PlacementPreset preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(PresetPath);
        if (preset == null)
        {
            preset = ScriptableObject.CreateInstance<PlacementPreset>();
            AssetDatabase.CreateAsset(preset, PresetPath);
        }

        preset.Label = "TEST - All Items Container";
        preset.Category = PlacementPreset.PlacementCategory.Chest;
        preset.Prefab = prefab;
        EditorUtility.SetDirty(preset);

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log($"All-items test container: {items.Count} unique ItemData assets wired into " +
                  $"{PrefabPath}; World Palette preset refreshed at {PresetPath}.");
        EditorUtility.DisplayDialog("Build All-Items Test Container",
            $"Built a test chest containing {items.Count} items.\n\n" +
            "Open Tools → World Palette, choose Chests, then place " +
            "'TEST - All Items Container' while editing your chunk prefab.", "OK");
    }

    private static List<ItemData> FindItems()
    {
        var byId = new Dictionary<string, ItemData>(StringComparer.OrdinalIgnoreCase);
        foreach (string guid in AssetDatabase.FindAssets("t:ItemData", new[] { ItemsFolder }))
        {
            ItemData item = AssetDatabase.LoadAssetAtPath<ItemData>(AssetDatabase.GUIDToAssetPath(guid));
            if (item == null || string.IsNullOrWhiteSpace(item.ItemID)) continue;

            string id = item.ItemID.Trim();
            if (byId.ContainsKey(id))
            {
                Debug.LogWarning($"All-items test container: duplicate ItemID '{id}'; " +
                                 $"keeping '{byId[id].name}' and skipping '{item.name}'.");
                continue;
            }
            byId.Add(id, item);
        }

        var items = new List<ItemData>(byId.Values);
        items.Sort((a, b) => string.Compare(a.ItemID, b.ItemID, StringComparison.OrdinalIgnoreCase));
        return items;
    }

    private static void ConfigurePrefab(GameObject root, List<ItemData> items)
    {
        root.name = "Container_AllItems_Test";

        LootChest chest = root.GetComponent<LootChest>();
        if (chest == null) chest = root.AddComponent<LootChest>();
        chest.ChestName = "All Items Test Container";
        chest.Loot = new LootDrop[items.Count];
        for (int i = 0; i < items.Count; i++)
            chest.Loot[i] = new LootDrop { Item = items[i], Quantity = 1 };

        Interactable interactable = root.GetComponent<Interactable>();
        if (interactable == null) interactable = root.AddComponent<Interactable>();
        interactable.Prompt = "Open All Items Test Container";
        interactable.Reusable = true;
        interactable.InteractRange = 2.75f;

        Transform visual = root.transform.Find("ChestVisual");
        if (visual == null)
        {
            GameObject source = AssetDatabase.LoadAssetAtPath<GameObject>(VisualPrefabPath);
            if (source != null)
            {
                GameObject instance = (GameObject)PrefabUtility.InstantiatePrefab(source);
                instance.name = "ChestVisual";
                instance.transform.SetParent(root.transform, false);
                visual = instance.transform;
            }
            else
            {
                Debug.LogWarning($"All-items test container: visual prefab missing at {VisualPrefabPath}; " +
                                 "the loot works but the prefab has no visible chest.");
            }
        }

        chest.ChestAnimation = visual != null ? visual.GetComponentInChildren<Animation>(true) : null;
        chest.Lid = null;
        EditorUtility.SetDirty(chest);
        EditorUtility.SetDirty(interactable);
    }

    private static void EnsureFolder(string assetFolder)
    {
        if (AssetDatabase.IsValidFolder(assetFolder)) return;
        string[] parts = assetFolder.Split('/');
        string current = parts[0];
        for (int i = 1; i < parts.Length; i++)
        {
            string next = current + "/" + parts[i];
            if (!AssetDatabase.IsValidFolder(next)) AssetDatabase.CreateFolder(current, parts[i]);
            current = next;
        }
    }
}
