using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.World;

namespace GBHEngland.EditorTools
{
    /// <summary>
    /// Production-grade Editor tool to generate and configure standardized 220x220 world chunk prefabs,
    /// ground materials, localized world-building details/overlays, MapChunkData assets,
    /// bidirectional adjacency wiring, and MapChunkRegistry registration.
    ///
    /// Run via: Tools → World → Generate Chunk Prefab
    /// </summary>
    public class ChunkPrefabGeneratorTool : EditorWindow
    {
        private const string ChunksPrefabFolder = "Assets/Prefabs/Chunks";
        private const string ChunksDataFolder = "Assets/Data/Chunks";
        private const string MaterialsFolder = "Assets/Materials";
        private const string ResourcesFolder = "Assets/Resources";
        private const string RegistryAssetPath = ResourcesFolder + "/MapChunkRegistry.asset";

        public enum DetailOverlayType
        {
            None,
            NorthSouth_Road,
            EastWest_Road,
            Crossroad_Intersection,
            Central_Plaza,
            Wasteland_Dirt_Track,
            TJunction_North_EastWest
        }

        [Header("Chunk Identity")]
        [SerializeField] private string _chunkName = "East_York";
        [SerializeField] private Vector2Int _coordinates = new Vector2Int(0, -2);
        [SerializeField] private bool _isCity = false;
        [SerializeField] private bool _suppressCheckpointSaves = false;

        [Header("Ground Visuals")]
        [SerializeField] private Material _groundMaterial;
        [SerializeField] private Vector2 _groundTiling = new Vector2(60f, 60f);

        [Header("World-Building Ground Detail")]
        [SerializeField] private DetailOverlayType _detailType = DetailOverlayType.NorthSouth_Road;
        [SerializeField] private Material _detailMaterial;

        [Header("Traversability & Adjacency")]
        [SerializeField] private MapChunkData _northChunk;
        [SerializeField] private MapChunkData _southChunk;
        [SerializeField] private MapChunkData _eastChunk;
        [SerializeField] private MapChunkData _westChunk;
        [SerializeField] private bool _wireBidirectional = true;

        [Header("Components & Settings")]
        [SerializeField] private bool _addNavMeshBaker = true;
        [SerializeField] private bool _addPlayerSpawn = true;
        [SerializeField] private string _defaultSpawnId = "";
        [SerializeField] private bool _addEdgeTriggers = true;
        [SerializeField] private bool _addBoundaryWalls = true;
        [SerializeField] private bool _registerInMapChunkRegistry = true;

        private Vector2 _scrollPos;

        [MenuItem("Tools/World/Generate Chunk Prefab")]
        public static void OpenWindow()
        {
            var window = GetWindow<ChunkPrefabGeneratorTool>("Chunk Generator");
            window.minSize = new Vector2(400, 540);
            window.InitDefaults();
            window.Show();
        }

        private void InitDefaults()
        {
            if (_groundMaterial == null)
                _groundMaterial = AssetDatabase.LoadAssetAtPath<Material>(MaterialsFolder + "/Grass.mat");
            if (_detailMaterial == null)
                _detailMaterial = AssetDatabase.LoadAssetAtPath<Material>(MaterialsFolder + "/Asphalt.mat");
            if (_northChunk == null)
                _northChunk = AssetDatabase.LoadAssetAtPath<MapChunkData>(ChunksDataFolder + "/Commie_Slum_Menshevik_Data.asset");
        }

