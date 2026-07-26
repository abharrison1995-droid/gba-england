using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.AI;
using UnityEngine.Events;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;
using ExiledAlvaston.Systems;
using ExiledAlvaston.AI;
using ExiledAlvaston.Vibe;

/// <summary>
/// One-click setup for Phase 1–4 modern British mechanics:
///   1. Builds 5 Police tier prefabs (PCSO, Bobby, Armed, Occult Agent, Occult Commander)
///   2. Builds a Nosey Parker civilian prefab
///   3. Builds a stealable Moped vehicle prefab
///   4. Builds a Pub (safehouse) prefab
///   5. Wires WantedManager.PolicePrefabs in the active scene
///   6. Adds StealthController to the player in the active scene
///   7. Places a Nosey Parker, a Moped, and a Pub into the active scene near the player
///
/// Run via: Tools → Exiled Alvaston → Setup (one-time) → Build Modern Britain Prefabs + Wire Scene
/// </summary>
public static class ModernBritainSetup
{
    private const string PrefabFolder = "Assets/Prefabs/ModernBritain";

    // ───────────────────────── colours for placeholder capsules ─────────────────────────
    private static readonly Color ColPCSO          = new Color(1.0f, 0.85f, 0.0f);   // hi-vis yellow
    private static readonly Color ColBobby         = new Color(0.15f, 0.15f, 0.35f);  // dark navy
    private static readonly Color ColArmed         = new Color(0.1f, 0.1f, 0.1f);     // tactical black
    private static readonly Color ColOccultAgent   = new Color(0.25f, 0.2f, 0.15f);   // trench-coat brown
    private static readonly Color ColOccultCmd     = new Color(0.4f, 0.05f, 0.05f);   // Ministry red
    private static readonly Color ColCivilian      = new Color(0.5f, 0.55f, 0.45f);   // casual grey-green
    private static readonly Color ColMoped         = new Color(0.85f, 0.4f, 0.0f);    // Deliveroo orange
    private static readonly Color ColPub           = new Color(0.35f, 0.15f, 0.05f);  // wooden brown

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  MENU ENTRY — the one button to rule them all
    // ═══════════════════════════════════════════════════════════════════════════════════════

