# AGENTS.md

Guidance for AI coding agents working in this repository. `CLAUDE.md` is the deep,
code-verified reference for the runtime systems (chunk world, save system, consequence
mechanics, mounts, art pipeline) — read it before touching anything under §"High-risk areas"
below. This file is the map; that one is the terrain.

## Project overview

**Exiled Alvaston** — a Unity **mobile RPG** (working title, from `productName` in
`ProjectSettings`). The rename to *GBA: England* has begun: `EKVibe.DisplayTitle` is already
"GBA: England" and the hub chunk is `Home_London`, but `productName` and the `ExiledAlvaston`
namespace are unchanged. The repo folder is `gba-england`. See CLAUDE.md §10.

- **Presentation: isometric 3D world with billboarded 2D sprites.** A fixed camera
  (pitch 30°, yaw −45°, ortho size 7), 3D physics (`Rigidbody`, `Collider`, movement on the
  X/Z plane), and sprites that face the camera. This is the intended design — an older brief
  calling it a "2D mobile RPG" is stale. **Never introduce `Physics2D`/`Rigidbody2D`.**
- **Setting:** modern Britain, slightly grim, slightly funny — council estates, pubs, e-bikes,
  with magic played straight. A GTA-like consequence layer (wanted level, police, stealth,
  pickpocketing, vehicle theft) sits on top of a classic RPG core (quests, dialogue, combat).
- **Naming is deliberately inconsistent — do not "unify" it.** `Exiled Alvaston` is the
  product name and C# root namespace; `Discover England` is the in-game display title;
  `EK*` prefixes refer to *Exiled Kingdoms*, the inspiration game.

## Two agents work in this repo

| Agent | Job | Writes to |
|---|---|---|
| **Claude Code** | All code, Unity assets, scene and prefab work. Reads `CLAUDE.md`. | `Assets/`, `Tools/`, git |
| **Art agent** (Antigravity/Gemini) | Generates sprites, sheets and textures. Reads `ART_PIPELINE.md`. | `art_incoming/` **only** |

### If you are the art agent, read this and then `ART_PIPELINE.md`

**You produce image files and their sidecar JSON into `art_incoming/`. Nothing else.**

Hard rules:

- **Never write anything inside `Assets/`.** Unity is usually open; it imports partial writes and
  generates `.meta` files that then conflict. Everything you make goes in `art_incoming/`, and a
  Unity-side importer moves it in deliberately.
- **Never create or edit a `.meta` file.** Unity owns those. A hand-written `.meta` can break the
  GUID binding that holds the whole project together.
- **Never edit `.cs`, `.unity`, `.prefab`, `.asset`, `.controller` or `.anim`.**
- **Never run git.** Do not commit, stage, branch or push. Claude Code handles version control.
- **Never run Unity or any editor tool.**
- **Do not leave intermediates behind.** No `.psd`, no upscaler outputs, no "v2_final" duplicates.
  This repo has **no Git LFS** and its history already carries hundreds of MB of art blobs — every
  file committed is permanent weight. One PNG per asset, plus its `.json`.

**There is no 3D pipeline, and you cannot supply one.** Everything above is 2D. The five named
London buildings in `ART_PIPELINE.md` §7.9 are **3D models** whose delivery route is undecided,
and building interiors are not an art deliverable at all — they are Unity-side chunk prefabs
assembled from existing assets.

If a **supported 2D** request is ambiguous, write your question into the asset's `.json` as a
`"question"` field and produce your best attempt anyway. Do not guess at project structure to
resolve it.

**Unsupported asset classes are the deliberate exception to that rule: ask and stop.** For the
§7.9 3D buildings, do not produce a substitute PNG, a model, or a sidecar. A best-attempt
placeholder there is worse than nothing — it would be imported as a billboard sprite and crushed
to 48 px per world unit.

### If you are Claude Code

`CLAUDE.md` is your file — this one only tells you where the art handoff lives. `ART_PIPELINE.md`
§"Importing" is your side of the contract: the art agent drops PNG+JSON pairs in `art_incoming/`
(gitignored staging), and `Tools → GBA → Art → Import Generated Art` (`Editor/ArtImportTool.cs`)
keys out the magenta backdrop, trims, reduces to 48 px per world unit, slices sheets, builds
clips and animator controllers, and archives clean pairs to `art_incoming/processed/`.

## Tech stack

- **Unity 2022.3.20f1** (`ProjectSettings/ProjectVersion.txt`), C#, mobile target.
- Packages (`Packages/manifest.json`): uGUI, TextMeshPro 3.0.6, glTFast 6.0.1, plus the
  standard Unity modules. No other third-party packages.
- **No `.asmdef` files** — everything compiles into `Assembly-CSharp` /
  `Assembly-CSharp-Editor`. `Assets/Editor/` is the only thing keeping editor code out of
  builds, so editor-only code **must** live there.
