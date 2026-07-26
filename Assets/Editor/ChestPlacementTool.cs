using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

/// <summary>
/// Drops a generic <see cref="LootChest"/> into the open scene or prefab, loot list authored
/// right in the tool. Works with the real Animated Chest prefab (its own opening clip plays)
/// or falls back to a plain procedural box+lid.
/// </summary>
public class ChestPlacementTool : EditorWindow
{
    private const string DefaultChestPrefabPath = "Assets/3DModels/Animated Chest/OldChest/Chest.prefab";

    private string _chestName = "Chest";
    private GameObject _chestVisualPrefab;
    private readonly List<LootDrop> _loot = new List<LootDrop>();
    private string _questKey = "";

    [MenuItem("Tools/Exiled Alvaston/Place/Chest Placement")]
    public static void Open()
    {
        var window = GetWindow<ChestPlacementTool>("Chest Placement");
        if (window._chestVisualPrefab == null)
            window._chestVisualPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(DefaultChestPrefabPath);
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Creates a LootChest at the Scene view pivot (or under the selected object).\n" +
            "Works in a scene or in Prefab Mode. No visual prefab = plain procedural box+lid.",
            MessageType.Info);

        _chestName = EditorGUILayout.TextField("Chest Name", _chestName);
        _chestVisualPrefab = (GameObject)EditorGUILayout.ObjectField(
            new GUIContent("Visual Prefab", "Optional — must have an Animation component for its opening clip."),
            _chestVisualPrefab, typeof(GameObject), false);
        _questKey = EditorGUILayout.TextField(
            new GUIContent("Quest Key (optional)", "Adds a QuestActor with this key so quest code can find this exact chest."),
            _questKey);

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Loot", EditorStyles.boldLabel);
        DrawLootList();

        EditorGUILayout.Space();
        if (GUILayout.Button("Create Chest", GUILayout.Height(32)))
            CreateChest();
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

    private void CreateChest()
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        Transform parent = Selection.activeTransform;
        if (parent == null && stage != null)
            parent = stage.prefabContentsRoot.transform;

        Vector3 pos = SceneView.lastActiveSceneView != null
            ? SceneView.lastActiveSceneView.pivot
            : Vector3.zero;
        pos.y = 0f;

        var go = new GameObject($"Chest_{_chestName}");
        Undo.RegisterCreatedObjectUndo(go, "Create Chest");
        if (parent != null)
            go.transform.SetParent(parent, true);
        go.transform.position = pos;

        var chest = go.AddComponent<LootChest>();
        chest.ChestName = _chestName;
        chest.Loot = _loot.ToArray();

        if (_chestVisualPrefab != null)
        {
            GameObject visual = (GameObject)PrefabUtility.InstantiatePrefab(_chestVisualPrefab);
            visual.transform.SetParent(go.transform, false);
            visual.transform.localPosition = Vector3.zero;
            visual.transform.localRotation = Quaternion.identity;
            chest.ChestAnimation = visual.GetComponentInChildren<Animation>();
        }
        else
        {
            BuildFallbackVisual(go.transform, chest);
        }

        var interactable = go.AddComponent<Interactable>();
        interactable.Prompt = $"Open {_chestName}";
        interactable.Reusable = true;
        interactable.InteractRange = 2.75f;

        if (!string.IsNullOrEmpty(_questKey))
            go.AddComponent<QuestActor>().Key = _questKey;

        Selection.activeGameObject = go;
        EditorSceneManager.MarkSceneDirty(stage != null ? stage.scene : EditorSceneManager.GetActiveScene());
        Debug.Log($"ChestPlacementTool: created '{go.name}' at {pos} with {_loot.Count} loot entr{(_loot.Count == 1 ? "y" : "ies")}. Move into place, Ctrl+S.");
    }

    /// <summary>Plain box+lid — used only if no visual prefab is assigned.</summary>
    private static void BuildFallbackVisual(Transform parent, LootChest chest)
    {
        Material bodyMat = EditorMaterialLibrary.GetOrCreate("ChestPlaceholder", new Color(0.55f, 0.38f, 0.15f));

        GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
        body.name = "ChestBody";
        Object.DestroyImmediate(body.GetComponent<Collider>());
        body.transform.SetParent(parent, false);
        body.transform.localPosition = new Vector3(0f, 0.2f, 0f);
        body.transform.localScale = new Vector3(1f, 0.4f, 0.7f);
        body.GetComponent<Renderer>().sharedMaterial = bodyMat;

        GameObject hinge = new GameObject("LidHinge");
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
