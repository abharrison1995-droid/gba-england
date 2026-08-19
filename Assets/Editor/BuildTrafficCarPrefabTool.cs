using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEditor;
using UnityEditor.Events;
using GBHEngland.Data;
using GBHEngland.World;

/// <summary>
/// Builds the traffic car prefabs and their VehicleData assets from the owner-supplied 3D models
/// in Assets/3DModels/Vehicles/. Run via: Tools -> Place -> Build Traffic Car Prefab.
///
/// This tool exists because the GLB GUIDs do not exist until Unity imports them, so the prefab
/// YAML cannot be hand-authored against them. It scans the vehicles folder, lets the owner assign
/// each car a tier (Common / Better), and builds:
///   - Assets/Prefabs/ModernBritain/TrafficCar_<Name>.prefab — model child plus the four
///     components wired (VehicleController, TrafficCar, Interactable, kinematic Rigidbody +
///     BoxCollider sized to the model).
///   - Assets/Data/Vehicles/TrafficCar_<Name>_Data.asset — a VehicleData seeded from the
///     spec table, so the two cars differ in ride speed, traffic speed, hotwire difficulty and
///     spawn weight.
///
/// New files only, never overwrites: a car that already has a prefab is skipped entirely (the
/// data is only written if it is missing), so re-running is the normal way the job finishes and
/// can never clobber Inspector tuning. Nothing destructive lives here.
///
/// The models are imported by glTFast (com.unity.cloud.gltfast), a ScriptedImporter whose main
/// asset is a GameObject — not a ModelImporter — so the scan searches t:GameObject and filters
/// by extension rather than relying on the t:Model filter.
/// </summary>
public class BuildTrafficCarPrefabTool : EditorWindow
{
    private const string ModelFolder = "Assets/3DModels/Vehicles";
    private const string PrefabFolder = "Assets/Prefabs/ModernBritain";
    private const string DataFolder = "Assets/Data/Vehicles";

    private enum Tier { Common, Better }

    private class CarSpec
    {
        public string ModelPath;
        public string ModelName;      // file name without extension
        public string FriendlyName;   // title-cased, for the prefab/data asset names
        public Tier Tier = Tier.Common;
    }

    private readonly List<CarSpec> _cars = new List<CarSpec>();
    private Vector2 _scroll;

    [MenuItem("Tools/Place/Build Traffic Car Prefab")]
    public static void Open()
    {
        var window = GetWindow<BuildTrafficCarPrefabTool>("Build Traffic Car Prefab");
        window.ScanModels();
    }

