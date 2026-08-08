using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// WIKIBRITAIN entry categories. Append-only: serialized by integer index, so never
    /// insert or reorder — new categories go at the end.
    /// </summary>
    public enum WikiCategory
    {
        Locations,
        People,
        Magic,
        Items
    }

    /// <summary>
    /// One WIKIBRITAIN encyclopedia entry. Unlocked during play — entering the LinkedChunk,
    /// or talking to an NPC that grants it — and read in the bag's WIKIBRITAIN window.
    ///
    /// EntryID is a SAVE KEY: unlocks persist in SaveData.UnlockedWikiEntries by this string,
    /// so never rename one once shipped (same rule as ItemData.ItemID / MapChunkData.ChunkName).
    /// Body prose is the owner's own work — machinery ships with placeholder text only.
    /// </summary>
    [CreateAssetMenu(fileName = "NewWikiEntry", menuName = "ExiledAlvaston/Data/Wiki Entry")]
    public class WikiEntryData : ScriptableObject
    {
        [Tooltip("Save key — never rename once shipped.")]
        public string EntryID;
        public string Title;
        public WikiCategory Category;
        [TextArea(4, 14)]
        public string Body;
        [Tooltip("Banner across the top of the entry. Null shows a placeholder instead.")]
        public Sprite Image;
        [Tooltip("Location entries: entering this chunk unlocks the entry. Null = granted another way (NPC, quest).")]
        public MapChunkData LinkedChunk;
    }
}
