using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;

/// <summary>
/// Authors a chunk's vehicle spawns without typing coordinates. Vehicles live on the chunk's
/// MapChunkData asset rather than inside the chunk prefab, so every vehicle in the world is
/// listed in one place — but that means there is nothing to drag in the scene, which is what
/// this window is for: line the scene view up where you want the vehicle and press the button.
///
/// Run via: Tools → GBH → Place → Vehicle Placement
/// </summary>
public class VehiclePlacementTool : EditorWindow
{
    private MapChunkData _chunk;
    private VehicleData _vehicle;
    private Vector3 _position;
    private float _yRotation;
    private Vector2 _scroll;

    [MenuItem("Tools/GBH/Place/Vehicle Placement")]
    public static void Open()
    {
        GetWindow<VehiclePlacementTool>("Vehicle Placement");
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Vehicles are spawned at runtime from the chunk's data, as children of the live chunk " +
            "instance. They exist only in the chunk that lists them, and re-entering a chunk puts " +
            "fresh ones back at these positions.",
            MessageType.Info);

        _chunk = (MapChunkData)EditorGUILayout.ObjectField(
            new GUIContent("Chunk", "The chunk asset to add the spawn to, e.g. Home_London_Data."),
            _chunk, typeof(MapChunkData), false);

        _vehicle = (VehicleData)EditorGUILayout.ObjectField(
            new GUIContent("Vehicle", "Create these via Assets > Create > ExiledAlvaston > Data > Vehicle Data."),
            _vehicle, typeof(VehicleData), false);

        EditorGUILayout.Space();
        _position = EditorGUILayout.Vector3Field("Position", _position);
        _yRotation = EditorGUILayout.Slider("Y rotation", _yRotation, 0f, 360f);

        using (new EditorGUILayout.HorizontalScope())
        {
            if (GUILayout.Button("From scene view"))
                UseSceneViewPivot();

            using (new EditorGUI.DisabledScope(Selection.activeTransform == null))
            {
                if (GUILayout.Button("From selection"))
                {
                    _position = Selection.activeTransform.position;
                    _yRotation = Selection.activeTransform.eulerAngles.y;
                }
            }
        }

        EditorGUILayout.Space();
        using (new EditorGUI.DisabledScope(_chunk == null || _vehicle == null))
        {
            if (GUILayout.Button("Add Vehicle Spawn", GUILayout.Height(30)))
                AddSpawn();
        }

        if (_chunk != null)
            DrawExistingSpawns();
    }

    private void UseSceneViewPivot()
    {
        var view = SceneView.lastActiveSceneView;
        if (view == null)
        {
            Debug.LogWarning("VehiclePlacementTool: no scene view open.");
            return;
        }

        Vector3 pivot = view.pivot;
        pivot.y = 0f; // vehicles sit on the ground plane
        _position = pivot;
    }

    private void AddSpawn()
    {
        Undo.RecordObject(_chunk, "Add vehicle spawn");

        if (_chunk.VehicleSpawns == null)
            _chunk.VehicleSpawns = new System.Collections.Generic.List<VehicleSpawn>();

        _chunk.VehicleSpawns.Add(new VehicleSpawn
        {
            Vehicle = _vehicle,
            Position = _position,
            YRotation = _yRotation
        });

        EditorUtility.SetDirty(_chunk);
        AssetDatabase.SaveAssets();
        Debug.Log($"VehiclePlacementTool: added {_vehicle.name} to {_chunk.ChunkName} at {_position}.");
    }

    private void DrawExistingSpawns()
    {
        var spawns = _chunk.VehicleSpawns;
        int count = spawns != null ? spawns.Count : 0;

        EditorGUILayout.Space();
        EditorGUILayout.LabelField($"{_chunk.ChunkName}: {count} vehicle(s)", EditorStyles.boldLabel);
        if (count == 0) return;

        // Removal is deferred rather than done mid-loop: mutating the list while the layout is
        // being built desynchronises Unity's IMGUI layout/repaint passes, and ExitGUI would skip
        // the EndScrollView below.
        int removeAt = -1;

        _scroll = EditorGUILayout.BeginScrollView(_scroll);
        for (int i = 0; i < count; i++)
        {
            VehicleSpawn spawn = spawns[i];
            using (new EditorGUILayout.HorizontalScope())
            {
                string label = spawn.Vehicle != null ? spawn.Vehicle.VehicleName : "<missing>";
                EditorGUILayout.LabelField($"{label}  {spawn.Position}", GUILayout.MinWidth(150));

                if (GUILayout.Button("Edit", GUILayout.Width(48)))
                {
                    _vehicle = spawn.Vehicle;
                    _position = spawn.Position;
                    _yRotation = spawn.YRotation;
                }

                if (GUILayout.Button("Remove", GUILayout.Width(64)))
                    removeAt = i;
            }
        }
        EditorGUILayout.EndScrollView();

        if (removeAt >= 0)
        {
            Undo.RecordObject(_chunk, "Remove vehicle spawn");
            spawns.RemoveAt(removeAt);
            EditorUtility.SetDirty(_chunk);
            AssetDatabase.SaveAssets();
        }
    }
}
