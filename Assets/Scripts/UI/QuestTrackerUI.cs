using UnityEngine;
using UnityEngine.UI;
using TMPro;
using ExiledAlvaston.Quests;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// On-HUD quest tracker (title + current objective). The box auto-sizes to its text so
    /// the objective never spills out, and a corner toggle collapses it to just the title.
    /// Keep this component on an always-active object; toggle <see cref="Root"/> only.
    /// </summary>
    public class QuestTrackerUI : MonoBehaviour
    {
        public TextMeshProUGUI TitleText;
        public TextMeshProUGUI ObjectiveText;
        public GameObject Root;

        private bool _built;
        private bool _collapsed;
        private RectTransform _boxRt;
        private TextMeshProUGUI _toggleLabel;

        private void OnEnable()
        {
            if (QuestManager.Instance != null)
                QuestManager.Instance.OnQuestsChanged += Refresh;
            Refresh();
        }

        private void OnDisable()
        {
            if (QuestManager.Instance != null)
                QuestManager.Instance.OnQuestsChanged -= Refresh;
        }

        private void Start()
        {
            if (QuestManager.Instance != null)
            {
                QuestManager.Instance.OnQuestsChanged -= Refresh;
                QuestManager.Instance.OnQuestsChanged += Refresh;
            }
            Refresh();
        }

        public void Refresh()
        {
            EnsureLayout();

            var q = QuestManager.Instance != null ? QuestManager.Instance.GetActiveQuest() : null;
            bool show = q != null;

            if (Root != null && Root != gameObject)
                Root.SetActive(show);

            if (!show) return;

            if (TitleText != null) TitleText.text = q.Title;
            if (ObjectiveText != null) ObjectiveText.text = q.Objective;

            ApplyCollapse();
        }

        private void ToggleCollapse()
        {
            _collapsed = !_collapsed;
            ApplyCollapse();
        }

        private void ApplyCollapse()
        {
            if (ObjectiveText != null)
                ObjectiveText.gameObject.SetActive(!_collapsed);
            if (_toggleLabel != null)
                _toggleLabel.text = _collapsed ? "+" : "-"; // "+" to expand, "-" to collapse

            if (_boxRt != null && _boxRt.gameObject.activeInHierarchy)
                LayoutRebuilder.ForceRebuildLayoutImmediate(_boxRt);
        }

        /// <summary>
        /// Converts the fixed-size box into a top-anchored panel that grows downward to fit its
        /// text (via VerticalLayoutGroup + ContentSizeFitter) and adds the collapse toggle.
        /// Runs once; cheap to call from every Refresh.
        /// </summary>
        private void EnsureLayout()
        {
            if (_built || Root == null || TitleText == null || ObjectiveText == null) return;
            _built = true;

            _boxRt = Root.GetComponent<RectTransform>();

            var vlg = Root.GetComponent<VerticalLayoutGroup>();
            if (vlg == null) vlg = Root.AddComponent<VerticalLayoutGroup>();
            vlg.padding = new RectOffset(12, 44, 8, 10); // extra right padding clears the toggle
            vlg.spacing = 4;
            vlg.childAlignment = TextAnchor.UpperLeft;
            vlg.childControlWidth = true;
            vlg.childControlHeight = true;
            vlg.childForceExpandWidth = true;
            vlg.childForceExpandHeight = false;

            var fitter = Root.GetComponent<ContentSizeFitter>();
            if (fitter == null) fitter = Root.AddComponent<ContentSizeFitter>();
            fitter.horizontalFit = ContentSizeFitter.FitMode.Unconstrained; // keep the 340px width
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;    // height fits content

            ConfigureLayoutChild(TitleText, FontStyles.Bold);
            ConfigureLayoutChild(ObjectiveText, FontStyles.Normal);
            ObjectiveText.transform.SetAsLastSibling(); // objective always below the title

            BuildToggleButton();
        }

        private static void ConfigureLayoutChild(TextMeshProUGUI tmp, FontStyles style)
        {
            var rt = tmp.rectTransform;
            rt.anchorMin = new Vector2(0f, 1f);
            rt.anchorMax = new Vector2(0f, 1f);
            rt.pivot = new Vector2(0f, 1f);
            tmp.enableWordWrapping = true;
            tmp.overflowMode = TextOverflowModes.Overflow;
            tmp.alignment = TextAlignmentOptions.TopLeft;
            tmp.fontStyle = style;
            tmp.raycastTarget = false;
        }

        private void BuildToggleButton()
        {
            var go = new GameObject("CollapseToggle", typeof(RectTransform));
            go.transform.SetParent(Root.transform, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(1f, 1f);
            rt.pivot = new Vector2(1f, 1f);
            rt.anchoredPosition = new Vector2(-6f, -6f);
            rt.sizeDelta = new Vector2(32f, 32f);

            // Float over the corner instead of being stacked by the layout group.
            go.AddComponent<LayoutElement>().ignoreLayout = true;

            var img = go.AddComponent<Image>();
            img.color = EKVibe.ButtonBrown;
            go.AddComponent<Button>().onClick.AddListener(ToggleCollapse);

            var labelGo = new GameObject("Label", typeof(RectTransform));
            labelGo.transform.SetParent(go.transform, false);
            var lrt = (RectTransform)labelGo.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.offsetMin = Vector2.zero;
            lrt.offsetMax = Vector2.zero;
            _toggleLabel = labelGo.AddComponent<TextMeshProUGUI>();
            _toggleLabel.text = "-";
            _toggleLabel.color = EKVibe.TextLight;
            _toggleLabel.fontSize = 24;
            _toggleLabel.fontStyle = FontStyles.Bold;
            _toggleLabel.alignment = TextAlignmentOptions.Center;
            _toggleLabel.raycastTarget = false;
        }
    }
}
