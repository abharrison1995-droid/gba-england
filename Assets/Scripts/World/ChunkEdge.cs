using UnityEngine;

namespace ExiledAlvaston.World
{
    [RequireComponent(typeof(BoxCollider))]
    public class ChunkEdge : MonoBehaviour
    {
        [Tooltip("Which direction does this edge lead to?")]
        public Direction EdgeDirection;

        private void OnTriggerEnter(Collider other)
        {
            // Only trigger if the player hits the edge
            if (other.CompareTag("Player") || other.GetComponent<ExiledAlvaston.Combat.CombatController>() != null)
            {
                if (ChunkManager.Instance != null)
                {
                    Debug.Log($"Player hit the {EdgeDirection} edge! Requesting Chunk Load...");
                    ChunkManager.Instance.OnPlayerHitEdge(EdgeDirection);
                }
            }
        }
    }
}
