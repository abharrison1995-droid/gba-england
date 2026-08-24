# Player combat — melee, the dodge roll and the two special attacks

```
Last verified against: branch feat/player-special-attacks @ 9f05661, read on disk 2026-08-24.
Verification scope:    C# read on disk only. No C# compiler, no Unity and no test framework were
                       available, so nothing here has been compiled or played. The special
                       attacks in particular have never run: their two AbilityData assets do not
                       exist yet (the editor tool that creates them has not been run) and the
                       player's SpecialAttacks list in c.unity is unassigned.
```

This file owns the player's melee side of `CombatController`: the three moves that swing, the one
helper they all resolve through, what each of them costs, and the invariant that keeps a special
attack out of the save file. Spells are **not** here — they live in [SPELLS.md](SPELLS.md).
Stamina as a resource, stealth and the riding refusal live in
[CONSEQUENCES_AND_MOUNTS.md](CONSEQUENCES_AND_MOUNTS.md).

---

## 1. The three ways the player swings

All three are in `Assets/Scripts/Combat/CombatController.cs`.

| Move | Entry point | Coroutine | Arc | Reach | Damage | Cost |
|---|---|---|---|---|---|---|
| Basic swing | `PerformMeleeAttack()` | `MeleeHitboxRoutine` | `MeleeArcAngle` (180 by default) | `MeleeRange` (1.95 by default) | `ComputeMeleeDamage(1f)` | free |
| Spin | `TrySpecialAttack(0)` | `SpinAttackRoutine` | 360, arc test skipped | `SpinRange`, falling back to `MeleeRange` when 0 | `ComputeMeleeDamage(SpinDamageMultiplier)` per tick | `SpinStaminaPercent` of maximum stamina |
| Dash | `TrySpecialAttack(1)` | `DashAttackRoutine` | `DashArcAngle` | `DashRange`, same fallback | `ComputeMeleeDamage(DashDamageMultiplier)` | `DashStaminaPercent` of maximum stamina |

The two specials are `AbilityData` assets with `IsSpecialAttack` set, dispatched by `SpecialKind`
in `PerformSpecialMeleeAttack`. They are resolved **by index** out of the Inspector-assigned
`CombatController.SpecialAttacks` list — element 0 is the spin, element 1 is the dash — and never
by id out of `Resources`. Section 6 is why.

`SpecialAttackKind.None` is refused at dispatch with a warning rather than defaulting to a spin.
That refusal happens **after** the cost has been charged and the cooldown started, because the
branch mirrors the cast path's order; it is a misauthored-asset path only.

Both specials go through `TryUseAbility`, the same private body `TryCastAbility` uses, so they
inherit the shared gates for free: `_isAttacking || _isRolling || _isKnockedBack || _isDead`,
`BlockedByRiding()`, and the cooldown dictionary. The special branch then leaves **before** the
concealment drain and before `CastAbilityRoutine`'s shout: a special attack is a weapon swing, not
magic, so it neither drains Concealment nor shouts a spell name.

⚠ Cooldowns are keyed by `AbilityID` in one dictionary shared with spells. Two assets carrying the
same `AbilityID` therefore share one cooldown, silently.

## 2. `ResolveMeleeSweep` and the dedupe contract

All three moves resolve their hits through one private helper:

```csharp
private int ResolveMeleeSweep(Vector3 origin, Vector3 facing, float reach, float arcAngle, int damage)
private int ComputeMeleeDamage(float moveMultiplier)
```

The helper does the whole pass: `Physics.OverlapSphereNonAlloc` at `origin` with mask `~0` and
`QueryTriggerInteraction.Collide`, the `Health` filter, the companion exclusion, the point-blank
grace, the arc test, `TakeDamage(damage, "you", foeName, gameObject)` and the melee-knockback perk.
`arcAngle >= 360` skips the arc test entirely — that is the spin.

Three details in it are load-bearing, and are the reason it is one method rather than three copies:

- the **four-argument** `TakeDamage` overload. Dropping `gameObject` leaves the player invisible to
  kill attribution, with no error;
- `CompanionAI` targets are skipped, so Alex is never cleaved;
- knockback is gated on `!targetHealth.IsDead`, so a corpse whose agent is already disabled is not
  shoved.

⚠ **The helper never clears `_hitThisSwing`. Its caller does, and when it does is the one thing
that differs between the three:**

