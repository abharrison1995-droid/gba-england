using UnityEngine;
using UnityEditor;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;
using ExiledAlvaston.Quests;
using ExiledAlvaston.Vibe;
using ExiledAlvaston.Systems;

/// <summary>
/// Boots Discover England: Title + Creator UI, Manor Cellars chunk, London link, GameFlow wiring.
/// </summary>
public static class DiscoverEnglandSetup
{
    const string DataFolder = "Assets/Data/Chunks";
    const string PrefabFolder = "Assets/Prefabs/Chunks";

    [MenuItem("Tools/Exiled Alvaston/Setup (one-time)/Discover England Bootstrap (rebuilds scene + prefabs!)")]
    public static void SetupAll()
    {
        string manorPrefabPath = PrefabFolder + "/Manor_Cellars_Prefab.prefab";
        bool manorExists = AssetDatabase.LoadAssetAtPath<GameObject>(manorPrefabPath) != null;
        if (manorExists)
        {
            bool proceed = EditorUtility.DisplayDialog(
                "Rebuild Manor Cellars + Flow UI?",
                "Manor_Cellars_Prefab.prefab already exists. Running this will unconditionally rebuild it " +
                "from scratch — destroying any NPCs/enemies/chests/markers hand-placed into it since it was " +
                "last generated — and will also destroy and rebuild the Title/Character-Creator UI and " +
                "GameFlowController in the open scene.\n\n" +
                "This does NOT touch Home_Alvaston_Prefab (where Mosley/the Neek Box live) — only Manor " +
                "Cellars and the flow UI are affected.\n\nContinue?",
                "Yes, rebuild",
                "Cancel");
            if (!proceed) return;
        }

        EnsureFolders();

        MapChunkData london = EnsureLondonData();
        MapChunkData manor = EnsureManorCellars(london);
        LinkChunks(london, manor);

        EnsureManorEntranceOnLondonPrefab();
        BuildFlowUiAndController(london, manor);
        EnsureQuestTrackerOnHud();
        // NOTE: not calling FixPinkGrounds.FixAll() here — it would overwrite the custom
        // ground/path materials already set up on Home_Alvaston. Only run that tool manually
        // if a ground actually shows up pink/broken.

        Debug.Log("Discover England ready: Title → Creator → Manor Cellars quest → London gates door (re-enter). Enter Play Mode.");
    }

    private static void EnsureFolders()
    {
        if (!AssetDatabase.IsValidFolder("Assets/Data")) AssetDatabase.CreateFolder("Assets", "Data");
        if (!AssetDatabase.IsValidFolder(DataFolder)) AssetDatabase.CreateFolder("Assets/Data", "Chunks");
        if (!AssetDatabase.IsValidFolder("Assets/Prefabs")) AssetDatabase.CreateFolder("Assets", "Prefabs");
        if (!AssetDatabase.IsValidFolder(PrefabFolder)) AssetDatabase.CreateFolder("Assets/Prefabs", "Chunks");
    }

    private static MapChunkData EnsureLondonData()
    {
        string path = DataFolder + "/Home_Alvaston_Data.asset";
        MapChunkData london = AssetDatabase.LoadAssetAtPath<MapChunkData>(path);
        if (london == null)
        {
            Debug.LogError("Home_Alvaston_Data.asset missing — run chunk skeleton first or create London data.");
            return null;
        }

        // Keep ChunkName as "Home_Alvaston" — SaveGameManager/DeathScreenUI look chunks up by
        // this exact name. "London" is used as display-only flavor text elsewhere (UI labels).
        london.IsCity = true;
        london.IsTutorialDungeon = false;
        london.LockExitsUntilTutorialComplete = false;
        EditorUtility.SetDirty(london);
        return london;
    }

