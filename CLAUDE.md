# CLAUDE.md — GBH: England

**This file is a bootloader, not a manual.** It holds project identity, the rules that must never
be missed, and a routing table. Detail lives in `docs/`, loaded on demand.

**Read [docs/README.md](docs/README.md) to find what your task needs. Never read all of `docs/`.**

---

## 1. What this project is

A Unity **mobile RPG** called **GBH: England** (`EKVibe.DisplayTitle`).

Set in a hostile modern Britain, with magic played straight. A GTA-like consequence layer — wanted
level, police, stealth, pickpocketing, vehicle theft — sits on top of a classic RPG core.

**The name is unified.** The old working title `Exiled Alvaston` and the older `Discover England`
were swept out on 2026-08-16 — root C# namespace `GBHEngland`, `productName` **`GBH England`** (no
colon: it becomes a real folder inside `persistentDataPath`), `Create →` menus under
`GBH England/Data/…`, and the repo itself still `gba-england` because a colon is illegal in a path.
**Do not reintroduce the old names.** The one deliberate survivor is the `EK*` prefix (`EKVibe`,
`EKNavMeshBaker`) — it refers to *Exiled Kingdoms*, the inspiration game, and is a lineage marker
rather than a stale title.
→ [docs/plans/NAME_UNIFICATION_PLAN.md](docs/plans/NAME_UNIFICATION_PLAN.md)

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
  Scripts/          # runtime code, namespace GBHEngland.<Folder>
    AI/ Camera/ Combat/ Data/ Dialogue/ Flow/ Quests/ Systems/ UI/ Vibe/ World/
  Editor/           # editor-only tools (no asmdef — see below)
  Data/Chunks/      # 19 MapChunkData .asset files
  Data/Presets/     # 38 PlacementPreset assets
  Data/Dialogue/    # DialogueData assets
  Prefabs/          # Chunks/, ModernBritain/, Enemies/
  Resources/        # loaded by name at runtime — Items/, Quests/, PlacementPresetLibrary
  Art/ Sprites/ Animations/ 3DModels/ Materials/
  6twelve/          # third-party pack, not our code
  c.unity           # THE only gameplay scene
  c/                # NavMesh data for c.unity, auto-linked by scene name
