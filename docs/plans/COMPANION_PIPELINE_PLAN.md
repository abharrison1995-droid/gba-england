# Companion pipeline — plan

```
Last updated:          2026-08-12 (after the first agent write-up + first compile pass)
Verification scope:    C0–C3 are WRITTEN; C4 and C6 are PARTIAL; C5, C7 and the Alex instance are
                       NOT STARTED. First compile pass surfaced three issues, all FIXED in the tree:
                       - CompanionHUDUI was missing `using ExiledAlvaston.Vibe;` (EKVibe.HealthBar
                         unresolved, CS0103) — fixed.
                       - CompanionHUDUI assigned CreateImage's GameObject to the `Image _fill` field
                         (CS0029) — fixed (`.GetComponent<Image>()`, then `_fill.rectTransform`).
                       - CompanionAI._attackReady / _nextRetargetTime were dead fields (CS0414) —
                         removed.
                       Still NOT run in the editor — runtime behaviour needs the owner in Unity.
                       Alex's eight sheets and controller are already imported (commit 5ec4cde), and
                       docs/plans/ALEX_COMPANION_PLAN.md is the approved Alex-specific design this
                       generalises.
```

## Goal

A data-driven companion system: one **paid follower** (Alex, the first instance) and the machinery
to author more companions and to bolt a companion onto a quest. The same follower, combat, HUD and
transition machinery serves both — a `ContractType.Paid` join comes from `SpendPounds`, a
`ContractType.QuestBound` join would come from quest state. This plan deliberately does not write
quest or dialogue prose (CLAUDE.md — the owner writes the words).

Companions are **placed around the world** via a new World Palette section, and the active follower
survives every chunk transition, portal, arrest, player death/reload, and save/continue.

## Design anchor

`docs/plans/ALEX_COMPANION_PLAN.md` is the approved player-facing design: Alex waits at a configurable
home anchor, `pay £25 -> hired and following -> knocked out or dismissed -> available at home`. One
active companion at a time, no contract timer, knockout is not death, Alex is an unarmed boxer who
heals and occasionally dodges. None of that is re-litigated here — this plan is how it gets built
generically so a second companion and a quest-bound companion cost almost nothing.

## Non-negotiable repo rules this touches

- **Save keys / serialized fields / enums are append-only.** Appended fields to `SaveData`; appended
  enum members only (`ContractType` is brand-new; `PlacementCategory.Companion` appends after
  `SpawnPoint`). Renaming any authored key orphans saves.
- **No `GameObject`/`Sprite`/`Controller` refs on anything in `Resources/`.** A `CompanionDefinition`
  under `Resources/Companions/` is strings + numbers only (the `QuestDefinition` discipline); Alex's
  art/controller is resolved through the `ArtSubject`-carrying `PlacementPreset`, which lives outside
  `Resources/` and may hold the heavy refs.
- **The active companion is a scene-root object, never parented under the chunk root.** Every chunk
  transition destroys that root. Reposition only after the destination/player arrival are valid, by
  polling `ChunkManager.CurrentChunkData/Instance` (the sanctioned seven-path-safe pattern).
- **Never `SetActive(false)` a chunk root or vehicle root.** The home-presence component toggles only
  its own GameObject.
- **Save/serialization work follows architect -> implementer -> reviewer.**

## Phases

### C0 — CompanionDefinition data + CompanionDatabase  — written

A `CompanionDefinition` ScriptableObject (strings/numbers only):

- `Id` — the save key (stable once shipped).
- `DisplayName`, `ArtSubject` (e.g. `"alex"` — resolves the controller/sprite via the preset).
- `HomeChunkName`, `HomeAnchorId` — strings matching `MapChunkData.ChunkName` / a `SceneMarker.Key`
  or `QuestActor.Key` in that chunk. Author once, treat as stable identifiers.
- Stats: `MaxHealth`, `Damage`, `MoveSpeed`, `AttackRange`, `AttackCooldown`, `AttackWindup`.
- `PricePounds` (Paid only), heal tuning (`HealAmount`, `HealCooldown`, `HealThreshold`), `DodgeCooldown`.
- `ContractType` — a new appended enum `{ Paid, QuestBound }`; `QuestBound` join/leave comes from
  quest state (Phase C7).