    private static MapChunkData EnsureManorCellars(MapChunkData london)
    {
        string dataPath = DataFolder + "/Manor_Cellars_Data.asset";
        MapChunkData manor = AssetDatabase.LoadAssetAtPath<MapChunkData>(dataPath);
        if (manor == null)
        {
            manor = ScriptableObject.CreateInstance<MapChunkData>();
            AssetDatabase.CreateAsset(manor, dataPath);
        }

        manor.ChunkName = "Manor Cellars";
        manor.Coordinates = new Vector2IntCoords(-1, 0);
        manor.IsCity = false;
        manor.IsTutorialDungeon = true;
        manor.LockExitsUntilTutorialComplete = true;
        manor.EastChunk = london;

        GameObject prefabRoot = BuildManorCellarsPrefab();
        string prefabPath = PrefabFolder + "/Manor_Cellars_Prefab.prefab";
        GameObject prefab = PrefabUtility.SaveAsPrefabAsset(prefabRoot, prefabPath);
        Object.DestroyImmediate(prefabRoot);
        manor.ChunkPrefab = prefab;

        EditorUtility.SetDirty(manor);
        return manor;
    }

    private static void LinkChunks(MapChunkData london, MapChunkData manor)
    {
        if (london == null || manor == null) return;

        // Manor Cellars is reached via its own door (ManorCellarsEntrance/InstanceDoor), not
        // the edge grid — NOT setting london.WestChunk here, since that edge already leads to
        // West_Canal. Only give Manor Cellars a rough map-back reference.
        manor.EastChunk = london;

        EditorUtility.SetDirty(london);
        EditorUtility.SetDirty(manor);
    }

    private static GameObject BuildManorCellarsPrefab()
    {
        GameObject root = new GameObject("Manor_Cellars_Prefab");

        // Dark cellar floor (smaller playable pad on the chunk)
        GameObject ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.name = "Ground";
        ground.transform.SetParent(root.transform, false);
        ground.transform.localScale = new Vector3(8f, 1f, 8f); // 80x80 playable
        var gr = ground.GetComponent<Renderer>();
        Material floorMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Placeholders/mat_dungeon_floor.mat");
        if (floorMat != null)
            gr.sharedMaterial = floorMat;
        else
            gr.sharedMaterial = MakeFallbackMat(new Color(0.25f, 0.22f, 0.2f));
        GameObjectUtility.SetStaticEditorFlags(ground,
            StaticEditorFlags.NavigationStatic | StaticEditorFlags.BatchingStatic);

        // Black void skirt
        GameObject voidPlane = GameObject.CreatePrimitive(PrimitiveType.Plane);
        voidPlane.name = "DungeonVoid";
        voidPlane.transform.SetParent(root.transform, false);
        voidPlane.transform.localPosition = new Vector3(0f, -0.2f, 0f);
        voidPlane.transform.localScale = new Vector3(22f, 1f, 22f);
        Object.DestroyImmediate(voidPlane.GetComponent<Collider>());
        var vr = voidPlane.GetComponent<Renderer>();
        vr.sharedMaterial = MakeFallbackMat(Color.black);

        Material wallMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Placeholders/mat_dungeon_wall.mat");

        // Simple rooms: start hall + corridor east to gate
        BuildWallBox(root.transform, new Vector3(0f, 0f, -10f), 14f, 10f, wallMat, openEast: true);
        BuildWallBox(root.transform, new Vector3(12f, 0f, -10f), 10f, 6f, wallMat, openWest: true, openEast: true);

        // Props
        CreateProp(root.transform, new Vector3(-2f, 0.4f, -10f), new Vector3(2f, 0.5f, 0.8f), new Color(0.3f, 0.2f, 0.12f));
        CreateProp(root.transform, new Vector3(4f, 0.45f, -8f), new Vector3(1.2f, 0.6f, 1.8f), new Color(0.45f, 0.42f, 0.38f));

        // Exit gate toward London (east end of corridor)
        GameObject gate = new GameObject("TutorialExitGate");
        gate.transform.SetParent(root.transform, false);
        gate.transform.localPosition = new Vector3(20f, 1.2f, -10f);
        var box = gate.AddComponent<BoxCollider>();
        box.isTrigger = true;
        box.size = new Vector3(3f, 3f, 4f);
        gate.AddComponent<TutorialExitGate>();

        GameObject gateVisual = GameObject.CreatePrimitive(PrimitiveType.Cube);
        gateVisual.name = "GateDoors";
        gateVisual.transform.SetParent(gate.transform, false);
        gateVisual.transform.localPosition = Vector3.zero;
        gateVisual.transform.localScale = new Vector3(0.4f, 2.8f, 3.5f);
        Object.DestroyImmediate(gateVisual.GetComponent<Collider>());
        var gvr = gateVisual.GetComponent<Renderer>();
        gvr.sharedMaterial = MakeFallbackMat(new Color(0.35f, 0.22f, 0.12f));

        // Chunk edges (full chunk size) — locked until tutorial complete
        float edge = EKVibe.ChunkSize * 0.5f - 1f; // ~109
        CreateEdge("NorthEdge", root.transform, new Vector3(0, 1, edge), new Vector3(EKVibe.ChunkSize, 5, 2), Direction.North);
        CreateEdge("SouthEdge", root.transform, new Vector3(0, 1, -edge), new Vector3(EKVibe.ChunkSize, 5, 2), Direction.South);
        CreateEdge("EastEdge", root.transform, new Vector3(edge, 1, 0), new Vector3(2, 5, EKVibe.ChunkSize), Direction.East);
        CreateEdge("WestEdge", root.transform, new Vector3(-edge, 1, 0), new Vector3(2, 5, EKVibe.ChunkSize), Direction.West);

        // Path hint slab pointing east (toward London)
        GameObject path = GameObject.CreatePrimitive(PrimitiveType.Cube);
        path.name = "PathTowardLondon";
        path.transform.SetParent(root.transform, false);
        path.transform.localPosition = new Vector3(16f, 0.02f, -10f);
        path.transform.localScale = new Vector3(12f, 0.08f, 2.5f);
        var pr = path.GetComponent<Renderer>();
        Material pathMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Placeholders/mat_path.mat");
        if (pathMat != null) pr.sharedMaterial = pathMat;

        // Player arrival marker — teleporting into the Manor Cellars lands here (movable in the prefab).
        GameObject spawn = new GameObject("PlayerSpawn");
        spawn.transform.SetParent(root.transform, false);
        spawn.transform.localPosition = new Vector3(0f, 0f, -8f);
        spawn.AddComponent<PlayerSpawnPoint>();

        // Chest arrival marker — the tutorial chest spawns on this (drag to move/raise the chest).
        GameObject chestMark = new GameObject("ChestSpawn");
        chestMark.transform.SetParent(root.transform, false);
        chestMark.transform.localPosition = new Vector3(12f, 0.4f, -12f);
        chestMark.AddComponent<SceneMarker>().Key = "ChestSpawn";

        return root;
    }