- **Python 3** helper scripts in `Tools/` (see "Build and verification").
- No build scripts, no CI, no test framework. Building and running happen in the Unity editor.

## Project layout

```
Assets/
  Scripts/            # all runtime code, namespace ExiledAlvaston.<Folder>
    AI/               # NoseyParkerAI (civilians who report you)
    Camera/           # IsometricCameraFollow
    Combat/           # CombatController (player), EnemyAI, Health, LightningBolt
    Data/             # ScriptableObjects: MapChunkData, CharacterData, AbilityData,
                      #   ItemData, DialogueData, PlayerClass, VehicleData
    Dialogue/         # DialogueManager
    Flow/             # GameFlowController, PlayerSession, SaveGameManager
    Quests/           # QuestManager
    Systems/          # PauseManager, WantedManager
    UI/               # UIManager, HUD, joystick, inventory, title/creator/death screens
    Vibe/             # EKVibe — central const/colour/tuning table
    World/            # ChunkManager, ChunkEdge, doors, nameplates, billboards,
                      #   MountController + VehicleController + VehicleSpawner
  Editor/             # editor-only tools: ArtImportTool, WorldPaletteWindow,
                      #   ModernBritainSetup, placement tools, repair tools
  Data/Chunks/        # 6 MapChunkData .asset files
  Prefabs/Chunks/     # 6 matching chunk prefabs
  Prefabs/ModernBritain/  # police tiers, Nosey Parker, e-bike, pub
  Resources/Items/    # ItemData loaded by name at runtime (Resources.Load)
  3DModels/, Sprites/, Art/, Animations/, Materials/   # art
  6twelve/            # third-party asset pack (has its own DEMO scene) — not our code
  c.unity             # THE main scene (only scene in build settings)
  c/                  # NavMesh data for c.unity (auto-linked by scene name)
Tools/                # Python: asset_reachability.py, precheck_sheets.py, tile_frames.py,
                      #   gen_placeholders.py, write_unity_metas.py
art_incoming/         # generated-art staging (gitignored except its README)
.claude/agents/       # architect / implementer / reviewer subagent definitions
```

**There is one gameplay scene: `Assets/c.unity`.** Renaming it orphans `Assets/c/NavMesh.asset`.

The world is discrete 220×220-unit chunks (`EKVibe.ChunkSize`), one live at a time, linked by
explicit `NorthChunk`/`SouthChunk`/`EastChunk`/`WestChunk` references on `MapChunkData`.
Current chunks: `Home_London` (hub city), `North_Wasteland`, `South_Slums`,
`East_RetailPark`, `West_Canal`, `Manor_Cellars` (tutorial dungeon, reached by door).

## Build and verification commands

There is **no test framework and no C# compiler available outside Unity.** What can be checked
mechanically from the command line:

```
python Tools/asset_reachability.py --check-dangling   # reference integrity; exits 1 on breakage
python Tools/asset_reachability.py --packs            # which asset packs are fully unused
python Tools/precheck_sheets.py [sheet.png ...]       # replicates the importer's sheet checks
python Tools/tile_frames.py <subject> <action>        # tiles art_incoming/frames/ into a sheet
```

The last two are the generated-art pipeline; `ART_PIPELINE.md` §7.3a is the workflow they belong
to. `precheck_sheets.py` exits 1 on anything the importer would refuse, so it is the gate before
opening Unity.

`--check-dangling` knows the build scene's built-in baseline (17 unresolved Unity-internal
GUIDs) and fails only above it. **Run it before and after anything that deletes, moves or
renames assets.**

Everything else — does the scene load, is anything pink, do the mechanics behave — needs the
Unity editor and therefore a human. Say so plainly rather than implying a change is verified.
A brace-balance scan catches truncated edits; it is not a compile and must not be reported as
one.

## Code conventions

- **Namespaces mirror folders**: `ExiledAlvaston.World`, `ExiledAlvaston.Combat`, etc.
- **Public serialized fields PascalCase** (`CurrentKnives`, `ChunkPrefab`);
  **private fields `_camelCase`** (`_isTransitioning`).
- **Singletons**: `public static X Instance { get; private set; }` set in `Awake`, accessed as
  `X.Instance ?? FindObjectOfType<X>()`.
- **Tuning constants belong in `EKVibe`** (`Assets/Scripts/Vibe/EKVibe.cs`) — colours, sizes,
  camera, `ChunkSize`. Prefer adding there over new magic numbers.
- **ScriptableObject create-menu path**: `ExiledAlvaston/Data/...`.
- **Editor menu path**: `Tools/GBA/<Category>/...` — categories `Place`, `Art`, `World`,
  `Debug`, `Repair`, `Content`, plus **`Danger Zone`** reserved exclusively for the four tools
  that overwrite or re-create assets. Nothing destructive may live outside `Danger Zone`.
