using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

/// <summary>
/// Authors a linked pair of doors between two chunks — an exterior entrance and the interior exit
/// that returns you to it — as one operation, and can re-run over its own output to update it.
///
/// Why a pair and not a portal: a single portal is half a door. Every one authored one end at a
/// time has to have its partner remembered, its return position typed as a raw coordinate, and its
/// target chunk registered somewhere the save system can find it. Missing any of those fails
/// quietly — the player walks into a building and cannot get out, or a save made inside it will not
/// load after a restart. Both ends and both arrival markers are written together here, and the
/// chunks are registered while we are at it.
///
/// Typical run:
///   1. Open the exterior chunk prefab in Prefab Mode, select the doorway, capture the door pose.
///   2. Capture or derive the return marker, at least 3.5 m clear of the door.
///   3. Open the interior prefab in Prefab Mode and do the same for its exit and arrival marker.
///   4. Leave Prefab Mode, then press Create Or Update Linked Pair.
///
/// Step 4 is not optional: closed prefabs are edited through LoadPrefabContents, and doing that to
/// a prefab that is simultaneously open in Prefab Mode fights whatever the stage has in memory.
/// The tool refuses rather than risking it.
/// </summary>
public class PortalPlacementTool : EditorWindow
{
    // Every authoring field is [SerializeField] on purpose. An EditorWindow is a ScriptableObject,
    // so marked fields survive a domain reload — a script recompile, or entering Play mode. The
    // workflow spans two trips through Prefab Mode and a save, and losing four captured poses to a
    // stray recompile halfway through is the kind of thing that makes a tool not get used.

    // ── Link ────────────────────────────────────────────────────────────────────────────────
    [SerializeField] private string _linkId = "police_station_front";
    [SerializeField] private MapChunkData _exteriorChunk;
    [SerializeField] private MapChunkData _interiorChunk;

    // ── Prompts and behaviour ───────────────────────────────────────────────────────────────
    [SerializeField] private string _enterPrompt = "Enter";
    [SerializeField] private string _exitPrompt = "Exit";
    [SerializeField] private float _interactRange = 3f;
    [SerializeField] private bool _requireTutorialComplete;
    [SerializeField] private bool _overwritePoses = true;

    // ── Poses, all relative to the chunk prefab root ─────────────────────────────────────────
    [SerializeField] private Vector3 _exteriorDoorPos, _exteriorDoorEuler;
    [SerializeField] private Vector3 _outsideMarkerPos = new Vector3(0f, 0f, -3.5f), _outsideMarkerEuler;
    [SerializeField] private Vector3 _interiorDoorPos, _interiorDoorEuler;
    [SerializeField] private Vector3 _insideMarkerPos = new Vector3(0f, 0f, 3.5f), _insideMarkerEuler;

    [SerializeField] private float _deriveOffset = LocationLinks.MinMarkerClearance;

    // ── Interior bundle ─────────────────────────────────────────────────────────────────────
    [SerializeField] private string _newInteriorName = "Police_Station_London";
    [SerializeField] private bool _showBundle;

    // ── Report ──────────────────────────────────────────────────────────────────────────────
    private List<LocationLinkValidator.Finding> _findings;
    private Vector2 _reportScroll;
    private Vector2 _windowScroll;

    [MenuItem("Tools/GBH/Place/Portal Placement")]
    public static void Open()
    {
        GetWindow<PortalPlacementTool>("Portal Placement");
    }