        private void OnGUI()
        {
            _scrollPos = EditorGUILayout.BeginScrollView(_scrollPos);

            EditorGUILayout.LabelField("GBH: England — Chunk Prefab Generator", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(
                "Generates a standard 220x220 world chunk with ground plane, custom tileable material, " +
                "unscaled detail containers, edge triggers, boundary walls, MapChunkData, and bidirectional wiring.",
                MessageType.Info);

            EditorGUILayout.Space(6);

            // Chunk Identity
            EditorGUILayout.LabelField("1. Chunk Identity", EditorStyles.boldLabel);
            _chunkName = EditorGUILayout.TextField("Chunk Name", _chunkName);
            _coordinates = EditorGUILayout.Vector2IntField("Coordinates (X, Y)", _coordinates);
            _isCity = EditorGUILayout.Toggle(new GUIContent("Is City", "Enables knife lockout timers and police spawning."), _isCity);
            _suppressCheckpointSaves = EditorGUILayout.Toggle(new GUIContent("Suppress Checkpoint Saves", "Skip autosave on arrival (e.g. transient arenas)."), _suppressCheckpointSaves);

            EditorGUILayout.Space(8);

            // Ground & Material
            EditorGUILayout.LabelField("2. Ground Plane & Material", EditorStyles.boldLabel);
            _groundMaterial = (Material)EditorGUILayout.ObjectField("Ground Material", _groundMaterial, typeof(Material), false);
            _groundTiling = EditorGUILayout.Vector2Field("Ground UV Tiling", _groundTiling);

            EditorGUILayout.Space(8);

            // World-Building Details
            EditorGUILayout.LabelField("3. World-Building Detail Overlays", EditorStyles.boldLabel);
            _detailType = (DetailOverlayType)EditorGUILayout.EnumPopup("Detail Style", _detailType);
            if (_detailType != DetailOverlayType.None)
            {
                _detailMaterial = (Material)EditorGUILayout.ObjectField("Detail Material", _detailMaterial, typeof(Material), false);
            }

            EditorGUILayout.Space(8);

            // Adjacency Wiring
            EditorGUILayout.LabelField("4. Adjacency & Traversal Wiring", EditorStyles.boldLabel);
            _northChunk = (MapChunkData)EditorGUILayout.ObjectField("North Chunk", _northChunk, typeof(MapChunkData), false);
            _southChunk = (MapChunkData)EditorGUILayout.ObjectField("South Chunk", _southChunk, typeof(MapChunkData), false);
            _eastChunk = (MapChunkData)EditorGUILayout.ObjectField("East Chunk", _eastChunk, typeof(MapChunkData), false);
            _westChunk = (MapChunkData)EditorGUILayout.ObjectField("West Chunk", _westChunk, typeof(MapChunkData), false);
            _wireBidirectional = EditorGUILayout.Toggle(new GUIContent("Wire Bidirectional", "Automatically links neighboring chunk opposite edges to this new chunk."), _wireBidirectional);

            EditorGUILayout.Space(8);

            // Options
            EditorGUILayout.LabelField("5. Options", EditorStyles.boldLabel);
            _addNavMeshBaker = EditorGUILayout.Toggle("Add Runtime NavMesh Baker", _addNavMeshBaker);
            _addPlayerSpawn = EditorGUILayout.Toggle("Add Default Player Spawn", _addPlayerSpawn);
            if (_addPlayerSpawn)
            {
                _defaultSpawnId = EditorGUILayout.TextField("Spawn ID (Empty = Default)", _defaultSpawnId);
            }
            _addEdgeTriggers = EditorGUILayout.Toggle("Add ChunkEdge Triggers (±109.8)", _addEdgeTriggers);
            _addBoundaryWalls = EditorGUILayout.Toggle("Add Boundary Walls (±110.0)", _addBoundaryWalls);
            _registerInMapChunkRegistry = EditorGUILayout.Toggle("Register in MapChunkRegistry", _registerInMapChunkRegistry);

            EditorGUILayout.Space(14);

            if (GUILayout.Button("Generate Chunk Prefab & Wire Data", GUILayout.Height(36)))
            {
                ExecuteGeneration();
            }

            EditorGUILayout.EndScrollView();
        }

        public void ExecuteGeneration()
        {
            if (string.IsNullOrWhiteSpace(_chunkName))
            {
                EditorUtility.DisplayDialog("Validation Error", "Chunk Name cannot be empty.", "OK");
                return;
            }

            if (_chunkName.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 || _chunkName.Contains("/") || _chunkName.Contains("\\"))
            {
                EditorUtility.DisplayDialog("Validation Error", "Chunk Name contains invalid path characters.", "OK");
                return;
            }

            EnsureDirectories();

            string prefabPath = $"{ChunksPrefabFolder}/{_chunkName}_Prefab.prefab";
            string dataPath = $"{ChunksDataFolder}/{_chunkName}_Data.asset";

            // 1. Build / Update Prefab
            GameObject prefab = GenerateChunkPrefab(prefabPath);
            if (prefab == null)
            {
                Debug.LogError($"ChunkPrefabGeneratorTool: Failed to create or update prefab at {prefabPath}");
                return;
            }

            // 2. Build / Update MapChunkData
            MapChunkData data = GenerateMapChunkData(dataPath, prefab);

            // 3. Bidirectional Adjacency Wiring
            if (_wireBidirectional && data != null)
            {
                WireAdjacencies(data);
            }

            // 4. Update MapChunkRegistry
            if (_registerInMapChunkRegistry && data != null)
            {
                RegisterChunk(data);
            }

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log($"<color=green>ChunkPrefabGeneratorTool: Successfully generated and wired '{_chunkName}'!</color>");
            EditorUtility.DisplayDialog("Chunk Generator", $"Successfully generated '{_chunkName}'!\nPrefab: {prefabPath}\nData: {dataPath}", "OK");
        }

        private GameObject GenerateChunkPrefab(string prefabPath)
        {
            bool exists = File.Exists(prefabPath);
            GameObject root = exists 
                ? PrefabUtility.LoadPrefabContents(prefabPath) 
                : new GameObject($"{_chunkName}_Prefab");

            if (root == null)
            {
                Debug.LogError($"ChunkPrefabGeneratorTool: Failed to load prefab contents for {prefabPath}");
                return null;
            }

            try
            {
                root.transform.position = Vector3.zero;
                root.transform.rotation = Quaternion.identity;
                root.transform.localScale = Vector3.one;
                root.layer = 0; // Default layer

                // 1. Runtime NavMesh Baker on Root
                if (_addNavMeshBaker)
                {
                    var baker = GetOrAdd<RuntimeNavMeshBaker>(root);
                    baker.AgentRadius = 0.3f;
                    baker.AgentHeight = 1.55f; // Standard adult worldHeight
                    baker.AgentClimb = 0.5f;
                    baker.AgentSlope = 45f;
                }
                else
                {
                    var baker = root.GetComponent<RuntimeNavMeshBaker>();
                    if (baker != null) DestroyImmediate(baker);
                }

                // 2. Ground Plane (220 x 220 world units)
                Mesh planeMesh = GetBuiltinPlaneMesh();
                Transform groundT = root.transform.Find("Ground");
                GameObject ground = groundT != null ? groundT.gameObject : new GameObject("Ground");
                ground.transform.SetParent(root.transform);
                ground.transform.localPosition = Vector3.zero;
                ground.transform.localRotation = Quaternion.identity;
                ground.transform.localScale = new Vector3(22f, 1f, 22f); // Plane is 10x10 -> 220x220

                var mf = GetOrAdd<MeshFilter>(ground);
                mf.sharedMesh = planeMesh;

                var mr = GetOrAdd<MeshRenderer>(ground);
                if (_groundMaterial != null)
                {
                    mr.sharedMaterial = _groundMaterial;
                }

                var mc = GetOrAdd<MeshCollider>(ground);
                mc.sharedMesh = planeMesh;

                // Mark Ground Static: Batching Static (4) + Navigation Static (8) = 12
                GameObjectUtility.SetStaticEditorFlags(ground, StaticEditorFlags.BatchingStatic | StaticEditorFlags.NavigationStatic);

                // 3. Unscaled Containers
                Transform envT = EnsureContainer(root.transform, "Environment");
                Transform pathsT = EnsureContainer(envT, "Paths");
                Transform detailsT = EnsureContainer(envT, "Details");
                Transform propsT = EnsureContainer(envT, "Props");

                // 4. World-Building Detail Overlays
                BuildDetailOverlays(pathsT, detailsT);

                // 5. Player Spawn Point (Preserves custom transform if already placed)
                if (_addPlayerSpawn)
                {
                    Transform spawnT = FindPlayerSpawnTransform(root.transform);
                    GameObject spawnGo;
                    if (spawnT != null)
                    {
                        spawnGo = spawnT.gameObject;
                    }
                    else
                    {
                        spawnGo = new GameObject("PlayerSpawn");
                        spawnGo.transform.SetParent(root.transform);
                        spawnGo.transform.localPosition = Vector3.zero;
                        spawnGo.transform.localRotation = Quaternion.identity;
                        spawnGo.transform.localScale = Vector3.one;
                    }

                    var psp = GetOrAdd<PlayerSpawnPoint>(spawnGo);
                    psp.Id = _defaultSpawnId ?? "";
                }

                // 6. Edge Triggers directly under root (±109.8 inner face, ±110.2 center)
                if (_addEdgeTriggers)
                {
                    BuildEdgeTrigger(root.transform, "NorthEdge", Direction.North, new Vector3(0f, 1f, 110.2f), new Vector3(220f, 4f, 0.8f));
                    BuildEdgeTrigger(root.transform, "SouthEdge", Direction.South, new Vector3(0f, 1f, -110.2f), new Vector3(220f, 4f, 0.8f));
                    BuildEdgeTrigger(root.transform, "EastEdge", Direction.East, new Vector3(110.2f, 1f, 0f), new Vector3(0.8f, 4f, 220f));
                    BuildEdgeTrigger(root.transform, "WestEdge", Direction.West, new Vector3(-110.2f, 1f, 0f), new Vector3(0.8f, 4f, 220f));
                }

                // 7. Boundary Walls directly under root (±110.0 inner face, ±110.5 center)
                if (_addBoundaryWalls)
                {
                    BuildBoundaryWall(root.transform, "BoundaryWall_North", new Vector3(0f, 2.5f, 110.5f), new Vector3(230f, 6f, 1f));
                    BuildBoundaryWall(root.transform, "BoundaryWall_South", new Vector3(0f, 2.5f, -110.5f), new Vector3(230f, 6f, 1f));
                    BuildBoundaryWall(root.transform, "BoundaryWall_East", new Vector3(110.5f, 2.5f, 0f), new Vector3(1f, 6f, 230f));
                    BuildBoundaryWall(root.transform, "BoundaryWall_West", new Vector3(-110.5f, 2.5f, 0f), new Vector3(1f, 6f, 230f));
                }

                PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            }
            finally
            {
                if (exists)
                    PrefabUtility.UnloadPrefabContents(root);
                else
                    DestroyImmediate(root);
            }

            return AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
        }

        private void BuildDetailOverlays(Transform pathsContainer, Transform detailsContainer)
        {
            // Clear existing children in detail containers to ensure idempotency when changing styles
            ClearChildren(pathsContainer);
            ClearChildren(detailsContainer);

            Mesh cubeMesh = GetBuiltinCubeMesh();
            Material mat = _detailMaterial != null ? _detailMaterial : _groundMaterial;

            switch (_detailType)
            {
                case DetailOverlayType.NorthSouth_Road:
                    EnsureOverlay(pathsContainer, "Road_NorthSouth", new Vector3(0f, 0.04f, 0f), new Vector3(10f, 0.04f, 220f), cubeMesh, mat);
                    break;

                case DetailOverlayType.EastWest_Road:
                    EnsureOverlay(pathsContainer, "Road_EastWest", new Vector3(0f, 0.04f, 0f), new Vector3(220f, 0.04f, 10f), cubeMesh, mat);
                    break;

                case DetailOverlayType.Crossroad_Intersection:
                    EnsureOverlay(pathsContainer, "Road_NorthSouth", new Vector3(0f, 0.04f, 0f), new Vector3(10f, 0.04f, 220f), cubeMesh, mat);
                    EnsureOverlay(pathsContainer, "Road_EastWest", new Vector3(0f, 0.04f, 0f), new Vector3(220f, 0.04f, 10f), cubeMesh, mat);
                    EnsureOverlay(detailsContainer, "Intersection_Centre", new Vector3(0f, 0.06f, 0f), new Vector3(14f, 0.04f, 14f), cubeMesh, mat);
                    break;

                case DetailOverlayType.Central_Plaza:
                    EnsureOverlay(detailsContainer, "Plaza_Pavement", new Vector3(0f, 0.04f, 0f), new Vector3(40f, 0.04f, 40f), cubeMesh, mat);
                    break;

                case DetailOverlayType.Wasteland_Dirt_Track:
                    EnsureOverlay(pathsContainer, "Track_Main", new Vector3(0f, 0.04f, 0f), new Vector3(6f, 0.04f, 220f), cubeMesh, mat);
                    break;

                case DetailOverlayType.TJunction_North_EastWest:
                    // North stem: starts from North edge (+110) down to center (0) -> center at Z=55, length=110
                    EnsureOverlay(pathsContainer, "Road_North_Stem", new Vector3(0f, 0.04f, 55f), new Vector3(10f, 0.04f, 110f), cubeMesh, mat);
                    // East-West cross: spans full West (-110) to East (+110) along Z=0 -> center at X=0, length=220
                    EnsureOverlay(pathsContainer, "Road_EastWest_Cross", new Vector3(0f, 0.04f, 0f), new Vector3(220f, 0.04f, 10f), cubeMesh, mat);
                    // Junction center patch at Y=0.06 to eliminate seam flickering
                    EnsureOverlay(detailsContainer, "TJunction_Centre", new Vector3(0f, 0.06f, 0f), new Vector3(14f, 0.04f, 14f), cubeMesh, mat);
                    break;

                case DetailOverlayType.None:
                default:
                    break;
            }
        }

        private static void EnsureOverlay(Transform parent, string name, Vector3 localPos, Vector3 localScale, Mesh mesh, Material mat)
        {
            Transform t = parent.Find(name);
            GameObject go = t != null ? t.gameObject : new GameObject(name);
            go.transform.SetParent(parent);
            go.transform.localPosition = localPos;
            go.transform.localRotation = Quaternion.identity;
            go.transform.localScale = localScale;

            var mf = GetOrAdd<MeshFilter>(go);
            mf.sharedMesh = mesh;

            var mr = GetOrAdd<MeshRenderer>(go);
            mr.sharedMaterial = mat;

            GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.NavigationStatic);
        }

