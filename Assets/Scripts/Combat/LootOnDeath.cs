using System.Collections.Generic;
using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.UI;

namespace ExiledAlvaston.Combat
{
    /// <summary>
    /// Optional death drop for an enemy: on <see cref="Health.OnDeath"/>, shows the same loot
    /// menu chests use (LootMenuUI already covers "chests/corpses"), granting taken entries to
    /// PlayerSession's inventory. No-ops silently if Loot is empty — most enemies won't drop
    /// anything. Pair with the Enemy Placement editor tool, or add by hand.
    /// </summary>
    [RequireComponent(typeof(Health))]
    public class LootOnDeath : MonoBehaviour
    {
        public LootDrop[] Loot;

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
            if (Loot == null || Loot.Length == 0) return;

            var entries = new List<LootEntry>();
            foreach (LootDrop drop in Loot)
            {
                if (drop == null || drop.Item == null || drop.Quantity <= 0) continue;

                ItemData item = drop.Item;
                int quantity = drop.Quantity;
                string label = quantity > 1 ? $"{item.ItemName} x{quantity}" : item.ItemName;

                entries.Add(new LootEntry
                {
                    Name = label,
                    Description = item.Description,
                    OnTaken = () =>
                    {
                        if (PlayerSession.Instance != null)
                            PlayerSession.Instance.AddItem(item, quantity);
                    }
                });
            }

            if (entries.Count > 0)
                LootMenuUI.Show(_health.DisplayName, entries);
        }
    }
}
