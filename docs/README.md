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
| Spells, spell tuning, spellbook persistence, spell VFX or debug spell grants | [reference/SPELLS.md](reference/SPELLS.md) |
| Player melee, the dodge roll, special attacks and the melee sweep helper | [reference/PLAYER_COMBAT.md](reference/PLAYER_COMBAT.md) |
| The Unity-side art importer, sprite sizing, animator controllers, `WorldActorVisual` | [reference/ART_IMPORTER.md](reference/ART_IMPORTER.md) |
| Git hygiene, asset pruning, `.gitattributes`, reference integrity | [reference/REPO_HYGIENE.md](reference/REPO_HYGIENE.md) |
| Confirming whether a landed change has been seen by a compiler or the editor | [reference/VERIFICATION_LEDGER.md](reference/VERIFICATION_LEDGER.md) |
| The `.quest` file format, its directives, authoring a new quest as plain text | [reference/QUEST_TEXT_FORMAT.md](reference/QUEST_TEXT_FORMAT.md) |

## Art

| Document | What it owns |
|---|---|
| [`ART_PIPELINE.md`](../ART_PIPELINE.md) (repo root) | The **contract** with the art agent: resolution, chroma key, sheet layout, sidecar JSON, naming. Stable. |
| [art/ART_QUEUE.md](art/ART_QUEUE.md) | The **only** live record of what art is delivered, outstanding or cancelled. |
| [art/SHEET_WORKFLOW.md](art/SHEET_WORKFLOW.md) | The single-frame generation and local tiling workflow, and the failures that produced it. |
| [`Tools/blender/README.md`](../Tools/blender/README.md) (repo root) | The **3D model** pipeline — procedural Blender scripts, the band 6 delivery route. Sprites are none of its business. |

The art status matrix is **derived, not maintained by hand**:

```bash
python Tools/art_status.py
```

## Plans — active

| Document | State |
|---|---|
| [plans/STAGE_RF_PLAN_REVISED.md](plans/STAGE_RF_PLAN_REVISED.md) | Stage F, the inventory and loot overhaul. F1 (equipment model + save format) landed on `main`; F2–F6 outstanding. |
| [plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md](plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md) | Design record for chunk suspend/resume. Not implemented. |
| [plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md](plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md) | XP, player level and enemy levels. **Landed on `main`**; unseen by a compiler or the editor. Its §9.3 is the owner's check list. |
| [plans/PROGRESSION_PHASE3_IMPLEMENTATION.md](plans/PROGRESSION_PHASE3_IMPLEMENTATION.md) | Player gains: level growth, proportional armour, perks and the perk window. Written on `progression-perks`; unseen by a compiler or the editor. Its §10.3 is the owner's check list, and §10.3 check 7 is how the first perk asset gets authored. |
| [plans/PROGRESSION_SYSTEM.md](plans/PROGRESSION_SYSTEM.md) | Parent design for the whole levelling system. Phase 4 (loot tiers) not implemented. |
| [plans/LEVELS_IN_WORLD_AND_HUD.md](plans/LEVELS_IN_WORLD_AND_HUD.md) | Authorable enemy levels at placement time, combat-gated nameplates, a bigger HUD cluster. Implemented on `levels-in-world-and-hud`; unseen by a compiler or the editor. Its §10.3 is the owner's check list. |
| [plans/MOBILE_PERFORMANCE_PASS.md](plans/MOBILE_PERFORMANCE_PASS.md) | Android/iOS texture compression tool, mobile quality tiers, a persisted graphics settings menu. Landed on `main`; unseen by a compiler or the editor. Its §10.3 is the owner's check list. |
| [plans/SURVIVAL_PRESSURE_RESOURCES.md](plans/SURVIVAL_PRESSURE_RESOURCES.md) | A stamina bar, a dodge roll priced at half the pool, slow stamina regen and the end of automatic mana regen. Phase 1 implemented; unseen by a compiler or the editor. Its §10.3 is the owner's check list; phases 2 and 3 are staged, not approved. |
| [plans/ALEX_COMPANION_PLAN.md](plans/ALEX_COMPANION_PLAN.md) | Approved design for the paid starter companion, reusable paid/quest companion framework, save lifecycle and Alex's eight-sheet art contract. **Implemented** — Alex recruits, follows, fights and can be dismissed (commit `ab2d6c5`, 2026-08-15). Never compiled or run in the editor. |
| [plans/TRAFFIC_AND_CAR_THEFT_PLAN.md](plans/TRAFFIC_AND_CAR_THEFT_PLAN.md) | Ambient traffic and car theft: chunk-owned cars drive authored routes, the player can stop and hotwire one, and drive off — triggering a police response. Code landed; unseen by a compiler or the editor. Its §10.2 is the owner's check list. |
| [plans/TRAFFIC_IMPLEMENTATION_CHEAT_SHEET.md](plans/TRAFFIC_IMPLEMENTATION_CHEAT_SHEET.md) | Operator checklist for switching on the traffic/car-theft code above in the Unity editor — not a design doc. |
| [plans/CONTAINER_SYSTEM_PLAN.md](plans/CONTAINER_SYSTEM_PLAN.md) | 3D world containers (`WorldContainer`/`SpriteContainer`), visit-counted respawn, `Tools → Place → Container Placement`. Implemented and landed on `main`; unseen by a compiler or the editor. Its §6 is the owner's check list. |
| [plans/QUEST_PIPELINE_PLAN.md](plans/QUEST_PIPELINE_PLAN.md) | Plain-text `.quest` authoring + importer, multi-quest watcher, quest focus, quest-gated dialogue choices. Phases 0–1 written; unseen by a compiler or the editor. Its verification gate is the owner's check list before Phase 2. |
| [plans/COMPANION_PIPELINE_PLAN.md](plans/COMPANION_PIPELINE_PLAN.md) | Data-driven paid/quest companions (Alex first): definition, follower AI, contract lifecycle, knockout, HUD. C0–C3 and C5 written, C4/C6 partial, C7 (quest-bound companions) not started. **Alex, the first instance, is implemented** — recruit, follow, fight, dismiss (commit `ab2d6c5`, 2026-08-15). Never compiled or run in the editor. Its verification section is the owner's check list. |
| [plans/ROYAL_FIGHT_ARENA_PLAN.md](plans/ROYAL_FIGHT_ARENA_PLAN.md) | **Castle Fight Arena**, hosted by Prince Mandrew outside the London castle: dialogue sends the player directly into a transient solo bout, then victory/defeat/forfeit returns them outside. Includes match-only rewards, persistent ladder wins, a dirty tiled-stone prefab contract, and a later `.arena` pipeline. Implemented under `FightPitController`/`FightPitConfig` (10 config-driven rounds); never compiled or run in the editor. |
| [plans/PLAYER_SPECIAL_ATTACKS_PLAN.md](plans/PLAYER_SPECIAL_ATTACKS_PLAN.md) | Spin and dash special attacks on the right HUD row: authored as `AbilityData` but executed as melee, never through `SpellRuntime`, and deliberately kept out of `Resources/` so they never become save keys. Adds a shared melee sweep helper. **Planned only — no code written.** Its §11 is the owner's check list. |

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
