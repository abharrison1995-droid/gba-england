using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

/// <summary>Replaces only the authored children of the existing character-creator root.</summary>
public static class CharacterCreatorSetup
{
    private const string ScenePath = "Assets/c.unity";
    private const string GeneratedRootName = "GeneratedCharacterCreator";
    private const string BackgroundPath = "Assets/Textures/UI/Title/Creator_Background.png";
    private const string ButtonFramePath = "Assets/Textures/UI/Title/Title_Button_Frame.png";

    // The mockup's details panel is a parchment scroll: flat parchment slab, dark text.
    private static readonly Color Parchment = new Color(0.93f, 0.87f, 0.70f, 0.96f);
    private static readonly Color ParchmentInk = new Color(0.25f, 0.16f, 0.09f, 1f);

    // The slab is framed rather than floating: dark wood edge, gilt line inside it. Same
    // treatment as the button and tab plaques, built from flat colour rather than the sliced
    // frame sprite so it stays crisp at any panel size.
    private static readonly Color DetailsBorder = new Color(0.16f, 0.11f, 0.07f, 0.98f);
    private static readonly Color DetailsEdgeGold = new Color(0.72f, 0.60f, 0.38f, 1f);

    // The intro slab is the inverse of the details slab: brown body, light brown trim. The body
    // is the same colour as the slabs painted into Creator_Background.png, sampled from the art
    // at (57, 47, 36), so it reads as part of the same set rather than a UI box laid over it.
    private static readonly Color IntroBody = new Color(0.224f, 0.184f, 0.141f, 0.97f);
    private static readonly Color IntroTrim = new Color(0.62f, 0.50f, 0.34f, 1f);

    /// <summary>
    /// The owner's intro copy, supplied 2026-08-05. Hoisted to a constant so it can be edited
    /// without reading the layout code around it.
    ///
    /// ⚠️ Straight apostrophes, deliberately. TMP's default static atlas is often ASCII-only —
    /// the same reason £ is flagged in CLAUDE.md §5 — and a curly U+2019 would render as a
    /// missing-glyph box. Keep them straight unless the font asset is switched to Dynamic.
    /// </summary>
    private const string IntroCopy =
        "It's time for GBH: England. Are you ready? Magic? Police? Fascists? It's all here!\n\n" +
        "Dive in! Pick one of five classes and discover the real England!";

    // The slab the character stands against: the parchment's darker cousin, so it reads as the
    // same material without competing with the details panel for attention.
    private static readonly Color SpriteBackdropFill = new Color(0.70f, 0.63f, 0.48f, 0.96f);
    private static readonly Color SpriteBackdropTrim = new Color(0.33f, 0.23f, 0.14f, 1f);

    [MenuItem("Tools/Danger Zone/Apply New Character Creator")]
    public static void ApplyNewCharacterCreator()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
        {
            EditorUtility.DisplayDialog("Apply New Character Creator", "Exit Play mode before changing the scene.", "OK");
            return;
        }

        Scene scene = SceneManager.GetActiveScene();
        if (scene.path != ScenePath)
        {
            EditorUtility.DisplayDialog("Apply New Character Creator", "Open Assets/c.unity first.", "OK");
            return;
        }

        GameFlowController[] flows = UnityEngine.Object.FindObjectsOfType<GameFlowController>(true);
        if (flows.Length != 1)
        {
            EditorUtility.DisplayDialog("Apply New Character Creator",
                "Expected exactly one GameFlowController; found " + flows.Length + ".", "OK");
            return;
        }

        GameFlowController flow = flows[0];
        GameObject creatorRoot = flow.CreatorRoot;
        RectTransform creatorRect = creatorRoot != null ? creatorRoot.GetComponent<RectTransform>() : null;
        CharacterCreatorUI creatorUi = creatorRoot != null ? creatorRoot.GetComponent<CharacterCreatorUI>() : null;
        if (creatorRect == null || creatorUi == null || creatorRoot.GetComponentInParent<Canvas>() == null)
        {
            EditorUtility.DisplayDialog("Apply New Character Creator",
                "GameFlowController.CreatorRoot must be the existing UI root with CharacterCreatorUI.", "OK");
            return;
        }

