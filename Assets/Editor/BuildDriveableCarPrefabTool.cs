using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEditor;
using GBHEngland.Data;
using GBHEngland.World;

/// <summary>
/// Builds driveable car prefabs, VehicleData assets, and World Palette PlacementPresets
/// from the 3D models in Assets/3DModels/Vehicles/.
///
/// Run via: Tools -> Place -> Build Driveable Car Prefabs
///
/// Builds:
///   - Assets/Prefabs/ModernBritain/DriveableCar_<Name>.prefab (with VehicleController, Rigidbody, BoxCollider, Interactable)
///   - Assets/Data/Vehicles/Driveable_<Name>_Data.asset (VehicleData with 3D arcade physics enabled)
///   - Assets/Data/Presets/Preset_Driveable_<Name>.asset (PlacementPreset categorized under DriveableVehicle)
/// </summary>
public class BuildDriveableCarPrefabTool : EditorWindow
{
    private const string ModelFolder = "Assets/3DModels/Vehicles";
    private const string PrefabFolder = "Assets/Prefabs/ModernBritain";
    private const string DataFolder = "Assets/Data/Vehicles";
    private const string PresetFolder = "Assets/Data/Presets";

    private enum VehicleClass
    {
        Hatchback,
        Sedan,
        ThreeWheeler,
        Van,
        Truck
    }

    private class CarSpec
    {
        public string ModelPath;
        public string ModelName;
        public string FriendlyName;
        public VehicleClass Class = VehicleClass.Hatchback;
    }

    private readonly List<CarSpec> _cars = new List<CarSpec>();
    private Vector2 _scroll;

    [MenuItem("Tools/Place/Build Driveable Car Prefabs")]
    public static void Open()
    {
        var window = GetWindow<BuildDriveableCarPrefabTool>("Build Driveable Cars");
        window.ScanModels();
    }