        private static void BuildEdgeTrigger(Transform parent, string name, Direction dir, Vector3 localPos, Vector3 size)
        {
            Transform t = parent.Find(name);
            GameObject go = t != null ? t.gameObject : new GameObject(name);
            go.transform.SetParent(parent);
            go.transform.localPosition = localPos;
            go.transform.localRotation = Quaternion.identity;
            go.transform.localScale = Vector3.one;

            var col = GetOrAdd<BoxCollider>(go);
            col.isTrigger = true;
            col.center = Vector3.zero;
            col.size = size;

            var edge = GetOrAdd<ChunkEdge>(go);
            edge.EdgeDirection = dir;
        }

        private static void BuildBoundaryWall(Transform parent, string name, Vector3 localPos, Vector3 size)
        {
            Transform t = parent.Find(name);
            GameObject go = t != null ? t.gameObject : new GameObject(name);
            go.transform.SetParent(parent);
            go.transform.localPosition = localPos;
            go.transform.localRotation = Quaternion.identity;
            go.transform.localScale = Vector3.one;

            var col = GetOrAdd<BoxCollider>(go);
            col.isTrigger = false;
            col.center = Vector3.zero;
            col.size = size;
        }

        private MapChunkData GenerateMapChunkData(string dataPath, GameObject prefab)
        {
            var data = AssetDatabase.LoadAssetAtPath<MapChunkData>(dataPath);
            bool isNew = false;
            if (data == null)
            {
                data = CreateInstance<MapChunkData>();
                data.ChunkName = _chunkName;
                isNew = true;
            }
            else if (data.ChunkName != _chunkName)
            {
                Debug.LogWarning($"ChunkPrefabGeneratorTool: Modifying existing chunk data asset ({dataPath}). " +
                                 $"Preserving original ChunkName '{data.ChunkName}' (save key invariant) instead of '{_chunkName}'.");
            }

            data.Coordinates = new Vector2IntCoords(_coordinates.x, _coordinates.y);
            data.IsCity = _isCity;
            data.SuppressCheckpointSaves = _suppressCheckpointSaves;
            data.ChunkPrefab = prefab;

            // Self-referencing guards
            if (_northChunk == data) _northChunk = null;
            if (_southChunk == data) _southChunk = null;
            if (_eastChunk == data) _eastChunk = null;
            if (_westChunk == data) _westChunk = null;

            // Clean up stale reciprocal references
            if (_wireBidirectional)
            {
                if (data.NorthChunk != null && data.NorthChunk != _northChunk && data.NorthChunk.SouthChunk == data)
                {
                    data.NorthChunk.SouthChunk = null;
                    EditorUtility.SetDirty(data.NorthChunk);
                }
                if (data.SouthChunk != null && data.SouthChunk != _southChunk && data.SouthChunk.NorthChunk == data)
                {
                    data.SouthChunk.NorthChunk = null;
                    EditorUtility.SetDirty(data.SouthChunk);
                }
                if (data.EastChunk != null && data.EastChunk != _eastChunk && data.EastChunk.WestChunk == data)
                {
                    data.EastChunk.WestChunk = null;
                    EditorUtility.SetDirty(data.EastChunk);
                }
                if (data.WestChunk != null && data.WestChunk != _westChunk && data.WestChunk.EastChunk == data)
                {
                    data.WestChunk.EastChunk = null;
                    EditorUtility.SetDirty(data.WestChunk);
                }

                // Also clean up new neighbor's old opposite partner if it wasn't us
                if (_northChunk != null && _northChunk.SouthChunk != null && _northChunk.SouthChunk != data)
                {
                    _northChunk.SouthChunk.NorthChunk = null;
                    EditorUtility.SetDirty(_northChunk.SouthChunk);
                }
                if (_southChunk != null && _southChunk.NorthChunk != null && _southChunk.NorthChunk != data)
                {
                    _southChunk.NorthChunk.SouthChunk = null;
                    EditorUtility.SetDirty(_southChunk.NorthChunk);
                }
                if (_eastChunk != null && _eastChunk.WestChunk != null && _eastChunk.WestChunk != data)
                {
                    _eastChunk.WestChunk.EastChunk = null;
                    EditorUtility.SetDirty(_eastChunk.WestChunk);
                }
                if (_westChunk != null && _westChunk.EastChunk != null && _westChunk.EastChunk != data)
                {
                    _westChunk.EastChunk.WestChunk = null;
                    EditorUtility.SetDirty(_westChunk.EastChunk);
                }
            }

            data.NorthChunk = _northChunk;
            data.SouthChunk = _southChunk;
            data.EastChunk = _eastChunk;
            data.WestChunk = _westChunk;

            if (isNew)
            {
                AssetDatabase.CreateAsset(data, dataPath);
            }
            else
            {
                EditorUtility.SetDirty(data);
            }

            return data;
        }

