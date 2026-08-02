using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// A named tag on a real gameplay object (an enemy, an NPC, a chest) so quest code can find
    /// it by key and wire up quest-specific behavior (e.g. <c>Health.OnDeath</c>,
    /// <c>Interactable.OnInteract</c>) without the placement tool that created it needing to
    /// know anything about quests. Parallels <see cref="SceneMarker"/>, which does the same job
    /// for an empty position marker rather than a live object.
    /// </summary>
    public class QuestActor : MonoBehaviour
    {
        [Tooltip("What quest code looks this up by, e.g. \"BanditLeader\".")]
        public string Key;

        /// <summary>The GameObject tagged with the given key inside a chunk (null if none).</summary>
        public static GameObject Find(GameObject chunkRoot, string key)
        {
            if (chunkRoot == null || string.IsNullOrEmpty(key)) return null;
            foreach (var actor in chunkRoot.GetComponentsInChildren<QuestActor>(true))
                if (actor.Key == key) return actor.gameObject;
            return null;
        }

        /// <summary>
        /// Every GameObject tagged with the given key inside a chunk. <see cref="Find"/> stops at
        /// the first, which is no use to a "kill three of them" objective. The caller owns
        /// <paramref name="results"/> and it is cleared first, so the list can be reused across
        /// rebinds instead of allocating a fresh one each time (CLAUDE.md §4).
        /// </summary>
        public static void FindAll(GameObject chunkRoot, string key, List<GameObject> results)
        {
            if (results == null) return;
            results.Clear();
            if (chunkRoot == null || string.IsNullOrEmpty(key)) return;

            foreach (var actor in chunkRoot.GetComponentsInChildren<QuestActor>(true))
                if (actor.Key == key) results.Add(actor.gameObject);
        }
    }
}
