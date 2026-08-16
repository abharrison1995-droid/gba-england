using System.Collections.Generic;
using UnityEngine;

namespace GBHEngland.Data
{
    /// <summary>
    /// Looks up <see cref="PerkData"/> assets. Every perk asset must live under a Resources/Perks
    /// folder (any depth) — drop one in and it's listed, no manual registration step. Mirrors
    /// <see cref="WikiDatabase"/> and <see cref="ItemDatabase"/>.
    ///
    /// The folder does not exist yet. <c>Resources.LoadAll</c> on a missing folder returns an empty
    /// array rather than erroring, so everything downstream works against zero perks.
    /// </summary>
    public static class PerkDatabase
    {
        private static PerkData[] _all;
        private static Dictionary<string, PerkData> _byId;

        /// <summary>Every perk asset, in whatever order Resources returns them. Grouping/sorting is the UI's job.</summary>
        public static IReadOnlyList<PerkData> All
        {
            get { EnsureLoaded(); return _all; }
        }

        public static PerkData Find(string perkId)
        {
            if (string.IsNullOrEmpty(perkId)) return null;
            EnsureLoaded();
            _byId.TryGetValue(perkId, out PerkData perk);
            if (perk == null)
                Debug.LogWarning($"PerkDatabase: no perk found for id '{perkId}'.");
            return perk;
        }

        private static void EnsureLoaded()
        {
            if (_all != null) return;

            _all = Resources.LoadAll<PerkData>("Perks");
            _byId = new Dictionary<string, PerkData>();
            foreach (PerkData perk in _all)
            {
                if (perk == null || string.IsNullOrEmpty(perk.PerkId)) continue;
                if (_byId.ContainsKey(perk.PerkId))
                {
                    Debug.LogWarning($"PerkDatabase: duplicate PerkId '{perk.PerkId}' — '{perk.name}' ignored.");
                    continue;
                }
                _byId.Add(perk.PerkId, perk);
            }
        }
    }
}
