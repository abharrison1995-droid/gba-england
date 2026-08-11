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
    /// Rebuilds the title screen as a Win95 desktop: flat teal field edge to edge, a grey
    /// taskbar with Start button and clock tray along the bottom, the GBH: England wordmark
    /// at the top, a framed St George's Cross poster on the desktop, and Continue / New Game /
    /// Quit as raised grey bevel buttons inside a navy-title-barred grey window layered over
    /// the flag's centre.
    ///
    /// The pixelated countryside plate (Big Ben towers, Union Jack baked in) is no longer
    /// referenced. Title_Background_Pixel.png stays on disk, unreferenced, so the swap can be
    /// reviewed before the file is retired; TitleScreenSetup's rollback path uses the non-pixel
    /// Title_Background.png and is unaffected.
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
        private const string LogoPath = "Assets/Textures/UI/Title/Title_Logo.png";

        // St George red (#CE1124). The flag is uGUI strips, not a texture, so it scales clean.
        private static readonly Color FlagRed = new Color(0.808f, 0.067f, 0.141f);

        private static readonly string[] AssetPaths =
        {
            LogoPath
        };

        [MenuItem("Tools/UI/Rebuild Title Screen (Win95)")]
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

                BuildDesktop(generatedRoot);
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

                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.spritePixelsPerUnit = 100f;
                importer.mipmapEnabled = false;
                importer.alphaIsTransparency = true;
                importer.alphaSource = TextureImporterAlphaSource.FromInput;
                importer.sRGBTexture = true;
                // Bilinear on purpose: a point filter would shimmer when the canvas scales
                // to a phone resolution.
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

        /// <summary>
        /// Flat Win95 desktop: teal field edge to edge plus the taskbar chrome along the
        /// bottom. Solid uGUI colour, no texture — the countryside plate is gone for good.
        /// </summary>
        private static void BuildDesktop(RectTransform parent)
        {
            RectTransform desktop = CreateRect("Desktop", parent);
            Stretch(desktop);
            Image field = desktop.gameObject.AddComponent<Image>();
            field.color = Win95Skin.Desktop;
            field.raycastTarget = false;

            BuildTaskbar(desktop);
        }

        // The taskbar chrome itself lives in Win95Skin.AddTaskbar, shared with the
        // character creator's desktop so both screens draw an identical bar.
        private static void BuildTaskbar(RectTransform parent)
        {
            Win95Skin.AddTaskbar(parent);
        }

        /// <summary>
        /// Same column geometry as TitleScreenSetup so the wordmark keeps its marked slot.
        /// The St George poster is created before the column so the logo and the grey menu
        /// window draw over it — the window sits on the flag's centre like a window over a
        /// poster pinned to the desktop.
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

            BuildFlag(safeArea);

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

        /// <summary>
        /// St George's Cross at 5:3, built from uGUI strips so it stays crisp at any phone
        /// resolution — no texture asset. Centre-anchored in the band the markup marked:
        /// its top edge just clears the wordmark slot (column top is +450, logo ends +210)
        /// and its bottom stays well clear of the taskbar. Cross-arm thickness is one fifth
        /// of the flag height, per the flag spec. Raised bevel frame so it reads as a poster
        /// sitting on the desktop; the menu window layers over its middle.
        /// </summary>
        private static void BuildFlag(RectTransform parent)
        {
            RectTransform flag = CreateRect("StGeorgeFlag", parent);
            flag.anchorMin = new Vector2(0.5f, 0.5f);
            flag.anchorMax = new Vector2(0.5f, 0.5f);
            flag.pivot = new Vector2(0.5f, 0.5f);
            flag.sizeDelta = new Vector2(800f, 480f);
            flag.anchoredPosition = new Vector2(0f, -30f);

            Image field = flag.gameObject.AddComponent<Image>();
            field.color = Color.white;
            field.raycastTarget = false;

            RectTransform vertical = CreateRect("CrossVertical", flag);
            vertical.anchorMin = new Vector2(0.44f, 0f);
            vertical.anchorMax = new Vector2(0.56f, 1f);
            vertical.offsetMin = Vector2.zero;
            vertical.offsetMax = Vector2.zero;
            Image verticalImage = vertical.gameObject.AddComponent<Image>();
            verticalImage.color = FlagRed;
            verticalImage.raycastTarget = false;

            RectTransform horizontal = CreateRect("CrossHorizontal", flag);
            horizontal.anchorMin = new Vector2(0f, 0.4f);
            horizontal.anchorMax = new Vector2(1f, 0.6f);
            horizontal.offsetMin = Vector2.zero;
            horizontal.offsetMax = Vector2.zero;
            Image horizontalImage = horizontal.gameObject.AddComponent<Image>();
            horizontalImage.color = FlagRed;
            horizontalImage.raycastTarget = false;

            Win95Skin.AddBevel(flag, sunken: false);
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
