using UnityEngine;
using GBHEngland.Flow;
using GBHEngland.Vibe;

namespace GBHEngland.Combat
{
    /// <summary>
    /// Decides whether a death pays the player XP, and how much.
    ///
    /// Deliberately not folded into <see cref="Health"/>: every eligibility rule lives in one
    /// greppable place, and Health stays generic — it hangs on props, chests and containers as
    /// well as on things that can be killed.
    /// </summary>
    internal static class KillXP
    {
        /// <summary>
        /// Called from <see cref="Health.Die"/>. Silently does nothing for every death that is not
        /// a player kill on a hostile — that is the normal case, not an error.
        /// </summary>
        public static void AwardFor(Health victim)
        {
            if (victim == null) return;

            // Nobody is on record as having dealt the last blow: an environmental death, or damage
            // routed through an overload that does not attribute.
            if (victim.LastAttacker == null) return;

            // Who gets the credit. The player's own kills pay full XP; the follower's pay 30% —
            // Alex does the work, but the player still gets a taste. Anything else (an
            // environmental death, enemy-kills-enemy, police-kills-civilian) pays nothing. The
            // player test is the same one Health.TakeDamage uses to decide whose armour applies.
            float multiplier;
            if (victim.LastAttacker.GetComponent<CombatController>() != null)
                multiplier = 1f;
            else if (Companions.CompanionManager.Instance != null
                     && victim.LastAttacker == Companions.CompanionManager.Instance.Follower)
                multiplier = 0.3f;
            else
                return;

            // Only things with an AI are hostiles. Civilians, props, LootChests and
            // SpriteContainers all carry Health too, and a murdered shopkeeper must not be a
            // better source of XP than a fight.
            var ai = victim.GetComponent<EnemyAI>();
            if (ai == null) return;

            // Killing police pays nothing — the consequence layer already prices that in with a
            // wanted level. One line, so reversing this decision is one line.
            if (ai.IsPolice) return;

            // With an EnemyLevel the payout follows the same curve its health and damage do; with
            // none it is a flat level-1 kill, which is what every enemy in the game is today.
            var level = victim.GetComponent<EnemyLevel>();
            int amount = level != null
                ? EKVibe.ScaledKillXP(level.ResolvedBaseXP, level.Level)
                : EKVibe.KillXPBase;
            amount = Mathf.Max(1, Mathf.RoundToInt(amount * multiplier));

            PlayerSession.Instance?.GrantXP(amount, victim.DisplayName);
        }
    }
}
