using UnityEngine;
using UnityEngine.UI;
using ExiledAlvaston.Flow;

namespace ExiledAlvaston.UI
{
    public class TitleScreenUI : MonoBehaviour
    {
        public Button NewGameButton;
        public Button QuitButton;

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
        }

        private void OnEnable()
        {
            RefreshContinueButton();
        }

        /// <summary>
        /// Builds a Continue button (clone of New Game, one row up) whenever a save exists.
        /// Created in code so existing scenes don't need re-wiring.
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
                _continueButton.onClick.RemoveAllListeners();
                _continueButton.onClick.AddListener(OnContinue);
            }

            if (_continueButton != null)
                _continueButton.gameObject.SetActive(hasSave);
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
