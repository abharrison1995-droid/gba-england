using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Serialization;

namespace GBHEngland.Data
{
    /// <summary>
    /// How a <see cref="QuestStage"/> knows it is done.
    ///
    /// ⚠️ Serialized by integer index — APPEND ONLY (CLAUDE.md §7). Reordering or inserting a
    /// value silently repoints every stage authored in every existing QuestDefinition asset.
    /// </summary>
    public enum QuestConditionType
    {
        /// <summary>Interact with the QuestActor keyed <see cref="QuestStage.QuestKey"/>.</summary>
        TalkTo = 0,
        /// <summary>Kill <see cref="QuestStage.Count"/> QuestActors keyed <see cref="QuestStage.QuestKey"/>.</summary>
        Kill = 1,
        /// <summary>Carry an item. Reports only — it never completes the quest. See QuestConditionWatcher.</summary>
        Collect = 2,
        /// <summary>Stand within <see cref="QuestStage.ReachRadius"/> of the keyed SceneMarker.</summary>
        Reach = 3,
        /// <summary>Nothing watches this. Bespoke code calls QuestManager.CompleteQuest itself.</summary>
        Manual = 4
    }

    /// <summary>
    /// One item a multi-item <see cref="QuestConditionType.Collect"/> stage requires, alongside the
    /// stage's primary <see cref="QuestStage.Item"/>. Lets a "gather A, B and C" objective read as
    /// met only once the player carries every one.
    /// </summary>
    [Serializable]
    public class QuestCollectItem
    {
        public ItemData Item;
        public int Quantity = 1;
    }

    /// <summary>One step of a quest: what the player is told to do, and how the game notices they did.</summary>
    [Serializable]
    public class QuestStage
    {
        [TextArea]
        [Tooltip("Shown in the journal and the HUD tracker while this stage is current.")]
        public string Objective;

        public QuestConditionType ConditionType = QuestConditionType.Manual;

        [Tooltip("Matches a World/QuestActor.Key (TalkTo, Kill) or a World/SceneMarker.Key (Reach). " +
                 "Unused by Collect and Manual.")]
        public string QuestKey;

        [Header("Collect")]
        [Tooltip("The item the player has to be carrying. Collect only.")]
        public ItemData Item;
        [Tooltip("How many of Item. Collect only.")]
        public int Quantity = 1;
        [TextArea]
        [Tooltip("Collect only. Objective text shown once the player is carrying enough — e.g. " +
                 "\"Take the ledger back to Mosley.\" Leave empty to keep showing Objective. This " +
                 "flips both ways: drop or sell the item and it reverts.")]
        public string ObjectiveWhenMet = "";

        [Header("Kill")]
        [Tooltip("How many keyed actors have to die. Kill only.")]
        public int Count = 1;

        [Header("Reach")]
        [Tooltip("How close (horizontally) counts as arrived, in world units. Reach only.")]
        public float ReachRadius = 3f;

        // Appended after every existing field (CLAUDE.md §3): a stage authored before multi-item
        // Collect existed reads this back as an empty list, which is exactly the single-item
        // behaviour it had before.
        [Header("Collect (extra items)")]
        [Tooltip("Optional. A Collect stage reads 'met' only when the player carries Item AND every " +
                 "one of these too — a 'gather A, B and C' objective. Leave empty for a single-item " +
                 "collect. The hand-in dialogue still completes the quest as usual.")]
        public List<QuestCollectItem> AlsoCollect = new List<QuestCollectItem>();
    }

    /// <summary>What the player gets for finishing a quest.</summary>
    [Serializable]
    public class QuestReward
    {
        [Tooltip("Pounds paid into the player's wallet on completion. Leave at 0 for no payout.")]
        [FormerlySerializedAs("GoldAmount")]
        public int PoundsAmount;

        public ItemData Item;
        public int Quantity = 1;

        [Tooltip("Wipes the Knives level and restores concealment — the Officer Riggs 'diplomatic " +
                 "immunity' pay-off.")]
        public bool ClearsWantedLevel;

        // Appended after every existing field, so nothing above it shifts and quest assets
        // authored before XP existed simply read back 0 — no XP, the correct default.
        [Tooltip("XP granted on completion. Leave at 0 for none.")]
        public int XP;
    }

    /// <summary>
    /// A quest authored as data: its stages, and what finishing it pays out. Assets live in
    /// <c>Assets/Resources/Quests/</c> and are resolved by <see cref="QuestDatabase"/> using
    /// <see cref="Id"/>, which must match the <c>DialogueChoice.GrantQuestId</c> that starts the
    /// quest — nothing here starts a quest, it only describes one that dialogue started.
    ///
    /// ⚠️ <b>This type ships in every build</b>, because everything reachable from a
    /// <c>Resources/</c> folder does. Never add a <c>GameObject</c>, <c>Sprite</c>, <c>Prefab</c>
    /// or <c>AudioClip</c> field to it: one prefab reference drags that prefab's entire dependency
    /// graph into the build, which is exactly why <c>PlacementPresetLibrary</c> keys its entries by
    /// string instead of holding art-heavy presets directly (CLAUDE.md §13). <c>ItemData</c> is
    /// already Resources-resident and is the only asset reference allowed here.
    ///
    /// ⚠️ A quest with no definition asset is untouched by the whole system — <c>QuestDatabase</c>
    /// returns null and <c>QuestConditionWatcher</c> skips it. That containment is deliberate: the
    /// tutorial quests deliberately have no definition and must keep running off their own code.
    /// </summary>
    [CreateAssetMenu(fileName = "NewQuest", menuName = "GBH England/Data/Quest Definition")]
    public class QuestDefinition : ScriptableObject
    {
        [Tooltip("The save key. Must match the DialogueChoice.GrantQuestId that starts this quest, " +
                 "or nothing will ever link the two.")]
        public string Id;

        [Tooltip("Mirrors QuestProgress.Title — shown in the journal.")]
        public string Title;
        [Tooltip("Mirrors QuestProgress.Giver — who handed it out.")]
        public string Giver;
        [Tooltip("Mirrors QuestProgress.Location — where it sends you.")]
        public string Location;

        public List<QuestStage> Stages = new List<QuestStage>();

        public QuestReward Reward = new QuestReward();
    }
}
