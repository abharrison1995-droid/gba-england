using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;

/// <summary>
/// Fills the World Palette with a usable starting set, so it is not an empty grid the first time
/// it is opened.
///
/// Run via: Tools → Content → Create Starter Presets
///
/// Idempotent by design: an asset that already exists is left completely alone, never overwritten.
/// Presets are meant to be tuned by hand once created, and a generator that reset them on every
/// run would make that pointless.
/// </summary>
public static class StarterPresetGenerator
{
    private const string PresetFolder = "Assets/Data/Presets";
    private const string ResourcesFolder = "Assets/Resources";
    private const string LibraryPath = ResourcesFolder + "/" + PlacementPresetLibrary.ResourcePath + ".asset";
    private const string VehicleDataPath = "Assets/Data/Vehicles/Limey_EBike_Data.asset";
    private const string EBikePrefabPath = "Assets/Prefabs/ModernBritain/EBike.prefab";
    private const string ChestPrefabPath = "Assets/3DModels/Animated Chest/OldChest/Chest.prefab";

    [MenuItem("Tools/Content/Create Starter Presets")]
    public static void Run()
    {
        EnsureFolder(PresetFolder);

        var created = new List<string>();
        var skipped = new List<string>();
        var filled = new List<string>();
        var notes = new List<string>();

        // ── NPCs ─────────────────────────────────────────────────────────────────────────
        // Each carries the art subject its sheets are named after (ART_PIPELINE.md §7.3), so the
        // art importer can find the preset and wire the controller and sprite to it. NpcHeight is
        // left at 0 on every one of them on purpose — see PlacementPreset.NpcHeight.
        foreach (NpcSpec spec in StarterNpcs)
            CreateNpcPreset(spec, created, skipped);

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

        // After creation, so a preset made moments ago already carries its subject and is skipped
        // rather than written twice.
        BackfillNpcPresets(filled);
        GenerateAmbientConversations(filled);
        EnsureLibrary(created, filled, notes);

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        var log = new System.Text.StringBuilder();
        log.AppendLine("Create Starter Presets");
        log.AppendLine("──────────────────────");
        log.AppendLine($"  created: {created.Count}");
        foreach (string c in created) log.AppendLine("    + " + c);
        if (filled.Count > 0)
        {
            log.AppendLine($"  filled in blank fields on existing presets: {filled.Count}");
            foreach (string f in filled) log.AppendLine("    ~ " + f);
        }
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
            $"{created.Count} created, {filled.Count} back-filled, {skipped.Count} already existed, " +
            $"{notes.Count} note(s).\n\n" +
            "Open Tools → World Palette to use them. Detail in the Console.", "OK");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// One starter NPC, and the two things about it that cannot be derived from its label: the art
    /// subject its sprite sheets are named after, and whether it wanders. Shared by the create path
    /// and the back-fill below so the two can never disagree.
    /// </summary>
    private struct NpcSpec
    {
        public readonly string Label;
        public readonly string NpcName;
        public readonly string ArtSubject;
        public readonly bool Roams;

        public NpcSpec(string label, string npcName, string artSubject, bool roams)
        {
            Label = label;
            NpcName = npcName;
            ArtSubject = artSubject;
            Roams = roams;
        }
    }

    private static readonly NpcSpec[] StarterNpcs =
    {
        new NpcSpec("Villager",           "Villager",           "villager",    true),
        // Mosley is a quest-giver who stands and talks (§7.3), so he holds his pitch.
        new NpcSpec("Councillor Mosley",  "Councillor Mosley",  "mosley",      false),
        // Daniel Pauls must not wander: the magic tutorial places him on the DanielPaulsSpawn
        // marker in the chunk prefab and expects to find him there.
        new NpcSpec("Daniel Pauls",       "Daniel Pauls",       "danielpauls", false),
        new NpcSpec("Tracksuit Geezer",   "Tracksuit Geezer",   "underhoused", false),
        new NpcSpec("Angry Squirrel",     "Angry Squirrel",     "squirrel",    true),
        new NpcSpec("Roaming Pharmacist", "Roaming Pharmacist", "pharmacist",  true),
    };

    private static void CreateNpcPreset(NpcSpec spec, List<string> created, List<string> skipped)
    {
        Create(spec.Label, PlacementPreset.PlacementCategory.NPC, created, skipped, p =>
        {
            p.NpcName = spec.NpcName;
            p.ArtSubject = spec.ArtSubject;
            p.Roams = spec.Roams;
        });
    }

