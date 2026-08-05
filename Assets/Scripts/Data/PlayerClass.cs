using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// Discover England player classes.
    /// </summary>
    public enum PlayerClass
    {
        YoungDriller = 0, // Blade
        Stabmeister = 1,  // Stab. Replaced EnGarde in place: the identifier changed, the
                          // index did not, and PlayerClass is saved as an int
                          // (SaveGameManager.PlayerClass), so existing saves carrying 1 load
                          // straight into Stabmeister. Never renumber this enum.
        MrHood = 2,       // Ranged
        Dynamo = 3,       // Magic
        BundaBasher = 4   // Owner-defined class details pending
    }

    public static class PlayerClassInfo
    {
        public static string DisplayName(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller: return "Young Driller";
                case PlayerClass.Stabmeister: return "Stabmeister";
                case PlayerClass.MrHood: return "Mr Hood";
                case PlayerClass.Dynamo: return "Dynamo";
                case PlayerClass.BundaBasher: return "Bunda Basher";
                default: return c.ToString();
            }
        }

        public static string Tagline(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller: return "Good with a ZK. Close-range chaos from the ends.";
                case PlayerClass.Stabmeister: return "Stab by name, stab by nature.";
                case PlayerClass.MrHood: return "Good with ranged. Keep your distance, stay hooded.";
                case PlayerClass.Dynamo: return "Good with magic. Street-level spark and pressure.";
                case PlayerClass.BundaBasher: return "If there's a bunda about, it's getting bashed.";
                default: return "";
            }
        }

        /// <summary>
        /// What the class is good at. Replaced <c>StartingWeaponLabel</c>: no class starts
        /// with a weapon, so advertising one in the creator promised something the game does
        /// not deliver. These are damage specialisms, not equipment.
        /// </summary>
        /// <remarks>
        /// ⚠️ Owner-editable copy. Ranged, Magic and Stab all come straight from their class's
        /// own tagline. Blade is the one still inferred rather than stated — it is read off
        /// Young Driller's "good with a ZK" — and Bunda Basher has no design yet.
        /// </remarks>
        public static string SpecialismLabel(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller: return "Blade";
                case PlayerClass.Stabmeister: return "Stab";
                case PlayerClass.MrHood: return "Ranged";
                case PlayerClass.Dynamo: return "Magic";
                // Owner-editable placeholder until the class design is supplied.
                case PlayerClass.BundaBasher: return "Not set";
                default: return "Unarmed";
            }
        }

        /// <summary>Baseline traits applied at character creation.</summary>
        public static CoreTraits StartingTraits(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller:
                    return new CoreTraits { Strength = 7, Endurance = 6, Agility = 7, Intelligence = 3, Awareness = 5, Perception = 4 };
                case PlayerClass.Stabmeister:
                    return new CoreTraits { Strength = 8, Endurance = 7, Agility = 5, Intelligence = 4, Awareness = 4, Perception = 4 };
                case PlayerClass.MrHood:
                    return new CoreTraits { Strength = 4, Endurance = 5, Agility = 7, Intelligence = 4, Awareness = 6, Perception = 8 };
                case PlayerClass.Dynamo:
                    return new CoreTraits { Strength = 3, Endurance = 5, Agility = 5, Intelligence = 8, Awareness = 6, Perception = 5 };
                // Neutral owner-editable placeholder until the class design is supplied.
                case PlayerClass.BundaBasher:
                    return new CoreTraits { Strength = 5, Endurance = 5, Agility = 5, Intelligence = 5, Awareness = 5, Perception = 5 };
                default:
                    return new CoreTraits { Strength = 5, Endurance = 5, Agility = 5, Intelligence = 5, Awareness = 5, Perception = 5 };
            }
        }

        public static int StartingMaxHealth(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.Stabmeister: return 120;
                case PlayerClass.YoungDriller: return 100;
                case PlayerClass.MrHood: return 90;
                case PlayerClass.Dynamo: return 85;
                case PlayerClass.BundaBasher: return 100; // neutral owner-editable placeholder
                default: return 100;
            }
        }

        public static int StartingMaxResource(PlayerClass c)
        {
            // Mana for Dynamo, stamina-ish for others
            switch (c)
            {
                case PlayerClass.Dynamo: return 80;
                case PlayerClass.MrHood: return 60;
                case PlayerClass.YoungDriller: return 55;
                case PlayerClass.Stabmeister: return 50;
                case PlayerClass.BundaBasher: return 50; // neutral owner-editable placeholder
                default: return 50;
            }
        }
    }
}
