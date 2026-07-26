using System;
using UnityEngine;
using ExiledAlvaston.Data;
using ExiledAlvaston.Dialogue;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Quests;

namespace ExiledAlvaston.World
{
    /// <summary>One quest-gated conversation variant — checked in StateOverrides order, first match wins.</summary>
    [Serializable]
    public class QuestStateDialogue
    {
        [Tooltip("Shown if this quest id is complete. Checked before IfQuestActive.")]
        public string IfQuestComplete;
        [Tooltip("Shown if this quest id has been started and isn't complete yet.")]
        public string IfQuestActive;
        public DialogueData Conversation;
    }

    /// <summary>
    /// Drop this on any NPC alongside an Interactable to make "talk to them" work — wires
    /// itself to Interactable.OnInteract automatically. Assign Conversation in the Inspector.
    ///
    /// For a quest giver with different lines before/during/after their quest, add entries to
    /// StateOverrides instead of writing a bespoke NPC script — the first matching entry's
    /// Conversation is shown; Conversation itself is the fallback when nothing matches (e.g.
    /// quest not yet started). Leave StateOverrides empty for a plain always-the-same-line NPC.
    /// </summary>
    [RequireComponent(typeof(Interactable))]
    public class NPCDialogueInteractable : MonoBehaviour
    {
        public DialogueData Conversation;
        public QuestStateDialogue[] StateOverrides;

        private void Awake()
        {
            var interactable = GetComponent<Interactable>();
            if (interactable != null)
            {
                if (string.IsNullOrEmpty(interactable.Prompt) || interactable.Prompt == "Interact")
                    interactable.Prompt = "Talk";
                interactable.OnInteract.AddListener(StartTalking);
            }
        }

        private void StartTalking()
        {
            DialogueData conversation = ResolveConversation();
            if (conversation == null)
            {
                Debug.LogWarning($"NPCDialogueInteractable on {name}: no Conversation assigned.");
                return;
            }
            CharacterData playerData = CombatController.Instance != null ? CombatController.Instance.PlayerData : null;
            DialogueManager.Ensure().StartDialogue(conversation, playerData);
        }

        private DialogueData ResolveConversation()
        {
            if (StateOverrides != null && QuestManager.Instance != null)
            {
                foreach (var state in StateOverrides)
                {
                    if (state == null || state.Conversation == null) continue;
                    if (!string.IsNullOrEmpty(state.IfQuestComplete) && QuestManager.Instance.IsComplete(state.IfQuestComplete))
                        return state.Conversation;
                    if (!string.IsNullOrEmpty(state.IfQuestActive) && QuestManager.Instance.IsActive(state.IfQuestActive))
                        return state.Conversation;
                }
            }
            return Conversation;
        }
    }
}
