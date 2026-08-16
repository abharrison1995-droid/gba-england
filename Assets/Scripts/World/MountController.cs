using UnityEngine;
using GBHEngland.Combat;
using GBHEngland.UI;

namespace GBHEngland.World
{
    /// <summary>
    /// Single owner of "is the player riding, and what". VehicleController used to answer that
    /// with a bool per vehicle, so two vehicles could each believe they had you — the same split
    /// ownership MovementSpeed had before modifiers were keyed by source.
    ///
    /// Lives on the Player. Nothing has to place it: Get() attaches it to the CombatController's
    /// GameObject on first use, so no scene or prefab wiring is required.
    /// </summary>
    public class MountController : MonoBehaviour
    {
        private static MountController _instance;

        /// <summary>The vehicle the player is currently on, or null on foot.</summary>
        public VehicleController CurrentVehicle { get; private set; }
        public bool IsMounted => CurrentVehicle != null;

        /// <summary>
        /// Cheap read for callers that only want to know, and must not cause the component to be
        /// created — CombatController checks this on every attack and cast.
        /// </summary>
        public static bool IsPlayerRiding => _instance != null && _instance.CurrentVehicle != null;

        /// <summary>
        /// The live instance without creating one. Use this anywhere a component must not be
        /// added — OnDisable and OnDestroy run during teardown, where AddComponent is illegal.
        /// </summary>
        public static MountController Current => _instance;

        /// <summary>The live instance, attaching one to the player if this is the first call.</summary>
        public static MountController Get()
        {
            if (_instance != null) return _instance;

            var player = CombatController.Instance;
            if (player == null) return null;

            var existing = player.GetComponent<MountController>();
            _instance = existing != null ? existing : player.gameObject.AddComponent<MountController>();
            return _instance;
        }

        private void Awake()
        {
            if (_instance == null) _instance = this;
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
        }

        public void Mount(VehicleController vehicle)
        {
            if (vehicle == null || IsMounted) return;

            var player = CombatController.Instance;
            if (player == null) return;

            CurrentVehicle = vehicle;
            vehicle.OnMounted(player);
        }

        public void Dismount()
        {
            if (CurrentVehicle == null) return;

            VehicleController vehicle = CurrentVehicle;
            CurrentVehicle = null;
            vehicle.OnDismounted(CombatController.Instance);
        }

        /// <summary>
        /// Called by a vehicle that is being disabled or destroyed while ridden. Drops the state
        /// without touching the vehicle back — it is on its way out and has already cleaned up.
        /// </summary>
        public void ForgetVehicle(VehicleController vehicle)
        {
            if (CurrentVehicle != vehicle) return;
            CurrentVehicle = null;
            UIManager.Instance?.ShowToast("Your ride's gone.");
        }
    }
}
