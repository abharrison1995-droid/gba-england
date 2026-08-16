using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using GBHEngland.Flow;
using GBHEngland.UI;

/// <summary>Replaces only the authored children of the existing title root.</summary>
public static class TitleScreenSetup
{
    private const string ScenePath = "Assets/c.unity";
    private const string GeneratedRootName = "GeneratedTitleLayout";
    private const string BackgroundPath = "Assets/Textures/UI/Title/Title_Background.png";
    private const string ButtonFramePath = "Assets/Textures/UI/Title/Title_Button_Frame.png";

    // The wordmark, keyed off its magenta plate by Tools/key_logo.py. Listing it here is what
    // gives it the missing-asset guard and the import settings; every branch in
    // ConfigureSpriteImports already resolves correctly for it.
    private const string LogoPath = "Assets/Textures/UI/Title/Title_Logo.png";

    private static readonly string[] AssetPaths =
    {
        BackgroundPath,
        ButtonFramePath,
        LogoPath
    };

    [MenuItem("Tools/Danger Zone/Apply New Title Screen")]
    public static void ApplyNewTitleScreen()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
        {
            EditorUtility.DisplayDialog("Apply New Title Screen", "Exit Play mode before changing the scene.", "OK");
            return;
        }

        Scene scene = SceneManager.GetActiveScene();
        if (scene.path != ScenePath)
        {
            EditorUtility.DisplayDialog(
                "Apply New Title Screen",
                "Open Assets/c.unity first. This tool will not open or replace a scene automatically.",
                "OK");
            return;
        }

        string missing = AssetPaths.FirstOrDefault(path => !File.Exists(path));
        if (missing != null)
        {
            EditorUtility.DisplayDialog("Apply New Title Screen", "Required asset is missing:\n" + missing, "OK");
            return;
        }

        GameFlowController[] flows = UnityEngine.Object.FindObjectsOfType<GameFlowController>(true);
        if (flows.Length != 1)
        {
            EditorUtility.DisplayDialog(
                "Apply New Title Screen",
                "Expected exactly one GameFlowController in Assets/c.unity; found " + flows.Length + ".",
                "OK");
            return;
        }

        GameFlowController flow = flows[0];
        GameObject titleRoot = flow.TitleRoot;
        if (titleRoot == null || titleRoot.GetComponent<RectTransform>() == null)
        {
            EditorUtility.DisplayDialog("Apply New Title Screen", "GameFlowController.TitleRoot is missing or is not UI.", "OK");
            return;
        }

        TitleScreenUI titleUi = titleRoot.GetComponent<TitleScreenUI>();
        if (titleUi == null)
        {
            EditorUtility.DisplayDialog("Apply New Title Screen", "The preserved TitleRoot has no TitleScreenUI component.", "OK");
            return;
        }

        Transform generated = titleRoot.transform.Find(GeneratedRootName);
        if (!ValidateReplaceableChildren(titleRoot.transform, generated != null, out string childSummary))
            return;