        private void WireAdjacencies(MapChunkData current)
        {
            if (current == null) return;

            if (current.NorthChunk != null)
            {
                current.NorthChunk.SouthChunk = current;
                EditorUtility.SetDirty(current.NorthChunk);
            }

            if (current.SouthChunk != null)
            {
                current.SouthChunk.NorthChunk = current;
                EditorUtility.SetDirty(current.SouthChunk);
            }

            if (current.EastChunk != null)
            {
                current.EastChunk.WestChunk = current;
                EditorUtility.SetDirty(current.EastChunk);
            }

            if (current.WestChunk != null)
            {
                current.WestChunk.EastChunk = current;
                EditorUtility.SetDirty(current.WestChunk);
            }
        }

        private static void RegisterChunk(MapChunkData chunkData)
        {
            if (chunkData == null) return;

            var registry = AssetDatabase.LoadAssetAtPath<MapChunkRegistry>(RegistryAssetPath);
            if (registry == null)
            {
                registry = CreateInstance<MapChunkRegistry>();
                AssetDatabase.CreateAsset(registry, RegistryAssetPath);
            }

            if (registry.Chunks == null)
                registry.Chunks = new List<MapChunkData>();

            // Prune null entries and replace any entry with the same ChunkName
            bool replaced = false;
            for (int i = registry.Chunks.Count - 1; i >= 0; i--)
            {
                MapChunkData existing = registry.Chunks[i];
                if (existing == null)
                {
                    registry.Chunks.RemoveAt(i);
                }
                else if (existing.ChunkName == chunkData.ChunkName)
                {
                    registry.Chunks[i] = chunkData;
                    replaced = true;
                }
            }

            if (!replaced && !registry.Chunks.Contains(chunkData))
            {
                registry.Chunks.Add(chunkData);
            }

            EditorUtility.SetDirty(registry);
        }

