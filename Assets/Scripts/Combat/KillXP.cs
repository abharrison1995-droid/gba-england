using ExiledAlvaston.Flow;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.Combat
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

            // The established player test, the same one Health.TakeDamage uses to decide whose
            // armour applies. It keeps police-kills-civilian and enemy-kills-enemy from paying out.
            if (victim.LastAttacker.GetComponent<CombatController>() == null) return;

            // Only things with an AI are hostiles. Civilians, props, LootChests and
            // SpriteContainers all carry Health too, and a murdered shopkeeper must not be a
            // better source of XP than a fight.
            var ai = victim.GetComponent<EnemyAI>();
            if (ai == null) return;

            // Killing police pays nothing — the consequence layer already prices that in with a
            // wanted level. One line, so reversing this decision is one line.
            if (ai.IsPolice) return;

            int amount = EKVibe.KillXPBase;

            PlayerSession.Instance?.GrantXP(amount, victim.DisplayName);
        }
    }
}
