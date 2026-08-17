using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using GBHEngland.Data;
using GBHEngland.Vibe;
using GBHEngland.World;

/// <summary>
/// Attaches a <see cref="WorldContainer"/> to an existing 3D object — a berry bush, a broken
/// vending machine, a heap of bus wreckage — as a child placed where the player should interact.
///
/// Why a child and not the model itself: the interaction point is rarely the model's origin. A
/// vending machine wants its slot, a bush wants the side you can reach. Keeping the container on a
/// child also means the model can be swapped, re-imported or moved without taking the container's
/// authored fields with it.
///
/// Typical run:
///   1. Open the chunk prefab in Prefab Mode and select the model in the Hierarchy.
///   2. Set the loot, the mode and the prompt in this window.
///   3. Press Pick Interaction Point, then click the spot on the model in the Scene view.
///      Hold Shift while clicking to stay armed and do a run of several objects.
///   4. Press Create Or Update Container, then Ctrl+S.
///
/// Re-running against an object that already has one loads its settings and edits in place rather
/// than adding a second — two containers on one model would be two save keys for one thing the
/// player sees.
/// </summary>
public class ContainerPlacementTool : EditorWindow
{
    // Every authoring field is [SerializeField] for the reason PortalPlacementTool records: an
    // EditorWindow is a ScriptableObject, so marked fields survive a domain reload. Losing a
    // half-configured container to a stray recompile is what stops a tool getting used.

    // ── Identity ────────────────────────────────────────────────────────────────────────────
    [SerializeField] private string _containerName = "Wreckage";
    [SerializeField] private string _interactPrompt = "Search wreckage";
    [SerializeField] private string _saveId = "";

    // ── Behaviour ───────────────────────────────────────────────────────────────────────────
    [SerializeField] private WorldContainer.ContainerMode _mode = WorldContainer.ContainerMode.Fixed;
    [SerializeField] private int _respawnVisits = EKVibe.DefaultContainerRespawnVisits;
    [SerializeField] private float _interactRange = EKVibe.DefaultContainerInteractRange;

    // ── Loot ────────────────────────────────────────────────────────────────────────────────
    [SerializeField] private LootBand _band;
    [SerializeField] private List<LootDrop> _fixedLoot = new List<LootDrop>();

    // ── Visuals ─────────────────────────────────────────────────────────────────────────────
    [SerializeField] private GameObject _fullVisual;
    [SerializeField] private GameObject _emptyVisual;

    // ── Interaction point, as a local offset from the target ────────────────────────────────
    [SerializeField] private Vector3 _localOffset = Vector3.zero;
    [SerializeField] private bool _hasPoint;

    // ── Scene-view arming ───────────────────────────────────────────────────────────────────
    private bool _armed;
    private Vector3 _hoverPoint;
    private bool _hoverValid;

    // ── Report ──────────────────────────────────────────────────────────────────────────────
    private List<string> _findings;
    private Vector2 _reportScroll;
    private Vector2 _windowScroll;
    private bool _showBackPocket;

    /// <summary>The name every container child is given, so re-runs can find their own output.</summary>
    private const string ChildName = "Container";

    private const float GroundPlaneY = 0f;

    [MenuItem("Tools/Place/Container Placement")]
    public static void Open()
    {
        GetWindow<ContainerPlacementTool>("Container Placement");
    }

    private void OnEnable()
    {
        SceneView.duringSceneGui += OnSceneGUI;
        Selection.selectionChanged += OnSelectionChanged;
    }

    private void OnDisable()
    {
        SceneView.duringSceneGui -= OnSceneGUI;
        Selection.selectionChanged -= OnSelectionChanged;
    }

    private void OnSelectionChanged()
    {
        Repaint();
    }

    // ════════════════════════════════════════════════════════════════════════════════════════
    // Window
    // ════════════════════════════════════════════════════════════════════════════════════════