`CompanionDatabase` mirrors `QuestDatabase`: `Resources.LoadAll<CompanionDefinition>("Companions")`
keyed by `Id`, duplicate-id warning, null miss is "not my business".

### C1 — CompanionManager (contract + spawn lifecycle)  — written

Bootstraps itself like `QuestConditionWatcher` (`RuntimeInitializeOnLoadMethod`). Owns the single
active contract; exposes `BeginContract(id, free)`, `EndContract()`, `CurrentCompanionId`,
`ActiveDefinition`, and the follower instance.

- Polls `ChunkManager.CurrentChunkData/Instance` every frame (reference compare) and, when the active
  companion is missing from a valid chunk + player, **rejoins it beside the player** after arrival.
  Same pattern as `VehicleSpawner`/`QuestConditionWatcher` — safe across the seven instantiation paths.

### C2 — CompanionAI (follower behaviour)  — written

NavMeshAgent follow shaped like `EnemyAI` (including the off-mesh capsule-cast fallback and uniform
0.28 agent radius):

- Follow on the X/Z plane, keep out of the player's body (stopping distance), catch up, **warp when
  stranded beyond a distance threshold**.
- **Fight only hostiles already aggroed on the player.** Needs one appended read-only accessor on
  `EnemyAI` exposing its current target (`AggroTarget`); Alex then attacks those. Never initiates on
  civilians or police.
- Unarmed punch: `Health.TakeDamage` on the hostile, with windup/cooldown from the definition.
- **Heal**: priority badly-injured player (`Health.Heal`), else self; `HealCooldown` gate.
- **Dodge**: roll animation + displacement only on a long `DodgeCooldown` (no i-frames — that's
  `CombatController` machinery, not the AI's to fake).
- Knockout: `Health.DestroyOnDeath = false`, `OnDeath` fires the companion shutdown (see C3).

### C3 — Knockout / dismissal handler  — written

`Health.Die` early-returns before the disable block when `DestroyOnDeath` is false (verified in
`Health.cs`), so the companion handler owns shutdown explicitly: disable agent + colliders + AI,
play the `Death` animation as the KO pose, despawn after the pose, end the contract. No loot, no XP
(`KillXP.AwardFor` must not run for a companion). Dismissal from a HUD/interaction path calls the
same teardown without the KO pose.

### C4 — Hire interaction + home presence  — PARTIAL (home presence written, palette deferred)

- **World Palette**: append `Companion = 7` to `PlacementCategory`. Add an appended `PlacementPreset`
  block: a `CompanionDefinition` reference (presets live outside `Resources/`, so an asset ref is
  fine). Placing stamps the home presence using the preset's `ArtSubject` art (idle sprite +
  controller) with a hire `Interactable`.
- **Hire**: on interact, if no active contract and `SpendPounds(PricePounds)` succeeds (bool, atomic),
  call `BeginContract(id, free:false)`. Refuses without changing state when funds are short. A loaded
  active contract must never re-charge.
- **`CompanionHomePresence`** component: on enable (each chunk instantiation), shows itself when there
  is no active contract, hides itself when one is active. Toggles only its own GameObject.
- The home anchor is **data**: definition's `HomeChunkName`/`HomeAnchorId`. For now a **temporary test
  anchor** is placed in `Home_London` (owner has not fixed the building yet); it is easy to move.

**Decision (2026-08-12):** the home-presence component is written, but the World Palette append is
**deferred**. Author the Alex home presence in `Home_London` with a dedicated editor builder tool
(`CompanionPresetTool`, mirroring `BuildTrafficCarPrefabTool` / `StarterPresetGenerator`) rather than
blocking on the full palette section. The `PlacementCategory.Companion = 7` append and the
`PlacementPreset` definition field can follow once the runtime is verified in the editor. This gets a
testable Alex onto a chunk without first touching the palette's serialization surface.

