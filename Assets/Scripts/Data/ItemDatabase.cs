using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// Looks up an <see cref="ItemData"/> asset by its <see cref="ItemData.ItemID"/>. Every item
    /// asset must live under a Resources/Items folder (any depth) — drop one in and it's
    /// findable, no manual registration step. Used to resolve item IDs back to assets when
    /// restoring a save.
    /// </summary>
    public static class ItemDatabase
    {
        private static Dictionary<string, ItemData> _byId;

        public static ItemData Find(string itemId)
        {
            if (string.IsNullOrEmpty(itemId)) return null;
            EnsureLoaded();
            _byId.TryGetValue(itemId, out ItemData item);
            if (item == null)
                Debug.LogWarning($"ItemDatabase: no item found for id '{itemId}'.");
            return item;
        }

        private static void EnsureLoaded()
        {
            if (_byId != null) return;

            _byId = new Dictionary<string, ItemData>();
            foreach (ItemData item in Resources.LoadAll<ItemData>("Items"))
            {
                if (item == null || string.IsNullOrEmpty(item.ItemID)) continue;
                if (_byId.ContainsKey(item.ItemID))
                {
                    Debug.LogWarning($"ItemDatabase: duplicate ItemID '{item.ItemID}' — '{item.name}' ignored.");
                    continue;
                }
                _byId.Add(item.ItemID, item);
            }
        }
    }
}
