using System.Collections.Generic;
using UnityEngine;

namespace GBHEngland.World
{
    /// <summary>
    /// Shared save-id collision registry for every container component keyed off
    /// "&lt;ChunkName&gt;/&lt;Id&gt;" — <see cref="WorldContainer"/> and <see cref="SpriteContainer"/>
    /// write into the SAME <c>PlayerSession</c> looted/cooldown dictionaries under that key, so a
    /// collision between the two types empties both just as surely as a collision within one type.
    ///
    /// Each type used to track its own claims in a separate static Dictionary, which meant a
    /// WorldContainer and a SpriteContainer sharing an id in the same chunk went completely
    /// unnoticed by both — this is the one place both now check.
    /// </summary>
    internal static class ContainerIdRegistry
    {
        /// <summary>
        /// ⚠ Must be released in the owner's OnDestroy. Chunks are destroyed and rebuilt on every
        /// visit, so without that every re-entry would warn about the previous instance of itself.
        /// </summary>
        private static readonly Dictionary<string, Component> _claimedIds =
            new Dictionary<string, Component>();

        /// <summary>
        /// Claims a save id for a container instance. Logs and does not overwrite the existing
        /// claim on collision, so the first container to Awake keeps the slot and both are warned
        /// about by name — silently taking the id would just move the ambiguity elsewhere.
        /// </summary>
        public static void Claim(string containerId, Component owner, string chunkName)
        {
            if (string.IsNullOrEmpty(containerId) || owner == null) return;

            if (_claimedIds.TryGetValue(containerId, out Component existing) && existing != null)
            {
                Debug.LogWarning(
                    $"Container id collision: {owner.GetType().Name} '{owner.name}' and " +
                    $"{existing.GetType().Name} '{existing.name}' both claim '{containerId}' in " +
                    $"'{chunkName}'. They share one save slot — looting either empties both. Give " +
                    "one a different Save Id (WorldContainer) or a different GameObject name " +
                    "(SpriteContainer).", owner);
                return;
            }

            _claimedIds[containerId] = owner;
        }

        /// <summary>Releases a claim — a no-op if this owner never held it, so it is safe to call
        /// unconditionally from OnDestroy even when Claim warned instead of registering.</summary>
        public static void Release(string containerId, Component owner)
        {
            if (string.IsNullOrEmpty(containerId)) return;

            if (_claimedIds.TryGetValue(containerId, out Component existing) && existing == owner)
            {
                _claimedIds.Remove(containerId);
            }
        }
    }
}
