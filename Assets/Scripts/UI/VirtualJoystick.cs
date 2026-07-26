using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Large semi-transparent thumb stick (bottom-left), EK mobile style.
    /// </summary>
    public class VirtualJoystick : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IDragHandler
    {
        public RectTransform Background;
        public RectTransform Handle;
        public float HandleRange = 0.55f;

        public Vector2 InputVector { get; private set; }

        private Canvas _canvas;
        private Camera _uiCam;
        private bool _dragging;

        private void Awake()
        {
            _canvas = GetComponentInParent<Canvas>();
            if (_canvas != null && _canvas.renderMode != RenderMode.ScreenSpaceOverlay)
                _uiCam = _canvas.worldCamera;

            if (Background == null) Background = transform as RectTransform;
            if (Handle == null && Background != null && Background.childCount > 0)
                Handle = Background.GetChild(0) as RectTransform;
        }

        public void OnPointerDown(PointerEventData eventData)
        {
            _dragging = true;
            OnDrag(eventData);
        }

        public void OnDrag(PointerEventData eventData)
        {
            if (!_dragging || Background == null) return;

            Vector2 localPoint;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                Background, eventData.position, _uiCam, out localPoint);

            // rect.size stays correct for anchor-stretched rects (sizeDelta would be 0/negative)
            Vector2 radius = Background.rect.size * 0.5f;
            Vector2 normalized = new Vector2(
                radius.x > 0 ? localPoint.x / radius.x : 0f,
                radius.y > 0 ? localPoint.y / radius.y : 0f);

            InputVector = normalized.magnitude > 1f ? normalized.normalized : normalized;

            if (Handle != null)
                Handle.anchoredPosition = InputVector * radius * HandleRange;
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            _dragging = false;
            InputVector = Vector2.zero;
            if (Handle != null) Handle.anchoredPosition = Vector2.zero;
        }
    }
}
