using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// One kind of rideable thing — hire e-bike, moped, milk float. The chassis prefab supplies the
    /// components and collider; this supplies the tuning and the art, so adding a vehicle is a
    /// new asset rather than a new prefab.
    /// </summary>
    [CreateAssetMenu(fileName = "NewVehicleData", menuName = "ExiledAlvaston/Data/Vehicle Data")]
    public class VehicleData : ScriptableObject
    {
        public string VehicleName = "Limey E-Bike";

        [Tooltip("Prefab to instantiate. Must carry a VehicleController and an Interactable.")]
        public GameObject ChassisPrefab;

        [Header("Handling")]
        [Tooltip("Multiplies the rider's movement speed while mounted.")]
        public float SpeedMultiplier = 2f;

        [Header("Ownership")]
        [Tooltip("Belongs to somebody else — mounting it is theft and spikes your knives. " +
                 "Cleared on the instance once you've nicked it, and reset when the chunk reloads.")]
        public bool IsNickable = true;

        [Tooltip("Interact prompt while parked and not yet yours.")]
        public string ParkedPrompt = "Nick this e-bike";

        [Header("Art")]
        [Tooltip("Drawn parked, and layered over the rider while mounted. Leave empty to keep " +
                 "whatever artwork the chassis prefab already has.")]
        public Sprite VehicleSprite;

        [Tooltip("Height of the parked vehicle in world units. The player is 1.8, an adult NPC 1.55.")]
        public float ParkedHeight = 0.9f;
    }
}
