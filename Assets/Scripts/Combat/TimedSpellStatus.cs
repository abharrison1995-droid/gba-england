using UnityEngine;

namespace GBHEngland.Combat
{
    /// <summary>
    /// Owns one temporary spell modifier. The token is parented to its target, so target teardown
    /// also tears down the modifier; OnDestroy always unregisters the exact source key it applied.
    /// </summary>
    public sealed class TimedSpellStatus : MonoBehaviour
    {
        public enum StatusKind { Armour, PlayerSpeed, EnemySpeed }

        private StatusKind _kind;
        private CombatController _player;
        private EnemyAI _enemy;
        private float _expiresAt;
        private bool _cleared;

        public static TimedSpellStatus FindExisting(Transform target, StatusKind kind)
        {
            if (target == null) return null;
            var statuses = target.GetComponentsInChildren<TimedSpellStatus>(true);
            for (int i = 0; i < statuses.Length; i++)
            {
                if (statuses[i]._kind == kind && !statuses[i]._cleared)
                    return statuses[i];
            }
            return null;
        }

        public static TimedSpellStatus ApplyArmour(CombatController player, int bonus, float duration)
        {
            if (player == null || bonus <= 0 || duration <= 0f) return null;
            TimedSpellStatus existing = FindExisting(player.transform, StatusKind.Armour);
            if (existing != null)
            {
                existing._expiresAt = Time.time + duration;
                player.SetTemporaryArmour(existing, bonus);
                return existing;
            }

            TimedSpellStatus status = Create(player.transform, "IronSkin", duration);
            status._kind = StatusKind.Armour;
            status._player = player;
            player.SetTemporaryArmour(status, bonus);
            return status;
        }

        public static TimedSpellStatus ApplyPlayerSpeed(CombatController player, float multiplier,
            float duration)
        {
            if (player == null || multiplier <= 0f || duration <= 0f) return null;
            TimedSpellStatus existing = FindExisting(player.transform, StatusKind.PlayerSpeed);
            if (existing != null)
            {
                existing._expiresAt = Time.time + duration;
                player.SetSpeedMultiplier(existing, multiplier);
                return existing;
            }

            TimedSpellStatus status = Create(player.transform, "LightFeet", duration);
            status._kind = StatusKind.PlayerSpeed;
            status._player = player;
            player.SetSpeedMultiplier(status, multiplier);
            return status;
        }

        public static TimedSpellStatus ApplyEnemySpeed(EnemyAI enemy, float multiplier, float duration)
        {
            if (enemy == null || multiplier <= 0f || duration <= 0f) return null;
            TimedSpellStatus existing = FindExisting(enemy.transform, StatusKind.EnemySpeed);
            if (existing != null)
            {
                existing._expiresAt = Time.time + duration;
                enemy.SetSpeedMultiplier(existing, multiplier);
                return existing;
            }

            TimedSpellStatus status = Create(enemy.transform, "SludgeBolt", duration);
            status._kind = StatusKind.EnemySpeed;
            status._enemy = enemy;
            enemy.SetSpeedMultiplier(status, multiplier);
            return status;
        }

        private static TimedSpellStatus Create(Transform target, string label, float duration)
        {
            var go = new GameObject($"~SpellStatus_{label}");
            go.transform.SetParent(target, false);
            TimedSpellStatus status = go.AddComponent<TimedSpellStatus>();
            status._expiresAt = Time.time + duration;
            return status;
        }

        private void Update()
        {
            if (Time.time >= _expiresAt)
                Destroy(gameObject);
        }

        /// <summary>Removes the modifier immediately and disposes its scene token.</summary>
        public void Cancel()
        {
            ClearModifier();
            Destroy(gameObject);
        }

        private void OnDestroy()
        {
            ClearModifier();
        }

        private void ClearModifier()
        {
            if (_cleared) return;
            _cleared = true;

            if (_kind == StatusKind.Armour && _player != null)
                _player.ClearTemporaryArmour(this);
            else if (_kind == StatusKind.PlayerSpeed && _player != null)
                _player.ClearSpeedMultiplier(this);
            else if (_kind == StatusKind.EnemySpeed && _enemy != null)
                _enemy.ClearSpeedMultiplier(this);
        }
    }
}