### C5 — Save / restore  — NOT STARTED

Append to `SaveData` (in order, after `FocusedQuestId`):

- `ActiveCompanionId` (string; empty = no active contract).
- `CompanionHealth` (int).

On save, write from `CompanionManager`. On load (`GameFlowController.ContinueFromSave`), if
`ActiveCompanionId` is non-empty, restore the contract **without charging** and set
`Health.CurrentHealth = clamp(saved, 1, def.MaxHealth)`. Knockout/dismissal clears the fields before
the next autosave. Old saves read null/0 -> no companion; no migration.

`CompanionManager` already exposes `CurrentFollowerHealth()` and `RestoreContract(id, health)` — this
phase only wires the two `SaveData` fields and the `ContinueFromSave` call, following the proven
`FocusedQuestId` append pattern. **Do this after the first in-editor compile pass**, because it
touches the same `SaveGameManager` / `GameFlowController` files that quest Phase 0 modified.

### C6 — Companion HUD  — PARTIAL (written, deviates from the seam — accepted)

Fill the existing unused `UIManager.CompanionHUDTemplate` / `CompanionHUDContainer` seam with name +
health. Code-built Win95 style (like the quest UIs), visible only while a contract is active,
subscribing to the follower `Health.OnTakeDamage`/`OnDeath`.

**Decision (2026-08-12):** the written HUD (`CompanionHUDUI`) does NOT fill the `UIManager` seam — it
self-bootstraps its own screen-space canvas (same pattern as `CompanionManager`'s runtime bootstrap)
and registers on a static `CompanionHUD` seam, so no scene wiring is needed. **This deviation is
accepted** for v1: zero scene edits, and the manager never depends on a HUD existing. The
`UIManager.CompanionHUDTemplate` / `CompanionHUDContainer` fields stay reserved for when the HUD moves
into the scene.

### C7 — Quest-bound hook (API only this pass)  — NOT STARTED

Expose `CompanionManager.BeginContract(id, free:true)` / `EndContract()` as the public API for
escort (Phase 5) and quest dialogue. Optional appended `DialogueChoice` fields
(`HireCompanionId`/`DismissCompanion`) and matching `.quest` directives (`HIRE:`, `DISMISS:`) only
if hire-by-dialogue is wanted now — the gates already exist (`QuestGateType`).

(`BeginContract(id, free)` / `EndContract()` are already public on `CompanionManager`; only the
optional dialogue fields and `.quest` directives remain for this phase.)

## Alex instance  — NOT STARTED

- Definition `Id = "alex"`, `ArtSubject = "alex"`, price £25 (provisional), a reasonable early-game
  starter stat block, heal/dodge tuning per the Alex plan (20 s heal cooldown, 8–10 s dodge cooldown).
- Prefab/preset built in place via editor tooling (never delete-and-recreate a preset — GUID
  discipline) or a new `CompanionPresetTool` following `StarterPresetGenerator` / `GeneratedEnemyPrefabTool`.
- Temporary home anchor in `Home_London`.
- Requires `Assets/Resources/Companions/` to exist (currently it does not) and the `alex` definition
  asset to be authored there; resolves art via the `alex` `PlacementPreset` already imported.

## Verification

- First compile pass cleanup is DONE in the tree (see header). Next in-editor step is behavioural.
- `python Tools/check_quest_phase0.py`-style brace scan extended to the new files (or fold into a
  generalized checker).
- `python Tools/asset_reachability.py --check-dangling` before/after (nothing here deletes/moves
  assets, but run it as a regression).
- `python Tools/art_status.py` — Alex sheets already done.
- **In-editor checklist** (only the owner can do this): insufficient funds, exactly £25, dismissal,
  knockout, rehire, save/continue without re-charge, every transition type (edge, portal, arrest,
  death/reload), healing priority + cooldown, infrequent dodge, hostile targeting, no
  civilian/police initiation, companion HUD, returning to the eventual home anchor.

Nothing here compiles in the agent environment; none of it is "done" until opened in the editor.