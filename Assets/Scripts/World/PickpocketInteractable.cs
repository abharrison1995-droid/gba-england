using UnityEngine;
using ExiledAlvaston.Systems;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Attach this to a civilian to allow the player to pickpocket them while crouched.
    /// </summary>
    public class PickpocketInteractable : MonoBehaviour
    {
        public int MinGold = 5;
        public int MaxGold = 25;
        
        [Tooltip("Percentage chance to get caught (0.0 to 1.0)")]
        public float CatchChance = 0.3f;

        private bool _hasBeenRobbed = false;

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
                int stolenGold = Random.Range(MinGold, MaxGold + 1);
                UIManager.Instance?.ShowToast($"Nicked {stolenGold} quid!");
                
                // TODO: Add to player inventory once the inventory system supports adding raw gold dynamically
                // Flow.PlayerSession.Instance.Inventory.AddGold(stolenGold);
            }

            _hasBeenRobbed = true; // Can only rob them once
        }
    }
}
