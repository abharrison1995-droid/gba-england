using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace GBHEngland.EditorTools
{
    /// <summary>
    /// Applies Android and iOS texture import overrides to the world/model/UI textures, so a
    /// build actually ships compressed on mobile instead of falling through to Unity's Standalone
    /// defaults. Idempotent and non-destructive: it only ever sets platform override blocks and
    /// never touches the default/Standalone platform, so re-running it after adding new textures
    /// is safe and expected.
    ///
    /// Deliberately skips ArtImportTool's territory (Assets/Art/Generated, Assets/Art/Placeholders)
    /// and the TextMesh Pro / third-party folders. See RuleFor() for the full path-prefix table and
    /// the reasoning per row — most importantly, npotScale/filterMode/spriteImportMode/textureType
    /// are never touched here, because ArtImportTool depends on the exact values it already set for
    /// sprite-sheet slicing to land in the right place.
    /// </summary>
    public static class MobileTextureSettingsTool
    {
        private const string FormatName = "ASTC_6x6";

        private struct Rule
        {
            public int MaxSize;
            public bool Mipmaps;

            public Rule(int maxSize, bool mipmaps)
            {
                MaxSize = maxSize;
                Mipmaps = mipmaps;
            }
        }

        [MenuItem("Tools/Art/Apply Mobile Texture Settings (Dry Run)")]
        public static void DryRun() => Run(true);

        [MenuItem("Tools/Art/Apply Mobile Texture Settings")]
        public static void Apply() => Run(false);

        private static void Run(bool dryRun)
        {
            string[] guids = AssetDatabase.FindAssets("t:Texture2D");

            int applied = 0;
            int skippedByRule = 0;
            int noImporter = 0;
            var problems = new List<string>();
            var appliedPaths = new List<string>();

            try
            {
                if (!dryRun) AssetDatabase.StartAssetEditing();

                foreach (string guid in guids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    Rule? rule = RuleFor(path);
                    if (rule == null)
                    {
                        skippedByRule++;
                        continue;
                    }

                    var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                    if (importer == null)
                    {
                        // Import can be deferred while assets are batched — surface it rather than
                        // silently leaving the texture on Unity's defaults, as ArtImportTool's own
                        // comment on the same situation warns.
                        noImporter++;
                        problems.Add(path);
                        continue;
                    }

                    if (dryRun)
                    {
                        applied++;
                        appliedPaths.Add(path);
                        continue;
                    }

                    ApplyPlatform(importer, "Android", rule.Value);
                    ApplyPlatform(importer, "iPhone", rule.Value);
                    importer.mipmapEnabled = rule.Value.Mipmaps;
                    importer.SaveAndReimport();

                    applied++;
                    appliedPaths.Add(path);
                }
            }
            finally
            {
                if (!dryRun) AssetDatabase.StopAssetEditing();
            }

            string verb = dryRun ? "Would apply" : "Applied";
            string message =
                $"{verb} mobile overrides to {applied} textures.\n" +
                $"Skipped by rule (folder excluded, e.g. Art/Generated sprite cast): {skippedByRule}\n" +
                $"No TextureImporter yet (see Console for paths): {noImporter}";

            Debug.Log($"[MobileTextureSettingsTool] {message}\n" + string.Join("\n", appliedPaths));
            if (problems.Count > 0)
            {
                Debug.LogWarning("[MobileTextureSettingsTool] No importer for:\n" + string.Join("\n", problems));
            }

            EditorUtility.DisplayDialog("Mobile Texture Settings", message, "OK");
        }

        private static void ApplyPlatform(TextureImporter importer, string platform, Rule rule)
        {
            TextureImporterPlatformSettings settings = importer.GetPlatformTextureSettings(platform);
            settings.overridden = true;
            settings.maxTextureSize = rule.MaxSize;
            settings.format = TextureImporterFormat.ASTC_6x6;
            settings.textureCompression = TextureImporterCompression.Compressed;
            settings.compressionQuality = 50;
            // ASTC has no ETC2 concept, but the field still exists on the settings struct; leaving
            // it at its default is correct — Quality32BitDownscaled only matters on the ETC2 path.
            //
            // Deliberately not touched anywhere in this method: importer.npotScale, filterMode,
            // spriteImportMode, textureType — see the class doc comment for why.
            importer.SetPlatformTextureSettings(settings);
        }

        /// <summary>
        /// null = skip. Order matters: more specific prefixes are checked first.
        /// </summary>
        private static Rule? RuleFor(string assetPath)
        {
            string p = assetPath.Replace('\\', '/');

            // The point-filtered pixel-art cast. ArtImportTool.ApplyImportSettings already sets
            // npotScale=None specifically so sprite-sheet slice rectangles land correctly; block
            // compression would also visibly artifact the hard chroma-keyed edges on 65px cells.
            // No size win either — the whole cast is a couple of MB uncompressed.
            if (p.StartsWith("Assets/Art/Generated/") || p.StartsWith("Assets/Art/Placeholders/"))
                return null;

            if (p.StartsWith("Assets/TextMesh Pro/")) return null;
            if (p.StartsWith("Assets/6twelve/")) return null;

            // A pixel-art enemy sprite sheet living outside Art/Generated -- the same category of
            // content, just from before ArtImportTool existed. A first run swept it into the
            // Assets/3DModels/ rule below and applied ASTC compression to it; reverted, and
            // excluded here so a re-run doesn't redo it.
            if (p.StartsWith("Assets/3DModels/Bandits/")) return null;

            if (p.StartsWith("Assets/Textures/UI/"))
                return new Rule(1024, false);

            if (p.StartsWith("Assets/Textures/") ||
                p.StartsWith("Assets/Art/Textures/") ||
                p.StartsWith("Assets/3DModels/"))
                return new Rule(512, true);

            return null;
        }
    }
}
