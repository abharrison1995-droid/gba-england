using UnityEngine;
using UnityEngine.UI;
using GBHEngland.Flow;

namespace GBHEngland.UI
{
    public class TitleScreenUI : MonoBehaviour
    {
        public Button NewGameButton;
        public Button QuitButton;
        public Button ContinueButton;

        private Button _continueButton;

        private void Awake()
        {
            if (NewGameButton != null)
            {
                NewGameButton.onClick.RemoveAllListeners();
                NewGameButton.onClick.AddListener(OnNewGame);
            }
            if (QuitButton != null)
            {
                QuitButton.onClick.RemoveAllListeners();
                QuitButton.onClick.AddListener(OnQuit);
            }
            if (ContinueButton != null)
            {
                _continueButton = ContinueButton;
                WireContinueButton();
            }

            RestyleWin95();
            BuildSettingsButton();
        }

        private void OnEnable()
        {
            RefreshContinueButton();
        }

        /// <summary>
        /// One-time Win95 skin for the scene-authored title buttons. The runtime-cloned
        /// Continue button inherits it, being an Instantiate of the already-styled New Game button.
        /// </summary>
        private void RestyleWin95()
        {
            Win95Skin.StyleButtonWithLabel(NewGameButton);
            Win95Skin.StyleButtonWithLabel(QuitButton);
            Win95Skin.StyleButtonWithLabel(ContinueButton);
        }

        /// <summary>
        /// Shows the authored Continue button whenever a save exists. Older scenes with no
        /// authored reference retain the original clone-of-New-Game fallback.
        /// </summary>
        /// <summary>
        /// Clones New Game rather than adding an authored field, so this doesn't need
        /// TitleScreenWin95Builder re-run and doesn't touch c.unity -- the builder's own field
        /// validation (expects exactly Label, Label, NewGameButton, QuitButton) never sees this
        /// button. WindowBody's VerticalLayoutGroup places it purely by sibling index.
        /// </summary>
        private void BuildSettingsButton()
        {
            if (NewGameButton == null || QuitButton == null) return;

            GameObject go = Instantiate(NewGameButton.gameObject, NewGameButton.transform.parent);
            go.name = "SettingsButton";
            go.transform.SetSiblingIndex(QuitButton.transform.GetSiblingIndex());

            var label = go.GetComponentInChildren<TMPro.TextMeshProUGUI>();
            if (label != null) label.text = "Settings";

            var button = go.GetComponent<Button>();
            button.onClick.RemoveAllListeners();
            button.onClick.AddListener(SettingsWindowUI.Open);
        }

        private void RefreshContinueButton()
        {
            bool hasSave = SaveGameManager.HasSave;

            if (_continueButton == null && hasSave && NewGameButton != null)
            {
                GameObject go = Instantiate(NewGameButton.gameObject, NewGameButton.transform.parent);
                go.name = "ContinueButton";

                var rt = go.GetComponent<RectTransform>();
                var src = NewGameButton.GetComponent<RectTransform>();
                rt.anchorMin = src.anchorMin + new Vector2(0f, 0.11f);
                rt.anchorMax = src.anchorMax + new Vector2(0f, 0.11f);

                var label = go.GetComponentInChildren<TMPro.TextMeshProUGUI>();
                if (label != null) label.text = "Continue";

                _continueButton = go.GetComponent<Button>();
                WireContinueButton();
            }

            if (_continueButton != null)
                _continueButton.gameObject.SetActive(hasSave);
        }

        private void WireContinueButton()
        {
            if (_continueButton == null) return;

            _continueButton.onClick.RemoveAllListeners();
            _continueButton.onClick.AddListener(OnContinue);
        }

        private void OnContinue()
        {
            if (GameFlowController.Instance == null)
            {
                Debug.LogWarning("TitleScreen: no GameFlowController.");
                return;
            }

            if (!GameFlowController.Instance.ContinueFromSave())
            {
                Debug.LogWarning("TitleScreen: save unreadable — starting fresh instead.");
                RefreshContinueButton();
            }
        }

        private void OnNewGame()
        {
            if (GameFlowController.Instance != null)
                GameFlowController.Instance.ShowCreator();
            else
                Debug.LogWarning("TitleScreen: no GameFlowController.");
        }

        private void OnQuit()
        {
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}
