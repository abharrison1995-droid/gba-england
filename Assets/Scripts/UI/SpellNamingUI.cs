using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Vibe;
using ExiledAlvaston.Flow;

namespace ExiledAlvaston.UI
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

            GameObject panel = QuestUIBuilder.CreateImage("Panel", _root.transform, EKVibe.ParchmentPanel);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(780, 430);

            var title = QuestUIBuilder.CreateTMP("Title", panel.transform, "NAME YOUR SPELL",
                EKVibe.TextDark, 30, TextAlignmentOptions.Center, FontStyles.Bold);
            var trt = title.rectTransform;
            trt.anchorMin = new Vector2(0, 1); trt.anchorMax = new Vector2(1, 1); trt.pivot = new Vector2(0.5f, 1f);
            trt.offsetMin = new Vector2(20, -72); trt.offsetMax = new Vector2(-20, -18);

            var blurb = QuestUIBuilder.CreateTMP("Blurb", panel.transform,
                "\"Fuck knows — you're the magic man now. Call it whatever you're happy shouting out loud.\"",
                EKVibe.TextDark, 20, TextAlignmentOptions.Center, FontStyles.Italic);
            blurb.enableWordWrapping = true;
            var brt = blurb.rectTransform;
            brt.anchorMin = new Vector2(0.07f, 0.56f); brt.anchorMax = new Vector2(0.93f, 0.8f);
            brt.offsetMin = Vector2.zero; brt.offsetMax = Vector2.zero;

            GameObject inputGo = QuestUIBuilder.CreateImage("Input", panel.transform, Color.white);
            var irt = inputGo.GetComponent<RectTransform>();
            irt.anchorMin = new Vector2(0.14f, 0.34f); irt.anchorMax = new Vector2(0.86f, 0.5f);
            irt.offsetMin = Vector2.zero; irt.offsetMax = Vector2.zero;
            _input = inputGo.AddComponent<TMP_InputField>();
            _input.characterLimit = 16;

            var textArea = QuestUIBuilder.CreateTMP("Text", inputGo.transform, "",
                EKVibe.TextDark, 26, TextAlignmentOptions.Left, FontStyles.Bold);
            var tart = textArea.rectTransform;
            tart.anchorMin = Vector2.zero; tart.anchorMax = Vector2.one;
            tart.offsetMin = new Vector2(14, 4); tart.offsetMax = new Vector2(-14, -4);
            _input.textComponent = textArea;
            _input.text = PlayerSession.DefaultSpellName;
            _input.onValidateInput = (text, index, added) => IsAllowed(added) ? added : '\0';

            var hint = QuestUIBuilder.CreateTMP("Hint", panel.transform,
                "letters, numbers & spaces — 16 max", new Color(EKVibe.TextDark.r, EKVibe.TextDark.g, EKVibe.TextDark.b, 0.55f),
                15, TextAlignmentOptions.Center, FontStyles.Normal);
            var hrt = hint.rectTransform;
            hrt.anchorMin = new Vector2(0.14f, 0.26f); hrt.anchorMax = new Vector2(0.86f, 0.33f);
            hrt.offsetMin = Vector2.zero; hrt.offsetMax = Vector2.zero;

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
