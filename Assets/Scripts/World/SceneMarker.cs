using UnityEngine;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// A named, draggable placement marker. Systems look one up by <see cref="Key"/> inside a
    /// chunk (e.g. the tutorial chest asks for "ChestSpawn") instead of hard-coding positions.
    /// Draws an amber gizmo so it's easy to see and drag in the Scene view.
    ///
    /// Like spawn points, markers must live in the chunk's PREFAB — chunks are instantiated from
    /// their prefab at runtime, so a copy left in the main scene is ignored.
    /// </summary>
    public class SceneMarker : MonoBehaviour
    {
        [Tooltip("What this marker is, e.g. \"ChestSpawn\". A system finds it by this exact key.")]
        public string Key;

        /// <summary>The marker transform with the given key inside a chunk (null if none).</summary>
        public static Transform Find(GameObject chunkRoot, string key)
        {
            if (chunkRoot == null || string.IsNullOrEmpty(key)) return null;
            foreach (var m in chunkRoot.GetComponentsInChildren<SceneMarker>(true))
                if (m.Key == key) return m.transform;
            return null;
        }

        /// <summary>World position of the keyed marker, or <paramref name="fallback"/> if absent.</summary>
        public static Vector3 ResolveWorldPosition(GameObject chunkRoot, string key, Vector3 fallback)
        {
            Transform t = Find(chunkRoot, key);
            return t != null ? t.position : fallback;
        }

#if UNITY_EDITOR
        private void OnDrawGizmos()
        {
            Vector3 p = transform.position;
            Gizmos.color = new Color(0.95f, 0.65f, 0.15f, 0.85f);
            Gizmos.DrawCube(p + Vector3.up * 0.03f, new Vector3(1f, 0.06f, 1f));
            Gizmos.color = new Color(0.95f, 0.65f, 0.15f, 0.35f);
            Gizmos.DrawWireCube(p + Vector3.up * 0.5f, new Vector3(0.8f, 1f, 0.8f));
        }

        private void OnDrawGizmosSelected()
        {
            UnityEditor.Handles.color = new Color(0.95f, 0.65f, 0.15f);
            UnityEditor.Handles.Label(transform.position + Vector3.up * 1.2f,
                string.IsNullOrEmpty(Key) ? "Marker" : Key);
        }
#endif
    }
}
