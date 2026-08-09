using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.Data;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;

/// <summary>
/// Drops an enemy prefab (e.g. Assets/Prefabs/Enemies/Enemy_Roadman) into the open scene or
/// prefab, with optional stat overrides, a death loot list, and a quest key — an authored,
/// saved-in-prefab placement rather than a Play-mode debug spawn. The chunk still needs its
/// NavMesh baked (Tools > GBH > World > Bake Navigation Mesh) for the enemy to path.
/// </summary>
public class EnemyPlacementTool : EditorWindow
{
    private GameObject _enemyPrefab;

    private bool _overrideHealth;
    private int _healthOverride = 45;
    private bool _overrideDamage;
    private int _damageOverride = 7;

    /// <summary>
    /// Parity with the World Palette's own per-stamp level. Without it the two placement paths
    /// disagree, and the disagreement is the kind found six months later by someone wondering why
    /// their enemy is level 1.
    /// </summary>
    private int _level;

    private readonly List<LootDrop> _loot = new List<LootDrop>();
    private string _questKey = "";

    [MenuItem("Tools/GBH/Place/Enemy Placement")]
    public static void Open()
    {
        GetWindow<EnemyPlacementTool>("Enemy Placement");
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Creates an enemy at the Scene view pivot (or under the selected object).\n" +
            "Works in a scene or in Prefab Mode. Bake the chunk's NavMesh afterward so it can path.",
            MessageType.Info);

        _enemyPrefab = (GameObject)EditorGUILayout.ObjectField(
            new GUIContent("Enemy Prefab", "e.g. Assets/Prefabs/Enemies/Enemy_Roadman"),
            _enemyPrefab, typeof(GameObject), false);

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Overrides (optional)", EditorStyles.boldLabel);
        EditorGUILayout.BeginHorizontal();
        _overrideHealth = EditorGUILayout.Toggle(_overrideHealth, GUILayout.Width(20));
        using (new EditorGUI.DisabledScope(!_overrideHealth))
            _healthOverride = EditorGUILayout.IntField("Health", _healthOverride);
        EditorGUILayout.EndHorizontal();

        EditorGUILayout.BeginHorizontal();
        _overrideDamage = EditorGUILayout.Toggle(_overrideDamage, GUILayout.Width(20));
        using (new EditorGUI.DisabledScope(!_overrideDamage))
            _damageOverride = EditorGUILayout.IntField("Damage", _damageOverride);
        EditorGUILayout.EndHorizontal();

        _level = Mathf.Max(0, EditorGUILayout.IntField(
            new GUIContent("Level", "0 attaches no EnemyLevel component at all — the enemy is " +
                "exactly what its prefab authors. 1 or more attaches one at that level.\n\n" +
                "The Health and Damage above are the level-1 baseline and are multiplied at " +
                "runtime, so the placed enemy's Inspector still reads the unscaled numbers."),
            _level));

        _questKey = EditorGUILayout.TextField(
            new GUIContent("Quest Key (optional)", "Adds a QuestActor with this key so quest code can find this exact enemy (e.g. via Health.OnDeath)."),
            _questKey);

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Death Loot (optional)", EditorStyles.boldLabel);
        DrawLootList();

        EditorGUILayout.Space();
        using (new EditorGUI.DisabledScope(_enemyPrefab == null))
        {
            if (GUILayout.Button("Create Enemy", GUILayout.Height(32)))
                CreateEnemy();
        }
    }

    private void DrawLootList()
    {
        int removeAt = -1;
        for (int i = 0; i < _loot.Count; i++)
        {
            EditorGUILayout.BeginHorizontal();
            _loot[i].Item = (ItemData)EditorGUILayout.ObjectField(_loot[i].Item, typeof(ItemData), false);
            _loot[i].Quantity = Mathf.Max(1, EditorGUILayout.IntField(_loot[i].Quantity, GUILayout.Width(40)));
            if (GUILayout.Button("X", GUILayout.Width(24)))
                removeAt = i;
            EditorGUILayout.EndHorizontal();
        }
        if (removeAt >= 0)
            _loot.RemoveAt(removeAt);

        if (GUILayout.Button("Add Loot Entry"))
            _loot.Add(new LootDrop());
    }

    private void CreateEnemy()
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        Transform parent = Selection.activeTransform;
        if (parent == null && stage != null)
            parent = stage.prefabContentsRoot.transform;

        Vector3 pos = SceneView.lastActiveSceneView != null
            ? SceneView.lastActiveSceneView.pivot
            : Vector3.zero;
        pos.y = 0f;

        GameObject instance = (GameObject)PrefabUtility.InstantiatePrefab(_enemyPrefab);
        Undo.RegisterCreatedObjectUndo(instance, "Create Enemy");
        if (parent != null)
            instance.transform.SetParent(parent, true);
        instance.transform.position = pos;

        Health health = instance.GetComponent<Health>();
        if (_overrideHealth && health != null)
        {
            health.MaxHealth = _healthOverride;
            health.CurrentHealth = _healthOverride;
        }

        EnemyAI ai = instance.GetComponent<EnemyAI>();
        if (_overrideDamage && ai != null)
            ai.Damage = _damageOverride;

        // Below 1 attaches nothing: level 1 and unlevelled are the same behaviourally, and a
        // level-1 component would still change the nameplate badge and the kill-XP source.
        // GetComponent first, never a bare AddComponent — two EnemyLevels would both run ApplyTo
        // and compound the scale with nothing logged.
        if (_level >= 1 && ai != null)
        {
            var enemyLevel = instance.GetComponent<EnemyLevel>();
            if (enemyLevel == null) enemyLevel = instance.AddComponent<EnemyLevel>();
            enemyLevel.Level = _level;
        }
        else if (_level >= 1)
        {
            Debug.LogWarning($"EnemyPlacementTool: Level {_level} was set but '{instance.name}' has " +
                             "no EnemyAI, so no EnemyLevel was attached.");
        }

        List<LootDrop> validLoot = _loot.FindAll(d => d != null && d.Item != null && d.Quantity > 0);
        if (validLoot.Count > 0)
        {
            var loot = instance.AddComponent<LootOnDeath>();
            loot.Loot = validLoot.ToArray();
        }

        if (!string.IsNullOrEmpty(_questKey))
            instance.AddComponent<QuestActor>().Key = _questKey;

        Selection.activeGameObject = instance;
        EditorSceneManager.MarkSceneDirty(stage != null ? stage.scene : EditorSceneManager.GetActiveScene());
        Debug.Log($"EnemyPlacementTool: created '{instance.name}' at {pos}. Move into place, Ctrl+S. " +
                  "Bake the chunk's NavMesh if you haven't already.");
    }
}
