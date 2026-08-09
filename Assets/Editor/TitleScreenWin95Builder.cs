using System;
using System.IO;
using System.Linq;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.EditorTools
{
    /// <summary>
    /// Rebuilds the title screen as a Win95 window over the pixelated countryside plate:
    /// the GBH: England wordmark stays at the top, the Union Jack stays baked into the
    /// backdrop at the bottom, and Continue / New Game / Quit become raised grey bevel
    /// buttons inside a navy-title-barred grey window.
    ///
    /// Same safety pattern as TitleScreenSetup: only the children of the preserved TitleRoot
    /// are replaced, the root itself, GameFlowController and TitleScreenUI are untouched,
    /// everything is one undo group, and any exception rolls the whole change back.
    ///
    /// Shares the generated root name "GeneratedTitleLayout" with TitleScreenSetup, so the
    /// fantasy tool still recognises this output and can be re-run to roll back.
    /// </summary>
    public static class TitleScreenWin95Builder
    {
        private const string ScenePath = "Assets/c.unity";
        private const string GeneratedRootName = "GeneratedTitleLayout";
        private const string BackgroundPath = "Assets/Textures/UI/Title/Title_Background_Pixel.png";
        private const string LogoPath = "Assets/Textures/UI/Title/Title_Logo.png";

        private static readonly string[] AssetPaths =
        {
            BackgroundPath,
            LogoPath
        };

        [MenuItem("Tools/GBH/UI/Rebuild Title Screen (Win95)")]
        public static void Rebuild()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                EditorUtility.DisplayDialog("Rebuild Title Screen (Win95)", "Exit Play mode before changing the scene.", "OK");
                return;
            }

            Scene scene = SceneManager.GetActiveScene();
            if (scene.path != ScenePath)
            {
                EditorUtility.DisplayDialog(
                    "Rebuild Title Screen (Win95)",
                    "Open Assets/c.unity first. This tool will not open or replace a scene automatically.",
                    "OK");
                return;
            }

            string missing = AssetPaths.FirstOrDefault(path => !File.Exists(path));
            if (missing != null)
            {
                EditorUtility.DisplayDialog("Rebuild Title Screen (Win95)", "Required asset is missing:\n" + missing, "OK");
                return;
            }

            GameFlowController[] flows = UnityEngine.Object.FindObjectsOfType<GameFlowController>(true);
            if (flows.Length != 1)
            {
                EditorUtility.DisplayDialog(
                    "Rebuild Title Screen (Win95)",
                    "Expected exactly one GameFlowController in Assets/c.unity; found " + flows.Length + ".",
                    "OK");
                return;
            }

            GameFlowController flow = flows[0];
            GameObject titleRoot = flow.TitleRoot;
            if (titleRoot == null || titleRoot.GetComponent<RectTransform>() == null)
            {
                EditorUtility.DisplayDialog("Rebuild Title Screen (Win95)", "GameFlowController.TitleRoot is missing or is not UI.", "OK");
                return;
            }

            TitleScreenUI titleUi = titleRoot.GetComponent<TitleScreenUI>();
            if (titleUi == null)
            {
                EditorUtility.DisplayDialog("Rebuild Title Screen (Win95)", "The preserved TitleRoot has no TitleScreenUI component.", "OK");
                return;
            }

            if (!ValidateReplaceableChildren(titleRoot.transform, out string childSummary))
                return;

            if (!EditorUtility.DisplayDialog(
                    "Rebuild Title Screen (Win95)",
                    "This will replace the following children under the existing TitleScreen root:\n\n" +
                    childSummary +
                    "\n\nThe TitleScreen root, CharacterCreator, Canvas, GameFlowController and HUD references remain intact.",
                    "Apply",
                    "Cancel"))
                return;

            try
            {
                ConfigureSpriteImports();
            }
            catch (Exception ex)
            {
                Debug.LogException(ex);
                EditorUtility.DisplayDialog("Rebuild Title Screen (Win95)", "Sprite import failed. The scene was not changed.\n\n" + ex.Message, "OK");
                return;
            }

            Sprite background = LoadSprite(BackgroundPath);
            Sprite logo = LoadSprite(LogoPath);

            GameObject originalTitleRoot = flow.TitleRoot;
            GameObject originalCreatorRoot = flow.CreatorRoot;
            GameObject originalHudRoot = flow.HudRoot;
            bool originalActiveState = titleRoot.activeSelf;
            int originalSiblingIndex = titleRoot.transform.GetSiblingIndex();

            Undo.IncrementCurrentGroup();
            int undoGroup = Undo.GetCurrentGroup();
            Undo.SetCurrentGroupName("Rebuild Title Screen (Win95)");

            try
            {
                Undo.RegisterFullObjectHierarchyUndo(titleRoot, "Rebuild Title Screen (Win95)");

                for (int i = titleRoot.transform.childCount - 1; i >= 0; i--)
                    Undo.DestroyObjectImmediate(titleRoot.transform.GetChild(i).gameObject);

                Image oldPanel = titleRoot.GetComponent<Image>();
                if (oldPanel != null)
                {
                    Undo.RecordObject(oldPanel, "Clear legacy title panel");
                    oldPanel.color = Color.clear;
                    oldPanel.raycastTarget = false;
                }

                RectTransform generatedRoot = CreateRect(GeneratedRootName, titleRoot.transform);
                Stretch(generatedRoot);

                BuildBackground(generatedRoot, background);
                BuildSafeContent(generatedRoot, logo, out Button continueButton, out Button newGameButton, out Button quitButton);

                SerializedObject serializedUi = new SerializedObject(titleUi);
                serializedUi.FindProperty("ContinueButton").objectReferenceValue = continueButton;
                serializedUi.FindProperty("NewGameButton").objectReferenceValue = newGameButton;
                serializedUi.FindProperty("QuitButton").objectReferenceValue = quitButton;
                serializedUi.ApplyModifiedProperties();

                if (flow.TitleRoot != originalTitleRoot || flow.CreatorRoot != originalCreatorRoot || flow.HudRoot != originalHudRoot ||
                    titleRoot.activeSelf != originalActiveState || titleRoot.transform.GetSiblingIndex() != originalSiblingIndex)
                    throw new InvalidOperationException("A preserved flow reference or TitleScreen root property changed unexpectedly.");

                EditorUtility.SetDirty(titleUi);
                EditorUtility.SetDirty(titleRoot);
                EditorSceneManager.MarkSceneDirty(scene);
                Selection.activeGameObject = titleRoot;
                Undo.CollapseUndoOperations(undoGroup);
                SceneView.RepaintAll();

                EditorUtility.DisplayDialog(
                    "Rebuild Title Screen (Win95)",
                    "The Win95 title screen is ready. Review it in the Game view, then save Assets/c.unity with Ctrl+S.",
                    "OK");
            }
            catch (Exception ex)
            {
                Undo.RevertAllDownToGroup(undoGroup);
                Debug.LogException(ex);
                EditorUtility.DisplayDialog("Rebuild Title Screen (Win95)", "The scene change was rolled back.\n\n" + ex.Message, "OK");
            }
        }

        private static bool ValidateReplaceableChildren(Transform titleRoot, out string summary)
        {
            var children = new System.Collections.Generic.List<Transform>();
            for (int i = 0; i < titleRoot.childCount; i++)
                children.Add(titleRoot.GetChild(i));

            summary = string.Join("\n", children.Select(child => "- " + child.name));

            // Both generated layouts share the root name, so this accepts the fantasy tool's
            // output and this tool's own previous output alike.
            if (children.Count == 1 && children[0].name == GeneratedRootName)
                return true;

            string[] names = children.Select(child => child.name).OrderBy(name => name).ToArray();
            string[] expected = { "Label", "Label", "NewGameButton", "QuitButton" };
            Array.Sort(expected);
            bool isLegacyLayout = names.SequenceEqual(expected);
            if (!isLegacyLayout)
            {
                EditorUtility.DisplayDialog(
                    "Rebuild Title Screen (Win95)",
                    "The TitleScreen children match neither the generated layout nor the four known legacy objects. Nothing was changed.\n\nFound:\n" + summary,
                    "OK");
            }
            return isLegacyLayout;
        }

        private static void ConfigureSpriteImports()
        {
            foreach (string path in AssetPaths)
            {
                AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
                TextureImporter importer = AssetImporter.GetAtPath(path) as TextureImporter;
                if (importer == null)
                    throw new InvalidOperationException("No TextureImporter for " + path);

                bool isBackground = path == BackgroundPath;
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.spritePixelsPerUnit = 100f;
                importer.mipmapEnabled = false;
                importer.alphaIsTransparency = !isBackground;
                importer.alphaSource = isBackground
                    ? TextureImporterAlphaSource.None
                    : TextureImporterAlphaSource.FromInput;
                importer.sRGBTexture = true;
                // Bilinear on purpose: the fat pixels are baked into the plate itself, and a
                // point filter would shimmer when the canvas scales to a phone resolution.
                importer.filterMode = FilterMode.Bilinear;
                importer.wrapMode = TextureWrapMode.Clamp;
                importer.npotScale = TextureImporterNPOTScale.None;
                importer.maxTextureSize = 2048;
                importer.textureCompression = TextureImporterCompression.CompressedHQ;
                importer.spriteBorder = Vector4.zero;
                importer.SaveAndReimport();
            }
        }

        private static Sprite LoadSprite(string path)
        {
            Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            if (sprite == null)
                throw new InvalidOperationException("Sprite failed to import: " + path);
            return sprite;
        }

        private static void BuildBackground(RectTransform parent, Sprite sprite)
        {
            RectTransform rect = CreateRect("Background", parent);
            Stretch(rect);
            Image image = rect.gameObject.AddComponent<Image>();
            image.sprite = sprite;
            image.color = Color.white;
            image.raycastTarget = false;

            AspectRatioFitter fitter = rect.gameObject.AddComponent<AspectRatioFitter>();
            fitter.aspectMode = AspectRatioFitter.AspectMode.EnvelopeParent;
            fitter.aspectRatio = sprite.rect.width / sprite.rect.height;
        }

        /// <summary>
        /// Same column geometry as TitleScreenSetup so the wordmark keeps its marked slot.
        /// The three buttons move off the column stack into the grey window that hangs
        /// below the logo; the Union Jack stays visible under everything, baked into the
        /// pixelated plate.
        /// </summary>
        private static void BuildSafeContent(
            RectTransform parent,
            Sprite logo,
            out Button continueButton,
            out Button newGameButton,
            out Button quitButton)
        {
            RectTransform safeArea = CreateRect("SafeArea", parent);
            Stretch(safeArea);
            safeArea.gameObject.AddComponent<SafeAreaFitter>();

            RectTransform column = CreateRect("CenterColumn", safeArea);
            column.anchorMin = new Vector2(0.5f, 0.5f);
            column.anchorMax = new Vector2(0.5f, 0.5f);
            column.pivot = new Vector2(0.5f, 0.5f);
            column.sizeDelta = new Vector2(660f, 700f);
            column.anchoredPosition = new Vector2(0f, 100f);

            VerticalLayoutGroup layout = column.gameObject.AddComponent<VerticalLayoutGroup>();
            layout.childAlignment = TextAnchor.UpperCenter;
            layout.childControlWidth = true;
            layout.childControlHeight = false;
            layout.childForceExpandWidth = false;
            layout.childForceExpandHeight = false;
            layout.spacing = 18f;

            // The wordmark, in the same slot and at the same height the fantasy layout used.
            CreateLogo("TitleLogo", column, logo, 240f);
            CreateSpacer(column, 40f);

            RectTransform window = CreateWindow(column, "Main Menu",
                out continueButton, out newGameButton, out quitButton);
            LayoutElement windowElement = window.gameObject.AddComponent<LayoutElement>();
            windowElement.preferredWidth = 470f;
            windowElement.preferredHeight = 330f;
        }

        private static RectTransform CreateWindow(
            RectTransform parent,
            string caption,
            out Button continueButton,
            out Button newGameButton,
            out Button quitButton)
        {
            RectTransform window = CreateRect("MenuWindow", parent);
            Image face = window.gameObject.AddComponent<Image>();
            Win95Skin.StyleWindow(face);
            Win95Skin.AddTitleBar(window, caption, 34f);

            RectTransform body = CreateRect("WindowBody", window);
            body.anchorMin = Vector2.zero;
            body.anchorMax = Vector2.one;
            // Clears the title bar (34 + 3 bevel + slack) at the top and the bevel elsewhere.
            body.offsetMin = new Vector2(18f, 16f);
            body.offsetMax = new Vector2(-18f, -48f);

            VerticalLayoutGroup bodyLayout = body.gameObject.AddComponent<VerticalLayoutGroup>();
            bodyLayout.childAlignment = TextAnchor.MiddleCenter;
            bodyLayout.childControlWidth = true;
            bodyLayout.childControlHeight = false;
            bodyLayout.childForceExpandWidth = true;
            bodyLayout.childForceExpandHeight = false;
            bodyLayout.spacing = 14f;

            continueButton = CreateButton("ContinueButton", "Continue", body);
            newGameButton = CreateButton("NewGameButton", "New Game", body);
            quitButton = CreateButton("QuitButton", "Quit", body);

            continueButton.gameObject.SetActive(false);
            return window;
        }

        private static Button CreateButton(string name, string label, RectTransform parent)
        {
            RectTransform rect = CreateRect(name, parent);
            rect.sizeDelta = new Vector2(400f, 64f);
            LayoutElement element = rect.gameObject.AddComponent<LayoutElement>();
            element.preferredWidth = 400f;
            element.preferredHeight = 64f;

            Image image = rect.gameObject.AddComponent<Image>();
            Button button = rect.gameObject.AddComponent<Button>();
            button.targetGraphic = image;

            RectTransform labelRect = CreateRect("Label", rect);
            Stretch(labelRect);
            labelRect.offsetMin = new Vector2(12f, 6f);
            labelRect.offsetMax = new Vector2(-12f, -6f);

            TextMeshProUGUI text = labelRect.gameObject.AddComponent<TextMeshProUGUI>();
            text.text = label;
            text.font = TMP_Settings.defaultFontAsset;
            text.fontStyle = FontStyles.Bold;
            text.fontSize = 28f;
            text.enableAutoSizing = true;
            text.fontSizeMin = 18f;
            text.fontSizeMax = 28f;
            text.alignment = TextAlignmentOptions.Center;

            Win95Skin.StyleButtonWithLabel(button);
            return button;
        }

        private static void CreateLogo(string name, RectTransform parent, Sprite sprite, float height)
        {
            RectTransform rect = CreateRect(name, parent);
            rect.sizeDelta = new Vector2(620f, height);
            LayoutElement element = rect.gameObject.AddComponent<LayoutElement>();
            element.preferredWidth = 620f;
            element.preferredHeight = height;

            Image image = rect.gameObject.AddComponent<Image>();
            image.sprite = sprite;
            image.preserveAspect = true;
            image.raycastTarget = false;
        }

        private static void CreateSpacer(RectTransform parent, float height)
        {
            RectTransform rect = CreateRect("ButtonSpacer", parent);
            rect.sizeDelta = new Vector2(1f, height);
            LayoutElement element = rect.gameObject.AddComponent<LayoutElement>();
            element.preferredHeight = height;
        }

        private static RectTransform CreateRect(string name, Transform parent)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            Undo.RegisterCreatedObjectUndo(go, "Create " + name);
            RectTransform rect = (RectTransform)go.transform;
            rect.SetParent(parent, false);
            go.layer = parent.gameObject.layer;
            return rect;
        }

        private static void Stretch(RectTransform rect)
        {
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.pivot = new Vector2(0.5f, 0.5f);
            rect.offsetMin = Vector2.zero;
            rect.offsetMax = Vector2.zero;
        }
    }
}
