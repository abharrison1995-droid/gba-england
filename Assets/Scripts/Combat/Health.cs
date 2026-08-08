using UnityEngine;
using UnityEngine.Events;
using ExiledAlvaston.UI;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.Combat
{
    public class Health : MonoBehaviour
    {
        public int MaxHealth = 50;
        public int CurrentHealth;
        public string DisplayName;

        [Tooltip("Enemies/props are destroyed on death. The player clears this so GameFlow can handle death instead.")]
        public bool DestroyOnDeath = true;
        [Tooltip("Seconds the corpse lingers before being removed — long enough for a death pose/animation to actually be seen.")]
        public float DestroyDelay = 1.2f;

        public UnityEvent<int> OnTakeDamage = new UnityEvent<int>();
        public UnityEvent OnDeath = new UnityEvent();

        public bool IsDead => CurrentHealth <= 0;

        /// <summary>The GameObject that last dealt damage to this entity. Used by arrest logic to check if attacker was police.</summary>
        [System.NonSerialized] public GameObject LastAttacker;

        /// <summary>
        /// Non-null only on the player — armour lives on PlayerSession but is gated on this Health
        /// belonging to the player, which is what this component answers. Cached rather than looked
        /// up per hit: nothing in the project adds a CombatController at runtime, so a null cached
        /// on an enemy stays correct for that object's whole life.
        /// </summary>
        private CombatController _combat;

        private void Awake()
        {
            _combat = GetComponent<CombatController>();

            // ⚠ Must stay ABOVE the line below. EnemyLevel raises MaxHealth, and anything reordered
            // past this point leaves a levelled enemy alive at level-1 health under a raised
            // maximum — which looks like a broken health bar, not a broken scale. Call order is the
            // guard here deliberately, rather than a [DefaultExecutionOrder] nobody would see.
            // No component, or a level of 1, means nothing is touched at all.
            GetComponent<EnemyLevel>()?.ApplyTo(this);

            CurrentHealth = MaxHealth;
            if (string.IsNullOrEmpty(DisplayName))
                DisplayName = gameObject.name;
        }

        /// <returns>True if the hit landed — see the four-argument overload.</returns>
        public bool TakeDamage(int damage)
        {
            return TakeDamage(damage, "Something", DisplayName);
        }

        /// <returns>True if the hit landed — see the four-argument overload.</returns>
        public bool TakeDamage(int damage, string attackerName, string targetLabel)
        {
            return TakeDamage(damage, attackerName, targetLabel, null);
        }

        /// <summary>
        /// Applies damage, unless the target refuses it.
        /// </summary>
        /// <returns>
        /// True if the hit landed. False means it was refused — currently only because the target
        /// was already dead — and a caller must not follow up with knockback, on-hit effects or
        /// attribution. Returning this rather than nothing is what lets an attacker tell a hit that
        /// connected from one that did not; without it every follow-up effect fires regardless.
        ///
        /// ⚠ Unity's Inspector only offers void methods in a UnityEvent dropdown, so this is no
        /// longer bindable there. Nothing binds it today (verified: no m_MethodName: TakeDamage
        /// anywhere under Assets/). If something ever needs to, add a void ApplyDamage wrapper
        /// rather than taking this return value away.
        /// </returns>
        public bool TakeDamage(int damage, string attackerName, string targetLabel, GameObject attacker)
        {
            if (IsDead) return false;

            // Armour only exists on the player (equipment lives on PlayerSession), so the
            // reduction is gated on this Health belonging to the player — enemies keep taking
            // raw damage.
            //
            // Proportional, not a flat subtraction: armour scales the hit down by a curve and
            // Mathf.Max(1, ...) keeps a hit always landing for something. The damage > 0 gate is
            // load-bearing — TakeDamage(int) is public, and without it a 0-damage call would be
            // floored *upward* to 1 and start hurting the player.
            if (_combat != null && damage > 0)
            {
                var session = Flow.PlayerSession.Instance;
                if (session != null)
                    damage = Mathf.Max(1, Mathf.RoundToInt(
                        damage * (1f - EKVibe.ArmourReduction(session.EffectiveArmour()))));
            }

            LastAttacker = attacker;
            CurrentHealth -= damage;
            OnTakeDamage?.Invoke(damage);

            FloatingDamageText.Spawn(transform.position, damage);

            if (UIManager.Instance != null)
            {
                string who = string.IsNullOrEmpty(targetLabel) ? DisplayName : targetLabel;
                UIManager.Instance.LogCombat($"{attackerName} hits {who}, {damage}");
            }

            if (CurrentHealth <= 0)
                Die();

            return true;
        }

        /// <summary>Restore health up to MaxHealth. No effect on the dead — use Revive for that.</summary>
        public void Heal(int amount)
        {
            if (IsDead || amount <= 0) return;
            CurrentHealth = Mathf.Min(MaxHealth, CurrentHealth + amount);
        }

        /// <summary>Bring a dead (non-destroyed) actor back — used by player respawn.</summary>
        public void Revive(int health)
        {
            CurrentHealth = Mathf.Clamp(health, 1, MaxHealth);
        }

        private void Die()
        {
            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat($"{DisplayName} dies.");

            OnDeath?.Invoke();

            // After the event so LootOnDeath still opens its menu first, and before the early
            // return below so an enemy authored not to be destroyed still pays out.
            KillXP.AwardFor(this);

            if (!DestroyOnDeath)
                return;

            // Corpse must stop fighting and blocking immediately, not after the destroy delay
            var ai = GetComponent<EnemyAI>();
            if (ai != null) ai.enabled = false;
            var agent = GetComponent<UnityEngine.AI.NavMeshAgent>();
            if (agent != null) agent.enabled = false;
            foreach (var col in GetComponentsInChildren<Collider>())
                col.enabled = false;

            Destroy(gameObject, DestroyDelay);
        }
    }
}