    private void ScanModels()
    {
        _cars.Clear();
        if (!AssetDatabase.IsValidFolder(ModelFolder))
        {
            Debug.LogWarning($"BuildTrafficCarPrefabTool: no {ModelFolder} folder — drop your car GLBs there first.");
            return;
        }

        // glTFast imports .glb as a GameObject, not a ModelImporter asset, so t:Model would find
        // nothing. Search t:GameObject and filter by extension.
        string[] guids = AssetDatabase.FindAssets("t:GameObject", new[] { ModelFolder });
        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            string ext = System.IO.Path.GetExtension(path).ToLowerInvariant();
            if (ext != ".glb" && ext != ".fbx" && ext != ".obj") continue;

            string fileName = System.IO.Path.GetFileNameWithoutExtension(path);
            _cars.Add(new CarSpec
            {
                ModelPath = path,
                ModelName = fileName,
                FriendlyName = FriendlyName(fileName),
            });
        }
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Builds a traffic car prefab and its VehicleData from each model in " + ModelFolder +
            ". New files only — a car that already has a prefab is skipped. Assign each car a tier: " +
            "Common (slower, easier to hotwire, spawns often) or Better (faster, harder, rarer).",
            MessageType.Info);

        if (GUILayout.Button("Rescan models folder"))
            ScanModels();

        if (_cars.Count == 0)
        {
            EditorGUILayout.LabelField("No models found in " + ModelFolder + ".");
            return;
        }

        _scroll = EditorGUILayout.BeginScrollView(_scroll);
        foreach (CarSpec car in _cars)
        {
            EditorGUILayout.BeginVertical("box");
            EditorGUILayout.LabelField(car.ModelName, EditorStyles.boldLabel);
            car.Tier = (Tier)EditorGUILayout.EnumPopup("Tier", car.Tier);
            EditorGUILayout.EndVertical();
        }
        EditorGUILayout.EndScrollView();

        EditorGUILayout.Space();
        using (new EditorGUI.DisabledScope(_cars.Count == 0))
        {
            if (GUILayout.Button("Build All", GUILayout.Height(30)))
                BuildAll();
        }
    }

    private void BuildAll()
    {
        var report = new StringBuilder();
        var problems = new StringBuilder();
        int created = 0, skipped = 0;

        foreach (CarSpec car in _cars)
        {
            string prefabPath = $"{PrefabFolder}/TrafficCar_{car.FriendlyName}.prefab";
            string dataPath = $"{DataFolder}/TrafficCar_{car.FriendlyName}_Data.asset";

            bool prefabExists = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath) != null;

            // A car that already has a prefab is skipped entirely — never overwrite it, or any
            // Inspector tuning on it is lost. Only a missing data asset is repaired.
            if (prefabExists)
            {
                if (AssetDatabase.LoadAssetAtPath<VehicleData>(dataPath) == null)
                {
                    GameObject existing = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                    BuildData(car, existing, dataPath);
                    report.AppendLine($"  + {car.FriendlyName}: prefab existed, data was missing — data created.");
                    created++;
                }
                else
                {
                    skipped++;
                    report.AppendLine($"  = {car.FriendlyName}: already exists, left alone.");
                }
                continue;
            }

            GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(car.ModelPath);
            if (model == null)
            {
                problems.AppendLine($"  ! {car.ModelName}: model failed to load at {car.ModelPath}.");
                continue;
            }

            GameObject prefab = BuildPrefab(car, model, prefabPath);
            if (prefab == null)
            {
                problems.AppendLine($"  ! {car.ModelName}: prefab save returned nothing — no data written.");
                continue;
            }

            BuildData(car, prefab, dataPath);
            created++;
            report.AppendLine($"  + {car.FriendlyName}: prefab + data created.");
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        var log = new StringBuilder();
        log.AppendLine("Build Traffic Car Prefab");
        log.AppendLine("────────────────────────");
        log.AppendLine($"  created: {created}, skipped (already exist): {skipped}");
        log.Append(report);
        if (problems.Length > 0)
        {
            log.AppendLine("  problems:");
            log.Append(problems);
        }
        Debug.Log(log.ToString());

        EditorUtility.DisplayDialog("Build Traffic Car Prefab",
            $"{created} created, {skipped} already existed.\n\nDetail in the Console.", "OK");
    }

    /// <summary>Returns the saved prefab asset, or null if the save failed.</summary>
    private static GameObject BuildPrefab(CarSpec car, GameObject model, string prefabPath)
    {
        string rootName = $"TrafficCar_{car.FriendlyName}";
        var root = new GameObject(rootName);
        try
        {
            // The model child. Instantiate the imported GLB so its meshes and materials come along.
            var modelGO = (GameObject)PrefabUtility.InstantiatePrefab(model);
            modelGO.name = "Model";
            modelGO.transform.SetParent(root.transform, false);
            modelGO.transform.localPosition = Vector3.zero;
            modelGO.transform.localRotation = Quaternion.identity;

            // BoxCollider sized to the model's renderers, so the car has a solid body to block on.
            var col = root.AddComponent<BoxCollider>();
            Bounds local = LocalBounds(root.transform);
            if (local.size.sqrMagnitude > 0.0001f)
            {
                col.center = local.center;
                col.size = local.size;
            }

            // Kinematic rigidbody: TrafficCar drives it with MovePosition in FixedUpdate.
            var rb = root.AddComponent<Rigidbody>();
            rb.isKinematic = true;
            rb.useGravity = false;

            // Interactable, wired to VehicleController.Toggle like the e-bike. TrafficCar.Awake
            // clears this and subscribes TryHotwire while driving, and swaps back to Toggle on
            // conversion — so the authored call is a sensible Inspector default, not the live one.
            var interactable = root.AddComponent<Interactable>();
            interactable.Prompt = "Nick this car";
            interactable.InteractRange = 3.5f;   // a car is ~4 m long; 2.5 only reached its centre
            interactable.Reusable = true;

            var vehicle = root.AddComponent<VehicleController>();
            vehicle.VehicleName = DisplayName(car);
            vehicle.ParkedModel = modelGO;
            vehicle.IsOwnedByNPC = true;
            vehicle.ReturnsHomeOnChunkChange = false;   // chunk-owned traffic; the route owns it
            vehicle.KeepModelVisibleWhileMounted = true;

            root.AddComponent<TrafficCar>();

            return PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    private static void BuildData(CarSpec car, GameObject prefab, string dataPath)
    {
        if (AssetDatabase.LoadAssetAtPath<VehicleData>(dataPath) != null) return;

        var data = ScriptableObject.CreateInstance<VehicleData>();
        data.VehicleName = DisplayName(car);
        data.ChassisPrefab = prefab;
        data.IsNickable = true;
        data.ParkedPrompt = "Nick this car";
        data.KeepModelVisibleWhileMounted = true;

        if (car.Tier == Tier.Better)
        {
            data.SpeedMultiplier = 3.75f;
            data.TrafficSpeed = 8.5f;
            data.HotwireWires = 4;
            data.HotwireSeconds = 5f;
        }
        else
        {
            data.SpeedMultiplier = 3.0f;
            data.TrafficSpeed = 7f;
            data.HotwireWires = 3;
            data.HotwireSeconds = 6f;
        }

        AssetDatabase.CreateAsset(data, dataPath);
    }

    private static Bounds LocalBounds(Transform root)
    {
        var bounds = new Bounds();
        bool any = false;
        foreach (Renderer r in root.GetComponentsInChildren<Renderer>())
        {
            if (r == null) continue;
            Vector3 min = root.InverseTransformPoint(r.bounds.min);
            Vector3 max = root.InverseTransformPoint(r.bounds.max);
            if (!any)
            {
                bounds.SetMinMax(min, max);
                any = true;
            }
            else
            {
                bounds.Encapsulate(min);
                bounds.Encapsulate(max);
            }
        }
        return bounds;
    }

    /// <summary>"car_1_reliant_robin" -> "ReliantRobin"; "car_2_corsa" -> "Corsa".</summary>
    private static string FriendlyName(string fileName)
    {
        string cleaned = fileName;
        // Strip a leading car_N_ prefix if present.
        int idx = cleaned.IndexOf('_');
        if (idx > 0 && cleaned.Substring(0, idx).StartsWith("car"))
            cleaned = cleaned.Substring(idx + 1);

        var sb = new StringBuilder();
        bool cap = true;
        foreach (char c in cleaned)
        {
            if (c == '_' || c == '-' || c == ' ')
            {
                cap = true;
                continue;
            }
            sb.Append(cap ? char.ToUpperInvariant(c) : c);
            cap = false;
        }
        return sb.ToString();
    }

    private static string DisplayName(CarSpec car)
    {
        // The better car is the Vauxhall Corsa — the name VehicleController has carried as its
        // default all along. Common falls back to the title-cased friendly name.
        if (car.Tier == Tier.Better && car.FriendlyName.ToLowerInvariant().Contains("corsa"))
            return "Vauxhall Corsa";
        if (car.Tier == Tier.Common && car.FriendlyName.ToLowerInvariant().Contains("robin"))
            return "Reliant Robin";
        return car.FriendlyName;
    }
}