using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// What a perk effect does. Append-only: serialized by integer index inside every authored
    /// PerkData asset, so never insert or reorder — doing so silently rewrites every authored
    /// perk's effect into a different effect, with nothing logged. New effects go at the end.
    /// </summary>
    /// <remarks>
    /// Every member here has a live call site. Two families were deliberately left out of v1
    /// because they have nowhere to be read:
    ///
    /// - Ranged damage. There is no player ranged attack — CombatController has exactly two damage
    ///   sites, melee and spell, and RangedCaster is an EnemyAI field. Declaring it would let a
    ///   player spend a point on nothing. Append it the day a ranged attack lands.
    /// - Fire/Cold/Poison/Magic resistance. Nothing consults them; there is no damage-type system.
    ///   A perk raising one would move the character sheet's readout and no damage. Physical is the
    ///   exception and is real — it feeds EKVibe.ArmourReduction.
    ///
    /// Crime-layer effects (concealment, pickpocket odds, wanted decay) are excluded by the owner's
    /// settled decision, not by omission.
    /// </remarks>
    public enum PerkEffectType
    {
        MeleeDamagePercent = 0,
        SpellDamagePercent = 1,
        MaxHealthFlat = 2,
        MaxHealthPercent = 3,
        ArmourFlat = 4,
        MaxResourceFlat = 5,
        ResourceRegenPercent = 6,
        MoveSpeedPercent = 7,
        ExtraLootRolls = 8,
        /// <summary>Flat metres the player's melee hits shove the target — not a percentage,
        /// not a chance. Read by PlayerSession.MeleeKnockbackDistance.</summary>
        MeleeKnockback = 9
    }

    /// <summary>
    /// One thing a perk does. <see cref="Magnitude"/> is read as whole points for the Flat and
    /// ExtraLootRolls types and as a percentage for the Percent types — 15 meaning +15%.
    /// MeleeKnockback reads it as a flat metre value (2 = shoved two metres).
    /// </summary>
    [System.Serializable]
    public class PerkEffect
    {
        public PerkEffectType Type;
        public float Magnitude;
    }

    /// <summary>
    /// One spendable passive perk. Assets live in a Resources/Perks folder and are resolved by
    /// <see cref="PerkDatabase"/>.
    ///
    /// PerkId is a SAVE KEY: spends persist in SaveData.PerkIds by this string, so never rename one
    /// once shipped (same rule as ItemData.ItemID, MapChunkData.ChunkName and WikiEntryData.EntryID).
    /// Title and Description are the owner's own prose — no perk asset ships with this code.
    /// </summary>
    [CreateAssetMenu(fileName = "NewPerk", menuName = "ExiledAlvaston/Data/Perk")]
    public class PerkData : ScriptableObject
    {
        [Tooltip("Save key — never rename once shipped.")]
        public string PerkId;

        public string Title;

        [TextArea(3, 10)]
        public string Description;

        [Tooltip("Leave empty to allow every class. Mirrors ItemData.AllowedClasses.")]
        public PlayerClass[] AllowedClasses;

        [Tooltip("Earliest level this perk may be taken at.")]
        public int MinLevel = 2;

        [Tooltip("Perk that must already be owned. None = no prerequisite.")]
        public PerkData Prerequisite;

        public List<PerkEffect> Effects = new List<PerkEffect>();

        /// <summary>Same shape as <see cref="ItemData.CanBeUsedBy"/>: an empty list admits everyone.</summary>
        public bool CanBeTakenBy(PlayerClass playerClass)
        {
            if (AllowedClasses == null || AllowedClasses.Length == 0) return true;
            for (int i = 0; i < AllowedClasses.Length; i++)
            {
                if (AllowedClasses[i] == playerClass) return true;
            }
            return false;
        }
    }
}
