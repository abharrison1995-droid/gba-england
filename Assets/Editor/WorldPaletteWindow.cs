using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.Data;

/// <summary>
/// Click-to-place content authoring. Replaces the five Place/… windows, which all shared one
/// shape — fill in fields, press a button, get one object at the Scene view pivot — with a palette
/// of preconfigured <see cref="PlacementPreset"/> assets you arm once and then click into place,
/// as many times as you like.
///
/// Run via: Tools → GBH → World Palette
///
/// Works in a scene or in Prefab Mode; in Prefab Mode placements go into the prefab's own scene,
/// which is how content gets authored into a chunk prefab (chunks are instantiated from their
/// prefab at runtime, so anything left loose in c.unity is not part of the chunk).
/// </summary>
public class WorldPaletteWindow : EditorWindow
{
    private const float ButtonSize = 68f;
    private const float GroundPlaneY = 0f;

    private PlacementPreset[] _presets = new PlacementPreset[0];
    private PlacementPreset _armed;
    private Vector2 _scroll;

    /// <summary>Where the last hover landed, for the ghost and for the placement itself.</summary>
    private Vector3 _hoverPoint;
    private bool _hoverValid;

    /// <summary>Vehicles are authored onto a chunk asset, not into a scene — this is the target.</summary>
    private MapChunkData _vehicleChunk;

    /// <summary>
    /// The level the next enemy stamp gets, overriding the armed preset's own Enemy Level.
    ///
    /// Lives on the window and therefore in no asset: a preset is a single file, so a level that
    /// only lived on it would mean one preset per band (Preset_Roadman_Lv2, _Lv6, …) or editing the
    /// asset between placements, which is a hidden mode nobody remembers they are in. Stamp five
    /// Lv2 Roadmen in Alvaston, retype 6, stamp five more in London.
    ///
    /// Reset from the preset every time one is armed, so a level never silently carries over from
    /// the last enemy stamped.
    /// </summary>
    private int _enemyLevel;

    /// <summary>
    /// Everything this window has placed, and the parent the last one went into.
    ///
    /// Placing selects what it just made, so you can nudge it straight away — but the parent is
    /// read from the selection, so without these the next stamp would land *inside* the previous
    /// one. Holding Shift for a run of five would bury the fifth four levels deep.
    /// </summary>
    private readonly HashSet<int> _placed = new HashSet<int>();
    private Transform _lastParent;

    [MenuItem("Tools/GBH/World Palette")]
    public static void Open()
    {
        GetWindow<WorldPaletteWindow>("World Palette");
    }

    private void OnEnable()
    {
        Refresh();
        SceneView.duringSceneGui += OnSceneGUI;
    }

    private void OnDisable()
    {
        SceneView.duringSceneGui -= OnSceneGUI;
    }