    private void OnGUI()
    {
        _windowScroll = EditorGUILayout.BeginScrollView(_windowScroll);

        EditorGUILayout.HelpBox(
            "Attaches a searchable container to an existing 3D object, as a child at the point " +
            "you click. Select the model in the Hierarchy first.\n\n" +
            "Containers are authored INSIDE a chunk prefab — chunks are instantiated from their " +
            "prefabs at runtime, so a container placed loose in the scene is not in the world.",
            MessageType.Info);

        GameObject target = Selection.activeGameObject;
        WorldContainer existing = FindExistingContainer(target);

        DrawTargetPanel(target, existing);

        if (target == null)
        {
            EditorGUILayout.EndScrollView();
            return;
        }

        EditorGUILayout.Space();
        DrawConfigPanel(target);
        EditorGUILayout.Space();
        DrawBackPocketPanel();
        EditorGUILayout.Space();
        DrawPointPanel(target);
        EditorGUILayout.Space();
        DrawActionsPanel(target, existing);
        EditorGUILayout.Space();
        DrawReportPanel();

        EditorGUILayout.EndScrollView();
    }

    private void DrawTargetPanel(GameObject target, WorldContainer existing)
    {
        EditorGUILayout.LabelField("Target", EditorStyles.boldLabel);

        if (target == null)
        {
            EditorGUILayout.HelpBox(
                "Nothing selected. Select the 3D object in the Hierarchy that should carry the " +
                "container.", MessageType.Warning);
            return;
        }

        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage != null)
        {
            if (!target.transform.IsChildOf(stage.prefabContentsRoot.transform))
            {
                EditorGUILayout.HelpBox(
                    $"'{target.name}' is not inside the prefab currently open in Prefab Mode. " +
                    "Select something inside it, or close Prefab Mode.", MessageType.Warning);
                return;
            }
            EditorGUILayout.LabelField("Selected", $"{target.name}  (in {stage.prefabContentsRoot.name})");
        }
        else
        {
            EditorGUILayout.LabelField("Selected", target.name);
            EditorGUILayout.HelpBox(
                "Not in Prefab Mode. A container placed in the open scene will not appear in the " +
                "world — chunks are instantiated from their prefabs at runtime. Open the chunk " +
                "prefab first unless you know why you are doing this.", MessageType.Warning);
        }

