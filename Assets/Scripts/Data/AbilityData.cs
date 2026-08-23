using UnityEngine;

namespace GBHEngland.Data
{
    public enum AbilityResourceType
    {
        Mana,
        Stamina,
        None
    }

    /// <summary>
    /// Runtime behaviour selected by an <see cref="AbilityData"/> spell. Explicit values are
    /// intentional: these values are serialized into the six spell assets, so future members must
    /// be appended and the existing numbers must never move.
    /// </summary>
    public enum SpellEffectType
    {
        None = 0,
        Spark = 1,
        Fireball = 2,
        HealingAura = 3,
        IronSkin = 4,
        SludgeBolt = 5,
        LightFeet = 6
    }

    /// <summary>
    /// Which special melee move an <see cref="AbilityData"/> runs when IsSpecialAttack is set.
    /// Explicit values for the same reason <see cref="SpellEffectType"/> has them: the numbers are
    /// serialized into the special-attack assets, so members are appended and never renumbered —
    /// renumbering would swap the spin and the dash on assets already authored.
    ///
    /// None = 0 is deliberate. An asset whose kind was never set must be REFUSED at use time, not
    /// silently become a spin.
    /// </summary>
    public enum SpecialAttackKind
    {
        None = 0,
        Spin = 1,
        Dash = 2
    }

    /// <summary>
    /// Represents an equippable spell or action.
    /// </summary>
    [CreateAssetMenu(fileName = "NewAbilityData", menuName = "GBH England/Data/Ability Data")]
    public class AbilityData : ScriptableObject
    {
        public string AbilityID;
        public string AbilityName;
        [TextArea] public string Description;
        public Sprite Icon;
        [Tooltip("Placeholder glyph/emoji shown on the spell button when no Icon sprite is set, e.g. \"⚡\".")]
        public string IconGlyph;

        [Header("Mechanics")]
        public float CooldownTime;
        public float CastTime;
        public float Range;
        
        [Header("Costs")]
        public AbilityResourceType ResourceType;
        public int ResourceCost;

        [Header("Effect")]
        public int BaseDamage;
        public GameObject EffectPrefab; // Vfx to spawn

        // Appended spell fields. Existing AbilityData assets (there were none when this shipped)
        // read the safe defaults: None, zero magnitudes and neutral multipliers.
        [Header("Spell Behaviour")]
        public SpellEffectType SpellEffect;
        public int HealAmount;
        public int ArmourBonus;
        public float EffectDuration;
        public float EffectRadius;
        public float SpeedMultiplier = 1f;
        public float SlowMultiplier = 1f;
        public float ProjectileSpeed = 10f;

        [Header("Spell VFX")]
        public AnimationClip CastEffectClip;
        public AnimationClip ProjectileClip;
        public AnimationClip ImpactClip;
        public AnimationClip LingeringClip;

        // Appended special-attack fields. Every existing ability asset reads the safe defaults:
        // IsSpecialAttack false, SpecialKind None, AllowedClasses empty (which admits everyone).
        //
        // ⚠ A special attack is an AbilityData but it is NOT a spell. It never goes through
        // SpellRuntime, it must never be placed under Assets/Resources/Abilities, and it must
        // never be passed to CombatController.LearnAbility — either would write its AbilityID
        // into savegame.json and turn that id into a save key forever.
        // See docs/reference/PLAYER_COMBAT.md.
        [Header("Special Attack")]
        [Tooltip("Runs as a melee special through CombatController, never through SpellRuntime.")]
        public bool IsSpecialAttack;
        [Tooltip("Which special move to run. None is refused at use time with a warning.")]
        public SpecialAttackKind SpecialKind;
        [Tooltip("Leave empty to allow every class. Mirrors PerkData.AllowedClasses.")]
        public PlayerClass[] AllowedClasses;

        /// <summary>Same shape as <see cref="PerkData.CanBeTakenBy"/>: an empty list admits everyone.</summary>
        public bool CanBeUsedBy(PlayerClass playerClass)
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
