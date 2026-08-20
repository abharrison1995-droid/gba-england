# Quest pipeline — modularity plan

```
Last updated:          2026-08-12 (Phase 0 + Phase 1 written); superseded by real use 2026-08-17
Verification scope:    Phase 0 (multi-quest watcher, quest focus, quest-gated dialogue choices,
                       landmine fallbacks) and Phase 1 (text importer, content validator, .quest
                       format, template) are merged and have since been exercised for real: a full
                       `Import Quests` run on 2026-08-17 wrote all ten `QuestDefinition`s and
                       rebuilt every generated `DialogueData` — see CLAUDE.md §5 for specifics. The
                       quest spine (QuestDefinition → QuestDatabase → QuestConditionWatcher →
                       QuestManager, dialogue grant/complete) is unchanged in shape and is described
                       in docs/reference/QUESTS_AND_DIALOGUE.md. This plan is the roadmap for making
                       the pipeline authorable end-to-end and modular per quest.
```

> **Owner verification gate (2026-08-12):** Phases 0–1 must be compiled and smoke-tested in the
> editor — `Tools → Content → Import Quests` and `Validate Quests` run clean, and one hand-authored
> quest is taken through grant → stage → hand-in → reward — BEFORE Phase 2 begins. Note the overlap
> with the companion pipeline: companion phase **C5 (save wiring)** appends to the same
> `SaveGameManager` / `GameFlowController` files that Phase 0 modified, so land and verify Phase 0
> first, then do C5. Do not stack two unverified save-format changes on the same files.

## Goal

A quest is authored end-to-end as one coherent unit — definition, stages, world targets, and the
dialogue that grants/completes it — and a later quest can be bolted onto the same NPC without
surgery on what already exists. Four archetypes:

1. **Retrieval** — find an item by clearing a place of enemies, killing a specific enemy, or
   stealing it from a person or place.
2. **Escort** — get someone somewhere, fending off attacks on the way.
3. **Gang war** — defend a point of interest from waves of gang members, with your own side present.
4. **Conversation** — simply talk to an NPC.

## Authoring spine: plain-text quest files + importer

The most encompassing and flexible surface is a **plain-text quest format** imported by a Tools
menu item, not a Quest Builder window. Reasons:

- Any quest shape and any dialogue graph, diffable in git, writable without Unity open — the owner
  and agents can author and revise quests together in the workspace.
- `DialogueValidator.Validate` is already public and UI-free *for exactly this* — a plain-text
  importer is meant to call it and refuse a bad script.
- The docs already anticipate this (`-> shop`, not `-> 7`).

**The text file is the source of truth for the quests it defines.** The importer regenerates those
assets wholesale, so Unity-side hand edits to those files get overwritten. Writing lives in the
text file, never only in the asset.

**Prose rule (from CLAUDE.md):** quest and dialogue prose is the owner's own work. The agent
scaffolds structure, ids, stages, conditions, node graphs, gating, rewards and spawn keys, with
clearly marked prose slots. The owner writes the words.

Text files live in a new repo-root `quests/` folder — git-tracked, diffable, outside `Assets/` so
nothing half-written ships in a build. Re-imports are idempotent: edit the file, re-run, assets
regenerate.

