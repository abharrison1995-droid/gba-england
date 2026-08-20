using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using GBHEngland.Data;
using GBHEngland.Vibe;
using GBHEngland.World;

namespace GBHEngland.Editor
{
    /// <summary>
    /// Builds and regenerates the 8 standard traffic routes (4 straight-through + 4 left-turns)
    /// across a four-way intersection chunk layout for British left-hand traffic.
    ///
    /// Reads 5 marker GameObjects under a parent named '~TrafficLayout':
    ///   - Road_South
    ///   - Road_North
    ///   - Road_West
    ///   - Road_East
    ///   - Intersection
    ///
    /// Run via: Tools -> Place -> Build Traffic Routes From Layout
    /// </summary>
    public class BuildTrafficRoutesTool : EditorWindow
    {
        private const string DefaultLayoutParentName = "~TrafficLayout";
        private const string SouthMarkerName = "Road_South";
        private const string NorthMarkerName = "Road_North";
        private const string WestMarkerName = "Road_West";
        private const string EastMarkerName = "Road_East";
        private const string IntersectionMarkerName = "Intersection";

        private GameObject _chunkPrefab;
        private string _layoutParentName = DefaultLayoutParentName;

        [Header("Geometry")]
        [Tooltip("Distance from road centreline to lane centre in metres. British traffic shifts left relative to travel direction.")]
        private float _laneOffset = EKVibe.TrafficLaneHalfWidth; // 1.6m

        [Tooltip("Radius of the turn arc at the intersection.")]
        private float _turnRadius = 8f;

        [Header("Traffic Density")]
        [Tooltip("Max alive cars on straight routes.")]
        private int _straightMaxAlive = 2;

        [Tooltip("Max alive cars on turning routes.")]
        private int _turnMaxAlive = 1;

        [Tooltip("Base seconds between spawns.")]
        private float _spawnInterval = 12f;

        [Tooltip("Random jitter added to SpawnInterval.")]
        private float _spawnJitter = 4f;

        [Header("Vehicle Tuning & Presets")]
        private List<TrafficCarEntry> _cars = new List<TrafficCarEntry>();
        private List<PlacementPreset> _driverPresets = new List<PlacementPreset>();

        private Vector2 _scroll;

        [MenuItem("Tools/Place/Build Traffic Routes From Layout")]
        public static void Open()
        {
            var window = GetWindow<BuildTrafficRoutesTool>("Traffic Route Builder");
            window.minSize = new Vector2(420, 520);
            window.AutoPopulateDefaults();
        }

        private void AutoPopulateDefaults()
        {
            // Auto-detect chunk prefab if Home_London_Prefab exists or is selected
            if (_chunkPrefab == null)
            {
                var stage = PrefabStageUtility.GetCurrentPrefabStage();
                if (stage != null && stage.prefabContentsRoot != null)
                {
                    string path = stage.assetPath;
                    _chunkPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                }
                else if (Selection.activeGameObject != null)
                {
                    string path = AssetDatabase.GetAssetPath(Selection.activeGameObject);
                    if (!string.IsNullOrEmpty(path) && path.EndsWith(".prefab"))
                        _chunkPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                }

                if (_chunkPrefab == null)
                {
                    string defaultPath = "Assets/Prefabs/Chunks/Home_London_Prefab.prefab";
                    _chunkPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(defaultPath);
                }
            }

            // Auto-detect VehicleData assets whose chassis is actually wired for ambient traffic.
            // A VehicleData with a ChassisPrefab but no TrafficCar component (e.g. the player's
            // e-bike) would spawn, fail TrafficRoute's GetComponent<TrafficCar> check, and get
            // destroyed every SpawnInterval forever — silently, with no console warning surfaced
            // in this window. Filtering here is what keeps "Build 8 Traffic Routes" from reporting
            // success while producing no visible traffic.
            if (_cars.Count == 0)
            {
                string[] vGuids = AssetDatabase.FindAssets("t:VehicleData");
                foreach (string guid in vGuids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    var vData = AssetDatabase.LoadAssetAtPath<VehicleData>(path);
                    if (vData != null && vData.ChassisPrefab != null && vData.ChassisPrefab.GetComponent<TrafficCar>() != null)
                    {
                        int weight = vData.name.Contains("Robin") ? 3 : 1;
                        _cars.Add(new TrafficCarEntry { Car = vData, Weight = weight });
                    }
                }
            }

            // Auto-detect PlacementPreset assets for drivers. Excludes child presets — a fleeing
            // driver auto-wired to a child NPC preset is a footgun, not a feature.
            if (_driverPresets.Count == 0)
            {
                string[] pGuids = AssetDatabase.FindAssets("t:PlacementPreset");
                foreach (string guid in pGuids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(path);
                    if (preset != null && !preset.name.Contains("Child") &&
                        (preset.name.Contains("Villager") || preset.name.Contains("Citizen") || preset.name.Contains("Driver")))
                    {
                        _driverPresets.Add(preset);
                    }
                }
            }
        }