Tools/              # python helpers (see §5) + Tools/blender/ (see Tools/blender/README.md)
docs/               # everything else — routed from docs/README.md
```

- **Namespaces mirror folders**: `GBHEngland.World`, `GBHEngland.Combat`. Keep it that way.
- **Public fields, PascalCase**, for anything Unity serializes (`CurrentKnives`, `ChunkPrefab`).
- **Private fields `_camelCase`** (`_isTransitioning`, `_hitThisSwing`).
- **Singletons**: `public static X Instance { get; private set; }` set in `Awake`. Access pattern
  is `X.Instance ?? FindObjectOfType<X>()`.
- **Tuning constants belong in `EKVibe`** (`Scripts/Vibe/EKVibe.cs`) — colours, sizes, camera,
  `ChunkSize`, `CharacterHeight`. Prefer adding there over new magic numbers.
- **ScriptableObject menu path**: `GBH England/Data/...`
- **Editor menu path**: `Tools/<Category>/...` — `Place`, `Art`, `World`, `UI`, `Debug`,
  `Repair`, `Content`, plus **`Danger Zone`** for the five tools that overwrite or re-create assets. Each of
  those confirms first and names what it destroys. **Nothing destructive may go anywhere else.**
  `Tools/World Palette` is the one deliberate uncategorised exception. **`Assets/Editor/` is
  physically organised into matching subfolders** (`Place/`, `Art/`, `World/`, `UI/`, `Debug/`,
  `Repair/`, `Content/`, `Danger Zone/`, since 2026-08-20), plus two the menu convention doesn't
  name: `Validators/` (the four content-validation tools) and `Shared/` (helper classes with no
  menu item of their own — `PlacementBuilders`, `EditorMaterialLibrary` — consumed by tools in
  other folders). A file's folder and its `MenuItem` category usually match, but the folder is
  about where the code lives, not what the menu shows — `WorldPaletteWindow.cs` sits in `World/`
  despite its own uncategorised menu path.
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
- **`AbilityData.AbilityID`** — learned and equipped spells are saved as ids and resolved through
  `Resources/Abilities`. Never rename a shipped spell id.
- **`WikiEntryData.EntryID`** — unlocked encyclopedia entries are saved as a list of these.
- **`PerkData.PerkId`** — spent perks are saved as a list of these and resolved through
  `Resources/Perks`. A changed id is read, fails to resolve, and the perk's effects quietly stop
  existing — the id is deliberately **kept** rather than dropped, so the point stays spent.

There is **one** save file: `persistentDataPath/savegame.json`, written with `JsonUtility`. Not
PlayerPrefs. Five call sites write it.

→ [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md)

### Unity serialization

- **Renaming a public serialized field drops its value everywhere** unless you add
  `[FormerlySerializedAs]`. Appending a field is safe; inserting is not.
- **Enums are serialized by integer index. Always append.** Twenty-one are live.
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
- ⚠️ **In `Awake`, ask `ChunkManager.ContentChunkName`, never `CurrentChunkData`.** `TravelRoutine`
  instantiates the destination *before* assigning `CurrentChunkData` — deliberately, so a broken
  arrival marker leaves the world untouched — and every `Awake` in the new chunk runs inside that
  `Instantiate`. Content that asks directly gets the chunk the player just **left**, on that one
  path of the seven, silently. This is a save-key bug wherever the answer is persisted.
- ⚠️ **A chunk root cannot be suspended with `SetActive(false)`.** It permanently blinds every
  `EnemyAI`, leaks a registered NavMesh, strands two tutorial singletons and leaves scene-root
  nameplates visible. Chunks are only ever destroyed.
- ⚠️ **`OnChunkTransition` takes a `ChunkTravelKind`, and only `EdgeCrossing` shakes the police.**
  A door is not an escape: every interior and dungeon carries `IsCity: 0`, so a new path that
  passes `EdgeCrossing` because it is the first enum value hands the player a free wanted-level
  wipe, silently. Pass `Portal` unless the player genuinely walked out of town.

→ [docs/reference/CHUNK_WORLD.md](docs/reference/CHUNK_WORLD.md)

### Vehicles

⚠️ **Never `SetActive(false)` a vehicle root.** `OnDisable` clears the speed multiplier, so the
vehicle cancels its own boost the instant it is mounted. Hide `ParkedModel` instead.

→ [docs/reference/CONSEQUENCES_AND_MOUNTS.md](docs/reference/CONSEQUENCES_AND_MOUNTS.md)

### Writing

⚠️ **Quest and dialogue prose is the owner's own work.** Build the machinery, leave the words.
Wiring, presets, quest definitions, conditions and tools are all fair game; the lines an NPC says
are not. If a task seems to need dialogue, ask for it rather than drafting it.

Note that `Tools > Content > Create Starter Presets` will generate a `DialogueData` from any
preset that has an `AmbientLine` and no `Conversation`. Leave a blank `AmbientLine` blank.

---

## 4. Where to look

| Task touches… | Read |
|---|---|
| Chunks, transitions, edges, building interiors | [docs/reference/CHUNK_WORLD.md](docs/reference/CHUNK_WORLD.md) |
| Saves, serialized fields, enums, `.meta`/GUIDs | [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md) |
| Wanted level, police, stealth, pickpocketing, mounts, movement speed | [docs/reference/CONSEQUENCES_AND_MOUNTS.md](docs/reference/CONSEQUENCES_AND_MOUNTS.md) |
| World Palette, presets, NPCs, enemy prefabs | [docs/reference/WORLD_AUTHORING_AND_NPCS.md](docs/reference/WORLD_AUTHORING_AND_NPCS.md) |
| Containers, foraging, loot respawn | [docs/plans/CONTAINER_SYSTEM_PLAN.md](docs/plans/CONTAINER_SYSTEM_PLAN.md) + save keys in [docs/reference/SAVE_AND_SERIALIZATION.md](docs/reference/SAVE_AND_SERIALIZATION.md) |
| Quests, quest conditions, dialogue graphs | [docs/reference/QUESTS_AND_DIALOGUE.md](docs/reference/QUESTS_AND_DIALOGUE.md) |
| The `.quest` file format, its directives, authoring a new quest as plain text | [docs/reference/QUEST_TEXT_FORMAT.md](docs/reference/QUEST_TEXT_FORMAT.md) |
| Spells, spell tuning, spellbook persistence and spell VFX | [docs/reference/SPELLS.md](docs/reference/SPELLS.md) |
| The art importer, sprite sizing, animator controllers | [docs/reference/ART_IMPORTER.md](docs/reference/ART_IMPORTER.md) |
| Title screen, character creator, their layout and art | the two `Assets/Editor/Danger Zone/*ScreenSetup.cs` / `*CreatorSetup.cs` builders — no reference doc; the anchors and the reasons for them are commented at each call site, because they are only true of the code that writes them |
| Git, asset pruning, `.gitattributes`, project naming | [docs/reference/REPO_HYGIENE.md](docs/reference/REPO_HYGIENE.md) |
| Generating art (the art agent's contract) | [ART_PIPELINE.md](ART_PIPELINE.md) + [docs/art/ART_QUEUE.md](docs/art/ART_QUEUE.md) |
| Building a 3D model (band 6 buildings, props) | [Tools/blender/README.md](Tools/blender/README.md) — or invoke the `model-author` skill |
| Confirming whether a landed change has been seen by a compiler or the editor | [docs/reference/VERIFICATION_LEDGER.md](docs/reference/VERIFICATION_LEDGER.md) |
| What to work on next | [docs/README.md](docs/README.md) → `docs/plans/` |

This table mirrors docs/README.md's. Change both together.

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

Everything that has landed on `main` but has never been seen by a compiler or an editor is
recorded in **[docs/reference/VERIFICATION_LEDGER.md](docs/reference/VERIFICATION_LEDGER.md)**,
which owns that status exclusively. **Read it before claiming any feature works, and before
touching a system listed in it.** It is not a routine read — §4 still routes ordinary work.

Compile checkpoints, confirmed items and open items all live there. Do not restate any of it here;
a status list in a bootloader rots faster than anywhere else (§7).

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
