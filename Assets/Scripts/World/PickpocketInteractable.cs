using UnityEngine;
using UnityEngine.Serialization;
using ExiledAlvaston.Systems;
using ExiledAlvaston.UI;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Attach this to a civilian to allow the player to pickpocket them while crouched.
    /// </summary>
    public class PickpocketInteractable : MonoBehaviour
    {
        [FormerlySerializedAs("MinGold")]
        public int MinPounds = 5;

        [FormerlySerializedAs("MaxGold")]
        public int MaxPounds = 25;

        [Tooltip("Percentage chance to get caught (0.0 to 1.0)")]
        public float CatchChance = 0.3f;

        private bool _hasBeenRobbed = false;

        /// <summary>
        /// Wires itself to the Interactable, the way NPCDialogueInteractable does — *unless* the
        /// object already carries a persistent call pointing back here.
        ///
        /// Self-subscribing is the only route that works for an authored asset: UnityEvent
        /// .AddListener produces a *non-persistent* listener that is never serialized, so wiring
        /// one at authoring time would look right in the editor and be silently gone from the
        /// saved prefab. Every mark in the project is therefore wired here, at Awake.
        ///
        /// The persistent-call scan is kept as a guard, not because anything currently needs it.
        /// Nothing on disk carries such a call any more — the one asset that did, NoseyParker
        /// .prefab, has been deleted — but an editor tool writing OnInteract → TryPickpocket
        /// through UnityEventTools would otherwise give that object two listeners and rob the
        /// player twice per press. Deciding from what the object actually carries costs one loop
        /// at Awake and keeps both routes safe.
        /// </summary>
        private void Awake()
        {
            var interactable = GetComponent<Interactable>();
            if (interactable == null || interactable.OnInteract == null) return;

            int persistent = interactable.OnInteract.GetPersistentEventCount();
            for (int i = 0; i < persistent; i++)
            {
                if (ReferenceEquals(interactable.OnInteract.GetPersistentTarget(i), this))
                    return;   // authored in a prefab already — leave it alone
            }

            interactable.OnInteract.AddListener(TryPickpocket);
        }

        public void TryPickpocket()
        {
            if (_hasBeenRobbed)
            {
                UIManager.Instance?.ShowToast("Already emptied their pockets!");
                return;
            }

            // Must be sneaking to pickpocket
            if (StealthController.Instance == null || !StealthController.Instance.IsCrouched)
            {
                UIManager.Instance?.ShowToast("You need to be sneaking to pickpocket.");
                return;
            }

            // Roll the dice
            if (Random.value < CatchChance)
            {
                // Busted!
                UIManager.Instance?.ShowToast("Oi! Get your hands off me! (Busted!)", 2f);
                if (WantedManager.Instance != null)
                {
                    WantedManager.Instance.SpikeKnives();
                }
            }
            else
            {
                // Success
                int stolen = Random.Range(MinPounds, MaxPounds + 1);
                Flow.PlayerSession.Instance?.AddPounds(stolen);
                UIManager.Instance?.ShowToast($"Nicked {EKVibe.FormatPounds(stolen)}!");
            }

            _hasBeenRobbed = true; // Can only rob them once
        }
    }
}
