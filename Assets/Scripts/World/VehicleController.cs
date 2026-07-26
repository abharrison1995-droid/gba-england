using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Systems;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Handles the "Grand Theft Moped" logic. When the player mounts, they get a speed boost.
    /// If they steal it, the law gets involved.
    /// </summary>
    public class VehicleController : MonoBehaviour
    {
        public string VehicleName = "Vauxhall Corsa";
        public float SpeedMultiplier = 2.0f;
        public bool IsOwnedByNPC = true;
        
        [Tooltip("The visual model of the parked vehicle to hide when mounted.")]
        public GameObject ParkedModel;

        private bool _isPlayerMounted = false;

        public void Mount()
        {
            if (_isPlayerMounted) return;

            var player = CombatController.Instance;
            if (player == null) return;

            if (IsOwnedByNPC)
            {
                // Grand Theft Auto!
                WantedManager.Instance?.SpikeKnives();
                UIManager.Instance?.ShowToast($"Nicked a {VehicleName}! The Fuzz is on to you.");
                IsOwnedByNPC = false; // it's yours now
            }
            else
            {
                UIManager.Instance?.ShowToast($"Hopped into the {VehicleName}.");
            }

            _isPlayerMounted = true;
            
            // Hide the parked model
            if (ParkedModel != null)
                ParkedModel.SetActive(false);

            // Boost player speed
            player.MovementSpeed *= SpeedMultiplier;

            // TODO: In a full implementation, swap player animator state to "Driving"
        }
        
        // You could also implement Unmount() here which drops the ParkedModel back down at player pos.
    }
}
