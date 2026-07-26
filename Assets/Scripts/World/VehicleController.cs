using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Systems;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Handles the "Grand Theft Moped" logic. When the player mounts, they get a speed boost.
    /// If they steal it, the law gets involved.
    ///
    /// Whether the player is riding is owned by <see cref="MountController"/>, not by a bool here.
    /// This component describes the vehicle and applies its own effects when told to.
    /// </summary>
    public class VehicleController : MonoBehaviour
    {
        public string VehicleName = "Vauxhall Corsa";
        public float SpeedMultiplier = 2.0f;
        public bool IsOwnedByNPC = true;

        [Tooltip("The visual model of the parked vehicle to hide when mounted.")]
        public GameObject ParkedModel;

        private Interactable _interactable;
        private string _parkedPrompt;

        /// <summary>True while this specific vehicle is the one under the player.</summary>
        public bool IsRidden => MountController.Current != null
                                && MountController.Current.CurrentVehicle == this;

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            _parkedPrompt = _interactable != null ? _interactable.Prompt : null;
        }

        /// <summary>
        /// Interact entry point, wired to Interactable.OnInteract. Mounts when parked and gets you
        /// off when you are already on it, so one prompt covers both.
        /// </summary>
        public void Toggle()
        {
            var mount = MountController.Get();
            if (mount == null) return;

            if (mount.CurrentVehicle == this)
                mount.Dismount();
            else if (!mount.IsMounted)
                mount.Mount(this);
            else
                UIManager.Instance?.ShowToast($"Get off the {mount.CurrentVehicle.VehicleName} first.");
        }

        public void Mount()
        {
            MountController.Get()?.Mount(this);
        }

        /// <summary>Step off: drops the vehicle where the player is standing and gives back their speed.</summary>
        public void Unmount()
        {
            var mount = MountController.Current;
            if (mount != null && mount.CurrentVehicle == this)
                mount.Dismount();
        }

        /// <summary>Applies this vehicle's effects. Called by MountController, which owns the state.</summary>
        public void OnMounted(CombatController player)
        {
            if (IsOwnedByNPC)
            {
                // Grand Theft Auto!
                WantedManager.Instance?.SpikeKnives();
                UIManager.Instance?.ShowToast($"Nicked a {VehicleName}! The Fuzz is on to you.");
                IsOwnedByNPC = false; // it's yours now
            }
            else
            {
                UIManager.Instance?.ShowToast($"Hopped onto the {VehicleName}.");
            }

            // Hide the parked model only. Never SetActive the root: that fires OnDisable below,
            // and the vehicle would cancel its own boost the instant it was mounted.
            if (ParkedModel != null)
                ParkedModel.SetActive(false);

            if (player != null)
                player.SetSpeedMultiplier(this, SpeedMultiplier);

            ApplyPrompt(true);
        }

        /// <summary>Undoes <see cref="OnMounted"/>. Called by MountController, which owns the state.</summary>
        public void OnDismounted(CombatController player)
        {
            if (player != null)
            {
                player.ClearSpeedMultiplier(this);
                transform.position = player.transform.position;
            }

            if (ParkedModel != null)
                ParkedModel.SetActive(true);

            ApplyPrompt(false);
            UIManager.Instance?.ShowToast($"Hopped off the {VehicleName}.");
        }

        private void ApplyPrompt(bool mounted)
        {
            if (_interactable == null) return;

            if (mounted)
            {
                _interactable.Prompt = $"Get off the {VehicleName}";
                // Rides at distance zero, so without this it masks every pub, door and NPC.
                _interactable.LowPriority = true;
            }
            else
            {
                _interactable.Prompt = IsOwnedByNPC ? _parkedPrompt : $"Ride the {VehicleName}";
                _interactable.LowPriority = false;
            }
        }

        // Without this the boost outlives the vehicle: chunk transitions destroy the whole chunk,
        // so a mounted moped would vanish with its multiplier still registered. The ride state is
        // dropped too — leaving it set made the vehicle permanently half-mounted if it came back.
        private void OnDisable()
        {
            if (!IsRidden) return;

            CombatController.Instance?.ClearSpeedMultiplier(this);

            if (ParkedModel != null)
                ParkedModel.SetActive(true);

            ApplyPrompt(false);
            MountController.Current?.ForgetVehicle(this);
        }
    }
}
