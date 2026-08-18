using UnityEngine;
using GBHEngland.Vibe;

namespace GBHEngland.Combat
{
    /// <summary>
    /// The level of one placed enemy. Absent means level 1, and level 1 scales nothing, so adding
    /// this script changes no existing enemy anywhere until an owner deliberately sets a Level.
    ///
    /// Attached at placement time by the World Palette, from PlacementPreset.EnemyLevel (or the
    /// palette's own per-stamp override). A preset level of 0 attaches nothing at all, so the two
    /// states an author sees are "this object has an Enemy Level component" and "it does not".
    ///
    /// ⚠ Ordering with the preset's OverrideHealth/OverrideDamage: the override is baked into the
    /// placed instance in the editor and is therefore the <b>level-1 baseline</b>; this multiplies
    /// it at runtime. An enemy placed with Override Health 100 and Level 5 reads 100 in the
    /// Inspector and has 240 HP in play. That is not a bug to fix — scaling first and overriding
    /// second would make the override silently cancel the level.
    ///
    /// Deliberately its own component rather than a promotion of <see cref="World.EnemyNameplate"/>'s
    /// Level field: all eleven nameplate-carrying prefabs store a 3 on disk, and reading that as a
    /// real level would make the entire cast level 3 and scale it up with nothing logged.
    /// </summary>
    [RequireComponent(typeof(Health))]
    public class EnemyLevel : MonoBehaviour
    {
        [Tooltip("Set per placement. The prefab's authored Health and Damage are the level-1 " +
                 "baseline; this multiplies them up from there. 1 changes nothing.")]
        public int Level = 1;

        [Tooltip("Tick to override the XP a kill pays, instead of following EKVibe.KillXPBase live.")]
        public bool OverrideBaseXP = false;

        [Tooltip("Only read when OverrideBaseXP is ticked. XP a kill pays at level 1, scaled up by " +
                 "EKVibe.EnemyXPPerLevel per level above.")]
        public int BaseXP = EKVibe.KillXPBase;

        /// <summary>
        /// The level-1 XP baseline this enemy actually pays: the authored override when
        /// <see cref="OverrideBaseXP"/> is set, otherwise the live <see cref="EKVibe.KillXPBase"/>, so a
        /// later retune of that constant is picked up by every enemy that never asked to diverge from it.
        ///
        /// <see cref="BaseXP"/> by itself is not a live reference — it is a plain field initializer, which
        /// Unity bakes into serialized YAML the moment a placed instance is authored, a frozen copy rather
        /// than a pointer to the constant. OverrideBaseXP is what makes that copy inert until an author
        /// deliberately opts in. Four EnemyLevel instances placed before this field existed
        /// (Home_London_Prefab x1, Mosleys_Lab_Basement_Prefab x3) have no OverrideBaseXP key in their
        /// YAML at all, so they deserialize it as Unity's default, false — no hand-edit needed, and they
        /// immediately track the live constant instead of staying pinned to the 25 they were baked with.
        /// </summary>
        public int ResolvedBaseXP => OverrideBaseXP ? BaseXP : EKVibe.KillXPBase;

        private bool _applied;

        /// <summary>
        /// Multiplies this enemy's stats up to its level. Called from <see cref="Health.Awake"/>
        /// <b>before</b> CurrentHealth is set from MaxHealth — scaling after that point would leave
        /// the enemy alive at level-1 health under a raised maximum, which reads as a health-bar
        /// bug rather than a scaling one.
        /// </summary>
        public void ApplyTo(Health health)
        {
            // A second call must never re-multiply: 1.35 x 1.35 compounds with nothing to show it
            // happened.
            if (_applied) return;
            _applied = true;

            if (Level < 1) Level = 1;

            // An authored default-1 component is exactly as inert as no component at all.
            if (Level <= 1) return;

            if (health != null)
                health.MaxHealth = EKVibe.ScaledHealth(health.MaxHealth, Level);

            // No ordering constraint here: EnemyAI.Damage is read live at swing time, not cached
            // in its Awake.
            var ai = GetComponent<EnemyAI>();
            if (ai != null)
                ai.Damage = EKVibe.ScaledDamage(ai.Damage, Level);

            // MoveSpeed and the NavMeshAgent are deliberately untouched. Agent tuning is physical,
            // not power — a high-level enemy is tougher, not faster.
        }
    }
}
