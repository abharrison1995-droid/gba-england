using UnityEngine;

namespace GBHEngland.World
{
    [RequireComponent(typeof(BoxCollider))]
    public class ChunkEdge : MonoBehaviour
    {
        [Tooltip("Which direction does this edge lead to?")]
        public Direction EdgeDirection;

        private void OnTriggerEnter(Collider other)
        {
            TryCross(other);
        }

        // Enter alone loses the crossing whenever ChunkManager declines it — a city lockout,
        // the tutorial lock, the post-arrival grace window. The boundary wall at ±110 now
        // stops forward movement while the trigger (inner face at ±109.8) keeps the player
        // inside its volume, so Stay re-offers the crossing every physics tick until it is
        // accepted or the player backs away. ChunkManager's own _isTransitioning / grace
        // guards dedupe the repeats, and arrival always lands 3.5 units clear of the
        // perimeter trigger, so this cannot ping-pong.
        private void OnTriggerStay(Collider other)
        {
            TryCross(other);
        }

        private void TryCross(Collider other)
        {
            // Trigger if the player hits the edge, or if a vehicle currently ridden by the player hits the edge
            bool isPlayer = other.CompareTag("Player") || other.GetComponent<GBHEngland.Combat.CombatController>() != null;
            bool isRiddenVehicle = MountController.IsPlayerRiding && MountController.Current != null &&
                                   MountController.Current.CurrentVehicle != null &&
                                   (other.transform.IsChildOf(MountController.Current.CurrentVehicle.transform) ||
                                    other.gameObject == MountController.Current.CurrentVehicle.gameObject);

            if (isPlayer || isRiddenVehicle)
            {
                // No Debug.Log here — from OnTriggerStay it would spam every physics tick.
                if (ChunkManager.Instance != null)
                    ChunkManager.Instance.OnPlayerHitEdge(EdgeDirection);
            }
        }
    }
}
