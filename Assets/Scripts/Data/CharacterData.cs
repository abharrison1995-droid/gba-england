using UnityEngine;
using System.Collections.Generic;

namespace ExiledAlvaston.Data
{
    [System.Serializable]
    public class CoreTraits
    {
        public int Strength;
        public int Endurance;
        public int Agility;
        public int Intelligence;
        public int Awareness;
        public int Perception;
    }

    [System.Serializable]
    public class Resistances
    {
        public int Physical;
        public int Magic;
        public int Fire;
        public int Cold;
        public int Poison;
    }

    /// <summary>
    /// Base configuration for any character (Player, Companion, NPC, Enemy)
    /// </summary>
    [CreateAssetMenu(fileName = "NewCharacterData", menuName = "ExiledAlvaston/Data/Character Data")]
    public class CharacterData : ScriptableObject
    {
        [Header("Identity")]
        public string CharacterName;
        public Sprite Portrait;
        public PlayerClass Class;

        [Header("Base Stats")]
        public int MaxHealth;
        public int MaxManaStamina;
        public int BaseMovementSpeed;

        [Header("RPG Attributes")]
        public CoreTraits BaseTraits;
        public Resistances BaseResistances;

        /// <summary>Apply Discover England class baselines (keeps name/portrait).</summary>
        public void ApplyClassDefaults(PlayerClass playerClass)
        {
            Class = playerClass;
            BaseTraits = PlayerClassInfo.StartingTraits(playerClass);
            MaxHealth = PlayerClassInfo.StartingMaxHealth(playerClass);
            MaxManaStamina = PlayerClassInfo.StartingMaxResource(playerClass);
            if (BaseMovementSpeed <= 0) BaseMovementSpeed = 5;
        }
    }
}