        private void OnGUI()
        {
            _scroll = EditorGUILayout.BeginScrollView(_scroll);

            EditorGUILayout.HelpBox(
                "Builds 8 British left-hand traffic routes (4 straight + 4 left-turn) from 5 layout markers.\n" +
                "Markers expected under '" + _layoutParentName + "':\n" +
                "  • Road_South\n  • Road_North\n  • Road_West\n  • Road_East\n  • Intersection",
                MessageType.Info);

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Target Prefab", EditorStyles.boldLabel);
            _chunkPrefab = (GameObject)EditorGUILayout.ObjectField("Chunk Prefab", _chunkPrefab, typeof(GameObject), false);
            _layoutParentName = EditorGUILayout.TextField("Layout Marker Parent", _layoutParentName);

            if (_chunkPrefab != null)
            {
                if (GUILayout.Button("Create / Verify ~TrafficLayout Template Markers"))
                {
                    CreateOrVerifyMarkersTemplate();
                }
            }

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Geometry (British Left-Hand)", EditorStyles.boldLabel);
            _laneOffset = EditorGUILayout.FloatField("Lane Offset (m)", _laneOffset);
            _turnRadius = EditorGUILayout.FloatField("Turn Radius (m)", _turnRadius);

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Traffic Density & Timing", EditorStyles.boldLabel);
            _straightMaxAlive = EditorGUILayout.IntField("Straight Max Alive", _straightMaxAlive);
            _turnMaxAlive = EditorGUILayout.IntField("Turn Max Alive", _turnMaxAlive);
            _spawnInterval = EditorGUILayout.FloatField("Spawn Interval (s)", _spawnInterval);
            _spawnJitter = EditorGUILayout.FloatField("Spawn Jitter (s)", _spawnJitter);

            EditorGUILayout.Space();
            EditorGUILayout.LabelField($"Vehicle Types ({_cars.Count})", EditorStyles.boldLabel);
            for (int i = 0; i < _cars.Count; i++)
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    _cars[i].Car = (VehicleData)EditorGUILayout.ObjectField(_cars[i].Car, typeof(VehicleData), false);
                    _cars[i].Weight = EditorGUILayout.IntField("Weight", _cars[i].Weight, GUILayout.Width(120));
                    if (GUILayout.Button("X", GUILayout.Width(24)))
                    {
                        _cars.RemoveAt(i);
                        break;
                    }
                }
            }
            if (GUILayout.Button("+ Add Vehicle Type"))
                _cars.Add(new TrafficCarEntry { Weight = 1 });

