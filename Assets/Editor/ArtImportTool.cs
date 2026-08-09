using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.Animations;

/// <summary>
/// Brings generated art out of the staging folder and into the project: import settings, sheet
/// slicing, animation clips and an AnimatorController wired to the parameter names the game
/// already calls.
///
/// Run via: Tools → GBH → Art → Import Generated Art
///
/// The contract with the generating agent is `ART_PIPELINE.md`. Staging lives at `art_incoming/`
/// beside `Assets/`, deliberately outside the project so Unity never imports a half-written file.
/// Nothing here happens automatically — the folder fills up and waits for this menu item.
///
/// Re-running is safe: an asset of the same name overwrites in place, so regenerating art and
/// importing again keeps the same GUID and every existing reference to it.
/// </summary>
public static class ArtImportTool
{
    private const string StagingFolder  = "art_incoming";
    private const string ProcessedFolder = "processed";
    private const string ArtRoot        = "Assets/Art/Generated";
    private const string AnimRoot       = "Assets/Animations/Generated";
    private const int    MaxTextureSize = 2048;

    /// <summary>The key colour the contract asks for. Anything else flat is refused, not keyed.</summary>
    private static readonly Color32 KeyColour = new Color32(255, 0, 255, 255);

    /// <summary>
    /// The whole art direction in one number. Sources arrive photoreal and high-resolution and are
    /// reduced to this density, so a 1.35-unit character lands at ~65 px and reads as a digitised
    /// sprite. Using it as the import PPU too means sprites sit at their natural size in the scene
    /// with a scale factor of 1.
    /// </summary>
    private const float PixelsPerWorldUnit = 48f;

    private const float PixelsPerUnit = PixelsPerWorldUnit;

    /// <summary>Action name in the JSON → state name in the controller → parameter that fires it.</summary>
    private static readonly Dictionary<string, string> ActionToState = new Dictionary<string, string>
    {
        { "idle",   "Idle"   },
        { "walk",   "Run"    },   // "Run" matches the existing Bandit_Controller
        { "attack", "Attack" },
        { "hurt",   "Hurt"   },
        { "death",  "Death"  },
        { "cast",   "Cast"   },
        { "cycle",  "Cycle"  },   // riding a vehicle — held by a bool, not fired by a trigger
        { "roll",       "Roll"      },
        { "knockback",  "Knockback" },
    };

    /// <summary>Bool parameters, for states that are held rather than fired once.</summary>
    private const string CyclingParameter = "Cycling";

    private static readonly Dictionary<string, string> ActionToTrigger = new Dictionary<string, string>
    {
        { "attack", "MeleeAttack" },
        { "hurt",   "Hit"         },
        { "death",  "Death"       },
        { "cast",   "CastSpell"   },   // nothing in the project defines this yet — see CLAUDE.md §8
        { "roll",       "Roll"      },
        { "knockback",  "Knockback" },
    };

    /// <summary>The frame/fps/loop table from ART_PIPELINE.md §8, so the two cannot drift apart.</summary>
    private class ActionSpec
    {
        public int Frames;
        public float Fps;
        public bool Loop;
    }

    private static readonly Dictionary<string, ActionSpec> ActionContract = new Dictionary<string, ActionSpec>
    {
        { "idle",   new ActionSpec { Frames = 4, Fps = 6f,  Loop = true  } },
        { "walk",   new ActionSpec { Frames = 4, Fps = 8f,  Loop = true  } },
        { "attack", new ActionSpec { Frames = 6, Fps = 12f, Loop = false } },
        { "cast",   new ActionSpec { Frames = 6, Fps = 12f, Loop = false } },
        { "hurt",   new ActionSpec { Frames = 3, Fps = 12f, Loop = false } },
        { "death",  new ActionSpec { Frames = 6, Fps = 10f, Loop = false } },
        { "cycle",  new ActionSpec { Frames = 6, Fps = 12f, Loop = true  } },
        { "roll",       new ActionSpec { Frames = 6, Fps = 14f, Loop = false } },
        // 6 frames, not the 3 this started as: the delivered knockback is a full tumble — launched,
        // over the back, planted, upright — which cannot be told in three. 6 @ 12 fps = 0.50 s of
        // clip against a 0.22 s physical slide; see CombatController.KnockbackSlideDuration for why
        // that mismatch is deliberate.
        { "knockback",  new ActionSpec { Frames = 6, Fps = 12f, Loop = false } },
    };

    /// <summary>
    /// One staged pair, tracked across the whole run so its files can be moved out of staging at
    /// the end. Cleanliness is per asset, not per run: one bad sheet must not pin seven good ones
    /// in the folder for the next run to re-process and re-report.
    /// </summary>
    private class PendingAsset
    {
        public string ManifestPath;
        public string PngPath;
        public string BaseName;
        public string Subject = "";
        public string Action = "";
        public bool Clean;
    }

    [Serializable]
    private class ArtManifest
    {
        public string name;
        public string type;          // "single" | "sheet"
        public string category;      // characters | vehicles | props | fx | ui
        public string subject;       // optional; defaults to name minus the action suffix
        public string action;        // idle | walk | attack | hurt | death | cast | cycle
        public string rendererPath;  // optional animation binding path; empty = same GameObject
        public float worldHeight;
        // Appended. A manifest written before this existed has no pixelSize key, JsonUtility reads
        // it back as 0, and 0 means "size from worldHeight" — the behaviour every sheet already
        // delivered was imported with.
        public int pixelSize;
        public int frameWidth;
        public int frameHeight;
        public int columns;
        public int rows;
        public int frameCount;
        public float fps;
        public bool loop;
        public string description;
        public string question;
    }

    [MenuItem("Tools/GBH/Art/Import Generated Art")]
    public static void Run()
    {
        string staging = Path.Combine(Directory.GetParent(Application.dataPath).FullName, StagingFolder);
        if (!Directory.Exists(staging))
        {
            EditorUtility.DisplayDialog("Import Generated Art",
                $"No staging folder at {staging}.\n\nSee ART_PIPELINE.md.", "OK");
            return;
        }

        string[] manifests = Directory.GetFiles(staging, "*.json", SearchOption.TopDirectoryOnly);
        if (manifests.Length == 0)
        {
            EditorUtility.DisplayDialog("Import Generated Art",
                "Nothing waiting in art_incoming/.\n\nEach asset needs a PNG and a .json of the " +
                "same name — see ART_PIPELINE.md. Anything already imported cleanly has been " +
                $"moved to {StagingFolder}/{ProcessedFolder}/.", "OK");
            return;
        }

        var report = new List<string>();
        var problems = new List<string>();
        var warnings = new List<string>();
        var questions = new List<string>();
        ShapesBySubject.Clear();
        RejectedSheets.Clear();

        // Controllers are built after every clip exists, so a subject's states can all be wired
        // in one pass rather than rebuilt per action.
        var clipsBySubject = new Dictionary<string, Dictionary<string, AnimationClip>>();

        // The worldHeight each subject declared, carried out of the manifests so presets can be
        // sized from the art rather than from a number retyped by hand per preset.
        var heightBySubject = new Dictionary<string, float>();

        var pending = new List<PendingAsset>();

        // Deliberately not wrapped in StartAssetEditing/StopAssetEditing. That batches — and
        // therefore defers — the ImportAsset calls, so AssetImporter.GetAtPath returns null for a
        // file that was only just written, the import settings never apply, and the asset lands
        // with Unity's defaults: Default texture type, no slices, no clips. A handful of assets
        // per run makes the batching worthless anyway.
        foreach (string manifestPath in manifests)
        {
            int problemsBefore = problems.Count;
            PendingAsset asset = ImportOne(manifestPath, staging, report, problems, warnings,
                questions, clipsBySubject, heightBySubject);
            if (asset == null) continue;

            asset.Clean = problems.Count == problemsBefore;
            pending.Add(asset);
        }

        // The loop above only ever looks at JSONs, so a PNG delivered without its sidecar is
        // otherwise ignored in complete silence.
        ReportOrphanPngs(staging, manifests, problems);

        AssetDatabase.Refresh();

        // Shapes are compared before any controller is built, so a sheet that fails can be kept
        // out of the animator rather than reported and wired up regardless.
        CompareSubjectShapes(problems);

        foreach (var kv in clipsBySubject)
        {
            foreach (string action in kv.Value.Keys.Where(a => IsRejected(kv.Key, a)).ToList())
            {
                kv.Value.Remove(action);
                report.Add($"    {kv.Key} '{action}' left out of the controller — it failed a check");
            }

            if (kv.Value.Count == 0) continue;

            try
            {
                BuildController(kv.Key, kv.Value, report);
            }
            catch (Exception e)
            {
                problems.Add($"{kv.Key}: controller failed — {e.Message}");
            }
        }

        AutoAssign(clipsBySubject, heightBySubject, report, problems);

        AssetDatabase.SaveAssets();

        // Last, because CompareSubjectShapes above is the final thing that can fail an asset —
        // moving inside ImportOne would archive a sheet that the cross-sheet check then rejects.
        ArchiveProcessed(staging, pending, report, problems);

        Summarise(report, problems, warnings, questions);
    }

    /// <summary>
    /// Moves the PNG and JSON of everything that imported without complaint into
    /// `art_incoming/processed/`. Anything that reported a problem stays put, so the folder
    /// converges on "only what is still wrong" instead of growing forever and burying each new
    /// batch's report lines under every previous batch's.
    /// </summary>
    private static void ArchiveProcessed(string staging, List<PendingAsset> pending,
        List<string> report, List<string> problems)
    {
        List<PendingAsset> movable = pending
            .Where(p => p.Clean && !IsRejected(p.Subject, p.Action))
            .ToList();
        if (movable.Count == 0) return;

        string processed = Path.Combine(staging, ProcessedFolder);
        try
        {
            Directory.CreateDirectory(processed);
        }
        catch (Exception e)
        {
            problems.Add($"could not create {StagingFolder}/{ProcessedFolder}/ — {e.Message}. " +
                         "Imports succeeded; the staged files were left where they are.");
            return;
        }

        int moved = 0;
        foreach (PendingAsset p in movable)
        {
            try
            {
                MoveOverwrite(p.PngPath, Path.Combine(processed, Path.GetFileName(p.PngPath)));
                MoveOverwrite(p.ManifestPath, Path.Combine(processed, Path.GetFileName(p.ManifestPath)));
                moved++;
            }
            catch (Exception e)
            {
                problems.Add($"{p.BaseName}: imported fine, but the staged pair could not be moved " +
                             $"to {ProcessedFolder}/ — {e.Message}");
            }
        }

        if (moved > 0)
            report.Add($"moved {moved} clean pair(s) to {StagingFolder}/{ProcessedFolder}/");

        int left = pending.Count - moved;
        if (left > 0)
            report.Add($"{left} pair(s) left in {StagingFolder}/ — they still have problems to fix");
    }

