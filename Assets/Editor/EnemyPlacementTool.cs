using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.Data;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;

/// <summary>
/// Drops an enemy prefab (e.g. Assets/Prefabs/Enemies/Enemy_Orc2) into the open scene or
/// prefab, with optional stat overrides, a death loot list, and a quest key — an authored,
/// saved-in-prefab placement rather than a Play-mode debug spawn. The chunk still needs its
/// NavMesh baked (Tools > Exiled Alvaston > World > Bake Navigation Mesh) for the enemy to path.
/// </summary>
public class EnemyPlacementTool : EditorWindow
{
    private GameObject _enemyPrefab;

    private bool _overrideHealth;
    private int _healthOverride = 45;
    private bool _overrideDamage;
    private int _damageOverride = 7;

    private readonly List<LootDrop> _loot = new List<LootDrop>();
    private string _questKey = "";

    [MenuItem("Tools/Exiled Alvaston/Place/Enemy Placement")]
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
            new GUIContent("Enemy Prefab", "e.g. Assets/Prefabs/Enemies/Enemy_Orc2"),
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
