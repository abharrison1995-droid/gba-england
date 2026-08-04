using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.AI;
using UnityEditor;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;
using ExiledAlvaston.Data;
using ExiledAlvaston.Vibe;

/// <summary>
/// Builds London's hostile enemy prefabs and their PlacementPresets from the generated art
/// sitting in Assets/Animations/Generated — the neek/OG/roadman/spicehead/tainted/torturedneek
/// cast, plus wiring the art onto Police_PCSO (that one prefab already exists, hand-built, and
/// is only ever updated, never created).
///
/// Run via: Tools -> GBA -> Content -> Build Enemies From Generated Art
///
/// One tool, not two, and it edits in place rather than deleting and re-creating. A pure "create"
/// tool has exactly one safe run; the moment a subject's missing sheets (torturedneek today) turn
/// up, running it again would either abort or do the thing CLAUDE.md §7 forbids — delete then
/// SaveAsPrefabAsset, minting a fresh GUID and orphaning every placed instance. Re-running this
/// tool is the normal way its own job finishes.
///
/// EnemyPrefabSetup.cs is the source of *values* here (see the per-field comments below, each
/// citing its line) but never of *save strategy* — that file deletes and re-creates its prefabs
/// on every run, which is exactly what CLAUDE.md §7 documents as a trap for anything already
/// placed. Update here always goes through LoadPrefabContents / SaveAsPrefabAsset /
/// UnloadPrefabContents, the same shape as ArtImportTool.AssignVehicleSprite.
/// </summary>
public static class GeneratedEnemyPrefabTool
{
    private const string PrefabFolder = "Assets/Prefabs/Enemies";
    private const string PresetFolder = "Assets/Data/Presets";
    private const string AnimRoot = "Assets/Animations/Generated";

    private struct EnemySpec
    {
        public string Subject;
        public string PrefabPath;
        public string DisplayName;
        /// <summary>Null means "no preset" — police are spawned by WantedManager, not placed from the palette.</summary>
        public string PresetLabel;
        public int Health;
        public int Damage;
        public string QuestKey;

        public EnemySpec(string subject, string prefabPath, string displayName, string presetLabel,
            int health, int damage, string questKey)
        {
            Subject = subject;
            PrefabPath = prefabPath;
            DisplayName = displayName;
            PresetLabel = presetLabel;
            Health = health;
            Damage = damage;
            QuestKey = questKey;
        }
    }

    private static readonly EnemySpec[] Enemies =
    {
        new EnemySpec("neek", $"{PrefabFolder}/Enemy_Neek.prefab", "Neek", "Neek", 45, 7, ""),
        new EnemySpec("og", $"{PrefabFolder}/Enemy_OG.prefab", "OG", "OG", 45, 7, ""),
        new EnemySpec("roadman", $"{PrefabFolder}/Enemy_Roadman.prefab", "Roadman", "Roadman", 45, 7, ""),
        new EnemySpec("spicehead", $"{PrefabFolder}/Enemy_Spicehead.prefab", "Spicehead", "Spicehead", 45, 7, ""),

        // Doubled numbers are the owner's starting values for a tougher enemy, not a balance
        // decision — retunable in the Inspector like every other Health/EnemyAI field here.
        new EnemySpec("tainted", $"{PrefabFolder}/Enemy_Tainted.prefab", "Tainted", "Tainted", 90, 14, ""),

        // torturedneek has only an idle sheet today (no walk/attack/hurt/death) — see Run()'s
        // "one null, still build" handling. QuestKey is a placeholder for a questline that has not
        // been written yet (CLAUDE.md §14's open question): planned as the Mosley quest target,
        // but nothing currently grants or completes a quest keyed on it.
        new EnemySpec("torturedneek", $"{PrefabFolder}/Enemy_TorturedNeek.prefab", "Tortured Neek",
            "Tortured Neek", 45, 7, "torturedneek"),

        // Update-only: Police_PCSO.prefab already exists, hand-built by ModernBritainSetup, and is
        // never (re)created here. No preset — police are spawned by WantedManager.SpawnPlod, not
        // placed from the World Palette. DisplayName/Health/Damage are unused on the update path
        // and left blank/zero. Its EnemyAI.IsPolice must not be disturbed: that flag is what routes
        // player death through GameFlowController.ArrestRoutine instead of killing them (CLAUDE.md §8).
        new EnemySpec("police_pcso", "Assets/Prefabs/ModernBritain/Police_PCSO.prefab", null, null, 0, 0, ""),
    };

