# Player special attacks — Spin and Dash — implementation plan

Status: **planned, not implemented.** Written against `main` as of 2026-08-23, after an eight-agent
assessment swarm surveyed the combat system. Nothing below has been near a C# compiler or the Unity
editor. §11 is the owner's check list.

Owner doc when landed: new `docs/reference/PLAYER_COMBAT.md` (see §10). Every claim carries the
`file:line` it was read at.

Five of the swarm's findings were overturned during planning; the three load-bearing ones (§0.1,
§0.2, §0.3) were independently re-verified before this document was written. They are recorded in §0
rather than silently corrected, because each changes a decision downstream.

---

## 0. Corrections to the briefing before anything else

Five of the established findings need adjusting. Each changes a decision downstream, so they come first.

**0.1 — `SpecialAttack` is already a live animator parameter with nothing behind it.**
All nine `player_*` controllers declare the trigger (`player_Controller`, `player_broomshiv_`, `player_bundabasher_` at `:353`, `player_butterknife_`, `player_dynamo_`, `player_mrhood_`, `player_rockinasock_`, `player_slingshot_`, `player_stabmeister_`), but **no player controller has a `Special` state** — searching `Assets/Animations/Generated/` for that state name matches only `trap_branch_manager_Controller`. The importer wrote the parameter (`ArtImportTool.cs:74`) without a state because no `special` sheet has been delivered for the player.

Consequence: `SetAnimatorTrigger("SpecialAttack")` passes the `HasAnimatorTrigger` check (`CombatController.cs:1307-1314`, which tests *parameters*, not states), sets a trigger, and **nothing ever consumes it**. It latches. The day a `special` sheet lands and the importer adds an Any-State transition, that stale trigger fires a special animation at an arbitrary moment. Mitigation is in §3.2: `ClearAnimatorTrigger("SpecialAttack")` in the routine's `finally`, precedent at `CombatController.cs:1020`.

**0.2 — The civilian premise in open question (a) is false.**
I resolved `Health.cs.meta`'s GUID (`45274f9b38b18b146948aef63147a308`) and grepped every prefab for it. Exactly twelve carry `Health`: the seven `Assets/Prefabs/Enemies/Enemy_*.prefab` and the five `Assets/Prefabs/ModernBritain/Police_*.prefab`. `NpcFactory` never adds one — it adds `Interactable`, optionally `NPCDialogueInteractable`, `NPCWander`, `PickpocketInteractable` (`NpcFactory.cs:42-102`) and no `Health`. **Civilians are not damageable at all.** `GetComponentInParent<Health>()` returns null for them and the filter at `CombatController.cs:717` drops them.

**0.3 — Damage raises no wanted level today.** `SpikeKnives` has exactly six call sites: `WantedManager.cs:83`, `PickpocketInteractable.cs:84,165`, `TrafficCar.cs:322,361`, `VehicleController.cs:422`. Nothing in `Health.TakeDamage` or `CombatController` calls it. So a 360° spin cannot hand out a free or unfair wanted level — there is no wanted hook on combat at all. Question (a) collapses; see §8a.

**0.4 — `FixedUpdate` not checking `IsPaused` is harmless here.** `PauseManager.Apply()` sets `Time.timeScale = 0` (`PauseManager.cs:35`), and at timeScale 0 Unity does not run FixedUpdate, so `WaitForFixedUpdate` stalls and a dash freezes in place. The *real* hazard the swarm was circling is different and worse: a chunk transition pushes a pause, teleports the player, then pops — and the dash resumes driving the body in the old direction from the new position. The guard that matters is the chunk-identity snapshot, not the pause flag. I still recommend both (§4).

**0.5 — "dedupe clearing per tick" is right for the spin and wrong for the dash.** A dash sweeping every physics step with a per-tick clear would deal ~14 hits to the same target over 0.28 s. Dash clears **once**; spin clears **per tick**. This is the single most important difference between the two routines and §3 makes it explicit at both call sites rather than hiding it in a parameter.

**Minor:** the briefing lists the player walk clip as `6@12`. `ArtImportTool.cs:88` and `ART_PIPELINE.md:365` both say **6 frames @ 8 fps**. The docs are correct; the summary drifted. No doc change needed.

---

## 1. Scope

**In**

- Two new melee special attacks, authored as `AbilityData` assets, executed as melee, never through `SpellRuntime`.
- Three appended fields + one new enum on `AbilityData`.
- One appended `HUDActionButton.ActionKind` member.
- One new `#region Special Attacks` in `CombatController`, plus a shared sweep helper extracted from `MeleeHitboxRoutine`.
- Two new HUD buttons in the existing bottom-right row, with radial cooldown overlays.
- One editor tool that creates the two assets.
- Docs: one new reference, two routing-table rows, one ledger entry.

**Out**

- Any change to `SpellEffectType` (`AbilityData.cs:17-26`) — it is a save-key enum and the specials never touch the spell path.
- Any change to `savegame.json`'s shape. **This plan adds nothing to the save file** (§2.3).
- Any change to `MeleeHitDelay` / `MeleeRecovery` (`CombatController.cs:43,45`) or the attack clip's frame count (§8c).
- Layer masks. `ProjectSettings/TagManager.asset` defines no user layers (indices 3, 6–31 empty) and `Enemy_Neek.prefab:19` / `Police_Bobby.prefab:18` are both `m_Layer: 0`. Introducing a mask means editing project settings *and* re-layering twelve prefabs. Not worth it; §5.3 solves the buffer problem differently.
- Pass-through dashing. `Enemy_Neek.prefab:57` is `m_IsTrigger: 0`, and `_rb.MovePosition` on a non-kinematic body sweeps and resolves (the reasoning is spelled out at `CombatController.cs:916-920`), so **the dash is stopped by the first solid enemy it reaches**. That is an acceptable and readable v1 feel. Making it pass through needs `Physics.IgnoreCollision` bookkeeping with its own restore-in-`finally`; deferred.
- Any player-facing prose. `AbilityName`, `Description`, `IconGlyph` and any shout text are left blank for the owner (CLAUDE.md §3).

---

## 2. Mapping table — every serialized change

### 2.1 New serialized members

