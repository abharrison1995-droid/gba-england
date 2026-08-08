using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;
using ExiledAlvaston.Vibe;

/// <summary>
/// The "what to build" half of content placement, lifted out of the five Place/… windows so it can
/// be driven by a <see cref="PlacementPreset"/> and called from the World Palette (or anywhere
/// else) rather than only from a window's own button.
///
/// Every builder takes a position and a parent and returns the created root, already
/// Undo-registered. Deciding *where* — scene pivot, raycast hit, prefab stage root — belongs to
/// the caller, so the same recipe works from a button and from a click in the Scene view.
///
/// Vehicles are deliberately absent: they are authored onto MapChunkData rather than into a scene,
/// so they have no GameObject to build. See WorldPaletteWindow.
/// </summary>
public static class PlacementBuilders
{
    /// <summary>Builds whatever the preset describes. Returns null if it cannot.</summary>
    public static GameObject Build(PlacementPreset preset, Vector3 position, Transform parent)
    {
        if (preset == null) return null;

        // A prefab wins over every recipe field — that is what "if Prefab is set" means, and it
        // keeps a preset that points at real authored content from being half-overwritten by
        // defaults left in the fields below it.
        if (preset.Prefab != null)
            return BuildFromPrefab(preset, position, parent);

        switch (preset.Category)
        {
            case PlacementPreset.PlacementCategory.NPC:        return BuildNPC(preset, position, parent);
            case PlacementPreset.PlacementCategory.Enemy:      return BuildEnemy(preset, position, parent);
            case PlacementPreset.PlacementCategory.Chest:      return BuildChest(preset, position, parent);
            case PlacementPreset.PlacementCategory.Portal:     return BuildPortal(preset, position, parent);
            case PlacementPreset.PlacementCategory.SpawnPoint: return BuildSpawnPoint(preset, position, parent);
            default:
                Debug.LogWarning($"PlacementBuilders: preset '{preset.Label}' is a " +
                                 $"{preset.Category} with no Prefab assigned, so there is nothing to build.");
                return null;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  BUILDERS
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static GameObject BuildFromPrefab(PlacementPreset preset, Vector3 position, Transform parent)
    {
        // InstantiatePrefab rather than Object.Instantiate: it keeps the prefab link, so the
        // placement still tracks edits to the prefab instead of becoming a detached copy.
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(preset.Prefab);
        Place(instance, position, parent, $"Place {preset.Label}");

        ApplyEnemyOverrides(preset, instance);
        ApplyQuestKey(preset, instance);
        return instance;
    }

    /// <summary>
    /// The NPC recipe itself lives in <see cref="NpcFactory"/>, so the running game builds exactly
    /// the same character from exactly the same preset. Everything left here is the editor's own
    /// concern and would not compile — or would not be wanted — at runtime.
    /// </summary>
    private static GameObject BuildNPC(PlacementPreset preset, Vector3 position, Transform parent)
    {
        GameObject go = NpcFactory.Build(preset, position, parent);
        if (go == null) return null;

        // Registered after the fact rather than at creation: undoing the root takes the whole
        // hierarchy the factory built underneath it.
        Undo.RegisterCreatedObjectUndo(go, $"Place {preset.Label}");

        // Something to see and click on while authoring. Animators do not evaluate in edit mode,
        // so a character placed before their art exists would otherwise be an invisible object
        // sitting in the middle of the prefab stage you are placing into. Editor-only on purpose:
        // a capsule loose in the running game is worse than a hole where a character should be.
        if (preset.NpcSprite == null)
            BuildPlaceholderBody(go.transform);

        return go;
    }

    private static GameObject BuildEnemy(PlacementPreset preset, Vector3 position, Transform parent)
    {
        if (preset.EnemyPrefab == null)
        {
            Debug.LogWarning($"PlacementBuilders: enemy preset '{preset.Label}' has no EnemyPrefab.");
            return null;
        }

        var instance = (GameObject)PrefabUtility.InstantiatePrefab(preset.EnemyPrefab);
        Place(instance, position, parent, $"Place {preset.Label}");

        ApplyEnemyOverrides(preset, instance);
        ApplyQuestKey(preset, instance);
        return instance;
    }

    private static void ApplyEnemyOverrides(PlacementPreset preset, GameObject instance)
    {
        if (instance == null) return;

        if (preset.OverrideHealth)
        {
            Health health = instance.GetComponent<Health>();
            if (health != null)
            {
                health.MaxHealth = preset.Health;
                health.CurrentHealth = preset.Health;
            }
        }

        if (preset.OverrideDamage)
        {
            EnemyAI ai = instance.GetComponent<EnemyAI>();
            if (ai != null) ai.Damage = preset.Damage;
        }

        ApplyEnemyLevel(preset, instance);

        List<LootDrop> valid = ValidLoot(preset.Loot);
        if (valid.Count > 0)
        {
            var loot = instance.GetComponent<LootOnDeath>();
            if (loot == null) loot = instance.AddComponent<LootOnDeath>();
            loot.Loot = valid.ToArray();
        }
    }

    /// <summary>
    /// Attaches an <see cref="EnemyLevel"/> when the preset asks for one.
    ///
    /// A level below 1 attaches nothing at all, which is what every preset authored before the
    /// field existed reads: level 1 and "unlevelled" are the same thing behaviourally, and a
    /// level-1 component would still change the nameplate badge and the kill-XP source.
    ///
    /// ⚠ Ordering with OverrideHealth/OverrideDamage: the override runs here, in the editor, and
    /// bakes the level-1 baseline into the placed instance. EnemyLevel.ApplyTo runs at runtime,
    /// from Health.Awake, and multiplies whatever the instance carries. So an override of 100 with
    /// a level of 5 is 240 HP in play while the Inspector still reads 100. That is the only order
    /// that composes — scaling first and overriding second would make the override silently cancel
    /// the level.
    /// </summary>
    private static void ApplyEnemyLevel(PlacementPreset preset, GameObject instance)
    {
        int level = preset.EnemyLevel;
        if (level < 1) return;

        // ApplyEnemyOverrides is called for every category from BuildFromPrefab, so a chest or NPC
        // preset with a stray level would otherwise get an EnemyLevel — whose [RequireComponent]
        // would silently add a Health to a chest, making it killable. Scaling Damage is meaningless
        // without an EnemyAI anyway, so require one and say so rather than failing quietly.
        if (instance.GetComponent<EnemyAI>() == null)
        {
            Debug.LogWarning($"PlacementBuilders: preset '{preset.Label}' sets Enemy Level {level} " +
                             $"but '{instance.name}' has no EnemyAI, so no EnemyLevel was attached.");
            return;
        }

        // Never a bare AddComponent: Unity permits duplicate components, and two EnemyLevels would
        // both run ApplyTo and compound the scale with nothing logged (_applied is per component).
        var enemyLevel = instance.GetComponent<EnemyLevel>();
        if (enemyLevel == null) enemyLevel = instance.AddComponent<EnemyLevel>();
        enemyLevel.Level = level;

        // BaseXP is deliberately left alone — AddComponent runs field initialisers, so it is
        // already EKVibe.KillXPBase.
    }

    private static GameObject BuildChest(PlacementPreset preset, Vector3 position, Transform parent)
    {
        string chestName = string.IsNullOrEmpty(preset.ChestName) ? "Chest" : preset.ChestName;

        var go = new GameObject($"Chest_{chestName}");
        Place(go, position, parent, $"Place {preset.Label}");

        var chest = go.AddComponent<LootChest>();
        chest.ChestName = chestName;
        chest.Loot = ValidLoot(preset.ChestLoot).ToArray();

        if (preset.ChestVisualPrefab != null)
        {
            var visual = (GameObject)PrefabUtility.InstantiatePrefab(preset.ChestVisualPrefab);
            visual.transform.SetParent(go.transform, false);
            visual.transform.localPosition = Vector3.zero;
            visual.transform.localRotation = Quaternion.identity;
            chest.ChestAnimation = visual.GetComponentInChildren<Animation>();
        }
        else
        {
            BuildFallbackChestVisual(go.transform, chest);
        }

        var interactable = go.AddComponent<Interactable>();
        interactable.Prompt = $"Open {chestName}";
        interactable.Reusable = true;
        interactable.InteractRange = 2.75f;

        ApplyQuestKey(preset, go);
        return go;
    }

    private static GameObject BuildPortal(PlacementPreset preset, Vector3 position, Transform parent)
    {
        if (preset.TargetChunk == null)
        {
            Debug.LogWarning($"PlacementBuilders: portal preset '{preset.Label}' has no TargetChunk.");
            return null;
        }

        var go = new GameObject($"Portal_{preset.TargetChunk.ChunkName}");
        Place(go, position, parent, $"Place {preset.Label}");

        var portal = go.AddComponent<DungeonPortal>();
        portal.TargetChunk = preset.TargetChunk;
        portal.SpawnPosition = preset.PortalSpawnPosition;
        portal.Prompt = preset.PortalPrompt;
        portal.RequireTutorialComplete = preset.RequireTutorialComplete;

        // DungeonPortal.Awake adds this at runtime; adding it now lets Prompt and InteractRange be
        // tuned in the Inspector.
        var interactable = go.AddComponent<Interactable>();
        interactable.Prompt = preset.PortalPrompt;
        interactable.InteractRange = 3f;

        if (preset.AddDoorVisual)
        {
            GameObject visual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            visual.name = "DoorVisual";
            Object.DestroyImmediate(visual.GetComponent<Collider>());
            visual.transform.SetParent(go.transform, false);
            visual.transform.localPosition = new Vector3(0f, 1.2f, 0f);
            visual.transform.localScale = new Vector3(0.5f, 2.6f, 3.2f);
            visual.GetComponent<Renderer>().sharedMaterial =
                EditorMaterialLibrary.GetOrCreate("PortalDoor", preset.DoorVisualColor);
        }

        ApplyQuestKey(preset, go);
        return go;
    }

    private static GameObject BuildSpawnPoint(PlacementPreset preset, Vector3 position, Transform parent)
    {
        string id = preset.SpawnPointId ?? "";
        var go = new GameObject(string.IsNullOrEmpty(id) ? "PlayerSpawn" : $"PlayerSpawn_{id}");
        Place(go, position, parent, $"Place {preset.Label}");

        go.AddComponent<PlayerSpawnPoint>().Id = id;
        return go;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  SHARED
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void Place(GameObject go, Vector3 position, Transform parent, string undoLabel)
    {
        Undo.RegisterCreatedObjectUndo(go, undoLabel);
        // worldPositionStays: true, then set the world position — matches what every old Place
        // window did, so a placement into a chunk prefab lands where it did before.
        if (parent != null) go.transform.SetParent(parent, true);
        go.transform.position = position;
    }

    private static void ApplyQuestKey(PlacementPreset preset, GameObject go)
    {
        if (go == null || string.IsNullOrEmpty(preset.QuestKey)) return;

        var actor = go.GetComponent<QuestActor>();
        if (actor == null) actor = go.AddComponent<QuestActor>();
        actor.Key = preset.QuestKey;
    }

    private static List<LootDrop> ValidLoot(List<LootDrop> source)
    {
        var valid = new List<LootDrop>();
        if (source == null) return valid;

        foreach (LootDrop d in source)
            if (d != null && d.Item != null && d.Quantity > 0) valid.Add(d);

        return valid;
    }

    private static void BuildPlaceholderBody(Transform parent)
    {
        GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        body.name = "PlaceholderBody";
        Object.DestroyImmediate(body.GetComponent<Collider>());
        body.transform.SetParent(parent, false);

        float h = EKVibe.CharacterHeight;
        body.transform.localPosition = new Vector3(0f, h * 0.5f, 0f);
        body.transform.localScale = new Vector3(0.5f, h * 0.5f, 0.5f);
        body.GetComponent<Renderer>().sharedMaterial =
            EditorMaterialLibrary.GetOrCreate("NPCPlaceholder", new Color(0.3f, 0.4f, 0.55f));
    }

    /// <summary>Plain box + lid, used only when a chest preset has no visual prefab.</summary>
    private static void BuildFallbackChestVisual(Transform parent, LootChest chest)
    {
        Material bodyMat = EditorMaterialLibrary.GetOrCreate("ChestPlaceholder", new Color(0.55f, 0.38f, 0.15f));

        GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
        body.name = "ChestBody";
        Object.DestroyImmediate(body.GetComponent<Collider>());
        body.transform.SetParent(parent, false);
        body.transform.localPosition = new Vector3(0f, 0.2f, 0f);
        body.transform.localScale = new Vector3(1f, 0.4f, 0.7f);
        body.GetComponent<Renderer>().sharedMaterial = bodyMat;

        var hinge = new GameObject("LidHinge");
        hinge.transform.SetParent(parent, false);
        hinge.transform.localPosition = new Vector3(0f, 0.4f, -0.35f);

        GameObject lid = GameObject.CreatePrimitive(PrimitiveType.Cube);
        lid.name = "ChestLid";
        Object.DestroyImmediate(lid.GetComponent<Collider>());
        lid.transform.SetParent(hinge.transform, false);
        lid.transform.localPosition = new Vector3(0f, 0.075f, 0.35f);
        lid.transform.localScale = new Vector3(1f, 0.15f, 0.7f);
        lid.GetComponent<Renderer>().sharedMaterial = bodyMat;

        chest.Lid = hinge.transform;
    }
}
