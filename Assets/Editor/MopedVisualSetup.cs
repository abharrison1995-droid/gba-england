using System.IO;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.World;

/// <summary>
/// Gives the Moped a billboarded sprite instead of the orange placeholder cube, and bakes the
/// placeholder sprite itself so the game reads as a moped before any real art exists.
///
/// Run via: Tools → Exiled Alvaston → Art → Build Moped Placeholder Art
///
/// ⚠ Unlike ModernBritainSetup.BuildMopedPrefab, this edits Moped.prefab **in place** via
/// LoadPrefabContents/SaveAsPrefabAsset. That tool does AssetDatabase.DeleteAsset first, which
/// takes the .meta with it and mints a fresh GUID — re-running it would orphan the moped, the
/// Nosey Parker and the pub instances already placed in c.unity. Never delete this asset to
/// rebuild it.
/// </summary>
public static class MopedVisualSetup
{
    private const string PrefabPath    = "Assets/Prefabs/ModernBritain/Moped.prefab";
    private const string ArtFolder     = "Assets/Art/Placeholders";
    private const string SpritePath    = ArtFolder + "/spr_moped_placeholder.png";
    private const string VisualName    = "MopedVisual";
    private const string OldBodyName   = "MopedBody";

    /// <summary>Parked moped height in world units. A moped is shorter than the 1.35 actor.</summary>
    private const float MopedHeight = 0.9f;

    private static readonly Color32 Bodywork  = new Color32(217, 102, 0, 255);   // Deliveroo orange
    private static readonly Color32 Darks     = new Color32(45, 45, 52, 255);    // tyres, seat
    private static readonly Color32 Metal     = new Color32(120, 124, 132, 255); // forks, bars
    private static readonly Color32 Lamp      = new Color32(255, 233, 150, 255);

    [MenuItem("Tools/Exiled Alvaston/Art/Build Moped Placeholder Art")]
    public static void Run()
    {
        Sprite sprite = EnsurePlaceholderSprite();
        if (sprite == null)
        {
            EditorUtility.DisplayDialog("Moped art", "Could not create the placeholder sprite.", "OK");
            return;
        }

        if (!ApplyToPrefab(sprite)) return;

        EditorUtility.DisplayDialog(
            "Moped art",
            "Placeholder sprite baked and Moped.prefab updated in place.\n\n" +
            "The prefab GUID is unchanged, so the instance in c.unity is still attached.\n\n" +
            "To use real artwork later, drop it on VehicleController.VehicleSprite, or assign a " +
            "bespoke rider sprite to the player's WorldActorVisual.MountedSprite.",
            "OK");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  SPRITE
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static Sprite EnsurePlaceholderSprite()
    {
        var existing = AssetDatabase.LoadAssetAtPath<Sprite>(SpritePath);
        if (existing != null)
        {
            Debug.Log($"MopedVisualSetup: reusing existing {SpritePath} (delete it to regenerate).");
            return existing;
        }

        if (!AssetDatabase.IsValidFolder(ArtFolder))
            AssetDatabase.CreateFolder("Assets/Art", "Placeholders");

        File.WriteAllBytes(SpritePath, BuildMopedTexture().EncodeToPNG());
        AssetDatabase.ImportAsset(SpritePath, ImportAssetOptions.ForceUpdate);

        var importer = AssetImporter.GetAtPath(SpritePath) as TextureImporter;
        if (importer != null)
        {
            importer.textureType         = TextureImporterType.Sprite;
            importer.spriteImportMode    = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 32f;
            importer.filterMode          = FilterMode.Point;
            importer.alphaIsTransparency = true;
            importer.mipmapEnabled       = false;
            importer.textureCompression  = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
        }

        Debug.Log($"MopedVisualSetup: baked placeholder sprite at {SpritePath}.");
        return AssetDatabase.LoadAssetAtPath<Sprite>(SpritePath);
    }

    /// <summary>A crude side-on moped: two wheels, a body, a seat, forks and bars.</summary>
    private static Texture2D BuildMopedTexture()
    {
        const int w = 64;
        const int h = 40;

        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        var px = new Color32[w * h];
        var clear = new Color32(0, 0, 0, 0);
        for (int i = 0; i < px.Length; i++) px[i] = clear;

        // Wheels, sat on the bottom edge
        Disc(px, w, h, 15, 10, 9, Darks);
        Disc(px, w, h, 49, 10, 9, Darks);
        Disc(px, w, h, 15, 10, 4, Metal);
        Disc(px, w, h, 49, 10, 4, Metal);

        Rect(px, w, h, 13, 13, 52, 23, Bodywork);   // body / footplate
        Rect(px, w, h, 17, 23, 33, 28, Darks);      // seat
        Rect(px, w, h, 43, 21, 47, 33, Metal);      // forks up to the bars
        Rect(px, w, h, 38, 31, 57, 34, Metal);      // handlebars
        Rect(px, w, h, 50, 24, 56, 30, Lamp);       // headlight

        tex.SetPixels32(px);
        tex.Apply();
        return tex;
    }

    private static void Rect(Color32[] px, int w, int h, int x0, int y0, int x1, int y1, Color32 c)
    {
        for (int y = Mathf.Max(0, y0); y < Mathf.Min(h, y1); y++)
            for (int x = Mathf.Max(0, x0); x < Mathf.Min(w, x1); x++)
                px[y * w + x] = c;
    }

    private static void Disc(Color32[] px, int w, int h, int cx, int cy, int r, Color32 c)
    {
        int rr = r * r;
        for (int y = Mathf.Max(0, cy - r); y <= Mathf.Min(h - 1, cy + r); y++)
        {
            for (int x = Mathf.Max(0, cx - r); x <= Mathf.Min(w - 1, cx + r); x++)
            {
                int dx = x - cx;
                int dy = y - cy;
                if (dx * dx + dy * dy <= rr) px[y * w + x] = c;
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  PREFAB — edited in place, never recreated
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static bool ApplyToPrefab(Sprite sprite)
    {
        if (AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath) == null)
        {
            Debug.LogError($"MopedVisualSetup: {PrefabPath} not found.");
            return false;
        }

        GameObject contents = PrefabUtility.LoadPrefabContents(PrefabPath);
        try
        {
            var vehicle = contents.GetComponent<VehicleController>();
            if (vehicle == null)
            {
                Debug.LogError("MopedVisualSetup: prefab has no VehicleController.");
                return false;
            }

            Transform visual = contents.transform.Find(VisualName);
            if (visual == null)
            {
                var go = new GameObject(VisualName);
                go.transform.SetParent(contents.transform, false);
                visual = go.transform;
            }

            var sr = visual.GetComponent<SpriteRenderer>();
            if (sr == null) sr = visual.gameObject.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = 5;

            if (visual.GetComponent<SpriteBillboard>() == null)
                visual.gameObject.AddComponent<SpriteBillboard>();

            float spriteH = sprite.bounds.size.y;
            if (spriteH < 0.001f) spriteH = 1f;
            visual.localScale = Vector3.one * (MopedHeight / spriteH);
            visual.localPosition = new Vector3(0f, MopedHeight * 0.5f, 0f);

            vehicle.ParkedModel = visual.gameObject;
            vehicle.VehicleSprite = sprite;

            // The orange cube it replaces
            Transform oldBody = contents.transform.Find(OldBodyName);
            if (oldBody != null) Object.DestroyImmediate(oldBody.gameObject);

            PrefabUtility.SaveAsPrefabAsset(contents, PrefabPath);
            Debug.Log("MopedVisualSetup: Moped.prefab updated in place — GUID and scene instance preserved.");
            return true;
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(contents);
        }
    }
}
