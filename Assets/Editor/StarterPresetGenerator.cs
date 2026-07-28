using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;

/// <summary>
/// Fills the World Palette with a usable starting set, so it is not an empty grid the first time
/// it is opened.
///
/// Run via: Tools → GBA → Content → Create Starter Presets
///
/// Idempotent by design: an asset that already exists is left completely alone, never overwritten.
/// Presets are meant to be tuned by hand once created, and a generator that reset them on every
/// run would make that pointless.
/// </summary>
public static class StarterPresetGenerator
{
    private const string PresetFolder = "Assets/Data/Presets";
    private const string VehicleDataPath = "Assets/Data/Vehicles/Limey_EBike_Data.asset";
    private const string EBikePrefabPath = "Assets/Prefabs/ModernBritain/EBike.prefab";
    private const string ChestPrefabPath = "Assets/3DModels/Animated Chest/OldChest/Chest.prefab";
    private const string EnemyPrefabFolder = "Assets/Prefabs/Enemies";

    [MenuItem("Tools/GBA/Content/Create Starter Presets")]
    public static void Run()
    {
        EnsureFolder(PresetFolder);

        var created = new List<string>();
        var skipped = new List<string>();
        var notes = new List<string>();

        // ── Enemies ──────────────────────────────────────────────────────────────────────
        CreateEnemyPreset("Orc 1", "Enemy_Orc1", created, skipped, notes);
        CreateEnemyPreset("Orc 2", "Enemy_Orc2", created, skipped, notes);
        CreateEnemyPreset("Orc 3", "Enemy_Orc3", created, skipped, notes);
        CreateEnemyPreset("Bot Wheel", "Enemy_BotWheel", created, skipped, notes);

        // ── NPCs ─────────────────────────────────────────────────────────────────────────
        // Placeholder capsules for now: none of these have sheets yet (ART_PIPELINE.md §7.3).
        // When their art lands, set NpcController on the preset and every future placement
        // animates — no change to the palette or the builders needed.
        CreateNpcPreset("Villager", "Villager", created, skipped);
        CreateNpcPreset("Councillor Mosley", "Councillor Mosley", created, skipped);
        CreateNpcPreset("Daniel Pauls", "Daniel Pauls", created, skipped);
        CreateNpcPreset("Tracksuit Geezer", "Tracksuit Geezer", created, skipped);
        CreateNpcPreset("Angry Squirrel", "Angry Squirrel", created, skipped);
        CreateNpcPreset("Roaming Pharmacist", "Roaming Pharmacist", created, skipped);

        // ── Chest ────────────────────────────────────────────────────────────────────────
        Create("Chest", PlacementPreset.PlacementCategory.Chest, created, skipped, p =>
        {
            p.ChestName = "Chest";
            p.ChestVisualPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(ChestPrefabPath);
            if (p.ChestVisualPrefab == null)
                notes.Add($"Chest: {ChestPrefabPath} not found — the preset falls back to the plain box+lid.");
        });

        // ── Portal ───────────────────────────────────────────────────────────────────────
        Create("Portal to Manor Cellars", PlacementPreset.PlacementCategory.Portal, created, skipped, p =>
        {
            p.TargetChunk = LoadChunk("Manor_Cellars_Data");
            p.PortalPrompt = "Enter the cellars";
            p.PortalSpawnPosition = new Vector3(0f, 0f, -8f);
            if (p.TargetChunk == null)
                notes.Add("Portal: Manor_Cellars_Data not found — assign a TargetChunk before using it.");
        });

        // ── Spawn point ──────────────────────────────────────────────────────────────────
        Create("Player Spawn", PlacementPreset.PlacementCategory.SpawnPoint, created, skipped, p =>
        {
            p.SpawnPointId = "";
        });

        // ── Vehicle ──────────────────────────────────────────────────────────────────────
        VehicleData ebike = EnsureEBikeData(notes);
        Create("Limey E-Bike", PlacementPreset.PlacementCategory.Vehicle, created, skipped, p =>
        {
            p.Vehicle = ebike;
        });

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        var log = new System.Text.StringBuilder();
        log.AppendLine("Create Starter Presets");
        log.AppendLine("──────────────────────");
        log.AppendLine($"  created: {created.Count}");
        foreach (string c in created) log.AppendLine("    + " + c);
        if (skipped.Count > 0)
        {
            log.AppendLine($"  left alone (already exist): {skipped.Count}");
            foreach (string s in skipped) log.AppendLine("    = " + s);
        }
        if (notes.Count > 0)
        {
            log.AppendLine("  notes:");
            foreach (string n in notes) log.AppendLine("    ! " + n);
        }
        Debug.Log(log.ToString());

        EditorUtility.DisplayDialog("Create Starter Presets",
            $"{created.Count} created, {skipped.Count} already existed, {notes.Count} note(s).\n\n" +
            "Open Tools → GBA → World Palette to use them. Detail in the Console.", "OK");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void CreateEnemyPreset(string label, string prefabName,
        List<string> created, List<string> skipped, List<string> notes)
    {
        Create(label, PlacementPreset.PlacementCategory.Enemy, created, skipped, p =>
        {
            string path = $"{EnemyPrefabFolder}/{prefabName}.prefab";
            p.EnemyPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (p.EnemyPrefab == null)
                notes.Add($"{label}: {path} not found — run Tools → GBA → Danger Zone → " +
                          "Build Enemy Prefabs first, then assign it.");
        });
    }

    private static void CreateNpcPreset(string label, string npcName,
        List<string> created, List<string> skipped)
    {
        Create(label, PlacementPreset.PlacementCategory.NPC, created, skipped, p =>
        {
            p.NpcName = npcName;
        });
    }

    /// <summary>
    /// Creates the VehicleData the e-bike spawner needs. CLAUDE.md §11 records an earlier attempt
    /// that left Home_Alvaston_Data pointing at one which was never written to disk, so this
    /// confirms the asset is really there before handing it back.
    /// </summary>
    private static VehicleData EnsureEBikeData(List<string> notes)
    {
        var existing = AssetDatabase.LoadAssetAtPath<VehicleData>(VehicleDataPath);
        if (existing != null) return existing;

        var chassis = AssetDatabase.LoadAssetAtPath<GameObject>(EBikePrefabPath);
        if (chassis == null)
        {
            notes.Add($"Limey E-Bike: {EBikePrefabPath} not found, so no VehicleData was created. " +
                      "The vehicle preset will need one assigning by hand.");
            return null;
        }

        EnsureFolder("Assets/Data/Vehicles");

        var data = ScriptableObject.CreateInstance<VehicleData>();
        data.VehicleName = "Limey E-Bike";
        data.ChassisPrefab = chassis;
        data.SpeedMultiplier = 2f;
        data.IsNickable = true;
        data.ParkedPrompt = "Nick this e-bike";
        data.ParkedHeight = 0.9f;
        AssetDatabase.CreateAsset(data, VehicleDataPath);
        AssetDatabase.SaveAssets();

        var written = AssetDatabase.LoadAssetAtPath<VehicleData>(VehicleDataPath);
        if (written == null)
        {
            notes.Add($"Limey E-Bike: VehicleData did not survive being written to {VehicleDataPath}.");
            return null;
        }

        notes.Add($"Created {VehicleDataPath} — this is the asset CLAUDE.md §11 lists as missing.");
        return written;
    }

    private static void Create(string label, PlacementPreset.PlacementCategory category,
        List<string> created, List<string> skipped, System.Action<PlacementPreset> configure)
    {
        string path = $"{PresetFolder}/Preset_{Sanitise(label)}.asset";
        if (AssetDatabase.LoadAssetAtPath<PlacementPreset>(path) != null)
        {
            skipped.Add(label);
            return;
        }

        var preset = ScriptableObject.CreateInstance<PlacementPreset>();
        preset.Label = label;
        preset.Category = category;
        configure(preset);

        AssetDatabase.CreateAsset(preset, path);
        created.Add(label);
    }

    private static MapChunkData LoadChunk(string assetName)
    {
        string path = $"Assets/Data/Chunks/{assetName}.asset";
        return AssetDatabase.LoadAssetAtPath<MapChunkData>(path);
    }

    private static string Sanitise(string label)
    {
        return label.Replace(" ", "").Replace("/", "").Replace("\\", "");
    }

    private static void EnsureFolder(string assetFolder)
    {
        if (AssetDatabase.IsValidFolder(assetFolder)) return;

        string[] parts = assetFolder.Split('/');
        string running = parts[0];
        for (int i = 1; i < parts.Length; i++)
        {
            string next = $"{running}/{parts[i]}";
            if (!AssetDatabase.IsValidFolder(next))
                AssetDatabase.CreateFolder(running, parts[i]);
            running = next;
        }
    }
}
