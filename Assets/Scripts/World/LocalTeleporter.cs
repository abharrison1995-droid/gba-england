using UnityEngine;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Same-chunk teleport: walk up, press Interact, appear at a named SceneMarker elsewhere in
    /// the SAME chunk instance — no chunk swap or loading screen, unlike DungeonPortal. For a
    /// sealed compound, secret tunnel, or one-way drop that doesn't warrant its own chunk.
    /// Drop this (and the target SceneMarker) in by hand; no placement tool needed for a
    /// two-field component like this one.
    /// </summary>
    public class LocalTeleporter : MonoBehaviour
    {
        [Tooltip("The SceneMarker.Key to teleport to, somewhere else in this same chunk.")]
        public string TargetMarkerKey;
        public string Prompt = "Enter";

        private void Awake()
        {
            var interactable = GetComponent<Interactable>();
            if (interactable == null)
            {
                interactable = gameObject.AddComponent<Interactable>();
                interactable.Prompt = Prompt;
                interactable.InteractRange = 3f;
            }
            interactable.OnInteract.AddListener(Teleport);
        }

        public void Teleport()
        {
            if (ChunkManager.Instance == null) return;

            GameObject chunkRoot = ChunkManager.Instance.CurrentChunkInstance;
            Vector3 pos = SceneMarker.ResolveWorldPosition(chunkRoot, TargetMarkerKey, transform.position);
            ChunkManager.Instance.TeleportPlayer(pos);
        }
    }
}