        if (existing != null)
        {
            EditorGUILayout.HelpBox(
                "This object already has a container. Its settings are loaded below — pressing " +
                "Create Or Update edits it in place rather than adding a second.",
                MessageType.None);
        }
    }

    private void DrawConfigPanel(GameObject target)
    {
        EditorGUILayout.LabelField("Container", EditorStyles.boldLabel);

        _containerName = EditorGUILayout.TextField(
            new GUIContent("Name", "The loot menu's title."), _containerName);
        _interactPrompt = EditorGUILayout.TextField(
            new GUIContent("Prompt", "What the USE button says. Blank falls back to \"Search <name>\"."),
            _interactPrompt);
        _saveId = EditorGUILayout.TextField(
            new GUIContent("Save Id",
                "Unique within the chunk. Part of the save key — changing it after a container " +
                "has been looted refills it for every existing save. Leave blank and Create will " +
                "generate one."),
            _saveId);

        _mode = (WorldContainer.ContainerMode)EditorGUILayout.EnumPopup(
            new GUIContent("Mode",
                "Fixed empties permanently. Respawning restocks after a number of visits."), _mode);

        if (_mode == WorldContainer.ContainerMode.Respawning)
        {
            _respawnVisits = EditorGUILayout.IntField(
                new GUIContent("Respawn Visits",
                    "Visits to this chunk before it restocks. 3 means available again on the " +
                    "third return; 1 refills every visit."),
                _respawnVisits);
            if (_respawnVisits < 1)
            {
                EditorGUILayout.HelpBox(
                    $"Zero or less falls back to the default ({EKVibe.DefaultContainerRespawnVisits}).",
                    MessageType.Warning);
            }
        }

        _interactRange = EditorGUILayout.FloatField(
            new GUIContent("Interact Range", "How close the player has to be, in metres."),
            _interactRange);

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Loot — one or the other, not both", EditorStyles.boldLabel);

        _band = (LootBand)EditorGUILayout.ObjectField(
            new GUIContent("Loot Band", "Weighted random table. Wins if a fixed list is also set."),
            _band, typeof(LootBand), false);

        var so = new SerializedObject(this);
        EditorGUILayout.PropertyField(
            so.FindProperty(nameof(_fixedLoot)),
            new GUIContent("Fixed Loot",
                "Exact items in exact quantities. Use this for anything a quest depends on — a " +
                "band that can roll nothing cannot promise the player the item."),
            true);
        so.ApplyModifiedProperties();

        bool hasFixed = _fixedLoot != null && _fixedLoot.Count > 0;
        if (_band != null && hasFixed)
        {
            EditorGUILayout.HelpBox(
                "Both are set. At runtime the band wins and the fixed list is ignored. Clear one.",
                MessageType.Error);
        }
        else if (_band == null && !hasFixed)
        {
            EditorGUILayout.HelpBox(
                "No loot source. The container will open onto nothing and retire immediately.",
                MessageType.Warning);
        }

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("Visuals — optional", EditorStyles.boldLabel);
        EditorGUILayout.LabelField(
            "Two child objects of the model: the full version and the picked-clean version.",
            EditorStyles.miniLabel);

        _fullVisual = (GameObject)EditorGUILayout.ObjectField(
            new GUIContent("Full Visual", "Shown while there is something left."),
            _fullVisual, typeof(GameObject), true);
        _emptyVisual = (GameObject)EditorGUILayout.ObjectField(
            new GUIContent("Empty Visual", "Shown once emptied."),
            _emptyVisual, typeof(GameObject), true);

        string visualProblem = DescribeVisualProblem(target);
        if (visualProblem != null) EditorGUILayout.HelpBox(visualProblem, MessageType.Error);
    }

    private void DrawBackPocketPanel()
    {
        _showBackPocket = EditorGUILayout.Foldout(_showBackPocket, "Traps and locks", true);
        if (!_showBackPocket) return;

        EditorGUILayout.HelpBox(
            "NOT WIRED. These fields exist on the component so their enum indices are settled " +
            "early, but nothing reads them — a container marked Locked is not locked, and a trap " +
            "does not fire. Set them on the component directly once the behaviour lands.",
            MessageType.Warning);
    }

    private void DrawPointPanel(GameObject target)
    {
        EditorGUILayout.LabelField("Interaction point", EditorStyles.boldLabel);

        EditorGUILayout.LabelField("Local offset", _hasPoint ? _localOffset.ToString("F2") : "not picked");

        using (new EditorGUI.DisabledScope(target == null))
        {
            if (!_armed)
            {
                if (GUILayout.Button("Pick Interaction Point"))
                {
                    _armed = true;
                    SceneView.RepaintAll();
                }
            }
            else
            {
                EditorGUILayout.HelpBox(
                    "Click the spot on the model in the Scene view. Hold Shift to stay armed for " +
                    "a run of several objects. Esc cancels.", MessageType.Info);
                if (GUILayout.Button("Cancel")) Disarm();
            }
        }

        if (GUILayout.Button("Use Object Origin"))
        {
            _localOffset = Vector3.zero;
            _hasPoint = true;
        }
    }

    private void DrawActionsPanel(GameObject target, WorldContainer existing)
    {
        EditorGUILayout.LabelField("Actions", EditorStyles.boldLabel);

        if (existing != null && GUILayout.Button("Load Settings From Existing"))
            LoadFrom(existing);

        using (new EditorGUI.DisabledScope(target == null))
        {
            if (GUILayout.Button(existing != null ? "Update Container" : "Create Container",
                                 GUILayout.Height(28)))
            {
                CreateOrUpdate(target);
            }
        }

        if (GUILayout.Button("Validate All Containers")) Validate();
    }

    private void DrawReportPanel()
    {
        if (_findings == null) return;

        EditorGUILayout.LabelField("Report", EditorStyles.boldLabel);

        if (_findings.Count == 0)
        {
            EditorGUILayout.HelpBox(
                "No problems found in what is currently open.\n\n" +
                "⚠ This only sees the open prefab or scene. It cannot tell you whether a save id " +
                "here collides with one in a different chunk prefab.", MessageType.Info);
            return;
        }

        _reportScroll = EditorGUILayout.BeginScrollView(_reportScroll, GUILayout.Height(160));
        foreach (string finding in _findings) EditorGUILayout.LabelField("• " + finding, EditorStyles.wordWrappedLabel);
        EditorGUILayout.EndScrollView();
    }

    // ════════════════════════════════════════════════════════════════════════════════════════
    // Scene view
    // ════════════════════════════════════════════════════════════════════════════════════════

    private void OnSceneGUI(SceneView view)
    {
        if (!_armed) return;

        Event e = Event.current;

        // Takes the default control so a click places instead of selecting whatever is under the
        // cursor. Without this the first click just picks the model.
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

        if (e.type == EventType.Repaint && _hoverValid) DrawGhost(_hoverPoint);

        if (e.type == EventType.MouseDown && e.button == 0 && !e.alt)
        {
            if (TryGetPoint(e.mousePosition, out Vector3 point))
            {
                GameObject target = Selection.activeGameObject;
                if (target != null)
                {
                    _localOffset = target.transform.InverseTransformPoint(point);
                    _hasPoint = true;

                    // Shift is stamp mode: place it now and stay armed, so a run of objects can be
                    // done without returning to the window between each.
                    if (e.shift) CreateOrUpdate(target);
                    else _armed = false;

                    Repaint();
                }
            }
            e.Use();
        }
    }

    private void Disarm()
    {
        _armed = false;
        _hoverValid = false;
        SceneView.RepaintAll();
        Repaint();
    }

    private static void DrawGhost(Vector3 point)
    {
        Handles.color = new Color(1f, 0.75f, 0.25f, 0.9f);
        Handles.DrawWireDisc(point, Vector3.up, 0.4f);
        Handles.DrawWireDisc(point, Vector3.up, 0.12f);
        Handles.DrawLine(point, point + Vector3.up * 0.8f);
    }

    /// <summary>
    /// Where the cursor is pointing. Prefers real geometry so the point lands on the model, and
    /// falls back to the ground plane.
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

    // ════════════════════════════════════════════════════════════════════════════════════════
    // Create / update
    // ════════════════════════════════════════════════════════════════════════════════════════

    private void CreateOrUpdate(GameObject target)
    {
        if (target == null) return;

        WorldContainer container = FindExistingContainer(target);

        if (container == null)
        {
            var child = new GameObject(ChildName);
            Undo.RegisterCreatedObjectUndo(child, "Create Container");
            Undo.SetTransformParent(child.transform, target.transform, "Create Container");
            child.transform.localRotation = Quaternion.identity;
            child.transform.localScale = Vector3.one;

            container = Undo.AddComponent<WorldContainer>(child);
            Undo.AddComponent<Interactable>(child);
        }

        Undo.RecordObject(container, "Configure Container");
        Undo.RecordObject(container.transform, "Configure Container");

        container.transform.localPosition = _hasPoint ? _localOffset : Vector3.zero;

        container.ContainerName = _containerName;
        container.InteractPrompt = _interactPrompt;
        container.Mode = _mode;
        container.RespawnVisits = _respawnVisits;
        container.InteractRange = _interactRange;
        container.Band = _band;
        container.FixedLoot = new List<LootDrop>(_fixedLoot ?? new List<LootDrop>());
        container.FullVisual = _fullVisual;
        container.EmptyVisual = _emptyVisual;

        // The save id is the one field that must never silently collide, so it is generated rather
        // than left to the GameObject name — every container child is called "Container".
        container.SaveId = ResolveSaveId(container, target);

        var interactable = container.GetComponent<Interactable>();
        if (interactable != null)
        {
            Undo.RecordObject(interactable, "Configure Container");
            interactable.Prompt = !string.IsNullOrEmpty(_interactPrompt)
                ? _interactPrompt
                : $"Search {_containerName}";
            interactable.InteractRange = _interactRange;
            interactable.Reusable = true;
            EditorUtility.SetDirty(interactable);
        }

        EditorUtility.SetDirty(container);
        MarkSceneDirty(container.gameObject);

        Debug.Log($"Container Placement: '{container.SaveId}' on '{target.name}'. " +
                  "Ctrl+S to save the prefab.", container);
    }

    /// <summary>
    /// Keeps an already-authored id, and otherwise mints one that no other container in scope is
    /// using. Uniqueness is checked against SpriteContainer too — the two components write into the
    /// same LootedContainers list, and no runtime warning sees across them.
    /// </summary>
    private string ResolveSaveId(WorldContainer container, GameObject target)
    {
        HashSet<string> taken = CollectSaveIds(container);

        if (!string.IsNullOrEmpty(_saveId) && !taken.Contains(_saveId)) return _saveId;
        if (!string.IsNullOrEmpty(container.SaveId) && !taken.Contains(container.SaveId))
            return container.SaveId;

        string root = Sanitize(target.name) + "_container";
        if (!taken.Contains(root)) return root;

        for (int i = 2; i < 1000; i++)
        {
            string candidate = root + "_" + i;
            if (!taken.Contains(candidate)) return candidate;
        }
        return root + "_" + System.Guid.NewGuid().ToString("N").Substring(0, 6);
    }

    private static string Sanitize(string raw)
    {
        if (string.IsNullOrEmpty(raw)) return "container";
        var sb = new System.Text.StringBuilder(raw.Length);
        foreach (char c in raw)
            sb.Append(char.IsLetterOrDigit(c) ? char.ToLowerInvariant(c) : '_');
        return sb.ToString().Trim('_');
    }

    /// <summary>Every save id already in use in the open prefab or scene, excluding one container.</summary>
    private static HashSet<string> CollectSaveIds(WorldContainer exclude)
    {
        var taken = new HashSet<string>();

        foreach (WorldContainer c in FindAllInScope<WorldContainer>())
        {
            if (c == exclude) continue;
            string id = !string.IsNullOrEmpty(c.SaveId) ? c.SaveId : c.gameObject.name;
            if (!string.IsNullOrEmpty(id)) taken.Add(id);
        }

        // SpriteContainer keys on its GameObject name and shares the save-key space.
        foreach (SpriteContainer s in FindAllInScope<SpriteContainer>())
            taken.Add(s.gameObject.name);

        return taken;
    }

    private void LoadFrom(WorldContainer container)
    {
        _containerName = container.ContainerName;
        _interactPrompt = container.InteractPrompt;
        _saveId = container.SaveId;
        _mode = container.Mode;
        _respawnVisits = container.RespawnVisits;
        _interactRange = container.InteractRange;
        _band = container.Band;
        _fixedLoot = new List<LootDrop>(container.FixedLoot ?? new List<LootDrop>());
        _fullVisual = container.FullVisual;
        _emptyVisual = container.EmptyVisual;
        _localOffset = container.transform.localPosition;
        _hasPoint = true;
        Repaint();
    }

    private static WorldContainer FindExistingContainer(GameObject target)
    {
        if (target == null) return null;

        WorldContainer own = target.GetComponent<WorldContainer>();
        if (own != null) return own;

        foreach (Transform child in target.transform)
        {
            WorldContainer c = child.GetComponent<WorldContainer>();
            if (c != null) return c;
        }
        return null;
    }

    // ════════════════════════════════════════════════════════════════════════════════════════
    // Validation
    // ════════════════════════════════════════════════════════════════════════════════════════

    private void Validate()
    {
        _findings = new List<string>();

        var byId = new Dictionary<string, List<string>>();
        List<WorldContainer> containers = FindAllInScope<WorldContainer>();

        foreach (WorldContainer c in containers)
        {
            string path = PathOf(c.transform);
            string id = !string.IsNullOrEmpty(c.SaveId) ? c.SaveId : c.gameObject.name;

            if (!byId.TryGetValue(id, out var owners)) byId[id] = owners = new List<string>();
            owners.Add(path);

            if (string.IsNullOrEmpty(c.SaveId))
            {
                _findings.Add(
                    $"{path}: no Save Id, so it falls back to the GameObject name '{c.gameObject.name}'. " +
                    "Every container child is called Container, so this is very likely to collide.");
            }

            bool hasFixed = c.FixedLoot != null && c.FixedLoot.Count > 0;
            if (c.Band != null && hasFixed)
                _findings.Add($"{path}: both a Loot Band and a Fixed Loot list are set — the band wins.");
            else if (c.Band == null && !hasFixed)
                _findings.Add($"{path}: no loot source. It opens onto nothing and retires immediately.");

            if (c.Band != null && TotalWeight(c.Band) <= 0)
                _findings.Add($"{path}: band '{c.Band.name}' has no positive weights, so it can only roll nothing.");

            if (hasFixed)
            {
                for (int i = 0; i < c.FixedLoot.Count; i++)
                {
                    LootDrop drop = c.FixedLoot[i];
                    if (drop == null || drop.Item == null)
                        _findings.Add($"{path}: fixed loot entry {i} has no item.");
                    else if (drop.Quantity <= 0)
                        _findings.Add($"{path}: fixed loot '{drop.Item.name}' has a quantity of {drop.Quantity}.");
                }
            }

            if (c.Mode == WorldContainer.ContainerMode.Respawning && c.RespawnVisits <= 0)
            {
                _findings.Add(
                    $"{path}: Respawning with {c.RespawnVisits} visits — falls back to the default " +
                    $"({EKVibe.DefaultContainerRespawnVisits}).");
            }

            if (c.InteractRange <= 0f)
                _findings.Add($"{path}: interact range is {c.InteractRange}, so it can never be reached.");

            if (c.GetComponent<Interactable>() == null)
                _findings.Add($"{path}: no Interactable component. One is added at runtime, but the prompt will not be previewable.");

            CheckVisual(c, c.FullVisual, "Full Visual", path);
            CheckVisual(c, c.EmptyVisual, "Empty Visual", path);

            if (c.FullVisual == null && c.EmptyVisual == null)
                _findings.Add($"{path}: no visual swap set — the model will look the same emptied. Fine if deliberate.");

            if (c.Trap != WorldContainer.TrapType.None || c.TrapChance > 0f || c.Locked ||
                c.QuestGate != QuestGateType.None)
            {
                _findings.Add($"{path}: a trap/lock/quest-gate field is set, and NONE of them are wired yet. It will behave as an ordinary open container.");
            }
        }

        foreach (var pair in byId)
        {
            if (pair.Value.Count > 1)
            {
                _findings.Insert(0,
                    $"DUPLICATE save id '{pair.Key}' on {pair.Value.Count} containers: " +
                    string.Join(", ", pair.Value) + " — looting one empties all of them.");
            }
        }

        // SpriteContainer shares the key space, so a WorldContainer id equal to a SpriteContainer's
        // GameObject name is the same collision with none of the same symptoms in either component.
        foreach (SpriteContainer s in FindAllInScope<SpriteContainer>())
        {
            if (byId.ContainsKey(s.gameObject.name))
            {
                _findings.Insert(0,
                    $"DUPLICATE across components: SpriteContainer '{PathOf(s.transform)}' keys on " +
                    $"'{s.gameObject.name}', which a WorldContainer also uses as its Save Id.");
            }
        }

        Debug.Log($"Container Placement: validated {containers.Count} container(s), {_findings.Count} finding(s).");
        Repaint();
    }

    private void CheckVisual(WorldContainer c, GameObject visual, string label, string path)
    {
        if (visual == null) return;

        if (visual == c.gameObject || c.transform.IsChildOf(visual.transform))
        {
            _findings.Add(
                $"{path}: {label} points at the container or one of its ancestors. Hiding it would " +
                "disable the container itself — the component refuses this at runtime.");
        }
    }

    private static int TotalWeight(LootBand band)
    {
        int total = Mathf.Max(0, band.EmptyWeight);
        if (band.Entries != null)
        {
            foreach (LootBandEntry entry in band.Entries)
                if (entry != null && entry.Weight > 0) total += entry.Weight;
        }
        return total;
    }

    // ════════════════════════════════════════════════════════════════════════════════════════
    // Scope helpers
    // ════════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// Every component of a type in the prefab currently open in Prefab Mode, or in the active
    /// scene when there is none. Includes inactive objects — a container hidden under a disabled
    /// parent still owns its save id.
    /// </summary>
    private static List<T> FindAllInScope<T>() where T : Component
    {
        var found = new List<T>();

        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage != null)
        {
            found.AddRange(stage.prefabContentsRoot.GetComponentsInChildren<T>(true));
            return found;
        }

        Scene scene = SceneManager.GetActiveScene();
        if (!scene.IsValid()) return found;

        foreach (GameObject root in scene.GetRootGameObjects())
            found.AddRange(root.GetComponentsInChildren<T>(true));

        return found;
    }

    private string DescribeVisualProblem(GameObject target)
    {
        if (target == null) return null;

        if (_fullVisual != null && IsUnsafeVisual(_fullVisual, target))
            return "Full Visual points at the target or one of its ancestors. Hiding it would take the container with it.";
        if (_emptyVisual != null && IsUnsafeVisual(_emptyVisual, target))
            return "Empty Visual points at the target or one of its ancestors. Hiding it would take the container with it.";

        return null;
    }

    private static bool IsUnsafeVisual(GameObject visual, GameObject target)
    {
        return visual == target || target.transform.IsChildOf(visual.transform);
    }

    private static string PathOf(Transform t)
    {
        string path = t.name;
        Transform cursor = t.parent;
        while (cursor != null)
        {
            path = cursor.name + "/" + path;
            cursor = cursor.parent;
        }
        return path;
    }

    private static void MarkSceneDirty(GameObject go)
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        if (stage != null) EditorSceneManager.MarkSceneDirty(stage.scene);
        else EditorSceneManager.MarkSceneDirty(go.scene);
    }
}
