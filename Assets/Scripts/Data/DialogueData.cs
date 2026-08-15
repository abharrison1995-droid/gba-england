using UnityEngine;
using System.Collections.Generic;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// When a <see cref="DialogueChoice"/> is shown, keyed on a quest id.
    ///
    /// ⚠️ Serialized by integer index — APPEND ONLY (CLAUDE.md §7). Reordering or inserting a
    /// value silently repoints every choice authored in every existing DialogueData asset.
    /// </summary>
    public enum QuestGateType
    {
        /// <summary>No gate — the choice always shows (the default).</summary>
        None = 0,
        /// <summary>Shown only while the quest has not been started.</summary>
        NotStarted = 1,
        /// <summary>Shown only while the quest is active (started and not complete).</summary>
        Active = 2,
        /// <summary>Shown only once the quest is complete.</summary>
        Complete = 3,
        /// <summary>
        /// Shown only while the quest is active AND sitting on a specific stage index, given by
        /// <see cref="DialogueChoice.QuestGateStage"/>. Exists because <see cref="Active"/> cannot
        /// tell one beat of a multi-stage quest from another — a "go find him" nudge and a "you
        /// did it" payoff are both Active, and one conversation has to offer them separately.
        /// </summary>
        ActiveAtStage = 4
    }

    /// <summary>
    /// Optional merchant window opened by a dialogue choice. Serialized by integer index: append
    /// only, exactly like <see cref="QuestGateType"/>.
    /// </summary>
    public enum MerchantActionType
    {
        None = 0,
        Buy = 1,
        Sell = 2
    }

    /// <summary>
    /// Optional command applied to the active companion when a dialogue choice is picked.
    /// Serialized by integer index: append only, exactly like QuestGateType.
    /// </summary>
    public enum CompanionCommandType
    {
        None = 0,
        FightBesideMe = 1,
        StopFighting = 2,
        Dismiss = 3
    }

    [System.Serializable]
    public class DialogueChoice
    {
        [TextArea] public string ChoiceText;
        public string NextNodeId;

        [Header("Quest Gate (Optional)")]
        [Tooltip("If set, this choice is only shown while the named quest is in the chosen state. " +
                 "Lets one conversation branch per quest instead of one asset per state.")]
        public QuestGateType QuestGate = QuestGateType.None;
        [Tooltip("The quest id the QuestGate checks. Ignored when QuestGate is None.")]
        public string QuestGateId;
        [Tooltip("Stage index the quest must be sitting on. Only read when QuestGate is " +
                 "ActiveAtStage; ignored by every other gate, and 0 in every asset authored " +
                 "before this field existed.")]
        public int QuestGateStage;

        [Header("Stat Checks (Optional)")]
        public string RequiredStat; // e.g., "Personality", "STR"
        public int RequiredStatLevel;

        [Header("Item Check (Optional)")]
        [Tooltip("If set, this choice is greyed out until the player carries at least RequiredItemQuantity of this item — e.g. handing over quest proof.")]
        public ItemData RequiredItem;
        public int RequiredItemQuantity = 1;
        [Tooltip("If true, picking this choice removes RequiredItemQuantity of RequiredItem from the player's inventory.")]
        public bool ConsumeRequiredItem = true;

        [Header("Quest Grant (Optional)")]
        [Tooltip("If set, picking this choice starts this quest (popup appears when the chat ends).")]
        public string GrantQuestId;
        public string GrantQuestTitle;
        [TextArea] public string GrantQuestObjective;
        [Tooltip("Where the quest sends the player (shown on the quest detail page). Optional.")]
        public string GrantQuestLocation;

        [Header("Magic Tutorial (Optional)")]
        [Tooltip("Picking this choice teaches the first spell and opens the naming popup after the chat closes.")]
        public bool TeachSpark;
        [Tooltip("Picking this choice marks the given quest id complete.")]
        public string CompleteQuestId;

        [Header("Merchant (Optional)")]
        [Tooltip("Shop opened after this choice closes the conversation.")]
        public MerchantData Merchant;
        public MerchantActionType MerchantAction = MerchantActionType.None;

        [Header("Companion (Optional)")]
        [Tooltip("Picking this choice hires the companion with this CompanionDefinition.Id " +
                 "(CompanionManager.BeginContract — a Paid contract still charges its price, and " +
                 "an unaffordable or already-taken hire is refused with a toast). The conversation " +
                 "ends on the pick. Empty means the choice hires nobody.")]
        public string HireCompanionId;

        [Header("Companion Command (Optional)")]
        [Tooltip("Picking this choice applies a command to the active companion (fight beside you, " +
                 "stop fighting, or dismiss). The conversation ends on the pick. None means no command.")]
        public CompanionCommandType CompanionCommand = CompanionCommandType.None;

        public bool MeetsRequirement(CoreTraits playerTraits)
        {
            if (string.IsNullOrEmpty(RequiredStat)) return true;

            // Simple mock evaluation
            if (RequiredStat == "STR" && playerTraits.Strength >= RequiredStatLevel) return true;
            if (RequiredStat == "INT" && playerTraits.Intelligence >= RequiredStatLevel) return true;
            if (RequiredStat == "Personality" && playerTraits.Awareness >= RequiredStatLevel) return true;

            return false;
        }

        /// <summary>
        /// True if this choice's quest gate is satisfied by the current quest state. A choice
        /// with <see cref="QuestGate"/> None, or a gate whose quest id is empty, is always shown.
        /// A quest id that resolves to no progress record counts as NotStarted.
        /// </summary>
        public bool MeetsQuestGate()
        {
            if (QuestGate == QuestGateType.None || string.IsNullOrEmpty(QuestGateId)) return true;

            var mgr = Quests.QuestManager.Instance;
            bool started = mgr != null && mgr.Find(QuestGateId) != null;
            bool active = mgr != null && mgr.IsActive(QuestGateId);
            bool complete = mgr != null && mgr.IsComplete(QuestGateId);

            switch (QuestGate)
            {
                case QuestGateType.NotStarted: return !started;
                case QuestGateType.Active: return active;
                case QuestGateType.Complete: return complete;
                case QuestGateType.ActiveAtStage:
                {
                    // Must be active AND on the named stage. A completed quest reports the last
                    // stage index, so the active test is what stops a payoff branch reappearing
                    // forever once the quest is over.
                    if (!active) return false;
                    var progress = mgr.Find(QuestGateId);
                    return progress != null && progress.StageIndex == QuestGateStage;
                }
                default: return true;
            }
        }
    }

    [System.Serializable]
    public class DialogueNode
    {
        public string Id;
        public CharacterData Speaker;
        [TextArea(3, 10)] public string DialogueText;
        public List<DialogueChoice> Choices = new List<DialogueChoice>();
    }

    /// <summary>
    /// Represents a full conversation graph: a flat list of nodes, each with a string Id, wired
    /// together by DialogueChoice.NextNodeId. Convergence (two choices leading to the same node)
    /// and cycles are both legal — see CLAUDE.md §15.
    /// </summary>
    [CreateAssetMenu(fileName = "NewDialogueTree", menuName = "ExiledAlvaston/Data/Dialogue Tree")]
    public class DialogueData : ScriptableObject
    {
        public const string DefaultStartId = "start";
        public string StartNodeId = DefaultStartId;
        public List<DialogueNode> Nodes = new List<DialogueNode>();

        /// <summary>The opening node: by StartNodeId if set and found, else Nodes[0], else null.</summary>
        public DialogueNode StartNode()
        {
            if (Nodes == null || Nodes.Count == 0) return null;

            if (!string.IsNullOrEmpty(StartNodeId))
            {
                DialogueNode found = FindNode(StartNodeId);
                if (found != null) return found;
                Debug.LogWarning($"DialogueData '{name}': StartNodeId '{StartNodeId}' matches no node. " +
                    "Falling back to the first node in the list.", this);
            }

            return Nodes[0];
        }

        /// <summary>
        /// Linear scan over Nodes by Id. Deliberately not a Dictionary — a conversation is tens of
        /// nodes, this runs once per button press while the game is paused, and a Dictionary would
        /// need invalidating on every Inspector edit for no measurable benefit (CLAUDE.md §4:
        /// mobile-first, avoid allocation on hot/input paths — this isn't hot, but the discipline
        /// still applies and keeps the type trivially serializable).
        /// </summary>
        public DialogueNode FindNode(string id)
        {
            if (string.IsNullOrEmpty(id) || Nodes == null) return null;
            for (int i = 0; i < Nodes.Count; i++)
                if (Nodes[i] != null && Nodes[i].Id == id) return Nodes[i];
            return null;
        }
    }
}
