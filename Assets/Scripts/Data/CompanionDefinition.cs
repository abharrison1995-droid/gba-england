using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// How a companion joins and leaves the playerw. Paid means the hire interaction charges
    /// PricePounds; QuestBound means quest state drives it (escort / quest dialogue).
    ///
    /// Serialized by integer index - APPEND ONLY. Inserting or reordering silently remaps every
    /// definition authored in every existing CompanionDefinition asset.
    /// </summary>
    public enum CompanionContractType
    {
        /// <summary>Hired by paying PricePounds at the home anchor.</summary>
        Paid = 0,
        /// <summary>Join / leave driven by quest state (escort archetype, Phase 5).</summary>
        QuestBound = 1
    }

    /// <summary>
    /// One recruitable companion, authored as data. Assets live in Resources/Companions/ and are
    /// resolved by CompanionDatabase using Id.
    ///
    /// STRINGS + NUMBERS ONLY. Everything reachable from a Resources/ folder ships in the build, so
    /// this may not hold a GameObject, Sprite, AudioClip or AnimatorController reference (the same
    /// rule QuestDefinition documents). The art lives on the ArtSubject's PlacementPreset, which is
    /// outside Resources/ and is resolved at build time by the companion's home preset and at spawn
    /// time by CompanionManager through the same preset. This keeps one 45MB prop pack or a sprite
    /// sheet from being dragged into every build by a companion nobody hired.
    /// </summary>
    [CreateAssetMenu(fileName = "NewCompanion", menuName = "ExiledAlvaston/Data/Companion Definition")]
    public class CompanionDefinition : ScriptableObject
    {
        [Tooltip("The save key. Must match the PlacementPreset QuestKey used as the home anchor, " +
                 "and any HireCompanionId reference. Changing a shipped Id orphans the save.")]
        public string Id;

        [Tooltip("Shown in the companion HUD.")]
        public string DisplayName = "Companion";

        [Tooltip("The art importer's subject - 'alex' for sheet_char_alex_*. Resolves the sprite " +
                 "and controller through the companion's PlacementPreset, which the importer fills " +
                 "when that subject's sheets land.")]
        public string ArtSubject = "";

        [Tooltip("How the contract starts and ends.")]
        public CompanionContractType ContractType = CompanionContractType.Paid;

        [Header("Home anchor")]
        [Tooltip("MapChunkData.ChunkName the companion waits in. Treated as a stable save key once " +
                 "shipped - renaming the chunk orphans the home.")]
        public string HomeChunkName = "";
        [Tooltip("The QuestActor/SceneMarker key, inside HomeChunkName, the home presence sits on. " +
                 "Authoring time places the presence here; the active follower ignores the anchor.")]
        public string HomeAnchorId = "";

        [Header("Price (Paid only)")]
        [Tooltip("Charged by the hire interaction when ContractType is Paid. Ignored for QuestBound.")]
        public int PricePounds = 25;

        [Header("Stats")]
        public int MaxHealth = 120;
        public int Damage = 8;
        public float MoveSpeed = 4.2f;
        public float AttackRange = 1.6f;
        public float AttackCooldown = 1.3f;
        public float AttackWindup = 0.3f;

        [Header("Heal")]
        [Tooltip("Health restored by the cast. Heals the badly-injured player first, else self.")]
        public int HealAmount = 18;
        [Tooltip("Seconds between heals. Alex plan: 20.")]
        public float HealCooldown = 20f;
        [Tooltip("Player health fraction (of max) at or below which Alex prioritises the player.")]
        [Range(0f, 1f)]
        public float HealPlayerPriorityFraction = 0.4f;

        [Header("Dodge")]
        [Tooltip("Seconds between dodge rolls. Alex plan: 8-10 (far rarer than the player's 1).")]
        public float DodgeCooldown = 9f;

        [Header("Size")]
        [Tooltip("World height of the companion's sprite. Applied at runtime to the follower and " +
                 "the home presence, so both stay the same size.")]
        public float Height = 1.3f;
        [Tooltip("World width of the sprite. 0 keeps the art's natural aspect (uniform scale from " +
                 "Height); a positive value fits the width independently for a deliberately wider " +
                 "silhouette. Alex: 1.1.")]
        public float Width = 1.1f;
    }
}