    [MenuItem("Tools/GBA/Content/Build Enemies From Generated Art")]
    public static void Run()
    {
        if (!AssetDatabase.IsValidFolder(AnimRoot))
        {
            EditorUtility.DisplayDialog("Build Enemies From Generated Art",
                $"No {AnimRoot} folder, so no generated art has been imported yet. Run " +
                "Tools -> GBA -> Art -> Import Generated Art first.", "OK");
            return;
        }

        var creates = new List<string>();
        var updates = new List<string>();
        var noArt = new List<string>();

        // Classify before asking, so the confirmation dialog names exactly what will happen.
        foreach (EnemySpec spec in Enemies)
        {
            RuntimeAnimatorController controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(
                $"{AnimRoot}/{spec.Subject}_Controller.controller");
            Sprite resting = ArtImportTool.FindIdleFrameZero(spec.Subject);

            if (controller == null && resting == null)
            {
                noArt.Add(spec.DisplayName ?? spec.Subject);
                continue;
            }

            bool exists = AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath) != null;
            (exists ? updates : creates).Add(spec.DisplayName ?? spec.Subject);
        }

        if (creates.Count == 0 && updates.Count == 0)
        {
            EditorUtility.DisplayDialog("Build Enemies From Generated Art",
                "No generated art matches any subject in the enemy spec table. Nothing to do.", "OK");
            return;
        }

        var dialogBody = new StringBuilder();
        if (creates.Count > 0)
            dialogBody.AppendLine($"Create ({creates.Count}): {string.Join(", ", creates)}");
        if (updates.Count > 0)
            dialogBody.AppendLine($"Update in place, GUID preserved, instances keep their link ({updates.Count}): " +
                                   string.Join(", ", updates));
        if (noArt.Count > 0)
            dialogBody.AppendLine($"No art yet, skipped: {string.Join(", ", noArt)}");

        bool proceed = EditorUtility.DisplayDialog("Build Enemies From Generated Art", dialogBody.ToString(),
            "Build", "Cancel");
        if (!proceed) return;

        EnsureFolder(PrefabFolder);
        EnsureFolder(PresetFolder);

        var report = new List<string>();
        var problems = new List<string>();
        var presetCreated = new List<string>();
        var presetSkipped = new List<string>();