    [MenuItem("Tools/Exiled Alvaston/Setup (one-time)/Build Modern Britain Prefabs + Wire Scene")]
    public static void Run()
    {
        CreateFolderRecursive(PrefabFolder);

        // ─── 1. Build Police prefabs ───
        GameObject pcso   = BuildPolicePrefab("Police_PCSO",          "PCSO",            ColPCSO,        60, 10, 1.5f, 3.5f);
        GameObject bobby  = BuildPolicePrefab("Police_Bobby",         "Bobby",           ColBobby,       50, 8, 1.6f, 3.6f);
        GameObject armed  = BuildPolicePrefab("Police_ArmedResponse", "Armed Response",  ColArmed,       80, 14, 1.7f, 4.2f);
        GameObject occult = BuildPolicePrefab("Police_OccultAgent",   "Occult Agent",    ColOccultAgent, 120, 20, 1.8f, 4.8f);
        GameObject occCmd = BuildPolicePrefab("Police_OccultCommander","Occult Commander",ColOccultCmd,  200, 30, 2.0f, 5.5f);

        // ─── 2. Build Nosey Parker civilian ───
        GameObject noseyParker = BuildNoseyParkerPrefab();

        // ─── 3. Build Moped vehicle ───
        GameObject moped = BuildMopedPrefab();

        // ─── 4. Build Pub safehouse ───
        GameObject pub = BuildPubPrefab();

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        // ─── 5. Wire scene objects ───
        WireWantedManager(pcso, bobby, armed, occult, occCmd);
        WireStealthToPlayer();
        PlaceWorldObjects(noseyParker, moped, pub);

        var scene = EditorSceneManager.GetActiveScene();
        EditorSceneManager.MarkSceneDirty(scene);

        Debug.Log(
            "═══════════════════════════════════════════════════════════════\n" +
            "  Modern Britain setup complete!\n" +
            "  • 5 Police prefabs saved to Assets/Prefabs/ModernBritain\n" +
            "  • Nosey Parker, Moped, and Pub prefabs built\n" +
            "  • WantedManager.PolicePrefabs wired\n" +
            "  • StealthController added to player\n" +
            "  • Instances placed in the active scene near the player\n" +
            "  Ctrl+S to save your scene!\n" +
            "═══════════════════════════════════════════════════════════════");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  POLICE PREFAB BUILDER
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static GameObject BuildPolicePrefab(string prefabName, string displayName, Color color,
        int hp, int damage, float scale, float moveSpeed)
    {
        string path = $"{PrefabFolder}/{prefabName}.prefab";
        float height = EKVibe.CharacterHeight * scale;
        float radius = 0.28f * scale;

        var root = new GameObject(prefabName);
        try
        {
            // Capsule collider
            var col = root.AddComponent<CapsuleCollider>();
            col.height = height;
            col.radius = radius;
            col.center = new Vector3(0f, height * 0.5f, 0f);

            // Health
            var health = root.AddComponent<Health>();
            health.MaxHealth = hp;
            health.CurrentHealth = hp;
            health.DisplayName = displayName;

            // NavMeshAgent
            var agent = root.AddComponent<NavMeshAgent>();
            agent.height = height;
            agent.radius = radius;
            agent.speed = moveSpeed;
            agent.stoppingDistance = 1.2f;

            // EnemyAI — so they actually chase the player
            var ai = root.AddComponent<EnemyAI>();
            ai.Damage = damage;
            ai.SightRadius = 20f;
            ai.AttackRange = 1.6f;
            ai.MoveSpeed = moveSpeed;
            ai.IsPolice = true;  // Triggers arrest instead of death

            // Nameplate
            var plate = root.AddComponent<EnemyNameplate>();
            plate.HeightOffset = height + 0.35f;

            // Placeholder visual body (coloured capsule)
            BuildPlaceholderBody(root.transform, height, color, prefabName + "Mat");

            int enemyLayer = LayerMask.NameToLayer("Enemy");
            if (enemyLayer >= 0) root.layer = enemyLayer;

            if (AssetDatabase.LoadAssetAtPath<GameObject>(path) != null)
                AssetDatabase.DeleteAsset(path);
            return PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  NOSEY PARKER PREFAB
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static GameObject BuildNoseyParkerPrefab()
    {
        string path = $"{PrefabFolder}/NoseyParker.prefab";
        float height = EKVibe.CharacterHeight;

        var root = new GameObject("NoseyParker");
        try
        {
            // Interactable for pickpocketing
            var interactable = root.AddComponent<Interactable>();
            interactable.Prompt = "Pickpocket";
            interactable.InteractRange = 2.0f;
            interactable.Reusable = false;

            // Nosey Parker AI — detects magic
            var parker = root.AddComponent<NoseyParkerAI>();
            parker.DetectionRadius = 8f;
            parker.ReportTime = 4f;

            // Pickpocket component
            var pickpocket = root.AddComponent<PickpocketInteractable>();
            pickpocket.MinGold = 5;
            pickpocket.MaxGold = 25;
            pickpocket.CatchChance = 0.3f;

            // Wire the Interactable.OnInteract → PickpocketInteractable.TryPickpocket
            UnityAction pickpocketAction = pickpocket.TryPickpocket;
            UnityEditor.Events.UnityEventTools.AddVoidPersistentListener(interactable.OnInteract, pickpocketAction);

            // Placeholder body
            BuildPlaceholderBody(root.transform, height, ColCivilian, "NoseyParkerMat");

            if (AssetDatabase.LoadAssetAtPath<GameObject>(path) != null)
                AssetDatabase.DeleteAsset(path);
            return PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  MOPED PREFAB
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static GameObject BuildMopedPrefab()
    {
        string path = $"{PrefabFolder}/Moped.prefab";

        var root = new GameObject("Moped");
        try
        {
            // Interactable
            var interactable = root.AddComponent<Interactable>();
            interactable.Prompt = "Nick this Moped";
            interactable.InteractRange = 2.5f;

            // Vehicle Controller
            var vehicle = root.AddComponent<VehicleController>();
            vehicle.VehicleName = "Deliveroo Moped";
            vehicle.SpeedMultiplier = 2.0f;
            vehicle.IsOwnedByNPC = true;

            // Wire OnInteract → VehicleController.Mount
            UnityAction mountAction = vehicle.Mount;
            UnityEditor.Events.UnityEventTools.AddVoidPersistentListener(interactable.OnInteract, mountAction);

            // Placeholder body — a flattened cube that reads as a moped
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.name = "MopedBody";
            Object.DestroyImmediate(body.GetComponent<Collider>());
            body.transform.SetParent(root.transform, false);
            body.transform.localPosition = new Vector3(0f, 0.4f, 0f);
            body.transform.localScale = new Vector3(0.6f, 0.5f, 1.4f);
            body.GetComponent<Renderer>().sharedMaterial =
                EditorMaterialLibrary.GetOrCreate("MopedMat", ColMoped);

            vehicle.ParkedModel = body;

            if (AssetDatabase.LoadAssetAtPath<GameObject>(path) != null)
                AssetDatabase.DeleteAsset(path);
            return PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  PUB SAFEHOUSE PREFAB
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static GameObject BuildPubPrefab()
    {
        string path = $"{PrefabFolder}/Pub_TheWinchester.prefab";

        var root = new GameObject("Pub_TheWinchester");
        try
        {
            // Interactable
            var interactable = root.AddComponent<Interactable>();
            interactable.Prompt = "Have a Pint";
            interactable.InteractRange = 3f;

            // Pub logic
            var pub = root.AddComponent<PubInteractable>();
            pub.PubName = "The Winchester";

            // Wire OnInteract → PubInteractable.HaveAPint
            UnityAction pintAction = pub.HaveAPint;
            UnityEditor.Events.UnityEventTools.AddVoidPersistentListener(interactable.OnInteract, pintAction);

            // Placeholder body — a taller cube that reads as a building/door
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.name = "PubBuilding";
            Object.DestroyImmediate(body.GetComponent<Collider>());
            body.transform.SetParent(root.transform, false);
            body.transform.localPosition = new Vector3(0f, 1.5f, 0f);
            body.transform.localScale = new Vector3(3f, 3f, 2f);
            body.GetComponent<Renderer>().sharedMaterial =
                EditorMaterialLibrary.GetOrCreate("PubMat", ColPub);

            // A small sign above the door
            GameObject sign = GameObject.CreatePrimitive(PrimitiveType.Cube);
            sign.name = "PubSign";
            Object.DestroyImmediate(sign.GetComponent<Collider>());
            sign.transform.SetParent(root.transform, false);
            sign.transform.localPosition = new Vector3(0f, 3.2f, 1.05f);
            sign.transform.localScale = new Vector3(1.8f, 0.4f, 0.1f);
            sign.GetComponent<Renderer>().sharedMaterial =
                EditorMaterialLibrary.GetOrCreate("PubSignMat", new Color(0.9f, 0.85f, 0.6f));

            if (AssetDatabase.LoadAssetAtPath<GameObject>(path) != null)
                AssetDatabase.DeleteAsset(path);
            return PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  SCENE WIRING
    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>Finds the WantedManager in the scene and assigns the 5 police prefabs.</summary>
    private static void WireWantedManager(params GameObject[] policePrefabs)
    {
        var wm = Object.FindObjectOfType<WantedManager>();
        if (wm == null)
        {
            Debug.LogWarning("ModernBritainSetup: no WantedManager in scene — creating one on a new GameObject.");
            var go = new GameObject("WantedManager");
            Undo.RegisterCreatedObjectUndo(go, "Create WantedManager");
            wm = go.AddComponent<WantedManager>();
        }

        Undo.RecordObject(wm, "Wire Police Prefabs");
        wm.PolicePrefabs = policePrefabs;
        EditorUtility.SetDirty(wm);
        Debug.Log($"WantedManager: PolicePrefabs wired ({policePrefabs.Length} tiers).");
    }

    /// <summary>Finds the player CombatController and adds StealthController if missing.</summary>
    private static void WireStealthToPlayer()
    {
        var player = Object.FindObjectOfType<CombatController>();
        if (player == null)
        {
            Debug.LogWarning("ModernBritainSetup: no CombatController in scene — StealthController not added. " +
                             "Enter Play Mode so the player spawns, then re-run, or add manually.");
            return;
        }

        if (player.GetComponent<StealthController>() == null)
        {
            Undo.AddComponent<StealthController>(player.gameObject);
            Debug.Log("StealthController added to player. Press C to crouch.");
        }
        else
        {
            Debug.Log("StealthController already on the player — skipped.");
        }
    }

    /// <summary>Drops one of each prefab into the scene near the player.</summary>
    private static void PlaceWorldObjects(GameObject noseyParkerPrefab, GameObject mopedPrefab, GameObject pubPrefab)
    {
        Vector3 playerPos = Vector3.zero;
        var player = Object.FindObjectOfType<CombatController>();
        if (player != null)
            playerPos = player.transform.position;

        SpawnInstance(noseyParkerPrefab, playerPos + new Vector3(5f, 0f, 3f),  "NoseyParker");
        SpawnInstance(mopedPrefab,       playerPos + new Vector3(-4f, 0f, 5f), "Moped");
        SpawnInstance(pubPrefab,         playerPos + new Vector3(8f, 0f, -4f), "Pub");
    }

    private static void SpawnInstance(GameObject prefab, Vector3 pos, string label)
    {
        if (prefab == null) return;
        pos.y = 0f;
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
        Undo.RegisterCreatedObjectUndo(instance, $"Place {label}");
        instance.transform.position = pos;
        Debug.Log($"Placed {label} at {pos}.");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  HELPERS
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void BuildPlaceholderBody(Transform parent, float height, Color color, string matName)
    {
        GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        body.name = "PlaceholderBody";
        Object.DestroyImmediate(body.GetComponent<Collider>());
        body.transform.SetParent(parent, false);
        body.transform.localPosition = new Vector3(0f, height * 0.5f, 0f);
        body.transform.localScale = new Vector3(0.5f, height * 0.5f, 0.5f);
        body.GetComponent<Renderer>().sharedMaterial =
            EditorMaterialLibrary.GetOrCreate(matName, color);
    }

    private static void CreateFolderRecursive(string path)
    {
        string[] parts = path.Split('/');
        string current = parts[0];
        for (int i = 1; i < parts.Length; i++)
        {
            string next = current + "/" + parts[i];
            if (!AssetDatabase.IsValidFolder(next))
                AssetDatabase.CreateFolder(current, parts[i]);
            current = next;
        }
    }
}
