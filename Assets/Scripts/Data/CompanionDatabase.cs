using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// Looks up a <see cref="CompanionDefinition"/> asset by its <see cref="CompanionDefinition.Id"/>.
    /// Every definition must live under a Resources/Companions folder (any depth) - drop one in and
    /// it is findable, no manual registration step. Mirrors <see cref="QuestDatabase"/>.
    ///
    /// A miss is not an error: CompanionManager treats null as "no definition for that id" and says
    /// so rather than throwing, so an authoring gap surfaces as a clear log line instead of a crash.
    /// </summary>
    public static class CompanionDatabase
    {
        private static Dictionary<string, CompanionDefinition> _byId;

        public static CompanionDefinition Find(string companionId)
        {
            if (string.IsNullOrEmpty(companionId)) return null;
            EnsureLoaded();
            _byId.TryGetValue(companionId, out CompanionDefinition definition);
            return definition;
        }

        private static void EnsureLoaded()
        {
            if (_byId != null) return;

            _byId = new Dictionary<string, CompanionDefinition>();
            foreach (CompanionDefinition definition in Resources.LoadAll<CompanionDefinition>("Companions"))
            {
                if (definition == null || string.IsNullOrEmpty(definition.Id)) continue;
                if (_byId.ContainsKey(definition.Id))
                {
                    Debug.LogWarning($"CompanionDatabase: duplicate companion Id '{definition.Id}' - '{definition.name}' ignored.");
                    continue;
                }
                _byId.Add(definition.Id, definition);
            }
        }
    }
}
