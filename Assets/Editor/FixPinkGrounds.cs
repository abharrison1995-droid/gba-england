using UnityEngine;
using UnityEditor;
using System.IO;
using ExiledAlvaston.Vibe;

/// <summary>
/// Reassigns chunk Ground / Path materials when Unity shows magenta (missing shader/texture).
/// </summary>
public static class FixPinkGrounds
{
    const string ArtFolder = "Assets/Art/Placeholders";
    const string PrefabFolder = "Assets/Prefabs/Chunks";

    [MenuItem("Tools/Exiled Alvaston/Repair/Fix Pink Grounds")]
    public static void FixAll()
    {
        // Regenerate textures + materials first (Unlit/Texture — hard to break)
        PlaceholderArtGenerator.GenerateAll();

        Material grass = LoadMat("mat_grass");
        Material stone = LoadMat("mat_stone");
        Material path = LoadMat("mat_path");
        Material dungeonFloor = LoadMat("mat_dungeon_floor");
        Material dungeonWall = LoadMat("mat_dungeon_wall");

        int fixedCount = 0;

        if (Directory.Exists(PrefabFolder.Replace("Assets/", Application.dataPath + "/").Replace('/', Path.DirectorySeparatorChar))
            || AssetDatabase.IsValidFolder(PrefabFolder))
        {
            string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { PrefabFolder });
            foreach (string guid in guids)
            {
                string pathAsset = AssetDatabase.GUIDToAssetPath(guid);
                GameObject root = PrefabUtility.LoadPrefabContents(pathAsset);
                try
                {
                    fixedCount += AssignInHierarchy(root.transform, grass, stone, path, dungeonFloor, dungeonWall);
                    PrefabUtility.SaveAsPrefabAsset(root, pathAsset);
                }
                finally
                {
                    PrefabUtility.UnloadPrefabContents(root);
                }
            }
        }

        // Open scene instances
        foreach (var r in Object.FindObjectsOfType<Renderer>())
            fixedCount += AssignRenderer(r, grass, stone, path, dungeonFloor, dungeonWall) ? 1 : 0;

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Pink ground fix applied ({fixedCount} renderers). Materials now use Unlit/Texture.");
    }

    private static Material LoadMat(string name)
    {
        return AssetDatabase.LoadAssetAtPath<Material>($"{ArtFolder}/{name}.mat");
    }

    private static int AssignInHierarchy(Transform root, Material grass, Material stone, Material path,
        Material dungeonFloor, Material dungeonWall)
    {
        int n = 0;
        var renderers = root.GetComponentsInChildren<Renderer>(true);
        foreach (var r in renderers)
        {
            if (AssignRenderer(r, grass, stone, path, dungeonFloor, dungeonWall))
                n++;
        }
        return n;
    }

    private static bool AssignRenderer(Renderer r, Material grass, Material stone, Material path,
        Material dungeonFloor, Material dungeonWall)
    {
        if (r == null) return false;
        string n = r.gameObject.name;

        Material pick = null;
        if (n.Contains("DungeonVoid"))
        {
            Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Sprites/Default");
            if (sh == null) return false;
            r.sharedMaterial = new Material(sh) { color = Color.black };
            EditorUtility.SetDirty(r);
            return true;
        }

        if (n == "Ground")
            pick = IsUnderManor(r.transform) ? dungeonFloor : grass;
        else if (n.Contains("Grass"))
            pick = grass;
        else if (n.Contains("Path") || n.Contains("Road") || n.Contains("Asphalt"))
            pick = path;
        else if (n.Contains("Wall") || n.Contains("GateDoors") || n.Contains("DoorVisual") || n.Contains("DungeonProp"))
            pick = dungeonWall != null ? dungeonWall : stone;
        else if (IsPinkOrMissing(r))
            pick = grass;
        else
            return false;

        if (pick == null) return false;
        r.sharedMaterial = pick;
        EditorUtility.SetDirty(r);
        return true;
    }

    private static bool IsUnderManor(Transform t)
    {
        while (t != null)
        {
            if (t.name.Contains("Manor") || t.name.Contains("Cellar"))
                return true;
            t = t.parent;
        }
        return false;
    }

    private static bool IsPinkOrMissing(Renderer r)
    {
        var mat = r.sharedMaterial;
        if (mat == null) return true;
        if (mat.shader == null) return true;
        string sn = mat.shader.name;
        if (string.IsNullOrEmpty(sn)) return true;
        if (sn.Contains("InternalError") || sn.Contains("Hidden/InternalErrorShader"))
            return true;
        // Missing texture on textured floor often looks broken; treat as needs fix if Ground
        if (r.gameObject.name == "Ground" && mat.mainTexture == null)
            return true;
        return false;
    }
}
