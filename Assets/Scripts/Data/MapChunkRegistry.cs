using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// Every <see cref="MapChunkData"/> the game must be able to resolve by name, held in one
    /// asset under <c>Resources/</c> so it is reachable without the main scene being open.
    ///
    /// Why this exists alongside <c>ChunkManager.AllChunks</c>: that list lives on the ChunkManager
    /// in <c>c.unity</c>, so it can only be edited with the scene open. Interiors are authored from
    /// Prefab Mode, where the scene ChunkManager is not loaded — and
    /// <c>ChunkManager.EnsureKnownChunk</c> only patches the list for the current run, so a save
    /// made inside a chunk that reached the list that way cannot be loaded after a restart.
    /// A Resources asset is editable from anywhere and survives the app closing.
    ///
    /// <c>AllChunks</c> is still consulted first and is still authoritative for anything already
    /// authored there; this is a fallback, not a replacement.
    ///
    /// ⚠ The strings inside are <see cref="MapChunkData.ChunkName"/> values, which are save keys —
    /// this asset stores object references, not names, so adding a chunk here is safe, but it can
    /// never be a reason to normalise a name (CLAUDE.md §3).
    /// </summary>
    [CreateAssetMenu(fileName = "MapChunkRegistry", menuName = "GBH England/Data/Map Chunk Registry")]
    public class MapChunkRegistry : ScriptableObject
    {
        /// <summary>Path passed to <see cref="Resources.Load"/> — the asset must sit at Assets/Resources/MapChunkRegistry.asset.</summary>
        public const string ResourcePath = "MapChunkRegistry";

        [Tooltip("Every loadable chunk, including interiors that are not part of the overworld grid. " +
                 "Maintained by Tools > Place > Portal Placement; safe to add to by hand.")]
        public List<MapChunkData> Chunks = new List<MapChunkData>();

        // Only successful loads are cached. A miss must stay retryable: the editor tool can create
        // the asset mid-session, and caching "absent" would make it invisible until a domain reload.
        private static MapChunkRegistry _cached;

        /// <summary>The registry asset, or null if none has been created yet.</summary>
        public static MapChunkRegistry Load()
        {
            if (_cached != null) return _cached;
            _cached = Resources.Load<MapChunkRegistry>(ResourcePath);
            return _cached;
        }

        /// <summary>The chunk with this exact <see cref="MapChunkData.ChunkName"/>, or null.</summary>
        public MapChunkData Find(string chunkName)
        {
            if (string.IsNullOrEmpty(chunkName) || Chunks == null) return null;
            for (int i = 0; i < Chunks.Count; i++)
            {
                MapChunkData c = Chunks[i];
                if (c != null && c.ChunkName == chunkName) return c;
            }
            return null;
        }
    }
}
