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

namespace ExiledAlvaston.EditorTools
{
    /// <summary>
    /// Rebuilds the character creator as a Win95 window in the inventory's image: navy title
    /// bar reading "Pick your Brit", grey raised face, sunken white name field, a row of five
    /// raised class tabs, a black name box over the class readouts, the intro copy on a grey
    /// panel, and the class sprite against a cornflower-blue block like the paper doll.
    /// The pixelated countryside plate shows around the window; the Union Jack baked into it
    /// stays visible along the bottom edge.
    ///
    /// Same safety pattern as CharacterCreatorSetup: only the children of the preserved
    /// CreatorRoot are replaced; the root, Canvas, title, HUD and GameFlow references are
    /// untouched; one undo group; any exception rolls back. Shares the generated root name
    /// "GeneratedCharacterCreator" with CharacterCreatorSetup so the fantasy tool still
    /// recognises this output and can roll back to it.
    /// </summary>
    public static class CharacterCreatorWin95Builder
    {
        private const string ScenePath = "Assets/c.unity";
        private const string GeneratedRootName = "GeneratedCharacterCreator";
        private const string BackgroundPath = "Assets/Textures/UI/Title/Creator_Background_Pixel.png";

        /// <summary>
        /// The owner's intro copy, carried over verbatim from CharacterCreatorSetup (supplied
        /// 2026-08-05). Straight apostrophes on purpose — TMP's default static atlas is often
        /// ASCII-only and a curly U+2019 would render as a missing-glyph box.
        /// </summary>
        private const string IntroCopy =
            "It's time for GBH: England. Are you ready? Magic? Police? Fascists? It's all here!\n\n" +
            "Dive in! Pick one of five classes and discover the real England!";

        /// <summary>Early-Windows cornflower blue, the same block the inventory paper doll stands on.</summary>
        private static readonly Color PaperDollBlue = new Color(0.392f, 0.584f, 0.929f); // #6495ED

