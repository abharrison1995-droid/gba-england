using UnityEngine;
using System.Collections.Generic;

namespace ExiledAlvaston.Data
{
    [System.Serializable]
    public class DialogueChoice
    {
        [TextArea] public string ChoiceText;
        public DialogueNode NextNode;
        
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
        public CharacterData Speaker;
        [TextArea(3, 10)] public string DialogueText;
        public List<DialogueChoice> Choices = new List<DialogueChoice>();
    }

    /// <summary>
    /// Represents a full conversation tree.
    /// </summary>
    [CreateAssetMenu(fileName = "NewDialogueTree", menuName = "ExiledAlvaston/Data/Dialogue Tree")]
    public class DialogueData : ScriptableObject
    {
        public DialogueNode StartingNode;
    }
}
