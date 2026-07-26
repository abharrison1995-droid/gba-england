using UnityEngine;
using UnityEditor;
using System.IO;
using ExiledAlvaston.Vibe;

/// <summary>
/// Generates muted EK-style placeholder textures + sprites under Assets/Art/Placeholders.
/// </summary>
public static class PlaceholderArtGenerator
{
    public const string ArtFolder = "Assets/Art/Placeholders";

    [MenuItem("Tools/Exiled Alvaston/Repair/Generate Placeholder Art")]
    public static void GenerateAll()
    {
        EnsureFolders();

        SaveOpaque("tex_grass", MakeNoiseTile(64, EKVibe.GroundGrass, 0.08f));
        SaveOpaque("tex_stone", MakeNoiseTile(64, EKVibe.GroundStone, 0.06f));
        SaveOpaque("tex_path", MakeNoiseTile(64, EKVibe.PathStone, 0.05f));
        SaveOpaque("tex_dungeon_floor", MakeBrickTile(64, EKVibe.DungeonFloor, new Color(0.32f, 0.3f, 0.28f)));
        SaveOpaque("tex_dungeon_wall", MakeBrickTile(64, EKVibe.DungeonWall, new Color(0.45f, 0.38f, 0.28f)));

        SaveSprite("spr_hero", MakeCharacterSprite(48, 64, new Color(0.35f, 0.45f, 0.7f), new Color(0.85f, 0.7f, 0.55f)));
        SaveSprite("spr_bandit", MakeCharacterSprite(48, 64, new Color(0.45f, 0.22f, 0.18f), new Color(0.75f, 0.6f, 0.45f)));
        SaveSprite("spr_bush", MakeBushSprite(48, 40));
        SaveSprite("spr_tree", MakeTreeSprite(48, 72));
        SaveSprite("spr_loot", MakeLootBagSprite(32, 32));

        CreateMaterial("mat_grass", "tex_grass");
        CreateMaterial("mat_stone", "tex_stone");
        CreateMaterial("mat_path", "tex_path");
        CreateMaterial("mat_dungeon_floor", "tex_dungeon_floor");
        CreateMaterial("mat_dungeon_wall", "tex_dungeon_wall");

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Placeholder art restored in " + ArtFolder + " (hero/bandit sprites + floor materials).");
    }

    public static Sprite LoadSprite(string name)
    {
        return AssetDatabase.LoadAssetAtPath<Sprite>($"{ArtFolder}/{name}.png");
    }

    public static Material LoadMaterial(string name)
    {
        return AssetDatabase.LoadAssetAtPath<Material>($"{ArtFolder}/{name}.mat");
    }

    private static void EnsureFolders()
    {
        if (!AssetDatabase.IsValidFolder("Assets/Art"))
            AssetDatabase.CreateFolder("Assets", "Art");
        if (!AssetDatabase.IsValidFolder(ArtFolder))
            AssetDatabase.CreateFolder("Assets/Art", "Placeholders");
    }

    private static void SaveOpaque(string name, Texture2D tex)
    {
        string path = $"{ArtFolder}/{name}.png";
        File.WriteAllBytes(path, tex.EncodeToPNG());
        Object.DestroyImmediate(tex);
        AssetDatabase.ImportAsset(path);
        var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureType = TextureImporterType.Default;
        importer.wrapMode = TextureWrapMode.Repeat;
        importer.filterMode = FilterMode.Point;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.SaveAndReimport();
    }

    private static void SaveSprite(string name, Texture2D tex)
    {
        string path = $"{ArtFolder}/{name}.png";
        File.WriteAllBytes(path, tex.EncodeToPNG());
        Object.DestroyImmediate(tex);
        AssetDatabase.ImportAsset(path);
        var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureType = TextureImporterType.Sprite;
        importer.spritePixelsPerUnit = 32f;
        importer.filterMode = FilterMode.Point;
        importer.alphaIsTransparency = true;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.SaveAndReimport();
    }

    private static void CreateMaterial(string matName, string texName)
    {
        string matPath = $"{ArtFolder}/{matName}.mat";
        Texture2D tex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{ArtFolder}/{texName}.png");

        // Unlit/Texture first — Built-in, never goes magenta from pipeline mismatches.
        Shader shader = Shader.Find("Unlit/Texture")
                        ?? Shader.Find("Unlit/Transparent")
                        ?? Shader.Find("Standard")
                        ?? Shader.Find("Sprites/Default");
        if (shader == null)
        {
            Debug.LogError("No usable shader found for " + matName);
            return;
        }

        Material mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
        if (mat == null)
        {
            mat = new Material(shader);
            AssetDatabase.CreateAsset(mat, matPath);
        }
        else
        {
            mat.shader = shader;
        }

        mat.mainTexture = tex;
        if (mat.HasProperty("_Color"))
            mat.color = Color.white;
        if (mat.HasProperty("_MainTex") && tex != null)
            mat.SetTexture("_MainTex", tex);

        // Large chunk planes look better with repeated tiling
        Vector2 scale = (texName.Contains("grass") || texName.Contains("path")
                         || texName.Contains("stone") || texName.Contains("dungeon"))
            ? new Vector2(8f, 8f)
            : Vector2.one;
        mat.mainTextureScale = scale;
        if (mat.HasProperty("_MainTex"))
            mat.SetTextureScale("_MainTex", scale);

        EditorUtility.SetDirty(mat);
    }

