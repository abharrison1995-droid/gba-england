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
    }
}