        if (!File.Exists(BackgroundPath) || !File.Exists(ButtonFramePath))
        {
            EditorUtility.DisplayDialog("Apply New Character Creator",
                "The creator background or button frame is missing from Assets/Textures/UI/Title.", "OK");
            return;
        }

        if (!ValidateChildren(creatorRoot.transform, out string summary)) return;
        if (!EditorUtility.DisplayDialog("Apply New Character Creator",
                "This replaces these CharacterCreator children:\n\n" + summary +
                "\n\nThe root, Canvas, title, HUD, and GameFlow references are preserved. Undo is supported.",
                "Apply", "Cancel")) return;

        try
        {
            ConfigureSprite(BackgroundPath, false);
            ConfigureSprite(ButtonFramePath, true);
        }
        catch (Exception ex)
        {
            Debug.LogException(ex);
            EditorUtility.DisplayDialog("Apply New Character Creator",
                "Sprite import failed; the scene was not changed.\n\n" + ex.Message, "OK");
            return;
        }

        Sprite background = LoadSprite(BackgroundPath);
        Sprite frame = LoadSprite(ButtonFramePath);
        GameObject originalTitle = flow.TitleRoot;
        GameObject originalCreator = flow.CreatorRoot;
        GameObject originalHud = flow.HudRoot;
        bool originalActive = creatorRoot.activeSelf;
        int originalSibling = creatorRoot.transform.GetSiblingIndex();

        Undo.IncrementCurrentGroup();
        int undoGroup = Undo.GetCurrentGroup();
        Undo.SetCurrentGroupName("Apply New Character Creator");

