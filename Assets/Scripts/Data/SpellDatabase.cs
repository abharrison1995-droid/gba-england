using System;
using System.Collections.Generic;
using UnityEngine;

namespace GBHEngland.Data
{
    /// <summary>
    /// Runtime lookup for the stable AbilityID values stored in savegame.json. Spell definitions
    /// live under Resources/Abilities so both normal progression and editor debug tools resolve the
    /// exact same objects.
    /// </summary>
    public static class SpellDatabase
    {
        private static AbilityData[] _all;
        private static Dictionary<string, AbilityData> _byId;
        private static List<string> _orderedIds;

        public static IReadOnlyList<AbilityData> All
        {
            get
            {
                EnsureLoaded();
                return _all;
            }
        }

        public static IReadOnlyList<string> CurrentSpellIds
        {
            get
            {
                EnsureLoaded();
                return _orderedIds;
            }
        }

        public static AbilityData Find(string abilityId)
        {
            if (string.IsNullOrWhiteSpace(abilityId)) return null;
            EnsureLoaded();
            _byId.TryGetValue(abilityId, out AbilityData ability);
            return ability;
        }

        /// <summary>Editor authoring calls this after creating/updating assets.</summary>
        public static void ResetCache()
        {
            _all = null;
            _byId = null;
            _orderedIds = null;
        }

        private static void EnsureLoaded()
        {
            if (_all != null && _byId != null && _orderedIds != null) return;

            _all = Resources.LoadAll<AbilityData>("Abilities");
            Array.Sort(_all, (a, b) => string.CompareOrdinal(a != null ? a.AbilityID : null,
                                                             b != null ? b.AbilityID : null));
            _byId = new Dictionary<string, AbilityData>(StringComparer.OrdinalIgnoreCase);
            _orderedIds = new List<string>(_all.Length);
            foreach (AbilityData ability in _all)
            {
                if (ability == null || string.IsNullOrWhiteSpace(ability.AbilityID)) continue;
                if (_byId.ContainsKey(ability.AbilityID))
                {
                    Debug.LogError($"SpellDatabase: duplicate AbilityID '{ability.AbilityID}' under Resources/Abilities.");
                    continue;
                }
                _byId.Add(ability.AbilityID, ability);
                _orderedIds.Add(ability.AbilityID);
            }
        }
    }
}
