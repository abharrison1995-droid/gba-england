using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.Animations;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

/// <summary>
/// Builds the searchable-container prefabs and their palette presets.
///
/// Run via: Tools → Content → Build Container Prefabs
///
/// **Content, not Danger Zone.** It creates and never overwrites: a prefab, controller or preset
/// that already exists is left completely alone and reported as skipped. That is what keeps it out
/// of the Danger Zone — nothing here deletes an asset or re-mints a GUID, so a container already
/// standing in a chunk cannot be orphaned by a second run. If you need to change a prefab it has
/// already made, edit it in place; do not delete it and re-run.
///
/// Every player-facing string it writes is a **placeholder**. The names a player reads are the
/// owner's to write (CLAUDE.md §3).
/// </summary>
public static class ContainerSetup
{
    private const string PrefabFolder = "Assets/Prefabs/ModernBritain/Containers";
    private const string PresetFolder = "Assets/Data/Presets";
    private const string AnimFolder = "Assets/Animations";
    private const string ControllerPath = AnimFolder + "/Container_Controller.controller";

    /// <summary>One container to build: prefab name, preset file name, and which mode it runs in.</summary>
    private struct ContainerSpec
    {
        public string PrefabName;
        public string PresetFileName;
        public string Label;
        public string ContainerName;
        public SpriteContainer.ContainerMode Mode;
    }

    private static readonly ContainerSpec[] Specs =
    {
        new ContainerSpec
        {
            PrefabName = "Container_Fixed",
            PresetFileName = "Preset_Container_Fixed",
            Label = "PLACEHOLDER Container (Fixed)",
            ContainerName = "PLACEHOLDER Container",
            Mode = SpriteContainer.ContainerMode.Fixed,
        },
        new ContainerSpec
        {
            PrefabName = "Container_Respawning",
            PresetFileName = "Preset_Container_Respawning",
            Label = "PLACEHOLDER Container (Respawning)",
            ContainerName = "PLACEHOLDER Container",
            Mode = SpriteContainer.ContainerMode.Respawning,
        },
    };

    [MenuItem("Tools/Content/Build Container Prefabs")]
    public static void Run()
    {
        EnsureFolder(PrefabFolder);
        EnsureFolder(PresetFolder);
        EnsureFolder(AnimFolder);

        var created = new List<string>();
        var skipped = new List<string>();
        var notes = new List<string>();

        AnimatorController controller = EnsureController(created, skipped, notes);

        foreach (ContainerSpec spec in Specs)
        {
            GameObject prefab = BuildPrefab(spec, controller, created, skipped);
            EnsurePreset(spec, prefab, created, skipped);
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log(
            "Build Container Prefabs\n" +
            $"  created: {(created.Count == 0 ? "nothing" : string.Join(", ", created))}\n" +
            $"  skipped (already existed, untouched): {(skipped.Count == 0 ? "nothing" : string.Join(", ", skipped))}\n" +
            (notes.Count == 0 ? "" : "  " + string.Join("\n  ", notes) + "\n") +
            "  Assign each prefab a Sprite and a LootBand in the Inspector — both are left empty " +
            "on purpose, because contents and art are authored, not generated.");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  ANIMATOR CONTROLLER
    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// One shared controller with an <c>Open</c> state and a <c>Close</c> state, which are the two
    /// names <see cref="SpriteContainer"/> calls <c>Animator.Play</c> with.
    ///
    /// Close reuses Open's clip at <c>speed = -1</c> rather than needing a second sheet: a lid
    /// shutting is a lid opening backwards, and asking for both would double the art for nothing.
    ///
    /// Close is the default state, because a container the player has not touched is shut.
    ///
    /// <c>writeDefaults</c> is left at whatever Unity gives a new state, matching the art importer,
    /// which never sets it either — one convention, not two.
    ///
    /// ⚠ Until a container animation clip exists there is **no motion on either state**, so both
    /// Plays are no-ops. That is not a defect: the loot menu still opens. Assign the clip to the
    /// Open state (and this tool will not do it for you on a second run — the controller already
    /// exists, so it is skipped).
    /// </summary>
    private static AnimatorController EnsureController(List<string> created, List<string> skipped,
        List<string> notes)
    {
        var existing = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
        if (existing != null)
        {
            skipped.Add("Container_Controller");
            return existing;
        }

        AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
        AnimatorStateMachine sm = controller.layers[0].stateMachine;

        AnimatorState open = sm.AddState("Open");
        AnimatorState close = sm.AddState("Close");
        close.speed = -1f;

        sm.defaultState = close;

        created.Add("Container_Controller");
        notes.Add("Container_Controller has no clip on Open or Close yet, so both Animator.Play " +
                  "calls are no-ops until one is assigned to the Open state.");
        return controller;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  PREFABS
    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// Saves one container prefab, or returns the existing one untouched.
    ///
    /// No Sprite is assigned. There is no container art yet, and guessing one would quietly bind a
    /// prefab to whatever happened to be lying around.
    /// </summary>
    private static GameObject BuildPrefab(ContainerSpec spec, AnimatorController controller,
        List<string> created, List<string> skipped)
    {
        string path = $"{PrefabFolder}/{spec.PrefabName}.prefab";

        var existing = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (existing != null)
        {
            skipped.Add(spec.PrefabName);
            return existing;
        }

        var root = new GameObject(spec.PrefabName);
        try
        {
            // SpriteRenderer first: SpriteContainer requires it, and adding the two in the other
            // order makes Unity add a second one implicitly.
            root.AddComponent<SpriteRenderer>();
            root.AddComponent<SpriteBillboard>();

            var animator = root.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;
            animator.applyRootMotion = false;

            var interactable = root.AddComponent<Interactable>();
            interactable.Prompt = $"Open {spec.ContainerName}";
            interactable.InteractRange = 2.75f;
            // Reusable: a half-emptied container has to be openable again. SpriteContainer
            // disables the Interactable itself once everything has been taken.
            interactable.Reusable = true;

            var container = root.AddComponent<SpriteContainer>();
            container.ContainerName = spec.ContainerName;
            container.Mode = spec.Mode;
            container.Animator = animator;

            // OnInteract is deliberately NOT wired here. SpriteContainer subscribes itself in
            // Awake, and UnityEvent.AddListener would not survive the save anyway; writing a
            // persistent call through UnityEventTools would give it two listeners.

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, path);
            created.Add(spec.PrefabName);
            return saved;
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  PRESETS
    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// A Prop-category preset pointing at the prefab. Category is only a palette heading for a
    /// preset with a Prefab assigned — PlacementBuilders.Build checks Prefab before the category
    /// switch and routes straight to BuildFromPrefab, so the prefab link survives the stamp.
    /// </summary>
    private static void EnsurePreset(ContainerSpec spec, GameObject prefab,
        List<string> created, List<string> skipped)
    {
        string path = $"{PresetFolder}/{spec.PresetFileName}.asset";
        if (AssetDatabase.LoadAssetAtPath<PlacementPreset>(path) != null)
        {
            skipped.Add(spec.PresetFileName);
            return;
        }

        var preset = ScriptableObject.CreateInstance<PlacementPreset>();
        preset.Label = spec.Label;
        preset.Category = PlacementPreset.PlacementCategory.Prop;
        preset.Prefab = prefab;

        AssetDatabase.CreateAsset(preset, path);
        created.Add(spec.PresetFileName);
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  HELPERS
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void EnsureFolder(string assetFolder)
    {
        if (AssetDatabase.IsValidFolder(assetFolder)) return;

        string[] parts = assetFolder.Split('/');
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