| # | File | Member | Kind | Index / position | Default on existing data | Blast radius if got wrong |
|---|---|---|---|---|---|---|
| 1 | `Assets/Scripts/Data/AbilityData.cs` | `SpecialAttackKind` enum: `None = 0`, `Spin = 1`, `Dash = 2` | **new** serialized enum | explicit values, mirroring `SpellEffectType` at `AbilityData.cs:17-26` | n/a — no asset references it yet | Once the two assets ship, renumbering swaps spin and dash on assets already authored. Append only. `None = 0` is deliberate: an asset where the owner forgets to set the kind must be *refused*, not silently become a spin. |
| 2 | `AbilityData.cs` | `public bool IsSpecialAttack;` | appended field | after `LingeringClip` (`:70`), under a new `[Header("Special Attack")]` | `false` on all six `Assets/Resources/Abilities/Spell_*.asset` | If it ever read `true` on a spell, that spell would execute as a melee sweep with no shout and no concealment drain. Default `false` makes that impossible without a deliberate edit. |
| 3 | `AbilityData.cs` | `public SpecialAttackKind SpecialKind;` | appended field | same block | `None` (=0) on all six spells | Refused at use time with a warning; see §3.4. |
| 4 | `AbilityData.cs` | `public PlayerClass[] AllowedClasses;` | appended field | same block | `null`/empty on all six spells → **admits every class**, mirroring `PerkData.cs:76-96` and `ItemData.CanBeUsedBy` | Empty-admits-everyone is the established house semantic; deviating from it here would surprise. |
| 5 | `Assets/Scripts/UI/HUDActionButton.cs:21` | `ActionKind.Special` | **appended enum member, integer index 6** | after `Dodge = 5` | n/a | ⚠ `Attack=0`, `Ability=1`, `Inventory=2`, `Interact=3` are live in `c.unity` (the file's own comment, `:13-20`). Inserting anywhere before index 6 turns `AttackButton` into something else in the scene, silently. **Append at the end, nothing else.** |
| 6 | `Assets/Scripts/Combat/CombatController.cs` | `public List<AbilityData> SpecialAttacks;` | new public field, placed immediately after `EquippedAbilities` (`:93`) under a new `[Header("Special Attacks")]` | new name — `c.unity` has no key for it | reads as an empty list on load; owner assigns in the Inspector | If left unassigned the buttons render dimmed and pressing them does nothing and logs. A **visible** failure, not a silent one — which is why the list is Inspector-assigned rather than resolved by id. |
| 7 | `CombatController.cs` | eleven new tuning floats/ints (§3.5) | new public fields | after `RollCooldown` (`:73`), own header | scene has no keys → Inspector defaults apply | None. All new names. |

### 2.2 Not renamed, not moved, not re-valued

Nothing existing is renamed. No `[FormerlySerializedAs]` is required anywhere in this plan. `_hitResults` (`CombatController.cs:113`) changes **size only** and is `private readonly` — not serialized, no scene or prefab impact.

### 2.3 Save-file impact: none — and the invariant that keeps it none

`savegame.json` stores spells as `AbilityID` strings resolved through `Resources/Abilities` (CLAUDE.md §3; `SpellDatabase.cs:55` is `Resources.LoadAll<AbilityData>("Abilities")`). The two special assets are **not** persisted, because:

1. They live in `Assets/Data/Abilities/`, **outside `Resources/`**, so `SpellDatabase.EnsureLoaded` cannot see them.
2. They reach the player through the Inspector `SpecialAttacks` list, never through `LearnAbility` (`CombatController.cs:1360`), so they never enter `KnownSpells` and are never written out.

⚠ **The invariant to write down and never break:** *a special-attack `AbilityData` must never be placed under `Resources/Abilities` and `LearnAbility` must never be called with one.* If either happens, `LearnAllCurrentSpells` (`CombatController.cs:1400-1408`, reachable from `Tools/Debug/Learn All Current Spells`, `SpellTools.cs:15`) will learn it, slot it into one of the four spell slots, show it in `SpellbookUI`, and write its `AbilityID` into `savegame.json` — at which point that id **becomes a save key** and can never be renamed. Commit 4 adds a code-level guard so folder discipline is not the only thing enforcing this.

---

## 3. The code

### 3.1 Shared helper — extract, and why (answers item 3)

**Decision: extract.** Two private methods, both lifted verbatim out of `MeleeHitboxRoutine` (`CombatController.cs:642-766`).

The argument for extraction over three copies is not tidiness, it is that the block contains three things with documented silent-failure modes, all of which must stay in step across every path that swings:

- `TakeDamage(damage, "you", foeName, gameObject)` at `:749` — the four-argument overload. The comment at `:746-748` says plainly that dropping `gameObject` leaves the player invisible to kill attribution with no error. Three hand-written copies is exactly how one copy loses that argument.
- `if (targetHealth.GetComponent<CompanionAI>() != null) continue;` at `:718` — Alex must not be cleaved. A copy that forgets it turns the spin into a companion-killer.
- The knockback gate at `:755`, `session.MeleeKnockbackDistance > 0f && !targetHealth.IsDead` — commented at `:752-754` as guarding against shoving a corpse whose agent is already disabled.

The extraction is a **pure move**: `MeleeHitboxRoutine` keeps its own `_hitThisSwing.Clear()` and calls the helper with `MeleeArcAngle`, producing identical behaviour. It lands as its own commit (§6, commit 1) so a reviewer can diff it against nothing else.

Signatures, both private, both non-allocating, both placed in the `Melee Combat` region immediately after `MeleeHitboxRoutine` (i.e. inserted at what is currently line 767, before `OnDrawGizmosSelected` at `:768`):

```csharp
/// <summary>
/// The swing's damage: Strength + the session's melee multiplier + equipped weapon + attack
/// bonus, then scaled by <paramref name="moveMultiplier"/> so a special can hit harder or
/// softer than a plain swing. Lifted unchanged from MeleeHitboxRoutine.
/// </summary>
private int ComputeMeleeDamage(float moveMultiplier)   // body = lines 689-701, × moveMultiplier at the end

/// <summary>
/// One overlap-and-resolve pass: sphere at <paramref name="origin"/>, filter, arc test, damage,
/// knockback. Returns how many targets took damage.
///
/// ⚠ The caller owns <see cref="_hitThisSwing"/> and must clear it itself. That is deliberate
/// and is the ONE thing that differs between the three users:
///   • MeleeHitboxRoutine clears once  → one hit per swing
///   • DashAttackRoutine  clears once  → one hit per dash, however many steps it sweeps over
///   • SpinAttackRoutine  clears per tick → one hit per tick, so standing in the spin hurts
/// Hiding that behind a bool parameter would bury the only decision worth seeing at the call site.
///
/// <paramref name="arcAngle"/> >= 360 skips the facing test entirely — that is the spin.
/// </summary>
private int ResolveMeleeSweep(Vector3 origin, Vector3 facing, float reach, float arcAngle, int damage)
```

`ResolveMeleeSweep` is lines `688` and `703-758` moved wholesale. Inside it, `playerPos` stays `transform.position` (as at `:706`) while `origin` is the waist-height sphere centre (as at `:687`) — the two are deliberately different in the shipped code and must remain so. `PointBlankRange` is read from the field, unchanged. The only new line is the `arcAngle >= 360f` short-circuit around the `Vector3.Dot` test at `:738-739`.

`MeleeHitboxRoutine` after the extraction, between `:706` and `:760`:

```csharp
_hitThisSwing.Clear();
ResolveMeleeSweep(sphereCenter, facing, reach, MeleeArcAngle, ComputeMeleeDamage(1f));
```

Everything else in that routine — the `_isAttacking = true` before the `try` at `:653`, the `finally` at `:762-765`, the `WaitForSeconds(delay)` and `WaitForSeconds(attackDuration)` — is untouched.

### 3.2 New region placement

A new `#region Special Attacks` goes **between the Dodge Roll region's `#endregion` (`:951`) and the Knockback region's `#region` (`:953`)**. It sits next to the roll because the dash is the roll's structural twin, and both are read together.

### 3.3 `PerformSpecialMeleeAttack` — the single entry point

```csharp
/// <summary>
/// Runs a special attack that has already been paid for and put on cooldown by TryUseAbility.
/// Everything a special shares with a plain swing — the riding refusal, the cooldown, the
/// stealth break — happens up there, so this is only the dispatch.
/// </summary>
private void PerformSpecialMeleeAttack(AbilityData ability)
{
    switch (ability.SpecialKind)
    {
        case SpecialAttackKind.Spin: StartCoroutine(SpinAttackRoutine(ability)); break;
        case SpecialAttackKind.Dash: StartCoroutine(DashAttackRoutine(ability)); break;
        default:
            Debug.LogWarning($"PerformSpecialMeleeAttack: '{ability.AbilityID}' has " +
                             $"IsSpecialAttack set but SpecialKind None — nothing to run.");
            break;
    }
}
```

⚠ The `default` case is reached *after* the cost has been charged and the cooldown started (§3.6 orders it that way to match `TryCastAbility`'s existing shape). That is a misauthored-asset path only, it warns loudly, and I judge the alternative — validating the kind before charging, i.e. a second branch earlier in `TryUseAbility` — not worth the extra branch. Flagging it so the reviewer does not read it as an oversight.

### 3.4 `SpinAttackRoutine`

**No new state flag.** It sets `_isAttacking`, which already (a) suspends `HandleMovement` via the `FixedUpdate` gate at `:259`, (b) blocks a second swing at `:613`, a dodge at `:851` and a cast at `:1190`, and (c) is cleared defensively in `OnDisable` (`:223`) and in the death handler (`:1150`). Adding `_isSpecialAttacking` would mean two more places to clear and two more ways to strand the player. Reusing `_isAttacking` is the safer design and costs nothing.

```csharp
private IEnumerator SpinAttackRoutine(AbilityData ability)
{
    // Same discipline as MeleeHitboxRoutine (:644-653) and RollRoutine (:889-892): a stuck
    // _isAttacking gates every attack, cast and step of movement for the rest of the session,
    // so the reset lives in a finally and the flag is raised before the first yield.
    _isAttacking = true;

    try
    {
        SetAnimatorTrigger("SpecialAttack");

        // Once, at the start. Zeroing per tick would suspend gravity for the whole spin —
        // the reason is spelled out at RollRoutine:898-899.
        _rb.velocity = Vector3.zero;

        // ⚠ Deliberately no SetFacing during the spin. The sprite is a billboard that only
        // flips left/right (SpriteBillboard + WorldActorVisual), so turning the facing three
        // times would read as the character twitching, not spinning. The Special clip sells
        // the rotation; the facing stays where the player left it.
        Vector3 facing = _facingDir.sqrMagnitude > 0.001f ? _facingDir.normalized : transform.forward;
        facing.y = 0f;
        if (facing.sqrMagnitude < 0.001f) facing = Vector3.forward;
        facing.Normalize();

        int ticks = Mathf.Max(1, SpinTicks);
        float interval = SpinDuration / ticks;
        int damage = ComputeMeleeDamage(SpinDamageMultiplier);
        float reach = SpinRange > 0f ? SpinRange : MeleeRange;

        for (int t = 0; t < ticks; t++)
        {
            yield return new WaitForSeconds(interval);

            if (_isDead || (_health != null && _health.IsDead)) yield break;
            if (_isKnockedBack) yield break;   // being hit wins, same rule as RollRoutine:912

            Vector3 sphereCenter = transform.position + Vector3.up * (EKVibe.CharacterHeight * 0.5f);

            // Per tick, not per spin: standing inside the spin is meant to hurt repeatedly.
            _hitThisSwing.Clear();
            ResolveMeleeSweep(sphereCenter, facing, reach, 360f, damage);
        }

        yield return new WaitForSeconds(MeleeRecovery);
    }
    finally
    {
        _isAttacking = false;
        // See §0.1: no player controller has a Special STATE yet, only the trigger parameter,
        // so a set trigger latches forever and would fire the day a special sheet is imported.
        ClearAnimatorTrigger("SpecialAttack");
    }
}
```

Uses `WaitForSeconds`, not `WaitForFixedUpdate` — the spin does not move the body, so it has no reason to run at physics rate, and `WaitForSeconds` is timeScale-scaled, so a pause freezes it correctly for free.

### 3.5 `DashAttackRoutine`

Mirrors `RollRoutine` (`:887-941`) structurally, **does not call it**, and reuses exactly one thing from it: `RollSpeedCurve` (`:950`), a `private static float` with the documented property that its integral over [0,1] is 1, which is what makes the distance field mean metres (`:943-949`). Reusing a pure static is not reusing the roll.

```csharp
private IEnumerator DashAttackRoutine(AbilityData ability)
{
    _isAttacking = true;

    try
    {
        // Unlike the roll, the dash faces where it goes. PerformDodge deliberately does NOT
        // SetFacing (:865-867) so you can roll backwards out of a fight; a dash is an attack
        // and must commit to a direction.
        Vector3 dir = GetScreenRelativeMoveDirection(ReadMoveInput());
        if (dir.sqrMagnitude < 0.0001f) dir = _facingDir;
        dir.y = 0f;
        if (dir.sqrMagnitude < 0.0001f) dir = Vector3.forward;
        dir.Normalize();
        SetFacing(dir);

        // The dash reuses the roll clip: SpecialAttack is one trigger and the spin has it,
        // and Roll is a 6@14 = 0.43 s lunge that reads correctly. See §8c.
        SetAnimatorTrigger("Roll");

        _rb.velocity = Vector3.zero;   // once, not per step — RollRoutine:898-899

        int damage = ComputeMeleeDamage(DashDamageMultiplier);
        float reach = DashRange > 0f ? DashRange : MeleeRange;

        // Once for the whole dash: passing an enemy must cost them one hit, not one per
        // physics step. This is the opposite of the spin and is the point of the helper
        // leaving the clear to the caller.
        _hitThisSwing.Clear();

        // ⚠ Snapshotted, then polled every step. CurrentChunkData is written from eight
        // places across six files (CLAUDE.md §3), so hooking one transition would miss the
        // others. A dash into an edge trigger starts TransitionToChunkRoutine, which pushes
        // a pause and teleports the player: without this, the dash resumes on the far side
        // and drives the body away from the arrival marker.
        var chunkManager = World.ChunkManager.Instance;
        MapChunkData chunkAtStart = chunkManager != null ? chunkManager.CurrentChunkData : null;

        float elapsed = 0f;
        var wait = new WaitForFixedUpdate();

        while (elapsed < DashDuration)
        {
            // Cooperative cancellation, checked before moving — RollRoutine:907-912.
            if (_isDead || (_health != null && _health.IsDead)) yield break;
            if (_isKnockedBack) yield break;
            if (Systems.PauseManager.IsPaused) yield break;
            if (chunkManager != null
                && (chunkManager.IsTransitioning || chunkManager.CurrentChunkData != chunkAtStart))
                yield break;

            float speed = DashDistance / DashDuration * RollSpeedCurve(elapsed / DashDuration);

            // ⚠ MovePosition, never a transform write: this Rigidbody is non-kinematic so
            // MovePosition sweeps and resolves against colliders (RollRoutine:916-920).
            // Enemy capsules are solid (Enemy_Neek.prefab:57 m_IsTrigger: 0), so the dash
            // STOPS at the first enemy it reaches. That is the intended v1 feel.
            _rb.MovePosition(_rb.position + dir * (speed * Time.fixedDeltaTime));

            Vector3 sphereCenter = transform.position + Vector3.up * (EKVibe.CharacterHeight * 0.5f);
            ResolveMeleeSweep(sphereCenter, dir, reach, DashArcAngle, damage);

            elapsed += Time.fixedDeltaTime;
            yield return wait;
        }

        yield return new WaitForSeconds(MeleeRecovery);
    }
    finally
    {
        _isAttacking = false;
    }
}
```

Note the `PauseManager.IsPaused` poll **cancels** rather than suspends. Per §0.4 a pause already freezes the loop (timeScale 0 stops FixedUpdate); this poll exists for the one frame where the pause is pushed and popped around a teleport, and because resuming a committed lunge after the player closes their inventory is the wrong behaviour. It is one line and it is the same idiom as `:912`.

Tuning fields, appended after `RollCooldown` (`:73`) under `[Header("Special Attacks")]`, all Inspector-tunable, all proposals:

```
SpinDuration          0.60f   SpinTicks 3   SpinRange 2.40f
SpinDamageMultiplier  0.60f   SpinStaminaPercent 35f
DashDuration          0.28f   DashDistance 3.20f
DashRange             1.10f   DashArcAngle 140f
DashDamageMultiplier  1.25f   DashStaminaPercent 30f
```

### 3.6 The branch in the ability path

`TryCastAbility` (`:1188-1238`) splits in two. The slot resolution stays; the body moves to a new private method so both entry points share one copy of the gates and the cooldown:

```csharp
public void TryCastAbility(int slotIndex)          // unchanged signature, still called from
{                                                  // HandleInput:390-393 and UIManager:716-721
    if (EquippedAbilities == null || slotIndex < 0 || slotIndex >= EquippedAbilities.Count) return;
    TryUseAbility(EquippedAbilities[slotIndex]);
}

public void TrySpecialAttack(int index)
{
    if (SpecialAttacks == null || index < 0 || index >= SpecialAttacks.Count) return;
    TryUseAbility(SpecialAttacks[index]);
}

private void TryUseAbility(AbilityData ability)
{
    if (_isAttacking || _isRolling || _isKnockedBack || _isDead) return;   // was :1190
    if (BlockedByRiding()) return;                                          // was :1191 — the
    if (ability == null) return;                                            // specials inherit
                                                                            // the riding refusal free

    if (_abilityCooldowns.ContainsKey(ability.AbilityID)                     // was :1197-1202
        && _abilityCooldowns[ability.AbilityID] > 0f) { …unchanged… }

    if (ability.IsSpecialAttack)
    {
        // ⚠ Before the concealment drain (:1225-1230) and before CastAbilityRoutine's shout
        // (:1265-1268). A special is a weapon swing, not magic: it must not drain Concealment
        // and must not shout a spell name.
        if (!ability.CanBeUsedBy(CurrentPlayerClass()))
        {
            UIManager.Instance?.LogCombat("You don't know how to do that.");   // owner may reword
            return;
        }

        int cost = SpecialStaminaCost(ability);
        if (CurrentStamina < cost) { UIManager.Instance?.LogCombat("Not enough Stamina."); return; }
        CurrentStamina -= cost;

        BeginAbilityCooldown(ability);
        BreakStealth();                      // §3.7
        PerformSpecialMeleeAttack(ability);
        return;
    }

    …lines 1204-1237 unchanged, with 1220-1222 replaced by BeginAbilityCooldown(ability)
      and 1232-1235 replaced by BreakStealth()…
}
```

Two three-line helpers keep the duplication at zero:

```csharp
private void BeginAbilityCooldown(AbilityData ability)   // exactly :1220-1222
private void BreakStealth()                              // exactly :1232-1235, the same body as
                                                         // :619-621 and :880-882
```

`BreakStealth` is a pure de-duplication of a block already written out three times identically (`:619-621`, `:880-882`, `:1232-1235`). Extracting it is optional; I recommend it because the comment attached to it ("routed through ToggleStealth so the tint, the toast and the CRO button come back in step") is a rule that now has a fourth caller.

Cost and class helpers:

```csharp
/// <summary>
/// Percent of the live maximum, floored, minimum 1 — the same shape as CurrentRollCost
/// (:840-843) and for the reason its comment gives at :828-838: a flat cost silently becomes
/// cheaper every level as MaxManaStamina grows. AbilityData.ResourceCost is deliberately NOT
/// read here, and the two assets carry ResourceType None so the generic charge at :1217-1218
/// would be a no-op even if this branch were ever removed.
/// </summary>
private int SpecialStaminaCost(AbilityData ability)
{
    float pct = ability.SpecialKind == SpecialAttackKind.Spin ? SpinStaminaPercent : DashStaminaPercent;
    return PlayerData != null
        ? Mathf.Max(1, Mathf.FloorToInt(PlayerData.MaxManaStamina * pct / 100f))
        : 12;
}

private static PlayerClass CurrentPlayerClass()
{
    var session = Flow.PlayerSession.Instance;
    return session != null ? session.Class : PlayerClass.YoungDriller;   // PlayerSession.cs:27
}
```

`CanBeUsedBy` on `AbilityData` is a copy of `PerkData.CanBeTakenBy` (`PerkData.cs:88-96`), empty-admits-everyone.

Cooldown read for the HUD, appended next to `GetCooldownRemaining` (`:1175-1186`):

```csharp
public float GetSpecialCooldownRemaining(int index, out float total)   // same body, SpecialAttacks
public AbilityData GetSpecial(int index)                               // null-safe accessor for the HUD
public const int SpecialSlots = 2;
```

Desktop input, appended after `:393`, outside the `#if UNITY_STANDALONE…` block to match how Alpha1–4 are written:

```csharp
if (Input.GetKeyDown(KeyCode.Alpha5)) TrySpecialAttack(0);
if (Input.GetKeyDown(KeyCode.Alpha6)) TrySpecialAttack(1);
```

---

## 4. The guards, itemised

| Guard | Where | Verified basis |
|---|---|---|
| Chunk change mid-dash | snapshot `ChunkManager.CurrentChunkData` before the loop, poll it **and** `IsTransitioning` before each `MovePosition` | `ChunkManager.cs:44` (field), `:105` (`IsTransitioning`); CLAUDE.md §3 "poll a remembered reference"; edge triggers enter via `OnPlayerHitEdge` (`:230`) |
| Pause mid-dash | `Systems.PauseManager.IsPaused` poll in the loop, cancels | `PauseManager.cs:13,35`; `FixedUpdate` (`:253-261`) has no pause check, `Update` (`:242`) does |
| Knockback mid-move | `if (_isKnockedBack) yield break;` in both loops, before moving | identical to `RollRoutine:912`; knockback always wins per `:977-979` |
| Death mid-move | `_isDead || _health.IsDead` in both loops | matches `:672` and `:912` |
| Buffer truncation at 32 | widen `_hitResults` to 64 + editor-only saturation warning in `ResolveMeleeSweep` | `:113`; `OverlapSphereNonAlloc` with mask `~0` at `:688` counts ground, buildings and props toward the cap before any filtering, and the spin's 2.4 m radius makes saturation likely in a built-up chunk. See §5.3. |
| Dedupe semantics | cleared **per tick** in the spin, **once** in the dash, **once** in the swing; helper never clears | `_hitThisSwing` at `:114`, cleared at `:708` today |
| Stealth break | `BreakStealth()` in the special branch | `PerformMeleeAttack:616-621`, `PerformDodge:877-882` both do it; a special that did not would leave the player crouched, tinted and boosted mid-cleave |
| Riding | inherited — `BlockedByRiding()` runs before the branch | `:630-640`, `:1191` |
| Companion friendly fire | inherited from the helper | `:718` |
| Latched animator trigger | `ClearAnimatorTrigger("SpecialAttack")` in the spin's `finally` | §0.1; precedent `:1020` |
| Stuck `_isAttacking` | `try`/`finally` in both routines, flag raised before the first yield | the discipline documented at `:644-652` |

---

## 5. The three shipped-code changes and their justification

**5.1 Extract `ResolveMeleeSweep` / `ComputeMeleeDamage`.** Justified in §3.1. Own commit, no behaviour change intended.

**5.2 `TryCastAbility` → `TryUseAbility`.** A body move below the slot lookup. Public signature unchanged, so `HandleInput:390-393` and `UIManager.OnActionButtonPressed:716-721` are untouched. Own commit.

**5.3 `_hitResults` 32 → 64.** This is a **deliberate behaviour change to shipped melee**, not a refactor, and gets its own commit for that reason. With mask `~0` and `QueryTriggerInteraction.Collide` (`:688`), the array fills with terrain, building and prop colliders before the filter ever runs; at 32 slots in a built-up chunk the enemy the player is aiming at may simply not be in the array, and `OverlapSphereNonAlloc` reports that by silently returning 32. Widening strictly increases what the player can hit — it can only fix misses, never create false ones. Cost is 32 extra references, allocated once, on a field that is `readonly` and never re-allocated. Adding:

```csharp
#if UNITY_EDITOR
if (hitCount == _hitResults.Length)
    Debug.LogWarning($"ResolveMeleeSweep: overlap buffer saturated at {hitCount} — " +
                     "targets beyond this were dropped. Raise _hitResults.");
#endif
```

A layer mask would be the real fix and is explicitly out of scope: `ProjectSettings/TagManager.asset` defines no user layers, and every enemy and police prefab sits on layer 0.

---

## 6. Commit sequence

Each is independently coherent and independently reviewable.

1. **`refactor(combat): extract ResolveMeleeSweep and ComputeMeleeDamage from MeleeHitboxRoutine`** — `CombatController.cs` only. Pure move; `_hitThisSwing.Clear()` stays at the call site. No new fields.
2. **`fix(combat): widen the melee overlap buffer to 64 and warn on saturation`** — `CombatController.cs:113` + the editor warning. Behaviour change, called out in the message.
3. **`feat(data): add IsSpecialAttack, SpecialKind and AllowedClasses to AbilityData`** — `AbilityData.cs` + new `SpecialAttackKind` enum + `CanBeUsedBy`. Data only, nothing reads it yet. **Existing `.asset` files are not touched** — all three fields default safely.
4. **`fix(data): keep special-attack assets out of the spellbook`** — one guard in `SpellDatabase.EnsureLoaded` (`SpellDatabase.cs:~61`): `if (ability.IsSpecialAttack) continue;`, with a comment naming §2.3's invariant. Defends against a misfiled asset reaching `LearnAllCurrentSpells` and thereby `savegame.json`.
5. **`feat(combat): add the spin and dash special-attack routines`** — the new `#region Special Attacks` between `:951` and `:953`, the eleven tuning fields, `PerformSpecialMeleeAttack`, both coroutines, `SpecialStaminaCost`, `CurrentPlayerClass`. Not reachable from anything yet — compiles and does nothing.
6. **`feat(combat): route special attacks through the ability path`** — `TryUseAbility` extraction, the `IsSpecialAttack` branch, `BeginAbilityCooldown`, `BreakStealth`, `SpecialAttacks` list, `SpecialSlots`, `GetSpecial`, `GetSpecialCooldownRemaining`, Alpha5/Alpha6. Now reachable by keyboard.
7. **`feat(ui): add ActionKind.Special to HUDActionButton`** — enum member at index 6, `Awake` overlay gate widened, `Update`'s cooldown source branched, `Invoke` gains a `case` **before** `default`.
8. **`feat(ui): build the SPN and DSH buttons into the action row`** — `UIManager.BuildActionButtons`, `OnSpecialAttackPressed`, `RefreshSpecialSlots` + its cache, the `Update` call.
9. **`feat(editor): add Tools/Content/Create Special Attack Assets`** — new file in `Assets/Editor/Content/` **with its `.meta` committed alongside** (CLAUDE.md §3).
10. **`docs: add PLAYER_COMBAT.md and route to it`** — see §10.
11. *(optional, offer separately)* **`fix(combat): bail the dodge roll on a chunk change or pause`** — the same two polls added to `RollRoutine:905-934`. The roll has the identical latent bug today. Out of the default scope; do not fold it into commit 5.

---

## 7. HUD work

### 7.1 Positions

Both buttons continue the existing bottom-right row, using the same 16 px gap arithmetic the DGE comment spells out at `UIManager.cs:930` ("361 = USE's 205 + its 140 width + a 16 px gap"). Added inside `BuildActionButtons`, immediately after the DGE call at `:931-932`, **parented to `panel.transform`**:

```csharp
// SPN / DSH — the row continues leftward: ATK, USE, DGE, SPN, DSH reading right to left.
// 517 = DGE's 361 + its 140 width + 16.   673 = 517 + 140 + 16.
var spin = CreateActionButton(panel.transform, "SPN", HUDActionButton.ActionKind.Special, 0,
    new Vector2(140f, 140f), new Vector2(-517f, 40f), rightEdge);
var dash = CreateActionButton(panel.transform, "DSH", HUDActionButton.ActionKind.Special, 1,
    new Vector2(140f, 140f), new Vector2(-673f, 40f), rightEdge);
_specialSlotImages[0] = spin.GetComponent<Image>();
_specialSlotLabels[0] = spin.GetComponentInChildren<TextMeshProUGUI>();
…same for dash…
```

`SPN`/`DSH` are placeholder glyphs; once the owner sets `IconGlyph` on the assets, `RefreshSpecialSlots` replaces them, exactly as `RefreshSpellSlots:1190-1192` does for spells.

`CreateActionButton` sets `pivot = anchor` (`:1097-1098`), so with `rightEdge = (1,0)` the anchored position is the button's bottom-**right** corner measured from the screen's bottom-right. Occupancy at the 1920×1080 reference:

| Element | x (from right edge) | y | Source |
|---|---|---|---|
| ATK 165×165 | −189 … −24 | 30 … 195 | `:906-907` |
| USE 140×140 | −345 … −205 | 40 … 180 | `:1136-1137` |
| DGE 140×140 | −501 … −361 | 40 … 180 | `:931-932` |
| **SPN 140×140** | **−657 … −517** | **40 … 180** | new |
| **DSH 140×140** | **−813 … −673** | **40 … 180** | new |
| Spell column 125×125 ×4 | −149 … −24 | 215 … 751 | `:910-916` |
| Interact prompt 260×36 | −420 … −160 | 200 … 236 | `:1147-1148` |
| CRO 130×130 (bottom-**left**) | 115 … 245 from left | 344 … 474 | `:923-924`, `:1048-1057` |
| Joystick 280×280 (bottom-left) | 40 … 320 from left | 40 … 320 | scene default per `:1046` |
| CombatLog 520×100 | top-centre, (0.5,1) anchored at (0,−12) | — | `c.unity`, RectTransform `1348187920` under parent `CombatLog` |

No overlap. The nearest miss is the interact prompt, which sits at y 200–236, 20 px above the new row's top edge of 180 — and it is `raycastTarget = false` (`:870`) so it could not steal a touch even if it did overlap.

Aspect-ratio check: the HUD canvas is the one carrying `UIManager` (GameObject `1081454732`), reference `1920×1080`, `ScreenMatchMode 0`, `m_MatchWidthOrHeight: 0.5` (`c.unity:75649-75651`). Worst realistic case is a 4:3 tablet at 2048×1536 → scale `(2048/1920)^0.5 × (1536/1080)^0.5 ≈ 1.232` → reference width ≈ 1662. DSH's left edge then sits 1662 − 813 = **849 px from the left**, against a joystick whose right edge is at 320. Clear by 529 px. On a 20:9 phone the reference width grows to ≈ 2147 and the margin is larger still.

### 7.2 Cooldown overlay

`HUDActionButton.Awake:32-33` currently builds the radial overlay only for `Ability`. Widen:

```csharp
if (Kind == ActionKind.Ability || Kind == ActionKind.Special)
    BuildCooldownOverlay();
```

and branch the source in `Update:68`, because `GetCooldownRemaining` indexes `EquippedAbilities` and would read the wrong list:

```csharp
float remaining = Kind == ActionKind.Special
    ? combat.GetSpecialCooldownRemaining(AbilityIndex, out float total)
    : combat.GetCooldownRemaining(AbilityIndex, out total);
```

`Invoke:78-98`: add `case ActionKind.Special: UIManager.Instance.OnSpecialAttackPressed(AbilityIndex); break;` **before** `default:` — `Ability` is served by `default` (`:95-97`), so a case appended after it would be unreachable.

New handler in `UIManager`, beside `OnDodgePressed` (`:747-752`):

```csharp
public void OnSpecialAttackPressed(int index)
{
    var combat = Combat.CombatController.Instance;
    if (combat != null) combat.TrySpecialAttack(index);
}
```

### 7.3 Availability painting

`RefreshSpecialSlots()` alongside `RefreshSpellSlots()` in `Update` (`:200`), with the same cached change-detection the comment at `:191-194` insists on for the mobile hot path (`_cachedSpecials[2]`, `_specialSlotsInitialized`). A slot is *unavailable* when the `SpecialAttacks` entry is null **or** `!ability.CanBeUsedBy(session.Class)`; unavailable paints `Win95Skin.Face` at alpha 0.35 and keeps the placeholder label, available paints full `Win95Skin.Face` and swaps in `IconGlyph`.

Note for the reviewer, not a change: `RefreshSpellSlots:1182` repaints the four spell buttons with `EKVibe.ButtonBrown`, overriding the `Win95Skin.StyleButton` face `CreateActionButton:1104` gave them. That inconsistency is pre-existing. I am matching **Win95Skin** for the two new buttons, so they will sit with ATK/USE/DGE/CRO rather than with the brown spell column. Left as-is deliberately; unifying the spell column is a separate UI decision.

### 7.4 Driving mode

Nothing to write. Both buttons are children of `_actionButtonsPanel`, and `SetDrivingMode:1014` does `_actionButtonsPanel.SetActive(!isDriving)`. ⚠ The invariant to preserve: they must be parented to `panel.transform` inside `BuildActionButtons`. Parent them anywhere else and they stay on screen while driving, and `BlockedByRiding` (`:630-640`) will bark a toast every tap. (This is a UI panel, not a vehicle root or a chunk root — CLAUDE.md's `SetActive(false)` prohibitions do not apply to it.)

---

## 8. The three open decisions

### (a) Does the spin hit civilians and police?

**Recommendation: use the basic melee filter unchanged. No new exclusion, no layer mask.**

Per §0.2 there is nothing to exclude. Civilians have no `Health`, so they are already skipped at `:717`. The only non-enemy `Health` inside 2.4 m is a police officer, and police are hostile combatants who should be hit. Per §0.3 no damage path raises a wanted level, so there is no free-star or unfair-star exposure either way.

The residual risk the swarm was reaching for is real but different: `~0` plus a 2.4 m sphere means the spin can hit an enemy the player did not intend to aggro. That is a design consequence of a 360° move, not a bug, and it is the move's cost.

*Alternative if the owner later disagrees:* add an `EnemyAI`-required filter to the spin only (`if (targetHealth.GetComponent<EnemyAI>() == null) continue;`, the same test `FindSpellTarget:1326` already uses). That would make the spin unable to hit police, which I think is wrong — police are the fight the consequence layer creates.

### (b) What do spin and dash cost?

**Recommendation: a percent of the live maximum, not `AbilityData.ResourceCost`. Spin 35 %, dash 30 %, both Inspector fields on `CombatController`.**

The reason is written into the codebase already: `CurrentRollCost`'s comment (`:826-838`) explains at length that a flat cost silently becomes cheaper at every level because `MaxManaStamina` grows, and that flooring rather than rounding is what makes "two rolls from full" an invariant. A flat `ResourceCost` int on the asset would reintroduce exactly the bug that comment exists to prevent. Set `ResourceType = None` on both assets so the generic charge at `:1217-1218` is inert even if the branch is ever restructured.

Against the pools (`PlayerClass.cs:151-163`: Dynamo 80, MrHood 60, YoungDriller 55, Stabmeister 50, BundaBasher 40) and the roll's 50 %, a full bar buys roll + spin (85 %), or spin + dash (65 %), or two rolls — never three actions. Regen is 5 %/s (`:90`), so a full bar refills in ~20 s. That reads as the right pressure for a survival-stamina design.

*Alternatives:* (i) flat `ResourceCost` — rejected above; (ii) free, cooldown-only — makes the stamina bar irrelevant to the two flashiest moves and undercuts the survival pass; (iii) health cost for the dash — interesting, but it needs a `Health.TakeDamage` self-call whose i-frame and `LastAttacker` interactions are not worth opening here.

### (c) New `special` sheets only, or re-frame the attack clip?

**Recommendation: new art for the spin only. Do not touch the attack clip. Ship the dash on the existing `Roll` clip.**

`MeleeHitDelay 0.15 + MeleeRecovery 0.35 = 0.50 s` (`:43,45`) is exactly `attack`'s 6 frames @ 12 fps (`ArtImportTool.cs:89`), and the coupling is deliberate. Changing the frame count forces retuning two Inspector-authored fields that live in `c.unity`, and the whole feel of basic melee is calibrated against them. Not worth it for this feature.

The spin gets a `sheet_char_player_special.png` per class subject (6 frames @ 12 fps, non-looping — `ArtImportTool.cs:103`), imported via `Tools → Art → Import Generated Art`. That is the only art this feature needs. **Nothing is blocked on it**: `SetAnimatorTrigger` no-ops on a missing parameter (`:1292-1294`) and a missing *state* just means no visual — the gameplay is complete without art.

The dash reuses `Roll` (6 @ 14 fps = 0.43 s, `ArtImportTool.cs:94`) because there is exactly one `special` action key in the contract and the spin has it. If the owner later wants a distinct dash clip, it is a three-line append to `ArtImportTool.cs` — `{"special_dash","SpecialDash"}` at `:60`, `{"special_dash","DashAttack"}` at `:74`, a contract row at `:103` — plus swapping one trigger string in `DashAttackRoutine`. No enum, no save key, no serialized field.

---

## 9. Verification

### What the implementer can prove here

```bash
python Tools/asset_reachability.py --check-dangling
```

Run before and after commit 9 (the editor tool adds a file and a `.meta`). Exit 0 clean, 1 dangling, 2 could-not-verify. **This proves reference integrity and nothing else** — it says nothing about whether the project compiles.

A brace/paren balance scan on the three touched `.cs` files catches a truncated edit. **It is not a compile and must not be reported as one.**

Grep checks worth running as cheap invariant tests:
- `grep -rn "IsSpecialAttack" Assets/Resources/Abilities/` returns nothing — no special asset has leaked into `Resources`.
- `grep -c "SetActive(false)" ` on the new `UIManager` lines: the two buttons must not do their own hiding.
- The `ActionKind` enum still reads `Attack, Ability, Inventory, Interact, Crouch, Dodge, Special` in that order.

### What cannot be proved without Unity, stated plainly

There is no C# compiler, no Unity and no test framework in this environment (CLAUDE.md §5). Everything below needs the owner:

- **Whether any of it compiles.** Nine of the eleven commits touch C#.
- Whether the two new buttons land where the arithmetic in §7.1 says they do. The maths is from the shipped constants and I am confident in it, but only the Game view proves it.
- Whether the spin's damage-per-tick × 3 feels right, and whether 0.28 s / 3.2 m reads as a dash rather than a stumble.
- Whether the dash stopping dead on the first enemy capsule reads as "connected" or as "stuck". This is the single most likely thing to need retuning.
- Whether the buffer widening actually changes anything observable — it only matters in a crowded, built-up chunk.
- Whether the chunk-change bail fires correctly. Reproducing it means dashing into a chunk edge trigger, which is a hand test.
- Whether `ClearAnimatorTrigger("SpecialAttack")` prevents the latch. Unprovable until a `special` sheet exists and a `Special` state is authored — flag it in the ledger as *deferred*, not verified.
- Whether the editor tool creates the assets correctly. **An editor tool that generates content has changed nothing until a human runs the menu item.**

---

## 10. Docs (CLAUDE.md §7)

- **New: `docs/reference/PLAYER_COMBAT.md`**, with a `Last verified against:` header naming the merge commit. It owns: the three melee entry points and their shared sweep helper; the dedupe contract (per-tick / once / once) and why the helper does not clear; the state-flag reuse of `_isAttacking` and why there is no `_isSpecialAttacking`; the percent-cost rule and its link to `CurrentRollCost`; the `ActionKind` index table; and — most importantly — the §2.3 invariant that a special-attack asset must never live under `Resources/Abilities` and must never be passed to `LearnAbility`.
- **`CLAUDE.md` §4 and `docs/README.md`** each gain the row *"Player melee, the dodge roll, special attacks and the melee sweep helper → `docs/reference/PLAYER_COMBAT.md`"*. CLAUDE.md §4 says "This table mirrors docs/README.md's. Change both together" — both, in commit 10.
- **`docs/reference/SPELLS.md`** gains one sentence: special attacks are `AbilityData` but are not spells, do not go through `SpellRuntime`, and are documented in `PLAYER_COMBAT.md`. Its verification header updates with it.
- **`docs/reference/VERIFICATION_LEDGER.md`** gains one open item in its existing format: everything in this plan lands unseen by a compiler or the editor.
- **`docs/plans/PLAYER_SPECIAL_ATTACKS_PLAN.md`** — this plan, plus §11 as its check list, listed in `docs/README.md`'s active-plans table.
- **`docs/art/ART_QUEUE.md`** — the player `special` sheet is requested but **not** marked delivered (its maintenance contract: an accepted import updates it in the same piece of work, not when the art is first asked for).

---

## 11. Editor checklist for the owner

Do these in order, after pulling the branch. **Exit Play mode before every step** — Inspector changes made during Play are discarded when it stops (CLAUDE.md §5).

1. Let Unity finish the recompile after the pull. Check the Console is clean before going further; if commits 1–8 do not compile, nothing below will work and the errors are the real output of this piece of work.
2. **Create the two assets.** Menu bar → `Tools → Content → Create Special Attack Assets`. It creates `Assets/Data/Abilities/Special_spin.asset` and `Assets/Data/Abilities/Special_dash.asset` if they are absent, and skips them if they already exist. It never overwrites — it is not a Danger Zone tool.
3. **Fill in the prose.** Project panel → `Assets/Data/Abilities/` → select `Special_spin`. In the Inspector, set `AbilityName`, `Description` and `IconGlyph` (the two-or-three-character glyph the HUD button shows). These are your words; the tool leaves them blank on purpose. Repeat for `Special_dash`. Verify `IsSpecialAttack` is ticked, `SpecialKind` is `Spin` / `Dash` respectively, and `ResourceType` is `None`. **Do not move these assets into `Assets/Resources/`** — see step 8.
4. **Set the class gate.** Same Inspector, `AllowedClasses`. Leave the array at size 0 to let every class use the move. To restrict, set the size and pick the classes.
5. **Set the cooldowns.** `CooldownTime` on each asset — this is what drives the radial sweep on the HUD button. Suggested 6 s spin, 5 s dash.
6. **Wire them to the player.** Hierarchy panel → find the player GameObject (the one carrying `CombatController`; if you cannot see it, use the Hierarchy search box for `CombatController` with the search dropdown set to `All`). Inspector → `Combat Controller` component → the new `Special Attacks` header → set `Size` to 2, drag `Special_spin` into element 0 and `Special_dash` into element 1. **Order matters**: element 0 is the SPN button, element 1 is DSH. Then `Ctrl+S` to save `c.unity`.
   *If you skip this step the two buttons render dimmed and do nothing — that is the designed failure mode, not a bug.*
7. **Tune.** Same component, the new `Special Attacks` header, eleven fields. The two you are most likely to want to change first are `DashDistance` and `SpinDamageMultiplier`.
8. **Confirm the spellbook is clean.** Menu bar → `Tools → Debug → Learn All Current Spells`, then open the spellbook in Play mode. **Only the six spells should appear.** If either special shows up, one of them has been placed under `Assets/Resources/Abilities/` — move it back to `Assets/Data/Abilities/` **inside Unity** (drag in the Project panel, never in Explorer, so the `.meta` travels with it) and re-check.
9. **Play test.** Press `5` and `6` on the keyboard, and tap SPN and DSH on the touch HUD. Check: the radial overlay sweeps; stamina drops by the expected percent; the CRO button pops back to "CRO" if you were crouched; both are refused with a toast while riding a vehicle; both hide entirely while driving; dashing into an enemy stops you rather than passing through.
10. **Dash the edge.** Walk to a chunk boundary and dash into it. The transition should happen and you should end up at the arrival marker, **not** sliding away from it. This is the guard in §4 and it is the one thing here most worth testing by hand.
11. *(when art exists)* Drop `sheet_char_player_special.png` + its sidecar into the staging folder, then menu bar → `Tools → Art → Import Generated Art`. The importer adds the `Special` state and its Any-State transition; the `SpecialAttack` parameter is already present in all five player controllers.

---

## Files this plan touches

- `Assets/Scripts/Combat/CombatController.cs`
- `Assets/Scripts/Data/AbilityData.cs`
- `Assets/Scripts/Data/SpellDatabase.cs`
- `Assets/Scripts/UI/HUDActionButton.cs`
- `Assets/Scripts/UI/UIManager.cs`
- `Assets/Editor/Content/SpecialAttackTools.cs` *(new, `.meta` must be committed with it)*
- `Assets/Data/Abilities/Special_spin.asset`, `Special_dash.asset` *(created by the editor tool, not by the implementer)*
- `Assets/c.unity` *(owner-only: the `SpecialAttacks` assignment in step 6)*
- `docs/reference/PLAYER_COMBAT.md` *(new)*, `docs/reference/SPELLS.md`, `docs/reference/VERIFICATION_LEDGER.md`, `docs/plans/PLAYER_SPECIAL_ATTACKS_PLAN.md` *(new)*, `docs/README.md`, `CLAUDE.md`
- Read but **not** changed: `Assets/Editor/Art/ArtImportTool.cs`, `Assets/Scripts/World/ChunkManager.cs`, `Assets/Scripts/Systems/PauseManager.cs`, `Assets/Scripts/Data/PerkData.cs`, `Assets/Scripts/Data/PlayerClass.cs`, `Assets/Scripts/Combat/Health.cs`, `Assets/Scripts/Combat/EnemyAI.cs`
