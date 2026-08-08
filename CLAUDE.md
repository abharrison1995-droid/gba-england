# CLAUDE.md — GBH: England

**This file is a bootloader, not a manual.** It holds project identity, the rules that must never
be missed, and a routing table. Detail lives in `docs/`, loaded on demand.

**Read [docs/README.md](docs/README.md) to find what your task needs. Never read all of `docs/`.**

---

## 1. What this project is

A Unity **mobile RPG**, working title **Exiled Alvaston** (`ProjectSettings` → `productName`),
displayed to the player as **GBH: England** (`EKVibe.DisplayTitle`).

Set in a hostile modern Britain, with magic played straight. A GTA-like consequence layer — wanted
level, police, stealth, pickpocketing, vehicle theft — sits on top of a classic RPG core.

Three names are live and **deliberately not unified**: `Exiled Alvaston` (product name and C#
namespace), `GBH: England` (display title), and `EK*` prefixes referring to *Exiled Kingdoms*, the
inspiration game. `Discover England` survives only as the name of one editor tool.

### Presentation model — read this before touching movement or combat

**Isometric, by design.** A 3D world rendered with billboarded 2D sprites and a fixed isometric
camera — the Exiled Kingdoms presentation model. This is the intended target, not a legacy
artifact. **It is not a 2D project**, whatever any older brief says.

- 3D physics: `Rigidbody`, `Collider`, `Physics.OverlapSphere`
- Movement is on the **X/Z plane**; `Y` is up. Chunk edges are `pos.x` / `pos.z`.
- Fixed isometric camera (`IsometricCameraFollow`, pitch 30°, yaw -45°, ortho size 7)
- Sprites face camera via `SpriteBillboard`; actors composed by `WorldActorVisual`
- Input is screen-relative (`GetScreenRelativeMoveDirection`), not world-axis

⚠️ **Never introduce `Physics2D` / `Rigidbody2D` / `Vector2` movement.** It will not interact with
any existing collider — nothing will throw, things will simply pass through each other.

---

## 2. Layout and conventions

```
Assets/
  Scripts/          # runtime code, namespace ExiledAlvaston.<Folder>
    AI/ Camera/ Combat/ Data/ Dialogue/ Flow/ Quests/ Systems/ UI/ Vibe/ World/
  Editor/           # editor-only tools (no asmdef — see below)
  Data/Chunks/      # 6 MapChunkData .asset files
  Data/Presets/     # 30 PlacementPreset assets
  Data/Dialogue/    # DialogueData assets
  Prefabs/          # Chunks/, ModernBritain/, Enemies/
  Resources/        # loaded by name at runtime — Items/, Quests/, PlacementPresetLibrary
  Art/ Sprites/ Animations/ 3DModels/ Materials/
  6twelve/          # third-party pack, not our code
  c.unity           # THE only gameplay scene
  c/                # NavMesh data for c.unity, auto-linked by scene name
Tools/              # python helpers (see §5)
docs/               # everything else — routed from docs/README.md
```

- **Namespaces mirror folders**: `ExiledAlvaston.World`, `ExiledAlvaston.Combat`. Keep it that way.
- **Public fields, PascalCase**, for anything Unity serializes (`CurrentKnives`, `ChunkPrefab`).
- **Private fields `_camelCase`** (`_isTransitioning`, `_hitThisSwing`).
- **Singletons**: `public static X Instance { get; private set; }` set in `Awake`. Access pattern
  is `X.Instance ?? FindObjectOfType<X>()`.
- **Tuning constants belong in `EKVibe`** (`Scripts/Vibe/EKVibe.cs`) — colours, sizes, camera,
  `ChunkSize`, `CharacterHeight`. Prefer adding there over new magic numbers.
- **ScriptableObject menu path**: `ExiledAlvaston/Data/...`
- **Editor menu path**: `Tools/GBH/<Category>/...` — `Place`, `Art`, `World`, `Debug`, `Repair`,
  `Content`, plus **`Danger Zone`** for the five tools that overwrite or re-create assets. Each of
  those confirms first and names what it destroys. **Nothing destructive may go anywhere else.**
  `Tools/GBH/World Palette` is the one deliberate uncategorised exception.
- **Mobile-first**: hot paths avoid allocation deliberately (preallocated `Collider[] _hitResults`,
  parallel key lists to avoid dictionary-iteration garbage). Respect this in `Update()` paths.
- **`Assets/Editor/` is stripped from builds** and there are **no `.asmdef` files**, so it is the
  only thing keeping editor code out of the build. Editor-only code must live there; anything the
  running game needs must not.

