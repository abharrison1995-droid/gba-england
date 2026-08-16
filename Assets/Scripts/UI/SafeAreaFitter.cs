using UnityEngine;

namespace GBHEngland.UI
{
    /// <summary>Keeps a full-screen UI container inside the device's reported safe area.</summary>
    [ExecuteAlways]
    [RequireComponent(typeof(RectTransform))]
    public sealed class SafeAreaFitter : MonoBehaviour
    {
        private RectTransform _rectTransform;
        private Rect _lastSafeArea = new Rect(-1f, -1f, -1f, -1f);
        private Vector2Int _lastScreenSize = new Vector2Int(-1, -1);

        private void OnEnable()
        {
            _rectTransform = GetComponent<RectTransform>();
            ApplySafeArea();
        }

        private void Update()
        {
            if (_lastSafeArea != Screen.safeArea ||
                _lastScreenSize.x != Screen.width || _lastScreenSize.y != Screen.height)
                ApplySafeArea();
        }

        private void ApplySafeArea()
        {
            if (_rectTransform == null)
                _rectTransform = GetComponent<RectTransform>();

            int width = Screen.width;
            int height = Screen.height;
            if (width <= 0 || height <= 0) return;

            Rect safeArea = Screen.safeArea;
            Vector2 anchorMin = safeArea.position;
            Vector2 anchorMax = safeArea.position + safeArea.size;
            anchorMin.x = Mathf.Clamp01(anchorMin.x / width);
            anchorMin.y = Mathf.Clamp01(anchorMin.y / height);
            anchorMax.x = Mathf.Clamp01(anchorMax.x / width);
            anchorMax.y = Mathf.Clamp01(anchorMax.y / height);

            _rectTransform.anchorMin = anchorMin;
            _rectTransform.anchorMax = anchorMax;
            _rectTransform.offsetMin = Vector2.zero;
            _rectTransform.offsetMax = Vector2.zero;
            _lastSafeArea = safeArea;
            _lastScreenSize = new Vector2Int(width, height);
        }
    }
}