        if (!EditorUtility.DisplayDialog(
                "Apply New Title Screen",
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
            EditorUtility.DisplayDialog("Apply New Title Screen", "Sprite import failed. The scene was not changed.\n\n" + ex.Message, "OK");
            return;
        }

        Sprite background = LoadSprite(BackgroundPath);
        Sprite buttonFrame = LoadSprite(ButtonFramePath);
        Sprite logo = LoadSprite(LogoPath);

        GameObject originalTitleRoot = flow.TitleRoot;
        GameObject originalCreatorRoot = flow.CreatorRoot;
        GameObject originalHudRoot = flow.HudRoot;
        bool originalActiveState = titleRoot.activeSelf;
        int originalSiblingIndex = titleRoot.transform.GetSiblingIndex();

        Undo.IncrementCurrentGroup();
        int undoGroup = Undo.GetCurrentGroup();
        Undo.SetCurrentGroupName("Apply New Title Screen");

        try
        {
            Undo.RegisterFullObjectHierarchyUndo(titleRoot, "Apply New Title Screen");

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
            BuildDecorations(generatedRoot);
            BuildSafeContent(generatedRoot, buttonFrame, logo, out Button continueButton, out Button newGameButton, out Button quitButton);

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
                "Apply New Title Screen",
                "The new title hierarchy is ready. Review it in the Game view, then save Assets/c.unity with Ctrl+S.",
                "OK");
        }
        catch (Exception ex)
        {
            Undo.RevertAllDownToGroup(undoGroup);
            Debug.LogException(ex);
            EditorUtility.DisplayDialog("Apply New Title Screen", "The scene change was rolled back.\n\n" + ex.Message, "OK");
        }
    }

    private static bool ValidateReplaceableChildren(Transform titleRoot, bool hasGeneratedRoot, out string summary)
    {
        var children = new List<Transform>();
        for (int i = 0; i < titleRoot.childCount; i++)
            children.Add(titleRoot.GetChild(i));

        if (hasGeneratedRoot)
        {
            bool valid = children.Count == 1 && children[0].name == GeneratedRootName;
            summary = valid ? "- " + GeneratedRootName + " (previous generated layout)" : string.Empty;
            if (!valid)
            {
                EditorUtility.DisplayDialog(
                    "Apply New Title Screen",
                    "A generated layout exists alongside unexpected TitleScreen children. Resolve them manually; nothing was changed.",
                    "OK");
            }
            return valid;
        }

        string[] names = children.Select(child => child.name).OrderBy(name => name).ToArray();
        string[] expected = { "Label", "Label", "NewGameButton", "QuitButton" };
        Array.Sort(expected);
        bool isLegacyLayout = names.SequenceEqual(expected);
        summary = string.Join("\n", children.Select(child => "- " + child.name));
        if (!isLegacyLayout)
        {
            EditorUtility.DisplayDialog(
                "Apply New Title Screen",
                "The TitleScreen children no longer match the four known legacy objects. Nothing was changed.\n\nFound:\n" + summary,
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
            importer.spritePixelsPerUnit = path == ButtonFramePath ? 400f : 100f;
            importer.mipmapEnabled = false;
            importer.alphaIsTransparency = path != BackgroundPath;
            importer.alphaSource = path == BackgroundPath
                ? TextureImporterAlphaSource.None
                : TextureImporterAlphaSource.FromInput;
            importer.sRGBTexture = true;
            importer.filterMode = FilterMode.Bilinear;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.maxTextureSize = 2048;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
            importer.spriteBorder = path == ButtonFramePath
                ? new Vector4(190f, 115f, 190f, 115f)
                : Vector4.zero;
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
    /// Deliberately places nothing. The countryside plate in Title_Background.png already
    /// carries the clock towers and the flag, so drawing them again would double them. The
    /// old overlay sprites (green-suited mice, Mr Hood idle still, flag banner) were deleted
    /// with the abandoned alley direction.
    ///
    /// The character creator uses its own plate (Creator_Background.png — same composition,
    /// gothic spires instead of clock towers) and likewise draws no towers or flag of its own,
    /// which is why they belong in the plate rather than here.
    ///
    /// To go back to a composited title — separate background, towers, flag — restore the
    /// CreateDecoration helper and its calls from this method's history and supply a plate
    /// with none of them baked in.
    /// </summary>
    private static void BuildDecorations(RectTransform parent)
    {
        RectTransform layer = CreateRect("DecorativeLayer", parent);
        Stretch(layer);
    }

    private static void BuildSafeContent(
        RectTransform parent,
        Sprite buttonFrame,
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
        // Raised from 70 so the taller wordmark row centres on the marked box instead of growing
        // downward into the buttons. See the arithmetic in the note by CreateLogo.
        column.anchoredPosition = new Vector2(0f, 134f);

        VerticalLayoutGroup layout = column.gameObject.AddComponent<VerticalLayoutGroup>();
        layout.childAlignment = TextAnchor.UpperCenter;
        layout.childControlWidth = true;
        layout.childControlHeight = false;
        layout.childForceExpandWidth = false;
        layout.childForceExpandHeight = false;
        layout.spacing = 18f;

        // The wordmark replaces the TMP title, sized to the box the owner marked on a title
        // screenshot: 240 tall draws it ~520 wide, which sits inside that box on all four sides.
        // It cannot fill the box — the box is 2.85:1 and the plate is 2.166:1, so height binds
        // and there is slack at the sides whatever height is chosen.
        //
        // These three numbers move together. Change one and recompute the others:
        //   anchoredPosition.y 134  puts the column's top edge 134 + 350 = 484 above centre,
        //                           which centres a 240 row on the marked box (+488 to +239)
        //   240 + 18 + 49 + 18 = 325 of stack sits above Continue
        //   so Continue's top stays at 484 - 325 = 159 above centre, which is exactly where
        //   420 - (105 + 18 + 120 + 18) put it before. The buttons do not move at all.
        CreateLogo("TitleLogo", column, logo, 240f);
        CreateSpacer(column, 49f);

        continueButton = CreateButton("ContinueButton", "Continue", column, buttonFrame);
        newGameButton = CreateButton("NewGameButton", "New Game", column, buttonFrame);
        quitButton = CreateButton("QuitButton", "Quit", column, buttonFrame);

        continueButton.gameObject.SetActive(false);
    }

    /// <summary>
    /// The wordmark, in the slot the TMP title used to hold.
    ///
    /// preserveAspect fits the plate inside the row, and the plate is far wider than it is tall,
    /// so the row *height* is what sets the drawn size — the 620 preferred width only caps it,
    /// and at any height this logo is drawn at, it never binds. Growing the logo has to be paid
    /// for out of the spacer below and the column's offset above, or the buttons move.
    ///
    /// <c>EKVibe.DisplayTitle</c> is untouched and still the project's title constant. It is
    /// simply no longer the thing drawn here.
    /// </summary>
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

    private static Button CreateButton(string name, string label, RectTransform parent, Sprite frame)
    {
        RectTransform rect = CreateRect(name, parent);
        rect.sizeDelta = new Vector2(440f, 82f);
        LayoutElement element = rect.gameObject.AddComponent<LayoutElement>();
        element.preferredWidth = 440f;
        element.preferredHeight = 82f;

        Image image = rect.gameObject.AddComponent<Image>();
        image.sprite = frame;
        image.type = Image.Type.Sliced;
        image.fillCenter = true;

        Button button = rect.gameObject.AddComponent<Button>();
        button.targetGraphic = image;
        ColorBlock colors = ColorBlock.defaultColorBlock;
        colors.normalColor = Color.white;
        colors.highlightedColor = new Color(1.08f, 1.03f, 0.88f, 1f);
        colors.pressedColor = new Color(0.72f, 0.68f, 0.58f, 1f);
        colors.selectedColor = colors.highlightedColor;
        colors.disabledColor = new Color(0.45f, 0.45f, 0.45f, 0.65f);
        colors.fadeDuration = 0.08f;
        button.colors = colors;

        RectTransform labelRect = CreateRect("Label", rect);
        Stretch(labelRect);
        labelRect.offsetMin = new Vector2(28f, 8f);
        labelRect.offsetMax = new Vector2(-28f, -8f);

        TextMeshProUGUI text = labelRect.gameObject.AddComponent<TextMeshProUGUI>();
        text.text = label;
        text.font = TMP_Settings.defaultFontAsset;
        text.fontStyle = FontStyles.Bold;
        text.fontSize = 34f;
        text.enableAutoSizing = true;
        text.fontSizeMin = 22f;
        text.fontSizeMax = 34f;
        text.alignment = TextAlignmentOptions.Center;
        text.color = new Color(0.80f, 0.72f, 0.59f, 1f);
        text.outlineColor = new Color32(20, 14, 10, 230);
        text.outlineWidth = 0.16f;
        text.raycastTarget = false;
        return button;
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