    private void Refresh()
    {
        _presets = AssetDatabase.FindAssets("t:PlacementPreset")
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<PlacementPreset>)
            .Where(p => p != null)
            .OrderBy(p => (int)p.Category)
            .ThenBy(p => (int)p.Region)
            .ThenBy(p => p.Label)
            .ToArray();
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  THE PALETTE
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void OnGUI()
    {
        using (new EditorGUILayout.HorizontalScope())
        {
            EditorGUILayout.LabelField(_armed != null ? $"Armed: {_armed.Label}" : "Nothing armed",
                EditorStyles.boldLabel);
            if (GUILayout.Button("Refresh", GUILayout.Width(70))) Refresh();
        }

        if (_armed != null)
        {
            EditorGUILayout.HelpBox(
                "Click in the Scene view to place. Hold Shift to keep placing.\n" +
                "Esc, or clicking the armed preset again, disarms.",
                MessageType.Info);

            if (_armed.Category == PlacementPreset.PlacementCategory.Enemy)
                DrawEnemyLevel();

            if (GUILayout.Button("Disarm")) Disarm();
        }
        else
        {
            EditorGUILayout.HelpBox(
                "Pick a preset, then click in the Scene view to place it.\n" +
                "In Prefab Mode placements go into the open prefab — which is where chunk content " +
                "has to live, since chunks are instantiated from their prefab at runtime.\n\n" +
                "A placement is a copy, not a link: editing a preset afterwards — or importing art " +
                "that rewires it — changes what you place NEXT, not what is already standing there. " +
                "To update an existing one, delete it and stamp it again.",
                MessageType.None);
        }

        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        EditorGUILayout.LabelField(stage != null
            ? $"Placing into prefab: {stage.assetPath}"
            : "Placing into the open scene", EditorStyles.miniLabel);

        if (_presets.Length == 0)
        {
            EditorGUILayout.Space();
            EditorGUILayout.HelpBox(
                "No PlacementPreset assets found.\n\n" +
                "Generate a starter set with Tools → GBH → Content → Create Starter Presets, or " +
                "make one via Assets → Create → ExiledAlvaston → Data → Placement Preset.",
                MessageType.Warning);
            if (GUILayout.Button("Create Starter Presets"))
            {
                StarterPresetGenerator.Run();
                Refresh();
            }
            return;
        }

        EditorGUILayout.Space();
        _scroll = EditorGUILayout.BeginScrollView(_scroll);

        foreach (var group in _presets.GroupBy(p => p.Category))
        {
            EditorGUILayout.LabelField(group.Key.ToString(), EditorStyles.boldLabel);

            if (group.Key == PlacementPreset.PlacementCategory.NPC)
                DrawNpcRegions(group.ToList());
            else
                DrawGrid(group.ToList());

            if (group.Key == PlacementPreset.PlacementCategory.Vehicle)
                DrawVehicleTarget();

            EditorGUILayout.Space();
        }

        EditorGUILayout.EndScrollView();
    }

    /// <summary>
    /// Every <see cref="PlacementPreset.CityRegion"/>, in enum order, resolved once rather than per
    /// repaint — <c>Enum.GetValues</c> allocates a fresh array on every call and OnGUI runs many
    /// times a second. Reading it from the enum rather than listing the regions here means an
    /// appended region shows up in the palette without touching this file.
    /// </summary>
    private static readonly PlacementPreset.CityRegion[] Regions =
        (PlacementPreset.CityRegion[])System.Enum.GetValues(typeof(PlacementPreset.CityRegion));

    /// <summary>
    /// The NPC section, split by city. Unlike the category grouping above this iterates the enum
    /// rather than the presets, so a region with nothing in it still draws its heading: the cast is
    /// being written city by city, and an empty Birmingham heading is the reminder that it is next.
    /// </summary>
    private void DrawNpcRegions(List<PlacementPreset> npcs)
    {
        EditorGUI.indentLevel++;

        foreach (PlacementPreset.CityRegion region in Regions)
        {
            EditorGUILayout.LabelField(region.ToString(), EditorStyles.miniBoldLabel);

            List<PlacementPreset> inRegion = npcs.Where(p => p.Region == region).ToList();
            if (inRegion.Count == 0)
                EditorGUILayout.LabelField("(none yet)", EditorStyles.miniLabel);
            else
                DrawGrid(inRegion);
        }

        EditorGUI.indentLevel--;
    }

    private void DrawGrid(List<PlacementPreset> presets)
    {
        int perRow = Mathf.Max(1, Mathf.FloorToInt((position.width - 30f) / (ButtonSize + 6f)));

        for (int i = 0; i < presets.Count; i++)
        {
            if (i % perRow == 0) EditorGUILayout.BeginHorizontal();

            PlacementPreset preset = presets[i];
            bool isArmed = preset == _armed;

            var content = new GUIContent(
                IconFor(preset) == null ? preset.Label : "",
                IconFor(preset),
                preset.Label);

            Color prev = GUI.backgroundColor;
            if (isArmed) GUI.backgroundColor = new Color(0.45f, 0.8f, 1f);

            if (GUILayout.Button(content, GUILayout.Width(ButtonSize), GUILayout.Height(ButtonSize)))
            {
                // Clicking the armed preset again disarms, so the palette has no dead-end state
                // where the only way out is Esc in a different window.
                if (isArmed) Disarm();
                else Arm(preset);
            }

            GUI.backgroundColor = prev;

            if (i % perRow == perRow - 1 || i == presets.Count - 1) EditorGUILayout.EndHorizontal();
        }
    }

