using TMPro;
using UnityEngine;
using UnityEngine.UI;
using GBHEngland.Systems;

namespace GBHEngland.UI
{
    /// <summary>
    /// DISPLAY SETTINGS — a small Win95-skinned window exposing GraphicsPrefs, opened from the
    /// title screen. Each row is a label plus a "cycle" button that steps through that setting's
    /// values and applies immediately (matching how little state there is here — four fields don't
    /// justify a slider or dropdown).
    ///
    /// Modelled directly on PerkWindowUI: self-creating singleton, DontDestroyOnLoad,
    /// PauseManager.Push/Pop balanced around open/close, QuestUIBuilder for chrome. Carries no
    /// serialized data and touches no scene/prefab — nothing here needs re-running a builder tool.
    /// </summary>
    public class SettingsWindowUI : MonoBehaviour
    {
        private static SettingsWindowUI _instance;

        private GameObject _root;
        private TextMeshProUGUI _qualityValue;
        private TextMeshProUGUI _shadowsValue;
        private TextMeshProUGUI _fpsCapValue;
        private TextMeshProUGUI _renderScaleValue;

        public static bool IsOpen => _instance != null && _instance._root != null && _instance._root.activeSelf;

        public static void Open()
        {
            if (_instance == null)
            {
                var go = new GameObject("SettingsWindowUI");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<SettingsWindowUI>();
                _instance.BuildUI();
            }
            _instance.OpenInternal();
        }

        public static void Toggle()
        {
            if (IsOpen)
            {
                _instance.Close();
                return;
            }
            if (PauseManager.IsPaused) return;
            Open();
        }

        private void OpenInternal()
        {
            if (IsOpen) return;
            RefreshLabels();
            _root.SetActive(true);
            PauseManager.Push();
        }

        private void Close()
        {
            if (!IsOpen) return;
            _root.SetActive(false);
            PauseManager.Pop();
        }

        // ── Setting rows ────────────────────────────────────────────────────────────────

        private void CycleQuality()
        {
            string[] names = QualitySettings.names;
            if (names.Length == 0) return;

            string current = GraphicsPrefs.QualityName;
            int index = System.Array.IndexOf(names, current);
            index = (index + 1) % names.Length;
            GraphicsPrefs.QualityName = names[index];
            RefreshLabels();
        }

        private void CycleShadows()
        {
            GraphicsPrefs.ShadowsEnabled = !GraphicsPrefs.ShadowsEnabled;
            RefreshLabels();
        }

        private static readonly int[] FpsCapSteps = { 30, 60, 0 };

        private void CycleFpsCap()
        {
            int current = GraphicsPrefs.FpsCap;
            int index = System.Array.IndexOf(FpsCapSteps, current);
            index = (index + 1) % FpsCapSteps.Length;
            GraphicsPrefs.FpsCap = FpsCapSteps[index];
            RefreshLabels();
        }

        private static readonly float[] RenderScaleSteps = { 1f, 0.75f, 0.6f };

        private void CycleRenderScale()
        {
            float current = GraphicsPrefs.RenderScale;
            int index = 0;
            for (int i = 0; i < RenderScaleSteps.Length; i++)
            {
                if (Mathf.Approximately(RenderScaleSteps[i], current)) { index = i; break; }
            }
            index = (index + 1) % RenderScaleSteps.Length;
            GraphicsPrefs.RenderScale = RenderScaleSteps[index];
            RefreshLabels();
        }

        private void RefreshLabels()
        {
            string qualityName = GraphicsPrefs.QualityName;
            if (_qualityValue != null)
                _qualityValue.text = string.IsNullOrEmpty(qualityName) ? "DEFAULT" : qualityName.ToUpperInvariant();

            if (_shadowsValue != null)
                _shadowsValue.text = GraphicsPrefs.ShadowsEnabled ? "ON" : "OFF";

            if (_fpsCapValue != null)
                _fpsCapValue.text = GraphicsPrefs.FpsCap > 0 ? GraphicsPrefs.FpsCap + " FPS" : "UNCAPPED";

            if (_renderScaleValue != null)
                _renderScaleValue.text = Mathf.RoundToInt(GraphicsPrefs.RenderScale * 100f) + "%";
        }