    private void OnGUI()
    {
        _windowScroll = EditorGUILayout.BeginScrollView(_windowScroll);

        EditorGUILayout.HelpBox(
            "Creates BOTH ends of a door: an entrance in the exterior chunk, an exit in the interior " +
            "chunk, and the arrival marker each one lands at.\n\n" +
            "Capture the poses from Prefab Mode, then LEAVE Prefab Mode before pressing Create — " +
            "closed prefabs are edited in place, and the tool refuses while a prefab is open.\n\n" +
            "Re-running with the same Link Id updates what it made before. It never duplicates and " +
            "never rebuilds a prefab from scratch, so no GUIDs change.",
            MessageType.Info);

        DrawPrefabStageBanner();

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Link", EditorStyles.boldLabel);
        _linkId = EditorGUILayout.TextField(
            new GUIContent("Link Id", "Stable name for this pair, e.g. police_station_front. Letters, " +
                                      "digits, _ and - only. Re-using it is how you update."), _linkId);
        _exteriorChunk = (MapChunkData)EditorGUILayout.ObjectField(
            new GUIContent("Exterior Chunk", "The chunk the door is in — usually an overworld chunk."),
            _exteriorChunk, typeof(MapChunkData), false);
        _interiorChunk = (MapChunkData)EditorGUILayout.ObjectField(
            new GUIContent("Interior Chunk", "The chunk being entered — building, basement, cave, sewer."),
            _interiorChunk, typeof(MapChunkData), false);

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Prompts", EditorStyles.boldLabel);
        _enterPrompt = EditorGUILayout.TextField(
            new GUIContent("Exterior Prompt", "Shown on the HUD outside, e.g. Enter Police Station."), _enterPrompt);
        _exitPrompt = EditorGUILayout.TextField(
            new GUIContent("Interior Prompt", "Shown on the HUD inside, e.g. Exit Police Station."), _exitPrompt);
        _interactRange = EditorGUILayout.FloatField(
            new GUIContent("Interact Range", "How close the player stands to get the prompt. 3 is the norm."),
            _interactRange);
        _requireTutorialComplete = EditorGUILayout.Toggle(
            new GUIContent("Require Tutorial Done", "Barred until the Manor Cellars tutorial is finished."),
            _requireTutorialComplete);

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Poses (relative to the chunk prefab root)", EditorStyles.boldLabel);
        _deriveOffset = EditorGUILayout.FloatField(
            new GUIContent("Derive Offset", "How far in front of a door the Derive button puts its marker."),
            _deriveOffset);

        DrawPose("Exterior Door", ref _exteriorDoorPos, ref _exteriorDoorEuler, null, null);
        DrawPose("Outside Marker", ref _outsideMarkerPos, ref _outsideMarkerEuler, _exteriorDoorPos, _exteriorDoorEuler);
        EditorGUILayout.Space(4);
        DrawPose("Interior Door", ref _interiorDoorPos, ref _interiorDoorEuler, null, null);
        DrawPose("Inside Marker", ref _insideMarkerPos, ref _insideMarkerEuler, _interiorDoorPos, _interiorDoorEuler);

        _overwritePoses = EditorGUILayout.Toggle(
            new GUIContent("Overwrite Poses On Update",
                           "On. Turn it OFF to change only the prompts, target or range of an existing pair " +
                           "and leave whatever positions the doors have been nudged to in the prefab."),
            _overwritePoses);

        DrawClearanceWarnings();

        EditorGUILayout.Space();
        DrawCreateButton();

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Checks and registration", EditorStyles.boldLabel);
        if (GUILayout.Button("Validate All Location Links", GUILayout.Height(24)))
        {
            _findings = LocationLinkValidator.Run();
            foreach (var f in _findings) Debug.Log("LocationLinks " + f);
        }
        using (new EditorGUI.DisabledScope(_exteriorChunk == null && _interiorChunk == null))
        {
            if (GUILayout.Button("Register Both Chunks With Scene ChunkManager"))
                RegisterWithChunkManager();
        }

        DrawReport();

        EditorGUILayout.Space();
        _showBundle = EditorGUILayout.Foldout(_showBundle, "Create Empty Interior Bundle", true);
        if (_showBundle) DrawBundleSection();

        EditorGUILayout.EndScrollView();
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  UI PIECES
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void DrawPrefabStageBanner()
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage == null) return;