    private static void MoveOverwrite(string from, string to)
    {
        // File.Move refuses an existing destination on .NET Framework, and re-importing a
        // regenerated asset of the same name is the normal case rather than the exception.
        if (File.Exists(to)) File.Delete(to);
        File.Move(from, to);
    }

    /// <summary>Reports PNGs in staging that no manifest claims, rather than skipping them silently.</summary>
    private static void ReportOrphanPngs(string staging, string[] manifests, List<string> problems)
    {
        var claimed = new HashSet<string>(
            manifests.Select(Path.GetFileNameWithoutExtension),
            StringComparer.OrdinalIgnoreCase);

        foreach (string png in Directory.GetFiles(staging, "*.png", SearchOption.TopDirectoryOnly))
        {
            string baseName = Path.GetFileNameWithoutExtension(png);
            if (claimed.Contains(baseName)) continue;

            problems.Add($"{baseName}.png has no {baseName}.json beside it, so it was skipped " +
                         "entirely. Every asset needs both — see ART_PIPELINE.md §4.");
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  AUTO-ASSIGNMENT
    //  Imported art is wired into the things that were waiting for it, so a batch of sprites
    //  does not need a follow-up round of hand-dragging in the Inspector.
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void AutoAssign(
        Dictionary<string, Dictionary<string, AnimationClip>> clipsBySubject,
        Dictionary<string, float> heightBySubject,
        List<string> report, List<string> problems)
    {
        AssignPlayerSprite("spr_char_player", report, problems);
        AssignPlayerRestingFrame(report, problems);
        // No spr_char_player_ebike assignment. WorldActorVisual.MountedSprite is superseded by the
        // `cycle` sheet — a single sprite there is overwritten by the Animator every frame, and the
        // pipeline no longer asks for that filename (ART_PIPELINE.md §7.2).
        AssignVehicleSprite("spr_vehicle_ebike", report, problems);
        AssignPlayerController(PlayerSubject, report, problems);

        bool classArtInBatch = clipsBySubject.Keys.Any(IsPlayerClassSubject);
        RefreshPlayerClassVisualLibrary(report, problems, classArtInBatch);

        // Every other subject in a run is an NPC, and NPCs are authored as PlacementPresets rather
        // than as scene objects. The PLAYER is excluded because they are a scene object with their
        // own wiring above — nothing the palette ever stamps. Player-CLASS subjects are not
        // excluded: the wiring only ever touches a preset that explicitly claims the subject, and
        // Preset_Stabmeister does exactly that. (The class's own visual library is refreshed above;
        // this is about stamping the class as a world NPC.)
        foreach (string subject in clipsBySubject.Keys)
        {
            if (string.Equals(subject, PlayerSubject, StringComparison.OrdinalIgnoreCase)) continue;

            heightBySubject.TryGetValue(subject, out float worldHeight);
            WirePresetsForSubject(subject, worldHeight, report);
        }

        AssignNpcPortraits(report, problems);
    }

    private static Sprite FindImported(string baseName)
    {
        string[] hits = AssetDatabase.FindAssets($"{baseName} t:Sprite", new[] { ArtRoot });
        foreach (string guid in hits)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            if (Path.GetFileNameWithoutExtension(path) != baseName) continue;
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }
        return null;
    }

    /// <summary>Player sprite on the WorldActorVisual in the open scene.</summary>
    private static void AssignPlayerSprite(string baseName, List<string> report, List<string> problems)
    {
        Sprite sprite = FindImported(baseName);
        if (sprite == null) return;

        var player = UnityEngine.Object.FindObjectOfType<ExiledAlvaston.Combat.CombatController>();
        if (player == null)
        {
            problems.Add($"{baseName}: imported, but no CombatController in the open scene — " +
                         "open Assets/c.unity and re-run to have it assigned.");
            return;
        }

        var visual = player.GetComponent<ExiledAlvaston.World.WorldActorVisual>();
        if (visual == null)
        {
            problems.Add($"{baseName}: the player has no WorldActorVisual to assign it to.");
            return;
        }

        Undo.RecordObject(visual, "Assign generated sprite");
        visual.ActorSprite = sprite;

        EditorUtility.SetDirty(visual);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(player.gameObject.scene);
        report.Add("    assigned to player WorldActorVisual.ActorSprite — save the scene (Ctrl+S)");
    }

    /// <summary>
    /// Points ActorSprite at the first frame of the idle sheet when the player has no single
    /// sprite of their own. It is what shows in edit mode and before the Animator takes over, so
    /// leaving it on whatever placeholder was there means the editor shows one character and the
    /// game shows another.
    /// </summary>
    private static void AssignPlayerRestingFrame(List<string> report, List<string> problems)
    {
        if (FindImported("spr_char_player") != null) return;   // a proper single wins

        string[] hits = AssetDatabase.FindAssets("sheet_char_player_idle t:Texture2D", new[] { ArtRoot });
        if (hits.Length == 0) return;

        string path = AssetDatabase.GUIDToAssetPath(hits[0]);
        Sprite first = AssetDatabase.LoadAllAssetRepresentationsAtPath(path)
            .OfType<Sprite>()
            .FirstOrDefault(s => s.name.EndsWith("_0"));
        if (first == null) return;

        var player = UnityEngine.Object.FindObjectOfType<ExiledAlvaston.Combat.CombatController>();
        var visual = player != null ? player.GetComponent<ExiledAlvaston.World.WorldActorVisual>() : null;
        if (visual == null) return;
        if (visual.ActorSprite == first) return;

        Undo.RecordObject(visual, "Assign resting frame");
        visual.ActorSprite = first;
        EditorUtility.SetDirty(visual);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(player.gameObject.scene);
        report.Add($"    player ActorSprite set to {first.name} — save the scene (Ctrl+S)");
    }

    /// <summary>
    /// Points the player's Animator at the controller built from their sheets. Without this the
    /// sheets import, the clips exist, and the player carries on playing whatever placeholder
    /// controller was assigned — Bandit_Controller, in this project.
    /// </summary>
    private static void AssignPlayerController(string subject, List<string> report, List<string> problems)
    {
        string path = $"{AnimRoot}/{subject}_Controller.controller";
        var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
        if (controller == null) return;

        var player = UnityEngine.Object.FindObjectOfType<ExiledAlvaston.Combat.CombatController>();
        if (player == null)
        {
            problems.Add($"{subject}_Controller built, but no CombatController in the open scene — " +
                         "open Assets/c.unity and re-run to have it assigned.");
            return;
        }

        Animator animator = player.PlayerAnimator;
        if (animator == null)
        {
            problems.Add($"{subject}_Controller built, but CombatController.PlayerAnimator is unset.");
            return;
        }
        if (animator.runtimeAnimatorController == controller) return;

        Undo.RecordObject(animator, "Assign generated controller");
        animator.runtimeAnimatorController = controller;
        EditorUtility.SetDirty(animator);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(player.gameObject.scene);
        report.Add($"    player Animator now uses {subject}_Controller — save the scene (Ctrl+S)");
    }

    /// <summary>Parked vehicle art, written into the prefab in place so the GUID survives.</summary>
    private static void AssignVehicleSprite(string baseName, List<string> report, List<string> problems)
    {
        Sprite sprite = FindImported(baseName);
        if (sprite == null) return;

        const string prefabPath = "Assets/Prefabs/ModernBritain/EBike.prefab";
        if (AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath) == null)
        {
            problems.Add($"{baseName}: {prefabPath} not found.");
            return;
        }

        GameObject contents = PrefabUtility.LoadPrefabContents(prefabPath);
        try
        {
            var vehicle = contents.GetComponent<ExiledAlvaston.World.VehicleController>();
            if (vehicle == null)
            {
                problems.Add($"{baseName}: EBike.prefab has no VehicleController.");
                return;
            }

            vehicle.VehicleSprite = sprite;

            if (vehicle.ParkedModel != null)
            {
                var sr = vehicle.ParkedModel.GetComponentInChildren<SpriteRenderer>(true);
                if (sr != null)
                {
                    sr.sprite = sprite;

                    // Parked height is 0.9 world units; the renderer is scaled to suit whatever
                    // the sprite's own bounds are, so replacement art of any resolution fits.
                    float spriteH = sprite.bounds.size.y;
                    if (spriteH > 0.001f)
                    {
                        sr.transform.localScale = Vector3.one * (0.9f / spriteH);
                        sr.transform.localPosition = new Vector3(0f, 0.45f, 0f);
                    }
                }
            }

            PrefabUtility.SaveAsPrefabAsset(contents, prefabPath);
            report.Add("    assigned to EBike.prefab (VehicleSprite + parked visual)");
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(contents);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  PRESETS
    //  An NPC is authored as a PlacementPreset, so "the art is wired up" means that preset knows
    //  which controller drives it, which sprite stands in before the Animator runs, and how tall
    //  the character is. All three come from the art, so all three are set here rather than being
    //  dragged into the Inspector once per character.
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private const string PlayerSubject   = "player";
    private const string ControllerSuffix = "_Controller";
    private static readonly string[] PlayerClassSubjects =
    {
        "player",
        "player_stabmeister",
        "player_mrhood",
        "player_dynamo",
        "player_bundabasher"
    };

    private static bool IsPlayerClassSubject(string subject)
    {
        return PlayerClassSubjects.Any(candidate =>
            string.Equals(candidate, subject, StringComparison.OrdinalIgnoreCase));
    }

    /// <summary>
    /// Wires every <c>PlacementPreset</c> whose <c>ArtSubject</c> matches, and reports what it
    /// touched. Returns how many presets changed.
    ///
    /// Deliberately asymmetric about overwriting. The controller and the resting sprite are
    /// *derived* from the art, so a fresh import wins outright — that is what lets a placeholder
    /// wiring be replaced by the real character with no manual fix-up. The height is *tunable*, so
    /// a value already set by hand is left alone. Point a preset at another subject's animations on
    /// purpose and the next import of its own subject will revert it; that is the accepted cost of
    /// the first property.
    /// </summary>
    /// <param name="worldHeight">
    /// From the manifest. Zero means unknown — the rescan menu item below has no manifest to read,
    /// so it leaves height alone rather than guessing it back out of the imported pixels.
    /// </param>
    private static int WirePresetsForSubject(string subject, float worldHeight, List<string> report)
    {
        if (string.IsNullOrEmpty(subject)) return 0;

        var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(
            $"{AnimRoot}/{subject}{ControllerSuffix}.controller");
        Sprite resting = FindIdleFrameZero(subject);

        if (controller == null && resting == null) return 0;

        int wired = 0;

        foreach (string guid in AssetDatabase.FindAssets("t:PlacementPreset"))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var preset = AssetDatabase.LoadAssetAtPath<ExiledAlvaston.Data.PlacementPreset>(path);
            if (preset == null) continue;
            if (!string.Equals(preset.ArtSubject, subject, StringComparison.OrdinalIgnoreCase)) continue;

            var changed = new List<string>();

            if (controller != null && preset.NpcController != controller)
            {
                preset.NpcController = controller;
                changed.Add("controller");
            }

            // Not cosmetic: an Animator does not evaluate in edit mode, so without this the preset
            // places something invisible in the prefab stage it is being authored in.
            if (resting != null && preset.NpcSprite != resting)
            {
                preset.NpcSprite = resting;
                changed.Add("resting sprite");
            }

            if (resting != null && preset.Icon == null)
            {
                preset.Icon = resting;
                changed.Add("palette icon");
            }

            if (worldHeight > 0f && preset.NpcHeight <= 0f)
            {
                preset.NpcHeight = worldHeight;
                changed.Add($"height {worldHeight:0.##}");
            }

            if (changed.Count == 0) continue;

            EditorUtility.SetDirty(preset);
            report.Add($"    {Path.GetFileNameWithoutExtension(path)} ← {subject} " +
                       $"({string.Join(", ", changed)})");
            wired++;
        }

        return wired;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  PORTRAITS
    //  A dialogue portrait is a single named spr_portrait_<subject>. It is not a scene object and
    //  not part of a preset's placed body — it is the face DialogueManager.DisplayNode shows, read
    //  from node.Speaker.Portrait. The one CharacterData that becomes that node.Speaker is
    //  PlacementPreset.Speaker (PresetDialogueTools copies it into the generated node), keyed by the
    //  same ArtSubject WirePresetsForSubject uses. So a portrait is wired by walking
    //  subject → preset(s) with that ArtSubject → their Speaker CharacterData → Portrait.
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private const string PortraitPrefix = "spr_portrait_";

    /// <summary>
    /// Assigns every imported <c>spr_portrait_&lt;subject&gt;</c> single to the <c>Portrait</c> of the
    /// <see cref="ExiledAlvaston.Data.CharacterData"/> that speaks for that subject — the
    /// <c>Speaker</c> on any <c>PlacementPreset</c> carrying the matching <c>ArtSubject</c>.
    ///
    /// Scans what is on disk rather than a batch, like the other single assignments, so it is
    /// idempotent and re-runnable from the "Wire Presets" menu. Overwrites outright, matching the
    /// asymmetry of the preset wiring: the portrait is derived from the art, so a fresh import wins.
    ///
    /// Reports a problem, never silence, when a portrait has nowhere to go — no preset for its
    /// subject, or presets that exist but have no Speaker CharacterData wired yet (currently every
    /// one of them). That gap is the owner's to close by assigning a CharacterData to each talking
    /// preset's Speaker field; this only stops the portrait being lost when they do.
    /// </summary>
    private static void AssignNpcPortraits(List<string> report, List<string> problems)
    {
        if (!AssetDatabase.IsValidFolder(ArtRoot)) return;

        foreach (string guid in AssetDatabase.FindAssets("t:Sprite", new[] { ArtRoot }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            string file = Path.GetFileNameWithoutExtension(path);
            if (!file.StartsWith(PortraitPrefix, StringComparison.Ordinal)) continue;

            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            if (sprite == null) continue;

            string subject = file.Substring(PortraitPrefix.Length);

            // Distinct Speaker assets across every preset on this subject — one CharacterData may be
            // shared by several presets, and it must not be reported (or recorded) twice.
            var speakers = new List<ExiledAlvaston.Data.CharacterData>();
            bool matchedAnyPreset = false;

            foreach (string presetGuid in AssetDatabase.FindAssets("t:PlacementPreset"))
            {
                var preset = AssetDatabase.LoadAssetAtPath<ExiledAlvaston.Data.PlacementPreset>(
                    AssetDatabase.GUIDToAssetPath(presetGuid));
                if (preset == null) continue;
                if (!string.Equals(preset.ArtSubject, subject, StringComparison.OrdinalIgnoreCase)) continue;

                matchedAnyPreset = true;
                if (preset.Speaker != null && !speakers.Contains(preset.Speaker))
                    speakers.Add(preset.Speaker);
            }

            if (!matchedAnyPreset)
            {
                problems.Add($"{file}: imported, but no PlacementPreset has ArtSubject '{subject}', " +
                             "so there is no character to hang the portrait on.");
                continue;
            }

            if (speakers.Count == 0)
            {
                problems.Add($"{file}: imported, but no preset for '{subject}' has a Speaker " +
                             "CharacterData, so the dialogue window has nothing to assign it to. " +
                             "Set the Speaker field on that character's preset and re-run " +
                             "Tools → GBH → Content → Wire Presets From Imported Art.");
                continue;
            }

            foreach (var speaker in speakers)
            {
                if (speaker.Portrait == sprite) continue;

                Undo.RecordObject(speaker, "Assign generated portrait");
                speaker.Portrait = sprite;
                EditorUtility.SetDirty(speaker);
                report.Add($"    {speaker.name}.Portrait ← {file}");
            }
        }
    }

    /// <summary>
    /// First frame of a subject's idle sheet — the pose the character holds when nothing is
    /// animating them.
    ///
    /// Found by matching the tail of the filename rather than building it, because subject →
    /// filename is not reversible: "characters" becomes the "char" of sheet_char_mosley_idle.
    ///
    /// internal, not private: GeneratedEnemyPrefabTool also calls this, so the two tools cannot
    /// disagree about which frame is a subject's resting pose.
    /// </summary>
    internal static Sprite FindIdleFrameZero(string subject)
    {
        if (!AssetDatabase.IsValidFolder(ArtRoot)) return null;

        foreach (string guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ArtRoot }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            string file = Path.GetFileNameWithoutExtension(path);
            if (file != $"{subject}_idle"
                && !file.EndsWith($"_{subject}_idle", StringComparison.OrdinalIgnoreCase)) continue;

            return AssetDatabase.LoadAllAssetRepresentationsAtPath(path)
                .OfType<Sprite>()
                .FirstOrDefault(s => s.name.EndsWith("_0", StringComparison.Ordinal));
        }
        return null;
    }

    internal static void PopulatePlayerClassVisualLibrary(
        ExiledAlvaston.Flow.PlayerClassVisualLibrary library, List<string> report)
    {
        if (library == null) return;

        var classes = new[]
        {
            ExiledAlvaston.Data.PlayerClass.YoungDriller,
            ExiledAlvaston.Data.PlayerClass.Stabmeister,
            ExiledAlvaston.Data.PlayerClass.MrHood,
            ExiledAlvaston.Data.PlayerClass.Dynamo,
            ExiledAlvaston.Data.PlayerClass.BundaBasher
        };
        string[] requiredActions = { "idle", "walk", "attack", "hurt", "death", "cast" };
        var profiles = new ExiledAlvaston.Flow.PlayerClassVisualProfile[classes.Length];

        for (int i = 0; i < classes.Length; i++)
        {
            string subject = PlayerClassSubjects[i];
            Sprite[] idleFrames = FindIdleFrames(subject);
            var controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(
                $"{AnimRoot}/{subject}{ControllerSuffix}.controller");

            bool complete = controller != null;
            for (int actionIndex = 0; actionIndex < requiredActions.Length; actionIndex++)
                complete &= FindClassClip(subject, requiredActions[actionIndex]) != null;

            profiles[i] = new ExiledAlvaston.Flow.PlayerClassVisualProfile
            {
                Class = classes[i],
                Controller = controller,
                RestingSprite = idleFrames.FirstOrDefault(),
                IdlePreviewFrames = idleFrames,
                PreviewFps = 6f,
                GameplayReady = complete
            };
        }

        Undo.RecordObject(library, "Refresh player class visual library");
        library.Profiles = profiles;
        EditorUtility.SetDirty(library);
        report?.Add("    refreshed five player-class visual profiles from imported art");
    }

    private static void RefreshPlayerClassVisualLibrary(
        List<string> report, List<string> problems, bool requiredForBatch)
    {
        if (UnityEngine.SceneManagement.SceneManager.GetActiveScene().path != "Assets/c.unity")
        {
            if (requiredForBatch)
                problems.Add("player class art imported, but Assets/c.unity is not open; " +
                             "open it and re-run the importer to refresh the class visual library.");
            return;
        }

        var flows = UnityEngine.Object.FindObjectsOfType<ExiledAlvaston.Flow.GameFlowController>(true);
        if (flows.Length != 1)
        {
            if (requiredForBatch)
                problems.Add("player class art imported, but the open scene does not contain exactly one GameFlowController.");
            return;
        }

        var library = flows[0].ClassVisuals != null
            ? flows[0].ClassVisuals
            : flows[0].GetComponent<ExiledAlvaston.Flow.PlayerClassVisualLibrary>();
        if (library == null)
        {
            if (requiredForBatch)
                problems.Add("player class art imported, but the Character Creator builder has not added " +
                             "PlayerClassVisualLibrary to GameFlow yet.");
            return;
        }

        PopulatePlayerClassVisualLibrary(library, report);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(flows[0].gameObject.scene);
    }

    private static Sprite[] FindIdleFrames(string subject)
    {
        if (!AssetDatabase.IsValidFolder(ArtRoot)) return Array.Empty<Sprite>();

        foreach (string guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ArtRoot }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            string file = Path.GetFileNameWithoutExtension(path);
            if (file != $"{subject}_idle" &&
                !file.EndsWith($"_{subject}_idle", StringComparison.OrdinalIgnoreCase)) continue;

            return AssetDatabase.LoadAllAssetRepresentationsAtPath(path)
                .OfType<Sprite>()
                .OrderBy(sprite => sprite.name, StringComparer.Ordinal)
                .ToArray();
        }
        return Array.Empty<Sprite>();
    }

    private static AnimationClip FindClassClip(string subject, string action)
    {
        foreach (string guid in AssetDatabase.FindAssets("t:AnimationClip", new[] { AnimRoot }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            string file = Path.GetFileNameWithoutExtension(path);
            if (file == $"{subject}_{action}" ||
                file.EndsWith($"_{subject}_{action}", StringComparison.OrdinalIgnoreCase))
                return AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
        }
        return null;
    }

    /// <summary>
    /// Wires presets against art that is already in the project, rather than against a run that has
    /// just happened.
    ///
    /// The import path only ever knows about the batch in front of it, and a clean batch is moved
    /// out of staging afterwards — so art imported last month, or a preset written after its
    /// subject arrived, would never be connected by an import alone. This closes that gap and is
    /// safe to run at any time: it is the same wiring, driven off what is on disk.
    /// </summary>
    [MenuItem("Tools/GBH/Content/Wire Presets From Imported Art")]
    public static void WirePresetsFromImportedArt()
    {
        if (!AssetDatabase.IsValidFolder(AnimRoot))
        {
            EditorUtility.DisplayDialog("Wire Presets From Imported Art",
                $"No {AnimRoot} folder, so no art has been imported yet.", "OK");
            return;
        }

        var report = new List<string>();
        int subjects = 0;

        foreach (string guid in AssetDatabase.FindAssets("t:AnimatorController", new[] { AnimRoot }))
        {
            string file = Path.GetFileNameWithoutExtension(AssetDatabase.GUIDToAssetPath(guid));
            if (!file.EndsWith(ControllerSuffix, StringComparison.Ordinal)) continue;

            string subject = file.Substring(0, file.Length - ControllerSuffix.Length);
            // Only the player is skipped — a scene object, never palette-stamped. A preset that
            // explicitly claims a player-CLASS subject (Preset_Stabmeister does) gets wired like
            // any NPC's; without this the class presets stay unwired no matter how often this runs.
            if (string.Equals(subject, PlayerSubject, StringComparison.OrdinalIgnoreCase)) continue;

            if (WirePresetsForSubject(subject, 0f, report) > 0) subjects++;
        }

        // Portraits are singles, not driven by a controller, so the controller sweep above never
        // reaches them — assign them from disk here on the same terms.
        var portraitProblems = new List<string>();
        AssignNpcPortraits(report, portraitProblems);
        foreach (string p in portraitProblems) report.Add($"    (skipped) {p}");

        AssetDatabase.SaveAssets();

        var log = new System.Text.StringBuilder();
        log.AppendLine("Wire Presets From Imported Art");
        log.AppendLine("──────────────────────────────");
        if (report.Count == 0) log.AppendLine("  nothing to do — every preset already matches its art.");
        foreach (string r in report) log.AppendLine(r);
        Debug.Log(log.ToString());

        EditorUtility.DisplayDialog("Wire Presets From Imported Art",
            report.Count == 0
                ? "Every preset already matches its art. Nothing changed."
                : $"{report.Count} preset(s) wired across {subjects} subject(s).\n\n" +
                  "Heights are left alone here — only an import knows a subject's worldHeight.\n\n" +
                  "Detail in the Console.", "OK");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  ONE ASSET
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static PendingAsset ImportOne(string manifestPath, string staging, List<string> report,
        List<string> problems, List<string> warnings, List<string> questions,
        Dictionary<string, Dictionary<string, AnimationClip>> clipsBySubject,
        Dictionary<string, float> heightBySubject)
    {
        string baseName = Path.GetFileNameWithoutExtension(manifestPath);

        string rawJson;
        ArtManifest m;
        try
        {
            rawJson = File.ReadAllText(manifestPath);
            m = JsonUtility.FromJson<ArtManifest>(rawJson);
        }
        catch (Exception e)
        {
            problems.Add($"{baseName}.json is not valid JSON — {e.Message}");
            return null;
        }
        if (m == null)
        {
            problems.Add($"{baseName}.json parsed as empty.");
            return null;
        }

        if (!string.IsNullOrEmpty(m.question))
            questions.Add($"{baseName}: {m.question}");

        string png = Path.Combine(staging, baseName + ".png");
        if (!File.Exists(png))
        {
            problems.Add($"{baseName}.json has no matching {baseName}.png.");
            return null;
        }

        // From here the pair is real, so it is tracked whatever happens next — the Clean flag the
        // caller sets is what decides whether it gets archived.
        var pending = new PendingAsset
        {
            ManifestPath = manifestPath,
            PngPath = png,
            BaseName = baseName,
            Subject = ResolveSubject(m, baseName),
            Action = (m.action ?? "").ToLowerInvariant()
        };

        // Recorded before anything can fail: a subject's height is a property of the character,
        // not of whether this particular sheet passed its checks.
        if (m.worldHeight > 0f && !string.IsNullOrEmpty(pending.Subject))
            heightBySubject[pending.Subject] = m.worldHeight;

        string category = string.IsNullOrEmpty(m.category) ? "props" : m.category.ToLowerInvariant();
        string destFolder = $"{ArtRoot}/{category}";
        EnsureFolder(destFolder);

        bool isSheet = string.Equals(m.type, "sheet", StringComparison.OrdinalIgnoreCase);

        ValidateManifest(m, baseName, isSheet, problems, warnings);
        if (isSheet) ApplyActionContract(m, rawJson, baseName, warnings);

        string destPath = $"{destFolder}/{baseName}.png";
        string destAbsolute = Path.Combine(Directory.GetParent(Application.dataPath).FullName, destPath);

        if (!Reduce(png, destAbsolute, m, isSheet, baseName, problems, report)) return pending;

        AssetDatabase.ImportAsset(destPath, ImportAssetOptions.ForceUpdate);
        if (!ApplyImportSettings(destPath, m, isSheet, problems)) return pending;

        if (!isSheet)
        {
            report.Add($"{baseName} → {destFolder} (single)");
            return pending;
        }

        Sprite[] frames = LoadFramesInOrder(destPath, baseName, m);
        if (frames.Length == 0)
        {
            problems.Add($"{baseName}: sliced to zero frames — check frameWidth/frameHeight against the image.");
            return pending;
        }

        AnimationClip clip = BuildClip(baseName, m, frames);
        report.Add($"{baseName} → {destFolder} ({frames.Length} frames, {m.fps:0.#} fps) + clip");

        string subject = pending.Subject;
        string action = pending.Action;
        if (string.IsNullOrEmpty(action) || !ActionToState.ContainsKey(action))
        {
            report.Add($"    (no recognised action — clip made, not wired into a controller)");
            return pending;
        }

        if (!clipsBySubject.TryGetValue(subject, out var byAction))
        {
            byAction = new Dictionary<string, AnimationClip>();
            clipsBySubject[subject] = byAction;
        }
        byAction[action] = clip;
        return pending;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  MANIFEST VALIDATION
    //  Every one of these was previously silent, so a malformed manifest produced a plausible
    //  looking import that was wrong in a way only visible in game.
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void ValidateManifest(ArtManifest m, string baseName, bool isSheet,
        List<string> problems, List<string> warnings)
    {
        // ART_PIPELINE.md §5 names files spr_<category>_<name> and sheet_<category>_<name>_<action>,
        // so the JSON's `name` is the *tail* of the filename rather than all of it: "player_idle"
        // for sheet_char_player_idle.png. Anything that is not a tail is a mismatch worth saying
        // out loud, because the filename is what every asset, clip and controller is named from.
        if (!string.IsNullOrEmpty(m.name)
            && !baseName.EndsWith(m.name, StringComparison.OrdinalIgnoreCase))
        {
            warnings.Add($"{baseName}: JSON name is '{m.name}', which is not the tail of the " +
                         "filename. The filename wins — nothing is named from the JSON.");
        }

        if (!isSheet) return;

        int columns = Mathf.Max(1, m.columns);
        int rows = Mathf.Max(1, m.rows);
        if (m.frameCount > columns * rows)
        {
            problems.Add($"{baseName}: frameCount is {m.frameCount} but the grid is {columns}×{rows} " +
                         $"= {m.frameCount - columns * rows} frame(s) short. Frames past the end of " +
                         "the grid cannot be sliced.");
        }
    }

    /// <summary>
    /// Checks a sheet against the frame/fps/loop table in ART_PIPELINE.md §8, and fills in fps
    /// and loop from it when the manifest omits them. Warns rather than refuses: the numbers are a
    /// house style, and a deliberate deviation should not cost a regeneration cycle.
    /// </summary>
    private static void ApplyActionContract(ArtManifest m, string rawJson, string baseName,
        List<string> warnings)
    {
        string action = (m.action ?? "").ToLowerInvariant();
        if (!ActionContract.TryGetValue(action, out ActionSpec spec)) return;

        if (m.fps <= 0f)
        {
            m.fps = spec.Fps;
            warnings.Add($"{baseName}: no fps given — defaulted to {spec.Fps:0.#} for '{action}'.");
        }
        else if (!Mathf.Approximately(m.fps, spec.Fps))
        {
            warnings.Add($"{baseName}: fps is {m.fps:0.#} where '{action}' is specified as " +
                         $"{spec.Fps:0.#}. Imported as given.");
        }

        // JsonUtility cannot distinguish an omitted bool from an explicit false, so the raw text is
        // what says whether the author had an opinion.
        if (rawJson.IndexOf("\"loop\"", StringComparison.OrdinalIgnoreCase) < 0)
        {
            m.loop = spec.Loop;
            warnings.Add($"{baseName}: no loop flag — defaulted to {Lower(spec.Loop)} for '{action}'.");
        }
        else if (m.loop != spec.Loop)
        {
            warnings.Add($"{baseName}: loop is {Lower(m.loop)} where '{action}' is specified as " +
                         $"{Lower(spec.Loop)}. Imported as given.");
        }

        int declared = m.frameCount > 0
            ? m.frameCount
            : Mathf.Max(1, m.columns) * Mathf.Max(1, m.rows);
        if (declared != spec.Frames)
        {
            warnings.Add($"{baseName}: {declared} frames where '{action}' is specified as " +
                         $"{spec.Frames}. Imported as given.");
        }
    }

    private static string Lower(bool b) => b ? "true" : "false";

    private static string ResolveSubject(ArtManifest m, string baseName)
    {
        if (!string.IsNullOrEmpty(m.subject)) return m.subject;

        string name = string.IsNullOrEmpty(m.name) ? baseName : m.name;
        if (!string.IsNullOrEmpty(m.action) && name.EndsWith("_" + m.action, StringComparison.OrdinalIgnoreCase))
            return name.Substring(0, name.Length - m.action.Length - 1);

        return name;
    }

    /// <summary>
    /// True for a manifest declaring the "ui" category, matched the same case-insensitive way the
    /// destination folder is chosen (an empty category means "props", never "ui").
    /// </summary>
    private static bool IsUiCategory(ArtManifest m) =>
        m != null && !string.IsNullOrEmpty(m.category) &&
        m.category.Trim().ToLowerInvariant() == "ui";

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  REDUCTION
    //  Sources arrive photoreal and large. The look comes from crushing them down here, not
    //  from asking a generator for low resolution — image models draw "fake pixel art" with an
    //  inconsistent grid, whereas a deterministic reduction gives the same treatment to every
    //  asset forever, however far apart they were generated.
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static bool Reduce(string sourcePath, string destAbsolute, ArtManifest m, bool isSheet,
        string baseName, List<string> problems, List<string> report)
    {
        var src = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!src.LoadImage(File.ReadAllBytes(sourcePath)))
        {
            problems.Add($"{Path.GetFileName(sourcePath)}: could not be read as a PNG.");
            return false;
        }

        // Must happen before the reduction below, which rewrites frameWidth/frameHeight/columns/rows
        // on the manifest to the post-reduction cell size — after that the declared grid always
        // agrees with the image and the check is worthless.
        if (isSheet) ValidateSheetDimensions(src, m, baseName, problems);

        float worldHeight = m.worldHeight > 0f ? m.worldHeight : ExiledAlvaston.Vibe.EKVibe.CharacterHeight;

        // Generators are poor at producing a real alpha channel and good at putting a subject on a
        // plain backdrop, so the contract asks for flat magenta and the backdrop is removed here.
        if (!KeyOutBackground(src, baseName, report, problems))
        {
            UnityEngine.Object.DestroyImmediate(src);
            return false;
        }

        // Trimming is not left to the generator either — sizing is derived from full image height,
        // so untrimmed art silently renders small. Sheets are never trimmed: the grid must stay
        // uniform or every frame shifts.
        if (!isSheet)
        {
            string trimNote = TrimToContent(ref src);
            if (trimNote != null) report.Add("    " + trimNote);
        }

        if (isSheet) CheckFrameAlignment(src, m, baseName, report, problems);

        if (!HasUsableAlpha(src))
        {
            problems.Add($"{m.name}: still opaque edge-to-edge after background removal — the source " +
                         "has neither an alpha channel nor a flat keyable backdrop. Regenerate it " +
                         "with a solid magenta (#FF00FF) background, no gradient and no shadow.");
            UnityEngine.Object.DestroyImmediate(src);
            return false;
        }

        int outW, outH;
        if (isSheet)
        {
            if (m.frameWidth <= 0 || m.frameHeight <= 0)
            {
                problems.Add($"{m.name}: sheet needs frameWidth and frameHeight to be reduced.");
                UnityEngine.Object.DestroyImmediate(src);
                return false;
            }

            int columns = m.columns > 0 ? m.columns : Mathf.Max(1, src.width / m.frameWidth);
            int rows    = m.rows    > 0 ? m.rows    : Mathf.Max(1, src.height / m.frameHeight);

            // Cells are sized first and the sheet built from them, so rounding can never drift
            // the grid out of alignment across a row.
            int cellH = Mathf.Max(1, Mathf.RoundToInt(worldHeight * PixelsPerWorldUnit));
            float scale = (float)cellH / m.frameHeight;
            int cellW = Mathf.Max(1, Mathf.RoundToInt(m.frameWidth * scale));

            outW = cellW * columns;
            outH = cellH * rows;

            m.frameWidth = cellW;
            m.frameHeight = cellH;
            m.columns = columns;
            m.rows = rows;
        }
        else if (IsUiCategory(m) && m.pixelSize > 0)
        {
            // A UI single is not standing in the world, so worldHeight means nothing for it — an
            // icon wants a pixel size. pixelSize is read as a HEIGHT and the width follows from the
            // trimmed aspect ratio; it deliberately does NOT force a square. Trimming has already
            // happened above, so the aspect here is the subject's own, and squaring it would either
            // stretch a tall icon or pad it with transparent margin that the atlas then has to
            // carry. A caller wanting a square icon should deliver square art.
            outH = m.pixelSize;
            outW = Mathf.Max(1, Mathf.RoundToInt(src.width * ((float)outH / src.height)));
        }
        else
        {
            outH = Mathf.Max(1, Mathf.RoundToInt(worldHeight * PixelsPerWorldUnit));
            outW = Mathf.Max(1, Mathf.RoundToInt(src.width * ((float)outH / src.height)));
        }

        if (outW >= src.width || outH >= src.height)
        {
            report.Add($"    source is {src.width}x{src.height}, target {outW}x{outH} — copied without reduction");
            File.WriteAllBytes(destAbsolute, src.EncodeToPNG());
        }
        else
        {
            Texture2D reduced = AreaAverage(src, outW, outH);
            File.WriteAllBytes(destAbsolute, reduced.EncodeToPNG());
            report.Add($"    {src.width}x{src.height} → {outW}x{outH}");
            UnityEngine.Object.DestroyImmediate(reduced);
        }

        UnityEngine.Object.DestroyImmediate(src);
        return true;
    }

    /// <summary>
    /// Chroma-keys a flat backdrop out, edge pixels included.
    ///
    /// A binary threshold is not enough. Anti-aliased edges are a *blend* of backdrop and subject,
    /// too far from the key colour to clear and too close to keep, and once the image is averaged
    /// down they dominate every thin structure — a bike came back with magenta spokes. So partial
    /// pixels are unmixed instead: a blended pixel is P = a·S + (1−a)·K, and the subject colour S
    /// is recovered rather than left with the backdrop smeared through it.
    ///
    /// Keying is global rather than flood-filled from the border, which also clears backdrop
    /// enclosed by the subject — between spokes, inside a basket. The cost is that anything
    /// genuinely this colour in the subject disappears, which is why the contract forbids it.
    ///
    /// Returns false only when the image must be refused outright.
    /// </summary>
    private static bool KeyOutBackground(Texture2D tex, string baseName, List<string> report,
        List<string> problems)
    {
        Color32[] px = tex.GetPixels32();
        int w = tex.width, h = tex.height;

        // Already has real transparency at the edges — nothing to key.
        if (px[0].a < 8 && px[w - 1].a < 8 && px[(h - 1) * w].a < 8 && px[h * w - 1].a < 8)
            return true;

        // Average the border, then check the border actually is one flat colour. A gradient
        // backdrop is not safely keyable and is better reported than half-removed.
        long sr = 0, sg = 0, sb = 0;
        int count = 0;
        foreach (int i in BorderIndices(w, h)) { sr += px[i].r; sg += px[i].g; sb += px[i].b; count++; }
        var seed = new Color32((byte)(sr / count), (byte)(sg / count), (byte)(sb / count), 255);

        float worst = 0f;
        foreach (int i in BorderIndices(w, h)) worst = Mathf.Max(worst, Distance(px[i], seed));
        if (worst > 90f)
        {
            report.Add($"    background is not flat (border varies by {worst:0}) — not keyed, expect a backdrop");
            return true;
        }

        // Keying is global, so whatever colour is found on the border is removed from the *whole*
        // image. That is deliberate — it clears backdrop trapped between a bike's spokes — but it
        // makes keying a colour the contract did not ask for actively destructive: a prop delivered
        // on flat white would lose every white pixel inside the subject too. Refuse instead.
        float fromKey = Distance(seed, KeyColour);
        if (fromKey > 90f)
        {
            problems.Add($"{baseName}: the backdrop is flat but is not the magenta the contract asks " +
                         $"for (it is RGB {seed.r},{seed.g},{seed.b}). Keying it would delete every " +
                         "pixel of that colour inside the subject as well, so nothing was keyed and " +
                         "the asset was not imported. Regenerate on flat #FF00FF, or deliver real " +
                         "alpha — see ART_PIPELINE.md §2.");
            return false;
        }

        // Below Inner the pixel is backdrop; above Outer it is untouched subject; between the two
        // it is a blend and gets unmixed. Values measured against a real 512px render.
        const float inner = 60f;
        const float outer = 170f;

        int cleared = 0, unmixed = 0;
        for (int i = 0; i < px.Length; i++)
        {
            float d = Distance(px[i], seed);

            if (d <= inner)
            {
                px[i] = new Color32(0, 0, 0, 0);
                cleared++;
                continue;
            }
            if (d >= outer)
            {
                px[i].a = 255;
                continue;
            }

            float coverage = (d - inner) / (outer - inner);
            float backdrop = 1f - coverage;

            px[i] = new Color32(
                Unmix(px[i].r, seed.r, coverage, backdrop),
                Unmix(px[i].g, seed.g, coverage, backdrop),
                Unmix(px[i].b, seed.b, coverage, backdrop),
                (byte)Mathf.Clamp(coverage * 255f, 0f, 255f));
            unmixed++;
        }

        tex.SetPixels32(px);
        tex.Apply();
        report.Add($"    keyed out backdrop ({cleared * 100 / px.Length}% cleared, {unmixed} edge pixels unmixed)");
        return true;
    }

    /// <summary>
    /// Confirms the image is actually the grid the manifest declares. Slicing is measured from the
    /// manifest rather than the texture (deliberately — see Slice), so a manifest that disagrees
    /// with its own PNG puts every single frame in the wrong place while importing without error.
    /// </summary>
    private static void ValidateSheetDimensions(Texture2D src, ArtManifest m, string baseName,
        List<string> problems)
    {
        if (m.frameWidth <= 0 || m.frameHeight <= 0)
        {
            problems.Add($"{baseName}: sheet has no frameWidth/frameHeight, so the grid is unknown.");
            return;
        }

        int columns = m.columns > 0 ? m.columns : Mathf.Max(1, src.width / m.frameWidth);
        int rows    = m.rows    > 0 ? m.rows    : Mathf.Max(1, src.height / m.frameHeight);

        int expectedW = m.frameWidth * columns;
        int expectedH = m.frameHeight * rows;
        const int tolerance = 4;   // a few px of encoder slop is not worth a regeneration

        if (Mathf.Abs(src.width - expectedW) <= tolerance
            && Mathf.Abs(src.height - expectedH) <= tolerance) return;

        problems.Add($"{baseName}: the image is {src.width}×{src.height}, but the manifest declares " +
                     $"{columns}×{rows} cells of {m.frameWidth}×{m.frameHeight}, which needs " +
                     $"{expectedW}×{expectedH}. Every slice would land off the grid.");

        // Kept out of the controller as well as reported — a sheet sliced off-grid is worse in game
        // than a missing animation.
        Reject(ResolveSubject(m, baseName), (m.action ?? "").ToLowerInvariant());
    }

    /// <summary>Recovers S from P = a·S + (1−a)·K for one channel.</summary>
    private static byte Unmix(byte pixel, byte key, float coverage, float backdrop)
    {
        return (byte)Mathf.Clamp((pixel - key * backdrop) / coverage, 0f, 255f);
    }

    private static IEnumerable<int> BorderIndices(int w, int h)
    {
        for (int x = 0; x < w; x++) { yield return x; yield return (h - 1) * w + x; }
        for (int y = 1; y < h - 1; y++) { yield return y * w; yield return y * w + (w - 1); }
    }

    private static float Distance(Color32 a, Color32 b)
    {
        float dr = a.r - b.r, dg = a.g - b.g, db = a.b - b.b;
        return Mathf.Sqrt(dr * dr + dg * dg + db * db);
    }

    /// <summary>How much of its cell the subject fills, for comparing sheets of the same subject.</summary>
    private class SubjectShape
    {
        public string Sheet;
        public string Action;
        public float Width;   // fraction of cell width
        public float Height;  // fraction of cell height
    }

    /// <summary>
    /// Actions where the figure is *supposed* to change shape — falling over, sitting on a bike,
    /// tucking into a roll, being flipped off their feet. Height and baseline comparisons are
    /// meaningless for these; width still is not, because no legitimate pose makes a character
    /// half as wide as they are standing.
    ///
    /// knockback used to be excluded here on the reading that a stagger is a standing pose. The
    /// delivered art is not a stagger: it is a 6-frame airborne tumble, feet leaving the ground
    /// entirely, so the standing height and baseline checks would refuse every one of them for
    /// doing exactly what was asked for.
    /// </summary>
    private static bool ShapeChanges(string action) =>
        action == "death" || action == "cycle" || action == "roll" || action == "knockback";

    private static readonly Dictionary<string, List<SubjectShape>> ShapesBySubject =
        new Dictionary<string, List<SubjectShape>>();

    /// <summary>
    /// "subject/action" for every sheet that failed a check. These are still imported as art —
    /// deleting a user's files is not this tool's business — but they are kept out of the
    /// AnimatorController, so a rejected sheet cannot end up playing in the game. Reporting a
    /// problem and then wiring the asset up anyway is how a rejected attack animation reached
    /// play mode.
    /// </summary>
    private static readonly HashSet<string> RejectedSheets = new HashSet<string>();

    private static void Reject(string subject, string action) =>
        RejectedSheets.Add($"{subject}/{action}");

    private static bool IsRejected(string subject, string action) =>
        RejectedSheets.Contains($"{subject}/{action}");

    /// <summary>
    /// A subject's sheets must agree with each other, not just internally. The first generated
    /// walk cycle sat on a correct baseline but was drawn near edge-on — 47 px wide against the
    /// idle sheet's 122 — so the character would have turned into a sliver the moment they moved.
    /// </summary>
    private static void CompareSubjectShapes(List<string> problems)
    {
        foreach (var kv in ShapesBySubject)
        {
            List<SubjectShape> shapes = kv.Value;

            // Idle is the canonical standing pose and the reference every other sheet is asked to
            // match. If this batch has no idle of its own, fall back to one already in the project
            // — a redelivered walk is normally alone in the folder, and comparing it against
            // nothing is how the mismatched sheets kept getting through.
            SubjectShape reference = shapes.Find(s => s.Action == "idle")
                                     ?? LoadReferenceShape(kv.Key);

            if (reference == null)
            {
                // Nothing authoritative anywhere: the widest of this batch is the least likely to
                // be the edge-on mistake being hunted for. Needs at least two to mean anything.
                if (shapes.Count < 2) continue;
                reference = shapes[0];
                foreach (SubjectShape s in shapes) if (s.Width > reference.Width) reference = s;
            }

            foreach (SubjectShape s in shapes)
            {
                if (s == reference || s.Width < 0.001f || s.Height < 0.001f) continue;

                // Only ever flagged for being too narrow. Wider is legitimate — a prone body or a
                // rider on a bike takes more room — but nothing makes a character half as wide as
                // they stand except drawing them edge-on.
                float narrowness = reference.Width / s.Width;
                if (narrowness > 1.4f)
                {
                    Reject(kv.Key, s.Action);
                    problems.Add($"{kv.Key}: '{s.Sheet}' is {narrowness:0.#}× narrower than " +
                                 $"'{reference.Sheet}' — the character is drawn at a different angle, " +
                                 "not the same person from the same view. Regenerate it using " +
                                 $"'{reference.Sheet}' as the visual reference.");
                }

                if (ShapeChanges(s.Action)) continue;

                float ratio = Mathf.Max(reference.Height, s.Height) / Mathf.Min(reference.Height, s.Height);
                if (ratio > 1.15f)
                {
                    Reject(kv.Key, s.Action);
                    problems.Add($"{kv.Key}: '{s.Sheet}' differs from '{reference.Sheet}' in height by " +
                                 $"{ratio:0.##}× — the character will change size between animations.");
                }
            }
        }
    }

    /// <summary>Opaque bounds of every cell of a sheet, averaged, plus how far the feet wander.</summary>
    private struct CellMetrics
    {
        public float WidthFraction;    // mean opaque width as a fraction of cell width
        public float HeightFraction;   // mean opaque height as a fraction of cell height
        public int BaselineSpread;     // px between the lowest and highest first opaque row
        public int Measured;           // cells that had any opaque pixel at all
    }

    /// <summary>
    /// The one implementation of "measure the subject inside each cell". Shared by the per-sheet
    /// baseline check and by the cross-run reference loader, so the numbers a new sheet is judged
    /// against are measured exactly the same way as its own.
    /// </summary>
    private static CellMetrics MeasureCells(Texture2D tex, int cellW, int cellH, int columns, int frames)
    {
        var result = new CellMetrics();
        Color32[] px = tex.GetPixels32();

        int lowest = int.MaxValue, highest = int.MinValue;
        long widthSum = 0, heightSum = 0;

        for (int f = 0; f < frames; f++)
        {
            int cx = (f % columns) * cellW;
            // Texture origin is bottom-left, so row 0 of the sheet is the top of the image.
            int cy = tex.height - ((f / columns) + 1) * cellH;
            if (cy < 0 || cx + cellW > tex.width || cy + cellH > tex.height) continue;

            int bottom = -1, top = -1, left = int.MaxValue, right = -1;
            for (int y = 0; y < cellH; y++)
            {
                for (int x = 0; x < cellW; x++)
                {
                    if (px[(cy + y) * tex.width + cx + x].a <= 8) continue;
                    if (bottom < 0) bottom = y;
                    top = y;
                    if (x < left) left = x;
                    if (x > right) right = x;
                }
            }
            if (bottom < 0) continue;

            lowest = Mathf.Min(lowest, bottom);
            highest = Mathf.Max(highest, bottom);
            widthSum += right - left + 1;
            heightSum += top - bottom + 1;
            result.Measured++;
        }

        if (result.Measured > 0)
        {
            result.WidthFraction = (float)widthSum / result.Measured / cellW;
            result.HeightFraction = (float)heightSum / result.Measured / cellH;
            result.BaselineSpread = highest - lowest;
        }

        return result;
    }

    /// <summary>
    /// Warns when the subject does not sit on the same baseline in every cell. Sheets are not
    /// trimmed, so a figure that drifts up the cell between frames bobs and floats once it is
    /// playing — and at 65 px that is very visible while being almost impossible to spot in the
    /// source. Cheap to measure here, painful to notice in game.
    /// </summary>
    private static void CheckFrameAlignment(Texture2D tex, ArtManifest m, string baseName,
        List<string> report, List<string> problems)
    {
        if (m.frameWidth <= 0 || m.frameHeight <= 0) return;

        int columns = Mathf.Max(1, m.columns);
        int rows = Mathf.Max(1, m.rows);
        int frames = m.frameCount > 0 ? Mathf.Min(m.frameCount, columns * rows) : columns * rows;
        if (frames < 2) return;

        CellMetrics metrics = MeasureCells(tex, m.frameWidth, m.frameHeight, columns, frames);

        string subject = ResolveSubject(m, baseName);
        string action = (m.action ?? "").ToLowerInvariant();

        if (metrics.Measured > 0)
        {
            if (!ShapesBySubject.TryGetValue(subject, out var list))
            {
                list = new List<SubjectShape>();
                ShapesBySubject[subject] = list;
            }
            list.Add(new SubjectShape
            {
                Sheet  = baseName,
                Action = action,
                Width  = metrics.WidthFraction,
                Height = metrics.HeightFraction
            });
        }
        else return;

        int spread = metrics.BaselineSpread;
        float atFinalSize = spread * (m.worldHeight > 0f ? m.worldHeight : ExiledAlvaston.Vibe.EKVibe.CharacterHeight)
                            * PixelsPerWorldUnit / m.frameHeight;

        if (atFinalSize >= 2f && ShapeChanges(action))
            report.Add($"    feet move {spread} px between frames ({atFinalSize:0.#} px at final " +
                       "size) — expected for this action, not flagged");
        else if (atFinalSize >= 2f)
        {
            Reject(subject, action);
            problems.Add($"{baseName}: the subject's feet move {spread} px between frames " +
                         $"({atFinalSize:0.#} px at final size) — it will bob. Frames should share " +
                         "a baseline; regenerate rather than importing.");
        }
        else if (spread > 0)
            report.Add($"    baseline drift {spread} px across frames (negligible at final size)");
    }

    /// <summary>
    /// Measures an already-imported idle sheet so a later batch can be compared against it.
    ///
    /// Without this, ShapesBySubject only ever holds the current run, and the check that exists
    /// precisely to catch "the walk does not match the idle" is dead whenever the two arrive in
    /// separate batches — which is the normal case, since a rejected sheet is redelivered alone.
    /// </summary>
    private static SubjectShape LoadReferenceShape(string subject)
    {
        // Subject → filename is not reversible ("characters" becomes the "char" of
        // sheet_char_player_idle), so the sheet is found by matching the tail of the name.
        foreach (string guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ArtRoot }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            string file = Path.GetFileNameWithoutExtension(path);
            if (file != $"{subject}_idle"
                && !file.EndsWith($"_{subject}_idle", StringComparison.OrdinalIgnoreCase)) continue;

            var sprites = AssetDatabase.LoadAllAssetRepresentationsAtPath(path).OfType<Sprite>().ToList();
            if (sprites.Count == 0) return null;

            // The slice rects are the cell grid, which is why the manifest is not needed here.
            int cellW = Mathf.RoundToInt(sprites[0].rect.width);
            int cellH = Mathf.RoundToInt(sprites[0].rect.height);
            if (cellW <= 0 || cellH <= 0) return null;

            // Imported textures are not readable, and flipping that setting would reimport the
            // asset as a side effect — so the PNG is re-read off disk instead.
            string absolute = Path.Combine(Directory.GetParent(Application.dataPath).FullName, path);
            if (!File.Exists(absolute)) return null;

            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            try
            {
                if (!tex.LoadImage(File.ReadAllBytes(absolute))) return null;

                int columns = Mathf.Max(1, tex.width / cellW);
                int rows = Mathf.Max(1, tex.height / cellH);
                int frames = Mathf.Min(sprites.Count, columns * rows);

                CellMetrics metrics = MeasureCells(tex, cellW, cellH, columns, frames);
                if (metrics.Measured == 0) return null;

                return new SubjectShape
                {
                    Sheet  = file + " (already imported)",
                    Action = "idle",
                    Width  = metrics.WidthFraction,
                    Height = metrics.HeightFraction
                };
            }
            catch (Exception)
            {
                return null;
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(tex);
            }
        }
        return null;
    }

    /// <summary>Crops to the opaque bounding box, so untrimmed art cannot silently render small.</summary>
    private static string TrimToContent(ref Texture2D tex)
    {
        Color32[] px = tex.GetPixels32();
        int w = tex.width, h = tex.height;

        int minX = w, minY = h, maxX = -1, maxY = -1;
        for (int y = 0; y < h; y++)
        {
            for (int x = 0; x < w; x++)
            {
                if (px[y * w + x].a <= 8) continue;
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
            }
        }

        if (maxX < 0) return null;                                   // nothing opaque at all
        if (minX == 0 && minY == 0 && maxX == w - 1 && maxY == h - 1) return null;  // already tight

        int newW = maxX - minX + 1;
        int newH = maxY - minY + 1;

        // GetPixels32 has no region overload — the float Color path does.
        var cropped = new Texture2D(newW, newH, TextureFormat.RGBA32, false);
        cropped.SetPixels(tex.GetPixels(minX, minY, newW, newH));
        cropped.Apply();

        UnityEngine.Object.DestroyImmediate(tex);
        tex = cropped;
        return $"trimmed {w}x{h} → {newW}x{newH}";
    }

    private static bool HasUsableAlpha(Texture2D tex)
    {
        Color32[] px = tex.GetPixels32();
        int transparent = 0;
        for (int i = 0; i < px.Length; i++) if (px[i].a <= 8) transparent++;
        return transparent > px.Length / 100;   // at least 1% — a trimmed sprite can be nearly solid
    }

    /// <summary>
    /// Box-filter reduction. Area averaging, not nearest-neighbour: a photographic source point
    /// sampled down to 65 px is aliased noise, whereas averaging gives the clean crushed look the
    /// digitised sprites of the era actually had. Point filtering at render time keeps it crisp.
    /// </summary>
    private static Texture2D AreaAverage(Texture2D src, int outW, int outH)
    {
        Color32[] source = src.GetPixels32();
        var result = new Color32[outW * outH];

        float xStep = (float)src.width / outW;
        float yStep = (float)src.height / outH;

        for (int y = 0; y < outH; y++)
        {
            int y0 = Mathf.FloorToInt(y * yStep);
            int y1 = Mathf.Min(src.height, Mathf.CeilToInt((y + 1) * yStep));
            if (y1 <= y0) y1 = y0 + 1;

            for (int x = 0; x < outW; x++)
            {
                int x0 = Mathf.FloorToInt(x * xStep);
                int x1 = Mathf.Min(src.width, Mathf.CeilToInt((x + 1) * xStep));
                if (x1 <= x0) x1 = x0 + 1;

                // Colour is weighted by alpha — averaging straight RGBA drags the colour of fully
                // transparent pixels into the edges and leaves a dark halo round every sprite.
                float r = 0f, g = 0f, b = 0f, a = 0f;
                int count = 0;

                for (int sy = y0; sy < y1; sy++)
                {
                    int row = sy * src.width;
                    for (int sx = x0; sx < x1; sx++)
                    {
                        Color32 c = source[row + sx];
                        float w = c.a / 255f;
                        r += c.r * w;
                        g += c.g * w;
                        b += c.b * w;
                        a += c.a;
                        count++;
                    }
                }

                if (count == 0) continue;

                float alpha = a / count;
                float weight = a / 255f;   // summed alpha, the divisor for the colour accumulation

                result[y * outW + x] = weight > 0.0001f
                    ? new Color32((byte)Mathf.Clamp(r / weight, 0f, 255f),
                                  (byte)Mathf.Clamp(g / weight, 0f, 255f),
                                  (byte)Mathf.Clamp(b / weight, 0f, 255f),
                                  (byte)Mathf.Clamp(alpha, 0f, 255f))
                    : new Color32(0, 0, 0, 0);
            }
        }

        var outTex = new Texture2D(outW, outH, TextureFormat.RGBA32, false);
        outTex.SetPixels32(result);
        outTex.Apply();
        return outTex;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  IMPORT SETTINGS AND SLICING
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static bool ApplyImportSettings(string assetPath, ArtManifest m, bool isSheet, List<string> problems)
    {
        var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
        if (importer == null)
        {
            problems.Add($"{assetPath}: no TextureImporter yet, so import settings and slicing " +
                         "were skipped and the asset landed with Unity's defaults. This happens " +
                         "when the import is deferred — do not batch these inside StartAssetEditing.");
            return false;
        }

        importer.textureType         = TextureImporterType.Sprite;
        importer.spritePixelsPerUnit = PixelsPerUnit;
        // Point, not bilinear: the pixels are the art now, and filtering would smear the very
        // thing the reduction just created. This is also why the existing 64x64 orcs look mushy.
        importer.filterMode          = FilterMode.Point;
        importer.alphaIsTransparency = true;
        importer.mipmapEnabled       = false;
        importer.maxTextureSize      = MaxTextureSize;
        importer.textureCompression  = TextureImporterCompression.Uncompressed;
        importer.spriteImportMode    = isSheet ? SpriteImportMode.Multiple : SpriteImportMode.Single;
        // Sheet dimensions are whatever the grid needs and are rarely powers of two. Left at the
        // default the texture is rescaled to the nearest power of two and every slice rectangle
        // lands in the wrong place.
        importer.npotScale           = TextureImporterNPOTScale.None;

        if (isSheet)
        {
            SpriteMetaData[] slices = Slice(assetPath, m, problems);
            // Deliberately not an early return. Slicing is the part most likely to go wrong, and
            // bailing here once left the asset imported with Unity's defaults — Default type,
            // PPU 100, bilinear — which is far worse than an unsliced sprite.
            //
            // CS0618: the replacement, UnityEditor.U2D.Sprites.ISpriteEditorDataProvider, ships in
            // com.unity.2d.sprite, which is not in Packages/manifest.json — so in this project the
            // modern API does not exist and this one still works. VerifySliced below is the guard
            // for the day that stops being true: it checks the sub-sprites actually appeared rather
            // than trusting the assignment.
#pragma warning disable 618
            if (slices != null) importer.spritesheet = slices;
#pragma warning restore 618
        }

        importer.SaveAndReimport();

        if (isSheet) VerifySliced(assetPath, m, problems);
        return true;
    }

    /// <summary>
    /// Confirms the slices actually became sub-sprites. TextureImporter.spritesheet is deprecated
    /// with a message claiming support has been removed; if it ever becomes a genuine no-op this
    /// is what will say so, rather than the sheet quietly importing as one undivided image.
    /// </summary>
    private static void VerifySliced(string assetPath, ArtManifest m, List<string> problems)
    {
        int found = AssetDatabase.LoadAllAssetRepresentationsAtPath(assetPath).OfType<Sprite>().Count();
        int expected = m.frameCount > 0 ? m.frameCount : Mathf.Max(1, m.columns) * Mathf.Max(1, m.rows);
        if (found >= expected) return;

        problems.Add($"{m.name}: expected {expected} sub-sprites after slicing but found {found}. " +
                     "If this is zero, TextureImporter.spritesheet has stopped working in this Unity " +
                     "version and the slicing needs moving to ISpriteEditorDataProvider.");
    }

    private static SpriteMetaData[] Slice(string assetPath, ArtManifest m, List<string> problems)
    {
        if (m.frameWidth <= 0 || m.frameHeight <= 0)
        {
            problems.Add($"{assetPath}: sheet needs frameWidth and frameHeight.");
            return null;
        }

        // Measured from the manifest, never from the imported texture. Reduce() has already
        // rewritten these to the post-reduction cell size, and asking Unity for the texture's
        // dimensions here returns whatever the *previous* import settings produced — for a
        // not-yet-a-sprite texture that is the power-of-two rescale, which is one pixel short and
        // throws the whole grid out.
        int columns = Mathf.Max(1, m.columns);
        int rows    = Mathf.Max(1, m.rows);
        int sheetHeight = rows * m.frameHeight;
        int total   = m.frameCount > 0 ? Mathf.Min(m.frameCount, columns * rows) : columns * rows;

        var slices = new List<SpriteMetaData>(total);
        for (int i = 0; i < total; i++)
        {
            int col = i % columns;
            int row = i / columns;

            // Frames read left-to-right then top-to-bottom, but Unity's texture origin is
            // bottom-left, so row 0 sits at the top of the image.
            float y = sheetHeight - (row + 1) * m.frameHeight;
            if (y < 0f)
            {
                problems.Add($"{assetPath}: frame {i} falls outside the image — check rows/frameHeight.");
                break;
            }

            slices.Add(new SpriteMetaData
            {
                name      = $"{Path.GetFileNameWithoutExtension(assetPath)}_{i}",
                rect      = new Rect(col * m.frameWidth, y, m.frameWidth, m.frameHeight),
                alignment = (int)SpriteAlignment.Center,
                pivot     = new Vector2(0.5f, 0.5f)
            });
        }

        return slices.Count > 0 ? slices.ToArray() : null;
    }

    private static Sprite[] LoadFramesInOrder(string assetPath, string baseName, ArtManifest m)
    {
        var byName = AssetDatabase.LoadAllAssetRepresentationsAtPath(assetPath)
            .OfType<Sprite>()
            .ToDictionary(s => s.name, s => s);

        var ordered = new List<Sprite>();
        for (int i = 0; ; i++)
        {
            if (!byName.TryGetValue($"{baseName}_{i}", out Sprite s)) break;
            ordered.Add(s);
        }
        return ordered.ToArray();
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  CLIPS AND CONTROLLER
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static AnimationClip BuildClip(string baseName, ArtManifest m, Sprite[] frames)
    {
        EnsureFolder(AnimRoot);
        string clipPath = $"{AnimRoot}/{baseName}.anim";

        float fps = m.fps > 0f ? m.fps : 10f;

        var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
        bool isNew = clip == null;
        if (isNew) clip = new AnimationClip();
        clip.frameRate = fps;

        var binding = new EditorCurveBinding
        {
            type = typeof(SpriteRenderer),
            // Empty means the SpriteRenderer sits on the same GameObject as the Animator, which
            // is what every existing clip in Assets/Animations does.
            path = m.rendererPath ?? "",
            propertyName = "m_Sprite"
        };

        var keys = new ObjectReferenceKeyframe[frames.Length];
        for (int i = 0; i < frames.Length; i++)
            keys[i] = new ObjectReferenceKeyframe { time = i / fps, value = frames[i] };

        AnimationUtility.SetObjectReferenceCurve(clip, binding, keys);

        var settings = AnimationUtility.GetAnimationClipSettings(clip);
        settings.loopTime = m.loop;
        AnimationUtility.SetAnimationClipSettings(clip, settings);

        if (isNew) AssetDatabase.CreateAsset(clip, clipPath);
        else EditorUtility.SetDirty(clip);

        return clip;
    }

    private static void BuildController(string subject, Dictionary<string, AnimationClip> clips, List<string> report)
    {
        EnsureFolder(AnimRoot);
        string path = $"{AnimRoot}/{subject}_Controller.controller";

        var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
        if (controller == null) controller = AnimatorController.CreateAnimatorControllerAtPath(path);

        // The parameter names the game already calls: CombatController and EnemyAI use Speed,
        // MeleeAttack, Hit and Death, and CombatController also calls CastSpell — which no
        // controller in the project defines today.
        EnsureParameter(controller, "Speed", AnimatorControllerParameterType.Float);
        EnsureParameter(controller, CyclingParameter, AnimatorControllerParameterType.Bool);
        foreach (string trigger in ActionToTrigger.Values)
            EnsureParameter(controller, trigger, AnimatorControllerParameterType.Trigger);

        var sm = controller.layers[0].stateMachine;

        AnimatorState batchIdle = null;

        foreach (var kv in clips)
        {
            string stateName = ActionToState[kv.Key];
            AnimatorState state = FindState(sm, stateName) ?? sm.AddState(stateName);
            state.motion = kv.Value;
            if (kv.Key == "idle") batchIdle = state;
        }

        // ⚠️ Everything below wires the controller from the states it *holds*, never from the clips
        // this batch happened to deliver. It used to do the opposite and that broke two ways at
        // once: all of the wiring sat behind "this batch contains an idle sheet", so a batch of
        // attack/cast/death alone added three states and not one transition; and the one-shot loop
        // only considered the batch's own clips, so even a batch with idle in it could not reach a
        // state a previous run had left orphaned. The player shipped with Attack, Cast and Death
        // fully built, motions and all, and no transition anywhere to reach them.
        //
        // Every add is also guarded against an equivalent already being present, because nothing
        // here used to check: each idle-bearing re-run stacked another full set of transitions on
        // top of the last. Re-running is now a no-op on a controller that is already wired.
        int removed = RemoveDuplicateTransitions(sm);

        // The batch's idle, else whatever the controller already calls Idle, else whatever it
        // currently starts in — a one-shot needs somewhere to return to, and any of the three will
        // do. Only an existing controller with no states and no default leaves this null.
        AnimatorState idle = batchIdle ?? FindState(sm, ActionToState["idle"]) ?? sm.defaultState;

        if (idle == null)
        {
            report.Add($"{subject}: controller built, but it has no Idle state and no default state " +
                       "to return to — transitions left unwired.");
        }
        else
        {
            sm.defaultState = idle;

            AnimatorState run = FindState(sm, ActionToState["walk"]);
            if (run != null && run != idle)
            {
                AddTransition(idle, run, "Speed", AnimatorConditionMode.Greater, 0.1f);
                AddTransition(run, idle, "Speed", AnimatorConditionMode.Less, 0.1f);
            }

            // Cycling is held for as long as you are on the vehicle, so it is a bool from Any
            // State rather than a one-shot trigger, and it returns to idle when the bool clears.
            AnimatorState cycle = FindState(sm, ActionToState["cycle"]);
            if (cycle != null && cycle != idle)
            {
                AddAnyStateTransition(sm, cycle, CyclingParameter, 0.05f);
                AddTransition(cycle, idle, CyclingParameter, AnimatorConditionMode.IfNot, 0f);
            }

            // One-shots fire from Any State on their trigger and fall back to idle when finished.
            foreach (var kv in ActionToTrigger)
            {
                AnimatorState state = FindState(sm, ActionToState[kv.Key]);
                if (state == null) continue;

                AddAnyStateTransition(sm, state, kv.Value, 0f);

                if (kv.Key == "death") continue; // dead things stay dead

                // Only reachable when idle fell back to a default state that is itself a one-shot;
                // returning it to itself would trap the state machine in a loop.
                if (state == idle) continue;

                if (HasUnconditionalTransition(state.transitions, idle)) continue;

                var back = state.AddTransition(idle);
                back.hasExitTime = true;
                back.exitTime = 1f;
                back.duration = 0f;
            }
        }

        EditorUtility.SetDirty(controller);
        string dedupeNote = removed > 0 ? $" ({removed} duplicate transition(s) removed)" : "";
        report.Add($"{subject}_Controller → {string.Join(", ", clips.Keys.OrderBy(k => k))}{dedupeNote}");
    }

    private static void AddTransition(AnimatorState from, AnimatorState to, string parameter,
        AnimatorConditionMode mode, float threshold)
    {
        if (HasConditionalTransition(from.transitions, to, parameter, mode)) return;

        var t = from.AddTransition(to);
        t.hasExitTime = false;
        t.duration = 0.05f;
        t.AddCondition(mode, threshold, parameter);
    }

    /// <summary>Any State → <paramref name="to"/> when <paramref name="parameter"/> is set, once.</summary>
    private static void AddAnyStateTransition(AnimatorStateMachine sm, AnimatorState to,
        string parameter, float duration)
    {
        if (HasConditionalTransition(sm.anyStateTransitions, to, parameter, AnimatorConditionMode.If))
            return;

        var any = sm.AddAnyStateTransition(to);
        any.hasExitTime = false;
        any.duration = duration;
        any.canTransitionToSelf = false;
        any.AddCondition(AnimatorConditionMode.If, 0f, parameter);
    }

    /// <summary>
    /// True if one of <paramref name="transitions"/> already lands on <paramref name="to"/> driven by
    /// <paramref name="parameter"/> in <paramref name="mode"/>. The threshold is deliberately not
    /// part of the comparison: two transitions to the same state on the same condition are the same
    /// piece of wiring however each is tuned, and only the first of them can ever fire.
    /// </summary>
    private static bool HasConditionalTransition(IEnumerable<AnimatorStateTransition> transitions,
        AnimatorState to, string parameter, AnimatorConditionMode mode)
    {
        foreach (AnimatorStateTransition t in transitions)
        {
            if (t == null || t.destinationState != to || t.conditions == null) continue;
            foreach (AnimatorCondition c in t.conditions)
                if (c.parameter == parameter && c.mode == mode) return true;
        }
        return false;
    }

    /// <summary>
    /// True if one of <paramref name="transitions"/> reaches <paramref name="to"/> on no condition at
    /// all — the exit-time return a one-shot state uses to fall back to idle.
    /// </summary>
    private static bool HasUnconditionalTransition(IEnumerable<AnimatorStateTransition> transitions,
        AnimatorState to)
    {
        foreach (AnimatorStateTransition t in transitions)
            if (t != null && t.destinationState == to && (t.conditions == null || t.conditions.Length == 0))
                return true;
        return false;
    }

    /// <summary>
    /// A transition's identity for dedupe purposes: where it lands, and what fires it. Timing is
    /// excluded for the reason given on <see cref="HasConditionalTransition"/>.
    /// </summary>
    private static string TransitionSignature(AnimatorStateTransition t)
    {
        var sb = new System.Text.StringBuilder();
        sb.Append(t.destinationState != null ? t.destinationState.name : "-");
        sb.Append('/');
        sb.Append(t.destinationStateMachine != null ? t.destinationStateMachine.name : "-");

        // Sorted so that two transitions carrying the same conditions in a different order still
        // read as the same wiring.
        AnimatorCondition[] conditions = t.conditions ?? new AnimatorCondition[0];
        foreach (AnimatorCondition c in conditions.OrderBy(x => x.parameter).ThenBy(x => (int)x.mode))
            sb.Append('|').Append(c.parameter).Append(':').Append((int)c.mode);

        return sb.ToString();
    }

    /// <summary>
    /// Drops any transition that repeats one already present on the same source — same destination,
    /// same conditions. Only the first of such a pair can ever fire, so this changes no behaviour.
    /// It exists because the wiring above used to add transitions unguarded, and the player's
    /// controller shipped carrying every one of its four transitions twice. Returns how many went.
    /// </summary>
    private static int RemoveDuplicateTransitions(AnimatorStateMachine sm)
    {
        int removed = 0;
        var seen = new HashSet<string>();

        // Snapshot before mutating: the getters build a fresh array today, but removing from a live
        // collection mid-iteration is not something to leave resting on that.
        AnimatorStateTransition[] fromAny = sm.anyStateTransitions;
        foreach (AnimatorStateTransition t in fromAny)
        {
            if (t == null || seen.Add(TransitionSignature(t))) continue;
            sm.RemoveAnyStateTransition(t);
            removed++;
        }

        foreach (ChildAnimatorState child in sm.states)
        {
            if (child.state == null) continue;

            seen.Clear();
            AnimatorStateTransition[] own = child.state.transitions;
            foreach (AnimatorStateTransition t in own)
            {
                if (t == null || seen.Add(TransitionSignature(t))) continue;
                child.state.RemoveTransition(t);
                removed++;
            }
        }

        return removed;
    }

    private static AnimatorState FindState(AnimatorStateMachine sm, string name)
    {
        foreach (ChildAnimatorState child in sm.states)
            if (child.state != null && child.state.name == name) return child.state;
        return null;
    }

    private static void EnsureParameter(AnimatorController controller, string name,
        AnimatorControllerParameterType type)
    {
        foreach (var p in controller.parameters)
            if (p.name == name) return;
        controller.AddParameter(name, type);
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  HELPERS
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void EnsureFolder(string assetFolder)
    {
        if (AssetDatabase.IsValidFolder(assetFolder)) return;

        string[] parts = assetFolder.Split('/');
        string running = parts[0]; // "Assets"
        for (int i = 1; i < parts.Length; i++)
        {
            string next = $"{running}/{parts[i]}";
            if (!AssetDatabase.IsValidFolder(next))
                AssetDatabase.CreateFolder(running, parts[i]);
            running = next;
        }
    }

    private static void Summarise(List<string> report, List<string> problems, List<string> warnings,
        List<string> questions)
    {
        var log = new System.Text.StringBuilder();
        log.AppendLine("Import Generated Art");
        log.AppendLine("────────────────────");

        if (report.Count == 0) log.AppendLine("Nothing imported.");
        foreach (string line in report) log.AppendLine("  " + line);

        if (questions.Count > 0)
        {
            log.AppendLine();
            log.AppendLine("Questions from the art agent:");
            foreach (string q in questions) log.AppendLine("  ? " + q);
        }

        // Kept apart from problems on purpose: a warning does not hold the asset in staging, so
        // lumping the two together would strand a perfectly good sheet over a house-style nit.
        if (warnings.Count > 0)
        {
            log.AppendLine();
            log.AppendLine("Warnings (imported anyway):");
            foreach (string w in warnings) log.AppendLine("  ~ " + w);
        }

        if (problems.Count > 0)
        {
            log.AppendLine();
            log.AppendLine("Problems (these pairs stay in art_incoming/):");
            foreach (string p in problems) log.AppendLine("  ! " + p);
        }

        if (problems.Count > 0) Debug.LogWarning(log.ToString());
        else Debug.Log(log.ToString());

        EditorUtility.DisplayDialog("Import Generated Art",
            $"{report.Count} imported, {problems.Count} problem(s), {warnings.Count} warning(s), " +
            $"{questions.Count} question(s).\n\nFull detail in the Console.", "OK");
    }
}
