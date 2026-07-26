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
            SelectClass(_selected);
            if (NameInput != null && string.IsNullOrEmpty(NameInput.text))
                NameInput.text = "Exile";
        }

        public void SelectClass(PlayerClass c)
        {
            _selected = c;
            if (ClassTitle != null)
                ClassTitle.text = PlayerClassInfo.DisplayName(c);
            if (ClassBlurb != null)
                ClassBlurb.text = PlayerClassInfo.Tagline(c);
            if (WeaponPreview != null)
                WeaponPreview.text = "Starts with: " + PlayerClassInfo.StartingWeaponLabel(c);
            if (StatsPreview != null)
            {
                var t = PlayerClassInfo.StartingTraits(c);
                StatsPreview.text =
                    $"STR {t.Strength}   END {t.Endurance}   AGI {t.Agility}\n" +
                    $"INT {t.Intelligence}   AWA {t.Awareness}   PER {t.Perception}\n" +
                    $"HP {PlayerClassInfo.StartingMaxHealth(c)}   Resource {PlayerClassInfo.StartingMaxResource(c)}";
            }
        }

        private void OnConfirm()
        {
            string name = NameInput != null ? NameInput.text : "Exile";
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