        [MenuItem("Tools/GBH/UI/Rebuild Character Creator (Win95)")]
        public static void Rebuild()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)", "Exit Play mode before changing the scene.", "OK");
                return;
            }

            Scene scene = SceneManager.GetActiveScene();
            if (scene.path != ScenePath)
            {
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)", "Open Assets/c.unity first.", "OK");
                return;
            }

            GameFlowController[] flows = UnityEngine.Object.FindObjectsOfType<GameFlowController>(true);
            if (flows.Length != 1)
            {
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)",
                    "Expected exactly one GameFlowController; found " + flows.Length + ".", "OK");
                return;
            }

            GameFlowController flow = flows[0];
            GameObject creatorRoot = flow.CreatorRoot;
            RectTransform creatorRect = creatorRoot != null ? creatorRoot.GetComponent<RectTransform>() : null;
            CharacterCreatorUI creatorUi = creatorRoot != null ? creatorRoot.GetComponent<CharacterCreatorUI>() : null;
            if (creatorRect == null || creatorUi == null || creatorRoot.GetComponentInParent<Canvas>() == null)
            {
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)",
                    "GameFlowController.CreatorRoot must be the existing UI root with CharacterCreatorUI.", "OK");
                return;
            }

            if (!File.Exists(BackgroundPath))
            {
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)",
                    "The pixelated creator background is missing:\n" + BackgroundPath, "OK");
                return;
            }

            if (!ValidateChildren(creatorRoot.transform, out string summary)) return;
            if (!EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)",
                    "This replaces these CharacterCreator children:\n\n" + summary +
                    "\n\nThe root, Canvas, title, HUD, and GameFlow references are preserved. Undo is supported.",
                    "Apply", "Cancel")) return;

            try
            {
                ConfigureSprite();
            }
            catch (Exception ex)
            {
                Debug.LogException(ex);
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)",
                    "Sprite import failed; the scene was not changed.\n\n" + ex.Message, "OK");
                return;
            }

            Sprite background = LoadSprite(BackgroundPath);
            GameObject originalTitle = flow.TitleRoot;
            GameObject originalCreator = flow.CreatorRoot;
            GameObject originalHud = flow.HudRoot;
            bool originalActive = creatorRoot.activeSelf;
            int originalSibling = creatorRoot.transform.GetSiblingIndex();

            Undo.IncrementCurrentGroup();
            int undoGroup = Undo.GetCurrentGroup();
            Undo.SetCurrentGroupName("Rebuild Character Creator (Win95)");

            try
            {
                Undo.RegisterFullObjectHierarchyUndo(creatorRoot, "Rebuild Character Creator (Win95)");
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
                CreatorReferences refs = BuildContent(generated);

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
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)",
                    "The Win95 character creator is ready. Review it in Game view, then save Assets/c.unity with Ctrl+S.", "OK");
            }
            catch (Exception ex)
            {
                Undo.RevertAllDownToGroup(undoGroup);
                Debug.LogException(ex);
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)", "The scene change was rolled back.\n\n" + ex.Message, "OK");
            }
        }

        private static bool ValidateChildren(Transform root, out string summary)
        {
            summary = string.Join("\n", Enumerable.Range(0, root.childCount)
                .Select(i => "- " + root.GetChild(i).name));

            // Both generated layouts share the root name, so this accepts the fantasy tool's
            // output and this tool's own previous output alike.
            if (root.childCount == 1 && root.GetChild(0).name == GeneratedRootName)
                return true;

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
                EditorUtility.DisplayDialog("Rebuild Character Creator (Win95)",
                    "Creator children are neither the known 12-object legacy layout nor the generated layout. Nothing changed.\n\n" + summary,
                    "OK");
            return validLegacy;
        }

        private static void ConfigureSprite()
        {
            AssetDatabase.ImportAsset(BackgroundPath, ImportAssetOptions.ForceSynchronousImport);
            TextureImporter importer = AssetImporter.GetAtPath(BackgroundPath) as TextureImporter;
            if (importer == null) throw new InvalidOperationException("No TextureImporter for " + BackgroundPath);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 100f;
            importer.mipmapEnabled = false;
            importer.alphaSource = TextureImporterAlphaSource.None;
            importer.alphaIsTransparency = false;
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

        private static Sprite LoadSprite(string path)
        {
            Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            if (sprite == null)
                throw new InvalidOperationException("Sprite failed to import: " + path);
            return sprite;
        }

        /// <summary>No dark veil: the pixelation and blur baked into the plate do the dimming.</summary>
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
        }

        private static CreatorReferences BuildContent(RectTransform parent)
        {
            RectTransform safe = CreateRect("SafeArea", parent);
            Stretch(safe);
            safe.gameObject.AddComponent<SafeAreaFitter>();

            // The window stops at y 0.15 so the Union Jack baked into the plate's bottom
            // edge stays visible below it, and insets on the sides so the pixelated
            // countryside frames it — the way the game world frames the inventory window.
            RectTransform window = CreateRect("CreatorWindow", safe);
            SetAnchors(window, new Vector2(0.04f, 0.15f), new Vector2(0.96f, 0.95f));
            Image face = window.gameObject.AddComponent<Image>();
            Win95Skin.StyleWindow(face);
            Win95Skin.AddTitleBar(window, "Pick your Brit", 36f);

            // Everything below is anchored inside the window. The 36 px title bar over a
            // ~610 px window eats roughly the top 7%, so content runs 0.02–0.90.
            TMP_InputField nameInput = CreateNameInput(window);
            SetAnchors(nameInput.GetComponent<RectTransform>(), new Vector2(0.28f, 0.835f), new Vector2(0.72f, 0.90f));

            RectTransform tabs = CreateRect("ClassTabs", window);
            SetAnchors(tabs, new Vector2(0.03f, 0.745f), new Vector2(0.97f, 0.82f));
            HorizontalLayoutGroup tabLayout = tabs.gameObject.AddComponent<HorizontalLayoutGroup>();
            tabLayout.spacing = 8f;
            tabLayout.childControlWidth = true;
            tabLayout.childControlHeight = true;
            tabLayout.childForceExpandWidth = true;
            tabLayout.childForceExpandHeight = true;
            string[] names = { "Young Driller", "Stabmeister", "Mr Hood", "Dynamo", "Bunda Basher" };
            Button[] classButtons = names.Select((label, i) => CreateButton("Class" + i, label, tabs, 22f)).ToArray();

            // Details panel — the inventory left column's counterpart: black name box on top,
            // then the readouts as black text on grey.
            RectTransform details = CreatePanel("Details", window);
            SetAnchors(details, new Vector2(0.03f, 0.22f), new Vector2(0.38f, 0.725f));

            RectTransform nameBox = CreateRect("NameBox", details);
            SetAnchors(nameBox, new Vector2(0.05f, 0.885f), new Vector2(0.95f, 0.975f));
            Image boxImg = nameBox.gameObject.AddComponent<Image>();
            boxImg.color = Win95Skin.NameBox;
            TextMeshProUGUI classTitle = CreateText("ClassTitle", nameBox,
                PlayerClassInfo.DisplayName(PlayerClass.YoungDriller), 30f, FontStyles.Bold, Win95Skin.TitleText);
            Stretch(classTitle.rectTransform);
            classTitle.alignment = TextAlignmentOptions.Center;

            TextMeshProUGUI blurb = CreateText("ClassBlurb", details,
                PlayerClassInfo.Tagline(PlayerClass.YoungDriller), 22f, FontStyles.Normal, Win95Skin.FieldText);
            SetAnchors(blurb.rectTransform, new Vector2(0.07f, 0.60f), new Vector2(0.93f, 0.87f));
            blurb.alignment = TextAlignmentOptions.Top;
            blurb.enableWordWrapping = true;

            TextMeshProUGUI weapon = CreateText("WeaponPreview", details,
                "Specialises in: " + PlayerClassInfo.SpecialismLabel(PlayerClass.YoungDriller), 22f, FontStyles.Bold, Win95Skin.FieldText);
            SetAnchors(weapon.rectTransform, new Vector2(0.07f, 0.51f), new Vector2(0.93f, 0.59f));
            weapon.alignment = TextAlignmentOptions.Left;

            TextMeshProUGUI stats = CreateText("StatsPreview", details,
                StatsText(PlayerClass.YoungDriller), 21f, FontStyles.Normal, Win95Skin.FieldText);
            SetAnchors(stats.rectTransform, new Vector2(0.07f, 0.05f), new Vector2(0.93f, 0.49f));
            stats.alignment = TextAlignmentOptions.TopLeft;

            // Intro panel — the owner's copy, now black on grey instead of tan on brown.
            RectTransform intro = CreatePanel("IntroPanel", window);
            SetAnchors(intro, new Vector2(0.40f, 0.22f), new Vector2(0.63f, 0.725f));
            TextMeshProUGUI introText = CreateText("IntroText", intro, IntroCopy, 22f, FontStyles.Normal, Win95Skin.FieldText);
            Stretch(introText.rectTransform);
            introText.rectTransform.offsetMin = new Vector2(18f, 18f);
            introText.rectTransform.offsetMax = new Vector2(-18f, -18f);
            introText.enableWordWrapping = true;
            introText.alignment = TextAlignmentOptions.TopLeft;

            // Preview panel — the paper doll's counterpart: grey sunken frame, cornflower
            // block, sprite on top. The preview rect itself stays transparent; only the
            // backdrop colours the character's ground.
            RectTransform previewPanel = CreatePanel("Preview", window);
            SetAnchors(previewPanel, new Vector2(0.65f, 0.22f), new Vector2(0.97f, 0.725f));

            RectTransform backdrop = CreateRect("PaperDollBackdrop", previewPanel);
            SetAnchors(backdrop, new Vector2(0.18f, 0.05f), new Vector2(0.82f, 0.95f));
            Image backdropImg = backdrop.gameObject.AddComponent<Image>();
            backdropImg.color = PaperDollBlue;
            backdropImg.raycastTarget = false;

            RectTransform previewRect = CreateRect("CharacterImage", previewPanel);
            // Wider than the blue block: the idle sheets are square and mostly transparent
            // padding, so preserveAspect must keep fitting by height, not shrink by width.
            SetAnchors(previewRect, new Vector2(0.02f, 0.07f), new Vector2(0.98f, 0.93f));
            Image previewImage = previewRect.gameObject.AddComponent<Image>();
            previewImage.preserveAspect = true;
            previewImage.raycastTarget = false;

            TextMeshProUGUI pending = CreateText("PendingLabel", previewPanel, "Visual pending", 24f, FontStyles.Italic, Win95Skin.FieldText);
            Stretch(pending.rectTransform);

            PlayerClassPreviewUI preview = previewPanel.gameObject.AddComponent<PlayerClassPreviewUI>();
            preview.PreviewImage = previewImage;
            preview.PendingLabel = pending;

            Button confirm = CreateButton("ConfirmButton", "Enter Manor Cellars", window, 24f);
            SetAnchors((RectTransform)confirm.transform, new Vector2(0.28f, 0.105f), new Vector2(0.72f, 0.195f));
            Button back = CreateButton("BackButton", "Back", window, 24f);
            SetAnchors((RectTransform)back.transform, new Vector2(0.28f, 0.02f), new Vector2(0.72f, 0.095f));

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

        /// <summary>Sunken white edit field, black text — the skin's standard input.</summary>
        private static TMP_InputField CreateNameInput(RectTransform parent)
        {
            RectTransform root = CreateRect("NameInput", parent);
            Image background = root.gameObject.AddComponent<Image>();
            background.color = Color.white;
            TMP_InputField input = root.gameObject.AddComponent<TMP_InputField>();
            Win95Skin.AddBevel(root, sunken: true);

            RectTransform viewport = CreateRect("TextArea", root);
            Stretch(viewport);
            viewport.offsetMin = new Vector2(12f, 6f);
            viewport.offsetMax = new Vector2(-12f, -6f);
            viewport.gameObject.AddComponent<RectMask2D>();

            TextMeshProUGUI placeholder = CreateText("Placeholder", viewport, "Player name here!", 26f, FontStyles.Italic,
                new Color(0f, 0f, 0f, 0.45f));
            Stretch(placeholder.rectTransform);
            placeholder.alignment = TextAlignmentOptions.Left;
            TextMeshProUGUI text = CreateText("Text", viewport, "", 26f, FontStyles.Normal, Win95Skin.FieldText);
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

        private static Button CreateButton(string name, string label, RectTransform parent, float fontSize)
        {
            RectTransform rect = CreateRect(name, parent);
            Image image = rect.gameObject.AddComponent<Image>();
            Button button = rect.gameObject.AddComponent<Button>();
            button.targetGraphic = image;

            TextMeshProUGUI text = CreateText("Label", rect, label, fontSize, FontStyles.Bold, Win95Skin.FieldText);
            Stretch(text.rectTransform);
            text.rectTransform.offsetMin = new Vector2(8f, 5f);
            text.rectTransform.offsetMax = new Vector2(-8f, -5f);

            Win95Skin.StyleButton(button);
            return button;
        }

        /// <summary>Grey raised interior panel — the same treatment as the inventory's left column.</summary>
        private static RectTransform CreatePanel(string name, RectTransform parent)
        {
            RectTransform rect = CreateRect(name, parent);
            Image image = rect.gameObject.AddComponent<Image>();
            Win95Skin.StyleWindow(image);
            return rect;
        }

        private static TextMeshProUGUI CreateText(string name, RectTransform parent, string value,
            float size, FontStyles style, Color color)
        {
            RectTransform rect = CreateRect(name, parent);
            TextMeshProUGUI text = rect.gameObject.AddComponent<TextMeshProUGUI>();
            text.text = value;
            text.font = TMP_Settings.defaultFontAsset;
            text.fontSize = size;
            text.enableAutoSizing = true;
            text.fontSizeMin = Mathf.Max(14f, size * 0.6f);
            text.fontSizeMax = size;
            text.fontStyle = style;
            text.alignment = TextAlignmentOptions.Center;
            text.color = color;
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
}