    /// <summary>
    /// Fills in the fields that were added after these presets were first generated.
    ///
    /// <see cref="Create"/> leaves an existing asset completely alone, deliberately — presets are
    /// meant to be tuned by hand, and a generator that reset them every run would make that
    /// pointless. The cost is that a preset created before a field existed never picks it up, and
    /// all six NPC presets predate ArtSubject and Roams.
    ///
    /// This closes that gap without giving the guarantee up: a preset is only touched while its
    /// ArtSubject is still blank, which is true exactly once in its life. Anything tuned after
    /// that first run — including turning Roams back off — survives every later run.
    /// </summary>
    private static void BackfillNpcPresets(List<string> filled)
    {
        foreach (NpcSpec spec in StarterNpcs)
        {
            string path = $"{PresetFolder}/Preset_{Sanitise(spec.Label)}.asset";
            var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(path);

            if (preset == null) continue;                            // never created, or renamed
            if (!string.IsNullOrEmpty(preset.ArtSubject)) continue;  // already been through here

            preset.ArtSubject = spec.ArtSubject;
            preset.Roams = spec.Roams;
            EditorUtility.SetDirty(preset);

            filled.Add($"{spec.Label}: subject '{spec.ArtSubject}', roams {(spec.Roams ? "yes" : "no")}");
        }
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

    /// <summary>
    /// Creates and fills the one preset library the running game can actually load.
    ///
    /// Presets live outside Resources/ deliberately — everything reachable from there ships in the
    /// build, and the chest preset alone would drag a 45 MB prop pack in with it. So a small asset
    /// sits in Resources/ instead, pointing at only the presets runtime code has to resolve by
    /// name. Today that is the magic tutorial's two characters.
    ///
    /// An entry already pointing at a preset is never re-pointed: the whole reason lookup is keyed
    /// rather than named is so the target can be changed by hand and stay changed.
    /// </summary>
    private static void EnsureLibrary(List<string> created, List<string> filled, List<string> notes)
    {
        EnsureFolder(ResourcesFolder);

        var library = AssetDatabase.LoadAssetAtPath<PlacementPresetLibrary>(LibraryPath);
        if (library == null)
        {
            library = ScriptableObject.CreateInstance<PlacementPresetLibrary>();
            AssetDatabase.CreateAsset(library, LibraryPath);
            created.Add($"PlacementPresetLibrary ({LibraryPath})");
        }

        bool changed = false;
        changed |= EnsureLibraryEntry(library, MagicTutorial.DanielPresetKey, "Daniel Pauls", filled, notes);
        changed |= EnsureLibraryEntry(library, MagicTutorial.GeezerPresetKey, "Tracksuit Geezer", filled, notes);

        if (changed) EditorUtility.SetDirty(library);
    }

    private static bool EnsureLibraryEntry(PlacementPresetLibrary library, string key,
        string presetLabel, List<string> filled, List<string> notes)
    {
        PlacementPresetLibrary.Entry entry =
            library.Entries.Find(e => e != null && e.Key == key);

        if (entry != null && entry.Preset != null) return false;

        string path = $"{PresetFolder}/Preset_{Sanitise(presetLabel)}.asset";
        var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(path);
        if (preset == null)
        {
            notes.Add($"Preset library: nothing at {path}, so '{key}' is unresolved — the magic " +
                      "tutorial will log an error instead of spawning that character.");
            return false;
        }

        if (entry == null)
        {
            entry = new PlacementPresetLibrary.Entry { Key = key };
            library.Entries.Add(entry);
        }
        entry.Preset = preset;

        filled.Add($"preset library: '{key}' → {presetLabel}");
        return true;
    }

    /// <summary>
    /// Turns any preset's typed ambient line into a real conversation asset.
    ///
    /// Ungated, unlike the back-fill above, and over every preset rather than only the starter
    /// NPCs. It acts only where a line has been typed and no conversation is linked, which is
    /// already exactly "asked for, not yet done" — so it is safe to run every time, and it picks up
    /// a line typed into a preset that was back-filled months ago.
    /// </summary>
    private static void GenerateAmbientConversations(List<string> filled)
    {
        foreach (string guid in AssetDatabase.FindAssets("t:PlacementPreset"))
        {
            var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(
                AssetDatabase.GUIDToAssetPath(guid));
            if (preset == null) continue;

            // Both outcomes change the preset, so both belong in the summary. Reporting only the
            // generated ones left the adopt path — which still writes preset.Conversation and marks
            // the asset dirty — showing up nowhere but a console warning, in a run that also emits
            // one "has no Speaker" warning per preset.
            if (PresetDialogueTools.EnsureAmbientConversation(preset, out bool adopted))
                filled.Add($"{preset.Label}: conversation generated from its ambient line");
            else if (adopted)
                filled.Add($"{preset.Label}: linked to the conversation already at its generated path");
        }
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
