using UnityEngine;
using GBHEngland.UI;

namespace GBHEngland.World
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
        private string _lastPrompt;
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
            if (GBHEngland.Systems.PauseManager.IsPaused)
            {
                _armedAt = Time.unscaledTime + 0.3f;
                if (_current != null)
                {
                    _current = null;
                    _lastPrompt = null;
                    if (UIManager.Instance != null)
                        UIManager.Instance.SetInteractPrompt(null);
                }
                return;
            }

            Interactable closest = FindClosest();
            string prompt = closest != null ? closest.Prompt : null;

            // The prompt is compared as well as the target: an interactable can rewrite its own
            // Prompt without the closest one changing — mounting a vehicle flips it to "Get off
            // the ...", and watching the reference alone left the HUD reading "Nick this Moped"
            // for the whole ride.
            if (closest != _current || prompt != _lastPrompt)
            {
                _current = closest;
                _lastPrompt = prompt;
                if (UIManager.Instance != null)
                    UIManager.Instance.SetInteractPrompt(prompt);
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

            // Tracked separately so a LowPriority option never beats a real one on distance —
            // a mounted vehicle rides at distance zero and would win every tie otherwise.
            Interactable fallback = null;
            float bestFallback = float.PositiveInfinity;

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
                if (sq > it.InteractRange * it.InteractRange) continue;

                if (it.LowPriority)
                {
                    if (sq < bestFallback)
                    {
                        bestFallback = sq;
                        fallback = it;
                    }
                }
                else if (sq < best)
                {
                    best = sq;
                    closest = it;
                }
            }
            return closest != null ? closest : fallback;
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
