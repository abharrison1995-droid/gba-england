using UnityEngine;
using UnityEditor;

/// <summary>
/// Materials referenced by prefab assets must themselves be saved assets — an in-memory
/// material would come back as a missing (magenta) reference. Editor tools get their
/// placeholder materials from here; they live under Assets/Materials.
/// </summary>
public static class EditorMaterialLibrary
{
    public static Material GetOrCreate(string name, Color color)
    {
        string path = $"Assets/Materials/{name}.mat";
        var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (mat != null) return mat;

        if (!AssetDatabase.IsValidFolder("Assets/Materials"))
            AssetDatabase.CreateFolder("Assets", "Materials");
        Shader sh = Shader.Find("Unlit/Color") ?? Shader.Find("Standard");
        mat = new Material(sh) { color = color };
        AssetDatabase.CreateAsset(mat, path);
        return mat;
    }
}
