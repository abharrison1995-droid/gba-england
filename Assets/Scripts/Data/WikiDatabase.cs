using System.Collections.Generic;
using UnityEngine;

namespace GBHEngland.Data
{
    /// <summary>
    /// Looks up <see cref="WikiEntryData"/> assets. Every entry asset must live under a
    /// Resources/Wiki folder (any depth) — drop one in and it's listed, no manual
    /// registration step. Mirrors <see cref="ItemDatabase"/>.
    /// </summary>
    public static class WikiDatabase
    {
        private static WikiEntryData[] _all;
        private static Dictionary<string, WikiEntryData> _byId;

        /// <summary>Every entry asset, in whatever order Resources returns them. Grouping/sorting is the UI's job.</summary>
        public static IReadOnlyList<WikiEntryData> All
        {
            get { EnsureLoaded(); return _all; }
        }

        public static WikiEntryData Find(string entryId)
        {
            if (string.IsNullOrEmpty(entryId)) return null;
            EnsureLoaded();
            _byId.TryGetValue(entryId, out WikiEntryData entry);
            if (entry == null)
                Debug.LogWarning($"WikiDatabase: no entry found for id '{entryId}'.");
            return entry;
        }

        /// <summary>The location entry unlocked by entering the named chunk, if one is linked to it.</summary>
        public static WikiEntryData FindForChunk(string chunkName)
        {
            if (string.IsNullOrEmpty(chunkName)) return null;
            EnsureLoaded();
            foreach (WikiEntryData entry in _all)
            {
                if (entry != null && entry.LinkedChunk != null && entry.LinkedChunk.ChunkName == chunkName)
                    return entry;
            }
            return null;
        }

        private static void EnsureLoaded()
        {
            if (_all != null) return;

            _all = Resources.LoadAll<WikiEntryData>("Wiki");
            _byId = new Dictionary<string, WikiEntryData>();
            foreach (WikiEntryData entry in _all)
            {
                if (entry == null || string.IsNullOrEmpty(entry.EntryID)) continue;
                if (_byId.ContainsKey(entry.EntryID))
                {
                    Debug.LogWarning($"WikiDatabase: duplicate EntryID '{entry.EntryID}' — '{entry.name}' ignored.");
                    continue;
                }
                _byId.Add(entry.EntryID, entry);
            }
        }
    }
}
