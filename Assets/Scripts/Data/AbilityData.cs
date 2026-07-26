using UnityEngine;

namespace ExiledAlvaston.Data
{
    public enum AbilityResourceType
    {
        Mana,
        Stamina,
        None
    }

    /// <summary>
    /// Represents an equippable spell or action.
    /// </summary>
    [CreateAssetMenu(fileName = "NewAbilityData", menuName = "ExiledAlvaston/Data/Ability Data")]
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
    }
}
