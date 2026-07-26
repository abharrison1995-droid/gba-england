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
    }
}
