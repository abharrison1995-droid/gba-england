using System;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// One entry in a loot table (chest contents, enemy death drop). Shared by
    /// <see cref="ExiledAlvaston.World.LootChest"/> and <see cref="ExiledAlvaston.Combat.LootOnDeath"/>.
    /// </summary>
    [Serializable]
    public class LootDrop
    {
        public ItemData Item;
        public int Quantity = 1;
    }
}