        private static Transform EnsureContainer(Transform parent, string name)
        {
            Transform t = parent.Find(name);
            if (t == null)
            {
                var go = new GameObject(name);
                go.transform.SetParent(parent);
                t = go.transform;
            }

            t.localPosition = Vector3.zero;
            t.localRotation = Quaternion.identity;
            t.localScale = Vector3.one;

            return t;
        }

        private static Transform FindPlayerSpawnTransform(Transform root)
        {
            var psp = root.GetComponentInChildren<PlayerSpawnPoint>(true);
            if (psp != null) return psp.transform;
            return root.Find("PlayerSpawn");
        }

        private static void ClearChildren(Transform container)
        {
            if (container == null) return;
            for (int i = container.childCount - 1; i >= 0; i--)
            {
                DestroyImmediate(container.GetChild(i).gameObject);
            }
        }

        private static T GetOrAdd<T>(GameObject go) where T : Component
        {
            T component = go.GetComponent<T>();
            if (component == null)
                component = go.AddComponent<T>();
            return component;
        }

        private static Mesh GetBuiltinPlaneMesh()
        {
            var temp = GameObject.CreatePrimitive(PrimitiveType.Plane);
            Mesh mesh = temp.GetComponent<MeshFilter>().sharedMesh;
            DestroyImmediate(temp);
            return mesh;
        }

        private static Mesh GetBuiltinCubeMesh()
        {
            var temp = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Mesh mesh = temp.GetComponent<MeshFilter>().sharedMesh;
            DestroyImmediate(temp);
            return mesh;
        }

        private static void EnsureDirectories()
        {
            EnsureAssetFolder("Assets", "Prefabs");
            EnsureAssetFolder("Assets/Prefabs", "Chunks");
            EnsureAssetFolder("Assets", "Data");
            EnsureAssetFolder("Assets/Data", "Chunks");
            EnsureAssetFolder("Assets", "Materials");
            EnsureAssetFolder("Assets", "Resources");
        }

        private static void EnsureAssetFolder(string parentFolder, string newFolder)
        {
            string fullPath = $"{parentFolder}/{newFolder}";
            if (!AssetDatabase.IsValidFolder(fullPath))
            {
                AssetDatabase.CreateFolder(parentFolder, newFolder);
            }
        }
    }
}
