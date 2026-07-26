using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.World;

/// <summary>
/// Drops a PlayerSpawnPoint (the player's arrival marker) into the open scene OR the open prefab
/// (Prefab Mode). Every teleport into a chunk — world load, instance door, DungeonPortal — puts
/// the player on that chunk's spawn point.
///
/// Workflow for a new instanced area (e.g. another cellar):
///   1. Open the area's chunk prefab in Prefab Mode.
///   2. Tools > Exiled Alvaston > Place > Player Spawn Point, then Create Spawn Point.
///   3. Drag the green marker where the player should appear, Ctrl+S to save the prefab.
/// </summary>
public class SpawnPointPlacementTool : EditorWindow
{
    private string _id = "";

    [MenuItem("Tools/Exiled Alvaston/Place/Spawn Point Placement")]
    public static void Open()
    {
        GetWindow<SpawnPointPlacementTool>("Player Spawn Point");
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Creates a PlayerSpawnPoint at the Scene view pivot (or under the selected object).\n\n" +
            "Chunks are instantiated from their PREFAB at runtime, so place the spawn point inside " +
            "the chunk's prefab (open it in Prefab Mode) — a copy left in the main scene is ignored.",
            MessageType.Info);

        _id = EditorGUILayout.TextField(
            new GUIContent("Id (optional)", "Leave blank for the default spawn. Set an id if a chunk " +
                "needs several arrival points that different doors/portals target."), _id);

        var stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage == null)
            EditorGUILayout.HelpBox(
                "You're not in Prefab Mode. Double-click a chunk prefab (e.g. Home_Alvaston_Prefab) " +
                "to edit it, or this marker will be created in the main scene and won't drive runtime spawns.",
                MessageType.Warning);

        EditorGUILayout.Space();
        if (GUILayout.Button("Create Spawn Point", GUILayout.Height(32)))
            CreateSpawnPoint();
    }

    private void CreateSpawnPoint()
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        Transform parent = Selection.activeTransform;
        if (parent == null && stage != null)
            parent = stage.prefabContentsRoot.transform;

        Vector3 pos = SceneView.lastActiveSceneView != null
            ? SceneView.lastActiveSceneView.pivot
            : Vector3.zero;
        pos.y = 0f;

        var go = new GameObject(string.IsNullOrEmpty(_id) ? "PlayerSpawn" : $"PlayerSpawn_{_id}");
        Undo.RegisterCreatedObjectUndo(go, "Create Player Spawn Point");
        if (parent != null)
            go.transform.SetParent(parent, true);
        go.transform.position = pos;

        var sp = go.AddComponent<PlayerSpawnPoint>();
        sp.Id = _id ?? "";

        Selection.activeGameObject = go;
        EditorSceneManager.MarkSceneDirty(stage != null ? stage.scene : EditorSceneManager.GetActiveScene());
        Debug.Log($"SpawnPointPlacementTool: created '{go.name}' at {pos}. Move the green marker into place, " +
                  "then Ctrl+S. (In Prefab Mode this saves into the chunk prefab, which is what runtime uses.)");
    }
}
