using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
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

        [Tooltip("Sprite layered over the player while riding. Left empty, whatever the " +
                 "ParkedModel renders is used, so the parked and ridden vehicle always match.")]
        public Sprite VehicleSprite;

        [Tooltip("Left wherever you drop it while you stay in that chunk. Leave the chunk — by " +
                 "edge, door, portal, load or death — and it turns up back where it started.")]
        public bool ReturnsHomeOnChunkChange = true;

        private Interactable _interactable;
        private string _parkedPrompt;

        private Vector3 _homePosition;
        private Quaternion _homeRotation;
        private MapChunkData _parkedChunk;
        private bool _displaced;

        /// <summary>True while this specific vehicle is the one under the player.</summary>
        public bool IsRidden => MountController.Current != null
                                && MountController.Current.CurrentVehicle == this;

        private void Awake()
        {
            _interactable = GetComponent<Interactable>();
            _parkedPrompt = _interactable != null ? _interactable.Prompt : null;

            _homePosition = transform.position;
            _homeRotation = transform.rotation;
        }

        // Polls the live chunk rather than subscribing to a transition event, deliberately.
        // CurrentChunkData is a public serialized field written from seven places across six
        // files — both ChunkManager routines, GameFlowController twice, SaveGameManager,
        // DeathScreenUI and two editor tools — so hooking any one transition path would miss the
        // other three, and converting the field to a property to raise an event would stop Unity
        // serialising the scene's authored starting chunk. A reference compare costs nothing and
        // catches every path, including load-game and the arrest return.
        private void Update()
        {
            // Ridden: travel with the player. Its own Interactable is what offers the dismount
            // prompt, so leaving the vehicle parked would put that prompt out of range the moment
            // you drove off — and homing doesn't apply to a vehicle you're sat on.
            if (IsRidden)
            {
                var rider = CombatController.Instance;
                if (rider != null)
                    transform.position = rider.transform.position;
                return;
            }

            if (!ReturnsHomeOnChunkChange || !_displaced) return;

            var chunks = ChunkManager.Instance;
            if (chunks == null || chunks.CurrentChunkData == _parkedChunk) return;

            ReturnHome();
        }

        /// <summary>Back to where it was standing when the scene loaded.</summary>
        public void ReturnHome()
        {
            transform.position = _homePosition;
            transform.rotation = _homeRotation;
            _parkedChunk = null;
            _displaced = false;
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

            // Resolved before the model is hidden, so the ridden sprite always matches the parked one.
            Sprite ridden = ResolveVehicleSprite();

            // Hide the parked model only. Never SetActive the root: that fires OnDisable below,
            // and the vehicle would cancel its own boost the instant it was mounted.
            if (ParkedModel != null)
                ParkedModel.SetActive(false);

            if (player != null)
            {
                player.SetSpeedMultiplier(this, SpeedMultiplier);
                player.GetComponent<WorldActorVisual>()?.SetMounted(true, ridden);
            }

            ApplyPrompt(true);
        }

        /// <summary>Undoes <see cref="OnMounted"/>. Called by MountController, which owns the state.</summary>
        public void OnDismounted(CombatController player)
        {
            if (player != null)
            {
                player.ClearSpeedMultiplier(this);
                player.GetComponent<WorldActorVisual>()?.SetMounted(false, null);
                transform.position = player.transform.position;

                // Remember which chunk it was abandoned in; Update sends it home once that
                // stops being the live one.
                _parkedChunk = ChunkManager.Instance != null ? ChunkManager.Instance.CurrentChunkData : null;
                _displaced = true;
            }

            if (ParkedModel != null)
                ParkedModel.SetActive(true);

            ApplyPrompt(false);
            UIManager.Instance?.ShowToast($"Hopped off the {VehicleName}.");
        }

        /// <summary>The sprite to draw over the rider. Reads the parked model's own art by default.</summary>
        private Sprite ResolveVehicleSprite()
        {
            if (VehicleSprite != null) return VehicleSprite;
            if (ParkedModel == null) return null;

            var sr = ParkedModel.GetComponentInChildren<SpriteRenderer>(true);
            return sr != null ? sr.sprite : null;
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

            var player = CombatController.Instance;
            if (player != null)
            {
                player.ClearSpeedMultiplier(this);
                player.GetComponent<WorldActorVisual>()?.SetMounted(false, null);
            }

            if (ParkedModel != null)
                ParkedModel.SetActive(true);

            ApplyPrompt(false);
            MountController.Current?.ForgetVehicle(this);
        }
    }
}
