# Dodge/Roll + Knockback — implementation plan

Status: **implemented — all four phases committed on `dodge-roll-phase2`, never compiled, never
playtested.** Revision 2, written against `main` as of 2026-08-08. The verification ledger in
CLAUDE.md §5 carries one entry per phase with the in-editor checks; delete each as it is
confirmed. Two deliberate deviations from this text, both recorded in the commit messages and the
ledger: the knockback slide duration is a `const` (0.22 s) rather than an Inspector field, and
`EnemyAI`'s agent resync skips dead enemies because `SnapToNavMesh` would re-enable a corpse's
agent (`TryStep` also gained an `out bool slid` to preserve `TryCollideMove`'s facing behaviour).
Revision 1 was reviewed against the real code; the corrections it produced are folded in below and
listed in §2 so the deltas are auditable rather than silently absorbed.

Two mechanics, four phases. The phasing is deliberate: all code lands and is playable with
**no new art**, and the sprite sheets slot in afterwards without another code change, because
every animation call site in this project already guards against missing parameters
(`CombatController.SetAnimatorTrigger`, CombatController.cs:781; `WorldActorVisual.HasAttackAnimation`).

Open design questions for the owner are collected at the bottom, each with a recommendation.
Nothing below blocks starting Phase 1.

***

## 1. Scope

**In:**

* A player dodge/roll: stamina-costed, i-framed, cooldown-gated, driven from a HUD button and the
  space bar.
* A `bool` return on `Health.TakeDamage` so a caller can tell whether the hit actually landed.
* Enemy-authored knockback of the player, off by default on every existing prefab.
* Two new art actions (`roll`, `knockback`) wired through the importer and queued.
* One new `PerkEffectType` (`MeleeKnockback = 9`) and the player→enemy knockback it drives.

**Out — explicitly:**

* Any dialogue, quest or flavour prose. The only new player-facing strings are mechanical: the
  three-letter HUD label, `"Dodged!"` over the player, and the existing `"Not enough Stamina."`
  line reused verbatim from CombatController.cs:693.
* Any perk asset. `PerkData` assets are authored by the owner in Unity; none ship with this code.
* Any enemy prefab authoring. Which enemies knock back is an Inspector pass, §13.4.
* Rebalancing armour, XP or enemy levels.
* Any `.asset`, `.prefab` or save-key rename. **Nothing in this plan renames a serialized field
  or reorders an enum.**

***

## 2. What changed from revision 1, and why

Each of these was verified in the file and line named. Revision 1's text is replaced, not
annotated — the old wording is what a reader carries away.

| # | Revision 1 said | Reality | Fix |
|---|---|---|---|
| 1 | Call `ApplyKnockback` "after the successful `TakeDamage` call" | `Health.TakeDamage` returns `void` (Health.cs:41–85). An i-frame early-out is invisible to `EnemyAI`, so **a dodged hit still knocks the player back** | `TakeDamage` returns `bool`, in **Phase 1**, so `Health.cs` is touched once |
| 2 | Cross-cutting checklist named only `PerkEffectType` as append-only | `HUDActionButton.ActionKind` (HUDActionButton.cs:19) is also serialized by index and needs `Dodge = 5` appended | Enum mapping table, §7 |
| 3 | `FloatingDamageText.Spawn(pos, 0)` for the dodge | The only overload is `Spawn(Vector3, int, Color?)` and it does `amount.ToString()` (FloatingDamageText.cs:20–26) — that renders a literal red **0** over the player | Add a `string` overload; `SpellShoutText.Spawn(Vector3, string)` is the precedent |
| 4 | Player knockback must use a capsule-cast like `EnemyAI.TryCollideMove` | The player's Rigidbody in `c.unity` is **non-kinematic** (`m_IsKinematic: 0`), gravity on, interpolate on, discrete, capsule r=0.28 h=1.8. `HandleMovement` already moves with `_rb.MovePosition` (CombatController.cs:337), which sweeps and resolves — that is why walking does not clip walls | Player roll and player knockback both use `MovePosition`. The capsule-cast is kept for **Phase 4 only** |
| 5 | 25 stamina per roll | ~50 max at 7/s regen = 3.6 s to afford the next roll, so the 1.0 s cooldown never binds and two rolls can never chain. The pool is shared with stamina abilities (CombatController.cs:690–698) | 14, and Inspector-visible. §3 |
| 6 | "a second `HUDActionButton` beside ATK … a scene edit to `Assets/c.unity`" | ⚠ **This is wrong, and so is the review finding that proposed a `HudActionClusterBuilder` editor tool to fix it.** The live action cluster is **built at runtime** by `UIManager.BuildActionButtons` (UIManager.cs:551–592): ATK, four spell slots and CRO. The scene's `ActionCluster` (holding `AttackButton`, `Skill0-2`) is the *legacy* cluster and is switched off at Start by `RightActionPanel.gameObject.SetActive(false)` (UIManager.cs:556) | **No scene edit and no editor tool.** The dodge button is one `CreateActionButton` call, exactly as CRO was added. §3 |
| 7 | i-frames as a `public bool { get; private set; }` cleared by two coroutines | Two systems (roll, knockback-recovery) both writing one bool is the classic way to get a permanently invulnerable player | A timestamp: `IsInvulnerable => Time.time < _invulnerableUntil` |
| 8 | Knockback and roll "cancel each other, last one wins — both coroutines must stop the other" | Requires `StopCoroutine`, and whether Unity runs a stopped coroutine's `finally` is not something this environment can verify | Knockback always wins, by a cooperative flag the roll polls. No `StopCoroutine` anywhere in this plan |
| 9 | Importer table called `ActionSpecs` | It is `ActionContract` (ArtImportTool.cs:75) | Named correctly in §5 |

Two documentation defects found on the way, neither caused by this work, both belonging to files
this plan touches:

* **`ArtImportTool.cs:67` and `:1006` cite "ART_PIPELINE.md §7.3" for the frame table.** §7 is
  "The canonical reference"; the frame table is **§8, "Standard frame counts"**. Owner of the
  claim: `Assets/Editor/ArtImportTool.cs`. Fix it in the Phase 3 commit that edits the same table.
* **The frame table and the importer disagree about `walk`.** `ART_PIPELINE.md` §8 line 338 says
  6 frames; `ArtImportTool.cs:78` says `Frames = 4`. The comment above the dictionary claims the
  two "cannot drift apart" — they have. Out of scope to fix here, but it must not be copied: when
  adding a `roll` row, put the same numbers in both files and flag the `walk` row to the owner.
  Deciding which is authoritative is the owner's call.

***

## 3. Phase 1 — Dodge/roll, and the "did the hit land" contract

### Feel targets

All six are **Inspector fields on `CombatController`**, not `EKVibe` constants — `MeleeHitDelay`
and `MeleeRecovery` (CombatController.cs:41–45) are the established home for combat timing, and
these need tuning without a recompile.

| Knob | Field | Value | Why |
|---|---|---|---|
| Stamina cost | `RollStaminaCost` | **14** | At 7/s regen that is exactly 2.0 s to repay. The 1.0 s cooldown governs the second roll, the pool governs the third (3 rolls from a full ~50 bar), and there is still headroom for a stamina ability. At 25 the cooldown was dead weight |
| Roll duration | `RollDuration` | 0.40 s | |
| Roll distance | `RollDistance` | 2.4 u | ≈6 u/s against a 5 u/s walk |
| i-frame start | `RollIFrameStart` | 0.05 s | A hair of startup, so a panic-tap is not free |
| i-frame length | `RollIFrameDuration` | 0.25 s | EK-ish rather than souls-ish. §13.3 |
| Cooldown | `RollCooldown` | 1.0 s from roll **start** | |

### `Health.cs` — the return value, and one cached lookup

`Health.TakeDamage` becomes `bool`: **true if the hit landed**, false if it was refused. All four
overloads return it, the three thin ones by `return TakeDamage(...)`.

```csharp
/// <returns>
/// True if the hit landed. False means it was refused — the target was already dead, or was in
/// i-frames — and the caller must not apply knockback, on-hit effects or attribution.
/// </returns>
public bool TakeDamage(int damage, string attackerName, string targetLabel, GameObject attacker)
{
    if (IsDead) return false;

    // Before LastAttacker and before armour: a dodged hit did not happen, so it must not set
    // attribution and must not be logged. Doing it here rather than at each attack site means
    // future damage sources — spells, traps — respect i-frames for free.
    if (_combat != null && _combat.IsInvulnerable)
    {
        FloatingDamageText.Spawn(transform.position, "Dodged!", EKVibe.TextLight);
        return false;
    }
    ...
    return true;
}
```

Cache the player test rather than adding a second lookup. Add `private CombatController _combat;`,
assign it in `Awake`, and rewrite the existing armour gate at Health.cs:63 from
`GetComponent<CombatController>() != null` to `_combat != null`. Verified safe: nothing in the
project calls `AddComponent<CombatController>` at runtime (the only runtime `AddComponent<Health>`
sites are TutorialSequence.cs:147 and MagicTutorial.cs:344, neither of which is the player), so a
null cached on an enemy is permanently correct.

⚠ **Verified safe, and this is the check that makes the change possible at all:**
`grep -rn "m_MethodName: TakeDamage" Assets/` returns nothing, so no `UnityEvent` persistent call
in any scene, prefab or asset binds `TakeDamage`. The four C# call sites are CombatController.cs:545,
:593, :758 and EnemyAI.cs:390, and all four currently ignore the result.

⚠ **Consequence to accept knowingly:** Unity's Inspector only offers *void* methods in a
`UnityEvent` dropdown, so after this change `TakeDamage` disappears from that list. Nothing uses it
today; if the owner later wants a trigger volume to hurt something from the Inspector, the fix is a
one-line `public void ApplyDamage(int d) => TakeDamage(d);`. Not adding it now — dead code.

`CombatController.TakeDamage(int)` (CombatController.cs:589) returns `bool` too, passing through
`_health.TakeDamage(...)` and returning `true` on its healthless fallback branch. Without this the
legacy path at EnemyAI.cs:394–397 has no way to answer the same question.

### `CombatController.cs` — the roll

1. **State.** `_isRolling` and `_isKnockedBack` alongside `_isAttacking`, with the same discipline:
   the reset lives in a `finally` inside the coroutine, never on the happy path. The comment at
   CombatController.cs:462–473 explains why, and it applies here exactly — a stuck `_isRolling`
   permanently freezes the player.
2. **Movement gate.** `FixedUpdate` (CombatController.cs:173) becomes
   `if (!_isAttacking && !_isRolling && !_isKnockedBack && !_isDead) HandleMovement();`
3. **Invulnerability as a timestamp, not a bool:**

   ```csharp
   private float _invulnerableUntil;
   /// <summary>
   /// ⚠ A timestamp, not a flag. The roll and the post-knockback grace both want to grant
   /// i-frames, and two coroutines setting and clearing one bool is how the player ends up
   /// permanently invulnerable when they overlap. Whoever wants the longer window wins by
   /// writing the later time; nothing has to clear anything.
   /// </summary>
   public bool IsInvulnerable => Time.time < _invulnerableUntil;
   ```

   `OnHealthDeath` and `OnDisable` set `_invulnerableUntil = 0f`.
4. **`PerformDodge()`** — public, mirrors `PerformMeleeAttack` (CombatController.cs:438):

   * returns if `_isRolling`, `_isKnockedBack`, `_isDead`, `BlockedByRiding()`, or
     `Time.time < _nextRollTime`;
   * returns if `_isAttacking && !_meleeInRecovery` (see §13.2);
   * if `CurrentStamina < RollStaminaCost`, logs `"Not enough Stamina."` through
     `UIManager.Instance.LogCombat` — the identical string already used at CombatController.cs:693
     — and returns;
   * spends the stamina, sets `_nextRollTime = Time.time + RollCooldown`;
   * direction = current move input via `GetScreenRelativeMoveDirection(ReadMoveInput())` if any,
     else `_facingDir`. **Rolling backwards out of a fight must be possible**, so the roll does not
     call `SetFacing` on a backwards roll — it moves along the roll direction while keeping the
     sprite facing where it was;
   * **breaks stealth** (§13, decision below): if `StealthController.Instance?.IsCrouched == true`,
     call `StealthController.Instance.ToggleStealth()`. One line, and it reuses the existing
     multiplier release (StealthController.cs:58), sprite untint and button repaint rather than
     duplicating any of them;
   * starts `RollRoutine(dir)`.
5. **`RollRoutine(Vector3 dir)`:**

   ```csharp
   _isRolling = true;
   try
   {
       SetAnimatorTrigger("Roll");
       // Once, at the start — the same reason MeleeHitboxRoutine does it at line 488. Zeroing
       // every step would suspend gravity for the whole 0.40 s and leave the player hovering
       // if they roll off a kerb.
       _rb.velocity = Vector3.zero;

       float elapsed = 0f;
       var wait = new WaitForFixedUpdate();   // per physics step, NOT WaitForSeconds
       while (elapsed < RollDuration)
       {
           // Cooperative cancellation. Death or a knockback landing mid-roll both bail here;
           // the finally still runs, so no flag is ever left set. No StopCoroutine anywhere.
           if (_isDead || _isKnockedBack) yield break;

           float t = elapsed / RollDuration;
           float speed = RollDistance / RollDuration * EaseOut(t);
           // MovePosition, not a capsule cast: this Rigidbody is non-kinematic (verified in
           // c.unity), so MovePosition sweeps and resolves against colliders. This is the same
           // call HandleMovement uses and the reason walking does not clip walls.
           // ⚠ EnemyAI.ApplyKnockback deliberately does NOT do this — see the comment there.
           _rb.MovePosition(_rb.position + dir * (speed * Time.fixedDeltaTime));

           if (elapsed >= RollIFrameStart && elapsed < RollIFrameStart + RollIFrameDuration)
               _invulnerableUntil = Mathf.Max(_invulnerableUntil, Time.time + Time.fixedDeltaTime * 1.5f);

           elapsed += Time.fixedDeltaTime;
           yield return wait;
       }
   }
   finally { _isRolling = false; }
   ```

   The i-frame window is re-armed each step rather than set once, so a roll cut short by death or
   knockback does not leave the player invulnerable past the end of it. The 1.5× margin covers the
   gap to the next physics step.

   ⚠ `PauseManager` sets `Time.timeScale = 0` (PauseManager.cs:36), which stops `FixedUpdate`
   entirely, so a roll in progress freezes at the pause and resumes on unpause. That is the wanted
   behaviour and needs no code; it is noted because it is easy to mistake for a hang.

### Input

* **Desktop:** `Input.GetKeyDown(KeyCode.Space)` in `HandleInput`, inside the same
  `#if UNITY_STANDALONE || UNITY_EDITOR || UNITY_WEBGL` block as `Fire1` (CombatController.cs:258–263),
  with the same `!IsPointerOverUI()` guard.
* **Mobile:** one call in `UIManager.BuildActionButtons`, immediately after the CRO block
  (UIManager.cs:585–589):

  ```csharp
  // DGE — fourth in the bottom row: ATK, USE, CRO, DGE reading right to left. Same 200 px
  // pitch as USE (-224) and CRO (-424), so at the 1920×1080 reference it spans x 1296-1406,
  // well clear of the joystick at 40-260.
  CreateActionButton(panel.transform, "DGE", HUDActionButton.ActionKind.Dodge, 0,
      new Vector2(110f, 110f), new Vector2(-624f, 40f));
  ```

  Plus `UIManager.OnDodgePressed()` mirroring `OnAttackPressed` (UIManager.cs:405–410), and a
  `case ActionKind.Dodge:` in `HUDActionButton.Invoke` (HUDActionButton.cs:76–93).

  ⚠ **No scene edit.** `HUDPanel` already gets a `SafeAreaFitter` at runtime (UIManager.cs:100–105),
  so the new button insets with the rest of the row on a notched device — and is invisible in a
  16:9 Game view, as the rest of the cluster is.

### Art (arrives in Phase 3, wires itself up)

`sheet_char_player_roll.png` — new `roll` action. Until it lands the roll is fully functional but
plays no clip; the `SetAnimatorTrigger` guard means no console spam. Art can never block the
mechanic.

***

## 4. Phase 2 — Enemy knockback of the player

### `EnemyAI.cs`

One new authored field, defaulting to **no knockback**, so every existing prefab is unchanged and
no `.prefab` file needs editing for this phase to be safe:

```csharp
[Header("Knockback")]
[Tooltip("Metres the target is shoved when this enemy's hit lands. 0 = no knockback.")]
public float KnockbackDistance = 0f;
```

In `AttackRoutine` (EnemyAI.cs:386–397), both damage branches gate on the new return value:

```csharp
Health playerHp = _target.GetComponentInParent<Health>();
if (playerHp != null)
{
    if (!playerHp.IsDead && playerHp.TakeDamage(Damage, foe, "you", gameObject))
        TryKnockback(toTarget);
}
else
{
    var combat = _target.GetComponent<CombatController>();
    if (combat != null && combat.TakeDamage(Damage))
        TryKnockback(toTarget);
}
```

```csharp
// Gated on the hit LANDING. Health.TakeDamage returns false when the player is in i-frames,
// which is the whole point of the return value: without it a dodged hit still shoves them.
private void TryKnockback(Vector3 toTarget)
{
    if (KnockbackDistance <= 0f || toTarget.sqrMagnitude <= 0.001f) return;
    var cc = _target.GetComponentInParent<CombatController>();
    if (cc != null) cc.ApplyKnockback(toTarget.normalized, KnockbackDistance);
}
```

### `CombatController.ApplyKnockback(Vector3 dir, float distance)`

* Returns immediately if `_isDead`.
* Sets `_isKnockedBack = true`, which the movement gate honours **and which `RollRoutine` polls to
  bail out**. Knockback always wins over a roll in progress; `PerformDodge` refuses while
  `_isKnockedBack`. This replaces revision 1's "last one wins, both coroutines stop the other" —
  that needed `StopCoroutine`, whose interaction with `finally` cannot be verified here.
* ~0.22 s slide, fast-out/slow-in, `WaitForFixedUpdate` per step, `_rb.MovePosition` — **not** a
  capsule cast. See §2 item 4; a comment at this site should say so, and point at the opposite
  choice in `EnemyAI.ApplyKnockback`, so the asymmetry does not read as an inconsistency.
* `SetAnimatorTrigger("Knockback")` — a no-op until Phase 3 art. The existing `Hit` trigger from
  `OnHealthDamaged` (CombatController.cs:607) already gives feedback today.
* On **end**: `_invulnerableUntil = Mathf.Max(_invulnerableUntil, Time.time + 0.4f)` so two enemies
  cannot chain-stun the player. Field: `KnockbackRecoveryIFrames = 0.4f`.
* `finally { _isKnockedBack = false; }`.
* Knockback while `_isAttacking` does **not** stop the melee coroutine — it keeps running and
  clears its own flag in its own `finally`. The swing's hitbox has either already fired or will
  fire from a position the player has been shoved out of, which is the correct punish, and nothing
  has to be cancelled to get it.

Which enemies get a value is an Inspector pass — §13.4.

***

## 5. Phase 3 — Sprites + importer wiring

Two new actions, following the frame-table conventions in **`ART_PIPELINE.md` §8** (not §7.3 —
see §2).

### Importer — `Assets/Editor/ArtImportTool.cs`

| Table (line) | Add |
|---|---|
| `ActionToState` (:45) | `"roll" → "Roll"`, `"knockback" → "Knockback"` |
| `ActionToTrigger` (:59) | `"roll" → "Roll"`, `"knockback" → "Knockback"` |
| `ActionContract` (:75) | `roll`: 6 frames, 14 fps, no loop · `knockback`: 3 frames, 12 fps, no loop |
| `ShapeChanges()` (:1344) | add `"roll"` — a tucked figure legitimately changes height and baseline, same as `death`. The width check stays: no roll pose halves a standing figure's width |
| `requiredActions` (:715) | **do not** add either. They are bonus actions, not part of the six-sheet minimum a class needs to become `GameplayReady` |

`knockback` is **not** added to `ShapeChanges`: a stagger is a standing pose and should pass the
full idle-comparison suite.

Also, in the same commit, fix the two stale `§7.3` citations at ArtImportTool.cs:67 and :1006 to
`§8`, and raise the `walk` frame-count disagreement (§2) to the owner rather than silently picking
a side.

### Contract — `ART_PIPELINE.md` §8, and `docs/art/ART_QUEUE.md`

Add `roll` and `knockback` rows to the §8 table with the same numbers as `ActionContract`, and a
new queue band in this order:

1. `sheet_char_player_roll` — 6×1, 512 px cells, 14 fps. The money sheet.
2. `sheet_char_player_knockback` — 3×1, 12 fps. Stagger driven backward, feet trailing.
3. `roll` for the four other class subjects **only once that class's six core sheets are accepted**
   — never ahead of them.
4. `knockback` for hostile subjects that can be knocked back — owner picks the list; start with
   `roadman`, `neek`, `spicehead`.

Until a `knockback` sheet exists for a subject, its `hurt` clip (fired by the damage itself)
carries the feedback — which is why Phase 2 ships without it.

***

## 6. Phase 4 — Player knockback perk

> ⚠ **`PerkEffectType` is serialized by integer index inside every authored `PerkData` asset.
> APPEND ONLY — never insert or reorder.** `ExtraLootRolls = 8` is currently last
> (PerkData.cs:35), so the new member is `MeleeKnockback = 9`. Confirmed by reading the enum.

1. **`PerkData.cs`** — append `MeleeKnockback = 9`. `Magnitude` reads as a **flat metre value**
   (see §13.5), documented in the enum's `<remarks>` alongside the existing "percentage vs whole
   points" note at PerkData.cs:38–41.
2. **`PlayerSession.cs`** — same shape as `ExtraLootRolls` throughout: reset
   `MeleeKnockbackDistance = 0f` with the other cached query values at PlayerSession.cs:250–256,
   add `case PerkEffectType.MeleeKnockback:` to the switch near :309, clamp with
   `Mathf.Max(0f, …)` at :320, and expose `public float MeleeKnockbackDistance { get; private set; }`
   near :347. ⚠ It must be reset in step 6 with the others — a cached value that is added to but
   never reset accumulates on every recompute, and stats are recomputed on **every load**.
3. **`CombatController.MeleeHitboxRoutine`** — at the damage site (CombatController.cs:545), gate
   on the new return value and on the enemy still being alive:

   ```csharp
   if (targetHealth.TakeDamage(damage, "you", foeName, gameObject))
   {
       _bar?.Ping();
       if (session != null && session.MeleeKnockbackDistance > 0f && !targetHealth.IsDead)
           targetHealth.GetComponent<EnemyAI>()?.ApplyKnockback(facing, session.MeleeKnockbackDistance);
   }
   ```

   `!targetHealth.IsDead` matters: `Health.Die` has already disabled the agent and the AI by then
   (Health.cs:115–118), and knocking a corpse would fight the destroy delay.
4. **`EnemyAI.ApplyKnockback(Vector3 dir, float distance)`** — the mirror of the player's, but
   enemies are `NavMeshAgent`-driven, so the mechanism is genuinely different:

   * ⚠ **Do not toggle `agent.enabled`.** Revision 1 proposed it. If the enemy dies mid-slide,
     `Health.Die` sets `ai.enabled = false` (Health.cs:116) — disabling a MonoBehaviour stops its
     coroutines, and whether the `finally` runs is not something this environment can verify. The
     failure mode is a corpse left with a permanently disabled agent. Use instead:

     ```csharp
     if (_agent != null && _agent.isOnNavMesh) { _agent.isStopped = true; _agent.ResetPath(); }
     _agent.updatePosition = false;   // agent stops fighting the transform for the slide
     ... slide ...
     _agent.updatePosition = true;
     _agent.Warp(transform.position); // resync the agent's internal position, then SnapToNavMesh
     ```

     Guard every `isStopped`/`ResetPath` with `_agent.isOnNavMesh`, as `ChaseAndAttack` already
     does at EnemyAI.cs:288 and :308.
   * The slide itself moves `transform.position` through the **capsule-cast wall check in
     `TryCollideMove`** (EnemyAI.cs:324–353). ⚠ **This is the one place the capsule cast is
     essential**, and the comment must say why: an enemy is not moved by a Rigidbody, so a bare
     `transform.position +=` clips straight through geometry. The player's knockback deliberately
     does the opposite. Factor the cast out of `TryCollideMove` into a small
     `TryStep(Vector3 dir, float step)` both can call, rather than copying it.
   * **`Update` must be gated.** EnemyAI.cs:124 early-returns on `_isAttacking`; add
     `_isKnockedBack` to the same condition or `ChaseAndAttack` will repath against the slide every
     frame and fight it.
   * Guard: no knockback while `_selfHealth.IsDead`. A knocked enemy's in-flight `AttackRoutine`
     whiffs naturally, because the range check at EnemyAI.cs:379 re-measures after the windup.
   * `Animator.SetTrigger("Knockback")` — but ⚠ **`EnemyAI` calls `Animator.SetTrigger` directly**
     (EnemyAI.cs:110, :116, :361) with no parameter guard, unlike `CombatController`. Firing an
     undefined trigger logs an error every call. Either add the same guard `CombatController` has
     (CombatController.cs:781–792) or do not fire the trigger until Phase 3 art exists. **Recommend
     adding the guard** — it is four lines and the existing calls benefit from it too.
5. The perk asset (PerkId, Title, Description) is authored by the owner in Unity. `Description` is
   owner prose.

***

## 7. Mapping table — serialized fields and enum indices

**Nothing is renamed and nothing is reordered.** Every entry below is an append, which is the safe
direction. No `[FormerlySerializedAs]` is needed anywhere in this plan.

### `HUDActionButton.ActionKind` (HUDActionButton.cs:19)

Verified against `c.unity` by resolving every `MonoBehaviour` carrying GUID
`331d1dcd64d330946a710cca818a6917`:

| Index | Value | On disk in `c.unity`? | Blast radius if reordered |
|---|---|---|---|
| 0 | `Attack` | Yes — `HUDPanel/ActionCluster/AttackButton` | Retired at runtime, but the stored 0 would become another action |
| 1 | `Ability` | Yes — `Skill0` (idx 0), `Skill1` (idx 1), `Skill2` (idx 2) | Three buttons change meaning |
| 2 | `Inventory` | Yes — `HUDPanel/MapBagShortcut` — **a live, visible button** | The bag button stops opening the bag |
| 3 | `Interact` | Yes — `HUDPanel/InteractButton` — **live, referenced by `UIManager.InteractButtonRoot`** | USE stops working |
| 4 | `Crouch` | **No** — the CRO button is built at runtime (UIManager.cs:585) | None on disk |
| **5** | **`Dodge`** ← append | No — runtime-built, same as CRO | None |

### `PerkEffectType` (PerkData.cs:25)

| Index | Value | Notes |
|---|---|---|
| 0–8 | `MeleeDamagePercent` … `ExtraLootRolls` | Unchanged. `ExtraLootRolls = 8` is the current last value |
| **9** | **`MeleeKnockback`** ← append | **No `PerkData` asset exists yet** (`Resources/Perks` is empty per the CLAUDE.md ledger), so there is currently nothing on disk to orphan — but append anyway, because the first asset authored will freeze these indices forever |

### New serialized fields — all additions, all new names

| File | Field | Default | Where it appears |
|---|---|---|---|
| `CombatController` | `RollStaminaCost`, `RollDuration`, `RollDistance`, `RollIFrameStart`, `RollIFrameDuration`, `RollCooldown`, `KnockbackRecoveryIFrames` | 14, 0.40, 2.4, 0.05, 0.25, 1.0, 0.4 | Player in `c.unity` — appended, so existing serialized values are untouched |
| `EnemyAI` | `KnockbackDistance` | **0** | 11 prefabs + the tutorial bandit; a default of 0 means every one of them behaves exactly as today |

### Save keys

**None touched.** No `ItemID`, `ChunkName`, `EntryID` or `PerkId` value changes. `SaveData` gains
no field. A save made before this work loads unchanged.

***

## 8. File-by-file change list

| File | Change | Why |
|---|---|---|
| `Assets/Scripts/Combat/Health.cs` | `TakeDamage` × 4 return `bool`; cache `_combat` in `Awake` and reuse it at the armour gate (:63); i-frame early-out | The hole in revision 1: without a return value a dodged hit still knocks back |
| `Assets/Scripts/UI/FloatingDamageText.cs` | Add `Spawn(Vector3, string, Color?)`; existing int overload delegates to it | `Spawn(pos, 0)` renders a red "0" |
| `Assets/Scripts/Combat/CombatController.cs` | `_isRolling`, `_isKnockedBack`, `_meleeInRecovery`, `_invulnerableUntil`, `_nextRollTime`; 7 tuning fields; `PerformDodge`, `RollRoutine`, `ApplyKnockback`, `KnockbackRoutine`; `FixedUpdate` gate; `Space` in `HandleInput`; `TakeDamage(int)` returns `bool`; Phase 4 melee-site knockback | The mechanic |
| `Assets/Scripts/UI/HUDActionButton.cs` | Append `Dodge` to `ActionKind`; add the `case` | Mobile input |
| `Assets/Scripts/UI/UIManager.cs` | `OnDodgePressed()`; one `CreateActionButton` call in `BuildActionButtons` | The cluster is runtime-built — no scene edit |
| `Assets/Scripts/Combat/EnemyAI.cs` | `KnockbackDistance`; `TryKnockback`; gate the two damage branches on the return value; `_isKnockedBack` in the `Update` gate; `ApplyKnockback` + `TryStep` extraction; trigger guard | Phases 2 and 4 |
| `Assets/Scripts/Data/PerkData.cs` | Append `MeleeKnockback = 9` + remark | Phase 4 |
| `Assets/Scripts/Flow/PlayerSession.cs` | `MeleeKnockbackDistance` — reset, case, clamp, property | Phase 4 |
| `Assets/Editor/ArtImportTool.cs` | 4 table edits + 2 stale §7.3 citations | Phase 3 |
| `ART_PIPELINE.md` | §8 rows for `roll`, `knockback` | The art agent's contract |
| `docs/art/ART_QUEUE.md` | New band | The queue |
| `CLAUDE.md` §5 | Ledger entries per phase | Nothing here can be verified from this environment |

**No new script files, therefore no new `.meta` files.** If that changes — e.g. the `TryStep`
extraction is put in its own helper — the `.meta` must be committed with it. **No `.asset`,
`.prefab` or `.unity` file is modified by any commit in this plan.**

***

## 9. Commit sequence

Small, single-concern, each coherent alone. Each phase is its own branch, played before the next
starts.

**Phase 1**

1. `Health.TakeDamage returns whether the hit landed` — `Health.cs` only: four overloads to `bool`,
   `_combat` cached, armour gate switched to the cached field. **No behaviour change yet** — no
   caller reads the result. Isolated deliberately, because it is the change with the widest blast
   radius and the easiest to review on its own.
2. `Add a text overload to FloatingDamageText` — `FloatingDamageText.cs` only.
3. `Player dodge roll` — `CombatController.cs`: state, tuning fields, `PerformDodge`, `RollRoutine`,
   `FixedUpdate` gate, `IsInvulnerable`, stealth break, and the i-frame early-out in `Health.cs`
   that consumes it. Space bar only — no HUD yet, so the mechanic can be judged before the UI.
4. `Dodge button on the HUD` — `HUDActionButton.cs` enum + case, `UIManager.cs` handler + build
   call. Three files, one concern.
5. `Ledger: dodge is unverified` — `CLAUDE.md` §5.

**Phase 2**

6. `Player knockback` — `CombatController.ApplyKnockback` + `KnockbackRoutine` + the gate.
7. `Enemies can knock the player back` — `EnemyAI.KnockbackDistance`, `TryKnockback`, both damage
   branches gated on the return value.
8. `Ledger: knockback is unverified`.

**Phase 3**

9. `Importer: roll and knockback actions` — `ArtImportTool.cs`, including the §7.3 → §8 fix.
10. `Contract and queue: roll and knockback` — `ART_PIPELINE.md`, `docs/art/ART_QUEUE.md`.

**Phase 4**

11. `Append MeleeKnockback perk effect` — `PerkData.cs` + `PlayerSession.cs`. The enum append and
    its only reader, together, so no commit exists where the value is declared but unhandled.
12. `Enemies can be knocked back` — `EnemyAI.ApplyKnockback`, `TryStep` extraction, `Update` gate,
    trigger guard.
13. `Melee hits apply the knockback perk` — `CombatController.MeleeHitboxRoutine`.
14. `Ledger: the knockback perk is unverified`.

***

## 10. Structural risk

Ranked by how quietly it fails.

1. ⚠ **`Health.TakeDamage`'s signature change is the highest-blast-radius edit in this plan.** It is
   safe *only* because no `UnityEvent` persistent call binds it — re-run
   `grep -rn "m_MethodName: TakeDamage" Assets/` immediately before the commit and abort if it
   returns anything. A persistent call bound to a method whose signature changed does not throw; it
   silently stops firing.
2. ⚠ **Two systems granting i-frames.** Handled by the timestamp, not a bool. If an implementer
   "simplifies" it back to `IsInvulnerable { get; private set; }`, a knockback landing during a
   roll leaves the player permanently invulnerable and nothing logs it.
3. ⚠ **A coroutine flag that never clears freezes the player forever.** Every flag reset lives in a
   `finally`, per the existing comment at CombatController.cs:462–473. `yield break` inside the
   `try` still runs the `finally`; `StopCoroutine` and `SetActive(false)` may not, which is why
   neither appears in this plan.
4. ⚠ **`agent.enabled` on a knocked-back enemy fights `Health.Die`.** Revision 1's approach.
   Superseded by `updatePosition` + `Warp` (§6.4).
5. ⚠ **Nothing may be suspended with `SetActive(false)`** — no chunk root, no vehicle root, and
   nothing in this plan asks for it. The player's Rigidbody stays enabled throughout the roll.
6. **The perk-value reset in `PlayerSession`.** `MeleeKnockbackDistance` must be reset in step 6
   with the others, or it accumulates across loads — the same failure the existing comment at
   PlayerSession.cs:250–251 warns about.
7. **Isometric, 3D, always.** `MovePosition` on X/Z, `Vector3` throughout. No `Physics2D`,
   `Rigidbody2D` or `Vector2` movement — they will not interact with any collider here and nothing
   will throw.
8. **Mobile hot paths.** `RollRoutine` allocates one `WaitForFixedUpdate` per roll, hoisted outside
   the loop. No per-step `new`, no `GetComponent` inside a loop, no `FindObjectOfType` at a damage
   site.

***

## 11. Cross-cutting checklist

* [x] **No save-key changes.** No `ItemID`, `ChunkName`, `EntryID` or `PerkId` value is renamed.
* [x] **Two enums appended, never inserted or reordered:** `HUDActionButton.ActionKind` (`Dodge = 5`)
  and `PerkEffectType` (`MeleeKnockback = 9`). Both carry their own APPEND ONLY warning; keep it.
* [x] **New serialized fields are new names** — no `[FormerlySerializedAs]` needed. `EnemyAI.KnockbackDistance`
  defaults to 0 so no prefab changes behaviour.
* [x] **No new script files**, therefore no new `.meta` — and if that changes, the `.meta` ships
  with the script in the same commit.
* [x] ⚠ **No scene edit.** Revision 1 called for one; the action cluster is built at runtime by
  `UIManager.BuildActionButtons` (UIManager.cs:551). `Assets/c.unity` must be untouched by every
  commit in this plan — check `git status` before each.
* [x] `SetAnimatorTrigger` guards mean controllers without `Roll`/`Knockback` keep working. ⚠ That
  guard exists on `CombatController` only — **`EnemyAI` calls `SetTrigger` unguarded** and needs one
  before Phase 4 fires `"Knockback"`.
* [x] Death mid-roll / mid-knockback: `OnHealthDeath` clears `_isRolling`, `_isKnockedBack` and
  `_invulnerableUntil`, **and** `RollRoutine`/`KnockbackRoutine` check `_isDead` each step and bail —
  clearing the flag alone does not stop a running coroutine, and a corpse would keep sliding.
* [x] Pause: `PauseManager` zeroes `timeScale`, so `FixedUpdate` stops and both routines freeze and
  resume. Input is already gated at CombatController.cs:158.
* [x] `python Tools/asset_reachability.py --check-dangling` before and after Phase 3.

***

## 12. Verification (honest version)

**There is no C# compiler, no Unity and no test framework in this environment.** Nothing below
proves the code builds.

What can be checked mechanically:

```bash
grep -rn "m_MethodName: TakeDamage" Assets/          # must stay empty — gate on the bool change
git status                                            # Assets/c.unity must NOT appear
python Tools/asset_reachability.py --check-dangling   # after any asset/meta change (Phase 3)
python Tools/art_status.py                            # after queue/importer changes
```

A brace-balance scan catches a truncated edit and says nothing about correctness. **Do not report
it as a compile.**

Everything else needs a human in the editor. Routes, with preconditions:

* **Roll, desktop.** Exit Play mode, wait for the recompile, press Play, hold a direction and press
  **Space**. Check: the player moves ~2.4 m, the stamina bar in the top-left cluster drops by 14,
  and a second Space within 1 s does nothing.
* **Roll, mobile.** Same session — the **DGE** button is fourth from the right along the bottom row
  (ATK, USE, CRO, DGE). It is built at runtime, so it will not appear in the Hierarchy until Play
  starts; look for `UI/UICanvas/HUDPanel/ActionButtons/DGE`. ⚠ If it overlaps the joystick, that is
  a layout call, not a bug — it is at x −624 on a 1920 reference.
* **i-frames.** Stand in a `Police_PCSO`'s attack range (the only `EnemyAI` currently in `c.unity`)
  and roll through the swing. Check a white **"Dodged!"** appears over the player, no red number
  does, and health does not move.
* **Stealth break.** Press **C** to crouch, then roll. Check the toast reads "Out of stealth.", the
  CRO button pops back out, and walk speed returns to normal.
* **Knockback (Phase 2).** ⚠ **No enemy prefab is placed in any chunk or in `c.unity`** — the
  CLAUDE.md ledger is explicit about this — so knockback cannot be tested without first stamping
  one. Route: `Tools → World Palette`, stamp `Enemy_OG`, then in the Hierarchy select it,
  Inspector → Enemy AI → Knockback → **Knockback Distance = 2**. ⚠ **Exit Play mode before
  setting it** — Inspector changes made during Play are discarded.
* **Dodging a knockback hit.** Same enemy: roll into its swing. Check the player is *not* shoved.
  This is the single most important check in the plan — it is the defect revision 1 shipped with.
* **Hovering.** Roll off a kerb or a step. Check the player falls normally. If they hover, the
  velocity zeroing has been put inside the loop.
* **Perk (Phase 4).** Needs a `PerkData` asset the owner authors: Project → Create →
  `GBH England/Data/Perk`, put it in a `Resources/Perks` folder, one effect of type
  `MeleeKnockback`, Magnitude 2. Then spend a point and hit something.

**What cannot be proved without a human, and should not be claimed:** that any of it compiles;
whether 0.40 s feels right; whether the i-frame window lines up with an animation that does not
exist yet; whether a knockback slide stops at a wall; whether the DGE button is reachable with a
thumb on a real device (Window → General → Device Simulator, landscape).

Add a ledger entry to `CLAUDE.md` §5 at the end of each phase, and delete it when confirmed rather
than hedging it.

***

## 13. Open questions — recommendations, but the owner's call

**Decisions recorded, 2026-08-09:** 1 — dedicated button (implemented, Phase 1). 2 — **flat "no"**:
`_meleeInRecovery` was dropped, `PerformDodge` gates on `_isAttacking` alone. 3 — shipped as
recommended (0.05/0.25); both are Inspector fields now, so this remains a slider question. 4 —
**`Enemy_OG` and `Enemy_Tainted` at 2 m, police at 0**, folded into one Inspector session with the
`Level: 3` and `IsPolice` prefab passes (still owed, in the editor). 5 — flat distance
(implemented, Phase 4). The original text below is kept as the reasoning behind each.

1. **Dodge input on mobile.** *Recommend a dedicated button.* It costs one `CreateActionButton`
   call, it is discoverable, and it cannot misfire. Double-tapping the joystick means adding
   tap-timing state to `VirtualJoystick`, and every mis-detected double-tap spends stamina the
   player did not mean to spend. **Assumed above.**

2. **Should rolling cancel a melee swing?** *Recommend: yes during `MeleeRecovery`, no during
   `MeleeHitDelay`.* Committing to the windup is the cost of swinging; being locked for the 0.35 s
   recovery is what makes melee feel unresponsive. ⚠ **This is more work than revision 1's flat
   "no"** — `_isAttacking` currently covers both halves of the swing (set at CombatController.cs:473,
   cleared at :553), so it needs a second flag, `_meleeInRecovery`, set immediately before the
   recovery `yield` at :549 and cleared in the same `finally`. `PerformDodge` then reads
   `if (_isAttacking && !_meleeInRecovery) return;`.
   **The melee coroutine is not stopped** — it runs out its recovery in the background and clears
   its own flag; `_isRolling` is what gates movement and further attacks meanwhile. That avoids
   `StopCoroutine` entirely. If the owner prefers the simpler flat "no", drop `_meleeInRecovery` and
   gate on `_isAttacking` alone; everything else in the plan is unaffected.

3. **i-frame generosity.** *Recommend 0.25 s of 0.40 s, starting 0.05 s in* — EK-ish rather than
   souls-ish, and a hair of startup so a panic-tap is not free. Both numbers are Inspector fields,
   so this is a slider question, not a code question, once Phase 1 lands.

4. **Which enemies knock back.** *Recommend the big bodies only: `Enemy_OG` and `Enemy_Tainted`,
   at 1.5–2 m.* Not police — being shoved by a PCSO undercuts the arrest fantasy, and police are
   the enemies the player is most often surrounded by. Neek/Roadman/Spicehead stay at 0 so a normal
   scrap stays readable.
   **Combine this with a pass already owed:** eleven prefabs store a cosmetic `Level: 3` on disk
   (CLAUDE.md §5) — the six in `Assets/Prefabs/Enemies/` and the five `Police_*` in
   `Assets/Prefabs/ModernBritain/`. The same five `Police_*` prefabs also need `IsPolice` ticked,
   which is a live defect, not a verification. One Inspector session fixes all three.
   ⚠ Edit those prefabs **in place** (open the prefab, change the field, Ctrl+S). Never by deleting
   and re-saving, and **never** by re-running `ModernBritainSetup`.

5. **Perk shape.** *Recommend always-on distance, not a percentage chance.* `PerkEffect` has a
   single `Magnitude` field (PerkData.cs:42–47) shared by every effect type; a chance-based perk
   needs a second number, and adding one to the class would put an unused field on every perk asset
   ever authored, forever. A flat "your hits shove them 2 m" also reads better on a character sheet
   than a probability.
