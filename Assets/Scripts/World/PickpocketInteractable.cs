using UnityEngine;
using UnityEngine.Serialization;
using GBHEngland.Systems;
using GBHEngland.UI;
using GBHEngland.Vibe;

namespace GBHEngland.World
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

        // Appended, per CLAUDE.md §3. A mark authored before this existed carries no value for it,
        // reads null, and falls back to the pounds-only roll below — exactly what it did before.
        [Tooltip("What is in their pockets. Left empty, the attempt is a straight pounds roll " +
                 "between Min and Max Pounds, with no minigame.")]
        public Data.LootBand PickpocketBand;

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

                _hasBeenRobbed = true;
                return;
            }

            // Marked robbed before the menu opens, not after it closes. The attempt is the theft;
            // walking away halfway through is the player's own choice and does not buy a retry.
            _hasBeenRobbed = true;

            if (PickpocketBand == null)
            {
                // The pre-minigame behaviour, kept for every mark authored without a band: one
                // roll, straight into the wallet.
                int stolen = Random.Range(MinPounds, MaxPounds + 1);
                Flow.PlayerSession.Instance?.AddPounds(stolen);
                UIManager.Instance?.ShowToast($"Nicked {EKVibe.FormatPounds(stolen)}!");
                return;
            }

            PickpocketMenuUI.Show(BuildTitle(), BuildSlots(), transform, OnMenuClosed);
        }

        private string BuildTitle()
        {
            var interactable = GetComponent<Interactable>();
            var health = GetComponent<Combat.Health>();
            if (health != null && !string.IsNullOrEmpty(health.DisplayName)) return health.DisplayName;
            return interactable != null ? interactable.Prompt : name;
        }

        /// <summary>
        /// The pockets. <see cref="EKVibe.PickpocketSlots"/> rolls of the band, plus exactly one
        /// pounds slot — the wallet is a single thing to lift, not something found four times over.
        /// An empty roll simply produces fewer pockets, which reads as a mark who had nothing on
        /// them rather than an error.
        /// </summary>
        private System.Collections.Generic.List<PickpocketSlot> BuildSlots()
        {
            var slots = new System.Collections.Generic.List<PickpocketSlot>();

            int pounds = Random.Range(MinPounds, MaxPounds + 1);
            if (pounds > 0)
            {
                slots.Add(new PickpocketSlot
                {
                    Name = EKVibe.FormatPounds(pounds),
                    Pounds = pounds,
                    TapsRemaining = 1,
                });
            }

            foreach (Data.LootBandResult result in PickpocketBand.Roll(EKVibe.PickpocketSlots))
            {
                if (result == null || result.Item == null || result.Quantity <= 0) continue;

                slots.Add(new PickpocketSlot
                {
                    Name = result.Quantity > 1
                        ? $"{result.Item.ItemName} x{result.Quantity}"
                        : result.Item.ItemName,
                    Item = result.Item,
                    Quantity = result.Quantity,
                    TapsRemaining = Mathf.Max(1, result.TapsToFree),
                });
            }

            return slots;
        }

        /// <summary>
        /// Running the clock down is being caught: the mark notices the hand still in their pocket.
        /// Every other way out — banking the lot, closing, walking off — is a clean getaway with
        /// whatever was banked.
        /// </summary>
        private void OnMenuClosed(bool expired)
        {
            if (!expired) return;

            UIManager.Instance?.ShowToast("Oi! Get your hands off me! (Busted!)", 2f);
            WantedManager.Instance?.SpikeKnives();
        }
    }
}
