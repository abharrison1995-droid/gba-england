using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace GBHEngland.UI
{
    /// <summary>
    /// Touch hold button for mobile driving pedals (Gas, Brake, Drift).
    /// Tracks continuous press state with Win95 bevel depression feedback.
    /// </summary>
    [RequireComponent(typeof(Image))]
    public class UITouchHoldButton : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
    {
        public bool IsPressed { get; private set; }
        public float Pressure { get; set; } = 1.0f;
        public float Value => IsPressed ? Pressure : 0f;

        public System.Action<bool> OnHoldStateChanged;

        private Image _image;
        private RectTransform _rectTransform;

        private void Awake()
        {
            _image = GetComponent<Image>();
            _rectTransform = GetComponent<RectTransform>();
        }

        private void OnDisable()
        {
            if (IsPressed)
            {
                IsPressed = false;
                UpdateVisualState();
                OnHoldStateChanged?.Invoke(false);
            }
        }

        public void OnPointerDown(PointerEventData eventData)
        {
            IsPressed = true;
            UpdateVisualState();
            OnHoldStateChanged?.Invoke(true);
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            if (!IsPressed) return;
            IsPressed = false;
            UpdateVisualState();
            OnHoldStateChanged?.Invoke(false);
        }

        public void OnPointerExit(PointerEventData eventData)
        {
            if (!IsPressed) return;
            IsPressed = false;
            UpdateVisualState();
            OnHoldStateChanged?.Invoke(false);
        }

        private void UpdateVisualState()
        {
            if (_image != null)
                _image.color = IsPressed ? Win95Skin.FacePressed : Win95Skin.Face;

            if (_rectTransform != null)
                Win95Skin.AddBevel(_rectTransform, sunken: IsPressed);
        }

        public void ResetState()
        {
            IsPressed = false;
            UpdateVisualState();
        }
    }
}
