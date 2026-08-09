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
            RestyleWin95();

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

        /// <summary>
        /// One-time Win95 skin for the scene-authored creator widgets: buttons raised grey,
        /// the name box a sunken white edit field, the readouts black.
        /// </summary>
        private void RestyleWin95()
        {
            if (ClassButtons != null)
                foreach (Button b in ClassButtons)
                    Win95Skin.StyleButtonWithLabel(b);

            Win95Skin.StyleButtonWithLabel(ConfirmButton);
            Win95Skin.StyleButtonWithLabel(BackButton);

            if (NameInput != null)
            {
                Image img = NameInput.GetComponent<Image>();
                if (img != null)
                {
                    img.color = Color.white;
                    Win95Skin.AddBevel((RectTransform)img.transform, sunken: true);
                }
                if (NameInput.textComponent != null)
                    NameInput.textComponent.color = Win95Skin.FieldText;
            }

            // ClassTitle is deliberately absent: the Win95 layout sits it white-on-black in a
            // NameBox while the parchment layout inks it dark, so its colour belongs to
            // whichever builder built the scene. Overriding it here would clash with one.
            if (ClassBlurb != null) ClassBlurb.color = Win95Skin.FieldText;
            if (StatsPreview != null) StatsPreview.color = Win95Skin.FieldText;
            if (WeaponPreview != null) WeaponPreview.color = Win95Skin.FieldText;
        }

        private void RefreshSelectedTab()
        {
            if (ClassButtons == null) return;

            for (int i = 0; i < ClassButtons.Length; i++)
            {
                Button button = ClassButtons[i];
                if (button == null) continue;

                // Win95 radio-tab behaviour: the picked class reads pressed-in, the rest raised.
                bool selected = i == (int)_selected;
                Image img = button.GetComponent<Image>();
                if (img != null) img.color = selected ? Win95Skin.FacePressed : Win95Skin.Face;
                Win95Skin.AddBevel((RectTransform)button.transform, sunken: selected);
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
