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
    private const int    MaxTextureSize = 2048;

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
    };

    /// <summary>Bool parameters, for states that are held rather than fired once.</summary>
    private const string CyclingParameter = "Cycling";

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
        ShapesBySubject.Clear();

        // Controllers are built after every clip exists, so a subject's states can all be wired
        // in one pass rather than rebuilt per action.
        var clipsBySubject = new Dictionary<string, Dictionary<string, AnimationClip>>();

        // Deliberately not wrapped in StartAssetEditing/StopAssetEditing. That batches — and
        // therefore defers — the ImportAsset calls, so AssetImporter.GetAtPath returns null for a
        // file that was only just written, the import settings never apply, and the asset lands
        // with Unity's defaults: Default texture type, no slices, no clips. A handful of assets
        // per run makes the batching worthless anyway.
        foreach (string manifestPath in manifests)
        {
            ImportOne(manifestPath, staging, report, problems, questions, clipsBySubject);
        }

        AssetDatabase.Refresh();

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

        CompareSubjectShapes(problems);
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
        AssignPlayerRestingFrame(report, problems);
        AssignPlayerSprite("spr_char_player_ebike", true, report, problems);
        AssignVehicleSprite("spr_vehicle_ebike", report, problems);
        AssignPlayerController("player", report, problems);
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

    /// <summary>Player sprite, or the riding variant, on the WorldActorVisual in the open scene.</summary>
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

        bool isSheet = string.Equals(m.type, "sheet", StringComparison.OrdinalIgnoreCase);

        string destPath = $"{destFolder}/{baseName}.png";
        string destAbsolute = Path.Combine(Directory.GetParent(Application.dataPath).FullName, destPath);

        if (!Reduce(png, destAbsolute, m, isSheet, problems, report)) return;

        AssetDatabase.ImportAsset(destPath, ImportAssetOptions.ForceUpdate);
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
    //  REDUCTION
    //  Sources arrive photoreal and large. The look comes from crushing them down here, not
    //  from asking a generator for low resolution — image models draw "fake pixel art" with an
    //  inconsistent grid, whereas a deterministic reduction gives the same treatment to every
    //  asset forever, however far apart they were generated.
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static bool Reduce(string sourcePath, string destAbsolute, ArtManifest m, bool isSheet,
        List<string> problems, List<string> report)
    {
        var src = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!src.LoadImage(File.ReadAllBytes(sourcePath)))
        {
            problems.Add($"{Path.GetFileName(sourcePath)}: could not be read as a PNG.");
            return false;
        }

        float worldHeight = m.worldHeight > 0f ? m.worldHeight : 1.35f;

        // Generators are poor at producing a real alpha channel and good at putting a subject on a
        // plain backdrop, so the contract asks for flat magenta and the backdrop is removed here.
        string keyNote = KeyOutBackground(src);
        if (keyNote != null) report.Add("    " + keyNote);

        // Trimming is not left to the generator either — sizing is derived from full image height,
        // so untrimmed art silently renders small. Sheets are never trimmed: the grid must stay
        // uniform or every frame shifts.
        if (!isSheet)
        {
            string trimNote = TrimToContent(ref src);
            if (trimNote != null) report.Add("    " + trimNote);
        }

        if (isSheet) CheckFrameAlignment(src, m, report, problems);

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
    /// Returns a note for the report, or null if the image already had alpha.
    /// </summary>
    private static string KeyOutBackground(Texture2D tex)
    {
        Color32[] px = tex.GetPixels32();
        int w = tex.width, h = tex.height;

        // Already has real transparency at the edges — nothing to key.
        if (px[0].a < 8 && px[w - 1].a < 8 && px[(h - 1) * w].a < 8 && px[h * w - 1].a < 8)
            return null;

        // Average the border, then check the border actually is one flat colour. A gradient
        // backdrop is not safely keyable and is better reported than half-removed.
        long sr = 0, sg = 0, sb = 0;
        int count = 0;
        foreach (int i in BorderIndices(w, h)) { sr += px[i].r; sg += px[i].g; sb += px[i].b; count++; }
        var seed = new Color32((byte)(sr / count), (byte)(sg / count), (byte)(sb / count), 255);

        float worst = 0f;
        foreach (int i in BorderIndices(w, h)) worst = Mathf.Max(worst, Distance(px[i], seed));
        if (worst > 90f)
            return $"background is not flat (border varies by {worst:0}) — not keyed, expect a backdrop";

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
        return $"keyed out backdrop ({cleared * 100 / px.Length}% cleared, {unmixed} edge pixels unmixed)";
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

    /// <summary>
    /// Warns when the subject does not sit on the same baseline in every cell. Sheets are not
    /// trimmed, so a figure that drifts up the cell between frames bobs and floats once it is
    /// playing — and at 65 px that is very visible while being almost impossible to spot in the
    /// source. Cheap to measure here, painful to notice in game.
    /// </summary>
    /// <summary>How much of its cell the subject fills, for comparing sheets of the same subject.</summary>
    private class SubjectShape
    {
        public string Sheet;
        public string Action;
        public float Width;   // fraction of cell width
        public float Height;  // fraction of cell height
    }

    /// <summary>
    /// Actions where the figure is *supposed* to change shape — falling over, sitting on a bike.
    /// Height and baseline comparisons are meaningless for these; width still is not, because no
    /// legitimate pose makes a character half as wide as they are standing.
    /// </summary>
    private static bool ShapeChanges(string action) => action == "death" || action == "cycle";

    private static readonly Dictionary<string, List<SubjectShape>> ShapesBySubject =
        new Dictionary<string, List<SubjectShape>>();

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
            if (shapes.Count < 2) continue;

            // Idle is the canonical standing pose and the reference every other sheet is asked to
            // match; without one, fall back to the widest, which is the least likely to be the
            // edge-on mistake being hunted for.
            SubjectShape reference = shapes.Find(s => s.Action == "idle");
            if (reference == null)
            {
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
                    problems.Add($"{kv.Key}: '{s.Sheet}' is {narrowness:0.#}× narrower than " +
                                 $"'{reference.Sheet}' — the character is drawn at a different angle, " +
                                 "not the same person from the same view. Regenerate it using " +
                                 $"'{reference.Sheet}' as the visual reference.");

                if (ShapeChanges(s.Action)) continue;

                float ratio = Mathf.Max(reference.Height, s.Height) / Mathf.Min(reference.Height, s.Height);
                if (ratio > 1.15f)
                    problems.Add($"{kv.Key}: '{s.Sheet}' differs from '{reference.Sheet}' in height by " +
                                 $"{ratio:0.##}× — the character will change size between animations.");
            }
        }
    }

    private static void CheckFrameAlignment(Texture2D tex, ArtManifest m, List<string> report,
        List<string> problems)
    {
        if (m.frameWidth <= 0 || m.frameHeight <= 0) return;

        int columns = Mathf.Max(1, m.columns);
        int rows = Mathf.Max(1, m.rows);
        int frames = m.frameCount > 0 ? Mathf.Min(m.frameCount, columns * rows) : columns * rows;
        if (frames < 2) return;

        Color32[] px = tex.GetPixels32();
        int lowest = int.MaxValue, highest = int.MinValue;
        long widthSum = 0, heightSum = 0;
        int measured = 0;

        for (int f = 0; f < frames; f++)
        {
            int cx = (f % columns) * m.frameWidth;
            // Texture origin is bottom-left, so row 0 of the sheet is the top of the image.
            int cy = tex.height - ((f / columns) + 1) * m.frameHeight;

            int bottom = -1, top = -1, left = int.MaxValue, right = -1;
            for (int y = 0; y < m.frameHeight; y++)
            {
                for (int x = 0; x < m.frameWidth; x++)
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
            measured++;
        }

        if (measured > 0)
        {
            string subject = ResolveSubject(m, m.name ?? "");
            if (!ShapesBySubject.TryGetValue(subject, out var list))
            {
                list = new List<SubjectShape>();
                ShapesBySubject[subject] = list;
            }
            list.Add(new SubjectShape
            {
                Sheet  = m.name,
                Action = (m.action ?? "").ToLowerInvariant(),
                Width  = (float)widthSum / measured / m.frameWidth,
                Height = (float)heightSum / measured / m.frameHeight
            });
        }

        if (lowest == int.MaxValue) return;

        int spread = highest - lowest;
        float atFinalSize = spread * (m.worldHeight > 0f ? m.worldHeight : 1.35f)
                            * PixelsPerWorldUnit / m.frameHeight;

        bool shapeChanges = ShapeChanges((m.action ?? "").ToLowerInvariant());

        if (atFinalSize >= 2f && shapeChanges)
            report.Add($"    feet move {spread} px between frames ({atFinalSize:0.#} px at final " +
                       "size) — expected for this action, not flagged");
        else if (atFinalSize >= 2f)
            problems.Add($"{m.name}: the subject's feet move {spread} px between frames " +
                         $"({atFinalSize:0.#} px at final size) — it will bob. Frames should share " +
                         "a baseline; regenerate rather than importing.");
        else if (spread > 0)
            report.Add($"    baseline drift {spread} px across frames (negligible at final size)");
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
            if (slices != null) importer.spritesheet = slices;
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

            // Cycling is held for as long as you are on the vehicle, so it is a bool from Any
            // State rather than a one-shot trigger, and it returns to idle when the bool clears.
            if (states.TryGetValue("cycle", out AnimatorState cycle))
            {
                var toCycle = sm.AddAnyStateTransition(cycle);
                toCycle.hasExitTime = false;
                toCycle.duration = 0.05f;
                toCycle.canTransitionToSelf = false;
                toCycle.AddCondition(AnimatorConditionMode.If, 0f, CyclingParameter);

                var offCycle = cycle.AddTransition(idle);
                offCycle.hasExitTime = false;
                offCycle.duration = 0.05f;
                offCycle.AddCondition(AnimatorConditionMode.IfNot, 0f, CyclingParameter);
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
