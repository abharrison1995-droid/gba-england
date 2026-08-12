using ExiledAlvaston.Data;

namespace ExiledAlvaston.UI
{
    /// <summary>
    /// Canonical paper-doll wiring: EquipSlot0..7 in the scene map to these ItemTypes, in this
    /// order. The editor rebuild tool (InventoryWin95Builder) lays the slots out from the same
    /// table, so the runtime binding and the scene layout cannot drift apart.
    /// </summary>
    public static class EquipmentSlotMap
    {
        public static readonly ItemType[] SlotOrder =
        {
            ItemType.Head, ItemType.Chest, ItemType.Legs, ItemType.Boots, // left column
            ItemType.Weapon, ItemType.Cloak, ItemType.Belt, ItemType.Ring // right column
        };

        public const int SlotCount = 8;
    }
}
