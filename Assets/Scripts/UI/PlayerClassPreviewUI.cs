using GBHEngland.Data;
using GBHEngland.Flow;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace GBHEngland.UI
{
    public sealed class PlayerClassPreviewUI : MonoBehaviour
    {
        public Image PreviewImage;
        public TextMeshProUGUI PendingLabel;
        public PlayerClassVisualLibrary Library;

        private Sprite[] _frames;
        private float _fps;
        private float _elapsed;
        private int _frameIndex;

        public void ShowClass(PlayerClass playerClass)
        {
            ResolveLibrary();
            PlayerClassVisualProfile profile = Library != null ? Library.GetProfile(playerClass) : null;
            _frames = profile != null ? profile.IdlePreviewFrames : null;
            _fps = profile != null && profile.PreviewFps > 0f ? profile.PreviewFps : 6f;
            _elapsed = 0f;
            _frameIndex = 0;

            bool hasFrames = _frames != null && _frames.Length > 0 && _frames[0] != null;
            if (PreviewImage != null)
            {
                PreviewImage.sprite = hasFrames ? _frames[0] : null;
                PreviewImage.enabled = hasFrames;
            }
            if (PendingLabel != null)
                PendingLabel.gameObject.SetActive(!hasFrames);
        }

        private void Update()
        {
            if (_frames == null || _frames.Length < 2 || PreviewImage == null) return;

            _elapsed += Time.unscaledDeltaTime;
            float frameDuration = 1f / Mathf.Max(1f, _fps);
            while (_elapsed >= frameDuration)
            {
                _elapsed -= frameDuration;
                _frameIndex = (_frameIndex + 1) % _frames.Length;
                PreviewImage.sprite = _frames[_frameIndex];
            }
        }

        private void OnDisable()
        {
            _frames = null;
            _elapsed = 0f;
            _frameIndex = 0;
            if (PreviewImage != null)
            {
                PreviewImage.sprite = null;
                PreviewImage.enabled = false;
            }
            if (PendingLabel != null)
                PendingLabel.gameObject.SetActive(false);
        }

        private void ResolveLibrary()
        {
            if (Library != null) return;
            GameFlowController flow = GameFlowController.Instance ?? FindObjectOfType<GameFlowController>(true);
            if (flow != null)
                Library = flow.ClassVisuals != null
                    ? flow.ClassVisuals
                    : flow.GetComponent<PlayerClassVisualLibrary>();
        }
    }
}