            EditorGUILayout.Space();
            EditorGUILayout.LabelField($"Driver Presets ({_driverPresets.Count})", EditorStyles.boldLabel);
            for (int i = 0; i < _driverPresets.Count; i++)
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    _driverPresets[i] = (PlacementPreset)EditorGUILayout.ObjectField(_driverPresets[i], typeof(PlacementPreset), false);
                    if (GUILayout.Button("X", GUILayout.Width(24)))
                    {
                        _driverPresets.RemoveAt(i);
                        break;
                    }
                }
            }
            if (GUILayout.Button("+ Add Driver Preset"))
                _driverPresets.Add(null);

            if (GUILayout.Button("Refresh / Auto-Detect Assets"))
                AutoPopulateDefaults();

            EditorGUILayout.Space(12);

            using (new EditorGUI.DisabledScope(_chunkPrefab == null))
            {
                GUI.backgroundColor = new Color(0.4f, 0.85f, 0.4f);
                if (GUILayout.Button("Build 8 Traffic Routes", GUILayout.Height(38)))
                {
                    BuildRoutes();
                }
                GUI.backgroundColor = Color.white;
            }

            EditorGUILayout.EndScrollView();
        }

        private void CreateOrVerifyMarkersTemplate()
        {
            if (_chunkPrefab == null) return;

            string path = AssetDatabase.GetAssetPath(_chunkPrefab);

            var stage = PrefabStageUtility.GetCurrentPrefabStage();
            if (stage != null && stage.assetPath == path)
            {
                EditorUtility.DisplayDialog("Leave Prefab Mode First",
                    "This prefab is open in Prefab Mode. Prefabs are edited in place while closed; " +
                    "editing this one while it is open would fight the stage's own copy. Close Prefab " +
                    "Mode and try again.",
                    "OK");
                return;
            }

            GameObject contents = PrefabUtility.LoadPrefabContents(path);
            try
            {
                Transform layout = contents.transform.Find(_layoutParentName);
                if (layout == null)
                {
                    var go = new GameObject(_layoutParentName);
                    go.transform.SetParent(contents.transform, false);
                    layout = go.transform;
                }

                EnsureMarker(layout, SouthMarkerName, new Vector3(0f, 0f, -109f));
                EnsureMarker(layout, NorthMarkerName, new Vector3(0f, 0f, 109f));
                EnsureMarker(layout, WestMarkerName, new Vector3(-109f, 0f, 0f));
                EnsureMarker(layout, EastMarkerName, new Vector3(109f, 0f, 0f));
                EnsureMarker(layout, IntersectionMarkerName, Vector3.zero);

                PrefabUtility.SaveAsPrefabAsset(contents, path);
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();
                Debug.Log($"BuildTrafficRoutesTool: Verified '{_layoutParentName}' template markers in {path}.");
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(contents);
            }
        }

        private static void EnsureMarker(Transform parent, string name, Vector3 defaultPos)
        {
            Transform existing = parent.Find(name);
            if (existing == null)
            {
                var marker = new GameObject(name);
                marker.transform.SetParent(parent, false);
                marker.transform.localPosition = defaultPos;
            }
        }

        private void BuildRoutes()
        {
            if (_chunkPrefab == null)
            {
                EditorUtility.DisplayDialog("Error", "Please select a chunk prefab.", "OK");
                return;
            }

            var invalidCars = new List<string>();
            foreach (var e in _cars)
            {
                if (e.Car == null) continue;
                if (e.Car.ChassisPrefab == null || e.Car.ChassisPrefab.GetComponent<TrafficCar>() == null)
                    invalidCars.Add(e.Car.name);
            }
            if (invalidCars.Count > 0)
            {
                EditorUtility.DisplayDialog("Invalid Vehicle Types",
                    "These VehicleData entries have no TrafficCar component on their ChassisPrefab and " +
                    "would spawn, fail to drive, and self-destruct every SpawnInterval:\n\n" +
                    string.Join("\n", invalidCars) +
                    "\n\nRemove them (or build their traffic prefab first) before building routes.",
                    "OK");
                return;
            }
            if (_cars.TrueForAll(e => e.Car == null))
            {
                EditorUtility.DisplayDialog("No Vehicle Types",
                    "No valid vehicle types are configured. Routes would generate with no cars to spawn.",
                    "OK");
                return;
            }

            string path = AssetDatabase.GetAssetPath(_chunkPrefab);

            var stage = PrefabStageUtility.GetCurrentPrefabStage();
            if (stage != null && stage.assetPath == path)
            {
                EditorUtility.DisplayDialog("Leave Prefab Mode First",
                    "This prefab is open in Prefab Mode. Prefabs are edited in place while closed; " +
                    "editing this one while it is open would fight the stage's own copy. Close Prefab " +
                    "Mode and try again.",
                    "OK");
                return;
            }

            GameObject contents = PrefabUtility.LoadPrefabContents(path);

            try
            {
                Transform layout = contents.transform.Find(_layoutParentName);
                if (layout == null)
                {
                    EditorUtility.DisplayDialog("Error",
                        $"Could not find '{_layoutParentName}' in prefab root. Click 'Create / Verify ~TrafficLayout Template Markers' first.",
                        "OK");
                    return;
                }

                Transform mSouth = layout.Find(SouthMarkerName);
                Transform mNorth = layout.Find(NorthMarkerName);
                Transform mWest = layout.Find(WestMarkerName);
                Transform mEast = layout.Find(EastMarkerName);
                Transform mInter = layout.Find(IntersectionMarkerName);

                if (mSouth == null || mNorth == null || mWest == null || mEast == null || mInter == null)
                {
                    EditorUtility.DisplayDialog("Missing Markers",
                        $"Ensure all 5 markers exist under '{_layoutParentName}':\n" +
                        $"- {SouthMarkerName} ({(mSouth != null ? "OK" : "MISSING")})\n" +
                        $"- {NorthMarkerName} ({(mNorth != null ? "OK" : "MISSING")})\n" +
                        $"- {WestMarkerName} ({(mWest != null ? "OK" : "MISSING")})\n" +
                        $"- {EastMarkerName} ({(mEast != null ? "OK" : "MISSING")})\n" +
                        $"- {IntersectionMarkerName} ({(mInter != null ? "OK" : "MISSING")})",
                        "OK");
                    return;
                }

                Vector3 pSouth = mSouth.position;
                Vector3 pNorth = mNorth.position;
                Vector3 pWest = mWest.position;
                Vector3 pEast = mEast.position;
                Vector3 pInter = mInter.position;

                // Find any existing TrafficRoute_* GameObjects to replace.
                var toDelete = new List<GameObject>();
                for (int i = 0; i < contents.transform.childCount; i++)
                {
                    Transform child = contents.transform.GetChild(i);
                    if (child.name.StartsWith("TrafficRoute_"))
                        toDelete.Add(child.gameObject);
                }

                if (toDelete.Count > 0)
                {
                    string names = string.Join("\n", toDelete.ConvertAll(go => go.name));
                    bool confirmed = EditorUtility.DisplayDialog("Replace Existing Traffic Routes",
                        $"This will permanently delete {toDelete.Count} existing route(s) in " +
                        $"{Path.GetFileName(path)}, including any hand-tuned waypoints or per-route " +
                        $"settings, and regenerate all 8 from the current layout markers:\n\n{names}",
                        "Delete and Regenerate", "Cancel");
                    if (!confirmed)
                        return;
                }

                foreach (var go in toDelete)
                    DestroyImmediate(go);

                // Build 8 routes:
                // 1. South -> North (Straight)
                CreateStraightRoute(contents.transform, "South", pSouth, pNorth, pInter);
                // 2. South -> West (Turn Left)
                CreateTurnLeftRoute(contents.transform, "South", pSouth, pWest, pInter);

                // 3. North -> South (Straight)
                CreateStraightRoute(contents.transform, "North", pNorth, pSouth, pInter);
                // 4. North -> East (Turn Left)
                CreateTurnLeftRoute(contents.transform, "North", pNorth, pEast, pInter);

                // 5. West -> East (Straight)
                CreateStraightRoute(contents.transform, "West", pWest, pEast, pInter);
                // 6. West -> North (Turn Left)
                CreateTurnLeftRoute(contents.transform, "West", pWest, pNorth, pInter);

                // 7. East -> West (Straight)
                CreateStraightRoute(contents.transform, "East", pEast, pWest, pInter);
                // 8. East -> South (Turn Left)
                CreateTurnLeftRoute(contents.transform, "East", pEast, pSouth, pInter);

                PrefabUtility.SaveAsPrefabAsset(contents, path);
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();
                Debug.Log($"BuildTrafficRoutesTool: Successfully generated 8 traffic routes in {path}.");
                EditorUtility.DisplayDialog("Success", $"Successfully generated 8 traffic routes in {Path.GetFileName(path)}.", "OK");
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(contents);
            }
        }

        private void CreateStraightRoute(Transform parent, string fromName, Vector3 pFrom, Vector3 pTo, Vector3 pInter)
        {
            Vector3 dIn = DirectionXZ(pFrom, pInter);
            Vector3 dOut = DirectionXZ(pInter, pTo);

            Vector3 oIn = LeftLaneOffset(dIn, _laneOffset);
            Vector3 oOut = LeftLaneOffset(dOut, _laneOffset);

            var waypoints = new List<Vector3>
            {
                pFrom + oIn,
                pInter - dIn * (_turnRadius + 2f) + oIn,
                pInter + dOut * (_turnRadius + 2f) + oOut,
                pTo + oOut
            };

            CreateRouteObject(parent, $"TrafficRoute_{fromName}_Straight", waypoints, _straightMaxAlive);
        }

        private void CreateTurnLeftRoute(Transform parent, string fromName, Vector3 pFrom, Vector3 pTo, Vector3 pInter)
        {
            Vector3 dIn = DirectionXZ(pFrom, pInter);
            Vector3 dOut = DirectionXZ(pInter, pTo);

            Vector3 oIn = LeftLaneOffset(dIn, _laneOffset);
            Vector3 oOut = LeftLaneOffset(dOut, _laneOffset);

            Vector3 p0 = pInter - dIn * _turnRadius + oIn;
            Vector3 p3 = pInter + dOut * _turnRadius + oOut;

            float innerRadius = Mathf.Max(1f, _turnRadius - _laneOffset);
            Vector3 p1 = p0 + dIn * (innerRadius * 0.55f);
            Vector3 p2 = p3 - dOut * (innerRadius * 0.55f);

            var waypoints = new List<Vector3>
            {
                pFrom + oIn,
                pInter - dIn * (_turnRadius + 8f) + oIn,
                p0,
                CubicBezier(p0, p1, p2, p3, 0.25f),
                CubicBezier(p0, p1, p2, p3, 0.50f),
                CubicBezier(p0, p1, p2, p3, 0.75f),
                p3,
                pInter + dOut * (_turnRadius + 8f) + oOut,
                pTo + oOut
            };

            CreateRouteObject(parent, $"TrafficRoute_{fromName}_TurnLeft", waypoints, _turnMaxAlive);
        }

        private void CreateRouteObject(Transform parent, string name, List<Vector3> waypoints, int maxAlive)
        {
            var routeGO = new GameObject(name);
            routeGO.transform.SetParent(parent, false);

            var route = routeGO.AddComponent<TrafficRoute>();
            route.MaxAlive = maxAlive;
            route.SpawnInterval = _spawnInterval;
            route.SpawnJitter = _spawnJitter;

            route.Cars = new List<TrafficCarEntry>();
            foreach (var e in _cars)
            {
                if (e.Car != null)
                    route.Cars.Add(new TrafficCarEntry { Car = e.Car, Weight = Mathf.Max(1, e.Weight) });
            }

            route.DriverPresets = new List<PlacementPreset>();
            foreach (var p in _driverPresets)
            {
                if (p != null)
                    route.DriverPresets.Add(p);
            }

            for (int i = 0; i < waypoints.Count; i++)
            {
                var wpGO = new GameObject($"WP_{i}");
                wpGO.transform.SetParent(routeGO.transform, false);
                wpGO.transform.position = waypoints[i];
            }
        }

        private static Vector3 DirectionXZ(Vector3 from, Vector3 to)
        {
            Vector3 d = to - from;
            d.y = 0f;
            return d.sqrMagnitude < 0.0001f ? Vector3.forward : d.normalized;
        }

        /// <summary>
        /// Driver's left vector in British left-hand driving: Vector3.Cross(forward, Vector3.up) = (-dir.z, 0, dir.x).
        /// </summary>
        private static Vector3 LeftLaneOffset(Vector3 forwardXZ, float offset)
        {
            Vector3 left = new Vector3(-forwardXZ.z, 0f, forwardXZ.x);
            return left * offset;
        }

        private static Vector3 CubicBezier(Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3, float t)
        {
            float u = 1f - t;
            float tt = t * t;
            float uu = u * u;
            float uuu = uu * u;
            float ttt = tt * t;

            Vector3 p = uuu * p0;
            p += 3f * uu * t * p1;
            p += 3f * u * tt * p2;
            p += ttt * p3;
            return p;
        }
    }
}
