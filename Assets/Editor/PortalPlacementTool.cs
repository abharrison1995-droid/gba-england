using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

/// <summary>
/// Drops DungeonPortal entrances/exits into the open scene OR the open prefab (Prefab Mode).
/// Typical dungeon hookup:
///   1. Open the overworld chunk prefab (or scene), point the tool at the dungeon's
///      MapChunkData, set the spawn position inside the dungeon, Create Portal.
///   2. Open the dungeon prefab, point the tool back at the overworld chunk with a spawn
///      just outside the entrance, Create Portal.
/// </summary>
public class PortalPlacementTool : EditorWindow
{
    private MapChunkData _targetChunk;
    private Vector3 _spawnPosition = new Vector3(0f, 0f, -8f);
    private string _prompt = "Enter";
    private bool _requireTutorialComplete;
    private bool _addVisual = true;
    private Color _visualColor = new Color(0.35f, 0.22f, 0.12f);

    [MenuItem("Tools/Exiled Alvaston/Place/Portal Placement")]
    public static void Open()
    {
        GetWindow<PortalPlacementTool>("Portal Placement");
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Creates a DungeonPortal at the Scene view pivot (or under the selected object).\n" +
            "Works in a scene or in Prefab Mode — open a dungeon prefab to place its exit portal.",
            MessageType.Info);

        _targetChunk = (MapChunkData)EditorGUILayout.ObjectField(
            new GUIContent("Target Chunk", "MapChunkData this portal loads — needs a ChunkPrefab."),
            _targetChunk, typeof(MapChunkData), false);
        _spawnPosition = EditorGUILayout.Vector3Field(
            new GUIContent("Spawn Position", "Where the player appears in the target chunk."), _spawnPosition);
        _prompt = EditorGUILayout.TextField("Prompt", _prompt);
        _requireTutorialComplete = EditorGUILayout.Toggle("Require Tutorial Done", _requireTutorialComplete);
        _addVisual = EditorGUILayout.Toggle("Add Door Visual", _addVisual);
        if (_addVisual)
            _visualColor = EditorGUILayout.ColorField("Visual Color", _visualColor);

        EditorGUILayout.Space();

        if (_targetChunk != null && _targetChunk.ChunkPrefab == null)
            EditorGUILayout.HelpBox($"'{_targetChunk.name}' has no ChunkPrefab — the portal won't work until it does.", MessageType.Warning);

        using (new EditorGUI.DisabledScope(_targetChunk == null))
        {
            if (GUILayout.Button("Create Portal", GUILayout.Height(32)))
                CreatePortal();
        }

        EditorGUILayout.Space();
        EditorGUILayout.HelpBox(
            "Also add the target chunk to the scene ChunkManager's AllChunks list so saves made " +
            "inside it can load (done automatically at runtime too — this just makes it explicit).",
            MessageType.None);
        using (new EditorGUI.DisabledScope(_targetChunk == null))
        {
            if (GUILayout.Button("Register Target Chunk With Scene ChunkManager"))
                RegisterWithChunkManager();
        }
    }

    private void CreatePortal()
    {
        // Prefab Mode edits go into the prefab's own scene, not the main scene
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        Transform parent = Selection.activeTransform;
        if (parent == null && stage != null)
            parent = stage.prefabContentsRoot.transform;

        Vector3 pos = SceneView.lastActiveSceneView != null
            ? SceneView.lastActiveSceneView.pivot
            : Vector3.zero;
        pos.y = 0f;

        var go = new GameObject($"Portal_{_targetChunk.ChunkName}");
        Undo.RegisterCreatedObjectUndo(go, "Create Dungeon Portal");
        if (parent != null)
            go.transform.SetParent(parent, true);
        go.transform.position = pos;

        var portal = go.AddComponent<DungeonPortal>();
        portal.TargetChunk = _targetChunk;
        portal.SpawnPosition = _spawnPosition;
        portal.Prompt = _prompt;
        portal.RequireTutorialComplete = _requireTutorialComplete;

        // Interactable is added by DungeonPortal.Awake at runtime, but adding it here too
        // lets you tweak Prompt/InteractRange in the Inspector.
        var interactable = go.AddComponent<Interactable>();
        interactable.Prompt = _prompt;
        interactable.InteractRange = 3f;

        if (_addVisual)
        {
            GameObject visual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            visual.name = "DoorVisual";
            Object.DestroyImmediate(visual.GetComponent<Collider>());
            visual.transform.SetParent(go.transform, false);
            visual.transform.localPosition = new Vector3(0f, 1.2f, 0f);
            visual.transform.localScale = new Vector3(0.5f, 2.6f, 3.2f);

            visual.GetComponent<Renderer>().sharedMaterial =
                EditorMaterialLibrary.GetOrCreate("PortalDoor", _visualColor);
        }

        Selection.activeGameObject = go;
        EditorSceneManager.MarkSceneDirty(stage != null ? stage.scene : EditorSceneManager.GetActiveScene());
        Debug.Log($"PortalPlacementTool: created '{go.name}' at {pos}. Move it into place, then Ctrl+S. " +
                  "Don't forget the return portal inside the target chunk's prefab.");
    }

    private void RegisterWithChunkManager()
    {
        var mgr = FindObjectOfType<ChunkManager>();
        if (mgr == null)
        {
            Debug.LogWarning("PortalPlacementTool: no ChunkManager in the open scene (are you in Prefab Mode? Do this from the main scene).");
            return;
        }

        if (mgr.AllChunks != null)
        {
            foreach (MapChunkData c in mgr.AllChunks)
                if (c == _targetChunk)
                {
                    Debug.Log("PortalPlacementTool: chunk already registered.");
                    return;
                }
        }

        Undo.RecordObject(mgr, "Register Chunk");
        int oldLen = mgr.AllChunks != null ? mgr.AllChunks.Length : 0;
        var grown = new MapChunkData[oldLen + 1];
        if (oldLen > 0) System.Array.Copy(mgr.AllChunks, grown, oldLen);
        grown[oldLen] = _targetChunk;
        mgr.AllChunks = grown;
        EditorUtility.SetDirty(mgr);
        EditorSceneManager.MarkSceneDirty(mgr.gameObject.scene);
        Debug.Log($"PortalPlacementTool: registered '{_targetChunk.ChunkName}' with ChunkManager. Ctrl+S to save the scene.");
    }
}