    private static void BuildWallBox(Transform parent, Vector3 center, float width, float depth, Material mat,
        bool openEast = false, bool openWest = false)
    {
        float hx = width * 0.5f;
        float hz = depth * 0.5f;

        // North / South walls
        CreateWall(parent, center + new Vector3(0f, 0f, hz), new Vector3(width, EKVibe.WallHeight, 0.4f), mat);
        CreateWall(parent, center + new Vector3(0f, 0f, -hz), new Vector3(width, EKVibe.WallHeight, 0.4f), mat);

        if (!openWest)
            CreateWall(parent, center + new Vector3(-hx, 0f, 0f), new Vector3(0.4f, EKVibe.WallHeight, depth), mat);
        if (!openEast)
            CreateWall(parent, center + new Vector3(hx, 0f, 0f), new Vector3(0.4f, EKVibe.WallHeight, depth), mat);
    }

    private static void CreateWall(Transform parent, Vector3 pos, Vector3 scale, Material mat)
    {
        GameObject wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
        wall.name = "Wall";
        wall.transform.SetParent(parent, false);
        wall.transform.localPosition = new Vector3(pos.x, scale.y * 0.5f, pos.z);
        wall.transform.localScale = scale;
        var r = wall.GetComponent<Renderer>();
        if (mat != null) r.sharedMaterial = mat;
        else r.sharedMaterial = MakeFallbackMat(EKVibe.DungeonWall);
        wall.AddComponent<EnvironmentBlocker>();
        GameObjectUtility.SetStaticEditorFlags(wall,
            StaticEditorFlags.NavigationStatic | StaticEditorFlags.BatchingStatic);
    }

