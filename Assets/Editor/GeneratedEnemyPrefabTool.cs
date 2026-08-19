using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.AI;
using UnityEditor;
using GBHEngland.Combat;
using GBHEngland.World;
using GBHEngland.Data;
using GBHEngland.Vibe;

/// <summary>
/// Builds London's hostile enemy prefabs and their PlacementPresets from the generated art
/// sitting in Assets/Animations/Generated — the neek/OG/roadman/spicehead/tainted/torturedneek
/// cast, plus wiring the art onto Police_PCSO (that one prefab already exists, hand-built, and
/// is only ever updated, never created).
///
/// Run via: Tools -> Content -> Build Enemies From Generated Art
///
/// One tool, not two, and it edits in place rather than deleting and re-creating. A pure "create"
/// tool has exactly one safe run; the moment a subject's missing sheets (torturedneek today) turn
/// up, running it again would either abort or do the thing CLAUDE.md §7 forbids — delete then
/// SaveAsPrefabAsset, minting a fresh GUID and orphaning every placed instance. Re-running this
/// tool is the normal way its own job finishes.
///
/// The per-field values below were inherited from EnemyPrefabSetup.cs, the retired builder for the
/// Orc and Bot Wheel subjects — those subjects were cut and the file deleted, so each comment now
/// states its value outright rather than citing a line. Git holds the original if the provenance is
/// ever wanted. Its *save strategy* was never copied: it deleted and re-created its prefabs on every
/// run, which is exactly what CLAUDE.md §7 documents as a trap for anything already placed. Update
/// here always goes through LoadPrefabContents / SaveAsPrefabAsset / UnloadPrefabContents, the same
/// shape as ArtImportTool.AssignVehicleSprite.
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
        /// <summary>Throws a bolt from AttackRange instead of meleeing. Needs a wide AttackRange.</summary>
        public bool RangedCaster;
        public float AttackRange;
        public float AttackCooldown;
        /// <summary>
        /// Built with the EnemyAI component disabled, for an enemy that stands passive until
        /// something enables it — a talk-then-turn-hostile character. Nothing else here is
        /// affected; the prefab is otherwise a normal enemy.
        /// </summary>
        public bool StartPassive;

        public EnemySpec(string subject, string prefabPath, string displayName, string presetLabel,
            int health, int damage, string questKey,
            bool rangedCaster = false, float attackRange = 1.6f, float attackCooldown = 1.2f,
            bool startPassive = false)
        {
            Subject = subject;
            PrefabPath = prefabPath;
            DisplayName = displayName;
            PresetLabel = presetLabel;
            Health = health;
            Damage = damage;
            QuestKey = questKey;
            // Defaulted to what this tool hardcoded before these existed, so every row above that
            // omits them builds byte-identically to how it did.
            RangedCaster = rangedCaster;
            AttackRange = attackRange;
            AttackCooldown = attackCooldown;
            StartPassive = startPassive;
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
            "Tortured Neek", 45, 7, "tortured_neek"),

        // The Spark of Talent tutorial's twitchy geezer, converted from the runtime-spawned
        // character MagicTutorial.cs used to build. Health 40, Damage 8, RangedCaster with a 7 m
        // AttackRange and a 1.6 s cooldown all match what that file set (MagicTutorial.cs:361-373)
        // — his bolt is the story beat the quest turns on, so a melee geezer would break it.
        //
        // StartPassive: he must stand there harmlessly until the player talks to him and the
        // conversation closes. HostileAfterDialogue enables the EnemyAI at that moment.
        //
        // under_housed is the QuestActor.Key the KILL stage of spark_of_talent binds to. It is
        // matched against the .quest file, not stored in saves.
        new EnemySpec("underhoused", $"{PrefabFolder}/Enemy_UnderHoused.prefab", "Under Housed",
            "Under Housed", 40, 8, "under_housed",
            rangedCaster: true, attackRange: 7f, attackCooldown: 1.6f, startPassive: true),

        // Update-only: Police_PCSO.prefab already exists, hand-built by ModernBritainSetup, and is
        // never (re)created here. No preset — police are spawned by WantedManager.SpawnPlod, not
        // placed from the World Palette. DisplayName/Health/Damage are unused on the update path
        // and left blank/zero.
        //
        // ⚠️ Do NOT expect EnemyAI.IsPolice to be set on this prefab. An earlier version of this
        // comment claimed it was and had to be preserved; it is not. None of the five Police_*
        // prefabs serializes IsPolice at all, so every officer loads with the C# default, false.
        // ModernBritainSetup.cs:144 does set it, but that never reached disk. Two live consequences,
        // both pre-existing and neither caused by this tool: GameFlowController's arrest path
        // (lines 321, 381) never fires, so police-dealt death kills instead of arresting; and
        // WantedManager.DespawnPolice (line 116) filters on the same flag and therefore destroys
        // nothing. Fix is five Inspector ticks — NOT a re-run of ModernBritainSetup, which is a
        // Danger Zone tool that mints fresh GUIDs and orphans placed instances (CLAUDE.md §7).
        //
        // Note this tool's SaveAsPrefabAsset rewrites the whole YAML, so IsPolice: 0 becomes
        // explicit serialized data rather than an absent key. Behaviour is identical today, but it
        // pins the value: changing the field's default to true later would fix the other four
        // prefabs and silently not fix this one.
        new EnemySpec("police_pcso", "Assets/Prefabs/ModernBritain/Police_PCSO.prefab", null, null, 0, 0, ""),

        // Same deal as the PCSO. The remaining three tiers — ArmedResponse, OccultAgent,
        // OccultCommander — have prefabs but no art at all, so they are deliberately absent: a spec
        // with neither controller nor sprite is skipped and reported, which is just noise for a
        // subject nobody has drawn yet. Add a row each when their sheets land.
        new EnemySpec("police_bobby", "Assets/Prefabs/ModernBritain/Police_Bobby.prefab", null, null, 0, 0, ""),
    };

    [MenuItem("Tools/Content/Build Enemies From Generated Art")]
    public static void Run()
    {
        if (!AssetDatabase.IsValidFolder(AnimRoot))
        {
            EditorUtility.DisplayDialog("Build Enemies From Generated Art",
                $"No {AnimRoot} folder, so no generated art has been imported yet. Run " +
                "Tools -> Art -> Import Generated Art first.", "OK");
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
                int before = problems.Count;
                prefab = UpdatePrefab(spec, controller, resting, problems);
                // Only claim success when nothing was recorded against it. Saying "updated in
                // place" beside a problem entry reads as though both happened.
                report.Add(problems.Count == before
                    ? $"{spec.PrefabPath}: updated in place."
                    : $"{spec.PrefabPath}: updated in place, with problems (below).");
            }
            else
            {
                prefab = CreatePrefab(spec, controller, resting);
                report.Add($"{spec.PrefabPath}: created.");
            }

            // Both branches return what the save actually produced rather than re-reading the path
            // and hoping. A null here means the save failed, and passing it on would write a
            // PlacementPreset with EnemyPrefab unset — which arms and ghosts in the World Palette
            // and then places nothing, logging only PlacementBuilders' "has no EnemyPrefab". Worse,
            // EnsurePreset never overwrites an existing preset, so a re-run would report "already
            // existed" and never repair it. Refusing to write the preset is the recoverable failure.
            if (prefab == null)
            {
                problems.Add($"{spec.PrefabPath}: the prefab save returned nothing, so no preset was " +
                             "written for it. Nothing partial was left behind — fix the cause and re-run.");
                continue;
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

    /// <summary>Returns the saved prefab asset, or null if the save failed.</summary>
    private static GameObject CreatePrefab(EnemySpec spec, RuntimeAnimatorController controller, Sprite resting)
    {
        string rootName = System.IO.Path.GetFileNameWithoutExtension(spec.PrefabPath);
        var root = new GameObject(rootName);
        try
        {
            // CapsuleCollider height/radius/center: 1.35 / 0.28 / (0, 0.675, 0), inherited values.
            var col = root.AddComponent<CapsuleCollider>();
            col.height = 1.35f;
            col.radius = 0.28f;
            col.center = new Vector3(0f, 0.675f, 0f);
            // col.direction left at its Unity default (1 = Y-axis).

            // Health.MaxHealth/CurrentHealth: 45/45, and 90/90 for tainted, per the spec table.
            // DestroyOnDeath/DestroyDelay left at Health.cs defaults (true/1.2).
            Health health = root.AddComponent<Health>();
            health.MaxHealth = spec.Health;
            health.CurrentHealth = spec.Health;
            health.DisplayName = spec.DisplayName;

            // NavMeshAgent height/radius/speed/stoppingDistance: 1.35 / 0.28 / 3.8 / 1.2, inherited.
            // EnemyAI.Awake overwrites most of these at runtime (speed, angularSpeed, acceleration,
            // stoppingDistance, radius, height) — authored anyway so the editor gizmo is not
            // misleading, per the plan's corrections.
            var agent = root.AddComponent<NavMeshAgent>();
            agent.height = 1.35f;
            agent.radius = 0.28f;
            agent.speed = 3.8f;
            agent.stoppingDistance = 1.2f;

            // EnemyAI.Damage: spec table (7; 14 for tainted). SightRadius/MoveSpeed: 16 / 3.8,
            // inherited. AttackRange/AttackCooldown/RangedCaster come from the spec and default to
            // the values this tool used to hardcode (1.6 / 1.2 / false), so every melee row builds
            // exactly as before. AttackWindup/EyeHeight/TurnSpeed left at EnemyAI.cs defaults
            // (0.3/0.95/10). IsPolice left false (EnemyAI.cs:27).
            EnemyAI ai = root.AddComponent<EnemyAI>();
            ai.Damage = spec.Damage;
            ai.SightRadius = 16f;
            ai.AttackRange = spec.AttackRange;
            ai.AttackCooldown = spec.AttackCooldown;
            ai.RangedCaster = spec.RangedCaster;
            ai.MoveSpeed = 3.8f;

            // WorldActorVisual.Height/Width: EKVibe.CharacterHeight/CharacterWidth (EKVibe.cs:60-61).
            var visual = root.AddComponent<WorldActorVisual>();
            visual.ActorSprite = resting;
            visual.Height = EKVibe.CharacterHeight;
            visual.Width = EKVibe.CharacterWidth;
            // Awake() does not run on an editor-built object, so ApplyVisual() is called explicitly.
            // Builds ActorVisual/SwingRoot and its SpriteRenderer.
            visual.ApplyVisual();

            if (controller != null)
            {
                // Public method, not a hand-rolled Find + AddComponent<Animator>. This also sets
                // cullingMode = AlwaysAnimate and applyRootMotion = false.
                Animator animator = visual.AttachAnimator(controller);
                // The line the whole feature turns on (CLAUDE.md §13: "a public field nothing
                // assigns unless asked"). Without it the sheets never play.
                if (animator != null) ai.Animator = animator;
            }

            // Disabled LAST, after every field above is written — a disabled component still
            // serializes its values, and whatever enables it later gets a fully configured AI.
            // Disabling the component is the correct passive state; a SightRadius of 0 is NOT,
            // because EnemyAI drops a target beyond SightRadius * 1.4 and would acquire then
            // instantly forget the player on the same tick.
            if (spec.StartPassive) ai.enabled = false;

            if (!string.IsNullOrEmpty(spec.QuestKey))
                root.AddComponent<QuestActor>().Key = spec.QuestKey;

            // The nameplate's Level is a display fallback only, used when the actor has no
            // EnemyLevel component — which is every generated enemy, since this tool deliberately
            // does not decide anyone's level. 1 is the honest badge for an unscaled enemy.
            //
            // Only newly created prefabs are affected: the update path below never touches the
            // nameplate, so the eleven prefabs already storing a 3 keep it until someone edits them.
            var plate = root.AddComponent<EnemyNameplate>();
            plate.Level = 1;
            plate.HeightOffset = 1.70f;

            // Root layer left at 0 — there is no Enemy layer (TagManager.asset has tags: []).

            // No DeleteAsset before this — a create-branch prefab does not exist yet by definition.
            // The return value IS the saved asset; use it rather than re-reading the path, so a
            // failed save surfaces as null instead of being silently indistinguishable from success.
            return PrefabUtility.SaveAsPrefabAsset(root, spec.PrefabPath);
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

    /// <summary>Returns the saved prefab asset, or null if the save failed.</summary>
    private static GameObject UpdatePrefab(EnemySpec spec, RuntimeAnimatorController controller,
        Sprite resting, List<string> problems)
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
            //
            // In practice this branch is unreachable on a freshly added component: WorldActorVisual
            // declares `public float Height = EKVibe.CharacterHeight`, so AddComponent above yields
            // 1.35 rather than 0. It fires only for a pre-existing component someone typed 0 into.
            // Kept because that case is real, but do not read it as the tool being able to size an
            // actor to anything other than CharacterHeight — it cannot, which is what the collider
            // check below exists to make visible.
            if (visual.Height <= 0f)
            {
                visual.Height = EKVibe.CharacterHeight;
                visual.Width = EKVibe.CharacterWidth;
            }
            visual.ApplyVisual();

            // A hand-built prefab may have been sized for a placeholder primitive rather than for
            // sprite art, and this tool deliberately never resizes a collider, agent or nameplate —
            // those are tuning, and update only touches what the art derives. Police_PCSO is the
            // live example: capsule 2.025 tall, nameplate offset 2.375, both 1.5x the 1.35 sprite
            // it is about to receive. Left alone that reads as a bug in the new art — a nameplate
            // floating a metre overhead and swings connecting well above the visible body — so say
            // so plainly rather than let it be discovered in play.
            var capsule = contents.GetComponent<CapsuleCollider>();
            if (capsule != null && visual.Height > 0f
                && Mathf.Abs(capsule.height - visual.Height) > visual.Height * 0.2f)
            {
                var plate = contents.GetComponent<EnemyNameplate>();
                problems.Add(
                    $"{spec.PrefabPath}: collider is {capsule.height:0.##} units tall but the sprite " +
                    $"is {visual.Height:0.##}. Nothing was resized — that is tuning, not art. To match " +
                    $"it by hand, set CapsuleCollider height {visual.Height:0.##} and center Y " +
                    $"{visual.Height * 0.5f:0.###}, NavMeshAgent height {visual.Height:0.##}" +
                    (plate != null ? $", and EnemyNameplate HeightOffset {visual.Height + 0.35f:0.##}" : "")
                    + ".");
            }

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

            // Preserves the .meta and the GUID, so c.unity's WantedManager.PolicePrefabs reference
            // to Police_PCSO survives. Return value is the saved asset — see CreatePrefab.
            return PrefabUtility.SaveAsPrefabAsset(contents, spec.PrefabPath);
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
