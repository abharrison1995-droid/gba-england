using UnityEngine;

namespace GBHEngland.Systems
{
    /// <summary>
    /// Device-local graphics/performance preferences, applied on boot and whenever the settings
    /// window changes one. Stored in PlayerPrefs deliberately, not SaveData/savegame.json -- this
    /// is a device preference, not game state, and must never go through SaveGameManager.
    ///
    /// Quality is stored by name, not QualitySettings index. An index would silently repoint to a
    /// different tier if a level is ever inserted or reordered; a name degrades safely to the
    /// platform default if it no longer resolves.
    /// </summary>
    public static class GraphicsPrefs
    {
        private const string QualityNameKey = "gbh.gfx.qualityName";
        private const string ShadowsKey = "gbh.gfx.shadows";
        private const string FpsCapKey = "gbh.gfx.fpsCap";
        private const string RenderScaleKey = "gbh.gfx.renderScale";

        private static float _lastAppliedRenderScale = -1f;

        public static string QualityName
        {
            get => PlayerPrefs.GetString(QualityNameKey, "");
            set { PlayerPrefs.SetString(QualityNameKey, value); Apply(); }
        }

        public static bool ShadowsEnabled
        {
            get => PlayerPrefs.GetInt(ShadowsKey, 1) != 0;
            set { PlayerPrefs.SetInt(ShadowsKey, value ? 1 : 0); Apply(); }
        }

        /// <summary>30, 60, or 0 for uncapped.</summary>
        public static int FpsCap
        {
            get => PlayerPrefs.GetInt(FpsCapKey, 60);
            set { PlayerPrefs.SetInt(FpsCapKey, value); Apply(); }
        }

        /// <summary>0.6-1.0.</summary>
        public static float RenderScale
        {
            get => PlayerPrefs.GetFloat(RenderScaleKey, 1f);
            set { PlayerPrefs.SetFloat(RenderScaleKey, value); Apply(); }
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void ApplyOnBoot()
        {
            Apply();
        }

        public static void Apply()
        {
            string name = QualityName;
            if (!string.IsNullOrEmpty(name))
            {
                string[] names = QualitySettings.names;
                for (int i = 0; i < names.Length; i++)
                {
                    if (names[i] == name)
                    {
                        QualitySettings.SetQualityLevel(i, true);
                        break;
                    }
                }
            }

            // SetQualityLevel overwrites QualitySettings.shadows as a side effect of switching
            // tiers, so the shadow override has to be applied after it, every time, or a manually
            // disabled shadow setting silently comes back the next time quality changes.
            QualitySettings.shadows = ShadowsEnabled ? ShadowQuality.All : ShadowQuality.Disable;

            int cap = FpsCap;
            Application.targetFrameRate = cap > 0 ? cap : -1;

            float scale = Mathf.Clamp(RenderScale, 0.6f, 1f);
            // At the default (1.0, native) Screen is left untouched entirely -- calling
            // SetResolution even with the current resolution still triggers a surface recreate on
            // mobile, so a fresh install with no preference set must not touch it at all. Below
            // 1.0, re-applying an identical scale is guarded the same way.
            if (scale < 0.999f && !Mathf.Approximately(scale, _lastAppliedRenderScale))
            {
                int width = Mathf.RoundToInt(Screen.currentResolution.width * scale);
                int height = Mathf.RoundToInt(Screen.currentResolution.height * scale);
                Screen.SetResolution(width, height, Screen.fullScreen);
                _lastAppliedRenderScale = scale;
            }
        }
    }
}