        foreach (EnemySpec spec in Enemies)
        {
            RuntimeAnimatorController controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(
                $"{AnimRoot}/{spec.Subject}_Controller.controller");
            Sprite resting = ArtImportTool.FindIdleFrameZero(spec.Subject);

            if (controller == null && resting == null)
            {
                report.Add($"{spec.Subject}: no controller and no idle sprite found — skipped.");
                continue;
            }
            if (controller == null)
                report.Add($"{spec.Subject}: no controller ({AnimRoot}/{spec.Subject}_Controller.controller) — will be static.");
            if (resting == null)
                report.Add($"{spec.Subject}: no idle sprite found — will be invisible in edit mode.");

            bool exists = AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath) != null;
            GameObject prefab;
            if (exists)
            {
                UpdatePrefab(spec, controller, resting, report, problems);
                prefab = AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath);
                report.Add($"{spec.PrefabPath}: updated in place.");
            }
            else
            {
                CreatePrefab(spec, controller, resting);
                prefab = AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath);
                report.Add($"{spec.PrefabPath}: created.");
            }

            EnsurePreset(spec, prefab, resting, presetCreated, presetSkipped);
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        var log = new StringBuilder();
        log.AppendLine("Build Enemies From Generated Art");
        log.AppendLine("─────────────────────────────────");
        foreach (string r in report) log.AppendLine("  " + r);
        if (presetCreated.Count > 0)
        {
            log.AppendLine($"  presets created: {presetCreated.Count}");
            foreach (string p in presetCreated) log.AppendLine("    + " + p);
        }
        if (presetSkipped.Count > 0)
        {
            log.AppendLine($"  presets already existed, left alone: {presetSkipped.Count}");
            foreach (string p in presetSkipped) log.AppendLine("    = " + p);
        }
        if (problems.Count > 0)
        {
            log.AppendLine("  problems:");
            foreach (string p in problems) log.AppendLine("    ! " + p);
        }
        Debug.Log(log.ToString());

        EditorUtility.DisplayDialog("Build Enemies From Generated Art",
            $"{creates.Count} created, {updates.Count} updated, {presetCreated.Count} preset(s) created, " +
            $"{presetSkipped.Count} preset(s) already existed.\n\nDetail in the Console.", "OK");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  CREATE
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void CreatePrefab(EnemySpec spec, RuntimeAnimatorController controller, Sprite resting)
    {
        string rootName = System.IO.Path.GetFileNameWithoutExtension(spec.PrefabPath);
        var root = new GameObject(rootName);
        try
        {
            // CapsuleCollider height/radius/center: EnemyPrefabSetup.cs:313,307,315.
            var col = root.AddComponent<CapsuleCollider>();
            col.height = 1.35f;
            col.radius = 0.28f;
            col.center = new Vector3(0f, 0.675f, 0f);
            // col.direction left at its Unity default (1 = Y-axis).

            // Health.MaxHealth/CurrentHealth: EnemyPrefabSetup.cs:318-319 (45/45; 90/90 for tainted
            // per the spec table). DestroyOnDeath/DestroyDelay left at Health.cs defaults (true/1.2).
            Health health = root.AddComponent<Health>();
            health.MaxHealth = spec.Health;
            health.CurrentHealth = spec.Health;
            health.DisplayName = spec.DisplayName;

            // NavMeshAgent height/radius/speed/stoppingDistance: EnemyPrefabSetup.cs:323-326.
            // EnemyAI.Awake overwrites most of these at runtime (speed, angularSpeed, acceleration,
            // stoppingDistance, radius, height) — authored anyway so the editor gizmo is not
            // misleading, per the plan's corrections.
            var agent = root.AddComponent<NavMeshAgent>();
            agent.height = 1.35f;
            agent.radius = 0.28f;
            agent.speed = 3.8f;
            agent.stoppingDistance = 1.2f;

            // EnemyAI.Damage: spec table (7; 14 for tainted). SightRadius/AttackRange/MoveSpeed:
            // EnemyPrefabSetup.cs:330-332. AttackCooldown/AttackWindup/EyeHeight/TurnSpeed left at
            // EnemyAI.cs defaults (1.2/0.3/0.95/10). RangedCaster/IsPolice left false (EnemyAI.cs:22,27).
            EnemyAI ai = root.AddComponent<EnemyAI>();
            ai.Damage = spec.Damage;
            ai.SightRadius = 16f;
            ai.AttackRange = 1.6f;
            ai.MoveSpeed = 3.8f;

            // WorldActorVisual.Height/Width: EKVibe.CharacterHeight/CharacterWidth (EKVibe.cs:60-61).
            var visual = root.AddComponent<WorldActorVisual>();
            visual.ActorSprite = resting;
            visual.Height = EKVibe.CharacterHeight;
            visual.Width = EKVibe.CharacterWidth;
            // Awake() does not run on an editor-built object, so ApplyVisual() is called explicitly
            // (EnemyPrefabSetup.cs:340 does the same and says why). Builds ActorVisual/SwingRoot and
            // its SpriteRenderer.
            visual.ApplyVisual();

            if (controller != null)
            {
                // Public method, not a hand-rolled Find + AddComponent<Animator> — EnemyPrefabSetup.cs
                // hand-rolls it and predates AttachAnimator; that shape must not be copied. This also
                // sets cullingMode = AlwaysAnimate and applyRootMotion = false.
                Animator animator = visual.AttachAnimator(controller);
                // The line the whole feature turns on (CLAUDE.md §13: "a public field nothing
                // assigns unless asked"). Without it the sheets never play.
                if (animator != null) ai.Animator = animator;
            }

            if (!string.IsNullOrEmpty(spec.QuestKey))
                root.AddComponent<QuestActor>().Key = spec.QuestKey;

            // EnemyNameplate.Level/HeightOffset: EnemyPrefabSetup.cs:355-356.
            var plate = root.AddComponent<EnemyNameplate>();
            plate.Level = 3;
            plate.HeightOffset = 1.70f;

            // Root layer left at 0 — there is no Enemy layer (TagManager.asset has tags: []).

            // No DeleteAsset before this — a create-branch prefab does not exist yet by definition.
            PrefabUtility.SaveAsPrefabAsset(root, spec.PrefabPath);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  UPDATE — only the three art-derived things. Never touches Health, EnemyAI tuning, the
    //  collider, the nameplate or the quest key: those are tunable and may already have been
    //  retuned by hand (this is exactly how Police_PCSO's existing IsPolice/Health survive).
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void UpdatePrefab(EnemySpec spec, RuntimeAnimatorController controller, Sprite resting,
        List<string> report, List<string> problems)
    {
        GameObject contents = PrefabUtility.LoadPrefabContents(spec.PrefabPath);
        try
        {
            var visual = contents.GetComponent<WorldActorVisual>();
            if (visual == null) visual = contents.AddComponent<WorldActorVisual>();

            if (resting != null) visual.ActorSprite = resting;

            // Height is tunable, so a hand-set value must survive — same rule as
            // ArtImportTool.WirePresetsForSubject (line 548): only fill in the derived default when
            // nothing has been set yet.
            if (visual.Height <= 0f)
            {
                visual.Height = EKVibe.CharacterHeight;
                visual.Width = EKVibe.CharacterWidth;
            }
            visual.ApplyVisual();

            if (controller != null)
            {
                Animator animator = visual.AttachAnimator(controller);
                var ai = contents.GetComponent<EnemyAI>();
                if (ai != null && animator != null)
                    ai.Animator = animator;
                else if (ai == null)
                    problems.Add($"{spec.PrefabPath}: has no EnemyAI component — a prefab in " +
                                 "Prefabs/Enemies (or ModernBritain) without one is unexpected, " +
                                 "so the Animator was attached but not wired to anything.");
            }

            // PlaceholderBody is only ever created (PlacementBuilders.BuildPlaceholderBody,
            // NPCPlacementTool, ModernBritainSetup), never read, and WorldActorVisual.HidePrimitiveMesh
            // only checks the root — so it must be deleted explicitly or it lingers forever.
            Transform placeholder = contents.transform.Find("PlaceholderBody");
            if (placeholder != null)
                Object.DestroyImmediate(placeholder.gameObject);

            PrefabUtility.SaveAsPrefabAsset(contents, spec.PrefabPath);
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(contents);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  PRESET
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void EnsurePreset(EnemySpec spec, GameObject prefab, Sprite resting,
        List<string> created, List<string> skipped)
    {
        if (spec.PresetLabel == null) return;

        string path = $"{PresetFolder}/Preset_{Sanitise(spec.PresetLabel)}.asset";
        if (AssetDatabase.LoadAssetAtPath<PlacementPreset>(path) != null)
        {
            skipped.Add(spec.PresetLabel);
            return;
        }

        var preset = ScriptableObject.CreateInstance<PlacementPreset>();
        preset.Label = spec.PresetLabel;
        preset.Category = PlacementPreset.PlacementCategory.Enemy;
        preset.EnemyPrefab = prefab;
        preset.Icon = resting;
        // OverrideHealth/OverrideDamage left false, Loot empty, QuestKey blank — StarterPresetGenerator.Create (line 249) verbatim in behaviour.

        AssetDatabase.CreateAsset(preset, path);
        created.Add(spec.PresetLabel);
    }

    // Same semantics as StarterPresetGenerator.Sanitise, so a later addition to that generator can
    // find these presets by the same path convention (CLAUDE.md §13's Preset_FUSportsClerk note).
    private static string Sanitise(string label) =>
        label.Replace(" ", "").Replace("/", "").Replace("\\", "");

    private static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;

        string[] parts = path.Split('/');
        string current = parts[0];
        for (int i = 1; i < parts.Length; i++)
        {
            string next = current + "/" + parts[i];
            if (!AssetDatabase.IsValidFolder(next))
                AssetDatabase.CreateFolder(current, parts[i]);
            current = next;
        }
    }
}
