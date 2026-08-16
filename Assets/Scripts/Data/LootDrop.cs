using System;

namespace GBHEngland.Data
{
    /// <summary>
    /// One entry in a loot table (chest contents, enemy death drop). Shared by
    /// <see cref="GBHEngland.World.LootChest"/> and <see cref="GBHEngland.Combat.LootOnDeath"/>.
    /// </summary>
    [Serializable]
    public class LootDrop
    {
        public ItemData Item;
        public int Quantity = 1;
    }
}
