using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Companions;
using GBHEngland.Data;
using GBHEngland.UI;
using GBHEngland.World;

namespace GBHEngland.Combat
{
    /// <summary>Executes the data-driven spell effect after CombatController pays its cost.</summary>
    public static class SpellRuntime
    {
        private static readonly RaycastHit[] ProjectileHits = new RaycastHit[16];
        private static readonly Collider[] AreaHits = new Collider[48];
        private static readonly HashSet<Health> AreaVictims = new HashSet<Health>();

        public static void Execute(CombatController caster, AbilityData ability, Health target,
            string shout)
        {
            if (caster == null || ability == null) return;

            switch (ability.SpellEffect)
            {
                case SpellEffectType.Spark:
                    CastSpark(caster, ability, target, shout);
                    break;
                case SpellEffectType.Fireball:
                case SpellEffectType.SludgeBolt:
                    caster.StartCoroutine(TravelProjectile(caster, ability, target, shout));
                    break;
                case SpellEffectType.HealingAura:
                    CastHealingAura(caster, ability);
                    break;
                case SpellEffectType.IronSkin:
                    CastIronSkin(caster, ability);
                    break;
                case SpellEffectType.LightFeet:
                    CastLightFeet(caster, ability);
                    break;
                default:
                    Debug.LogWarning($"SpellRuntime: '{ability.AbilityID}' has no SpellEffectType.");
                    break;
            }

            if (ability.EffectPrefab != null)
                Object.Instantiate(ability.EffectPrefab,
                    caster.transform.position + caster.FacingDirection * 1.2f,
                    caster.transform.rotation);
        }

        private static void CastSpark(CombatController caster, AbilityData ability, Health target,
            string shout)
        {
            Vector3 from = caster.transform.position + Vector3.up * 0.8f;
            Vector3 to = target != null
                ? target.transform.position + Vector3.up * 0.7f
                : from + caster.FacingDirection * Mathf.Max(2f, ability.Range * 0.6f);

            if (ability.ProjectileClip != null)
            {
                SpellFxPlayer bolt = SpellFxPlayer.Spawn(ability.ProjectileClip, (from + to) * 0.5f);
                bolt?.Span(from, to);
            }
            else
            {
                // Safe until the staged Spark flight sheet completes its Unity import.
                LightningBolt.Spawn(from, to);
            }

            SpellFxPlayer.Spawn(ability.ImpactClip, to);
            DealDamage(caster, target, ability.BaseDamage, shout);
        }

        private static IEnumerator TravelProjectile(CombatController caster, AbilityData ability,
            Health target, string shout)
        {
            Vector3 origin = caster.transform.position + Vector3.up * 0.75f;
            Vector3 destination = target != null
                ? target.transform.position + Vector3.up * 0.65f
                : origin + caster.FacingDirection * Mathf.Max(2f, ability.Range * 0.75f);

            float speed = Mathf.Max(1f, ability.ProjectileSpeed);
            float maximumLifetime = Mathf.Max(1f, ability.Range / speed + 1f);
            SpellFxPlayer visual = SpellFxPlayer.Spawn(ability.ProjectileClip, origin, loop: true,
                lifetime: maximumLifetime);
            Transform projectile = visual != null ? visual.transform : null;
            float startedAt = Time.time;
            Vector3 position = origin;
            bool reached = false;

            while (Time.time - startedAt < maximumLifetime)
            {
                if (target != null && !target.IsDead)
                    destination = target.transform.position + Vector3.up * 0.65f;

                Vector3 delta = destination - position;
                float dist = delta.magnitude;
                float step = speed * Time.deltaTime;
                float moveDist = Mathf.Min(dist, step);

                if (moveDist > 0.0001f)
                {
                    Vector3 dir = delta / dist;
                    int hitCount = Physics.RaycastNonAlloc(position, dir, ProjectileHits, moveDist, ~0,
                        QueryTriggerInteraction.Ignore);

                    RaycastHit closestHit = default;
                    float closestDist = float.MaxValue;
                    bool hitSomething = false;
                    Health hitHealth = null;

                    for (int i = 0; i < hitCount; i++)
                    {
                        RaycastHit hit = ProjectileHits[i];
                        Collider col = hit.collider;
                        if (col == null) continue;
                        if (col.transform == caster.transform || col.transform.IsChildOf(caster.transform)) continue;
                        if (col.GetComponentInParent<CombatController>() != null) continue;

                        Health h = col.GetComponentInParent<Health>();
                        if (h != null)
                        {
                            if (h == caster.GetComponent<Health>() || h.IsDead) continue;
                            if (h.GetComponent<CompanionAI>() != null || col.GetComponentInParent<CompanionAI>() != null) continue;
                        }

                        if (hit.distance < closestDist)
                        {
                            closestDist = hit.distance;
                            closestHit = hit;
                            hitSomething = true;
                            hitHealth = h;
                        }
                    }

                    if (hitSomething)
                    {
                        position = closestHit.point;
                        target = hitHealth;
                        reached = true;
                        break;
                    }

                    position += dir * moveDist;
                }

                if (projectile != null) projectile.position = position;
                if ((position - destination).sqrMagnitude <= 0.01f)
                {
                    reached = true;
                    break;
                }
                yield return null;
            }

            if (projectile != null) Object.Destroy(projectile.gameObject);

            if (ability.SpellEffect == SpellEffectType.Fireball)
                ResolveFireball(caster, ability, position, shout);
            else
                ResolveSludge(caster, ability, reached ? target : null, position, shout);
        }

