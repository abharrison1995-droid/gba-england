using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.UI;

namespace GBHEngland.Combat
{
    /// <summary>
    /// Optional death drop for an enemy: on <see cref="Health.OnDeath"/>, shows the same loot
    /// menu chests use (LootMenuUI already covers "chests/corpses"), granting taken entries to
    /// PlayerSession's inventory. No-ops silently if Loot is empty — most enemies won't drop
    /// anything. Authored via an enemy `PlacementPreset`'s Loot list (stamped through the World
    /// Palette), or added by hand.
    /// </summary>
    [RequireComponent(typeof(Health))]
    public class LootOnDeath : MonoBehaviour
    {
        public LootDrop[] Loot;

        [Tooltip("Optional weighted drops rolled once on death, in addition to fixed Loot.")]
        public LootBand Band;

        private Health _health;

        private void Awake()
        {
            _health = GetComponent<Health>();
            _health.OnDeath.AddListener(OnDied);
        }

        private void OnDestroy()
        {
            if (_health != null)
                _health.OnDeath.RemoveListener(OnDied);
        }

        private void OnDied()
        {
            var entries = new List<LootEntry>();
            if (Loot != null)
            {
                foreach (LootDrop drop in Loot)
                {
                    if (drop == null || drop.Item == null || drop.Quantity <= 0) continue;

                    AddEntry(entries, drop.Item, drop.Quantity);
                }
            }

            if (Band != null)
            {
                foreach (LootBandResult result in Band.Roll())
                {
                    if (result == null || result.Item == null || result.Quantity <= 0) continue;
                    AddEntry(entries, result.Item, result.Quantity);
                }
            }

            if (entries.Count > 0)
                LootMenuUI.Show(_health.DisplayName, entries);
        }

        private static void AddEntry(List<LootEntry> entries, ItemData item, int quantity)
        {
            string label = quantity > 1 ? $"{item.ItemName} x{quantity}" : item.ItemName;
            entries.Add(new LootEntry
            {
                Name = label,
                Description = item.Description,
                Icon = item.Icon,
                OnTaken = () =>
                {
                    if (PlayerSession.Instance != null)
                        PlayerSession.Instance.AddItem(item, quantity);
                }
            });
        }
    }
}