        // ── Chrome ──────────────────────────────────────────────────────────────────────

        private void BuildUI()
        {
            // Highest sorting order in use is WikiToastCanvas at 610; +25 keeps clear headroom.
            var canvasGO = QuestUIBuilder.CreateCanvas(transform, "SettingsWindowCanvas", 635);

            GameObject dim = QuestUIBuilder.CreateImage("Dimmer", canvasGO.transform, new Color(0f, 0f, 0f, 0.55f));
            QuestUIBuilder.Stretch(dim, Vector2.zero, Vector2.one);
            dim.AddComponent<Button>().onClick.AddListener(Close);
            _root = dim;

            GameObject panel = QuestUIBuilder.CreateImage("SettingsPanel", dim.transform, Win95Skin.Face);
            Win95Skin.AddBevel((RectTransform)panel.transform, sunken: false);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.sizeDelta = new Vector2(560f, 420f);

            RectTransform header = Win95Skin.AddTitleBar(prt, "DISPLAY SETTINGS", 34f);
            QuestUIBuilder.CreateCloseX(header, Close);

            float cursorY = 34f + 24f;
            _qualityValue = BuildRow(panel.transform, "QUALITY", CycleQuality, ref cursorY);
            _shadowsValue = BuildRow(panel.transform, "SHADOWS", CycleShadows, ref cursorY);
            _fpsCapValue = BuildRow(panel.transform, "FRAME CAP", CycleFpsCap, ref cursorY);
            _renderScaleValue = BuildRow(panel.transform, "RENDER SCALE", CycleRenderScale, ref cursorY);

            GameObject close = QuestUIBuilder.CreateButton("CloseButton", panel.transform, "CLOSE", Close);
            var crt = close.GetComponent<RectTransform>();
            crt.anchorMin = crt.anchorMax = new Vector2(0.5f, 0f);
            crt.pivot = new Vector2(0.5f, 0f);
            crt.anchoredPosition = new Vector2(0f, 16f);
            crt.sizeDelta = new Vector2(160f, 44f);

            _root.SetActive(false);
        }

        /// <summary>One label + cycle-value-button row, top-anchored, advancing cursorY.</summary>
        private static TextMeshProUGUI BuildRow(Transform panel, string label, UnityEngine.Events.UnityAction onClick, ref float cursorY)
        {
            const float rowH = 56f;

            var lbl = QuestUIBuilder.CreateTMP("Label_" + label, panel, label,
                Win95Skin.FieldText, 20, TextAlignmentOptions.Left, FontStyles.Bold);
            var lrt = lbl.rectTransform;
            lrt.anchorMin = new Vector2(0f, 1f);
            lrt.anchorMax = new Vector2(0.5f, 1f);
            lrt.pivot = new Vector2(0f, 1f);
            lrt.anchoredPosition = new Vector2(24f, -cursorY);
            lrt.sizeDelta = new Vector2(-24f, rowH);

            GameObject btn = QuestUIBuilder.CreateButton("Value_" + label, panel, "", onClick);
            var brt = btn.GetComponent<RectTransform>();
            brt.anchorMin = new Vector2(0.5f, 1f);
            brt.anchorMax = new Vector2(1f, 1f);
            brt.pivot = new Vector2(1f, 1f);
            brt.anchoredPosition = new Vector2(-24f, -cursorY);
            brt.sizeDelta = new Vector2(-24f, 40f);

            var valueLabel = btn.GetComponentInChildren<TextMeshProUGUI>(true);

            cursorY += rowH;
            return valueLabel;
        }
    }
}
