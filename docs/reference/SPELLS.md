# Spells

```
Last verified against: working tree, 2026-08-15. Special-attack note added 2026-08-24 against
                       branch feat/player-special-attacks.
Verification scope:    code and AbilityData YAML reviewed; asset references checked mechanically.
                       No C# compiler or Unity runtime was available. The special-attack note was
                       read off the source only - none of that feature has been compiled or run.
```

⚠ Not every `AbilityData` is a spell. The two special attacks - the spin and the dash - are
`AbilityData` assets with `IsSpecialAttack` set: they never go through `SpellRuntime`, are never
learned or persisted, must never be placed under `Assets/Resources/Abilities`, and are documented
in [PLAYER_COMBAT.md](PLAYER_COMBAT.md), not here.

Six current spell definitions live under `Assets/Resources/Abilities`. `AbilityData.AbilityID` is
a save key: never rename an existing id. `SpellDatabase.CurrentSpellIds` is the canonical order
used by the debug grant tool.

| ID | Spell | Mana | Cooldown | Effect |
|---|---|---:|---:|---|
| `spark` | Spark | 12 | 5s | 20 damage to one enemy. |
| `fireball` | Fireball | 20 | 10s | 30 damage to enemies in a 2m impact radius; no player or companion friendly fire. |
| `healing_aura` | Healing Aura | 18 | 30s | Restores 35 HP to the player and the active living companion. |
| `iron_skin` | Iron Skin | 16 | 20s | Adds 10 armour for 15 seconds. |
| `sludge_bolt` | Sludge Bolt | 16 | 8s | Deals 18 damage and reduces the target enemy to 60% speed for 6 seconds; puddle follows the target. |
| `light_feet` | Light Feet | 14 | 25s | Raises player movement speed to 135% for 8 seconds. |

## Runtime ownership

- `CombatController` owns learning, four equipped slots, mana payment and cooldowns.
- `SpellRuntime` owns damage, healing, projectiles, area hits and timed effects.
- `TimedSpellStatus` applies source-keyed armour/speed modifiers and always removes them on expiry,
  cancellation or target teardown.
- `SpellFxPlayer` evaluates imported non-legacy FX clips through a manual, Animator-backed
  PlayableGraph, with direct `AnimationClip.SampleAnimation` as a compatibility fallback. This
  avoids a dedicated AnimatorController per transient effect while still using Unity's runtime
  animation binding path.
- `KnownSpellIds`, four-position `EquippedSpellIds`, and Spark's `SpellName` are saved. Old saves
  default to an empty spellbook.

Spark uses the imported flight clip when available and falls back to the existing procedural
`LightningBolt` otherwise. The imported Spark impact is already referenced. After importing the
remaining `sheet_fx_spark_effect` pair, exit Play Mode and run
`Tools > Content > Wire Current Spell VFX` to attach it without changing spell tuning.

## Play Mode test tools

- `Tools > Debug > Learn All Current Spells` learns all six and equips Spark, Fireball, Healing
  Aura and Iron Skin into the four slots.
- `Tools > Debug > Forget All Spells` clears known spells, slots, cooldowns and active player spell
  buffs.
- `Tools > Debug > Preview Current Spell VFX` spawns every distinct wired clip in a grid around the
  player and reports how many successfully bound a sprite. Close the spellbook first: paused time
  intentionally prevents transient effects from advancing.

All three debug commands are intentionally enabled only in Play Mode and do not write a save by
themselves.
