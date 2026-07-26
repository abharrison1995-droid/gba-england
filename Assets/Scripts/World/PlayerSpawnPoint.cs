using UnityEngine;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Marks where the player arrives in a chunk. Drop one into a chunk prefab (via
    /// Tools/Exiled Alvaston/Place/Player Spawn Point, or add this component to an empty object)
    /// and every teleport into that chunk — world load, instance door, or DungeonPortal — puts
    /// the player here instead of at a hard-coded position.
    ///
    /// A chunk may hold several: give each an <see cref="Id"/> and a portal/door can ask for a
    /// specific one (e.g. "WestGate"). The first id-less point is the default.
    ///
    /// IMPORTANT: chunks are instantiated from their PREFAB at runtime, so this must live in the
    /// chunk's prefab asset (open it in Prefab Mode). Moving a copy in the main scene has no effect.
    /// </summary>
    public class PlayerSpawnPoint : MonoBehaviour
    {
        [Tooltip("Optional label so one chunk can have several arrival points. Empty = the default spawn.")]
        public string Id = "";

        /// <summary>Finds the matching spawn point inside an instantiated chunk (null if none).</summary>
        public static PlayerSpawnPoint Find(GameObject chunkRoot, string id = null)
        {
            if (chunkRoot == null) return null;
            var points = chunkRoot.GetComponentsInChildren<PlayerSpawnPoint>(true);
            if (points.Length == 0) return null;

            if (!string.IsNullOrEmpty(id))
            {
                foreach (var p in points)
                    if (p.Id == id) return p;
            }
            foreach (var p in points)
                if (string.IsNullOrEmpty(p.Id)) return p; // default (id-less) point
            return points[0];
        }

        /// <summary>
        /// World position the player should arrive at: the matching spawn point's position, or
        /// <paramref name="fallback"/> when the chunk has no spawn point.
        /// </summary>
        public static Vector3 ResolveWorldPosition(GameObject chunkRoot, Vector3 fallback, string id = null)
        {
            var sp = Find(chunkRoot, id);
            return sp != null ? sp.transform.position : fallback;
        }

#if UNITY_EDITOR
        // Green pad + pillar so the point is easy to see and select in the Scene view; blue arrow = facing.
        private void OnDrawGizmos()
        {
            Vector3 p = transform.position;
            Gizmos.color = new Color(0.25f, 0.9f, 0.35f, 0.85f);
            Gizmos.DrawCube(p + Vector3.up * 0.03f, new Vector3(1.3f, 0.06f, 1.3f));
            Gizmos.color = new Color(0.25f, 0.9f, 0.35f, 0.35f);
            Gizmos.DrawWireCube(p + Vector3.up * 1f, new Vector3(0.9f, 2f, 0.9f));

            Gizmos.color = new Color(0.2f, 0.5f, 1f, 1f);
            Vector3 tip = p + transform.forward * 1.6f + Vector3.up * 0.05f;
            Gizmos.DrawLine(p + Vector3.up * 0.05f, tip);
            Gizmos.DrawSphere(tip, 0.12f);
        }

        private void OnDrawGizmosSelected()
        {
            UnityEditor.Handles.color = Color.green;
            string label = "Player Spawn" + (string.IsNullOrEmpty(Id) ? "" : $" [{Id}]");
            UnityEditor.Handles.Label(transform.position + Vector3.up * 2.2f, label);
        }
#endif
    }
}
