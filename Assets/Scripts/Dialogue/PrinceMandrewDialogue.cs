using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;

namespace GBHEngland.Dialogue
{
    /// <summary>
    /// Builds and provides dialogue data for Prince Mandrew outside the Castle.
    /// Handles the 3 core options: Enter Arena, Royal Arena Shop, and Leave.
    /// </summary>
    public static class PrinceMandrewDialogue
    {
        public static DialogueData CreateDialogue(MerchantData royalShop = null, Sprite mandrewPortrait = null)
        {
            var data = ScriptableObject.CreateInstance<DialogueData>();
            data.name = "Dialogue_PrinceMandrew";
            data.StartNodeId = "start";

            var startNode = new DialogueNode
            {
                Id = "start",
                DialogueText = "Ah! You there! Yes, you! Care to partake in a spot of... sanctioned cardiovascular exertion? Good for the constitution, keeps the local ruffians employed. *dabs forehead with a silk handkerchief*",
                Choices = new List<DialogueChoice>
                {
                    new DialogueChoice
                    {
                        ChoiceText = "I'm ready to fight. Let me in the Castle Arena.",
                        NextNodeId = "enter_arena"
                    },
                    new DialogueChoice
                    {
                        ChoiceText = "What royal goods do you have for sale?",
                        NextNodeId = "shop"
                    },
                    new DialogueChoice
                    {
                        ChoiceText = "I'll leave you to your sweating, Your Highness.",
                        NextNodeId = "" // Ends chat cleanly
                    }
                }
            };

            var enterNode = new DialogueNode
            {
                Id = "enter_arena",
                DialogueText = "Splendid! The paperwork is frightfully lax today. Mind the bloodstains on the paving, won't you? Give those oiks what for!",
                Choices = new List<DialogueChoice>
                {
                    new DialogueChoice
                    {
                        ChoiceText = "[Enter the Castle Fight Arena]",
                        StartsFightPit = true
                    }
                }
            };

            var shopNode = new DialogueNode
            {
                Id = "shop",
                DialogueText = "Oh, just a few royal trinkets and antiquities that fell off the back of a gilded carriage. Mind you, the finest heirlooms are reserved for true champions of the arena!",
                Choices = new List<DialogueChoice>
                {
                    new DialogueChoice
                    {
                        ChoiceText = "[Browse the Royal Arena Shop]",
                        Merchant = royalShop,
                        MerchantAction = MerchantActionType.Buy
                    }
                }
            };

            data.Nodes.Add(startNode);
            data.Nodes.Add(enterNode);
            data.Nodes.Add(shopNode);
            return data;
        }
    }
}
