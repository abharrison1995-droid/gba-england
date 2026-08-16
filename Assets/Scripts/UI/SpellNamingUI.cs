using UnityEngine;
using UnityEngine.UI;
using TMPro;
using GBHEngland.Flow;

namespace GBHEngland.UI
{
    /// <summary>
    /// "Name your spell" popup shown when Daniel Pauls hands the spell over. Letters/digits/spaces,
    /// 16 chars, defaults to "Spark Out". The chosen name is what gets shouted when you cast.
    /// Code-built on its own overlay canvas; pauses while open.
    /// </summary>
    public class SpellNamingUI : MonoBehaviour
    {
        private static SpellNamingUI _instance;
        private GameObject _root;
        private TMP_InputField _input;
        private System.Action<string> _onNamed;

        public static void Show(System.Action<string> onNamed = null)
        {
            if (_instance == null)
            {
                var go = new GameObject("SpellNamingUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<SpellNamingUI>();
                _instance.Build();
            }
            _instance._onNamed = onNamed;
            _instance.Open();
        }

        private void Build()
        {
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "SpellNamingCanvas", 600);

            _root = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.6f));
            QuestUIBuilder.Stretch(_root, Vector2.zero, Vector2.one);

            GameObject panel = QuestUIBuilder.CreateImage("Panel", _root.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(780, 430);

            // Navy title bar like every other window; Confirm is still the only way out.
            GameObject header = QuestUIBuilder.CreateImage("Header", panel.transform, Win95Skin.TitleBar);
            var hrt = header.GetComponent<RectTransform>();
            hrt.anchorMin = new Vector2(0, 1);
            hrt.anchorMax = Vector2.one;
            hrt.pivot = new Vector2(0.5f, 1f);
            hrt.anchoredPosition = Vector2.zero;
            hrt.sizeDelta = new Vector2(0, 52);

            var title = QuestUIBuilder.CreateTMP("Title", header.transform, "NAME YOUR SPELL",
                Win95Skin.TitleText, 24, TextAlignmentOptions.Center, FontStyles.Bold);
            QuestUIBuilder.Stretch(title.gameObject, Vector2.zero, Vector2.one);

            var blurb = QuestUIBuilder.CreateTMP("Blurb", panel.transform,
                "\"Fuck knows — you're the magic man now. Call it whatever you're happy shouting out loud.\"",
                Win95Skin.FieldText, 20, TextAlignmentOptions.Center, FontStyles.Italic);
            blurb.enableWordWrapping = true;
            var brt = blurb.rectTransform;
            brt.anchorMin = new Vector2(0.07f, 0.52f); brt.anchorMax = new Vector2(0.93f, 0.78f);
            brt.offsetMin = Vector2.zero; brt.offsetMax = Vector2.zero;

            // Classic Win95 edit control: white fill, sunken bevel, black text.
            GameObject inputGo = QuestUIBuilder.CreateImage("Input", panel.transform, Color.white);
            Win95Skin.AddBevel((RectTransform)inputGo.transform, sunken: true);
            var irt = inputGo.GetComponent<RectTransform>();
            irt.anchorMin = new Vector2(0.14f, 0.34f); irt.anchorMax = new Vector2(0.86f, 0.5f);
            irt.offsetMin = Vector2.zero; irt.offsetMax = Vector2.zero;
            _input = inputGo.AddComponent<TMP_InputField>();
            _input.characterLimit = 16;

            var textArea = QuestUIBuilder.CreateTMP("Text", inputGo.transform, "",
                Win95Skin.FieldText, 26, TextAlignmentOptions.Left, FontStyles.Bold);
            var tart = textArea.rectTransform;
            tart.anchorMin = Vector2.zero; tart.anchorMax = Vector2.one;
            tart.offsetMin = new Vector2(14, 4); tart.offsetMax = new Vector2(-14, -4);
            _input.textComponent = textArea;
            _input.text = PlayerSession.DefaultSpellName;
            _input.onValidateInput = (text, index, added) => IsAllowed(added) ? added : '\0';

            var hint = QuestUIBuilder.CreateTMP("Hint", panel.transform,
                "letters, numbers & spaces — 16 max", new Color(0f, 0f, 0f, 0.55f),
                15, TextAlignmentOptions.Center, FontStyles.Normal);
            var hintRt = hint.rectTransform;
            hintRt.anchorMin = new Vector2(0.14f, 0.26f); hintRt.anchorMax = new Vector2(0.86f, 0.33f);
            hintRt.offsetMin = Vector2.zero; hintRt.offsetMax = Vector2.zero;

            GameObject confirm = QuestUIBuilder.CreateButton("Confirm", panel.transform, "SHOUT IT", Confirm);
            var crt = confirm.GetComponent<RectTransform>();
            crt.anchorMin = new Vector2(0.33f, 0.07f); crt.anchorMax = new Vector2(0.67f, 0.19f);
            crt.offsetMin = Vector2.zero; crt.offsetMax = Vector2.zero;

            _root.SetActive(false);
        }

        private static bool IsAllowed(char c)
        {
            return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == ' ';
        }

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        private void Open()
        {
            if (IsOpen) return;
            _root.SetActive(true);
            Systems.PauseManager.Push();
        }

        private void Confirm()
        {
            string name = PlayerSession.SanitizeSpellName(_input != null ? _input.text : null);
            if (PlayerSession.Instance != null) PlayerSession.Instance.SpellName = name;

            _root.SetActive(false);
            Systems.PauseManager.Pop();

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat($"Your spell is called \"{name}\".");
            _onNamed?.Invoke(name);
        }
    }
}