    private void DrawVehicleTarget()
    {
        EditorGUI.indentLevel++;
        _vehicleChunk = (MapChunkData)EditorGUILayout.ObjectField(
            new GUIContent("Target chunk", "Vehicles live on the chunk's MapChunkData, not in the " +
                "chunk prefab, so a vehicle placement writes a VehicleSpawn entry here."),
            _vehicleChunk, typeof(MapChunkData), false);

        if (_armed != null
            && _armed.Category == PlacementPreset.PlacementCategory.Vehicle
            && _vehicleChunk == null)
        {
            EditorGUILayout.HelpBox("Pick a target chunk before placing a vehicle.", MessageType.Warning);
        }
        EditorGUI.indentLevel--;
    }

    private void DrawEnemyLevel()
    {
        // Clamped at 0 so -1 can never be typed: PlacementBuilders reads a negative as "no
        // override, use the preset", which is not something the author should be able to mean by
        // accident.
        _enemyLevel = Mathf.Max(0, EditorGUILayout.IntField(
            new GUIContent("Level", "Level for the enemies you stamp next, overriding the preset's " +
                "own Enemy Level. 0 attaches no EnemyLevel component at all — the enemy is exactly " +
                "what its prefab authors.\n\n" +
                "The prefab's Health and Damage are the level-1 baseline and are multiplied at " +
                "runtime, so a placed enemy's Inspector still reads the unscaled numbers."),
            _enemyLevel));
    }

    private static Texture IconFor(PlacementPreset preset)
    {
        if (preset.Icon == null) return null;

        // AssetPreview renders asynchronously and returns null on the first few calls, so the
        // sprite's own texture is the fallback rather than an empty button.
        Texture preview = AssetPreview.GetAssetPreview(preset.Icon);
        return preview != null ? preview : preset.Icon.texture;
    }

    private void Arm(PlacementPreset preset)
    {
        _armed = preset;
        _hoverValid = false;
        // From the preset every time, so arming a Lv1 Neek after stamping Lv6 Roadmen does not
        // quietly place Lv6 Neeks.
        _enemyLevel = preset != null ? Mathf.Max(0, preset.EnemyLevel) : 0;
        SceneView.RepaintAll();
        Repaint();
    }

    private void Disarm()
    {
        _armed = null;
        _hoverValid = false;
        SceneView.RepaintAll();
        Repaint();
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  THE SCENE VIEW
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void OnSceneGUI(SceneView view)
    {
        if (_armed == null) return;

        Event e = Event.current;

        // Takes the default control so a click places instead of selecting whatever is under the
        // cursor. Without this, the first click just picks the ground mesh.
        int control = GUIUtility.GetControlID(FocusType.Passive);
        HandleUtility.AddDefaultControl(control);

        if (e.type == EventType.KeyDown && e.keyCode == KeyCode.Escape)
        {
            Disarm();
            e.Use();
            return;
        }

        if (e.type == EventType.MouseMove || e.type == EventType.MouseDrag || e.type == EventType.Repaint)
        {
            _hoverValid = TryGetPoint(e.mousePosition, out _hoverPoint);
            if (e.type != EventType.Repaint) view.Repaint();
        }

        if (e.type == EventType.Repaint && _hoverValid)
            DrawGhost(_hoverPoint);

        if (e.type == EventType.MouseDown && e.button == 0 && !e.alt)
        {
            if (TryGetPoint(e.mousePosition, out Vector3 point))
            {
                PlaceAt(point);
                // Shift is stamp mode — keep the preset armed for a run of placements.
                if (!e.shift) Disarm();
            }
            e.Use();
        }
    }

    private static void DrawGhost(Vector3 point)
    {
        Handles.color = new Color(0.35f, 0.8f, 1f, 0.9f);
        Handles.DrawWireDisc(point, Vector3.up, 0.6f);
        Handles.DrawWireDisc(point, Vector3.up, 0.15f);
        Handles.DrawLine(point, point + Vector3.up * 1.35f);
    }

    /// <summary>
    /// Where the cursor is pointing in the world. Prefers real geometry so placements sit on
    /// whatever is under them, and falls back to the ground plane — which is also the only option
    /// in Prefab Mode when the prefab has no colliders yet.
    /// </summary>
    private static bool TryGetPoint(Vector2 mousePosition, out Vector3 point)
    {
        Ray ray = HandleUtility.GUIPointToWorldRay(mousePosition);

        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage != null)
        {
            // A prefab stage has its own physics scene; the global Physics.Raycast would hit the
            // main scene's colliders, which are not even visible here.
            if (stage.scene.GetPhysicsScene().Raycast(ray.origin, ray.direction, out RaycastHit stageHit, 5000f))
            {
                point = stageHit.point;
                return true;
            }
        }
        else if (Physics.Raycast(ray, out RaycastHit hit, 5000f))
        {
            point = hit.point;
            return true;
        }

        var ground = new Plane(Vector3.up, new Vector3(0f, GroundPlaneY, 0f));
        if (ground.Raycast(ray, out float distance))
        {
            point = ray.GetPoint(distance);
            return true;
        }

        point = Vector3.zero;
        return false;
    }

