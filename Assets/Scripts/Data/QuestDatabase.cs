using System.Collections.Generic;
using UnityEngine;

namespace GBHEngland.Data
{
    /// <summary>
    /// Looks up a <see cref="QuestDefinition"/> asset by its <see cref="QuestDefinition.Id"/>.
    /// Every definition must live under a Resources/Quests folder (any depth) — drop one in and
    /// it's findable, no manual registration step. Mirrors <see cref="ItemDatabase"/>.
    ///
    /// A miss is not an error: quests with no definition (the tutorial's, today) are meant to be
    /// invisible to the definition system, so the caller treats null as "not my business".
    /// </summary>
    public static class QuestDatabase
    {
        private static Dictionary<string, QuestDefinition> _byId;

        public static QuestDefinition Find(string questId)
        {
            if (string.IsNullOrEmpty(questId)) return null;
            EnsureLoaded();
            _byId.TryGetValue(questId, out QuestDefinition definition);
            return definition;
        }

        /// <summary>Editor authoring calls this after creating/updating assets.</summary>
        public static void ResetCache()
        {
            _byId = null;
        }

        private static void EnsureLoaded()
        {
            if (_byId != null) return;

            _byId = new Dictionary<string, QuestDefinition>();
            foreach (QuestDefinition definition in Resources.LoadAll<QuestDefinition>("Quests"))
            {
                if (definition == null || string.IsNullOrEmpty(definition.Id)) continue;
                if (_byId.ContainsKey(definition.Id))
                {
                    Debug.LogWarning($"QuestDatabase: duplicate quest Id '{definition.Id}' — '{definition.name}' ignored.");
                    continue;
                }
                _byId.Add(definition.Id, definition);
            }
        }
    }
}
