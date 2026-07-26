using UnityEngine;
using UnityEngine.Events;
using ExiledAlvaston.UI;

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

        private void Awake()
        {
            CurrentHealth = MaxHealth;
            if (string.IsNullOrEmpty(DisplayName))
                DisplayName = gameObject.name;
        }

        public void TakeDamage(int damage)
        {
            TakeDamage(damage, "Something", DisplayName);
        }

        public void TakeDamage(int damage, string attackerName, string targetLabel)
        {
            TakeDamage(damage, attackerName, targetLabel, null);
        }

        public void TakeDamage(int damage, string attackerName, string targetLabel, GameObject attacker)
        {
            if (IsDead) return;

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
