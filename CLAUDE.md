# CLAUDE.md — Exiled Alvaston

Guidance for Claude Code sessions in this repo. Written from a codebase audit (2026-07-26),
revised the same day after the consequence mechanics were recovered from a stash and landed,
and again after the mount/vehicle work on `fix/moped-mount-and-melee-flag` (see §9 and §11).
Facts here are verified against code, not against design docs. Where code and a design doc
disagree, this file records **what the code actually does**.

> **§11 is not verified in a running editor.** Everything else in this file was read off code
> that has at least been compiled. The vehicle work has not been — no Unity session has opened
> since it was written. Treat §11 as "what the code says it does", not "what the game does".

> **Stale-brief warning.** An older written brief describes this as a "2D mobile RPG".
> That is out of date. The game is **isometric by design** (confirmed 2026-07-26) and the
> code is correct. Do not treat §2 as a defect to be fixed, and do not act on any doc that
> calls this project 2D.

---

## 1. What this project is

Unity mobile RPG. Working title **Exiled Alvaston** (`ProjectSettings` → `productName`).

**Naming warning — three names are live in the codebase:**

| Name | Where it lives | Notes |
|---|---|---|
| `Exiled Alvaston` | `productName`, root C# namespace, most editor menus | The canonical one |
| `Discover England` | `EKVibe.DisplayTitle`, `DiscoverEnglandSetup.cs` | In-game title shown to player |
| `EK` / Exiled Kingdoms | `EKVibe`, `EKNavMeshBaker` | Refers to the *inspiration* game, not this project |

Do not "unify" these without an explicit task — `DisplayTitle` is player-facing copy,
`EK*` is a deliberate reference to the art/UX target.

## 2. Presentation model — read this before touching movement or combat

**Isometric, by design.** A 3D world rendered with billboarded 2D sprites and a fixed
isometric camera — the Exiled Kingdoms presentation model. This is the intended target,
not a legacy artifact. It is **not** a 2D project.

- 3D physics: `Rigidbody`, `Collider`, `Physics.OverlapSphere` (not `Rigidbody2D`/`Physics2D`)
- Movement is on the **X/Z plane**; `Y` is up. Chunk edges are `pos.x` / `pos.z`.
- Fixed isometric camera (`IsometricCameraFollow`, pitch 30°, yaw -45°, ortho size 7)
- Sprites face camera via `SpriteBillboard`; actors composed by `WorldActorVisual`
- Input is screen-relative (`GetScreenRelativeMoveDirection`), not world-axis

Never introduce `Physics2D` / `Rigidbody2D` / `Vector2` movement here — it will not
interact with any existing collider.

## 3. Folder structure

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
                      #   MountController + VehicleController + VehicleSpawner (§11)
  Editor/             # editor-only tools (no asmdef — see below)
  Data/Chunks/        # 6 MapChunkData .asset files
  Prefabs/Chunks/     # 6 matching chunk prefabs
  Prefabs/ModernBritain/  # police tiers, Nosey Parker, e-bike, pub — see §6
  Resources/Items/    # ItemData loaded by name at runtime (Resources.Load)
  3DModels/, Sprites/, Art/, Animations/, Materials/   # art
  6twelve/            # third-party asset pack (has its own DEMO scene) — not our code
  c.unity             # THE main scene (only scene in build settings)
  c/                  # NavMesh data for c.unity (auto-linked by scene name)
