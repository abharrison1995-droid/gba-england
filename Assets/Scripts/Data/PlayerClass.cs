using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// Discover England player classes.
    /// </summary>
    public enum PlayerClass
    {
        YoungDriller = 0, // ZK / zombie knife
        EnGarde = 1,      // Long swords
        MrHood = 2,       // Ranged
        Dynamo = 3        // Magic
    }

    public static class PlayerClassInfo
    {
        public static string DisplayName(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller: return "Young Driller";
                case PlayerClass.EnGarde: return "En Garde";
                case PlayerClass.MrHood: return "Mr Hood";
                case PlayerClass.Dynamo: return "Dynamo";
                default: return c.ToString();
            }
        }

        public static string Tagline(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller: return "Good with a ZK. Close-range chaos from the ends.";
                case PlayerClass.EnGarde: return "Good with long swords. Proper blade work.";
                case PlayerClass.MrHood: return "Good with ranged. Keep your distance, stay hooded.";
                case PlayerClass.Dynamo: return "Good with magic. Street-level spark and pressure.";
                default: return "";
            }
        }

        public static string StartingWeaponLabel(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller: return "ZK (Zombie Knife)";
                case PlayerClass.EnGarde: return "Long Sword";
                case PlayerClass.MrHood: return "Hood Bow";
                case PlayerClass.Dynamo: return "Dynamo Charm";
                default: return "Fists";
            }
        }

        /// <summary>Baseline traits applied at character creation.</summary>
        public static CoreTraits StartingTraits(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.YoungDriller:
                    return new CoreTraits { Strength = 7, Endurance = 6, Agility = 7, Intelligence = 3, Awareness = 5, Perception = 4 };
                case PlayerClass.EnGarde:
                    return new CoreTraits { Strength = 8, Endurance = 7, Agility = 5, Intelligence = 4, Awareness = 4, Perception = 4 };
                case PlayerClass.MrHood:
                    return new CoreTraits { Strength = 4, Endurance = 5, Agility = 7, Intelligence = 4, Awareness = 6, Perception = 8 };
                case PlayerClass.Dynamo:
                    return new CoreTraits { Strength = 3, Endurance = 5, Agility = 5, Intelligence = 8, Awareness = 6, Perception = 5 };
                default:
                    return new CoreTraits { Strength = 5, Endurance = 5, Agility = 5, Intelligence = 5, Awareness = 5, Perception = 5 };
            }
        }

        public static int StartingMaxHealth(PlayerClass c)
        {
            switch (c)
            {
                case PlayerClass.EnGarde: return 120;
                case PlayerClass.YoungDriller: return 100;
                case PlayerClass.MrHood: return 90;
                case PlayerClass.Dynamo: return 85;
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
                case PlayerClass.EnGarde: return 50;
                default: return 50;
            }
        }
    }
}