| Caller | Clears | Result |
|---|---|---|
| `MeleeHitboxRoutine` | once | one hit per swing |
| `DashAttackRoutine` | once, before the loop | one hit per target per dash, however many physics steps it sweeps over |
| `SpinAttackRoutine` | before every tick | one hit per tick, so standing inside the spin hurts repeatedly |

Clearing the dash per step would deal roughly one hit per fixed update — about fourteen over
0.28 s — to the same target. This is the most consequential difference between the two moves, and
it is deliberately visible at each call site rather than hidden behind a parameter.

`_hitResults` is 64 wide. The mask is `~0`, so ground, buildings and props all count toward the cap
**before** any filtering, and `OverlapSphereNonAlloc` reports overflow only by silently returning
the array length. An editor-only warning fires on saturation. A layer mask would be the real fix
and is out of scope: `ProjectSettings/TagManager.asset` defines no user layers, and every enemy and
police prefab sits on layer 0.

Note also, inside the helper: `origin` is the waist-height sphere centre, while the `playerPos`
used by the distance and arc tests is `transform.position`. The two have always been different
values and must stay different — the overlap is a 3D sphere, the arc test is flat on X/Z.

## 3. State flags — why there is no `_isSpecialAttacking`

Both special routines set `_isAttacking`, the flag the basic swing already uses. It suspends
`HandleMovement` via the `FixedUpdate` gate, blocks a second swing, a dodge and a cast, and is
cleared defensively in `OnDisable` and in the death handler. A second flag would be two more places
to clear and two more ways to strand the player with movement disabled for the rest of the session.

In all three routines the flag is raised **before the first yield** and cleared in a `finally`.
That discipline is the only thing standing between a mid-move `yield break` and a permanently
unresponsive player.

The spin also calls `ClearAnimatorTrigger("SpecialAttack")` in its `finally`. All nine `player_*`
controllers declare the `SpecialAttack` **parameter**, but no player controller has a `Special`
**state** — `HasAnimatorTrigger` tests parameters, not states, so the trigger is set and nothing
ever consumes it. Without the clear it latches, and would fire a special animation at an arbitrary
moment the day a `special` sheet is imported. The dash sidesteps this entirely by reusing the
`Roll` trigger, which does have a state.

## 4. What the specials cost, and why it is a percent

`SpecialStaminaCost` charges a **percent of the live maximum**, floored, minimum 1:

```csharp
Mathf.Max(1, Mathf.FloorToInt(PlayerData.MaxManaStamina * pct / 100f))   // 12 if PlayerData is unbound
```

This is the same shape as `CurrentRollCost`, and for the reason that method's comment spells out at
length: a flat cost silently becomes cheaper at every level because `MaxManaStamina` grows, and
flooring rather than rounding is what keeps "two rolls from full" true.

⚠ `AbilityData.ResourceCost` is deliberately **not** read for a special. Both assets are created
with `ResourceType = None`, so the generic charge on the cast path would be a no-op even if the
special branch were ever removed. Setting `ResourceType` to anything else on those assets would
start charging a second, flat cost out of the wrong pool.

Defaults, all Inspector-tunable on `CombatController` under `Special Attacks`:

| Spin | | Dash | |
|---|---:|---|---:|
| `SpinDuration` | 0.60 s | `DashDuration` | 0.28 s |
| `SpinTicks` | 3 | `DashDistance` | 3.20 m |
| `SpinRange` | 2.40 m | `DashRange` | 1.10 m |
| `SpinDamageMultiplier` | 0.60 | `DashArcAngle` | 140 |
| `SpinStaminaPercent` | 35 % | `DashDamageMultiplier` | 1.25 |
| | | `DashStaminaPercent` | 30 % |

## 5. The guards, and which move needs which

The spin does not move the body, so it yields on `WaitForSeconds` — timeScale-scaled, so a pause
freezes it for free — and needs only the death and knockback bails.

The dash moves the body and therefore runs on `WaitForFixedUpdate`, with four cooperative bails
checked **before** each move:

| Guard | Why |
|---|---|
| `_isDead` or `_health.IsDead` | matches the roll |
| `_isKnockedBack` | being hit always wins |
| `PauseManager.IsPaused` | cancels rather than suspends; exists for the frame where a pause is pushed and popped around a teleport |
| `ChunkManager.IsTransitioning`, or `CurrentChunkData` no longer the snapshot | ⚠ the important one |

The chunk guard **snapshots a reference and polls it**, per CLAUDE.md §3: `CurrentChunkData` is
written from eight places across six files, so hooking one transition would miss the others. A dash
into an edge trigger starts a transition that pauses and teleports the player; without this the
dash resumes on the far side and drives the body away from the arrival marker.