---

## 3. Safety capsule — these are never safe to get wrong

Each item below is repeated deliberately from its canonical reference, because a reference that
was never loaded cannot stop a mistake.

### Save keys

Changing the **value** of any of these silently orphans existing saves — nothing throws, nothing
logs, the data is gone:

- **`MapChunkData.ChunkName`** — stored as a string, resolved via `ChunkManager.FindChunkByName`.
  `Manor_Cellars_Data` uses `"Manor Cellars"` **with a space**. Do not normalise it.
- **`ItemData.ItemID`** — inventory is saved as `ItemID` + `Quantity` and resolved through
  `Resources/Items`. A changed id is read, fails to resolve, and is dropped in silence.

There is **one** save file: `persistentDataPath/savegame.json`, written with `JsonUtility`. Not
PlayerPrefs. Five call sites write it.

→ [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md)

### Unity serialization

- **Renaming a public serialized field drops its value everywhere** unless you add
  `[FormerlySerializedAs]`. Appending a field is safe; inserting is not.
- **Enums are serialized by integer index. Always append.** Twelve are live.
- **Commit a script's `.meta` with the script.** The GUID inside it is what binds prefabs and the
  scene to the class. This has gone wrong twice, and it fails silently on a fresh clone.
- ⚠️ **Never rebuild an existing prefab by deleting and re-saving it.** That takes the `.meta` with
  it and mints a fresh GUID, orphaning every instance already placed. Edit in place:
  `PrefabUtility.LoadPrefabContents` → modify → `SaveAsPrefabAsset` → `UnloadPrefabContents`.
- **`UnityEvent.AddListener` does not survive being saved into a prefab.** Only
  `UnityEditor.Events.UnityEventTools` writes a persistent call.

**Before any rename or refactor touching a save key or a serialized field, produce an explicit
mapping table first.**

### The chunk world

- **Seven runtime code paths instantiate a chunk. Two do the full lifecycle**
  (`TransitionToChunkRoutine`, `TravelRoutine`); five are direct replacements. Change transition
  behaviour and you must touch all seven.
- **`CurrentChunkData` is written from eight places across six files.** To react to a chunk change,
  **poll a remembered reference** — do not hook one transition and assume you caught them all.
- ⚠️ **A chunk root cannot be suspended with `SetActive(false)`.** It permanently blinds every
  `EnemyAI`, leaks a registered NavMesh, strands two tutorial singletons and leaves scene-root
  nameplates visible. Chunks are only ever destroyed.

→ [docs/reference/CHUNK_WORLD.md](docs/reference/CHUNK_WORLD.md)

### Vehicles

⚠️ **Never `SetActive(false)` a vehicle root.** `OnDisable` clears the speed multiplier, so the
vehicle cancels its own boost the instant it is mounted. Hide `ParkedModel` instead.

→ [docs/reference/CONSEQUENCES_AND_MOUNTS.md](docs/reference/CONSEQUENCES_AND_MOUNTS.md)

### Writing

⚠️ **Quest and dialogue prose is the owner's own work.** Build the machinery, leave the words.
Wiring, presets, quest definitions, conditions and tools are all fair game; the lines an NPC says
are not. If a task seems to need dialogue, ask for it rather than drafting it.

Note that `Tools > GBH > Content > Create Starter Presets` will generate a `DialogueData` from any
preset that has an `AmbientLine` and no `Conversation`. Leave a blank `AmbientLine` blank.

---

## 4. Where to look

