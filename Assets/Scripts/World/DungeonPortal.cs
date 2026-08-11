using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Generic two-way door between chunks: drop one in the overworld pointing at a dungeon or
    /// building interior chunk, and one inside that chunk pointing back. Uses the range-based
    /// interact system (walk up, press USE) — no colliders or trigger volumes.
    ///
    /// Author linked pairs with Tools/GBH/Place/Portal Placement, which creates both ends and
    /// their arrival markers together. Adding one by hand and filling in the fields still works.
    /// </summary>
    public class DungeonPortal : MonoBehaviour
    {
        [Tooltip("Chunk this portal loads. Must have a ChunkPrefab assigned.")]
        public MapChunkData TargetChunk;
        [Tooltip("Where the player appears in the target chunk. Ignored when Target Spawn Point Id " +
                 "is set. Put it a few units clear of the return portal.")]
        public Vector3 SpawnPosition;
        public string Prompt = "Enter";
        [Tooltip("Barred until the Manor Cellars tutorial is finished.")]
        public bool RequireTutorialComplete;

        // Appended, never inserted — Unity serializes by field order and every portal already
        // authored carries no value for this, so they all read empty and keep the raw-position
        // behaviour they have always had (CLAUDE.md §3).
        [Tooltip("PlayerSpawnPoint.Id to arrive at inside the target chunk. This is the way to " +
                 "author a door: the marker moves with the geometry it belongs to, where a raw " +
                 "Spawn Position quietly stops matching the moment the building is nudged.\n\n" +
                 "The marker's blue arrow sets arrival facing too.\n\n" +
                 "Leave empty to use Spawn Position instead. A non-empty id that does not resolve " +
                 "aborts the journey rather than falling back — see ChunkManager.TravelTo.")]
        public string TargetSpawnPointId = "";

        // Shared across all portals so arriving next to a paired return portal
        // can't immediately bounce the player back where they came from.
        private static float _nextUseAt;

        private void Awake()
        {
            var interactable = GetComponent<Interactable>();
            bool created = interactable == null;
            if (created)
            {
                interactable = gameObject.AddComponent<Interactable>();
                // Only set on a component we just made. An Interactable authored alongside this
                // portal — which is what the placement tool creates — carries a deliberate range,
                // and overwriting it here would silently discard whatever the designer set.
                interactable.InteractRange = 3f;
            }
            interactable.Prompt = Prompt;
            interactable.OnInteract.AddListener(Travel);
        }

        private void OnEnable()
        {
            _nextUseAt = Mathf.Max(_nextUseAt, Time.unscaledTime + 0.75f);
        }

        public void Travel()
        {
            if (Time.unscaledTime < _nextUseAt) return;

            if (RequireTutorialComplete
                && (PlayerSession.Instance == null || !PlayerSession.Instance.TutorialComplete))
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat("The way is barred for now.");
                return;
            }

            // Refused rather than handled: the vehicle is a separate root that would be left
            // behind in a chunk about to be destroyed, and the one obvious workaround — hiding or
            // disabling it — is exactly what must never be done to a vehicle root, because
            // OnDisable clears its speed multiplier (CLAUDE.md §3). Dismounting is the player's.
            if (MountController.IsPlayerRiding)
            {
                if (UIManager.Instance != null)
                    UIManager.Instance.LogCombat("Get off the vehicle first.");
                return;
            }

            if (TargetChunk == null || TargetChunk.ChunkPrefab == null)
            {
                Debug.LogWarning($"DungeonPortal '{name}': TargetChunk missing or has no prefab.");
                return;
            }
            if (ChunkManager.Instance == null)
            {
                Debug.LogWarning($"DungeonPortal '{name}': no ChunkManager in scene.");
                return;
            }

            _nextUseAt = Time.unscaledTime + 1.5f;

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat(Prompt + "...");

            ChunkManager.Instance.TravelTo(TargetChunk, TargetSpawnPointId, SpawnPosition);
        }

#if UNITY_EDITOR
        // A portal is a bare interaction point with no renderer of its own — most doorways already
        // have their own geometry, so the tool does not add a placeholder cube. Without a gizmo
        // there would be nothing to see or click in the Scene view. Amber pad + doorway arch, with
        // the interact radius drawn from whatever the Interactable actually carries.
        private void OnDrawGizmos()
        {
            Vector3 p = transform.position;

            Gizmos.color = new Color(1f, 0.72f, 0.2f, 0.85f);
            Gizmos.DrawCube(p + Vector3.up * 0.03f, new Vector3(1.1f, 0.06f, 1.1f));
            Gizmos.color = new Color(1f, 0.72f, 0.2f, 0.4f);
            Gizmos.DrawWireCube(p + Vector3.up * 1.1f, new Vector3(0.4f, 2.2f, 1.4f));

            // Which way through the door — the return marker is derived from this.
            Gizmos.color = new Color(1f, 0.55f, 0.1f, 1f);
            Vector3 tip = p + transform.forward * 1.4f + Vector3.up * 0.05f;
            Gizmos.DrawLine(p + Vector3.up * 0.05f, tip);

            var interactable = GetComponent<Interactable>();
            float range = interactable != null ? interactable.InteractRange : 3f;
            Gizmos.color = new Color(1f, 0.72f, 0.2f, 0.18f);
            Gizmos.DrawWireSphere(p, range);
        }

        private void OnDrawGizmosSelected()
        {
            string label = string.IsNullOrEmpty(Prompt) ? "Portal" : Prompt;
            if (TargetChunk != null)
            {
                label += $" → {TargetChunk.ChunkName}";
                if (!string.IsNullOrEmpty(TargetSpawnPointId))
                    label += $" [{TargetSpawnPointId}]";
            }
            UnityEditor.Handles.color = new Color(1f, 0.72f, 0.2f, 1f);
            UnityEditor.Handles.Label(transform.position + Vector3.up * 2.6f, label);
        }
#endif
    }
}
