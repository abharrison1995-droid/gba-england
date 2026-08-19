using System;
using System.Collections.Generic;
using GBHEngland.Data;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace GBHEngland.UI
{
    /// <summary>
    /// Runtime-built Win95 story cutscene viewer. Displays still image slides with story narrative
    /// text underneath for the player to read and tap through. Freezes world via PauseManager while reading.
    /// </summary>
    public class StoryCutsceneUI : MonoBehaviour
    {
        private static StoryCutsceneUI _instance;

        private GameObject _panelRoot;
        private Image _illustrationImage;
        private GameObject _illustrationPlaceholder;
        private TextMeshProUGUI _titleText;
        private TextMeshProUGUI _speakerText;
        private TextMeshProUGUI _narrativeText;
        private TextMeshProUGUI _progressText;
        private Button _nextButton;
        private TextMeshProUGUI _nextButtonLabel;

        private CutsceneData _currentCutscene;
        private int _currentSlideIndex;
        private Action _onCompleteCallback;

        public static bool IsOpen => _instance != null && _instance._panelRoot != null && _instance._panelRoot.activeSelf;

        public static void Show(CutsceneData cutscene, Action onComplete = null)
        {
            if (IsOpen)
            {
                Hide();
            }

            if (cutscene == null || cutscene.Slides == null || cutscene.Slides.Count == 0)
            {
                onComplete?.Invoke();
                return;
            }

            if (_instance == null)
            {
                var go = new GameObject("StoryCutsceneUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<StoryCutsceneUI>();
                _instance.BuildUI();
            }

            _instance._currentCutscene = cutscene;
            _instance._currentSlideIndex = 0;
            _instance._onCompleteCallback = onComplete;
            _instance.DisplayCurrentSlide();

            _instance._panelRoot.SetActive(true);
            Systems.PauseManager.Push();
        }

        public static void Hide()
        {
            if (_instance != null && _instance._panelRoot != null && _instance._panelRoot.activeSelf)
            {
                _instance._panelRoot.SetActive(false);
                Systems.PauseManager.Pop();
                Action cb = _instance._onCompleteCallback;
                _instance._onCompleteCallback = null;
                cb?.Invoke();
            }
        }

        private void OnDisable()
        {
            if (_panelRoot != null && _panelRoot.activeSelf)
            {
                _panelRoot.SetActive(false);
                Systems.PauseManager.Pop();
            }
        }

        private void OnDestroy()
        {
            if (_panelRoot != null && _panelRoot.activeSelf)
            {
                _panelRoot.SetActive(false);
                Systems.PauseManager.Pop();
            }
            if (_instance == this) _instance = null;
        }

        private void DisplayCurrentSlide()
        {
            if (_currentCutscene == null || _currentSlideIndex >= _currentCutscene.Slides.Count)
            {
                Hide();
                return;
            }

            CutsceneSlide slide = _currentCutscene.Slides[_currentSlideIndex];
            _titleText.text = _currentCutscene.Title;
            _speakerText.text = !string.IsNullOrEmpty(slide.SpeakerName) ? slide.SpeakerName : "Narrator";
            _narrativeText.text = slide.NarrativeText;
            _progressText.text = $"{_currentSlideIndex + 1} / {_currentCutscene.Slides.Count}";

            if (slide.Illustration != null)
            {
                _illustrationImage.gameObject.SetActive(true);
                _illustrationImage.sprite = slide.Illustration;
                _illustrationPlaceholder.SetActive(false);
            }
            else
            {
                _illustrationImage.gameObject.SetActive(false);
                _illustrationPlaceholder.SetActive(true);
            }

            bool isLastSlide = _currentSlideIndex == _currentCutscene.Slides.Count - 1;
            _nextButtonLabel.text = isLastSlide ? "FINISH" : "NEXT >>";
        }

        private void OnNextClicked()
        {
            if (_currentCutscene == null)
            {
                Hide();
                return;
            }

            if (_currentSlideIndex < _currentCutscene.Slides.Count - 1)
            {
                _currentSlideIndex++;
                DisplayCurrentSlide();
            }
            else
            {
                Hide();
            }
        }

        private void BuildUI()
        {
            var canvasGo = new GameObject("CutsceneCanvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasGo.transform.SetParent(transform, false);
            var canvas = canvasGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 950;

            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;

            // Fullscreen Dimmer Background
            _panelRoot = CreateImage("Dimmer", canvasGo.transform, new Color(0f, 0f, 0f, 0.78f));
            Stretch(_panelRoot, Vector2.zero, Vector2.one);

            // Centered Win95 Window Frame (Width: 840, Height: 720)
            GameObject window = CreateImage("CutsceneWindow", _panelRoot.transform, Win95Skin.Face);
            SetRect(window, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(860, 740), new Vector2(0.5f, 0.5f));
            Win95Skin.AddBevel((RectTransform)window.transform, sunken: false);

            // Title Bar
            GameObject titleBar = CreateImage("TitleBar", window.transform, Win95Skin.TitleBar);
            titleBar.GetComponent<Image>().raycastTarget = false;
            SetRect(titleBar, new Vector2(0, 1), new Vector2(1, 1), new Vector2(0, -22), new Vector2(-12, 34), new Vector2(0.5f, 0.5f));
            _titleText = CreateTMP("TitleText", titleBar.transform, "Royal Arena Chronicle", Win95Skin.TitleText, 22, TextAlignmentOptions.Left);
            SetRect(_titleText.gameObject, new Vector2(0, 0), new Vector2(1, 1), new Vector2(14, 0), new Vector2(-28, 0), new Vector2(0.5f, 0.5f));

            // Illustration Sunken Frame (Upper Half: 820 x 360)
            GameObject illusFrame = CreateImage("IllustrationFrame", window.transform, Win95Skin.SlotFill);
            illusFrame.GetComponent<Image>().raycastTarget = false;
            SetRect(illusFrame, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0, -230), new Vector2(820, 360), new Vector2(0.5f, 0.5f));
            Win95Skin.AddBevel((RectTransform)illusFrame.transform, sunken: true);

            // Illustration Sprite Image
            GameObject illusGo = CreateImage("IllustrationImage", illusFrame.transform, Color.white);
            _illustrationImage = illusGo.GetComponent<Image>();
            _illustrationImage.preserveAspect = true;
            _illustrationImage.raycastTarget = false;
            Stretch(illusGo, new Vector2(0.02f, 0.02f), new Vector2(0.98f, 0.98f));

            // Placeholder Text if no sprite assigned
            _illustrationPlaceholder = CreateTMP("PlaceholderText", illusFrame.transform, "[Royal Chronicle Illustration]", new Color(0.2f, 0.2f, 0.2f, 0.8f), 26, TextAlignmentOptions.Center).gameObject;
            Stretch(_illustrationPlaceholder, Vector2.zero, Vector2.one);

            // Narrative Panel (Lower Half: 820 x 220)
            GameObject textFrame = CreateImage("TextFrame", window.transform, Color.white);
            textFrame.GetComponent<Image>().raycastTarget = false;
            SetRect(textFrame, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0, 160), new Vector2(820, 190), new Vector2(0.5f, 0.5f));
            Win95Skin.AddBevel((RectTransform)textFrame.transform, sunken: true);

            // Speaker Tag
            _speakerText = CreateTMP("SpeakerText", textFrame.transform, "Prince Mandrew", new Color(0f, 0f, 0.5f, 1f), 22, TextAlignmentOptions.TopLeft);
            SetRect(_speakerText.gameObject, new Vector2(0, 1), new Vector2(1, 1), new Vector2(16, -22), new Vector2(-32, 30), new Vector2(0.5f, 0.5f));
            _speakerText.fontStyle = FontStyles.Bold;

            // Narrative Body Text
            _narrativeText = CreateTMP("NarrativeBody", textFrame.transform, "Story narration...", Win95Skin.FieldText, 21, TextAlignmentOptions.TopLeft);
            SetRect(_narrativeText.gameObject, new Vector2(0, 0), new Vector2(1, 1), new Vector2(16, -55), new Vector2(-32, -65), new Vector2(0.5f, 0.5f));

            // Footer Bar: Progress Indicator + Next/Finish Button
            _progressText = CreateTMP("ProgressText", window.transform, "1 / 3", Win95Skin.FieldText, 20, TextAlignmentOptions.Left);
            SetRect(_progressText.gameObject, new Vector2(0, 0), new Vector2(0, 0), new Vector2(40, 35), new Vector2(200, 40), new Vector2(0, 0.5f));

            GameObject buttonGo = CreateImage("NextButton", window.transform, Win95Skin.Face);
            SetRect(buttonGo, new Vector2(1, 0), new Vector2(1, 0), new Vector2(-120, 35), new Vector2(180, 48), new Vector2(0.5f, 0.5f));
            _nextButton = buttonGo.AddComponent<Button>();
            Win95Skin.StyleButton(_nextButton);
            _nextButton.onClick.AddListener(OnNextClicked);

            _nextButtonLabel = CreateTMP("NextLabel", buttonGo.transform, "NEXT >>", Win95Skin.FieldText, 22, TextAlignmentOptions.Center);
            _nextButtonLabel.fontStyle = FontStyles.Bold;
            Stretch(_nextButtonLabel.gameObject, Vector2.zero, Vector2.one);

            _panelRoot.SetActive(false);
        }

        private static GameObject CreateImage(string name, Transform parent, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            var img = go.GetComponent<Image>();
            img.color = color;
            return go;
        }

        private static TextMeshProUGUI CreateTMP(string name, Transform parent, string text, Color color, float size, TextAlignmentOptions alignment)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.color = color;
            tmp.fontSize = size;
            tmp.alignment = alignment;
            tmp.raycastTarget = false;
            return tmp;
        }

        private static void Stretch(GameObject go, Vector2 anchorMin, Vector2 anchorMax)
        {
            var rt = (RectTransform)go.transform;
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        private static void SetRect(GameObject go, Vector2 anchorMin, Vector2 anchorMax, Vector2 position, Vector2 size, Vector2 pivot)
        {
            var rt = (RectTransform)go.transform;
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.pivot = pivot;
            rt.anchoredPosition = position;
            rt.sizeDelta = size;
        }
    }
}