    private void PlaceAt(Vector3 point)
    {
        if (_armed.Category == PlacementPreset.PlacementCategory.Vehicle)
        {
            PlaceVehicle(point);
            return;
        }

        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        Transform parent = ResolveParent(stage);

        GameObject created = PlacementBuilders.Build(_armed, point, parent, _enemyLevel);
        if (created == null) return;

        _placed.Add(created.GetInstanceID());
        _lastParent = parent;

        Selection.activeGameObject = created;
        EditorSceneManager.MarkSceneDirty(stage != null ? stage.scene : EditorSceneManager.GetActiveScene());
        Debug.Log($"World Palette: placed '{created.name}' at {point}. Ctrl+S to save " +
                  (stage != null ? "the prefab." : "the scene."));
    }

    /// <summary>
    /// Where a placement is parented.
    ///
    /// The rule the old Place windows used still holds — an explicit selection wins, then the open
    /// prefab's root, then the scene root — with one exception this window needs and they did not:
    /// a placement of ours is never allowed to become a parent. Placing selects what it made, so
    /// without that exception each stamp would nest inside the last, and a Shift-held run would
    /// build a chain instead of a row. When the selection is ours, the parent that one went into
    /// is used again, which is what "keep stamping into the same group" should mean.
    /// </summary>
    private Transform ResolveParent(PrefabStage stage)
    {
        Transform selected = Selection.activeTransform;

        if (selected != null && IsOurs(selected))
            return _lastParent != null ? _lastParent
                 : (stage != null ? stage.prefabContentsRoot.transform : null);

        if (selected != null) return selected;

        return stage != null ? stage.prefabContentsRoot.transform : null;
    }

    /// <summary>
    /// True if this transform is something this window placed, or sits inside one — selecting a
    /// child of a placement is just as bad a parent as the placement itself.
    /// </summary>
    private bool IsOurs(Transform t)
    {
        for (Transform c = t; c != null; c = c.parent)
            if (_placed.Contains(c.gameObject.GetInstanceID())) return true;

        return false;
    }

    /// <summary>
    /// Vehicles have no scene object to create — VehicleSpawner instantiates them at runtime from
    /// the chunk's own list, so authoring one means appending to that list (CLAUDE.md §11).
    /// </summary>
    private void PlaceVehicle(Vector3 point)
    {
        if (_vehicleChunk == null)
        {
            Debug.LogWarning("World Palette: pick a target chunk before placing a vehicle.");
            return;
        }
        if (_armed.Vehicle == null)
        {
            Debug.LogWarning($"World Palette: vehicle preset '{_armed.Label}' has no VehicleData assigned.");
            return;
        }

        Undo.RecordObject(_vehicleChunk, "Add vehicle spawn");

        if (_vehicleChunk.VehicleSpawns == null)
            _vehicleChunk.VehicleSpawns = new List<VehicleSpawn>();

        point.y = GroundPlaneY;   // vehicles sit on the ground plane
        _vehicleChunk.VehicleSpawns.Add(new VehicleSpawn
        {
            Vehicle = _armed.Vehicle,
            Position = point,
            YRotation = 0f
        });

        EditorUtility.SetDirty(_vehicleChunk);
        AssetDatabase.SaveAssets();
        Debug.Log($"World Palette: added {_armed.Vehicle.VehicleName} to " +
                  $"{_vehicleChunk.ChunkName} at {point}.");
    }
}
