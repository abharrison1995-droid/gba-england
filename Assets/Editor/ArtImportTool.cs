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
/// Run via: Tools → Exiled Alvaston → Art → Import Generated Art
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
    private const string ArtRoot        = "Assets/Art/Generated";
    private const string AnimRoot       = "Assets/Animations/Generated";
    private const float  PixelsPerUnit  = 100f;   // matches the sprites already in Assets/Sprites
    private const int    MaxTextureSize = 2048;

    /// <summary>Action name in the JSON → state name in the controller → parameter that fires it.</summary>
    private static readonly Dictionary<string, string> ActionToState = new Dictionary<string, string>
    {
        { "idle",   "Idle"   },
        { "walk",   "Run"    },   // "Run" matches the existing Bandit_Controller
        { "attack", "Attack" },
        { "hurt",   "Hurt"   },
        { "death",  "Death"  },
        { "cast",   "Cast"   },
    };

    private static readonly Dictionary<string, string> ActionToTrigger = new Dictionary<string, string>
    {
        { "attack", "MeleeAttack" },
        { "hurt",   "Hit"         },
        { "death",  "Death"       },
        { "cast",   "CastSpell"   },   // nothing in the project defines this yet — see CLAUDE.md §8
    };

    [Serializable]
    private class ArtManifest
    {
        public string name;
        public string type;          // "single" | "sheet"
        public string category;      // characters | vehicles | props | fx | ui
        public string subject;       // optional; defaults to name minus the action suffix
        public string action;        // idle | walk | attack | hurt | death | cast
        public string rendererPath;  // optional animation binding path; empty = same GameObject
        public float worldHeight;
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

    [MenuItem("Tools/Exiled Alvaston/Art/Import Generated Art")]
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
                "same name — see ART_PIPELINE.md.", "OK");
            return;
        }

        var report = new List<string>();
        var problems = new List<string>();
        var questions = new List<string>();

        // Controllers are built after every clip exists, so a subject's states can all be wired
        // in one pass rather than rebuilt per action.
        var clipsBySubject = new Dictionary<string, Dictionary<string, AnimationClip>>();

        try
        {
            AssetDatabase.StartAssetEditing();

            foreach (string manifestPath in manifests)
            {
                ImportOne(manifestPath, staging, report, problems, questions, clipsBySubject);
            }
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
            AssetDatabase.Refresh();
        }

        foreach (var kv in clipsBySubject)
        {
            try
            {
                BuildController(kv.Key, kv.Value, report);
            }
            catch (Exception e)
            {
                problems.Add($"{kv.Key}: controller failed — {e.Message}");
            }
        }

        AutoAssign(report, problems);

        AssetDatabase.SaveAssets();
        Summarise(report, problems, questions);
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  AUTO-ASSIGNMENT
    //  Imported art is wired into the things that were waiting for it, so a batch of sprites
    //  does not need a follow-up round of hand-dragging in the Inspector.
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void AutoAssign(List<string> report, List<string> problems)
    {
        AssignPlayerSprite("spr_char_player", false, report, problems);
        AssignPlayerSprite("spr_char_player_moped", true, report, problems);
        AssignMopedSprite("spr_vehicle_moped", report, problems);
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

    /// <summary>Player sprite or the sat-on-a-moped variant, on the WorldActorVisual in the open scene.</summary>
    private static void AssignPlayerSprite(string baseName, bool mounted, List<string> report, List<string> problems)
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
        if (mounted) visual.MountedSprite = sprite;
        else visual.ActorSprite = sprite;

        EditorUtility.SetDirty(visual);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(player.gameObject.scene);
        report.Add($"    assigned to player WorldActorVisual.{(mounted ? "MountedSprite" : "ActorSprite")} " +
                   "— save the scene (Ctrl+S)");
    }

    /// <summary>Parked moped art, written into the prefab in place so the GUID survives.</summary>
    private static void AssignMopedSprite(string baseName, List<string> report, List<string> problems)
    {
        Sprite sprite = FindImported(baseName);
        if (sprite == null) return;

        const string prefabPath = "Assets/Prefabs/ModernBritain/Moped.prefab";
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
                problems.Add($"{baseName}: Moped.prefab has no VehicleController.");
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
            report.Add("    assigned to Moped.prefab (VehicleSprite + parked visual)");
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(contents);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  ONE ASSET
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void ImportOne(string manifestPath, string staging, List<string> report,
        List<string> problems, List<string> questions,
        Dictionary<string, Dictionary<string, AnimationClip>> clipsBySubject)
    {
        string baseName = Path.GetFileNameWithoutExtension(manifestPath);

        ArtManifest m;
        try
        {
            m = JsonUtility.FromJson<ArtManifest>(File.ReadAllText(manifestPath));
        }
        catch (Exception e)
        {
            problems.Add($"{baseName}.json is not valid JSON — {e.Message}");
            return;
        }
        if (m == null)
        {
            problems.Add($"{baseName}.json parsed as empty.");
            return;
        }

        if (!string.IsNullOrEmpty(m.question))
            questions.Add($"{baseName}: {m.question}");

        string png = Path.Combine(staging, baseName + ".png");
        if (!File.Exists(png))
        {
            problems.Add($"{baseName}.json has no matching {baseName}.png.");
            return;
        }

        string category = string.IsNullOrEmpty(m.category) ? "props" : m.category.ToLowerInvariant();
        string destFolder = $"{ArtRoot}/{category}";
        EnsureFolder(destFolder);

        string destPath = $"{destFolder}/{baseName}.png";
        File.Copy(png, Path.Combine(Directory.GetParent(Application.dataPath).FullName, destPath), true);
        AssetDatabase.ImportAsset(destPath, ImportAssetOptions.ForceUpdate);

        bool isSheet = string.Equals(m.type, "sheet", StringComparison.OrdinalIgnoreCase);
        if (!ApplyImportSettings(destPath, m, isSheet, problems)) return;

        if (!isSheet)
        {
            report.Add($"{baseName} → {destFolder} (single)");
            return;
        }

        Sprite[] frames = LoadFramesInOrder(destPath, baseName, m);
        if (frames.Length == 0)
        {
            problems.Add($"{baseName}: sliced to zero frames — check frameWidth/frameHeight against the image.");
            return;
        }

        AnimationClip clip = BuildClip(baseName, m, frames);
        report.Add($"{baseName} → {destFolder} ({frames.Length} frames, {m.fps:0.#} fps) + clip");

        string subject = ResolveSubject(m, baseName);
        string action = (m.action ?? "").ToLowerInvariant();
        if (string.IsNullOrEmpty(action) || !ActionToState.ContainsKey(action))
        {
            report.Add($"    (no recognised action — clip made, not wired into a controller)");
            return;
        }

        if (!clipsBySubject.TryGetValue(subject, out var byAction))
        {
            byAction = new Dictionary<string, AnimationClip>();
            clipsBySubject[subject] = byAction;
        }
        byAction[action] = clip;
    }

    private static string ResolveSubject(ArtManifest m, string baseName)
    {
        if (!string.IsNullOrEmpty(m.subject)) return m.subject;

        string name = string.IsNullOrEmpty(m.name) ? baseName : m.name;
        if (!string.IsNullOrEmpty(m.action) && name.EndsWith("_" + m.action, StringComparison.OrdinalIgnoreCase))
            return name.Substring(0, name.Length - m.action.Length - 1);

        return name;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  IMPORT SETTINGS AND SLICING
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static bool ApplyImportSettings(string assetPath, ArtManifest m, bool isSheet, List<string> problems)
    {
        var importer = AssetImporter.GetAtPath(assetPath) as TextureImporter;
        if (importer == null)
        {
            problems.Add($"{assetPath}: no TextureImporter — is it a valid PNG?");
            return false;
        }

        importer.textureType         = TextureImporterType.Sprite;
        importer.spritePixelsPerUnit = PixelsPerUnit;
        importer.filterMode          = FilterMode.Bilinear;
        importer.alphaIsTransparency = true;
        importer.mipmapEnabled       = false;
        importer.maxTextureSize      = MaxTextureSize;
        importer.spriteImportMode    = isSheet ? SpriteImportMode.Multiple : SpriteImportMode.Single;

        if (isSheet)
        {
            SpriteMetaData[] slices = Slice(assetPath, m, problems);
            if (slices == null) return false;
            importer.spritesheet = slices;
        }

        importer.SaveAndReimport();
        return true;
    }

    private static SpriteMetaData[] Slice(string assetPath, ArtManifest m, List<string> problems)
    {
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(assetPath);
        if (texture == null)
        {
            problems.Add($"{assetPath}: could not load the texture to slice it.");
            return null;
        }

        if (m.frameWidth <= 0 || m.frameHeight <= 0)
        {
            problems.Add($"{assetPath}: sheet needs frameWidth and frameHeight.");
            return null;
        }

        int columns = m.columns > 0 ? m.columns : Mathf.Max(1, texture.width / m.frameWidth);
        int rows    = m.rows    > 0 ? m.rows    : Mathf.Max(1, texture.height / m.frameHeight);
        int total   = m.frameCount > 0 ? Mathf.Min(m.frameCount, columns * rows) : columns * rows;

        var slices = new List<SpriteMetaData>(total);
        for (int i = 0; i < total; i++)
        {
            int col = i % columns;
            int row = i / columns;

            // Frames read left-to-right then top-to-bottom, but Unity's texture origin is
            // bottom-left, so row 0 sits at the top of the image.
            float y = texture.height - (row + 1) * m.frameHeight;
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
        foreach (string trigger in ActionToTrigger.Values)
            EnsureParameter(controller, trigger, AnimatorControllerParameterType.Trigger);

        var sm = controller.layers[0].stateMachine;

        AnimatorState idle = null;
        var states = new Dictionary<string, AnimatorState>();

        foreach (var kv in clips)
        {
            string stateName = ActionToState[kv.Key];
            AnimatorState state = FindState(sm, stateName) ?? sm.AddState(stateName);
            state.motion = kv.Value;
            states[kv.Key] = state;
            if (kv.Key == "idle") idle = state;
        }

        if (idle == null)
        {
            report.Add($"{subject}: controller built, but no idle sheet — default state left as-is.");
        }
        else
        {
            sm.defaultState = idle;

            if (states.TryGetValue("walk", out AnimatorState run))
            {
                AddTransition(idle, run, "Speed", AnimatorConditionMode.Greater, 0.1f);
                AddTransition(run, idle, "Speed", AnimatorConditionMode.Less, 0.1f);
            }

            // One-shots fire from Any State on their trigger and fall back to idle when finished.
            foreach (var kv in ActionToTrigger)
            {
                if (!states.TryGetValue(kv.Key, out AnimatorState state)) continue;

                var any = sm.AddAnyStateTransition(state);
                any.hasExitTime = false;
                any.duration = 0f;
                any.canTransitionToSelf = false;
                any.AddCondition(AnimatorConditionMode.If, 0f, kv.Value);

                if (kv.Key == "death") continue; // dead things stay dead

                var back = state.AddTransition(idle);
                back.hasExitTime = true;
                back.exitTime = 1f;
                back.duration = 0f;
            }
        }

        EditorUtility.SetDirty(controller);
        report.Add($"{subject}_Controller → {string.Join(", ", clips.Keys.OrderBy(k => k))}");
    }

    private static void AddTransition(AnimatorState from, AnimatorState to, string parameter,
        AnimatorConditionMode mode, float threshold)
    {
        var t = from.AddTransition(to);
        t.hasExitTime = false;
        t.duration = 0.05f;
        t.AddCondition(mode, threshold, parameter);
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

    private static void Summarise(List<string> report, List<string> problems, List<string> questions)
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

        if (problems.Count > 0)
        {
            log.AppendLine();
            log.AppendLine("Problems:");
            foreach (string p in problems) log.AppendLine("  ! " + p);
        }

        if (problems.Count > 0) Debug.LogWarning(log.ToString());
        else Debug.Log(log.ToString());

        EditorUtility.DisplayDialog("Import Generated Art",
            $"{report.Count} imported, {problems.Count} problem(s), {questions.Count} question(s).\n\n" +
            "Full detail in the Console.", "OK");
    }
}