        try
        {
            Undo.RegisterFullObjectHierarchyUndo(creatorRoot, "Apply New Character Creator");
            for (int i = creatorRoot.transform.childCount - 1; i >= 0; i--)
                Undo.DestroyObjectImmediate(creatorRoot.transform.GetChild(i).gameObject);

            Image oldPanel = creatorRoot.GetComponent<Image>();
            if (oldPanel != null)
            {
                Undo.RecordObject(oldPanel, "Clear legacy creator panel");
                oldPanel.color = Color.clear;
                oldPanel.raycastTarget = false;
            }

            RectTransform generated = CreateRect(GeneratedRootName, creatorRoot.transform);
            Stretch(generated);
            BuildBackground(generated, background);
            CreatorReferences refs = BuildContent(generated, frame);

            PlayerClassVisualLibrary library = flow.GetComponent<PlayerClassVisualLibrary>();
            if (library == null)
                library = Undo.AddComponent<PlayerClassVisualLibrary>(flow.gameObject);
            var artReport = new List<string>();
            ArtImportTool.PopulatePlayerClassVisualLibrary(library, artReport);
            refs.Preview.Library = library;

            SerializedObject ui = new SerializedObject(creatorUi);
            ui.FindProperty("NameInput").objectReferenceValue = refs.NameInput;
            ui.FindProperty("ClassTitle").objectReferenceValue = refs.ClassTitle;
            ui.FindProperty("ClassBlurb").objectReferenceValue = refs.ClassBlurb;
            ui.FindProperty("StatsPreview").objectReferenceValue = refs.Stats;
            ui.FindProperty("WeaponPreview").objectReferenceValue = refs.Weapon;
            SerializedProperty buttons = ui.FindProperty("ClassButtons");
            buttons.arraySize = refs.ClassButtons.Length;
            for (int i = 0; i < refs.ClassButtons.Length; i++)
                buttons.GetArrayElementAtIndex(i).objectReferenceValue = refs.ClassButtons[i];
            ui.FindProperty("ConfirmButton").objectReferenceValue = refs.Confirm;
            ui.FindProperty("BackButton").objectReferenceValue = refs.Back;
            ui.FindProperty("Preview").objectReferenceValue = refs.Preview;
            ui.ApplyModifiedProperties();

            SerializedObject serializedFlow = new SerializedObject(flow);
            serializedFlow.FindProperty("ClassVisuals").objectReferenceValue = library;
            serializedFlow.ApplyModifiedProperties();

            if (flow.TitleRoot != originalTitle || flow.CreatorRoot != originalCreator || flow.HudRoot != originalHud ||
                creatorRoot.activeSelf != originalActive || creatorRoot.transform.GetSiblingIndex() != originalSibling)
                throw new InvalidOperationException("A preserved flow reference or creator-root property changed.");

            EditorUtility.SetDirty(creatorUi);
            EditorUtility.SetDirty(library);
            EditorUtility.SetDirty(flow);
            EditorSceneManager.MarkSceneDirty(scene);
            Selection.activeGameObject = creatorRoot;
            Undo.CollapseUndoOperations(undoGroup);
            SceneView.RepaintAll();
            EditorUtility.DisplayDialog("Apply New Character Creator",
                "The generated creator is ready. Review it in Game view, then save Assets/c.unity with Ctrl+S.", "OK");
        }
        catch (Exception ex)
        {
            Undo.RevertAllDownToGroup(undoGroup);
            Debug.LogException(ex);
            EditorUtility.DisplayDialog("Apply New Character Creator", "The scene change was rolled back.\n\n" + ex.Message, "OK");
        }
    }

    private static bool ValidateChildren(Transform root, out string summary)
    {
        Transform generated = root.Find(GeneratedRootName);
        summary = string.Join("\n", Enumerable.Range(0, root.childCount)
            .Select(i => "- " + root.GetChild(i).name));
        if (generated != null)
        {
            bool validGenerated = root.childCount == 1 && root.GetChild(0) == generated;
            if (!validGenerated)
                EditorUtility.DisplayDialog("Apply New Character Creator",
                    "GeneratedCharacterCreator exists beside unexpected children; nothing changed.", "OK");
            return validGenerated;
        }

        string[] expected =
        {
            "BackButton", "Class0", "Class1", "Class2", "Class3", "ConfirmButton",
            "Label", "Label", "Label", "Label", "Label", "NameInput"
        };
        string[] actual = Enumerable.Range(0, root.childCount).Select(i => root.GetChild(i).name).ToArray();
        Array.Sort(expected);
        Array.Sort(actual);
        bool validLegacy = actual.SequenceEqual(expected);
        if (!validLegacy)
            EditorUtility.DisplayDialog("Apply New Character Creator",
                "Creator children are neither the known 12-object legacy layout nor exactly GeneratedCharacterCreator. Nothing changed.\n\n" + summary,
                "OK");
        return validLegacy;
    }

    private static void ConfigureSprite(string path, bool button)
    {
        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
        TextureImporter importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null) throw new InvalidOperationException("No TextureImporter for " + path);
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Single;
        importer.spritePixelsPerUnit = button ? 400f : 100f;
        importer.mipmapEnabled = false;
        importer.alphaSource = button ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None;
        importer.alphaIsTransparency = button;
        importer.sRGBTexture = true;
        importer.filterMode = FilterMode.Bilinear;
        importer.wrapMode = TextureWrapMode.Clamp;
        importer.npotScale = TextureImporterNPOTScale.None;
        importer.maxTextureSize = 2048;
        importer.textureCompression = TextureImporterCompression.CompressedHQ;
        importer.spriteBorder = button ? new Vector4(190f, 115f, 190f, 115f) : Vector4.zero;
        importer.SaveAndReimport();
    }

    private static Sprite LoadSprite(string path)
    {
        Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
        if (sprite == null) throw new InvalidOperationException("Sprite failed to import: " + path);
        return sprite;
    }

    private static void BuildBackground(RectTransform parent, Sprite sprite)
    {
        RectTransform rect = CreateRect("Background", parent);
        Stretch(rect);
        Image image = rect.gameObject.AddComponent<Image>();
        image.sprite = sprite;
        image.raycastTarget = false;
        AspectRatioFitter fitter = rect.gameObject.AddComponent<AspectRatioFitter>();
        fitter.aspectMode = AspectRatioFitter.AspectMode.EnvelopeParent;
        fitter.aspectRatio = sprite.rect.width / sprite.rect.height;

        RectTransform veil = CreateRect("DarkVeil", parent);
        Stretch(veil);
        Image veilImage = veil.gameObject.AddComponent<Image>();
        veilImage.color = new Color(0.025f, 0.035f, 0.045f, 0.3f);
        veilImage.raycastTarget = false;
    }

    private static CreatorReferences BuildContent(RectTransform parent, Sprite frame)
    {
        RectTransform safe = CreateRect("SafeArea", parent);
        Stretch(safe);
        safe.gameObject.AddComponent<SafeAreaFitter>();

        // The heading sits above the brown box painted into the backdrop, whose top edge is at
        // y 0.854, so it lands on pale sky where tan text has little to hold on to. It does not
        // get moved onto the box: the strip between the box top and the details panels is 226
        // units and already carries the name field (81) and the tabs (92), so a third row would
        // mean shrinking all three. It gets its own plate instead — same treatment as the intro
        // panel, so it reads as deliberate rather than as a label that missed its backing.
        //
        // Created before the heading: Unity UI draws in hierarchy order.
        RectTransform headingPlate = CreatePanel("HeadingPlate", safe, IntroTrim);
        SetAnchors(headingPlate, new Vector2(0.33f, 0.873f), new Vector2(0.67f, 0.977f));
        RectTransform headingPlateBody = CreatePanel("HeadingPlateBody", headingPlate, IntroBody);
        Stretch(headingPlateBody);
        headingPlateBody.offsetMin = new Vector2(5f, 5f);
        headingPlateBody.offsetMax = new Vector2(-5f, -5f);

        TextMeshProUGUI heading = CreateText("Heading", safe, "Pick your Brit", 58f, FontStyles.Bold);
        SetAnchors(heading.rectTransform, new Vector2(0.14f, 0.88f), new Vector2(0.86f, 0.97f));

        TMP_InputField nameInput = CreateNameInput(safe, frame);
        SetAnchors(nameInput.GetComponent<RectTransform>(), new Vector2(0.34f, 0.79f), new Vector2(0.66f, 0.865f));

        // Narrowed from 0.04-0.96 to sit inside the backdrop's brown box (0.167-0.848), which the
        // outer two tabs used to overhang onto the countryside. Each tab drops from ~344 units
        // wide to ~246; the labels auto-size, and "Bunda Basher" is the longest at 12 characters.
        RectTransform tabs = CreateRect("ClassTabs", safe);
        SetAnchors(tabs, new Vector2(0.175f, 0.68f), new Vector2(0.84f, 0.765f));
        HorizontalLayoutGroup tabLayout = tabs.gameObject.AddComponent<HorizontalLayoutGroup>();
        tabLayout.spacing = 12f;
        tabLayout.childControlWidth = true;
        tabLayout.childControlHeight = true;
        tabLayout.childForceExpandWidth = true;
        tabLayout.childForceExpandHeight = true;
        string[] names = { "Young Driller", "Stabmeister", "Mr Hood", "Dynamo", "Bunda Basher" };
        Button[] classButtons = names.Select((label, i) => CreateButton("Class" + i, label, tabs, frame, 26f)).ToArray();

        // Details and Preview are anchored to SafeArea directly instead of sharing a
        // HorizontalLayoutGroup. Under the layout group the preview's position was whatever was
        // left over once TMP had decided how wide the parchment wanted to be, so changing the
        // panel silently moved the character. The two are now independent.
        RectTransform details = CreatePanel("Details", safe, DetailsBorder);
        SetAnchors(details, new Vector2(0.16f, 0.215f), new Vector2(0.48f, 0.645f));

        RectTransform detailsEdge = CreatePanel("DetailsEdge", details, DetailsEdgeGold);
        Stretch(detailsEdge);
        detailsEdge.offsetMin = new Vector2(8f, 8f);
        detailsEdge.offsetMax = new Vector2(-8f, -8f);

        RectTransform parchment = CreatePanel("Parchment", detailsEdge, Parchment);
        Stretch(parchment);
        parchment.offsetMin = new Vector2(3f, 3f);
        parchment.offsetMax = new Vector2(-3f, -3f);

        VerticalLayoutGroup detailsLayout = parchment.gameObject.AddComponent<VerticalLayoutGroup>();
        // Padding is lighter than it was because the 11px border now supplies the visual margin.
        detailsLayout.padding = new RectOffset(20, 20, 16, 16);
        detailsLayout.spacing = 12f;
        // Any slack is split above and below rather than pooling under the last row.
        detailsLayout.childAlignment = TextAnchor.MiddleCenter;
        detailsLayout.childControlWidth = true;
        // ScaleWithScreenSize is width-matched, so 20:9 phones expose fewer canvas units
        // vertically than 16:9. Let the layout shrink these auto-sized text rows instead of
        // preserving their 16:9 preferred heights and spilling into the footer.
        detailsLayout.childControlHeight = true;
        detailsLayout.childForceExpandWidth = true;
        detailsLayout.childForceExpandHeight = false;

        TextMeshProUGUI classTitle = CreateText("ClassTitle", parchment, PlayerClassInfo.DisplayName(PlayerClass.YoungDriller), 42f, FontStyles.Bold, 68f, ParchmentInk);
        TextMeshProUGUI blurb = CreateText("ClassBlurb", parchment, PlayerClassInfo.Tagline(PlayerClass.YoungDriller), 25f, FontStyles.Normal, 86f, ParchmentInk);
        blurb.enableWordWrapping = true;
        TextMeshProUGUI weapon = CreateText("WeaponPreview", parchment, "Specialises in: " + PlayerClassInfo.SpecialismLabel(PlayerClass.YoungDriller), 25f, FontStyles.Bold, 54f, ParchmentInk);
        TextMeshProUGUI stats = CreateText("StatsPreview", parchment, StatsText(PlayerClass.YoungDriller), 24f, FontStyles.Normal, 150f, ParchmentInk);

        // The intro slab, sharing the details slab's vertical extent so the two read as a pair.
        // Its copy is the owner's own (CLAUDE.md §3) and lives in IntroCopy above.
        RectTransform intro = CreatePanel("IntroPanel", safe, IntroTrim);
        SetAnchors(intro, new Vector2(0.50f, 0.215f), new Vector2(0.695f, 0.645f));

        RectTransform introBody = CreatePanel("IntroBody", intro, IntroBody);
        Stretch(introBody);
        introBody.offsetMin = new Vector2(5f, 5f);
        introBody.offsetMax = new Vector2(-5f, -5f);

        // One stretched text rather than a layout group: a single block needs no stacking, and
        // TMP's auto-sizing and a layout group's height negotiation fight each other. Filling a
        // fixed rect means auto-sizing alone decides, so copy of any length shrinks to fit
        // instead of overflowing the panel.
        // No colour argument on purpose: CreateText's default is the light tan used elsewhere on
        // the scenery, with a dark outline. Passing an explicit colour would switch the outline
        // to the pale one meant for dark ink on parchment, which vanishes on a brown panel.
        TextMeshProUGUI introText = CreateText("IntroText", introBody, IntroCopy, 25f, FontStyles.Normal);
        Stretch(introText.rectTransform);
        introText.rectTransform.offsetMin = new Vector2(22f, 22f);
        introText.rectTransform.offsetMax = new Vector2(-22f, -22f);
        introText.enableWordWrapping = true;
        introText.alignment = TextAlignmentOptions.Top;

        // The slab behind the character.
        //
        // ⚠️ Created *before* Preview on purpose. Unity UI draws in hierarchy order, so a sibling
        // meant to sit behind the sprite has to exist first. Move this below Preview and it
        // covers the character instead.
        //
        // Centred on x 0.80 — the same axis as Preview — and stopping at 0.845 so its right edge
        // stays inside the brown box painted into Creator_Background.png, which ends at ~0.85.
        // Narrower than the sprite's drawn square (0.6885-0.9115), which is mostly transparent
        // padding: the visible figure only spans about 0.765-0.835, so it still clears the trim.
        RectTransform spriteBack = CreatePanel("SpriteBackdrop", safe, SpriteBackdropTrim);
        SetAnchors(spriteBack, new Vector2(0.755f, 0.195f), new Vector2(0.845f, 0.645f));

        RectTransform spriteBackBody = CreatePanel("SpriteBackdropBody", spriteBack, SpriteBackdropFill);
        Stretch(spriteBackBody);
        spriteBackBody.offsetMin = new Vector2(6f, 6f);
        spriteBackBody.offsetMax = new Vector2(-6f, -6f);

        // The preview panel itself stays transparent: the sprite reads against SpriteBackdrop,
        // which is a separate rect, so this one only positions and sizes the character.
        //
        // Centred on x 0.80, the same axis as SpriteBackdrop. Deliberately wider than it is
        // tall — the idle sprites are square, so preserveAspect must keep fitting them by
        // height; a narrower rect would fit by width instead and shrink the character. That is
        // why it is 0.66–0.94 while the slab behind it is only 0.755–0.845: most of this rect is
        // the sprite sheet's transparent padding, not the figure.
        RectTransform previewPanel = CreatePanel("Preview", safe, new Color(1f, 1f, 1f, 0f));
        SetAnchors(previewPanel, new Vector2(0.66f, 0.20f), new Vector2(0.94f, 0.65f));
        RectTransform previewRect = CreateRect("CharacterImage", previewPanel);
        SetAnchors(previewRect, new Vector2(0.08f, 0.06f), new Vector2(0.92f, 0.94f));
        Image previewImage = previewRect.gameObject.AddComponent<Image>();
        previewImage.preserveAspect = true;
        previewImage.raycastTarget = false;
        TextMeshProUGUI pending = CreateText("PendingLabel", previewPanel, "Visual pending", 28f, FontStyles.Italic, -1f, ParchmentInk);
        Stretch(pending.rectTransform);
        PlayerClassPreviewUI preview = previewPanel.gameObject.AddComponent<PlayerClassPreviewUI>();
        preview.PreviewImage = previewImage;
        preview.PendingLabel = pending;

        RectTransform footer = CreateRect("Footer", safe);
        SetAnchors(footer, new Vector2(0.34f, 0.025f), new Vector2(0.66f, 0.18f));
        VerticalLayoutGroup footerLayout = footer.gameObject.AddComponent<VerticalLayoutGroup>();
        footerLayout.spacing = 10f;
        footerLayout.childControlWidth = true;
        footerLayout.childControlHeight = true;
        footerLayout.childForceExpandWidth = true;
        footerLayout.childForceExpandHeight = true;
        Button confirm = CreateButton("ConfirmButton", "Enter Manor Cellars", footer, frame, 29f);
        Button back = CreateButton("BackButton", "Back", footer, frame, 29f);

        return new CreatorReferences
        {
            NameInput = nameInput,
            ClassTitle = classTitle,
            ClassBlurb = blurb,
            Weapon = weapon,
            Stats = stats,
            ClassButtons = classButtons,
            Confirm = confirm,
            Back = back,
            Preview = preview
        };
    }

    private static TMP_InputField CreateNameInput(RectTransform parent, Sprite frame)
    {
        RectTransform root = CreateRect("NameInput", parent);
        Image background = root.gameObject.AddComponent<Image>();
        background.sprite = frame;
        background.type = Image.Type.Sliced;
        TMP_InputField input = root.gameObject.AddComponent<TMP_InputField>();

        RectTransform viewport = CreateRect("TextArea", root);
        Stretch(viewport);
        viewport.offsetMin = new Vector2(32f, 8f);
        viewport.offsetMax = new Vector2(-32f, -8f);
        viewport.gameObject.AddComponent<RectMask2D>();

        TextMeshProUGUI placeholder = CreateText("Placeholder", viewport, "Player name here!", 28f, FontStyles.Italic);
        Stretch(placeholder.rectTransform);
        placeholder.color = new Color(0.7f, 0.66f, 0.58f, 0.65f);
        placeholder.alignment = TextAlignmentOptions.Left;
        TextMeshProUGUI text = CreateText("Text", viewport, "", 28f, FontStyles.Normal);
        Stretch(text.rectTransform);
        text.alignment = TextAlignmentOptions.Left;

        input.textViewport = viewport;
        input.textComponent = text;
        input.placeholder = placeholder;
        input.lineType = TMP_InputField.LineType.SingleLine;
        input.characterLimit = 24;
        // Empty on purpose, so the placeholder shows. A prefilled value would have to be
        // deleted before typing, and anyone who did not would start the game under it.
        input.text = "";
        return input;
    }

    private static Button CreateButton(string name, string label, RectTransform parent, Sprite frame, float fontSize)
    {
        RectTransform rect = CreateRect(name, parent);
        Image image = rect.gameObject.AddComponent<Image>();
        image.sprite = frame;
        image.type = Image.Type.Sliced;
        Button button = rect.gameObject.AddComponent<Button>();
        button.targetGraphic = image;
        ColorBlock colors = ColorBlock.defaultColorBlock;
        colors.highlightedColor = new Color(1f, 0.93f, 0.78f, 1f);
        colors.pressedColor = new Color(0.72f, 0.66f, 0.56f, 1f);
        colors.selectedColor = colors.highlightedColor;
        button.colors = colors;
        TextMeshProUGUI text = CreateText("Label", rect, label, fontSize, FontStyles.Bold);
        Stretch(text.rectTransform);
        text.rectTransform.offsetMin = new Vector2(18f, 7f);
        text.rectTransform.offsetMax = new Vector2(-18f, -7f);
        return button;
    }

    private static RectTransform CreatePanel(string name, RectTransform parent, Color color, Sprite frame = null)
    {
        RectTransform rect = CreateRect(name, parent);
        Image image = rect.gameObject.AddComponent<Image>();
        image.color = color;
        if (frame != null)
        {
            image.sprite = frame;
            image.type = Image.Type.Sliced;
        }
        return rect;
    }

    private static TextMeshProUGUI CreateText(string name, RectTransform parent, string value,
        float size, FontStyles style, float preferredHeight = -1f, Color? color = null)
    {
        RectTransform rect = CreateRect(name, parent);
        if (preferredHeight > 0f)
        {
            rect.sizeDelta = new Vector2(0f, preferredHeight);
            LayoutElement element = rect.gameObject.AddComponent<LayoutElement>();
            element.preferredHeight = preferredHeight;
        }
        TextMeshProUGUI text = rect.gameObject.AddComponent<TextMeshProUGUI>();
        text.text = value;
        text.font = TMP_Settings.defaultFontAsset;
        text.fontSize = size;
        text.enableAutoSizing = true;
        text.fontSizeMin = Mathf.Max(16f, size * 0.65f);
        text.fontSizeMax = size;
        text.fontStyle = style;
        text.alignment = TextAlignmentOptions.Center;
        text.color = color ?? new Color(0.82f, 0.74f, 0.61f, 1f);
        text.outlineColor = color.HasValue
            ? (Color)new Color32(235, 222, 196, 110)
            : (Color)new Color32(18, 12, 8, 220);
        text.outlineWidth = 0.12f;
        text.raycastTarget = false;
        return text;
    }

    private static string StatsText(PlayerClass playerClass)
    {
        CoreTraits t = PlayerClassInfo.StartingTraits(playerClass);
        return $"STR {t.Strength}   END {t.Endurance}   AGI {t.Agility}\n" +
               $"INT {t.Intelligence}   AWA {t.Awareness}   PER {t.Perception}\n" +
               $"HP {PlayerClassInfo.StartingMaxHealth(playerClass)}   Resource {PlayerClassInfo.StartingMaxResource(playerClass)}";
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
        rect.offsetMin = Vector2.zero;
        rect.offsetMax = Vector2.zero;
    }

    private static void SetAnchors(RectTransform rect, Vector2 min, Vector2 max)
    {
        rect.anchorMin = min;
        rect.anchorMax = max;
        rect.offsetMin = Vector2.zero;
        rect.offsetMax = Vector2.zero;
    }

    private sealed class CreatorReferences
    {
        public TMP_InputField NameInput;
        public TextMeshProUGUI ClassTitle;
        public TextMeshProUGUI ClassBlurb;
        public TextMeshProUGUI Stats;
        public TextMeshProUGUI Weapon;
        public Button[] ClassButtons;
        public Button Confirm;
        public Button Back;
        public PlayerClassPreviewUI Preview;
    }
}