Sketch of the format (prose placeholders are the owner's):

```
QUEST find_the_ledger
  title: ...   giver: ...   location: ...
  stage 1: KILL estate_lads x3        objective: [...]
  stage 2: COLLECT item_ledger x1     objective: [...]  when-met: [...]
  reward: £40, 60xp

DIALOGUE mosley
  [start]
  Mosley: [...]
    * "..." (if quest find_the_ledger not-started) -> offer
    * "..." (if quest find_the_ledger active)     -> chase
    * "..."                                        -> end
  [offer]
  Mosley: [...]
    * "..." (grant find_the_ledger) -> end
```

Unity keeps what it is good at: placing actors/markers into chunk prefabs via the World Palette.
A new **Quest content validator** is the contract between the two — it statically checks that every
key a quest references actually exists somewhere, that Collect stages have a dialogue hand-in, that
grant objectives are not blank, etc. Every documented landmine becomes a console error.

## Design decisions (owner-confirmed)

- **Multi-active quests with a player-chosen focus.** Any number of quests can be active (within
  reason, only if available). The top-right HUD tracker shows the **focused** quest; the journal
  holds the rest. Focus is switched **journal-only** — no HUD cycle button.
- **New grants auto-focus** — the tracker switches to the newly granted quest immediately.
- **Gang war failure = reload, not persistent failure.** A dialogue choice gains an **autosave
  flag** (appended, safe). The gang war trigger choice carries it — picking it writes the
  checkpoint (same single `savegame.json`, consistent with existing travel autosaves) at the moment
  the quest grants. On failure (point destroyed), a "Mission failed" overlay offers one action:
  reload last save → back at the giver's conversation, war un-started, stage 0. Spawned waves die
  with the chunk teardown on reload, so cleanup is free. Player death keeps the existing death
  screen; this reuses the same reload path. No persistent Failed state is needed.
- **Escort lands last**, after the companion system (Alex sheets already staged in `art_incoming/`
  and passed precheck). Escort reuses the Phase 3 spawner + fail/reload loop + arrival check.
- **Gang war v1 is rudimentary**: waves as Kill stages, a defensible point of interest with
  `Health`, minimal `EnemyAI` extension (attack the point when the player is not in sight — no
  faction-vs-faction combat yet), allies decorative. Polish later.

## Phases

### Phase 0 — quest foundations (own commit, plan → implement → review)  — WRITTEN, unverified

The riskiest runtime change in the programme; it wants a clean diff and its own review before
anything is built on it.

- **Watcher binds all active quests**, not just the first. Per-quest binding state, same
  re-entrancy (all mutation in `Update`) and full-teardown discipline.
- **`FocusedQuestId` appended to the save.** Tracker reads it; journal gets a Focus button per
  quest; new grants auto-focus.
- **Landmine fixes**: `Stages[0].Objective` fallback when `GrantQuestObjective` is blank;
  definition Title/Giver/Location fallbacks; TalkTo-final-stage warning.
- **Quest-gated dialogue choices** (appended enum: show if quest NotStarted / Active / Complete),
  with `CanEscapeFrom` and validator updates.

Status: written and brace-balanced (`python Tools/check_quest_phase0.py` → BALANCE OK); NOT compiled
or run in the editor. Awaits the owner verification gate above, then its own commit.

### Phase 1 — text pipeline  — WRITTEN, unverified

**Implemented (written, brace-balanced, NOT compiled or run in Unity):**

- `docs/reference/QUEST_TEXT_FORMAT.md` — the `.quest` format spec.
- `quests/_template.quest` — the scaffold (prose slots left `[TODO: ...]` for the owner).
- `Assets/Editor/QuestTextImporter.cs` — `Tools → Content → Import Quests`: parses `quests/*.quest`,
  writes the `QuestDefinition` to `Resources/Quests/<id>.asset` and each `DIALOGUE` block to
  `Assets/Data/Dialogue/Generated/Dialogue_<npcId>.asset`, wires the preset `Conversation`, and
  refuses on parse or `DialogueValidator` errors (update-in-place, GUIDs preserved).
- `Assets/Editor/QuestContentValidator.cs` — `Tools → Content → Validate Quests`: cross-checks
  quest id ↔ `GRANT:`, non-blank objectives, `Collect`-is-last + has a `COMPLETE:` route.

Remaining from the original Phase 1 intent, deferred: the QuestKey-to-placed-actor/marker static
scan (needs loading chunk prefabs at editor time) and a real template quest proving the full
grant → stage → hand-in → reward loop end to end (needs content + Unity).

### Phase 2 — retrieval archetype  — gated (see top)

Guaranteed quest item in a mark's pockets (bands are random today); template quest covering
clear-out / specific-kill / steal-from-person / steal-from-place, all data-only.

### Phase 3 — gang war v1

Spawn markers in chunk prefabs (they may hold prefab references; `QuestDefinition` may not); waves
as Kill stages; point of interest with `Health`; minimal `EnemyAI` extension; autosave-choice flag;
mission-failed overlay → reload; allies decorative.

### Phase 4 — companion system (Alex)

Per the existing `docs/plans/ALEX_COMPANION_PLAN.md` and `docs/plans/COMPANION_PIPELINE_PLAN.md`.
Sheets already staged. C0–C3 runtime is written (unverified); C4/C6 partial; C5/C7/Alex outstanding.

### Phase 5 — escort archetype

Follower + Phase 3 spawner for ambushes + same fail/reload loop + arrival check.

## Art asks

Nothing for Phases 0–3 beyond optionally a point-of-interest prop sprite (placeholder-able). Alex
is covered. The six existing enemy prefabs (Roadman/Neek/OG) cast the gang.

## Verification

There is no compiler or Unity in the agent environment. Every phase lands as "written, reviewed,
unverified" until the owner opens the editor. Each phase ships with an explicit in-editor check
list, per the repo's convention. `python Tools/asset_reachability.py --check-dangling` runs before
and after anything that deletes, moves or renames assets.