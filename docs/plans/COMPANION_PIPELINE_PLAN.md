# Companion pipeline — plan

```
Last updated:          2026-08-12 (C5 save wiring + CompanionPresetTool landed)
Verification scope:    C0–C3 WRITTEN; C4 and C6 PARTIAL; C5 WRITTEN this pass; C7 NOT STARTED.
                       The Alex instance is authored by a new editor tool (CompanionPresetTool),
                       created but NOT yet run in the editor.
                       Compile passes so far (owner, in-editor): the first pass surfaced three
                       issues, all FIXED in the tree — CompanionHUDUI missing `using
                       ExiledAlvaston.Vibe;` (CS0103), a GameObject→Image assignment (CS0029), and
                       two dead CompanionAI fields (CS0414). C5 (below) compiles clean per the
                       owner's latest pass; its runtime is NOT yet exercised.
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

**Decision (2026-08-12):** the World Palette append is **deferred**. Rather than touch the palette's
serialization surface (or blind-edit the committed `Home_London_Prefab`), `CompanionPresetTool`
authors a **self-contained `CompanionHome_Alex.prefab`** the owner drags into Home_London. The
`PlacementCategory.Companion = 7` append and the `PlacementPreset` definition field can follow once
the runtime is verified in the editor.

### C5 — Save / restore  — WRITTEN, unverified

Appended to `SaveData` (in order, after `FocusedQuestId`), matching the proven `FocusedQuestId`
pattern:

- `ActiveCompanionId` (string; empty/null = no active contract).
- `CompanionHealth` (int; 0/negative reads as "no companion" on restore).

On save, `SaveGameManager.Save` writes both from `CompanionManager` (`CurrentCompanionId` /
`CurrentFollowerHealth()`). On load, `GameFlowController.ContinueFromSave` calls
`CompanionManager.RestoreContract(id, health)` right after `RestoreFocusedQuest` — **without
charging** — and clamps `Health.CurrentHealth = clamp(saved, 1, def.MaxHealth)`. Knockout/dismissal
clears the manager's contract state, so the next autosave writes empty. Old saves read null/0 -> no
companion; no migration. The follower spawns beside the player and rejoins across `LoadWorld` via the
manager's chunk poll.

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

## Alex instance  — tool authored, unrun in the editor

`Tools → Content → Companions → Build Alex Companion` (`Assets/Editor/CompanionPresetTool.cs`)
authors three assets, all new-file-only / update-in-place (never delete-and-recreate):

- `Assets/Data/Presets/Preset_Alex.asset` — the `ArtSubject = "alex"` preset. None existed, so the
  importer never wired Alex's art into any preset; the tool creates and wires it (controller + idle
  frame zero + cast height) as the shared recipe for both the home presence and the runtime follower.
- `Assets/Resources/Companions/Companion_alex.asset` — `Id = "alex"`, `ArtSubject = "alex"`, price
  £25 (provisional), starter stat block (120 HP, 8 dmg), heal/dodge tuning per the Alex plan (20 s
  heal cooldown, 9 s dodge cooldown, 0.4 player-priority fraction). Left untouched on re-run, so
  Inspector tuning survives.
- `Assets/Prefabs/ModernBritain/Companions/CompanionHome_Alex.prefab` — the hireable home presence,
  `NpcFactory.Build` output stripped to hire-only plus a `CompanionHomePresence`. **The owner drags
  this into `Home_London`** where Alex should wait (the tool deliberately does not edit the chunk
  prefab). `HomeAnchorId` is left blank until the anchor's `QuestKey` is fixed.

The runtime follower is spawned by `CompanionManager` from the same `alex` preset, not by this tool.
⚠ If the follower spawns as a **capsule** in play, the `alex` preset is not reachable via
`PlacementPresetLibrary` at runtime — re-run the library/preset wiring so `ResolveCompanionPreset`
finds it (the home-presence prefab carries its art directly, so it is unaffected).

## Verification

- First compile pass cleanup is DONE in the tree (see header). C5 compiles clean; runtime unexercised.
- `python Tools/check_quest_phase0.py`-style brace scan extended to the new files (or fold into a
  generalized checker).
- `python Tools/asset_reachability.py --check-dangling` before/after (C5 adds no asset moves; the
  tool's outputs are new files — run it as a regression once they exist).
- `python Tools/art_status.py` — Alex sheets already done.
- **In-editor checklist** (only the owner can do this): run `Build Alex Companion`; drag
  `CompanionHome_Alex` into Home_London; hire with insufficient funds (refused, no state change) and
  at exactly £25; Alex follows, fights only your aggroed hostiles, heals, dodges infrequently;
  knockout → KO pose → rehire; dismissal; **save → Continue → Alex returns without re-charging**;
  every transition type (edge, portal, arrest, death/reload); companion HUD shows name + health.

Nothing here compiles in the agent environment; none of it is "done" until opened in the editor.