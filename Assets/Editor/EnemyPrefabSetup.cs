using UnityEngine;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine.AI;
using System.Collections.Generic;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;
using ExiledAlvaston.Vibe;

/// <summary>
/// Builds reusable enemy prefabs from sliced sprite poses: Orc1/Orc2/Orc3 (single held pose per
/// state — the source pack is a directional paper-doll rig, not a walk-cycle) and Bot Wheel
/// (real multi-frame sequences). Also adds "Spawn Enemy For Testing" commands that drop a
/// temporary one next to the player for combat testing — for a permanent, authored placement
/// saved into a chunk prefab (with loot/overrides/quest key), use Place/Enemy Placement instead.
/// </summary>
public static class EnemyPrefabSetup
{
    private const string AnimFolder = "Assets/Animations/Enemies";
    private const string PrefabFolder = "Assets/Prefabs/Enemies";
    private const string SpriteRoot = "Assets/Sprites/Enemies";

    // Player-relative size multiplier — these enemies read as small next to the player at 1x.
    private const float OrcScale = 1.6f;
    private const float BotWheelScale = 1.4f;

    private class PoseClipSet
    {
        public AnimationClip Idle, Move, Attack, Hurt, Death;
    }

    [MenuItem("Tools/Exiled Alvaston/Setup (one-time)/Build Enemy Prefabs (Orc + Bot Wheel)")]
    public static void Run()
    {
        CreateFolderRecursive(AnimFolder);
        CreateFolderRecursive(PrefabFolder);

        BuildOrcs();
        BuildBotWheel();

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Enemy prefabs ready: Enemy_Orc1, Enemy_Orc2, Enemy_Orc3, Enemy_BotWheel (Assets/Prefabs/Enemies). " +
                  "Use Tools/Exiled Alvaston/Debug/Spawn Enemy For Testing/... to drop one in near the player for combat testing, " +
                  "or Tools/Exiled Alvaston/Place/Enemy Placement for a permanent, authored placement.");
    }

    // ---------- Orc ----------

    private static void BuildOrcs()
    {
        EnsureSpritesImportedInFolder($"{SpriteRoot}/Orc1");
        EnsureSpritesImportedInFolder($"{SpriteRoot}/Orc2");
        EnsureSpritesImportedInFolder($"{SpriteRoot}/Orc3");
        AssetDatabase.Refresh();

        PoseClipSet orc1 = BuildOrcClipSet("Orc1");
        PoseClipSet orc2 = BuildOrcClipSet("Orc2");
        PoseClipSet orc3 = BuildOrcClipSet("Orc3");

        AnimatorController baseController = BuildPoseController("Orc_Controller", orc1);
        AnimatorOverrideController orc2Override = BuildPoseOverride("Orc2_Override", baseController, orc2);
        AnimatorOverrideController orc3Override = BuildPoseOverride("Orc3_Override", baseController, orc3);

        BuildEnemyPrefab("Enemy_Orc1", "Orc", baseController, OrcScale);
        BuildEnemyPrefab("Enemy_Orc2", "Orc", orc2Override, OrcScale);
        BuildEnemyPrefab("Enemy_Orc3", "Orc", orc3Override, OrcScale);
    }

    private static PoseClipSet BuildOrcClipSet(string variant)
    {
        string dir = $"{SpriteRoot}/{variant}";
        return new PoseClipSet
        {
            Idle = BuildHeldPoseClip($"{dir}/{variant}_Idle.png", $"{variant}_Idle", 1.2f, true),
            Move = BuildHeldPoseClip($"{dir}/{variant}_Walk.png", $"{variant}_Move", 1.2f, true),
            Attack = BuildHeldPoseClip($"{dir}/{variant}_Attack.png", $"{variant}_Attack", 0.4f, false),
            Hurt = BuildHeldPoseClip($"{dir}/{variant}_Hurt.png", $"{variant}_Hurt", 0.3f, false),
            Death = BuildHeldPoseClip($"{dir}/{variant}_Death.png", $"{variant}_Death", 1.0f, false),
        };
    }

    /// <summary>A "clip" that just holds one sprite for a duration — for packs with no real in-between frames.</summary>
    private static AnimationClip BuildHeldPoseClip(string spritePath, string clipName, float holdDuration, bool loop)
    {
        Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);
        if (sprite == null)
            Debug.LogWarning($"EnemyPrefabSetup: missing sprite at {spritePath}");

        var clip = new AnimationClip { frameRate = 8f };
        var keyframes = new[]
        {
            new ObjectReferenceKeyframe { time = 0f, value = sprite },
            new ObjectReferenceKeyframe { time = holdDuration, value = sprite },
        };
        EditorCurveBinding binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
        AnimationUtility.SetObjectReferenceCurve(clip, binding, keyframes);

        AnimationClipSettings settings = AnimationUtility.GetAnimationClipSettings(clip);
        settings.loopTime = loop;
        AnimationUtility.SetAnimationClipSettings(clip, settings);

        return SaveClip(clip, clipName);
    }

    // ---------- Bot Wheel ----------

    private static void BuildBotWheel()
    {
        EnsureSpritesImportedInFolder($"{SpriteRoot}/BotWheel");
        AssetDatabase.Refresh();

        var set = new PoseClipSet
        {
            Idle = BuildFrameClip("BotWheel_Idle_", 1, 4f, true, "BotWheel_Idle"),
            Move = BuildFrameClip("BotWheel_Move_", 8, 12f, true, "BotWheel_Move"),
            Attack = BuildFrameClip("BotWheel_Attack_", 4, 10f, false, "BotWheel_Attack"),
            Hurt = BuildFrameClip("BotWheel_Hurt_", 2, 8f, false, "BotWheel_Hurt"),
            Death = BuildFrameClip("BotWheel_Death_", 6, 8f, false, "BotWheel_Death"),
        };

        AnimatorController controller = BuildPoseController("BotWheel_Controller", set);
        BuildEnemyPrefab("Enemy_BotWheel", "Bot Wheel", controller, BotWheelScale);
    }

    private static AnimationClip BuildFrameClip(string prefix, int frameCount, float frameRate, bool loop, string clipName)
    {
        string folder = $"{SpriteRoot}/BotWheel";
        var clip = new AnimationClip { frameRate = frameRate };
        var keyframes = new ObjectReferenceKeyframe[frameCount];
        for (int i = 0; i < frameCount; i++)
        {
            string path = $"{folder}/{prefix}{i}.png";
            Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            if (sprite == null)
                Debug.LogWarning($"EnemyPrefabSetup: missing sprite at {path}");
            keyframes[i] = new ObjectReferenceKeyframe { time = i / frameRate, value = sprite };
        }

        EditorCurveBinding binding = EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite");
        AnimationUtility.SetObjectReferenceCurve(clip, binding, keyframes);

        AnimationClipSettings settings = AnimationUtility.GetAnimationClipSettings(clip);
        settings.loopTime = loop;
        AnimationUtility.SetAnimationClipSettings(clip, settings);

        return SaveClip(clip, clipName);
    }

    private static AnimationClip SaveClip(AnimationClip clip, string clipName)
    {
        string clipPath = $"{AnimFolder}/{clipName}.anim";
        if (AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath) != null)
            AssetDatabase.DeleteAsset(clipPath);
        AssetDatabase.CreateAsset(clip, clipPath);
        return clip;
    }

    // ---------- shared: Animator Controller / Override (Idle/Move/Attack/Hurt/Death) ----------

    private static AnimatorController BuildPoseController(string name, PoseClipSet clips)
    {
        string path = $"{AnimFolder}/{name}.controller";
        if (AssetDatabase.LoadAssetAtPath<AnimatorController>(path) != null)
            AssetDatabase.DeleteAsset(path);

        var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
        controller.AddParameter("Speed", AnimatorControllerParameterType.Float);
        controller.AddParameter("MeleeAttack", AnimatorControllerParameterType.Trigger);
        controller.AddParameter("Hit", AnimatorControllerParameterType.Trigger);
        controller.AddParameter("Death", AnimatorControllerParameterType.Trigger);

        AnimatorStateMachine sm = controller.layers[0].stateMachine;

        AnimatorState idleState = sm.AddState("Idle");
        idleState.motion = clips.Idle;
        sm.defaultState = idleState;

        AnimatorState moveState = sm.AddState("Move");
        moveState.motion = clips.Move;

        AnimatorState attackState = sm.AddState("Attack");
        attackState.motion = clips.Attack;

        AnimatorState hurtState = sm.AddState("Hurt");
        hurtState.motion = clips.Hurt;

        AnimatorState deathState = sm.AddState("Death");
        deathState.motion = clips.Death;

        AnimatorStateTransition toMove = idleState.AddTransition(moveState);
        toMove.hasExitTime = false;
        toMove.duration = 0.1f;
        toMove.AddCondition(AnimatorConditionMode.Greater, 0.1f, "Speed");

        AnimatorStateTransition toIdle = moveState.AddTransition(idleState);
        toIdle.hasExitTime = false;
        toIdle.duration = 0.1f;
        toIdle.AddCondition(AnimatorConditionMode.Less, 0.1f, "Speed");

        AnimatorStateTransition toAttack = sm.AddAnyStateTransition(attackState);
        toAttack.hasExitTime = false;
        toAttack.duration = 0.05f;
        toAttack.AddCondition(AnimatorConditionMode.If, 0, "MeleeAttack");

        AnimatorStateTransition attackToIdle = attackState.AddTransition(idleState);
        attackToIdle.hasExitTime = true;
        attackToIdle.exitTime = 1f;
        attackToIdle.duration = 0.1f;
        attackToIdle.hasFixedDuration = true;

        AnimatorStateTransition toHurt = sm.AddAnyStateTransition(hurtState);
        toHurt.hasExitTime = false;
        toHurt.duration = 0.03f;
        toHurt.AddCondition(AnimatorConditionMode.If, 0, "Hit");

        AnimatorStateTransition hurtToIdle = hurtState.AddTransition(idleState);
        hurtToIdle.hasExitTime = true;
        hurtToIdle.exitTime = 1f;
        hurtToIdle.duration = 0.1f;
        hurtToIdle.hasFixedDuration = true;

        AnimatorStateTransition toDeath = sm.AddAnyStateTransition(deathState);
        toDeath.hasExitTime = false;
        toDeath.duration = 0.05f;
        toDeath.AddCondition(AnimatorConditionMode.If, 0, "Death");
        // No transition out of Death — the GameObject is destroyed shortly after (Health.DestroyDelay).

        return controller;
    }

    private static AnimatorOverrideController BuildPoseOverride(string name, AnimatorController baseController, PoseClipSet clips)
    {
        string path = $"{AnimFolder}/{name}.overrideController";
        if (AssetDatabase.LoadAssetAtPath<AnimatorOverrideController>(path) != null)
            AssetDatabase.DeleteAsset(path);

        var overrideController = new AnimatorOverrideController(baseController);
        var overrides = new List<KeyValuePair<AnimationClip, AnimationClip>>();
        overrideController.GetOverrides(overrides);
        for (int i = 0; i < overrides.Count; i++)
        {
            AnimationClip orig = overrides[i].Key;
            if (orig == null) continue;
            if (orig.name.EndsWith("Idle")) overrides[i] = new KeyValuePair<AnimationClip, AnimationClip>(orig, clips.Idle);
            else if (orig.name.EndsWith("Move")) overrides[i] = new KeyValuePair<AnimationClip, AnimationClip>(orig, clips.Move);
            else if (orig.name.EndsWith("Attack")) overrides[i] = new KeyValuePair<AnimationClip, AnimationClip>(orig, clips.Attack);
            else if (orig.name.EndsWith("Hurt")) overrides[i] = new KeyValuePair<AnimationClip, AnimationClip>(orig, clips.Hurt);
            else if (orig.name.EndsWith("Death")) overrides[i] = new KeyValuePair<AnimationClip, AnimationClip>(orig, clips.Death);
        }
        overrideController.ApplyOverrides(overrides);
        AssetDatabase.CreateAsset(overrideController, path);
        return overrideController;
    }

    private static void EnsureSpritesImportedInFolder(string folder)
    {
        string[] guids = AssetDatabase.FindAssets("t:Texture2D", new[] { folder });
        foreach (string guid in guids)
        {
            string assetPath = AssetDatabase.GUIDToAssetPath(guid);
            if (AssetImporter.GetAtPath(assetPath) is TextureImporter importer && importer.textureType != TextureImporterType.Sprite)
            {
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.SaveAndReimport();
            }
        }
    }

    private static void CreateFolderRecursive(string path)
    {
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

    // ---------- Prefab ----------

    private static void BuildEnemyPrefab(string prefabName, string displayName, RuntimeAnimatorController controller, float scale = 1f)
    {
        string path = $"{PrefabFolder}/{prefabName}.prefab";
        float height = EKVibe.CharacterHeight * scale;
        float width = EKVibe.CharacterWidth * scale;
        float radius = 0.28f * scale;

        GameObject root = new GameObject(prefabName);
        try
        {
            var col = root.AddComponent<CapsuleCollider>();
            col.height = height;
            col.radius = radius;
            col.center = new Vector3(0f, height * 0.5f, 0f);

            Health health = root.AddComponent<Health>();
            health.MaxHealth = 45;
            health.CurrentHealth = 45;
            health.DisplayName = displayName;

            var agent = root.AddComponent<NavMeshAgent>();
            agent.height = height;
            agent.radius = radius;
            agent.speed = 3.8f;
            agent.stoppingDistance = 1.2f;

            EnemyAI ai = root.AddComponent<EnemyAI>();
            ai.Damage = 7;
            ai.SightRadius = 16f;
            ai.AttackRange = 1.6f;
            ai.MoveSpeed = 3.8f;

            var visual = root.AddComponent<WorldActorVisual>();
            visual.Height = height;
            visual.Width = width;
            // ActorSprite stays unassigned — the Animator drives m_Sprite once Play starts.
            // ApplyVisual() still builds the ActorVisual/SwingRoot/SpriteRenderer hierarchy the
            // Animator below needs, same as it does at runtime in Awake().
            visual.ApplyVisual();

            Transform swingRoot = root.transform.Find("ActorVisual/SwingRoot");
            if (swingRoot != null)
            {
                var animator = swingRoot.gameObject.AddComponent<Animator>();
                animator.runtimeAnimatorController = controller;
                ai.Animator = animator;
            }
            else
            {
                Debug.LogWarning($"EnemyPrefabSetup: couldn't find ActorVisual/SwingRoot on {prefabName} — Animator not attached.");
            }

            var plate = root.AddComponent<EnemyNameplate>();
            plate.Level = 3;
            plate.HeightOffset = height + 0.35f;

            int enemyLayer = LayerMask.NameToLayer("Enemy");
            if (enemyLayer >= 0) root.layer = enemyLayer;

            if (AssetDatabase.LoadAssetAtPath<GameObject>(path) != null)
                AssetDatabase.DeleteAsset(path);
            PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    // ---------- Spawn commands ----------

    [MenuItem("Tools/Exiled Alvaston/Debug/Spawn Enemy For Testing/Orc1")]
    public static void SpawnOrc1() => SpawnEnemy("Enemy_Orc1");

    [MenuItem("Tools/Exiled Alvaston/Debug/Spawn Enemy For Testing/Orc2")]
    public static void SpawnOrc2() => SpawnEnemy("Enemy_Orc2");

    [MenuItem("Tools/Exiled Alvaston/Debug/Spawn Enemy For Testing/Orc3")]
    public static void SpawnOrc3() => SpawnEnemy("Enemy_Orc3");

    [MenuItem("Tools/Exiled Alvaston/Debug/Spawn Enemy For Testing/Bot Wheel")]
    public static void SpawnBotWheel() => SpawnEnemy("Enemy_BotWheel");

    private static void SpawnEnemy(string prefabName)
    {
        string path = $"{PrefabFolder}/{prefabName}.prefab";
        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (prefab == null)
        {
            Debug.LogWarning($"EnemyPrefabSetup: {path} not found — run Tools/Exiled Alvaston/Setup Enemy Prefabs (Orc + Bot Wheel) first.");
            return;
        }

        Vector3 spawnPos = new Vector3(3f, 0f, 2f);
        var player = Object.FindObjectOfType<CombatController>();
        if (player != null)
        {
            Vector3 facing = player.FacingDirection.sqrMagnitude > 0.01f ? player.FacingDirection : player.transform.forward;
            facing.y = 0f;
            if (facing.sqrMagnitude < 0.01f) facing = Vector3.forward;
            facing.Normalize();
            spawnPos = player.transform.position + facing * 3.5f;
        }
        spawnPos.y = 0f;

        if (NavMesh.SamplePosition(spawnPos, out NavMeshHit navHit, 10f, NavMesh.AllAreas))
            spawnPos = navHit.position;
        else
            Debug.LogWarning("EnemyPrefabSetup: no NavMesh here — enemy will still spawn, but may not path. Run Tools/World/Bake Navigation Mesh.");

        GameObject instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        Undo.RegisterCreatedObjectUndo(instance, "Spawn Enemy");
        instance.transform.position = spawnPos;

        var agent = instance.GetComponent<NavMeshAgent>();
        if (agent != null && agent.isOnNavMesh) agent.Warp(spawnPos);

        Selection.activeGameObject = instance;
        EditorGUIUtility.PingObject(instance);
        Debug.Log($"{prefabName} spawned at {spawnPos}. Enter Play Mode to fight.");
    }
}
