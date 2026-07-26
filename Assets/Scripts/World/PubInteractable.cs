using UnityEngine;
using ExiledAlvaston.Systems;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// The Winchester Protocol: Have a pint, clear your wanted level, and save the game.
    /// </summary>
    public class PubInteractable : MonoBehaviour
    {
        public string PubName = "The Winchester";
        
        public void HaveAPint()
        {
            // Clear Wanted Level and Concealment
            if (WantedManager.Instance != null)
            {
                WantedManager.Instance.CurrentKnives = 0;
                WantedManager.Instance.CurrentConcealment = WantedManager.Instance.MaxConcealment;
                // Force update UI manually since SpikeKnives does it for increases
                if (UIManager.Instance != null)
                {
                    UIManager.Instance.UpdateKnivesUI(0);
                    UIManager.Instance.UpdatePlayerConcealment(WantedManager.Instance.MaxConcealment, WantedManager.Instance.MaxConcealment);
                }
            }

            // Heal the player
            var player = Combat.CombatController.Instance;
            if (player != null)
            {
                player.ReviveFull(); // Heals to max
            }

            // Save the game
            SaveGameManager.Save();

            if (UIManager.Instance != null)
            {
                UIManager.Instance.ShowToast($"Had a pint at {PubName}. Heat cleared. Game saved.");
            }
        }
    }
}
