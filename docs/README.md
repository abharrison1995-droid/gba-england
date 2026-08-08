# Documentation index

**Read this file to find the one or two documents your task needs. Never read all of `docs/`.**

`CLAUDE.md` and `AGENTS.md` are bootloaders — project identity, the safety rules that must never
be missed, and this routing table. Everything else lives here and is loaded on demand.

This index carries **no status and no "what's next"** on purpose. It is the file every session
reads, so anything perishable in it would rot faster than anywhere else. Current work lives in
`docs/plans/`, where a stale plan at least looks like a plan.

---

## Routing table

| If your task touches… | Read |
|---|---|
| Chunks, transitions, edges, loading or unloading a chunk, building interiors | [reference/CHUNK_WORLD.md](reference/CHUNK_WORLD.md) |
| The save file, save keys, renaming a serialized field, enums, `.meta`/GUIDs | [reference/SAVE_AND_SERIALIZATION.md](reference/SAVE_AND_SERIALIZATION.md) |
| Wanted level, police, stealth, pickpocketing, pubs, arrest, mounts, vehicles, movement speed | [reference/CONSEQUENCES_AND_MOUNTS.md](reference/CONSEQUENCES_AND_MOUNTS.md) |
| Placing content, the World Palette, `PlacementPreset`, building an NPC or an enemy prefab | [reference/WORLD_AUTHORING_AND_NPCS.md](reference/WORLD_AUTHORING_AND_NPCS.md) |
| Quests, quest conditions, dialogue graphs, dialogue authoring or validation | [reference/QUESTS_AND_DIALOGUE.md](reference/QUESTS_AND_DIALOGUE.md) |
| The Unity-side art importer, sprite sizing, animator controllers, `WorldActorVisual` | [reference/ART_IMPORTER.md](reference/ART_IMPORTER.md) |
| Git hygiene, asset pruning, `.gitattributes`, reference integrity | [reference/REPO_HYGIENE.md](reference/REPO_HYGIENE.md) |

## Art

| Document | What it owns |
|---|---|
| [`ART_PIPELINE.md`](../ART_PIPELINE.md) (repo root) | The **contract** with the art agent: resolution, chroma key, sheet layout, sidecar JSON, naming. Stable. |
| [art/ART_QUEUE.md](art/ART_QUEUE.md) | The **only** live record of what art is delivered, outstanding or cancelled. |
| [art/SHEET_WORKFLOW.md](art/SHEET_WORKFLOW.md) | The single-frame generation and local tiling workflow, and the failures that produced it. |

The art status matrix is **derived, not maintained by hand**:

```bash
python Tools/art_status.py
```

## Plans — active

| Document | State |
|---|---|
| [plans/STAGE_RF_PLAN_REVISED.md](plans/STAGE_RF_PLAN_REVISED.md) | Stage F, the inventory and loot overhaul. Not implemented. |
| [plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md](plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md) | Design record for chunk suspend/resume. Not implemented. |
| [plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md](plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md) | XP, player level and enemy levels. **Landed on `main`**; unseen by a compiler or the editor. Its §9.3 is the owner's check list. |
| [plans/PROGRESSION_PHASE3_IMPLEMENTATION.md](plans/PROGRESSION_PHASE3_IMPLEMENTATION.md) | Player gains: level growth, proportional armour, perks and the perk window. Written on `progression-perks`; unseen by a compiler or the editor. Its §10.3 is the owner's check list, and §10.3 check 7 is how the first perk asset gets authored. |
| [plans/PROGRESSION_SYSTEM.md](plans/PROGRESSION_SYSTEM.md) | Parent design for the whole levelling system. Phase 4 (loot tiers) not implemented. |
| [plans/LEVELS_IN_WORLD_AND_HUD.md](plans/LEVELS_IN_WORLD_AND_HUD.md) | Authorable enemy levels at placement time, combat-gated nameplates, a bigger HUD cluster. Implemented on `levels-in-world-and-hud`; unseen by a compiler or the editor. Its §10.3 is the owner's check list. |

## Archive — history only

`docs/archive/` holds superseded briefs and dated snapshots. **Nothing in a routine task should
read from it**, and no live document should link into it. It is kept so that a decision can be
traced, not so that it can be followed.

---

## Maintenance contract

- **Each operational fact has one canonical owner.** A subsystem change updates that one
  reference, not four files. Critical invariants may be *repeated* in a bootloader as a short
  guardrail, because a reference is not guaranteed to be loaded.
- **Replace a stale statement — never strike it through and correct it beside itself.** The old
  wording is what a reader carries away. Git holds the history.
- **An accepted art import updates `ART_QUEUE.md` in the same piece of work**, not when the art is
  first requested.
- **Anything dated is archived, not nursed.** A snapshot that claims to be current and is not is
  worse than one that is honestly six months old.
- **Every reference carries a verification header.** If you change what a reference describes,
  update its header — including downgrading the scope when you could not verify.
