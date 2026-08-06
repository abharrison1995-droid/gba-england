using UnityEngine;
using UnityEngine.UI;
using ExiledAlvaston.Flow;

namespace ExiledAlvaston.UI
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
        }

        private void OnEnable()
        {
            RefreshContinueButton();
        }

        /// <summary>
        /// Shows the authored Continue button whenever a save exists. Older scenes with no
        /// authored reference retain the original clone-of-New-Game fallback.
        /// </summary>
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
