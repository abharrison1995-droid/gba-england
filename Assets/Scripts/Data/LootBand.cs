using System;
using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>One weighted entry in a <see cref="LootBand"/>.</summary>
    [Serializable]
    public class LootBandEntry
    {
        public ItemData Item;

        [Tooltip("Relative chance against every other entry's weight, plus EmptyWeight. Not a " +
                 "percentage — a weight of 3 against a total of 12 is a one-in-four chance.")]
        public int Weight = 1;

        [Tooltip("Fewest of this item a single roll yields.")]
        public int MinQuantity = 1;

        [Tooltip("Most of this item a single roll yields. Inclusive.")]
        public int MaxQuantity = 1;

        [Tooltip("Taps needed to work this loose before it can be taken. Used by the pickpocket " +
                 "minigame; the container menu ignores it.")]
        public int TapsToFree = 1;
    }

    /// <summary>What one roll of a band produced.</summary>
    public class LootBandResult
    {
        public ItemData Item;
        public int Quantity;
        public int TapsToFree;
    }

    /// <summary>
    /// A weighted table of what might be inside something — a container, or a victim's pockets.
    /// Both roll through the same <see cref="Roll"/> so a band authored for one works in the other
    /// and there is one description of how weighting behaves.
    ///
    /// Weights are relative, not percentages. <see cref="EmptyWeight"/> is the chance of a roll
    /// yielding nothing at all, and counts towards the total like any entry, so a band of one item
    /// at weight 1 with EmptyWeight 3 pays out a quarter of the time.
    /// </summary>
    [CreateAssetMenu(fileName = "NewLootBand", menuName = "ExiledAlvaston/Data/Loot Band")]
    public class LootBand : ScriptableObject
    {
        public List<LootBandEntry> Entries = new List<LootBandEntry>();

        [Tooltip("How many independent rolls one open/pickpocket makes. Each can come up empty.")]
        public int RollCount = 1;

        [Tooltip("Weight of the 'nothing' outcome, counted alongside the entries. 0 means every " +
                 "roll yields something.")]
        public int EmptyWeight = 0;

        /// <summary>
        /// Rolls the band <paramref name="count"/> times and returns what came up. Never returns
        /// null — an empty list is the ordinary "their pockets were empty" outcome, and callers
        /// have to cope with it anyway because <see cref="EmptyWeight"/> exists.
        ///
        /// A band whose weights total zero or less cannot be rolled meaningfully, so it warns
        /// naming itself and returns nothing rather than picking arbitrarily. That is an authoring
        /// mistake — every entry left at weight 0 — and silence would look like bad luck.
        /// </summary>
        public List<LootBandResult> Roll(int count)
        {
            var results = new List<LootBandResult>();
            if (count <= 0) return results;

            int total = Mathf.Max(0, EmptyWeight);
            if (Entries != null)
            {
                for (int i = 0; i < Entries.Count; i++)
                {
                    var entry = Entries[i];
                    if (entry == null || entry.Item == null || entry.Weight <= 0) continue;
                    total += entry.Weight;
                }
            }

            if (total <= 0)
            {
                Debug.LogWarning(
                    $"LootBand '{name}': every entry has a weight of 0 or no Item, and EmptyWeight " +
                    "is 0 too, so there is nothing to roll. Give at least one entry an Item and a " +
                    "Weight above 0.", this);
                return results;
            }

            for (int roll = 0; roll < count; roll++)
            {
                int pick = UnityEngine.Random.Range(0, total);

                // EmptyWeight occupies the first slice, so a band that is mostly empty short-
                // circuits without walking the entries.
                if (pick < EmptyWeight) continue;
                pick -= Mathf.Max(0, EmptyWeight);

                if (Entries == null) continue;

                for (int i = 0; i < Entries.Count; i++)
                {
                    var entry = Entries[i];
                    if (entry == null || entry.Item == null || entry.Weight <= 0) continue;

                    if (pick < entry.Weight)
                    {
                        int min = Mathf.Max(1, entry.MinQuantity);
                        int max = Mathf.Max(min, entry.MaxQuantity);

                        results.Add(new LootBandResult
                        {
                            Item = entry.Item,
                            Quantity = UnityEngine.Random.Range(min, max + 1),
                            TapsToFree = Mathf.Max(1, entry.TapsToFree),
                        });
                        break;
                    }
                    pick -= entry.Weight;
                }
            }

            return results;
        }

        /// <summary>Rolls <see cref="RollCount"/> times — the ordinary entry point.</summary>
        public List<LootBandResult> Roll() => Roll(Mathf.Max(1, RollCount));
    }
}