    private static void CreateProp(Transform parent, Vector3 pos, Vector3 scale, Color color)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = "DungeonProp";
        go.transform.SetParent(parent, false);
        go.transform.localPosition = pos;
        go.transform.localScale = scale;
        var r = go.GetComponent<Renderer>();
        r.sharedMaterial = MakeFallbackMat(color);
        go.AddComponent<EnvironmentBlocker>();
    }

    private static Material MakeFallbackMat(Color color)
    {
        Shader sh = Shader.Find("Unlit/Color")
                    ?? Shader.Find("Unlit/Texture")
                    ?? Shader.Find("Sprites/Default")
                    ?? Shader.Find("Standard");
        var mat = new Material(sh != null ? sh : Shader.Find("Hidden/InternalErrorShader"));
        if (mat.HasProperty("_Color")) mat.color = color;
        return mat;
    }

    private static void CreateEdge(string name, Transform parent, Vector3 pos, Vector3 size, Direction dir)
    {
        GameObject edge = new GameObject(name);
        edge.transform.SetParent(parent, false);
        edge.transform.localPosition = pos;
        var box = edge.AddComponent<BoxCollider>();
        box.isTrigger = true;
        box.size = size;
        var ce = edge.AddComponent<ChunkEdge>();
        ce.EdgeDirection = dir;
    }

    private static void BuildFlowUiAndController(MapChunkData london, MapChunkData manor)
    {
        // Event system
        if (Object.FindObjectOfType<UnityEngine.EventSystems.EventSystem>() == null)
        {
            var es = new GameObject("EventSystem");
            es.AddComponent<UnityEngine.EventSystems.EventSystem>();
            es.AddComponent<UnityEngine.EventSystems.StandaloneInputModule>();
        }

        // Canvas
        GameObject canvasGO = GameObject.Find("FlowCanvas");
        if (canvasGO != null) Object.DestroyImmediate(canvasGO);
        canvasGO = new GameObject("FlowCanvas");
        var canvas = canvasGO.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;
        var scaler = canvasGO.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        canvasGO.AddComponent<GraphicRaycaster>();

        // Title
        GameObject title = CreatePanel("TitleScreen", canvasGO.transform, EKVibe.ParchmentDark);
        StretchFull(title);
        CreateLabel(title.transform, "Discover England", 64, new Vector2(0.5f, 0.72f), EKVibe.TextLight);
        CreateLabel(title.transform, "London waits. The Manor Cellars come first.", 22, new Vector2(0.5f, 0.62f), EKVibe.TextLight);
        var newGame = CreateButton(title.transform, "NewGameButton", "New Game", new Vector2(0.5f, 0.42f));
        var quit = CreateButton(title.transform, "QuitButton", "Quit", new Vector2(0.5f, 0.32f));
        var titleUi = title.AddComponent<TitleScreenUI>();
        titleUi.NewGameButton = newGame;
        titleUi.QuitButton = quit;

        // Creator
        GameObject creator = CreatePanel("CharacterCreator", canvasGO.transform, EKVibe.ParchmentPanel);
        StretchFull(creator);
        CreateLabel(creator.transform, "Create Your Exile", 40, new Vector2(0.5f, 0.92f), EKVibe.TextDark);

        GameObject nameGo = new GameObject("NameInput");
        nameGo.transform.SetParent(creator.transform, false);
        var nameRt = nameGo.AddComponent<RectTransform>();
        nameRt.anchorMin = new Vector2(0.35f, 0.82f);
        nameRt.anchorMax = new Vector2(0.65f, 0.88f);
        nameRt.offsetMin = Vector2.zero;
        nameRt.offsetMax = Vector2.zero;
        var nameImg = nameGo.AddComponent<Image>();
        nameImg.color = Color.white;
        var input = nameGo.AddComponent<TMP_InputField>();
        GameObject textArea = new GameObject("Text");
        textArea.transform.SetParent(nameGo.transform, false);
        var textRt = textArea.AddComponent<RectTransform>();
        textRt.anchorMin = Vector2.zero;
        textRt.anchorMax = Vector2.one;
        textRt.offsetMin = new Vector2(10, 4);
        textRt.offsetMax = new Vector2(-10, -4);
        var nameTmp = textArea.AddComponent<TextMeshProUGUI>();
        nameTmp.fontSize = 24;
        nameTmp.color = EKVibe.TextDark;
        input.textComponent = nameTmp;
        input.text = "Exile";

        string[] classNames = { "Young Driller", "En Garde", "Mr Hood", "Dynamo" };
        Button[] classBtns = new Button[4];
        for (int i = 0; i < 4; i++)
        {
            float x = 0.15f + i * 0.2f;
            classBtns[i] = CreateButton(creator.transform, "Class" + i, classNames[i], new Vector2(x, 0.7f), new Vector2(0.18f, 0.07f));
        }

        var classTitle = CreateLabel(creator.transform, "Young Driller", 32, new Vector2(0.5f, 0.58f), EKVibe.TextDark);
        var classBlurb = CreateLabel(creator.transform, PlayerClassInfo.Tagline(PlayerClass.YoungDriller), 20, new Vector2(0.5f, 0.5f), EKVibe.TextDark);
        var weapon = CreateLabel(creator.transform, "Starts with: ZK", 20, new Vector2(0.5f, 0.42f), EKVibe.TextDark);
        var stats = CreateLabel(creator.transform, "Stats", 20, new Vector2(0.5f, 0.32f), EKVibe.TextDark);

        var confirm = CreateButton(creator.transform, "ConfirmButton", "Enter Manor Cellars", new Vector2(0.5f, 0.16f));
        var back = CreateButton(creator.transform, "BackButton", "Back", new Vector2(0.5f, 0.08f));

        var creatorUi = creator.AddComponent<CharacterCreatorUI>();
        creatorUi.NameInput = input;
        creatorUi.ClassTitle = classTitle;
        creatorUi.ClassBlurb = classBlurb;
        creatorUi.WeaponPreview = weapon;
        creatorUi.StatsPreview = stats;
        creatorUi.ClassButtons = classBtns;
        creatorUi.ConfirmButton = confirm;
        creatorUi.BackButton = back;

        creator.SetActive(false);

        // Game flow
        GameObject flowGo = GameObject.Find("GameFlow");
        if (flowGo != null) Object.DestroyImmediate(flowGo);
        flowGo = new GameObject("GameFlow");
        var flow = flowGo.AddComponent<GameFlowController>();
        flow.TitleRoot = title;
        flow.CreatorRoot = creator;
        flow.ManorCellarsChunk = manor;
        flow.LondonChunk = london;

        var chunkMgr = Object.FindObjectOfType<ChunkManager>();
        if (chunkMgr == null)
            chunkMgr = new GameObject("ChunkManager").AddComponent<ChunkManager>();
        flow.ChunkManager = chunkMgr;
        chunkMgr.CurrentChunkData = manor;

        if (Object.FindObjectOfType<WantedManager>() == null)
            new GameObject("WantedManager").AddComponent<WantedManager>();

        if (Object.FindObjectOfType<QuestManager>() == null)
            new GameObject("QuestManager").AddComponent<QuestManager>();

        // Hide HUD while on title (if present)
        var hud = GameObject.Find("UICanvas");
        flow.HudRoot = hud;
        if (hud != null) hud.SetActive(false);

        Selection.activeGameObject = flowGo;
    }

    private static void EnsureManorEntranceOnLondonPrefab()
    {
        string prefabPath = PrefabFolder + "/Home_Alvaston_Prefab.prefab";
        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
        if (prefab == null)
        {
            Debug.LogWarning("London prefab missing — manor door will spawn at runtime on exit.");
            return;
        }

        string assetPath = AssetDatabase.GetAssetPath(prefab);
        GameObject root = PrefabUtility.LoadPrefabContents(assetPath);
        try
        {
            if (root.GetComponentInChildren<InstanceDoor>(true) != null)
                return;

            float half = EKVibe.ChunkSize * 0.5f;
            GameObject door = new GameObject("ManorCellarsEntrance");
            door.transform.SetParent(root.transform, false);
            door.transform.localPosition = new Vector3(-half + 4f, 1.2f, 0f);

            var box = door.AddComponent<BoxCollider>();
            box.isTrigger = true;
            box.size = new Vector3(3.5f, 3f, 4f);

            var inst = door.AddComponent<InstanceDoor>();
            inst.Target = InstanceDoor.Destination.ManorCellars;
            inst.Prompt = "Enter Manor Cellars";
            inst.RequireTutorialComplete = true;

            GameObject visual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            visual.name = "DoorVisual";
            visual.transform.SetParent(door.transform, false);
            visual.transform.localPosition = Vector3.zero;
            visual.transform.localScale = new Vector3(0.5f, 2.6f, 3.2f);
            Object.DestroyImmediate(visual.GetComponent<Collider>());
            var r = visual.GetComponent<Renderer>();
            r.sharedMaterial = MakeFallbackMat(new Color(0.35f, 0.22f, 0.12f));

            PrefabUtility.SaveAsPrefabAsset(root, assetPath);
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(root);
        }
    }

    private static void EnsureQuestTrackerOnHud()
    {
        GameObject canvasGO = GameObject.Find("UICanvas");
        if (canvasGO == null) return;

        Transform hud = canvasGO.transform.Find("HUDPanel");
        if (hud == null) return;

        if (hud.Find("QuestTracker") != null) return;

        GameObject questRoot = new GameObject("QuestTracker");
        questRoot.transform.SetParent(hud, false);
        var rt = questRoot.AddComponent<RectTransform>();
        rt.anchorMin = new Vector2(1, 1);
        rt.anchorMax = new Vector2(1, 1);
        rt.pivot = new Vector2(1, 1);
        rt.anchoredPosition = new Vector2(-16, -100);
        rt.sizeDelta = new Vector2(280, 72);
        var img = questRoot.AddComponent<Image>();
        img.color = new Color(0.2f, 0.15f, 0.1f, 0.72f);

        TextMeshProUGUI title = CreateHudTmp(questRoot.transform, "QuestTitle", "", 18, new Vector2(0.06f, 0.52f), new Vector2(0.94f, 0.95f));
        TextMeshProUGUI objective = CreateHudTmp(questRoot.transform, "QuestObjective", "", 15, new Vector2(0.06f, 0.08f), new Vector2(0.94f, 0.52f));
        objective.enableWordWrapping = true;

        var questUi = hud.gameObject.GetComponent<QuestTrackerUI>();
        if (questUi == null) questUi = hud.gameObject.AddComponent<QuestTrackerUI>();
        questUi.Root = questRoot;
        questUi.TitleText = title;
        questUi.ObjectiveText = objective;
        questRoot.SetActive(false);
    }

    private static TextMeshProUGUI CreateHudTmp(Transform parent, string name, string text, float size, Vector2 aMin, Vector2 aMax)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var rt = go.AddComponent<RectTransform>();
        rt.anchorMin = aMin;
        rt.anchorMax = aMax;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
        var tmp = go.AddComponent<TextMeshProUGUI>();
        tmp.text = text;
        tmp.fontSize = size;
        tmp.color = EKVibe.TextLight;
        tmp.alignment = TextAlignmentOptions.Left;
        return tmp;
    }

    private static GameObject CreatePanel(string name, Transform parent, Color color)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var rt = go.AddComponent<RectTransform>();
        var img = go.AddComponent<Image>();
        img.color = color;
        return go;
    }

    private static void StretchFull(GameObject go)
    {
        var rt = go.GetComponent<RectTransform>();
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
    }

    private static TextMeshProUGUI CreateLabel(Transform parent, string text, float size, Vector2 anchor, Color color)
    {
        GameObject go = new GameObject("Label");
        go.transform.SetParent(parent, false);
        var rt = go.AddComponent<RectTransform>();
        rt.anchorMin = anchor - new Vector2(0.4f, 0.04f);
        rt.anchorMax = anchor + new Vector2(0.4f, 0.04f);
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
        var tmp = go.AddComponent<TextMeshProUGUI>();
        tmp.text = text;
        tmp.fontSize = size;
        tmp.color = color;
        tmp.alignment = TextAlignmentOptions.Center;
        return tmp;
    }

    private static Button CreateButton(Transform parent, string name, string label, Vector2 anchor)
    {
        return CreateButton(parent, name, label, anchor, new Vector2(0.22f, 0.07f));
    }

    private static Button CreateButton(Transform parent, string name, string label, Vector2 anchor, Vector2 size)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var rt = go.AddComponent<RectTransform>();
        rt.anchorMin = anchor - size * 0.5f;
        rt.anchorMax = anchor + size * 0.5f;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
        var img = go.AddComponent<Image>();
        img.color = EKVibe.ButtonBrown;
        var btn = go.AddComponent<Button>();
        CreateLabel(go.transform, label, 22, new Vector2(0.5f, 0.5f), EKVibe.TextLight);
        // fix label stretch inside button
        var labelRt = go.transform.GetChild(0).GetComponent<RectTransform>();
        labelRt.anchorMin = Vector2.zero;
        labelRt.anchorMax = Vector2.one;
        return btn;
    }
}