- **Mobile-first**: hot paths (`Update()`, physics ticks) deliberately avoid allocation —
  preallocated buffers, parallel lists instead of dictionary iteration. Respect this when
  editing those paths.
- Content placement goes through the **World Palette** (`Tools → GBA → World Palette`,
  `Editor/WorldPaletteWindow.cs`): arm a `PlacementPreset`, click in the Scene view.
  `PlacementCategory` is serialized by index — **append only**.

## High-risk areas — read `CLAUDE.md` before touching these

- **Save system** (`Flow/SaveGameManager.cs` — one JSON file written with `JsonUtility` to
  `persistentDataPath/savegame.json`; **not** PlayerPrefs, no `EA_` prefix exists). Saves key
  chunks by
  `ChunkName` string — editing a chunk's `ChunkName` value silently invalidates existing
  saves. `Manor_Cellars_Data` uses `"Manor Cellars"` (with a space); that is a save key, not a
  typo. Saves trigger on chunk-edge crossings, portal travel, new-game start, tutorial
  completion, and `PubInteractable.HaveAPint()` (pubs are the manual save point).
- **Serialized-reference hazards** (CLAUDE.md §7). Renaming public fields, class names, or
  reordering enums breaks Unity serialization **silently**. Enums serialize by index — always
  append. Never rebuild an existing prefab by delete-and-re-save (it mints a fresh GUID and
  orphans scene instances); edit in place via `PrefabUtility.LoadPrefabContents` →
  `SaveAsPrefabAsset`. Never hand-edit or regenerate `.meta` files — GUIDs bind everything.
- **Chunk transitions** (CLAUDE.md §5). Four different code paths instantiate chunks; only
  `ChunkManager.TransitionToChunkRoutine` does the full job (pause, wanted notification,
  autosave, camera snap). To *react* to a chunk change, poll `CurrentChunkData` — it is
  written from seven places, so no hook catches them all.
- **Speed modifiers** are keyed by source (`CombatController.SetSpeedMultiplier` /
  `ClearSpeedMultiplier`); movement reads `EffectiveMovementSpeed`. Never multiply
  `MovementSpeed` in place.
- **Ride state has one owner: `World/MountController`** (CLAUDE.md §11). Never
  `SetActive(false)` a vehicle root — hide `ParkedModel` instead.
- **Never `SetActive(false)` a chunk root either** (CLAUDE.md §5). Verified 2026-08-03, and it
  fails three separate ways at once: `EnemyAI` starts its perception coroutine only in `Start`,
  so a deactivate/reactivate leaves every enemy permanently blind; `RuntimeNavMeshBaker` removes
  its registered mesh only in `OnDestroy`, so an inactive chunk keeps its NavMesh live at the
  shared world origin; and `MagicTutorial`/`TutorialSequence` clear their static `Instance` only
  in `OnDestroy`, so both keep pointing at a disabled object. Suspending a chunk safely needs
  explicit lifecycle hooks, designed in
  `docs/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md` and **not implemented**.

## Working agreement

Multi-agent workflow: **plan → implement → review → merge**, via three subagents defined in
`.claude/agents/`: `architect` (Opus, plans, never edits code), `implementer` (Sonnet, works
strictly from the plan), `reviewer` (Opus, hunts silent failure modes in the diff). Skip the
ceremony for small, low-risk changes; use it for anything touching the high-risk areas above.
Before any rename/refactor touching saves or serialization, produce an explicit mapping table.

⚠️ **Changes made in the Inspector during Play mode are discarded when Play stops.** When
asking for an editor change, say whether Play must be stopped first, and give the UI route
(menu path, which object to select), not just a field name.

## Security and hygiene considerations

- **No Git LFS. A `.gitattributes` does exist** — an earlier version of this line said it did
  not, and that was wrong (CLAUDE.md §9). It is not LFS: it pins `* text=auto` plus an explicit
  binary list, so the repo stores LF while each working tree gets what it wants. That matters
  because Unity rewrites a whole YAML file whenever it touches one, and without it a line-ending
  difference and a real edit are indistinguishable in a 100,000-line diff. A file written by an
  agent can land with the wrong endings in the working tree; it commits identically, but `rm` it
  and `git checkout --` it back to normalise. Binary art blobs committed to git are permanent
  weight — the repo already went 672 MB → 204 MB in `Assets/` by pruning unreachable packs.
  Policy: pull individual sprites in when a system needs them rather than carrying whole
  packs. Reachability is a transitive GUID walk rooted at `c.unity`, `Resources/`, `Editor/`,
  code, `ProjectSettings/`, and hardcoded `"Assets/..."` strings in `.cs` — use
  `Tools/asset_reachability.py`, never a text search. A pack's own demo scene is not a root.
- **Generated art people must be synthetic, not real** — no photographs of real identifiable
  people (likeness rights survive any licence); the cast is fictional anyway.
- No secrets, credentials or network services exist in the project; saves are a single local
  JSON file only.