⚠ `RollRoutine` has the identical latent bug today and is **not** guarded. That is known, and was
deliberately held back as separate work.

The dash moves with `_rb.MovePosition`, never a transform write. The body is non-kinematic, so
`MovePosition` sweeps and resolves against colliders, and enemy capsules are solid — so **the dash
stops at the first enemy it reaches**. That is the intended feel, not a bug.

## 6. ⚠ The invariant: a special attack must never become a save key

*A special-attack `AbilityData` must never be placed under `Assets/Resources/Abilities`, and must
never be passed to `CombatController.LearnAbility`.*

If either happens, `LearnAllCurrentSpells` (reachable from `Tools → Debug → Learn All Current
Spells`) learns it, slots it into one of the four spell slots, shows it in the spellbook and writes
its `AbilityID` into `savegame.json` — at which point that id **is** a save key and can never be
renamed, because renaming it silently drops it on load (CLAUDE.md §3).

Three things enforce this, and none of them is a comment:

1. The assets live in `Assets/Data/Abilities/`, outside `Resources/`, so
   `SpellDatabase.EnsureLoaded` (`Resources.LoadAll<AbilityData>("Abilities")`) cannot see them.
2. `SpellDatabase.EnsureLoaded` skips any `AbilityData` with `IsSpecialAttack` set, so even a
   misfiled asset cannot be learned.
3. `Tools → Content → Create Special Attack Assets` refuses to write into a `Resources` folder.

The specials reach the player through the Inspector `SpecialAttacks` list only. **Nothing about
this feature is written to `savegame.json`.**

## 7. HUD

`HUDActionButton.ActionKind` is **serialized by integer index**, and indices 0–3 are live in
`c.unity`. Append only — inserting a member turns the scene's attack button into something else,
silently.

| Index | Member | Built where |
|---:|---|---|
| 0 | `Attack` | `c.unity` (legacy cluster) + `UIManager.BuildActionButtons` |
| 1 | `Ability` | `c.unity` + `BuildActionButtons` (the four spell slots) |
| 2 | `Inventory` | `c.unity` |
| 3 | `Interact` | `c.unity` |
| 4 | `Crouch` | `BuildActionButtons` only |
| 5 | `Dodge` | `BuildActionButtons` only |
| 6 | `Special` | `BuildActionButtons` only |

`Ability` is the kind the `Invoke` switch's `default:` serves, so **any new `case` must go above
`default:`** or it is unreachable.

The bottom-right row reads ATK, USE, DGE, SPN, DSH right to left, each 16 px apart: SPN at
`(-517, 40)`, DSH at `(-673, 40)`, both 140×140, both anchored and pivoted to the screen's
bottom-right corner. ⚠ Both must stay parented to `panel.transform` inside `BuildActionButtons`:
`SetDrivingMode` hides that panel, and a button parented elsewhere would remain on screen while
driving, where `BlockedByRiding` refuses it with a toast at every tap.

`RefreshSpecialSlots` is polled from `Update` alongside `RefreshSpellSlots` and carries the same
cached change detection, because that is a mobile hot path: it compares the two ability references
and the player's class, and repaints only when one of them has moved. A slot paints dimmed
(`Win95Skin.Face` at alpha 0.35) when it is empty or the class is gated out. The `SPN` and `DSH`
labels are code placeholders held in a static array; the owner's `IconGlyph` replaces them.

Cooldown overlays branch their source: `GetSpecialCooldownRemaining` indexes `SpecialAttacks`,
while `GetCooldownRemaining` indexes `EquippedAbilities`, and a special button reading the latter
would sweep to whatever spell happened to be in slot 0 or 1.

`Alpha5` / `Alpha6` also call `TrySpecialAttack`. That is a desktop/editor testing path; the HUD
buttons are the shipping route.

## 8. What has never been verified

Everything in sections 1–7 was read off the source, not run. Nothing in the special-attack feature
has been compiled or played, the two assets do not exist, and `c.unity` has no `SpecialAttacks`
assignment. The owner's step-by-step is §11 of
[../plans/PLAYER_SPECIAL_ATTACKS_PLAN.md](../plans/PLAYER_SPECIAL_ATTACKS_PLAN.md); the standing
record of what is still unseen is [VERIFICATION_LEDGER.md](VERIFICATION_LEDGER.md).