```

**There is one gameplay scene: `Assets/c.unity`.** Everything is built inside it.
Renaming that scene orphans `Assets/c/NavMesh.asset`.

**No `.asmdef` files exist** in project code — everything compiles into
`Assembly-CSharp` / `Assembly-CSharp-Editor`. `Assets/Editor/` is the only thing keeping
editor code out of builds, so editor-only code **must** live there.

## 4. Conventions

- **Namespaces mirror folders**: `ExiledAlvaston.World`, `ExiledAlvaston.Combat`, etc.
  This is consistent across every file — keep it that way.
- **Public fields, PascalCase**, for anything Unity serializes (`CurrentKnives`, `ChunkPrefab`)
- **Private fields `_camelCase`** (`_isTransitioning`, `_hitThisSwing`)
- **Singletons**: `public static X Instance { get; private set; }` set in `Awake`.
  Used by `ChunkManager`, `CombatController`, `UIManager`, `WantedManager`,
  `GameFlowController`, `PlayerSession`, `QuestManager`, `DeathScreenUI`.
  Access pattern is `X.Instance ?? FindObjectOfType<X>()`.
- **Tuning constants belong in `EKVibe`** (`Assets/Scripts/Vibe/EKVibe.cs`) — colours,
  sizes, camera, `ChunkSize`. Prefer adding there over new magic numbers.
- **ScriptableObject menu path**: `ExiledAlvaston/Data/...`
- **Editor menu path**: `Tools/GBA/<Category>/...`. All 27 items live under this root, in six
  categories: `Place`, `Art`, `World`, `Debug`, `Repair`, `Content`, plus **`Danger Zone`** for
  the four tools that overwrite or re-create assets — `Build Modern Britain Prefabs`,
  `Build Enemy Prefabs`, `Discover England Bootstrap` and `Generate Placeholder Art`. Each of
  those confirms first and names what it destroys. Nothing else may go in `Danger Zone`, and
  nothing destructive may go anywhere else.
- Mobile-first: hot paths avoid allocation deliberately (preallocated
  `Collider[] _hitResults`, parallel key lists to avoid dictionary-iteration garbage).
  Respect this when editing `Update()` paths.

## 5. The chunk world system

Discrete chunks, **220×220 units** (`EKVibe.ChunkSize = 220f`). One chunk is live at a time.

- `MapChunkData` (ScriptableObject) holds `ChunkName`, `Coordinates`, `IsCity`,
  `ChunkPrefab`, and **explicit `NorthChunk`/`SouthChunk`/`EastChunk`/`WestChunk` references**.
  Adjacency is authored by reference, *not* computed from `Coordinates` — `Coordinates`
  is only used as a dictionary key for city lockout timers.
- `ChunkEdge` (BoxCollider trigger at a chunk boundary) → `ChunkManager.OnPlayerHitEdge(dir)`
- `ChunkManager.TransitionToChunkRoutine` is the **canonical** transition: pauses, instantiates
  the new chunk *before* destroying the old, repositions the player to the opposite edge
  (12-unit buffer), snaps the camera, and autosaves.

**Four different code paths instantiate chunks.** Only the first does the full job:

| Path | Entry point | Pauses | Notifies Wanted | Autosaves | Snaps camera |
|---|---|---|---|---|---|
| Edge crossing | `ChunkManager.TransitionToChunkRoutine` | yes | yes | yes | yes |
| Interior door | `ChunkTransitionDoor.OnTriggerEnter` | no | no | no | no |
| Instance door | `GameFlowController.EnterManorCellars` | no | no | no | no |
| Tutorial exit | `GameFlowController.LoadLondonAtWestGates` | no | no | no | no |

If you add or change transition behaviour, you must touch all four or consolidate them.

**If you need to *react* to a chunk change, poll — do not hook a transition.** `CurrentChunkData`
is a public serialized field written from **seven** places across six files: both `ChunkManager`
routines, `GameFlowController` ×2, `SaveGameManager`, `DeathScreenUI`, and two editor tools. Any
one hook misses the other paths, and turning the field into a property to raise an event would
stop Unity serialising the scene's authored starting chunk. `VehicleSpawner` and
`VehicleController` both compare against a remembered reference instead — cheap, and it catches
load-game and the arrest return for free. Watch `CurrentChunkInstance` too if a reload of the
*same* chunk matters to you (dying in Home_Alvaston and respawning into it).

Current chunks: `Home_Alvaston` (0,0 — the "London" hub, `IsCity: 1`), `North_Wasteland`,
`South_Slums`, `East_RetailPark`, `West_Canal`, `Manor_Cellars` (tutorial dungeon, reached
by `InstanceDoor`, not by edge). Outer chunks link back to Home only — their other three
directions are null and walking into them silently does nothing.

Two live defects here, both still open:
- **Dead-end edges give no feedback.** `OnPlayerHitEdge` returns silently when the adjacent
  chunk is null, so the player walks into nothing and nothing happens — no wall, no message.
- **`Manor_Cellars` and `West_Canal` both claim `Coordinates (-1, 0)`.** Harmless today
  because city lockout only keys on `IsCity` chunks, latent if either becomes one.

## 6. Save system — highest-risk area in the repo

`Assets/Scripts/Flow/SaveGameManager.cs`. PlayerPrefs, keys prefixed `EA_`.
Saves: chunk name, position, health, mana, stamina.

Two triggers write a save: every chunk edge crossing, and `PubInteractable.HaveAPint()`.
Pubs are therefore the deliberate manual save point — see §9.

**The save stores `MapChunkData.ChunkName` as a string** and resolves it on load via
`ChunkManager.FindChunkByName` against the `ChunkManager.AllChunks` array.

Consequences to respect:
- Editing the `ChunkName` **value** in any `Assets/Data/Chunks/*.asset` invalidates existing
  saves. `Load()` returns `false` and "Load Last Game" silently fails — no error surfaced.
- A chunk missing from the `AllChunks` array is unloadable even if it exists.
- `Manor_Cellars_Data` has `ChunkName: "Manor Cellars"` (space) while every other chunk uses
  underscores. Do not "normalise" this casually — it is a save key.

**Not saved:** `PlayerSession.TutorialComplete`, quest state, inventory, wanted level, and
whether you are riding anything (§11 — a load puts you on foot with vehicles back at their
authored spots, and a vehicle you had already nicked is nickable again).
`PlayerSession` is `DontDestroyOnLoad` (memory only) so tutorial state resets on app restart
while the position save survives — gates keyed off `TutorialComplete` will re-lock.

## 7. Serialized-reference hazards

Renaming these breaks Unity serialization silently (fields go null / enums shift):

- **Public serialized field names** — Unity matches by name. Renaming any public field on a
  `MonoBehaviour`/`ScriptableObject` drops its value in every prefab, scene and `.asset`
  unless you add `[FormerlySerializedAs]`.
- **Class names** — the `.cs` filename must match the `MonoBehaviour` class name, and script
  GUIDs in `.meta` files bind prefabs/scene to the script. Rename via Unity, not the filesystem.
- **Enums are serialized by integer index.** Reordering or inserting values silently remaps
  existing data. Live enums: `Direction`, `AbilityResourceType`, `ItemType`, `PlayerClass`,
  `GameFlowState`, `HUDActionButton.ActionKind`, `InstanceDoor.Destination`. Always append.
- **`Assets/Data/Chunks/*.asset` reference each other by GUID** for adjacency. Deleting or
  regenerating a `.meta` breaks the adjacency graph.
- ⚠️ **Never rebuild an existing prefab by deleting and re-saving it.**
  `ModernBritainSetup.BuildEBikePrefab` does `AssetDatabase.DeleteAsset(path)` then
  `SaveAsPrefabAsset`. That takes the `.meta` with it and mints a fresh GUID, so **re-running
  that tool orphans the EBike, Nosey Parker and Pub instances already placed in `c.unity`** —
  they detach silently and the scene keeps empty prefab stubs. To change an existing prefab,
  edit it in place: `PrefabUtility.LoadPrefabContents` → modify → `SaveAsPrefabAsset` →
  `UnloadPrefabContents`, which overwrites without touching the `.meta`. `ArtImportTool` is
  the worked example.
- **Appending a serialized field is safe; inserting is not.** `MapChunkData.VehicleSpawns` was
  added after the adjacency block for this reason — existing `.asset` files carry no value for
  it and Unity reads an empty list, which is the correct default.

## 8. The consequence systems (the GTA layer)

All five are implemented and wired — components live inside the `Prefabs/ModernBritain/`
prefabs, whose instances are placed in `c.unity`. `Editor/ModernBritainSetup.cs` is the tool
that generates and wires this content; the scene already holds its output, so you do not need
to run it to have a working game.

**`WantedManager` (`Systems/`) is the hub.** Two coupled meters:

- **Knives** (0–5) — the wanted level. `SpikeKnives()` raises it and calls `SpawnPlod()`,
  which instantiates `PolicePrefabs[Knives-1]` near the player. All five tiers are assigned
  in the scene: PCSO → Bobby → Armed Response → Occult Agent → Occult Commander.
- **Concealment** (0–100) — regenerates at `ConcealmentRecoveryRate`/sec.
  `DrainConcealment(amount)` lowers it; hitting zero resets it to full and spikes Knives.

**Casting magic is the trigger.** `CombatController` calls `DrainConcealment(34f)` on spell
cast — three spells busts you. This is the design's "magic stands in for GTA's guns", and it
is the single most load-bearing line in the whole consequence loop.

| System | Script | Behaviour |
|---|---|---|
| Nosey Parkers | `AI/NoseyParkerAI` | Civilians. Within `DetectionRadius`, if concealment is below max, they spend `ReportTime` dialling 999, then `SpikeKnives()`. |
| Stealth | `World/StealthController` | Crouch toggle: halves move speed, halves parker detection radius. |
| Pickpocketing | `World/PickpocketInteractable` | Requires crouch. Rolls `CatchChance`; failure spikes Knives. |
| Grand Theft E-Bike | `World/VehicleController` + `World/MountController` | Mounting an `IsOwnedByNPC` vehicle spikes Knives and grants `SpeedMultiplier`. See §11 — ride state, dismounting and spawning all changed. |
| Pub safehouses | `World/PubInteractable` | A pint clears Knives + concealment, heals, and saves. |
| Arrest | `Flow/GameFlowController.ArrestRoutine` | Death dealt by an `EnemyAI.IsPolice` attacker (tracked via `Health.LastAttacker`) arrests instead of killing: clears wanted level, despawns police, returns you to the cellars. |

### Known issues in these systems (verified, all open)

- **Stealth is keyboard-only.** `StealthController.Update` reads `Input.GetKeyDown(KeyCode.C)`,
  with its own comment noting mobile needs a UI button. On a touchscreen-first game this makes
  stealth unreachable — and since `TryPickpocket` requires `IsCrouched`, **pickpocketing is
  unreachable on mobile too.** It also means the crouch-plus-vehicle composition that §11's
  modifier stack exists to handle cannot be exercised on a device at all.
- **The ModernBritain props are in every chunk.** `NoseyParker` and `Pub_TheWinchester` are
  scene-root instances in `c.unity` (`m_TransformParent: {fileID: 0}`), and every chunk is
  instantiated at `Vector3.zero`, so both stand at the same world coordinates in all six chunks.
  The parker reports you in the wasteland; the pub — the only manual save point — follows you
  everywhere. The e-bike had this too and was fixed by §11's spawner; these two have not been.
- ~~**`MovementSpeed` has no single owner.**~~ **Fixed** (`a6b387e`, on `main`). Modifiers are
  keyed by source via `CombatController.SetSpeedMultiplier` / `ClearSpeedMultiplier`, and
  movement reads `EffectiveMovementSpeed`. `MovementSpeed` is now a read-only base — never
  multiply it in place again. ~~`VehicleController` has no `Unmount`~~ — see §11.
- **Nosey Parkers fire on any concealment below max.** One cast drains 34 with 5/sec regen, so
  every cast opens a ~7-second window in which every parker in range starts reporting. Each
  parker also sets `this.enabled = false` after reporting (the comment says "run away", but it
  only stops), making them single-use per scene load.
- **Two rewards are TODOs.** Pickpocketed gold and the £50 arrest fine are toasts only —
  neither touches inventory, because raw gold tracking does not exist yet.
- `AbilityData` still has no "is magic" flag — the drain is hardcoded in `CombatController`
  rather than driven by ability data.
- `TagManager.asset` still has `tags: []` and no custom layers. Nothing currently needs them
  (the old `LayerMask.GetMask("Police")` path is gone), but do not assume a layer exists.

## 9. Git / repo hygiene

- `main` now contains the quest-placement work (PR #1), the §8 consequence mechanics (PR #2),
  and `archive/stash-mechanics` (PR #3).
- `archive/stash-mechanics` pinned the stash the §8 work was recovered from. Merging it into
  `main` was unnecessary — everything in it had already landed via PR #2 — but it did no harm:
  nothing was resurrected and no file diverged. Because it is now an ancestor of `main`, the
  stash commit is permanently reachable and **the branch itself is safe to delete.**
- **`fix/moped-mount-and-melee-flag` is merged into `main`** (the melee-flag fix and all of §11),
  along with the art pipeline in §12. The branch is safe to delete.
- ⚠️ **`4b93ccc` on `feat/quest-placement-tools-and-mosley-quest` is NOT merged.** It holds one
  fix worth keeping — a `PauseManager.IsPaused` guard in `CombatController.Update` that stops
  spell/attack input firing through open menus — tangled together with 1,789 craftpix renames
  that would resurrect the deleted sprite folder. Cherry-pick the fix; do not merge the branch.
- `Assets/` is ~672 MB with `.psd`/`.fbx`/`.glb`/`.aseprite` committed and **no Git LFS**
  (no `.gitattributes`). Pruning will not shrink `.git` — history keeps the blobs.
### Asset pruning — how it was done, and how to redo it

`Assets/` went **672 MB → 204 MB**. Two passes: the craftpix packs, then 22 packs with zero
reachable assets (3,815 files, 286 MB).

Reachability is a **transitive GUID walk**, not a text search. Roots are:

- the build scene (`Assets/c.unity`)
- everything under `Resources/` — loaded by name at runtime (`Resources.LoadAll<ItemData>("Items")`),
  so it is never GUID-reachable
- everything under `Editor/` and `StreamingAssets/`
- all `.cs` / `.asmdef` / `.dll` — code is not GUID-reachable either
- GUIDs referenced from `ProjectSettings/`
- **hardcoded `"Assets/…"` strings inside `.cs`** — the editor tools pass literal paths to
  `AssetDatabase.LoadAssetAtPath` (e.g. `Assets/Art/Placeholders/mat_dungeon_wall.mat`).
  Miss these and you delete the tooling's dependencies.

Then verify: every unresolved GUID left in `c.unity` must be one that was *already* unresolved
before the deletion. There are 17 such built-in Unity GUIDs; that is the expected baseline, not
a defect.

**Delete whole packs only where the reachable count is zero.** Partially used packs must be
trimmed per-file or left alone. The remaining opportunities, all partial:

| Pack | Used / total | Size |
|---|---|---|
| `psx urban pack` | 10 / 1009 | 105 MB |
| `Animated Chest` | 6 / 7 | 46 MB — one decorative prop, see below |
| `retro_house_pack` | 6 / 69 | 36 MB |

⚠️ An earlier ad-hoc check wrongly reported `Assets/6twelve/` as heavily used. It was counting
the pack's own `DEMO.unity` referencing its own textures. **A pack's own demo scene is not a
root** — exclude it, or every pack looks used.
- **`Assets/3DModels/Sprites/` was deleted** (1,998 files, 454 MB — the craftpix packs), after
  verifying zero of its 2,123 assets were referenced. Policy going forward: **pull individual
  sprites in when a system needs them, rather than carrying whole packs speculatively.**
  Recoverable from history; note `.git` still carries the blobs.
- ⚠️ **Merge hazard:** `feat/quest-placement-tools-and-mosley-quest` (`4b93ccc`) *renamed* 1,789
  of those craftpix files rather than deleting them. Merging that branch after the deletion can
  resurrect the whole folder via git's rename detection. Check `3DModels/Sprites/` is still
  absent after any merge involving that branch.
- The five loose fantasy art packs (Bringer Of Death, EVil Wizard, Medieval Warrior Pack 1–2,
  Monsters Creatures Fantasy) were deleted — never committed, effectively unreferenced.
- **Reference integrity is clean.** A full pass over every tracked `.unity`/`.prefab`/`.asset`/
  `.mat`/`.controller`/`.anim` found exactly one dangling reference (`Animated Chest`), now
  fixed. Nothing tracked points at anything missing. Re-run that check before the repo move.
- **Biggest remaining trim: `Assets/3DModels/Animated Chest` — 45 MB for one decorative prop**,
  almost all uncompressed TGA. It is committed only because `c.unity` references its
  `Chest.prefab`. Delete the chest instance in the Unity editor and the whole pack goes with it.
  Next largest unreferenced: `psx urban pack` (105 MB), `Characters_psx` (54 MB),
  `Magic+atk animations` (50 MB).
- One tracked `__MACOSX` junk file remains.

## 10. Working agreement

Multi-agent workflow: **plan → implement → review → merge.**

Three agents are defined in `.claude/agents/`. Invoke them by name.

| Agent | Model | Role |
|---|---|---|
| `architect` | Opus | Scopes, produces the plan and mapping table, flags structural risk. **Never edits code.** |
| `implementer` | Sonnet | Works strictly from the plan. Small single-concern commits. No scope improvisation. |
| `reviewer` | Opus | Reviews the diff against the plan, hunting silent failure modes — not style. |

Typical use: *"use the architect subagent to plan X"* → approve the plan → *"use the implementer
subagent to execute it"* → *"use the reviewer subagent to review the diff against the plan"*.

Skip the ceremony for genuinely small, low-risk changes. It exists for anything touching §5–§7.

Before any rename/refactor touching §6 or §7, produce an explicit mapping table first.

### Verification — read this before claiming something works

There is **no test framework in this project.** A "test" step cannot be automated yet, which is
why the third agent is a reviewer rather than a tester. What *can* be checked mechanically:

```
python Tools/asset_reachability.py --check-dangling   # reference integrity; exits 1 on breakage
python Tools/asset_reachability.py --packs            # which asset packs are fully unused
```

`--check-dangling` knows the build scene's built-in baseline (17 unresolved GUIDs) and fails only
above it. Run it before and after anything that deletes, moves or renames assets.

Everything else — does the scene load, is anything pink, do the mechanics behave — needs the
Unity editor and therefore needs a human. Say so plainly rather than implying otherwise.

⚠️ **Changes made in the Inspector while Play mode is running are discarded when it stops.** This
has wasted real time: a value is tuned in play, it looks right, play stops, the old value returns,
the scene is saved over the top. When asking for an editor change, say whether Play must be
stopped first. Give the route through the UI as well as the field name — panel, menu path, which
object to select — not just what to set.

**There is no C# compiler in the agent environment either.** Reference integrity passing says
nothing about whether the project builds. Anything written without a Unity session is unverified
in both senses; §11 is the current example.

A rename to **GBA: England** (Great British Annals) is under consideration. Notes if it
proceeds: the `ExiledAlvaston` namespace appears in 46 `.cs` files and **zero serialized
assets**, so a namespace rename is safe — Unity binds scripts by `.meta` GUID, not type name.
What is *not* safe is `Home_Alvaston`, which is a `ChunkName` and therefore a save key (§6).
A colon is illegal in Windows paths and git repo names, so any repo/folder would be
`gba-england` with `GBA: England` only as a display string.

---

## 11. Mounts and vehicles

Merged to `main`, compiled, and play-tested in the editor: mounting, dismounting, the boost, the
prompt flip and the visuals all work. The **data-driven spawner path is not yet exercised** — the
scene still holds a hand-placed vehicle instance and no chunk has a `VehicleSpawns` entry.

The stealable vehicle is a **hire e-bike** ("Limey E-Bike"). It was a Deliveroo moped until
`EBike.prefab` was renamed; if you find "moped" in a comment it is describing history.

**Ride state has one owner: `World/MountController`.** It holds `CurrentVehicle`;
`VehicleController` describes a vehicle and applies its own effects when told to. Nothing places
the component — `MountController.Get()` attaches it to the `CombatController` GameObject on first
use. Use `MountController.Current` (non-creating) inside `OnDisable`/`OnDestroy`; `AddComponent`
during teardown is illegal.

| Piece | Script | What it does |
|---|---|---|
| Ride state | `World/MountController` | `Mount` / `Dismount` / `ForgetVehicle`. `IsPlayerRiding` is the cheap static read. |
| The vehicle | `World/VehicleController` | `Toggle` (the interact entry point), effects, prompt, homing. |
| Spawning | `World/VehicleSpawner` | Reads `MapChunkData.VehicleSpawns`, parents instances to the live chunk. Self-bootstraps via `RuntimeInitializeOnLoadMethod`. |
| Definition | `Data/VehicleData` | Name, speed multiplier, nickable, prompt, sprite, parked height. |

**Two ownership models, deliberately separate.** A vehicle spawned by `VehicleSpawner` is
*chunk-owned*: it dies with its chunk and is respawned at its authored spot next visit, so it
needs no homing. It unparents on mount (so riding across an edge cannot destroy it under you) and
rejoins whichever chunk you abandon it in. A vehicle hand-placed in the scene is *not*
chunk-owned and uses `ReturnsHomeOnChunkChange` + `ReturnHome` instead. Do not merge these.

**Things that will catch you out:**

- **Never `SetActive(false)` a vehicle root** to hide it. `OnDisable` clears the speed multiplier,
  so the vehicle would cancel its own boost the instant it was mounted. Hide `ParkedModel`.
- **A mounted vehicle rides at distance zero**, so it wins `PlayerInteractor.FindClosest` on
  distance every time. `Interactable.LowPriority` is what stops it masking pubs, doors and NPCs;
  the mounted vehicle sets it.
- **`PlayerInteractor` compares the prompt string, not just the target.** An interactable that
  rewrites its own `Prompt` without the closest one changing — which is exactly what mounting
  does — would otherwise leave the HUD stale.
- **`VehicleSpawner` tracks what each spawn entry produced.** Without that, riding a chunk's
  vehicle out and back mints a second one from the same entry, once per round trip.
- **The player must not gain a stray `SpriteRenderer` lookup.** `WorldActorVisual.ActorRenderer`
  exists because `GetComponentInChildren<SpriteRenderer>()` starts returning the layered vehicle
  sprite once one exists — `StealthController`'s crouch tint used to do exactly that.
- **`MountedSprite` is superseded by the `cycle` sheet.** It writes `_sr.sprite`, which an Animator
  overwrites every frame — the player's Animator sits on `SwingRoot` with a controller assigned, so
  `WorldActorVisual` suspends it while a `MountedSprite` shows. Now that riding has an animated
  `Cycle` state, prefer a `cycle` sheet: it animates, and it needs no per-character rider art.
- **Nicking does not persist**, by decision. `IsOwnedByNPC` is cleared on the instance, and the
  instance is replaced when the chunk reloads — so you re-nick and re-spike on every visit.
  Consistent with §6, where wanted level and inventory are not saved either.

**Still open, to move off the hand-placed instance:**

1. Create a `VehicleData` (`Assets > Create > ExiledAlvaston > Data > Vehicle Data`), set
   `ChassisPrefab` to `EBike.prefab`. An earlier attempt left `Home_Alvaston_Data` pointing at one
   that was never written to disk — check the asset exists before trusting a spawn entry.
2. `Tools → GBA → Place → Vehicle Placement` — add it to `Home_Alvaston_Data`.
3. **Delete the EBike instance at the root of `c.unity`**, or the hand-placed every-chunk one and
   the spawned one both exist.

`EBike.prefab` currently has **no sprite assigned** — the code-generated placeholder was deleted
with the rename, and the art comes from §12 instead.

---

## 12. Generated art pipeline

Art is produced by a **second agent** (Antigravity/Gemini) and imported by a Unity tool. The
contract is `AGENTS.md` (hard rules) and `ART_PIPELINE.md` (the spec and the request list).
`GEMINI.md` is a pointer to those, not a copy.

- The art agent writes **PNG + sidecar JSON to `art_incoming/`, and nothing else** — never inside
  `Assets/`, never a `.meta`, never git. `art_incoming/` is gitignored apart from its README.
- `Tools → GBA → Art → Import Generated Art` (`Editor/ArtImportTool.cs`) does the rest:
  keys out the backdrop, trims, reduces, sets import settings, slices sheets, builds clips and an
  `AnimatorController`, then assigns known assets to what was waiting for them.

**The art direction is a post-process, not a prompt.** Sources arrive photoreal and large; the
importer area-averages them down to **48 px per world unit**, so a 1.35-unit character lands near
65 px — digitised-sprite style. This is deliberate: asking a generator for low resolution produces
a different fake pixel grid every time, whereas a deterministic reduction treats every asset
identically however far apart they were generated. Filtering is **Point**.

Things learned the hard way, every one of them encoded in the tool rather than asked for in a
prompt. Do not undo these to simplify the code — each cost a wasted generation cycle:

- **Chroma key, globally, and unmix the edges.** Generators are unreliable at emitting real alpha
  and reliable at putting a subject on a plain backdrop, so the contract asks for flat magenta
  `#FF00FF`. A threshold alone is not enough: anti-aliased edges are a blend of backdrop and
  subject, and once averaged down they dominate thin structures — a bike arrived with magenta
  spokes. Partial pixels are unmixed via `P = a·S + (1−a)·K`. Keying is global, not flood-filled
  from the border, so backdrop trapped inside the subject goes too.
- **Trim in the tool, never in the prompt.** Sizing derives from full image height, so untrimmed
  art silently renders small.
- **Reduction is area-averaged**, not nearest-neighbour — point sampling a photograph down to 65 px
  is aliased noise. Colour is weighted by alpha through the average or edges get a dark halo.
- **Sheets are never trimmed**: it would shift every cell off the grid.
- **Sheets are checked for a shared baseline.** A figure that drifts up its cell between frames
  bobs in motion while looking fine frame by frame. Refused above 2 px at final size.
- **Sheets of one subject are checked against each other.** Each can be internally perfect and
  still disagree — a walk drawn near edge-on was 47 px wide against the idle sheet's 122. Refused
  above 1.4× on width or 1.15× on height.
- ⚠️ **Never wrap the import loop in `AssetDatabase.StartAssetEditing`.** It defers `ImportAsset`,
  so `AssetImporter.GetAtPath` returns null for a file just written, every import setting is
  skipped, and assets land with Unity's defaults — no slices, no clips, no controller — while
  appearing to succeed. This cost a full round trip once already.

### Actor sprite sizing — two traps that cost a cycle each

- **Resize an actor with `WorldActorVisual.Height`, never by scaling its `ActorVisual` child.**
  `ApplyVisual` positions that child at `Height / 2` — the sprite's centre — assuming its scale is
  1. Scaling it grows the sprite about that centre and buries the feet below the floor.
  `GroundOffset` is there for the small art-dependent nudge, not for resizing.
- **`FitScaleToHeight` refits in `LateUpdate` whenever the displayed sprite changes, and must
  keep doing so.** It divides the target height by the sprite's *bounds*, and an Animator swaps
  `m_Sprite` for frames whose pixel size and import PPU differ from whatever `ActorSprite` holds.
  Fitting once at Awake against a stale 48 px @ PPU 100 placeholder, then animating 65 px @ PPU 48
  frames, rendered the player at 4.5 units instead of 1.6 with the bottom 1.46 units underground.
  The giveaway is that it looks correct the instant any Inspector field is touched, because
  `OnValidate` refits against the sprite actually showing. It is a reference compare per frame.

Frame counts are deliberately low (4-frame walks). Every extra frame is another chance for the
figure to drift, and at 65 px the difference is barely visible.

The generated controller defines `Speed`, `MeleeAttack`, `Hit`, `Death`, `CastSpell` and a
`Cycling` bool. `CastSpell` is the one nothing else in the project defines, which is the console
error noted in §8. `Cycling` holds a `Cycle` state for as long as the player is riding — see §11.
Once a subject's sheets import, the tool points the player's Animator at the controller it built;
without that the sheets would import and the player would carry on playing `Bandit_Controller`.

`Assets/Sprites/Enemies` is the old craftpix content: 64×64 pixel art imported at PPU 100 with
**bilinear** filtering, which is why it looks mushy. It predates all of this and is not the
reference style.

### Where the art stands

Delivered and in the game:

- `spr_vehicle_ebike` — the hire e-bike, wired into `EBike.prefab`.
- `sheet_char_player_idle` (4 frames) and `sheet_char_player_walk` (4 frames) — sliced, clipped,
  and driving `player_Controller`, which is assigned to the player's Animator in place of
  `Bandit_Controller`. The player is `Height 1.6`, `GroundOffset 0`, `ActorVisual` scale 1.

Requested but not yet generated, all specced in `ART_PIPELINE.md` §7: the player's `attack`,
`cast`, `hurt`, `death` and `cycle` sheets; the five NPCs in §7.3 (Councillor Mosley, Daniel
Pauls, the tracksuit geezer, the angry squirrel, the roaming pharmacist); the office block and
shed in §7.4.

Not yet solved: those NPCs are spawned in code by `MagicTutorial`, which assigns a single `Sprite`
rather than an `AnimatorController`. Animated NPCs need that changed before their sheets are
worth generating.