        private static void ResolveFireball(CombatController caster, AbilityData ability,
            Vector3 position, string shout)
        {
            SpellFxPlayer.Spawn(ability.ImpactClip, position);
            float radius = Mathf.Max(0.1f, ability.EffectRadius);
            int count = Physics.OverlapSphereNonAlloc(position, radius, AreaHits, ~0,
                QueryTriggerInteraction.Ignore);
            AreaVictims.Clear();
            for (int i = 0; i < count; i++)
            {
                Health health = AreaHits[i] != null ? AreaHits[i].GetComponentInParent<Health>() : null;
                if (health == null || health.IsDead || !AreaVictims.Add(health)) continue;
                if (health.GetComponent<EnemyAI>() == null) continue; // no player/companion friendly fire
                DealDamage(caster, health, ability.BaseDamage, shout);
            }
            AreaVictims.Clear();
        }

        private static void ResolveSludge(CombatController caster, AbilityData ability, Health target,
            Vector3 position, string shout)
        {
            SpellFxPlayer.Spawn(ability.ImpactClip, position);
            if (target == null || target.IsDead) return;
            EnemyAI enemy = target.GetComponent<EnemyAI>();
            if (enemy == null) return;

            DealDamage(caster, target, ability.BaseDamage, shout);
            if (target.IsDead) return;

            TimedSpellStatus.ApplyEnemySpeed(enemy, ability.SlowMultiplier, ability.EffectDuration);
            SpellFxPlayer.Spawn(ability.LingeringClip, target.transform.position + Vector3.up * 0.05f,
                loop: true, lifetime: ability.EffectDuration, follow: target.transform,
                followOffset: Vector3.up * 0.05f);
        }

        private static void CastHealingAura(CombatController caster, AbilityData ability)
        {
            Health playerHealth = caster.GetComponent<Health>();
            if (playerHealth != null)
            {
                playerHealth.Heal(ability.HealAmount);
                SpawnActorAura(ability.CastEffectClip, caster.transform);
            }

            CompanionManager manager = CompanionManager.Instance;
            Health companionHealth = manager != null && manager.FollowerAI != null
                ? manager.FollowerAI.FollowerHealth
                : null;
            if (companionHealth != null && !companionHealth.IsDead)
            {
                companionHealth.Heal(ability.HealAmount);
                SpawnActorAura(ability.CastEffectClip, companionHealth.transform);
            }

            UIManager.Instance?.LogCombat($"Healing Aura restores {ability.HealAmount} health.");
        }

        private static void CastIronSkin(CombatController caster, AbilityData ability)
        {
            TimedSpellStatus.ApplyArmour(caster, ability.ArmourBonus, ability.EffectDuration);
            SpawnActorAura(ability.CastEffectClip, caster.transform);
            UIManager.Instance?.LogCombat($"Iron Skin grants {ability.ArmourBonus} armour for {ability.EffectDuration:0} seconds.");
        }

        private static void CastLightFeet(CombatController caster, AbilityData ability)
        {
            TimedSpellStatus.ApplyPlayerSpeed(caster, ability.SpeedMultiplier, ability.EffectDuration);
            SpellFxPlayer.Spawn(ability.CastEffectClip, caster.transform.position + Vector3.up * 0.25f,
                follow: caster.transform, followOffset: Vector3.up * 0.25f);
            UIManager.Instance?.LogCombat($"Light Feet increases movement speed for {ability.EffectDuration:0} seconds.");
        }

        private static void SpawnActorAura(AnimationClip clip, Transform actor)
        {
            if (clip == null || actor == null) return;
            float halfHeight = 0.8f;
            WorldActorVisual visual = actor.GetComponent<WorldActorVisual>();
            if (visual != null && visual.Height > 0f) halfHeight = visual.Height * 0.5f;
            Vector3 offset = Vector3.up * halfHeight;
            SpellFxPlayer.Spawn(clip, actor.position + offset, follow: actor, followOffset: offset);
        }

        private static void DealDamage(CombatController caster, Health target, int baseDamage,
            string shout)
        {
            if (target == null || target.IsDead || baseDamage <= 0) return;
            Flow.PlayerSession session = Flow.PlayerSession.Instance;
            int damage = session != null
                ? Mathf.RoundToInt(baseDamage * session.SpellDamageMultiplier)
                : baseDamage;
            if (target.TakeDamage(damage, shout, target.DisplayName, caster.gameObject))
                caster.PingHealthBar();
        }
    }
}
