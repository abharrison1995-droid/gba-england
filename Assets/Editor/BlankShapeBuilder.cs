using System.Collections.Generic;
using ExiledAlvaston.World;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace ExiledAlvaston.EditorTools
{
    /// <summary>
    /// Creates the blank flat-shape kit: untextured primitives sized in real metres, each with its
    /// own material, ready for the owner to drop a texture onto.
    ///
    /// Built through GameObject.CreatePrimitive rather than hand-authored prefab YAML so that Unity
    /// supplies the built-in mesh references itself. Nothing here overwrites: a prefab or material
    /// that already exists is left alone and reported as skipped, so the tool is safe to re-run and
    /// belongs under Content rather than Danger Zone.
    ///
    /// Why Quad and not Plane: the existing Path_West and Dirt_path prefabs are the built-in Plane,
    /// which is 200 triangles for a flat rectangle and reads 1 unit of scale as 10 metres. The Quad
    /// is 2 triangles and 1 unit is 1 metre, so the scale field in the Inspector is the size in
    /// metres. The Quad faces -Z, so it lives on a child rotated X+90 and the root transform stays
    /// clean for scaling and Y-rotation. A 90-degree rotation permutes axes without shearing, so
    /// non-uniform scale on the root is safe: root X is width, root Z is length.
    /// </summary>
    public static class BlankShapeBuilder
    {
        private const string PrefabFolder = "Assets/Prefabs/Blanks";
        private const string MaterialFolder = "Assets/Materials/Blanks";

        // Deliberate layering for flats laid on top of each other. Ground sits at 0, the existing
        // paths sit at 0.01-0.03, so the kit's surfaces go above those and decals above the kit.
        // Overlapping flats at the same height z-fight, and the fighting is view-dependent, so it
        // will not always show in the scene view.
        private const float SurfaceHeight = 0.04f;
        private const float DecalHeight = 0.06f;

        [MenuItem("Tools/GBH/Content/Create Blank Shape Kit")]
        public static void CreateKit()
        {
            EnsureFolder(PrefabFolder);
            EnsureFolder(MaterialFolder);

            var created = new List<string>();
            var skipped = new List<string>();

            // A 4m square floor tile. The general-purpose one: floors, plazas, pavement,
            // courtyards, carpets. Scale it to whatever rectangle is wanted.
            BuildFlat("Blank_Slab", new Vector3(4f, 1f, 4f), 0.5f, false, created, skipped);

            // A narrow strip, 2m wide and 20m long, running along Z. The small-path piece: rotate
            // the root on Y to aim it. Narrower and shorter than Path_West on purpose.
            BuildFlat("Blank_Strip", new Vector3(2f, 1f, 20f), 0.5f, false, created, skipped);

            // A 2m square matching the strip's width. Drop one at every corner and junction and
            // butt the strips into it, rather than overlapping two strips and z-fighting the join.
            BuildFlat("Blank_Cap", new Vector3(2f, 1f, 2f), 0.5f, false, created, skipped);

            // A single 1m stamp on a transparent material: puddles, oil stains, blood, road
            // markings, manhole covers, drain grates. No TilingSurface, because a decal is one
            // stamp that should stretch with the transform rather than repeat.
            BuildFlat("Blank_Decal", new Vector3(1f, 1f, 1f), 0f, true, created, skipped);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            string message =
                (created.Count > 0 ? "Created:\n  " + string.Join("\n  ", created) : "Created nothing.") +
                (skipped.Count > 0 ? "\n\nAlready existed, left untouched:\n  " + string.Join("\n  ", skipped) : "");

            Debug.Log("[BlankShapeBuilder] " + message);
            EditorUtility.DisplayDialog("Blank Shape Kit", message, "OK");
        }

        private static void BuildFlat(
            string name,
            Vector3 rootScale,
            float tilesPerMetre,
            bool transparent,
            List<string> created,
            List<string> skipped)
        {
            string prefabPath = PrefabFolder + "/" + name + ".prefab";
            if (AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath) != null)
            {
                skipped.Add(prefabPath);
                return;
            }

            Material material = GetOrCreateMaterial("Mat_" + name, transparent, created, skipped);

            var root = new GameObject(name);
            root.transform.localPosition = new Vector3(0f, transparent ? DecalHeight : SurfaceHeight, 0f);
            root.transform.localScale = rootScale;

            var surface = GameObject.CreatePrimitive(PrimitiveType.Quad);
            surface.name = "Surface";

            // CreatePrimitive attaches a MeshCollider. These are cosmetic ground dressing, exactly
            // like the existing path prefabs, which carry no collider at all. A collider here would
            // also sit in the way of anything raycasting at the ground.
            var collider = surface.GetComponent<Collider>();
            if (collider != null) Object.DestroyImmediate(collider);

            surface.transform.SetParent(root.transform, false);
            surface.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            surface.transform.localPosition = Vector3.zero;
            surface.transform.localScale = Vector3.one;

            var renderer = surface.GetComponent<MeshRenderer>();
            renderer.sharedMaterial = material;

            // A flat sheet lying on the ground casting a shadow onto the ground is wasted work and
            // a common source of shadow acne along its own edge.
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = true;

            if (tilesPerMetre > 0f)
            {
                var tiling = surface.AddComponent<TilingSurface>();
                tiling.TilesPerMetre = tilesPerMetre;
                tiling.CrossAxisMultiplier = 1f;
            }

            // Matches the static flags Path_West already carries: batching and occludee, but not
            // navigation. These are cosmetic and must not contribute to the NavMesh bake.
            var flags = StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic;
            GameObjectUtility.SetStaticEditorFlags(root, flags);
            GameObjectUtility.SetStaticEditorFlags(surface, flags);

            PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
            Object.DestroyImmediate(root);

            created.Add(prefabPath);
        }

        private static Material GetOrCreateMaterial(
            string name,
            bool transparent,
            List<string> created,
            List<string> skipped)
        {
            string path = MaterialFolder + "/" + name + ".mat";
            var existing = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (existing != null)
            {
                skipped.Add(path);
                return existing;
            }

            // Standard, to match Asphalt.mat and the rest of the project's world materials.
            var material = new Material(Shader.Find("Standard"));
            material.color = Color.white;

            // Untextured white on the default 0.5 smoothness reads as wet plastic under the scene
            // lights, which makes it hard to judge a texture once one is dropped in.
            material.SetFloat("_Glossiness", 0f);

            if (transparent)
            {
                // Standard's Fade mode. The shader keywords and render queue have to be set by hand
                // when a material is built from code; setting _Mode alone does nothing.
                material.SetFloat("_Mode", 2f);
                material.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
                material.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha);
                material.SetInt("_ZWrite", 0);
                material.DisableKeyword("_ALPHATEST_ON");
                material.EnableKeyword("_ALPHABLEND_ON");
                material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
                material.renderQueue = (int)RenderQueue.Transparent;
            }

            AssetDatabase.CreateAsset(material, path);
            created.Add(path);
            return material;
        }

        private static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;

            int split = path.LastIndexOf('/');
            string parent = path.Substring(0, split);
            string leaf = path.Substring(split + 1);
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, leaf);
        }
    }
}
