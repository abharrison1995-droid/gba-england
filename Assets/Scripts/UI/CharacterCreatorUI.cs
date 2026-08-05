using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;

namespace ExiledAlvaston.UI
{
    public class CharacterCreatorUI : MonoBehaviour
    {
        public TMP_InputField NameInput;
        public TextMeshProUGUI ClassTitle;
        public TextMeshProUGUI ClassBlurb;
        public TextMeshProUGUI StatsPreview;
        public TextMeshProUGUI WeaponPreview;
        public Button[] ClassButtons; // order matches PlayerClass enum
        public Button ConfirmButton;
        public Button BackButton;
        public PlayerClassPreviewUI Preview;

        private PlayerClass _selected = PlayerClass.YoungDriller;

        private void Awake()
        {
            if (ClassButtons != null)
            {
                for (int i = 0; i < ClassButtons.Length; i++)
                {
                    int idx = i;
                    if (ClassButtons[i] == null) continue;
                    ClassButtons[i].onClick.RemoveAllListeners();
                    ClassButtons[i].onClick.AddListener(() => SelectClass((PlayerClass)idx));
                }
            }

            if (ConfirmButton != null)
            {
                ConfirmButton.onClick.RemoveAllListeners();
                ConfirmButton.onClick.AddListener(OnConfirm);
            }
            if (BackButton != null)
            {
                BackButton.onClick.RemoveAllListeners();
                BackButton.onClick.AddListener(OnBack);
            }

            SelectClass(PlayerClass.YoungDriller);
        }

        private void OnEnable()
        {
            // Deliberately does not seed NameInput. Writing a value into an empty field here
            // would suppress the "Player name here!" placeholder every time the screen opened,
            // and leave the player deleting text before they can type. A blank name is handled
            // where it belongs, in PlayerSession.BeginNewGame.
            SelectClass(_selected);
        }

        public void SelectClass(PlayerClass c)
        {
            _selected = c;
            if (ClassTitle != null)
                ClassTitle.text = PlayerClassInfo.DisplayName(c);
            if (ClassBlurb != null)
                ClassBlurb.text = PlayerClassInfo.Tagline(c);
            if (WeaponPreview != null)
                WeaponPreview.text = "Specialises in: " + PlayerClassInfo.SpecialismLabel(c);
            if (StatsPreview != null)
            {
                var t = PlayerClassInfo.StartingTraits(c);
                StatsPreview.text =
                    $"STR {t.Strength}   END {t.Endurance}   AGI {t.Agility}\n" +
                    $"INT {t.Intelligence}   AWA {t.Awareness}   PER {t.Perception}\n" +
                    $"HP {PlayerClassInfo.StartingMaxHealth(c)}   Resource {PlayerClassInfo.StartingMaxResource(c)}";
            }

            if (Preview != null)
                Preview.ShowClass(c);

            RefreshSelectedTab();
        }

        private void RefreshSelectedTab()
        {
            if (ClassButtons == null) return;

            for (int i = 0; i < ClassButtons.Length; i++)
            {
                Button button = ClassButtons[i];
                if (button == null) continue;

                ColorBlock colors = button.colors;
                bool selected = i == (int)_selected;
                colors.normalColor = selected
                    ? new Color(0.82f, 0.69f, 0.45f, 1f)
                    : Color.white;
                colors.selectedColor = selected
                    ? new Color(0.9f, 0.78f, 0.52f, 1f)
                    : colors.highlightedColor;
                button.colors = colors;
            }
        }

        private void OnConfirm()
        {
            string name = NameInput != null ? NameInput.text : "Vince";
            if (GameFlowController.Instance != null)
                GameFlowController.Instance.StartNewGame(name, _selected);
            else
                Debug.LogWarning("CharacterCreator: no GameFlowController.");
        }

        private void OnBack()
        {
            if (GameFlowController.Instance != null)
                GameFlowController.Instance.ShowTitle();
        }
    }
}
