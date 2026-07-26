using UnityEngine;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Lives on the Player. Polls every enabled Interactable by horizontal distance each
    /// frame and surfaces the closest in-range one as a HUD prompt. Desktop also gets an
    /// E-key shortcut alongside the HUD Interact button.
    /// </summary>
    public class PlayerInteractor : MonoBehaviour
    {
        public static PlayerInteractor Instance { get; private set; }

        private Interactable _current;
        private float _armedAt;

        private void Awake()
        {
            Instance = this;
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        private void Update()
        {
            // While any menu/dialogue pauses the game, interacting is off — and stays off
            // for a beat after unpausing so the E that closed a popup can't also re-open
            // the conversation that spawned it.
            if (ExiledAlvaston.Systems.PauseManager.IsPaused)
            {
                _armedAt = Time.unscaledTime + 0.3f;
                if (_current != null)
                {
                    _current = null;
                    if (UIManager.Instance != null)
                        UIManager.Instance.SetInteractPrompt(null);
                }
                return;
            }

            Interactable closest = FindClosest();
            if (closest != _current)
            {
                _current = closest;
                if (UIManager.Instance != null)
                    UIManager.Instance.SetInteractPrompt(_current != null ? _current.Prompt : null);
            }

#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL
            if (_current != null && Input.GetKeyDown(KeyCode.E))
                TryInteract();
#endif
        }

        private Interactable FindClosest()
        {
            Interactable closest = null;
            float best = float.PositiveInfinity;
            Vector3 pos = transform.position;

            var all = Interactable.Active;
            for (int i = all.Count - 1; i >= 0; i--)
            {
                Interactable it = all[i];
                if (it == null)
                {
                    all.RemoveAt(i);
                    continue;
                }
                if (!it.CanInteract) continue;

                Vector3 delta = it.transform.position - pos;
                delta.y = 0f;
                float sq = delta.sqrMagnitude;
                if (sq <= it.InteractRange * it.InteractRange && sq < best)
                {
                    best = sq;
                    closest = it;
                }
            }
            return closest;
        }

        /// <summary>Called by the HUD Interact button, or the E-key shortcut above.</summary>
        public void TryInteract()
        {
            if (Time.unscaledTime < _armedAt) return;
            if (_current != null)
                _current.Interact();
        }
    }
}
