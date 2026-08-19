using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Vibe;

namespace GBHEngland.Combat
{
    /// <summary>
    /// Builds runtime dialogue trees for the Fight Pit between-round options (Continue / Cash Out).
    /// </summary>
    public static class FightPitDialogue
    {
        /// <summary>
        /// Creates a runtime DialogueData ScriptableObject offering the player the choice to continue or cash out.
        /// Caller is responsible for destroying the runtime DialogueData instance when finished to avoid leaks.
        /// </summary>
        public static DialogueData CreateBetweenRoundDialogue(int completedRoundIndex, int runningPurse, int cashOutAmount)
        {
            var data = ScriptableObject.CreateInstance<DialogueData>();
            data.name = $"RuntimeDialogue_PitRound_{completedRoundIndex + 1}";
            data.StartNodeId = "start";

            string formattedPurse = EKVibe.FormatPounds(runningPurse);
            string formattedCashOut = EKVibe.FormatPounds(cashOutAmount);

            var node = new DialogueNode
            {
                Id = "start",
                DialogueText = $"!DO YOU WISH TO CONTINUE WITH THE OIK BASHING? *sweats profusely*\n\n" +
                               $"Round {completedRoundIndex + 1} Cleared! Running Purse: {formattedPurse}.\n" +
                               $"Take your winnings ({formattedCashOut}) or press on to Round {completedRoundIndex + 2}?",
                Choices = new List<DialogueChoice>
                {
                    new DialogueChoice
                    {
                        ChoiceText = "YES LETS GO",
                        IsFightPitContinue = true
                    },
                    new DialogueChoice
                    {
                        ChoiceText = "GET ME OUTTA HERE!!!",
                        IsFightPitCashOut = true
                    }
                }
            };

            data.Nodes.Add(node);
            return data;
        }

        /// <summary>
        /// Cleans up a runtime DialogueData ScriptableObject.
        /// </summary>
        public static void DestroyDialogue(ref DialogueData dialogue)
        {
            if (dialogue != null)
            {
                Object.Destroy(dialogue);
                dialogue = null;
            }
        }
    }
}