    private void ScanModels()
    {
        _cars.Clear();
        if (!AssetDatabase.IsValidFolder(ModelFolder))
        {
            Debug.LogWarning($"BuildDriveableCarPrefabTool: no {ModelFolder} folder found.");
            return;
        }

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
                Class = AutoDetectClass(fileName)
            });
        }
    }

    private static VehicleClass AutoDetectClass(string name)
    {
        string lower = name.ToLowerInvariant();
        if (lower.Contains("robin")) return VehicleClass.ThreeWheeler;
        if (lower.Contains("van") || lower.Contains("transit")) return VehicleClass.Van;
        if (lower.Contains("truck") || lower.Contains("flatbed")) return VehicleClass.Truck;
        if (lower.Contains("mondeo")) return VehicleClass.Sedan;
        return VehicleClass.Hatchback;
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Builds Driveable Car prefabs, VehicleData assets, and World Palette presets from 3D models in " + ModelFolder +
            ". Each car is configured with arcade Rigidbody physics and safe mount/dismount lifecycle.",
            MessageType.Info);

        if (GUILayout.Button("Rescan Models Folder"))
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
            car.Class = (VehicleClass)EditorGUILayout.EnumPopup("Vehicle Class", car.Class);
            EditorGUILayout.EndVertical();
        }
        EditorGUILayout.EndScrollView();

        EditorGUILayout.Space();
        using (new EditorGUI.DisabledScope(_cars.Count == 0))
        {
            if (GUILayout.Button("Build All Driveable Cars", GUILayout.Height(32)))
                BuildAll();
        }
    }

    private void BuildAll()
    {
        EnsureFolder(PrefabFolder);
        EnsureFolder(DataFolder);
        EnsureFolder(PresetFolder);

        var report = new StringBuilder();
        int created = 0, skipped = 0;

        foreach (CarSpec car in _cars)
        {
            string prefabPath = $"{PrefabFolder}/DriveableCar_{car.FriendlyName}.prefab";
            string dataPath = $"{DataFolder}/Driveable_{car.FriendlyName}_Data.asset";
            string presetPath = $"{PresetFolder}/Preset_Driveable_{car.FriendlyName}.asset";

            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(car.ModelPath);
                if (model == null) continue;

                prefab = BuildPrefab(car, model, prefabPath);
                created++;
                report.AppendLine($"  + Prefab created: {prefabPath}");
            }
            else
            {
                skipped++;
            }

            VehicleData data = AssetDatabase.LoadAssetAtPath<VehicleData>(dataPath);
            if (data == null && prefab != null)
            {
                data = BuildData(car, prefab, dataPath);
                report.AppendLine($"  + Data created: {dataPath}");
            }

            PlacementPreset preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(presetPath);
            if (preset == null && data != null)
            {
                BuildPreset(car, data, presetPath);
                report.AppendLine($"  + Preset created: {presetPath}");
            }
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Debug.Log($"Build Driveable Cars Complete:\n{report}");
        EditorUtility.DisplayDialog("Build Driveable Cars", $"{created} prefabs built, {skipped} existing.\nCheck Console for full report.", "OK");
    }

    private static void EnsureFolder(string path)
    {
        if (!AssetDatabase.IsValidFolder(path))
        {
            string parent = System.IO.Path.GetDirectoryName(path).Replace("\\", "/");
            string folder = System.IO.Path.GetFileName(path);
            if (!AssetDatabase.IsValidFolder(parent))
                EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, folder);
        }
    }

    private static GameObject BuildPrefab(CarSpec car, GameObject model, string prefabPath)
    {
        string rootName = $"DriveableCar_{car.FriendlyName}";
        var root = new GameObject(rootName);
        try
        {
            var modelGO = (GameObject)PrefabUtility.InstantiatePrefab(model);
            modelGO.name = "Model";
            modelGO.transform.SetParent(root.transform, false);
            modelGO.transform.localPosition = Vector3.zero;
            modelGO.transform.localRotation = Quaternion.identity;

            var col = root.AddComponent<BoxCollider>();
            Bounds local = LocalBounds(root.transform);
            if (local.size.sqrMagnitude > 0.0001f)
            {
                col.center = local.center;
                col.size = local.size;
            }

            var rb = root.AddComponent<Rigidbody>();
            rb.mass = GetClassMass(car.Class);
            rb.useGravity = false;
            rb.isKinematic = false;
            rb.constraints = RigidbodyConstraints.FreezeRotationX |
                             RigidbodyConstraints.FreezeRotationZ |
                             RigidbodyConstraints.FreezePositionY;

            var interactable = root.AddComponent<Interactable>();
            interactable.Prompt = "Nick this car";
            interactable.InteractRange = 3.5f;
            interactable.Reusable = true;

            var vehicle = root.AddComponent<VehicleController>();
            vehicle.VehicleName = DisplayName(car);
            vehicle.ParkedModel = modelGO;
            vehicle.IsOwnedByNPC = true;
            vehicle.ReturnsHomeOnChunkChange = false;
            vehicle.KeepModelVisibleWhileMounted = true;
            vehicle.IsDriveablePhysics = true;
            vehicle.EnterPrompt = "Get in";
            vehicle.ExitPrompt = "Get out";

            // Physics tuning by class
            ApplyClassTuning(vehicle, car.Class);

            return PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    private static VehicleData BuildData(CarSpec car, GameObject prefab, string dataPath)
    {
        var data = ScriptableObject.CreateInstance<VehicleData>();
        data.VehicleName = DisplayName(car);
        data.ChassisPrefab = prefab;
        data.IsNickable = true;
        data.ParkedPrompt = "Nick this car";
        data.EnterPrompt = "Get in";
        data.ExitPrompt = "Get out";
        data.KeepModelVisibleWhileMounted = true;
        data.IsDriveablePhysics = true;

        switch (car.Class)
        {
            case VehicleClass.ThreeWheeler:
                data.SpeedMultiplier = 3.0f;
                data.TopSpeed = 13f;
                data.DriveForce = 38f;
                data.SteeringTorque = 14f;
                data.TireGrip = 6.5f;
                break;
            case VehicleClass.Van:
                data.SpeedMultiplier = 3.2f;
                data.TopSpeed = 14f;
                data.DriveForce = 48f;
                data.SteeringTorque = 10f;
                data.TireGrip = 8.5f;
                break;
            case VehicleClass.Truck:
                data.SpeedMultiplier = 2.8f;
                data.TopSpeed = 12f;
                data.DriveForce = 55f;
                data.SteeringTorque = 8f;
                data.TireGrip = 9.0f;
                break;
            case VehicleClass.Sedan:
                data.SpeedMultiplier = 3.8f;
                data.TopSpeed = 17f;
                data.DriveForce = 46f;
                data.SteeringTorque = 12f;
                data.TireGrip = 8.0f;
                break;
            default: // Hatchback
                data.SpeedMultiplier = 3.6f;
                data.TopSpeed = 16f;
                data.DriveForce = 44f;
                data.SteeringTorque = 13f;
                data.TireGrip = 8.0f;
                break;
        }

        AssetDatabase.CreateAsset(data, dataPath);
        return data;
    }

    private static void BuildPreset(CarSpec car, VehicleData data, string presetPath)
    {
        var preset = ScriptableObject.CreateInstance<PlacementPreset>();
        preset.Label = DisplayName(car);
        preset.Category = PlacementPreset.PlacementCategory.DriveableVehicle;
        preset.Vehicle = data;

        AssetDatabase.CreateAsset(preset, presetPath);
    }

    private static float GetClassMass(VehicleClass vClass)
    {
        switch (vClass)
        {
            case VehicleClass.ThreeWheeler: return 500f;
            case VehicleClass.Van: return 1800f;
            case VehicleClass.Truck: return 2800f;
            case VehicleClass.Sedan: return 1400f;
            default: return 1100f;
        }
    }

    private static void ApplyClassTuning(VehicleController vehicle, VehicleClass vClass)
    {
        switch (vClass)
        {
            case VehicleClass.ThreeWheeler:
                vehicle.DriveForce = 38f;
                vehicle.TopSpeed = 13f;
                vehicle.SteeringTorque = 14f;
                vehicle.TireGrip = 6.5f;
                break;
            case VehicleClass.Van:
                vehicle.DriveForce = 48f;
                vehicle.TopSpeed = 14f;
                vehicle.SteeringTorque = 10f;
                vehicle.TireGrip = 8.5f;
                break;
            case VehicleClass.Truck:
                vehicle.DriveForce = 55f;
                vehicle.TopSpeed = 12f;
                vehicle.SteeringTorque = 8f;
                vehicle.TireGrip = 9.0f;
                break;
            case VehicleClass.Sedan:
                vehicle.DriveForce = 46f;
                vehicle.TopSpeed = 17f;
                vehicle.SteeringTorque = 12f;
                vehicle.TireGrip = 8.0f;
                break;
            default:
                vehicle.DriveForce = 44f;
                vehicle.TopSpeed = 16f;
                vehicle.SteeringTorque = 13f;
                vehicle.TireGrip = 8.0f;
                break;
        }
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

    private static string FriendlyName(string fileName)
    {
        string cleaned = fileName;
        int idx = cleaned.IndexOf('_');
        if (idx > 0 && cleaned.Substring(0, idx).StartsWith("car"))
            cleaned = cleaned.Substring(idx + 1);

        var sb = new StringBuilder();
        bool cap = true;
        foreach (char c in cleaned)
        {
            if (c == '_' || c == '-' || c == '+' || c == ' ')
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
        string lower = car.FriendlyName.ToLowerInvariant();
        if (lower.Contains("corsa")) return "Vauxhall Corsa";
        if (lower.Contains("robin")) return "Reliant Robin";
        if (lower.Contains("transit")) return "Ford Transit Van";
        if (lower.Contains("cinquecento")) return "Fiat Cinquecento";
        if (lower.Contains("mondeo")) return "Ford Mondeo";
        if (lower.Contains("ibiza")) return "Seat Ibiza";
        if (lower.Contains("flatbed")) return "Flatbed Truck";
        if (lower.Contains("cargotruck")) return "Cargo Truck";
        return car.FriendlyName;
    }
}
