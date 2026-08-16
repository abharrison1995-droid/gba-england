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

        // Enter alone loses the crossing whenever ChunkManager declines it — the post-arrival
        // grace window, a city lockout, the tutorial lock. The player then walks through the
        // 2-unit trigger and off the ground, which ends at +/-110, and Enter never fires again.
        // Stay re-offers the crossing every physics tick until it is accepted or the player
        // leaves. ChunkManager's own _isTransitioning / grace guards dedupe the repeats, and
        // arrival always lands 12 units clear of any trigger, so this cannot ping-pong.
        private void OnTriggerStay(Collider other)
        {
            TryCross(other);
        }

        private void TryCross(Collider other)
        {
            // Only trigger if the player hits the edge
            if (other.CompareTag("Player") || other.GetComponent<GBHEngland.Combat.CombatController>() != null)
            {
                // No Debug.Log here — from OnTriggerStay it would spam every physics tick.
                if (ChunkManager.Instance != null)
                    ChunkManager.Instance.OnPlayerHitEdge(EdgeDirection);
            }
        }
    }
}