    private static Texture2D MakeNoiseTile(int size, Color baseCol, float variance)
    {
        var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
        for (int y = 0; y < size; y++)
        for (int x = 0; x < size; x++)
        {
            float n = Mathf.PerlinNoise(x * 0.18f, y * 0.18f);
            float v = (n - 0.5f) * 2f * variance;
            Color c = new Color(
                Mathf.Clamp01(baseCol.r + v),
                Mathf.Clamp01(baseCol.g + v * 0.9f),
                Mathf.Clamp01(baseCol.b + v * 0.7f),
                1f);
            if (x == 0 || y == 0)
                c *= 0.92f;
            tex.SetPixel(x, y, c);
        }
        tex.Apply();
        return tex;
    }

    private static Texture2D MakeBrickTile(int size, Color mortar, Color brick)
    {
        var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
        int brickH = 8;
        int brickW = 16;
        for (int y = 0; y < size; y++)
        for (int x = 0; x < size; x++)
        {
            int row = y / brickH;
            int offset = (row % 2 == 0) ? 0 : brickW / 2;
            bool isMortar = (y % brickH == 0) || ((x + offset) % brickW == 0);
            float n = Mathf.PerlinNoise(x * 0.2f, y * 0.2f) * 0.08f;
            Color c = isMortar ? mortar : brick;
            c.r = Mathf.Clamp01(c.r + n);
            c.g = Mathf.Clamp01(c.g + n);
            c.b = Mathf.Clamp01(c.b + n);
            tex.SetPixel(x, y, c);
        }
        tex.Apply();
        return tex;
    }

    private static Texture2D MakeCharacterSprite(int w, int h, Color body, Color skin)
    {
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        Clear(tex);
        FillEllipse(tex, w / 2, 6, w / 3, 4, new Color(0f, 0f, 0f, 0.35f));
        FillRect(tex, w / 2 - 8, 8, 6, 14, body * 0.85f);
        FillRect(tex, w / 2 + 2, 8, 6, 14, body * 0.85f);
        FillRect(tex, w / 2 - 10, 20, 20, 22, body);
        FillEllipse(tex, w / 2, 48, 8, 9, skin);
        tex.SetPixel(w / 2 - 3, 49, Color.black);
        tex.SetPixel(w / 2 + 2, 49, Color.black);
        tex.Apply();
        return tex;
    }

    private static Texture2D MakeBushSprite(int w, int h)
    {
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        Clear(tex);
        Color leaf = new Color(0.28f, 0.42f, 0.2f, 1f);
        FillEllipse(tex, w / 2, h / 2, w / 2 - 2, h / 2 - 2, leaf);
        FillEllipse(tex, w / 2 - 8, h / 2 + 4, 10, 10, leaf * 1.1f);
        FillEllipse(tex, w / 2 + 8, h / 2 + 2, 10, 10, leaf * 0.9f);
        tex.Apply();
        return tex;
    }

    private static Texture2D MakeTreeSprite(int w, int h)
    {
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        Clear(tex);
        Color trunk = new Color(0.35f, 0.22f, 0.12f, 1f);
        Color canopy = new Color(0.22f, 0.38f, 0.18f, 1f);
        FillRect(tex, w / 2 - 3, 4, 6, 22, trunk);
        FillEllipse(tex, w / 2, 42, 18, 16, canopy);
        FillEllipse(tex, w / 2 - 8, 36, 12, 12, canopy * 1.15f);
        FillEllipse(tex, w / 2 + 8, 38, 12, 12, canopy * 0.9f);
        tex.Apply();
        return tex;
    }

    private static Texture2D MakeLootBagSprite(int w, int h)
    {
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        Clear(tex);
        Color bag = new Color(0.45f, 0.3f, 0.15f, 1f);
        FillEllipse(tex, w / 2, h / 2 - 2, 10, 9, bag);
        FillRect(tex, w / 2 - 8, h / 2 + 4, 16, 4, bag * 0.8f);
        tex.Apply();
        return tex;
    }

    private static void Clear(Texture2D tex)
    {
        Color clear = new Color(0, 0, 0, 0);
        for (int y = 0; y < tex.height; y++)
        for (int x = 0; x < tex.width; x++)
            tex.SetPixel(x, y, clear);
    }

    private static void FillRect(Texture2D tex, int x, int y, int w, int h, Color c)
    {
        for (int yy = y; yy < y + h; yy++)
        for (int xx = x; xx < x + w; xx++)
        {
            if (xx >= 0 && yy >= 0 && xx < tex.width && yy < tex.height)
                tex.SetPixel(xx, yy, c);
        }
    }

    private static void FillEllipse(Texture2D tex, int cx, int cy, int rx, int ry, Color c)
    {
        for (int y = -ry; y <= ry; y++)
        for (int x = -rx; x <= rx; x++)
        {
            if ((x * x) / (float)(rx * rx) + (y * y) / (float)(ry * ry) <= 1f)
            {
                int px = cx + x;
                int py = cy + y;
                if (px >= 0 && py >= 0 && px < tex.width && py < tex.height)
                    tex.SetPixel(px, py, c);
            }
        }
    }
}
