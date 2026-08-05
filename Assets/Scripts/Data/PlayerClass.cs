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
        BundaBasher = 4   // Bash
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
                case PlayerClass.Dynamo: return "Pulled one too many rabbits out of one too many hats.";
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
        /// ⚠️ Owner-editable copy. Ranged and Stab come straight from their class's own tagline,
        /// and Bash from Bunda Basher's. Two are inferred rather than stated: Blade, read off
        /// Young Driller's "good with a ZK", and Magic, which was stated by Dynamo's previous
        /// tagline before it was replaced on 2026-08-05 — his current line names no discipline.
        /// </remarks>
        public static string SpecialismLabel(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller: return "Blade";
                case PlayerClass.Stabmeister: return "Stab";
                case PlayerClass.MrHood: return "Ranged";
                case PlayerClass.Dynamo: return "Magic";
                // "Bash" rather than "Blunt" to follow Stabmeister's precedent, where the label is
                // the class's own verb. Proposed 2026-08-05, owner-editable like the rest.
                case PlayerClass.BundaBasher: return "Bash";
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
                // Proposed 2026-08-05, owner-editable. 32 points, matching Young Driller,
                // Stabmeister and Dynamo (Mr Hood is the outlier at 34). Spent on the one shape
                // no other class occupies: the slow bruiser. Top Strength and Endurance in the
                // roster, and the lowest Agility and Intelligence — he is meant to be telegraphed
                // and to not care. Stabmeister is the nearest neighbour at STR 8 / END 7; the
                // AGI 5→3 and INT 4→2 gap is what keeps them from being the same character.
                case PlayerClass.BundaBasher:
                    return new CoreTraits { Strength = 9, Endurance = 8, Agility = 3, Intelligence = 2, Awareness = 5, Perception = 5 };
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
                case PlayerClass.BundaBasher: return 140; // proposed 2026-08-05; the roster's tank
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
                case PlayerClass.BundaBasher: return 40; // proposed 2026-08-05; least finesse, least resource
                default: return 50;
            }
        }
    }
}