| Task touches… | Read |
|---|---|
| Chunks, transitions, edges, building interiors | [docs/reference/CHUNK_WORLD.md](docs/reference/CHUNK_WORLD.md) |
| Saves, serialized fields, enums, `.meta`/GUIDs | [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md) |
| Wanted level, police, stealth, pickpocketing, mounts, movement speed | [docs/reference/CONSEQUENCES_AND_MOUNTS.md](docs/reference/CONSEQUENCES_AND_MOUNTS.md) |
| World Palette, presets, NPCs, enemy prefabs | [docs/reference/WORLD_AUTHORING_AND_NPCS.md](docs/reference/WORLD_AUTHORING_AND_NPCS.md) |
| Quests, quest conditions, dialogue graphs | [docs/reference/QUESTS_AND_DIALOGUE.md](docs/reference/QUESTS_AND_DIALOGUE.md) |
| The art importer, sprite sizing, animator controllers | [docs/reference/ART_IMPORTER.md](docs/reference/ART_IMPORTER.md) |
| Title screen, character creator, their layout and art | the two `Assets/Editor/*ScreenSetup.cs` / `*CreatorSetup.cs` builders — no reference doc; the anchors and the reasons for them are commented at each call site, because they are only true of the code that writes them |
| Git, asset pruning, `.gitattributes`, project naming | [docs/reference/REPO_HYGIENE.md](docs/reference/REPO_HYGIENE.md) |
| Generating art (the art agent's contract) | [ART_PIPELINE.md](ART_PIPELINE.md) + [docs/art/ART_QUEUE.md](docs/art/ART_QUEUE.md) |
| What to work on next | [docs/README.md](docs/README.md) → `docs/plans/` |

---

## 5. Verification — read this before claiming something works

**There is no C# compiler, no Unity, and no test framework in the agent environment.** This is the
single most important thing to be honest about in this repo, because the whole convention here is
that documentation records what the code *actually does*.

What can be checked mechanically:

```bash
python Tools/asset_reachability.py --check-dangling   # reference integrity; exits 1 on breakage
python Tools/asset_reachability.py --packs            # which asset packs are fully unused
python Tools/art_status.py                            # what art exists and what is still owed
```

On Linux that is `python3` — Mint has no bare `python`.

`--check-dangling` resolves GUIDs from `Assets/`, `Packages/` **and `Library/PackageCache/`** —
every script Unity ships lives in a package, so without that last root `LayoutElement` and friends
read as missing and the check fails the moment the scene uses a UI component it had not used
before. Unity's two sentinel GUIDs are filtered. Everything still unresolved is real breakage and
is listed by name in `KNOWN_DANGLING`, not absorbed into a tolerated count; **anything not on that
list fails the run**, naming the GameObject and field that points at nothing. Exit codes are `0`
clean, `1` dangling, `2` couldn't verify — `Library/` is gitignored, so on a fresh clone it reports
that it checked nothing rather than passing. Run it before and after anything that deletes, moves
or renames assets.

**Everything else needs the Unity editor and therefore needs a human.** Say so plainly rather than
implying otherwise:

- Reference integrity passing says **nothing** about whether the project builds.
- A brace/paren balance scan catches a truncated edit. It says nothing about whether the code is
  correct or even compiles. **Do not report it as though it were a compile.**
- An editor tool that *generates* content has not changed anything until a human runs the menu
  item. Say that, rather than describing the change as landed.

⚠️ **Changes made in the Inspector while Play mode is running are discarded when it stops.** This
has wasted real time. When asking for an editor change, say whether Play must be stopped first.

⚠️ **Give the route through the editor UI, not just the field name** — name the panel (Hierarchy,
Inspector, Project), the full menu path, which GameObject to select and how to reach it, and any
precondition (exit Play mode, wait for the recompile, Ctrl+S). Naming a field alone is not enough.

### Never verified — the standing ledger

Everything here is on `main` and pushed. **None has been seen by a compiler or an editor.** Check
these the next time Unity is open, and keep this list current — delete an item when it is
confirmed, rather than leaving it hedged.

1. **The project compiled on 2026-08-05.** Both Danger Zone screen tools were run successfully
   that day, and `CharacterCreatorSetup` references `CharacterCreatorUI`, `PlayerClass` and
   `GameFlowController`, so the editor assembly could not have loaded unless `Assembly-CSharp`
   built too. That clears the whole backlog of never-compiled files — `EKVibe`, `EnemyAI`,
   `UIManager` and everything the pounds rename touched. **It proves they compile, nothing more:
   none of their behaviour has been exercised.** The creator tool was run again later the same
   day, after `CharacterCreatorUI`, `PlayerSession`, `SaveGameManager` and `CharacterCreatorSetup`
   changed, so those compile too.
2. **`UIManager.EnsureDedicatedTrack`** — wraps a bar fill in its own parent when the scene did not
   give it one, fixing the concealment readout overlapping the mana bar. *Check the readouts no
   longer overlap, and that the concealment bar snaps back to wherever it was actually authored* —
   it has been stretched across the whole cluster until now, so its real size and position are
   unknown and may need moving.
3. **Every actor is 0.2 taller** — player 1.8, NPCs 1.55, child 1.3. Colliders, agents and
   nameplates were matched to each actor's sprite. *Check nobody's feet are underground and no
   nameplate sits on a head.*
4. **`EnemyAI.Awake` no longer hardcodes `_agent.height = 1.35f`** — it takes
   `WorldActorVisual.Height`. *Check enemies path around buildings, not through them* (needs a
   NavMesh bake after collision).
5. **Six enemy prefabs never seen in play** — Neek, OG, Roadman, Spicehead, Tainted, Tortured Neek.
   Expect Tortured Neek to slide and to have no death pose: he has only an idle sheet, which is an
   art gap, not a defect.
6. **The three quest fixes** — `ClearWanted` despawning police, `StartQuest` no longer rewinding a
   mid-flight objective, and the watcher claiming a reward only after paying it. The editor session
   that exercised the quest system predates all three. Re-testing needs a `QuestDefinition` in
   `Resources/Quests/` and some way to grant a quest; the throwaway rig was deleted deliberately,
   because quests are meant to be granted by an NPC or a world trigger, never a menu item.
7. **`murtaugh_Controller` is hand-authored YAML**, verified only structurally. *Check Murtaugh
   animates while roaming instead of sliding.* If Unity rejects it, re-stage the walk pair from
   `art_incoming/processed/` and re-run the importer.
8. ⚠️ **The pounds rename relies on `[FormerlySerializedAs]` doing its job.** 25 `Preset_*.asset`
   files still hold the old `…Gold` keys on disk. *Open any robbable
   preset (e.g. `Preset_Villager`) in the Inspector and check Pickpocket Min/Max Pounds read
   **5 and 25**, not 0.* If they read 0 the remap did not take and the values are gone — restore
   from git rather than retyping 25 assets.
9. **£ may not be in the TMP font atlas.** `EKVibe.FormatPounds` emits U+00A3, and TMP's default
   static atlases are often ASCII-only, which renders it as a missing-glyph box. *Check the bag's
   money readout and the pickpocket toast.* Fix is on the font asset (Project → the TMP font →
   Inspector): add £ to the character set and regenerate, or switch Atlas Population Mode to
   Dynamic.
10. **The wallet has never run.** Pickpocket a civilian authored `Pickpocketable`, get arrested,
    and reload a save.
    *Check the bag readout tracks all three, and that a save made before today loads at £0 rather
    than failing.*
11. **The blank-name fallback has never run.** The creator's name box starts empty behind a
    "Player name here!" placeholder, and `PlayerSession.BeginNewGame` turns a blank into
    **Vince**. The screen itself is confirmed; what is not is what happens on confirming without
    typing. *Start a new game leaving the box untouched and check the nameplate reads Vince, not
    blank.*

12. **Eleven sheets were mirrored to face camera-right** by `Tools/flip_sheets.py`, in place, so no
    `.meta`, GUID, clip or controller changed: `murtaugh_walk`, `neek_hurt`, `og_hurt`,
    `police_pcso_walk`, `roadman_death`, `spicehead_hurt`, `spicehead_walk`, and all four villager
    walks. The facing call was made from the art by eye, not measured — *check each one plays
    facing right and that the walk cycles still run forwards, not backwards.* A wrong call is
    undone with `python Tools/flip_sheets.py --force <name>`. `player_stabmeister_walk` was flipped
    too but is still in `art_incoming/` and has never been imported.

**The cast is now uniformly 65 px.** Every character sidecar declares `worldHeight: 1.35`, which
imports at 65 px cells. `sheet_char_player_mrhood_idle` and `sheet_char_player_stabmeister_idle`
were the last two still on disk at 74; the importer has re-done them in place, GUIDs intact, and
both measure 65 px tall as of 2026-08-08.

⚠️ **`ART_PIPELINE.md` still tells the art agent adults are `1.55`**, so the next delivered batch
will arrive at the wrong density again and need the same correction. Deciding whether the contract
or the cast is the thing to change is the owner's call, and nothing here has made it.

**Also outstanding — a live defect, not a verification:** no `Police_*` prefab has `IsPolice` set,
so arrest never fires and `DespawnPolice` destroys nothing. Fix is ticking the box on all five
prefabs in the Inspector, **never** by re-running `ModernBritainSetup`.

**Also outstanding — four sprites in `c.unity` point at files that do not exist.** Three `Visual`
SpriteRenderers on one missing texture, three on another, one more on a third, and the **PCSO**
actor's `WorldActorVisual.ActorSprite` on a fourth. They are as old as commit `fc1d035` at least,
and were hidden until now inside a `--check-dangling` baseline that called them built-in Unity
GUIDs. They are listed in `KNOWN_DANGLING` in `Tools/asset_reachability.py`. Fix is reassigning
each sprite in the Inspector, then deleting its line from that list. The PCSO one probably wants
`sheet_char_police_pcso_idle`, which is on disk — *check that before assuming it.*

**Also outstanding — XP and levels, phases 1–2, none of it exercised.** Merged 2026-08-08,
code-reviewed against its plan, never compiled:

- **Kill XP depends on a one-line fix landing.** Both player damage sites now pass `gameObject`
  into `TakeDamage` so `Health.LastAttacker` is set; before, it was always null for player hits.
  *Kill an enemy and check XP moves off zero.* If it does not, that fix did not take, and nothing
  will say so.
- **`EnemyLevel` scales from the prefab's level-1 baseline**, applied inside `Health.Awake` before
  `CurrentHealth = MaxHealth`. *Add one to an enemy, set Level 5, and check it spawns at full
  health, not partial.* An enemy without the component is untouched and stays level 1.
- ⚠️ **Every existing enemy still wears a "3" badge** while actually being level 1 — eleven
  prefabs store `Level: 3` on disk from when the nameplate's level was cosmetic. Cosmetic only,
  but it will look wrong until levels are authored.
- **`SaveData.TotalXP` is appended.** *Load a save made before today and check it arrives at
  level 1 rather than failing.*
- **The bag readout binds only after** `Tools → GBH → UI → Rebuild Inventory Panel (Win95)` is
  run — the scene's `LevelText` is unassigned until then. The HUD badge is already wired.

→ [docs/plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md](docs/plans/PROGRESSION_PHASE1_2_IMPLEMENTATION.md) §9.3 for the full routes.

**Also outstanding — the equipment, map and encyclopedia work, none of it exercised.** Committed
2026-08-08, never in an editor:

- **The paper doll.** *Equip a weapon and check the melee number goes up by its `Damage`; equip
  armour and check incoming hits drop by `TotalArmor`.* ⚠️ Armour is a **flat** subtraction floored
  at zero, so a full doll may make weak enemies harmless — a balance question, not a bug.
- **The bag window was rebuilt by `InventoryWin95Builder`.** The scene edit is committed, but
  *check the rail buttons, the equipment slots and the tooltip all sit where they should* — the
  builder is an editor tool and its output has never been looked at in Play mode.
- **Map of Britain and WIKIBRITAIN.** *Check a first arrival toasts and a reload does not, and that
  a save made before today opens a populated encyclopedia rather than a toast storm* — the
  backfill path in `ContinueFromSave` is the one most likely to be wrong.
- **Three new save fields** (`Equipment`, `VisitedChunks`, `UnlockedWikiEntries`). *Load a
  pre-equipment save and check it arrives with an empty doll and a blank map instead of failing.*

---

## 6. Working agreement

Multi-agent workflow: **plan → implement → review → merge.** Three agents in `.claude/agents/`,
invoked by name.

| Agent | Role |
|---|---|
| `architect` | Scopes, produces the plan and mapping table, flags structural risk. **Never edits code.** |
| `implementer` | Works strictly from the plan. Small single-concern commits. No scope improvisation. |
| `reviewer` | Reviews the diff against the plan, hunting silent failure modes — not style. |

Typical use: *"use the architect subagent to plan X"* → approve → *"use the implementer subagent to
execute it"* → *"use the reviewer subagent to review the diff against the plan"*.

**Skip the ceremony for genuinely small, low-risk changes.** It exists for anything touching §3.

The `model:` frontmatter takes an **exact model id**, not the `opus`/`sonnet` tier alias the `Agent`
tool's own parameter is limited to. ⚠️ An exact id launches without error — that proves the launch
path accepts it, **not** that the named model served the request. There is no way from inside a
session to confirm which model ran a subagent, so never report a pin as "working" beyond that.

---

## 7. Documentation rules

- **Each operational fact has one canonical owner** (the table in §4). A subsystem change updates
  that one reference, not four files. Critical invariants may be repeated in §3 as short
  guardrails, because a reference is not guaranteed to be loaded.
- **Replace a stale statement — never strike it through and correct it beside itself.** The old
  wording is what a reader carries away. Git holds the history.
- **Do not put branch history, PR numbers or completed bug postmortems in a bootloader.** Git
  already has them, in more detail and better indexed.
- **Volatile snapshots are dated and archived**, not nursed into looking current.
- **"What's next" belongs in `docs/plans/`**, never here.
- **Every reference carries a verification header.** If you change what a reference describes,
  update its header — including downgrading its scope when you could not verify.
