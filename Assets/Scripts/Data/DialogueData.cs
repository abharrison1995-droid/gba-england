using UnityEngine;
using System.Collections.Generic;

namespace ExiledAlvaston.Data
{
    [System.Serializable]
    public class DialogueChoice
    {
        [TextArea] public string ChoiceText;
        public string NextNodeId;

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

        public bool MeetsRequirement(CoreTraits playerTraits)
        {
            if (string.IsNullOrEmpty(RequiredStat)) return true;

            // Simple mock evaluation
            if (RequiredStat == "STR" && playerTraits.Strength >= RequiredStatLevel) return true;
            if (RequiredStat == "INT" && playerTraits.Intelligence >= RequiredStatLevel) return true;
            if (RequiredStat == "Personality" && playerTraits.Awareness >= RequiredStatLevel) return true;

            return false;
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
