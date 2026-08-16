using UnityEngine;
using UnityEngine.UI;
using TMPro;
using GBHEngland.Companions;
using GBHEngland.Vibe;

namespace GBHEngland.UI
{
    /// <summary>
    /// Companion health/name badge, code-built Win95 style like the quest popup. Appears only while a
    /// companion is active. CompanionManager pushes updates through the UI.CompanionHUD static seam
    /// (which this class registers itself on), so the manager never has to know about this type.
    /// </summary>
    public class CompanionHUDUI : MonoBehaviour
    {
        private static CompanionHUDUI _instance;

        private GameObject _root;
        private TextMeshProUGUI _nameText;
        private Image _fill;
        private TextMeshProUGUI _hpText;

        public static void Ensure()
        {
            if (_instance != null) return;
            var go = new GameObject("CompanionHUD");
            DontDestroyOnLoad(go);
            _instance = go.AddComponent<CompanionHUDUI>();
            _instance.Build();
            // Register so CompanionManager.CompanionHUD.Refresh reaches us.
            CompanionHUD.SetTarget(_instance);
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
            CompanionHUD.SetTarget(null);
        }

        private void Build()
        {
            var canvasGO = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasGO.transform.SetParent(transform, false);
            var canvas = canvasGO.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 200;
            var scaler = canvasGO.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;

            // Top-centre, just under the quest tracker, like the player health bar's mirror.
            _root = CreateImage("Badge", canvasGO.transform, Win95Skin.Face);
            var rt = (RectTransform)_root.transform;
            rt.anchorMin = new Vector2(0.5f, 1f);
            rt.anchorMax = new Vector2(0.5f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.anchoredPosition = new Vector2(0, -8f);
            rt.sizeDelta = new Vector2(260, 46);
            Win95Skin.AddBevel(rt, sunken: false);

            _nameText = CreateTMP("Name", _root.transform, "", Win95Skin.FieldText, 18,
                TextAlignmentOptions.Left, FontStyles.Bold);
            var nrt = (RectTransform)_nameText.transform;
            nrt.anchorMin = new Vector2(0, 1);
            nrt.anchorMax = new Vector2(1, 1);
            nrt.pivot = new Vector2(0.5f, 1f);
            nrt.anchoredPosition = new Vector2(0, -4);
            nrt.sizeDelta = new Vector2(-16, 20);

            var barBg = CreateImage("BarBg", _root.transform, Win95Skin.SlotFill);
            var brt = (RectTransform)barBg.transform;
            brt.anchorMin = new Vector2(0, 0);
            brt.anchorMax = new Vector2(1, 0);
            brt.pivot = new Vector2(0.5f, 0);
            brt.anchoredPosition = new Vector2(0, 4);
            brt.sizeDelta = new Vector2(-16, 12);
            Win95Skin.AddBevel(brt, sunken: true);

            _fill = CreateImage("Fill", barBg.transform, EKVibe.HealthBar).GetComponent<Image>();
            var frt = _fill.rectTransform;
            frt.anchorMin = Vector2.zero;
            frt.anchorMax = new Vector2(1f, 1f);
            frt.offsetMin = new Vector2(2, 2);
            frt.offsetMax = new Vector2(-2, -2);

            _hpText = CreateTMP("HP", barBg.transform, "", Win95Skin.FieldText, 12,
                TextAlignmentOptions.Center, FontStyles.Normal);

            _root.SetActive(false);
            Refresh();
        }

        public void Refresh()
        {
            if (_root == null) return;

            CompanionManager mgr = CompanionManager.Instance;
            bool show = mgr != null && mgr.HasActiveCompanion && mgr.FollowerAI != null;
            if (_root.activeSelf != show) _root.SetActive(show);
            if (!show) return;

            string name = mgr.ActiveDefinition != null && !string.IsNullOrEmpty(mgr.ActiveDefinition.DisplayName)
                ? mgr.ActiveDefinition.DisplayName
                : (mgr.CurrentCompanionId ?? "Companion");
            if (_nameText != null) _nameText.text = name;

            var health = mgr.FollowerAI.FollowerHealth;
            if (health != null && _fill != null)
            {
                float frac = (float)health.CurrentHealth / Mathf.Max(1, health.MaxHealth);
                if (_fill != null) _fill.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(frac), 1f);
                if (_hpText != null) _hpText.text = $"{health.CurrentHealth}/{health.MaxHealth}";
            }
        }

        private static GameObject CreateImage(string name, Transform parent, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            go.AddComponent<Image>().color = color;
            return go;
        }

        private static TextMeshProUGUI CreateTMP(string name, Transform parent, string text,
            Color color, float size, TextAlignmentOptions align, FontStyles style)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.color = color;
            tmp.fontSize = size;
            tmp.alignment = align;
            tmp.fontStyle = style;
            tmp.raycastTarget = false;
            return tmp;
        }
    }

    /// <summary>
    /// Static seam between CompanionManager and the companion HUD. CompanionHUDUI registers itself;
    /// the manager only ever calls Refresh. A no-op when no HUD is running, so the companion never
    /// depends on one existing.
    /// </summary>
    public static partial class CompanionHUD
    {
        private static CompanionHUDUI _target;

        public static void SetTarget(CompanionHUDUI target) => _target = target;
        public static void Refresh(Companions.CompanionManager manager)
        {
            if (_target != null) _target.Refresh();
            else Ensure();
        }

        private static void Ensure()
        {
            // The HUD is optional chrome - only spin it up once a companion actually exists, and
            // never more than once.
            if (_target != null) return;
            if (managerNull()) return;
            CompanionHUDUI.Ensure();
        }

        private static bool managerNull() => Companions.CompanionManager.Instance == null
            || !Companions.CompanionManager.Instance.HasActiveCompanion;
    }
}