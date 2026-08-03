# State of play — 2026-08-03

> **What this is.** An honest snapshot of where the game actually is, written to be argued with.
> It is not a plan and it does not decide anything. `CLAUDE.md` is the terrain — what the code does
> and what will bite you; this is the map you hold while deciding where to go next.
>
> Every number here was checked against the repo on the date above. Where something is unverified,
> it says so.

---

## 1. The one-paragraph version

There is a working game engine with almost no game in it. The systems are real and mostly
play-tested: movement, combat, chunks, saves, the GTA-style consequence layer, mounts, an art
pipeline that turns generated images into animated actors, and a data-driven quest system. What is
missing is **content**. One of six chunks is dressed; the other four overworld chunks are empty
ground. Eleven NPCs stand in London and **not one of them can say a word**, because the v1 dialogue
was deleted today so the writing could start fresh. There are zero quests beyond the hand-coded
tutorial.

The bottleneck is no longer engineering. It is words and world-building.

---

## 2. What exists and is known to work

Play-tested in the editor by the owner, not merely written:

| System | Where | Notes |
|---|---|---|
| Chunk world, edge crossings | `World/ChunkManager`, `ChunkEdge` | 6 chunks, one live at a time, boundary walls generated |
| Save / load | `Flow/SaveGameManager` | One JSON file. Quest state, inventory, tutorial flag all persist |
| Combat, health, death, arrest | `Combat/`, `Flow/GameFlowController` | Police-dealt death arrests instead of killing |
| Consequence layer | `Systems/WantedManager` + 5 systems | Knives, concealment, Nosey Parkers, stealth, pickpocketing, e-bike theft, pub safehouses |
| Mounts / vehicles | `World/MountController` etc. | Data-driven spawning confirmed working |
| Art pipeline | `Editor/ArtImportTool` | Generated PNG → sliced sheet → clips → animator → auto-wired preset |
| World Palette | `Editor/WorldPaletteWindow` | How content gets placed. Has authored real content |
| Tutorial | `MagicTutorial`, `TutorialSequence` | Hand-coded, works, and is deliberately outside the quest system |

## 3. What is built but has never run

| Thing | Risk |
|---|---|
| **Three quest fixes** (`06a894f`, `73790a5`, `87f35db`) | The editor session that exercised the quest system predates all three. Low risk, but unproven |
| **Six open quest-system findings** | Written up in `CLAUDE.md` §14. Two are authoring traps that nothing warns about — read them before writing a quest |
| **NPC pipeline, tutorial half** | `MagicTutorial`'s preset-built cast has never been exercised, nor anything keyed off `EnemyAI.Animator` |

## 4. The content gap, in numbers

| | Count | Reality |
|---|---|---|
| Chunk prefabs | 6 | **Only `Home_London` is dressed** (161 objects). `North_Wasteland`, `South_Slums`, `East_RetailPark`, `West_Canal` contain **10 objects each**: a root, a ground plane, four edge triggers, four boundary walls. Nothing else. `Manor_Cellars` has 18 |
| NPCs placed | 11 | 9 London cast + 2 villagers, all in London. Commissioner Spencer is unplaced |
| NPCs that can talk | **0** | No `PlacementPreset` has a `Conversation`. Checked across all 23 |
| `DialogueData` assets | **0** | Only `NPC_Mosley.asset` survives, and that is a speaker identity, not a conversation |
| `QuestDefinition` assets | **0** | The quest system is built and completely inert |
| Grantable quests | **0** | Nothing in the game can start a quest except the hand-coded tutorial |
| Art subjects committed | 23 | Player (6 actions), e-bike, 8 London cast, 6 enemies, PCSO, villager, tutorial cast |

**The four empty chunks are the single largest gap.** Three quarters of the overworld is a flat
plane you can walk across and nothing else.

## 5. What is designed but not built

| Plan | Status |
|---|---|
| `docs/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md` | Approved design. Enterable buildings, location caching, corpse loot. **Nothing implemented.** Baseline verified against code |
| `docs/STAGE_RF_PLAN_REVISED.md` | Stage R done; **Stage F** — the six-commit inventory and loot overhaul — outstanding. `CLAUDE.md` §9 still calls this "the next task" |
| `ART_PIPELINE.md` §7 bands 3–8 | 21 world props, ambient cast, police tiers, 5 3D buildings (no delivery route), item icons, weapon sheets |
| Generated enemy prefabs | Fully planned in an earlier session, plan never written to disk. Art landed today, so this is unblocked |

## 6. Named things that are implied but do not exist

Worth knowing before planning around them:

- **No gold.** Pickpocketing and the arrest fine pay out in toast messages. `QuestReward.GoldAmount` warns and pays nothing
- **No shops.** Quidland (weapons) and F.U. Sports (armour) have clerks who stand there. No vendor UI, no buying, no selling
- **No bounty system.** Officer Riggs is meant to clear your wanted level for completed missions. Nothing is wired
- **No quest gating.** Mayor Swalls carries a `QuestKey` but nothing can hide him
- **No 3D building pipeline.** The five named London buildings have no approved delivery route

## 7. Known open issues worth carrying into any plan

- **Only the first active quest is watched *or* tracked.** A second concurrent quest is invisible and its conditions never advance. This becomes likely the moment two NPCs can talk
- **Death-respawn keeps you mounted** (`CLAUDE.md` §11). Deferred; needs a design call
- **Nosey Parkers are single-use per scene load** and fire on any concealment below max
- **`CastSpell` animator parameter** is declared by generated controllers but nothing else defines it — a console error
- **No test framework, and no C# compiler outside Unity.** Nothing can be verified mechanically beyond reference integrity

## 8. Repo hygiene

Clean as of this date: one branch (`main`), in sync with `origin`, no stashes, no worktrees,
nothing uncommitted, asset reachability at the known 17-GUID baseline.

Two empty directories remain under `.claude/worktrees/` — git no longer knows about them, they are
gitignored, and they are locked by a process that has not exited. Cosmetic.

---

## 9. The question this document exists to support

The engine is ahead of the content by a wide margin. Any goals conversation probably has to choose
between:

1. **Fill the world** — props for four empty chunks, then dress them.
2. **Make the cast live** — dialogue and quests, so eleven placed NPCs stop being scenery.
3. **Deepen the systems** — Stage F inventory/loot, gold, shops, building interiors.
4. **Consolidate** — pay down the open issues in §7 before adding surface area.

They are not mutually exclusive, but they compete for the same scarce thing: authored content.
Nothing in this document says which is right.