        EditorGUILayout.HelpBox(
            $"Prefab Mode is open on {System.IO.Path.GetFileName(stage.assetPath)}. Capturing poses is " +
            "exactly what you want here — creating the pair is not, and is disabled until you leave.",
            MessageType.Warning);
    }

    /// <summary>
    /// One pose row. <paramref name="deriveFromPos"/> being non-null turns on the Derive button,
    /// which puts the marker a set distance out along the door's own forward — the direction the
    /// portal gizmo's arrow points.
    /// </summary>
    private void DrawPose(string label, ref Vector3 pos, ref Vector3 euler,
                          Vector3? deriveFromPos, Vector3? deriveFromEuler)
    {
        EditorGUILayout.LabelField(label, EditorStyles.miniBoldLabel);
        EditorGUI.indentLevel++;
        pos = EditorGUILayout.Vector3Field("Position", pos);
        euler = EditorGUILayout.Vector3Field("Rotation", euler);

        EditorGUILayout.BeginHorizontal();
        GUILayout.Space(EditorGUI.indentLevel * 15f);
        if (GUILayout.Button(new GUIContent("From Selection",
                "Takes the position and rotation of whatever is selected in the Hierarchy.")))
        {
            if (Selection.activeTransform == null)
                Debug.LogWarning("PortalPlacementTool: nothing selected.");
            else
                CaptureFrom(Selection.activeTransform, ref pos, ref euler);
        }
        if (GUILayout.Button(new GUIContent("From Scene Pivot",
                "Takes the Scene view's pivot point. Rotation is left as it is — the pivot has none.")))
        {
            if (SceneView.lastActiveSceneView == null)
                Debug.LogWarning("PortalPlacementTool: no Scene view open.");
            else
                pos = ToRootSpace(SceneView.lastActiveSceneView.pivot);
        }
        using (new EditorGUI.DisabledScope(!deriveFromPos.HasValue || !deriveFromEuler.HasValue))
        {
            if (GUILayout.Button(new GUIContent("Derive From Door",
                    "Puts this marker Derive Offset metres along the door's forward direction.")))
            {
                Quaternion rot = Quaternion.Euler(deriveFromEuler.Value);
                pos = deriveFromPos.Value + rot * Vector3.forward * _deriveOffset;
                euler = deriveFromEuler.Value;
            }
        }
        EditorGUILayout.EndHorizontal();
        EditorGUI.indentLevel--;
    }

    private void DrawClearanceWarnings()
    {
        // Distance is measured on the X/Z plane, matching PlayerInteractor: it ignores Y when it
        // decides what is in range, so a marker directly above a door is still "on top of" it.
        float outside = FlatDistance(_outsideMarkerPos, _exteriorDoorPos);
        float inside = FlatDistance(_insideMarkerPos, _interiorDoorPos);

        if (outside < LocationLinks.MinMarkerClearance)
        {
            EditorGUILayout.HelpBox(
                $"The outside marker is {outside:0.00} m from the exterior door — under " +
                $"{LocationLinks.MinMarkerClearance:0.0} m. Exiting will drop the player straight back " +
                "inside the entrance's USE range with its prompt lit.", MessageType.Warning);
        }
        if (inside < LocationLinks.MinMarkerClearance)
        {
            EditorGUILayout.HelpBox(
                $"The inside marker is {inside:0.00} m from the interior door — under " +
                $"{LocationLinks.MinMarkerClearance:0.0} m. Entering will drop the player straight onto " +
                "the way out.", MessageType.Warning);
        }
    }

    private void DrawCreateButton()
    {
        string blocker = WhyCannotCreate();
        if (blocker != null)
            EditorGUILayout.HelpBox(blocker, MessageType.Warning);

        using (new EditorGUI.DisabledScope(blocker != null))
        {
            if (GUILayout.Button("Create Or Update Linked Pair", GUILayout.Height(32)))
                CreateOrUpdateLinkedPair();
        }
    }

    private void DrawReport()
    {
        if (_findings == null) return;

        EditorGUILayout.Space();
        EditorGUILayout.LabelField($"Validation — {_findings.Count} finding(s)", EditorStyles.boldLabel);
        _reportScroll = EditorGUILayout.BeginScrollView(_reportScroll, GUILayout.Height(180));
        foreach (var f in _findings)
        {
            MessageType type = f.Level == LocationLinkValidator.Severity.Error ? MessageType.Error
                             : f.Level == LocationLinkValidator.Severity.Warning ? MessageType.Warning
                             : MessageType.Info;
            EditorGUILayout.HelpBox($"{f.Where}\n{f.Message}", type);
        }
        EditorGUILayout.EndScrollView();
    }

    private void DrawBundleSection()
    {
        EditorGUILayout.HelpBox(
            "Creates an EMPTY MapChunkData and an EMPTY chunk prefab, and registers them. It will not " +
            "overwrite anything that already exists, and it does not decorate the interior.\n\n" +
            "⚠ The prefab it makes has no floor. Give it geometry with a collider before wiring a door " +
            "to it, or the player falls through and the void catcher loops them.",
            MessageType.None);

        _newInteriorName = EditorGUILayout.TextField(
            new GUIContent("Name", "Used for the ChunkName, the asset and the prefab, e.g. Police_Station_London."),
            _newInteriorName);

        using (new EditorGUI.DisabledScope(string.IsNullOrEmpty(_newInteriorName)
                                           || PrefabStageUtility.GetCurrentPrefabStage() != null))
        {
            if (GUILayout.Button("Create Empty Interior Bundle"))
                CreateInteriorBundle();
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  CAPTURE
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void CaptureFrom(Transform t, ref Vector3 pos, ref Vector3 euler)
    {
        pos = ToRootSpace(t.position);
        euler = ToRootSpaceRotation(t.rotation).eulerAngles;
    }

    /// <summary>
    /// Poses are stored relative to the chunk prefab root, because that is the space the runtime
    /// uses: chunks are always instantiated at the origin, so root-relative is what the player will
    /// actually walk into. Outside Prefab Mode there is nothing to be relative to and the world
    /// value is taken as-is — which is correct when the chunk instance is sitting at the origin,
    /// as ChunkManager always puts it.
    /// </summary>
    private static Vector3 ToRootSpace(Vector3 world)
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage == null) return world;
        return stage.prefabContentsRoot.transform.InverseTransformPoint(world);
    }

    private static Quaternion ToRootSpaceRotation(Quaternion world)
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage == null) return world;
        return Quaternion.Inverse(stage.prefabContentsRoot.transform.rotation) * world;
    }

    private static float FlatDistance(Vector3 a, Vector3 b)
    {
        Vector3 d = a - b;
        d.y = 0f;
        return d.magnitude;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  CREATE
    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// Null when the pair can be written; otherwise the reason, shown to the user.
    ///
    /// Runs every repaint, so it stays to checks that read only the fields in front of us. The
    /// project-wide duplicate-name scan is in <see cref="FindDuplicateChunkName"/> and is run once,
    /// at the moment Create is pressed.
    /// </summary>
    private string WhyCannotCreate()
    {
        if (!LocationLinks.IsValidLinkId(_linkId))
            return "Link Id must be non-empty and contain only letters, digits, underscores or hyphens.";
        if (_exteriorChunk == null || _interiorChunk == null)
            return "Both the exterior and interior chunk must be set.";
        if (_exteriorChunk == _interiorChunk)
            return "The two chunks are the same asset. A portal into its own chunk destroys and " +
                   "re-instantiates the chunk the player is standing in. Use LocalTeleporter for a " +
                   "same-chunk hop.";
        if (_exteriorChunk.ChunkPrefab == null)
            return $"'{_exteriorChunk.name}' has no ChunkPrefab.";
        if (_interiorChunk.ChunkPrefab == null)
            return $"'{_interiorChunk.name}' has no ChunkPrefab.";
        if (string.IsNullOrEmpty(_exteriorChunk.ChunkName))
            return $"'{_exteriorChunk.name}' has an empty ChunkName — it is the save key and must be set.";
        if (string.IsNullOrEmpty(_interiorChunk.ChunkName))
            return $"'{_interiorChunk.name}' has an empty ChunkName — it is the save key and must be set.";

        if (PrefabStageUtility.GetCurrentPrefabStage() != null)
            return "Leave Prefab Mode first. Prefabs are edited in place while closed; doing that to one " +
                   "that is open would fight the stage's own copy.";

        if (_interactRange <= 0f)
            return "Interact Range must be greater than zero or the door can never be reached.";

        return null;
    }

    private static string FindDuplicateChunkName(MapChunkData chunk)
    {
        foreach (MapChunkData other in LocationLinkValidator.AllChunkAssets())
        {
            if (other == chunk || other.ChunkName != chunk.ChunkName) continue;
            return $"ChunkName '{chunk.ChunkName}' is used by both {chunk.name} and {other.name}. " +
                   "FindChunkByName returns the first match, so one of them is unreachable. Fix that " +
                   "before wiring a door — and note that renaming either orphans saves made inside it.";
        }
        return null;
    }

    private void CreateOrUpdateLinkedPair()
    {
        string blocker = WhyCannotCreate()
                         ?? FindDuplicateChunkName(_exteriorChunk)
                         ?? FindDuplicateChunkName(_interiorChunk);
        if (blocker != null)
        {
            Debug.LogWarning("PortalPlacementTool: " + blocker);
            return;
        }

        string outsideId = LocationLinks.OutsideMarkerId(_linkId);
        string insideId = LocationLinks.InsideMarkerId(_linkId);

        // Captured into locals so the closures below cannot be affected by the fields changing.
        string linkId = _linkId;
        float range = _interactRange;
        bool requireTutorial = _requireTutorialComplete;
        bool overwrite = _overwritePoses;

        MapChunkData interior = _interiorChunk;
        MapChunkData exterior = _exteriorChunk;

        var entrance = new PortalEnd
        {
            PortalObjectName = LocationLinks.PortalEnterName,
            PortalPos = _exteriorDoorPos,
            PortalEuler = _exteriorDoorEuler,
            MarkerId = outsideId,
            MarkerPos = _outsideMarkerPos,
            MarkerEuler = _outsideMarkerEuler,
            TargetChunk = interior,
            TargetMarkerId = insideId,
            Prompt = _enterPrompt,
        };
        var exit = new PortalEnd
        {
            PortalObjectName = LocationLinks.PortalExitName,
            PortalPos = _interiorDoorPos,
            PortalEuler = _interiorDoorEuler,
            MarkerId = insideId,
            MarkerPos = _insideMarkerPos,
            MarkerEuler = _insideMarkerEuler,
            TargetChunk = exterior,
            TargetMarkerId = outsideId,
            Prompt = _exitPrompt,
        };

        string error;
        if (!WritePrefab(exterior.ChunkPrefab,
                         root => ApplyEnd(root, linkId, entrance, overwrite, requireTutorial, range),
                         out error))
        {
            Debug.LogError($"PortalPlacementTool: could not write '{exterior.name}' — {error}. " +
                           "Nothing was changed in the interior either.");
            return;
        }

        if (!WritePrefab(interior.ChunkPrefab,
                         root => ApplyEnd(root, linkId, exit, overwrite, requireTutorial, range),
                         out error))
        {
            Debug.LogError($"PortalPlacementTool: the exterior end of '{linkId}' was written, but the " +
                           $"interior end failed — {error}. The pair is HALF DONE: '{exterior.ChunkName}' " +
                           $"now has a door into '{interior.ChunkName}' with no way back. Fix the cause " +
                           "and re-run before entering it.");
            return;
        }

        RegisterInRegistry(exterior, interior);
        AssetDatabase.SaveAssets();

        Debug.Log(
            $"PortalPlacementTool: linked '{linkId}'.\n" +
            $"  {exterior.ChunkName} / {LocationLinks.RootName}/{linkId}/{LocationLinks.PortalEnterName} " +
            $"→ {interior.ChunkName} [{insideId}]\n" +
            $"  {interior.ChunkName} / {LocationLinks.RootName}/{linkId}/{LocationLinks.PortalExitName} " +
            $"→ {exterior.ChunkName} [{outsideId}]\n" +
            "Both chunks are in MapChunkRegistry. Run Validate All Location Links to check the result.");

        _findings = LocationLinkValidator.Run();
    }

    private struct PortalEnd
    {
        public string PortalObjectName;
        public Vector3 PortalPos;
        public Vector3 PortalEuler;
        public string MarkerId;
        public Vector3 MarkerPos;
        public Vector3 MarkerEuler;
        public MapChunkData TargetChunk;
        public string TargetMarkerId;
        public string Prompt;
    }

    /// <summary>
    /// Writes one end of the link into an already-loaded prefab copy. Everything is found by name
    /// under LocationLinks/&lt;linkId&gt;/ and updated in place, which is what makes a re-run an
    /// update rather than a second door beside the first.
    /// </summary>
    private static void ApplyEnd(GameObject root, string linkId, PortalEnd end,
                                 bool overwritePoses, bool requireTutorial, float range)
    {
        Transform group = EnsureChild(EnsureChild(root.transform, LocationLinks.RootName), linkId);

        Transform portalT = EnsureChild(group, end.PortalObjectName);
        if (overwritePoses)
            SetRootRelative(root, portalT, end.PortalPos, end.PortalEuler);

        var portal = portalT.GetComponent<DungeonPortal>();
        if (portal == null) portal = portalT.gameObject.AddComponent<DungeonPortal>();
        portal.TargetChunk = end.TargetChunk;
        portal.TargetSpawnPointId = end.TargetMarkerId;
        portal.Prompt = end.Prompt;
        portal.RequireTutorialComplete = requireTutorial;
        // Left as whatever it was. The marker id above is what travel actually uses, and a stale
        // coordinate under it is harmless — but blanking it would throw away a fallback someone may
        // have set by hand on a portal that predates markers.

        var interactable = portalT.GetComponent<Interactable>();
        if (interactable == null) interactable = portalT.gameObject.AddComponent<Interactable>();
        interactable.Prompt = end.Prompt;
        interactable.InteractRange = range;
        interactable.Reusable = true;
        // ⚠ OnInteract is deliberately NOT wired here. DungeonPortal.Awake adds its own listener at
        // runtime, and a persistent editor-time call would sit alongside it — one press, two
        // journeys. UnityEventTools is the only way to write a persistent call, so simply not
        // calling it is enough; AddListener would not survive the prefab save anyway.

        Transform markerT = EnsureChild(group, LocationLinks.MarkerObjectName(end.MarkerId));
        if (overwritePoses)
            SetRootRelative(root, markerT, end.MarkerPos, end.MarkerEuler);

        var marker = markerT.GetComponent<PlayerSpawnPoint>();
        if (marker == null) marker = markerT.gameObject.AddComponent<PlayerSpawnPoint>();
        marker.Id = end.MarkerId;
    }

    private static Transform EnsureChild(Transform parent, string name)
    {
        Transform existing = parent.Find(name);
        if (existing != null) return existing;

        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        return go.transform;
    }

    /// <summary>
    /// Places a child at a pose expressed relative to the prefab root, whatever the intermediate
    /// group transforms happen to be. The groups are created at identity, but a designer moving one
    /// later must not silently shift every door under it.
    /// </summary>
    private static void SetRootRelative(GameObject root, Transform t, Vector3 pos, Vector3 euler)
    {
        t.position = root.transform.TransformPoint(pos);
        t.rotation = root.transform.rotation * Quaternion.Euler(euler);
    }

    /// <summary>
    /// The in-place prefab edit from CLAUDE.md §3: load contents, mutate, save back over the same
    /// path, unload. Never delete-and-recreate — that takes the .meta with it and mints a fresh
    /// GUID, orphaning every instance already placed.
    /// </summary>
    private static bool WritePrefab(GameObject prefabRootAsset, System.Action<GameObject> mutate, out string error)
    {
        error = null;

        string path = AssetDatabase.GetAssetPath(prefabRootAsset);
        if (string.IsNullOrEmpty(path))
        {
            error = "ChunkPrefab is not a saved prefab asset.";
            return false;
        }
        if (prefabRootAsset.transform.parent != null)
        {
            error = $"ChunkPrefab points at '{prefabRootAsset.name}', which is a child inside {path}, " +
                    "not the prefab root. Re-assign it to the root object.";
            return false;
        }

        GameObject contents = PrefabUtility.LoadPrefabContents(path);
        if (contents == null)
        {
            error = $"Could not open {path} for editing.";
            return false;
        }

        try
        {
            mutate(contents);
            PrefabUtility.SaveAsPrefabAsset(contents, path);
        }
        catch (System.Exception e)
        {
            error = e.Message;
            return false;
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(contents);
        }

        return true;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  REGISTRATION
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void RegisterInRegistry(params MapChunkData[] chunks)
    {
        MapChunkRegistry registry = LoadOrCreateRegistry();
        if (registry == null) return;

        if (registry.Chunks == null) registry.Chunks = new List<MapChunkData>();

        bool changed = false;
        foreach (MapChunkData chunk in chunks)
        {
            if (chunk == null || registry.Chunks.Contains(chunk)) continue;
            registry.Chunks.Add(chunk);
            changed = true;
        }

        if (changed) EditorUtility.SetDirty(registry);
    }

    private static MapChunkRegistry LoadOrCreateRegistry()
    {
        var registry = AssetDatabase.LoadAssetAtPath<MapChunkRegistry>(LocationLinks.RegistryAssetPath);
        if (registry != null) return registry;

        if (!AssetDatabase.IsValidFolder("Assets/Resources"))
            AssetDatabase.CreateFolder("Assets", "Resources");

        registry = ScriptableObject.CreateInstance<MapChunkRegistry>();
        AssetDatabase.CreateAsset(registry, LocationLinks.RegistryAssetPath);
        Debug.Log($"PortalPlacementTool: created {LocationLinks.RegistryAssetPath}.");
        return registry;
    }

    /// <summary>
    /// Adds both chunks to the open scene's ChunkManager.AllChunks as well. Not required — the
    /// registry covers loading — but AllChunks is consulted first and keeping the scene list honest
    /// makes what the game can reach visible in the Inspector.
    /// </summary>
    private void RegisterWithChunkManager()
    {
        var mgr = FindObjectOfType<ChunkManager>();
        if (mgr == null)
        {
            Debug.LogWarning("PortalPlacementTool: no ChunkManager in the open scene (are you in Prefab " +
                             "Mode? Do this from c.unity).");
            return;
        }

        Undo.RecordObject(mgr, "Register Chunks");
        int added = 0;
        foreach (MapChunkData chunk in new[] { _exteriorChunk, _interiorChunk })
        {
            if (chunk == null) continue;

            bool present = false;
            if (mgr.AllChunks != null)
            {
                foreach (MapChunkData c in mgr.AllChunks)
                    if (c == chunk) { present = true; break; }
            }
            if (present) continue;

            int oldLen = mgr.AllChunks != null ? mgr.AllChunks.Length : 0;
            var grown = new MapChunkData[oldLen + 1];
            if (oldLen > 0) System.Array.Copy(mgr.AllChunks, grown, oldLen);
            grown[oldLen] = chunk;
            mgr.AllChunks = grown;
            added++;
        }

        if (added == 0)
        {
            Debug.Log("PortalPlacementTool: both chunks were already registered with the scene ChunkManager.");
            return;
        }

        EditorUtility.SetDirty(mgr);
        EditorSceneManager.MarkSceneDirty(mgr.gameObject.scene);
        Debug.Log($"PortalPlacementTool: added {added} chunk(s) to the scene ChunkManager. Ctrl+S to save c.unity.");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  INTERIOR BUNDLE
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void CreateInteriorBundle()
    {
        string name = _newInteriorName.Trim();
        if (string.IsNullOrEmpty(name))
        {
            Debug.LogWarning("PortalPlacementTool: give the interior a name first.");
            return;
        }

        string prefabPath = $"Assets/Prefabs/Chunks/{name}_Prefab.prefab";
        string dataPath = $"Assets/Data/Chunks/{name}_Data.asset";

        if (AssetDatabase.LoadAssetAtPath<Object>(prefabPath) != null)
        {
            Debug.LogWarning($"PortalPlacementTool: {prefabPath} already exists. Nothing was overwritten.");
            return;
        }
        if (AssetDatabase.LoadAssetAtPath<Object>(dataPath) != null)
        {
            Debug.LogWarning($"PortalPlacementTool: {dataPath} already exists. Nothing was overwritten.");
            return;
        }
        foreach (MapChunkData other in LocationLinkValidator.AllChunkAssets())
        {
            if (other.ChunkName != name) continue;
            Debug.LogWarning($"PortalPlacementTool: ChunkName '{name}' is already used by {other.name}. " +
                             "Chunk names are save keys and must be unique — pick another.");
            return;
        }

        var temp = new GameObject($"{name}_Prefab");
        GameObject prefab;
        try
        {
            prefab = PrefabUtility.SaveAsPrefabAsset(temp, prefabPath);
        }
        finally
        {
            Object.DestroyImmediate(temp);
        }

        if (prefab == null)
        {
            Debug.LogError($"PortalPlacementTool: failed to create {prefabPath}.");
            return;
        }

        var data = ScriptableObject.CreateInstance<MapChunkData>();
        data.ChunkName = name;
        data.ChunkPrefab = prefab;
        AssetDatabase.CreateAsset(data, dataPath);

        RegisterInRegistry(data);
        AssetDatabase.SaveAssets();

        _interiorChunk = data;
        Selection.activeObject = prefab;

        Debug.Log($"PortalPlacementTool: created {dataPath} and {prefabPath}, and registered the chunk.\n" +
                  "It is EMPTY — open the prefab and give it a floor with a collider, walls, and a " +
                  "RuntimeNavMeshBaker if anything in it will use a NavMeshAgent. Do not add ChunkEdge " +
                  "triggers: an interior has no grid neighbours.");
    }
}
