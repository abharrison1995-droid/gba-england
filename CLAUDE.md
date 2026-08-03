# CLAUDE.md — Exiled Alvaston

Guidance for Claude Code sessions in this repo. Written from a codebase audit (2026-07-26),
revised the same day after the consequence mechanics were recovered from a stash and landed,
again after the mount/vehicle work on `fix/moped-mount-and-melee-flag` (see §9 and §11), and
again on 2026-07-28 for the chunk-edge, tooling and World Palette work on
`fix/chunk-edges-and-tooling` (§5, §4, §9b, §12), and again on 2026-07-29 for the NPC pipeline on
`feat/npc-preset-pipeline` (**§13**, plus §5, §9, §9b, §11 and §12 where that work closed items
they had open), and again the same day on `docs/art-brief-and-queue` for the art brief (§11 and
§12 — the `cycle` sheet is cancelled and the rejected player sheets have been measured) and
`fix/scene-root-props` for the scene-root props (§8, §9b, §11 — all verified in the
editor) and `feat/crouch-button` for the mobile crouch toggle (§7, §8), and
`feat/pickpocket-preset` for preset-authored marks (§8, §13), and again on 2026-07-30 on
`feat/london-cast-and-region-palette` for the region split and the London cast (§9, §9b, §13), and
again on 2026-08-02 on `feat/quest-definitions` for data-authored quests (**§14**, plus §6, §8 and
§9). Facts here are verified against code, not against design docs. Where code and a design doc
disagree, this file records **what the code actually does**.

> ⚠️ **§13 is partly exercised as of 2026-07-30 — the NPC path works, the tutorial path does not
> yet.** `Assets/Resources/PlacementPresetLibrary.asset` exists and binds to the pinned script
> GUID, so `PlacementPresetLibrary.Get` resolves.
>
> **Exercised, end to end and reported working by the owner:** the `villager` subject went art →
> importer → `Preset_Villager` auto-wired (controller, sprite, icon, `NpcHeight` inherited as
> 1.35) → World Palette → two `NPC_Villager` instances standing in `Home_London_Prefab`. That is
> `PlacementPreset` → `PlacementBuilders` → `NpcFactory` in full, plus `AutoAssign`. He is
> authored as a talker (`Pickpocketable: 0`, prompt "Talk to Villager") and `Roams: 1`.
>
> **Still unexercised:** the tutorial's preset-built cast (`MagicTutorial`, Daniel Pauls and the
> geezer). ⚠️ **Correction (2026-08-03): both now have art** — `Preset_DanielPauls` and
> `Preset_TracksuitGeezer` both carry resolved `NpcSprite`/`NpcController` references, so "neither
> subject's art exists yet" is stale. What's still unexercised is anything keyed off
> `EnemyAI.Animator` being set from a preset-built NPC.
>
> Everything before §13 **has** been exercised: `fix/chunk-edges-and-tooling` is merged, the
> boundary walls are generated and committed, the hardened importer has done a real round trip
> (Mosley and the pharmacist), and the World Palette has authored live content into
> `Home_London_Prefab`.

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
- **Editor menu path**: `Tools/GBA/<Category>/...`. **30 of the 32 menu items** live under this
  root; the two that do not are right-click items, `CONTEXT/PlacementPreset/Create Dialogue` and
  `CONTEXT/DialogueData/Validate This Conversation`. The `Tools/GBA/` ones are in six
  categories: `Place`, `Art`, `World`, `Debug`, `Repair`, `Content`, plus **`Danger Zone`** for
  the four tools that overwrite or re-create assets — `Build Modern Britain Prefabs`,
  `Build Enemy Prefabs`, `Discover England Bootstrap` and `Generate Placeholder Art`. Each of
  those confirms first and names what it destroys. Nothing else may go in `Danger Zone`, and
  nothing destructive may go anywhere else. **`World Palette` is the one exception to the
  category rule** — it sits directly at `Tools/GBA/World Palette`, uncategorised, because it is
  the entry point rather than one tool among many (§9b).
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

**Six code paths instantiate chunks. Two do the full job; four are direct replacements.**
Re-verified line by line on 2026-08-03 — an earlier version of this table listed four paths, named
a class that does not exist, and got two autosave columns wrong:

| Path | Entry point | Pauses | Notifies Wanted | Autosaves | Snaps camera |
|---|---|---|---|---|---|
| Edge crossing | `ChunkManager.TransitionToChunkRoutine` | yes | yes | yes | yes |
| USE door / portal | `DungeonPortal` → `ChunkManager.TravelTo` → `TravelRoutine` | yes | yes | yes | yes |
| Manor instance door | `GameFlowController.EnterManorCellars` | no | no | **yes** | no |
| Tutorial exit | `GameFlowController.LoadLondonAtWestGates` | no | no | **yes** | no |
| Continue / load | `SaveGameManager.LoadWorld` | no | no | no | no |
| New-game fallback | `DeathScreenUI.OnNewGame` | no | no | no | no |

⚠️ **There is no `ChunkTransitionDoor` in this repository.** Earlier documentation named it as the
"interior door" path; no such source file exists. The generic USE-driven door is `DungeonPortal`,
which adds its own `Interactable` if one is missing and routes through `TravelRoutine` — and that
routine does the *same* full lifecycle as an edge crossing, so it is a second canonical path, not
a shortcut. It is the closest thing to a working model for a building door (§5's suspension
subsection, and `docs/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md`).

`EnterManorCellars` and `LoadLondonAtWestGates` both call `SaveGameManager.Save()` even though
they skip everything else — they are the two `GameFlowController` checkpoints §6 counts.

If you add or change transition behaviour you must touch all six, or consolidate them first.

⚠️ **`Home_London_Prefab` contains a `Portal_Home_London` whose `TargetChunk` is
`Home_London_Data` itself** (verified: both resolve to guid `5a35b572…`). Using it reloads and
resets Home. It is an authoring trap, not an example to copy.

**If you need to *react* to a chunk change, poll — do not hook a transition.** `CurrentChunkData`
is a public serialized field written from **seven** places across six files: both `ChunkManager`
routines, `GameFlowController` ×2, `SaveGameManager`, `DeathScreenUI`, and two editor tools. Any
one hook misses the other paths, and turning the field into a property to raise an event would
stop Unity serialising the scene's authored starting chunk. `VehicleSpawner` and
`VehicleController` both compare against a remembered reference instead — cheap, and it catches
load-game and the arrest return for free. Watch `CurrentChunkInstance` too if a reload of the
*same* chunk matters to you (dying in Home_London and respawning into it).

Current chunks: `Home_London` (0,0 — the "London" hub, `IsCity: 1`), `North_Wasteland`,
`South_Slums`, `East_RetailPark`, `West_Canal`, `Manor_Cellars` (tutorial dungeon, reached
by `InstanceDoor`, not by edge). Outer chunks link back to Home only — their other three
directions are null.

### Edge crossings — how they fail, and what now catches it

The prefab and adjacency data are correct: all six chunk prefabs carry all four `ChunkEdge`
triggers at ±109 (2 units deep, `IsTrigger`), and every outer chunk links back to Home. The
failures were all behavioural, and all had the same shape — **`OnPlayerHitEdge` declines a
crossing and the trigger never fires again.** `ChunkEdge` only had `OnTriggerEnter`, the trigger
is 2 units deep, and the ground stops at ±110, so a declined crossing walked the player off the
world with no kill floor.

Fixed (all unverified in a running editor — see §10):

- `ChunkEdge` re-offers the crossing from **`OnTriggerStay`** as well as Enter. The manager's
  `_isTransitioning` and grace-window guards dedupe, and arrival always lands 12 units clear, so
  it cannot ping-pong. **Do not add a `Debug.Log` back to that path** — it fires every physics tick.
- **Arrivals clamp the lateral axis too.** `RepositionPlayerForTransition` used to preserve the
  crossing's lateral coordinate, so crossing near a corner landed the player inside the new
  chunk's *perpendicular* edge trigger.
- The post-arrival grace is **0.25s**, not 1s. A full second ate the return trip if you turned
  straight around after a crossing.
- Dead ends call `ShowWarning("There's nothing that way.")`, throttled — `OnTriggerStay` would
  otherwise re-show it every tick.
- **`ChunkBoundaryWallTool`** (`Tools/GBA/World/Add Chunk Boundary Walls`) puts invisible solid
  walls on all four sides of all six chunk prefabs. Where a neighbour exists the teleport at 109
  fires first, so they are inert; where the crossing is declined you bump a wall. Idempotent, and
  it edits prefabs in place, so re-running is safe. **It has been run** — every chunk prefab
  carries `BoundaryWall_North/South/East/West`, committed in `a27d25a`.
- `ChunkManager.Update` teleports anyone below `y = -20` to the chunk's default `PlayerSpawnPoint`,
  falling back to the origin. It used to always use the origin, which stops being a recovery once
  a chunk has buildings near the middle.

`Manor_Cellars` was moved to `Coordinates (-1, -1)`; it used to collide with `West_Canal`'s
`(-1, 0)`. All six are now unique. `Coordinates` is **not** a save key — only `ChunkName` is (§6)
— so it was safe to edit.

### ⚠️ A chunk root cannot be suspended with `SetActive(false)`

Chunks are currently only ever **destroyed**, never suspended, and the code reflects that. If you
are tempted to keep one alive in the background — for a building interior, a cached location, or
anything else — a bare `SetActive(false)` on the root breaks four systems at once. **All of these
were verified against the code on 2026-08-03**, so this is a description, not a caution:

| System | Cleans up in | What a deactivated root does |
|---|---|---|
| `EnemyAI` | — | `StartCoroutine(PerceptionRoutine())` runs **only in `Start`**. Deactivating stops the coroutine; reactivating does not re-run `Start`, so every enemy is permanently blind. |
| `RuntimeNavMeshBaker` | `OnDestroy` (and `Rebake`) | `_instance.Remove()` is never called on disable, so an inactive chunk keeps its NavMesh registered — and every chunk instantiates at the same origin, so meshes overlap. |
| `MagicTutorial`, `TutorialSequence` | `OnDestroy` | Both set their static `Instance` in `Awake` and clear it only on destroy, so the singleton keeps pointing at a disabled object. |
| `EnemyNameplate` | `OnDestroy` | Builds an **unparented scene-root** `GameObject("Nameplate")`, so it is not a child of the chunk and does not hide with it. |

Two more things are not chunk-owned at all and would leak across any suspend: **police**, which
`WantedManager` creates with `Instantiate(prefab, spawnPos, Quaternion.identity)` and no parent,
and **`Assets/c/NavMesh.asset`**, which `c.unity`'s single `NavMeshSettings` block registers for
the life of the scene regardless of which chunk is loaded. That last one is the hard structural
obstacle: London's baked mesh and a compact interior mesh cannot both be registered at the shared
origin, and nothing in code registers London's — the scene does it.

`Interactable` is the one part that is already suspend-safe: `Active` is added on `OnEnable` and
removed on `OnDisable`.

Doing this properly needs explicit suspend/resume/evict hooks. That design — plus a location
cache, return stack, encounter ledger and corpse-loot lifecycle — is written up in
**`docs/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md`**. ⚠️ **None of it is implemented.** The
plan is a design record, not a description of the runtime; read it before touching chunk lifetime,
and treat its §11 phases as architect-first work (§10).

## 6. Save system — highest-risk area in the repo

`Assets/Scripts/Flow/SaveGameManager.cs`. One JSON file, written with `JsonUtility` to
`persistentDataPath/savegame.json` — **not** PlayerPrefs, and no `EA_` prefix exists anywhere
(an earlier version of this file said both, and was wrong). `SaveData` holds: character name,
class, `TutorialComplete`, chunk name, position, health, mana, stamina, quest list, inventory.

Five call sites write a save: every chunk edge crossing
(`ChunkManager.TransitionToChunkRoutine`), portal travel (`ChunkManager.TravelTo`, which runs
`TravelRoutine` — an earlier version of this line called it `TravelToChunk`, and no such method
exists),
new-game start and tutorial completion (both `GameFlowController` checkpoints), and
`PubInteractable.HaveAPint()` — pubs are the deliberate manual save point, see §9.

**The save stores `MapChunkData.ChunkName` as a string** and resolves it on load via
`ChunkManager.FindChunkByName` against the `ChunkManager.AllChunks` array.

Consequences to respect:
- Editing the `ChunkName` **value** in any `Assets/Data/Chunks/*.asset` invalidates existing
  saves. The lookup fails, `ContinueFromSave` logs a warning and falls back to spawning at the
  London gates (`GameFlowController.LoadLondonAtWestGates`) — the run continues, but the saved
  chunk and position are gone.
- A chunk missing from the `AllChunks` array is unloadable even if it exists.
- `Manor_Cellars_Data` has `ChunkName: "Manor Cellars"` (space) while every other chunk uses
  underscores. Do not "normalise" this casually — it is a save key.

**Inventory IS saved** — an earlier version of this file said it was not, and that was wrong.
`SaveGameManager` writes one `InventorySaveEntry` per stack as `ItemID` + `Quantity`, and
`PlayerSession.RestoreInventory` resolves each back through `Resources/Items`. Two consequences:

- **`ItemData.ItemID` is a save key**, in the same class as `ChunkName`. Changing the `ItemID`
  *value* on an existing item orphans it out of every save silently — the entry is read, the
  lookup fails, the item is dropped and nothing is reported.
- An item must stay reachable from `Resources/Items`, since that is how the load resolves it.

`QuestProgress` gained three **appended** fields on `feat/quest-definitions` — `StageIndex`,
`StageProgress`, `RewardsClaimed` (§14). `SaveGameManager` needed no change and was not touched:
it hands the whole `List<QuestProgress>` to `JsonUtility`, so new fields are picked up
automatically and an old save reads them as zero/false, which is the correct default. They are
public fields rather than properties because `JsonUtility` only serializes public fields — a
property there would have silently never persisted.

**Also saved: `TutorialComplete` and quest state.** `GameFlowController.ContinueFromSave` passes
both back through `PlayerSession.RestoreFromSave` and `QuestManager.RestoreQuests`. Tutorial
completion is checkpointed the moment it happens (`GameFlowController`, "tutorial completion
must survive an app restart"), and a *mid*-tutorial save restarts the tutorial cleanly on load
rather than resuming half-staged. Gates keyed off `TutorialComplete` do **not** re-lock after an
app restart — an earlier version of this file claimed they did, and that was wrong.

**Not saved:** wanted level, and whether you are riding anything (§11 — a load puts you on foot
with vehicles back at their authored spots, and a vehicle you had already nicked is nickable
again).

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
  `HUDActionButton.ActionKind` is the one with values proven live in serialized data: `c.unity`
  holds **six** authored `HUDActionButton` components covering all four original values —
  `Attack=0` on `AttackButton`, `Ability=1` on `Skill0/1/2`, `Inventory=2` on `MapBagShortcut`,
  `Interact=3` on `InteractButton`. They belong to the legacy cluster that `BuildActionButtons`
  deactivates, but they are still serialized, so a reorder would repoint them. `Crouch` was
  appended as 4.
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
| Pickpocketing | `World/PickpocketInteractable` | Requires crouch. Rolls `CatchChance`; failure spikes Knives. Authored by ticking `Pickpocketable` on a `PlacementPreset` (§13). |
| Grand Theft E-Bike | `World/VehicleController` + `World/MountController` | Mounting an `IsOwnedByNPC` vehicle spikes Knives and grants `SpeedMultiplier`. See §11 — ride state, dismounting and spawning all changed. |
| Pub safehouses | `World/PubInteractable` | A pint clears Knives + concealment, heals, and saves. |
| Arrest | `Flow/GameFlowController.ArrestRoutine` | Death dealt by an `EnemyAI.IsPolice` attacker (tracked via `Health.LastAttacker`) arrests instead of killing: clears wanted level, despawns police, returns you to the cellars. |

### Known issues in these systems (verified, all open)

- ~~**Stealth is keyboard-only.**~~ **Fixed** on `feat/crouch-button`. The HUD has a **CRO** button
  (`HUDActionButton.ActionKind.Crouch` → `UIManager.OnCrouchPressed` →
  `StealthController.ToggleStealth`), built in code beside ATK and USE, reading `ATK, USE, CRO`
  right to left along the bottom. `KeyCode.C` still works and is how it gets tested in the editor.
  The button shows its state — `EKVibe.ButtonBrownActive` and the label **STAND** while crouched —
  repainted by `UIManager.RefreshCrouchButton`, which `ToggleStealth` calls so the key and the
  button can never disagree. This also makes **pickpocketing reachable on mobile** for the first
  time, since `TryPickpocket` requires `IsCrouched`.
- ~~**The ModernBritain props are in every chunk.**~~ **Fixed** on `fix/scene-root-props`. All
  three scene-root instances are gone from `c.unity`, each by the route that suits it:
  - `Pub_TheWinchester` is now a **nested prefab instance inside `Home_London_Prefab`** at local
    `(8, 0, -4)` — the same world position it held, since chunks instantiate at the origin. Pubs
    are cities only, and Home is the only city, so one instance in one chunk is the whole of it.
  - `NoseyParker` was deleted and replaced by **`Preset_NoseyParker`** (`Prop`, `Prefab` →
    `NoseyParker.prefab`), so parkers are stamped per chunk wherever there are civilians. Placing
    the prefab rather than composing a civilian is deliberate: `Interactable.OnInteract →
    PickpocketInteractable.TryPickpocket` is a **persisted UnityEvent living inside that prefab**,
    written only by `ModernBritainSetup` — a Danger Zone tool that orphans prefabs when re-run.
    `PlacementBuilders.BuildFromPrefab` uses `PrefabUtility.InstantiatePrefab`, so the link and
    the event survive. Author a new civilian type from scratch and it will not be robbable.
  - `Moped` (the hand-placed e-bike) was deleted — see §11, which this closes.

  **All four verified in the editor on 2026-07-29**: the scene loads clean, the parkers were
  stamped through the palette, the pub is where it was, and the bike spawns. The hand-written
  nested `PrefabInstance` block was accepted by Unity — which is worth knowing, because it means
  mirroring the blocks already in a prefab file is a workable way to author one without Unity.
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
- **`fix/chunk-edges-and-tooling` is merged into `main` and deleted** — edge fixes, boundary walls,
  the `Tools/GBA` menu move, the importer hardening and the World Palette. So is
  `fix/moped-mount-and-melee-flag` (the melee-flag fix and all of §11).
- **`feat/npc-preset-pipeline` is merged (PR #1) and deleted**, both locally and on `origin`. Its
  last commit landed separately: the PR merged at `0fb5046`, and the Resources library asset was
  cherry-picked onto `main` afterwards as `2382c36`.
- **2026-07-29: five stacked branches were fast-forwarded into `main` and deleted** —
  `docs/art-brief-and-queue` (`6de4cda`), `fix/scene-root-props` (`14c5d91`, `ebc2f66`),
  `feat/crouch-button` (`b9d5124`, `7b620f0`) and `feat/pickpocket-preset` (`b1de7fd`). They were
  cut in sequence off each other, so the merge was a fast-forward and no merge commit exists.
  ⚠️ **`b1de7fd` reached `main` without ever being compiled** — the pickpocket preset work was
  written after the last editor session. Everything before it has at least compiled;
  `fix/scene-root-props` was fully verified in the editor.
- **2026-08-03: `feat/london-cast-and-region-palette` and `feat/quest-definitions` are both merged
  into `main` and deleted.** They were cut in sequence off each other, so the merge was a
  **fast-forward** — `main` advanced from `68dd957` in one move and no merge commit exists.
  Together: the `CityRegion` field, the palette's NPC region split, the eight London cast presets,
  the four art-queue bands, then `QuestDefinition`/`QuestDatabase`, `QuestConditionWatcher`, the
  three appended `QuestProgress` fields, `QuestActor.FindAll` and `WantedManager.ClearWanted`
  (§14, §6, §8). Nothing in the range touches the scene, any prefab, `MapChunkData`,
  `SaveGameManager`, `DialogueData`, `DialogueManager` or any tutorial flow file.
  - **Reviewed before merge** by the `reviewer` agent (§10) against §14. Verdict was *merge with
    follow-ups*. Three findings were fixed on the branch first — `ClearWanted` not despawning
    police, a re-granted quest rewinding its own objective, and `RewardsClaimed` being set before
    the reward was paid. **The first two were live bugs, not doc drift.** The six left unfixed are
    written up under §14's open-issues heading; the two authoring traps there are worth reading
    before anyone authors a real quest.
  - ⚠️ **Still no compiler has run over any of it** (§10). The editor session that exercised the
    quest system predates the three fixes above, so **those three commits are unverified in both
    senses** even though the system around them is not.
- **The next task is Stage F, written up in `docs/STAGE_RF_PLAN_REVISED.md`**: the six-commit
  inventory and loot overhaul. Stage R (the `Home_Alvaston` → `Home_London` rename) is **done**
  — renamed in the working tree with the save-key migration in `SaveGameManager.ReadSaveData`;
  the original brief (`docs/STAGE_F_BRIEF.md`) is kept for history and its R section no longer
  applies. The revised plan is a self-contained brief meant to be pasted into a fresh session.
- ⚠️ **Commit a script's `.meta` with the script. This has now happened twice.** `PlacementPreset.cs`
  went in without one, and that file holds the GUID all twenty-three `Preset_*.asset` files bind to via
  `m_Script` — a fresh clone would have minted a new one and silently detached every preset. Fixed
  in `37e90d7`. Then `PlacementPresetLibrary.cs` did the same; fixed in `e130481`, before anything
  bound to it, which is the only reason a fresh GUID was safe to invent.
  **The check is one command, so run it after adding any `.cs` from outside the editor:**
  ```
  git ls-files 'Assets/**/*.cs' | while read f; do [ -f "$f.meta" ] || echo "NO META: $f"; done
  ```
  Unity writes metas on its next open, so a session that adds a script without opening Unity leaves
  the meta missing entirely — and if two machines then open it independently, they mint different
  GUIDs and whatever binds to the script resolves on one and is null on the other.
- ~~**`4b93ccc` on `feat/quest-placement-tools-and-mosley-quest` is NOT merged.**~~ **Nothing to
  do here.** That commit and that branch no longer exist in this repository — `git cat-file`
  cannot find the object, and `origin` carries only `main`. The fix it was said to hold, the
  `PauseManager.IsPaused` guard in `CombatController.Update`, has been present since the
  **initial commit** (`git log -S "PauseManager.IsPaused"`), so there was never anything to
  cherry-pick. The craftpix merge hazard below is likewise moot while no such branch exists.
- `Assets/` is ~672 MB with `.psd`/`.fbx`/`.glb`/`.aseprite` committed and **no Git LFS**.
  Pruning will not shrink `.git` — history keeps the blobs.
- **A `.gitattributes` does exist** (an earlier version of this line said it did not). It is not
  LFS: it pins `* text=auto` plus an explicit binary list, so the repo stores LF and each working
  tree gets what it wants — CRLF on Windows, LF on Linux. This matters because Unity rewrites a
  whole YAML file whenever it touches one, so without it a line-ending difference and a real edit
  are indistinguishable in a 100,000-line diff. **A file hand-written by an agent lands LF in the
  Windows working tree**, which commits identically but leaves the tree inconsistent; `rm` it and
  `git checkout --` it back to normalise.
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
- ⚠️ **Merge hazard (historical, currently inert):** `feat/quest-placement-tools-and-mosley-quest`
  (`4b93ccc`) *renamed* 1,789 of those craftpix files rather than deleting them, and merging it
  after the deletion could resurrect the whole folder via git's rename detection. **Neither the
  branch nor the commit exists in this repo any more** (see §9), so there is nothing to merge —
  but if either is ever restored from a clone, check `3DModels/Sprites/` is still absent
  afterwards.
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

## 9b. Content authoring — the World Palette

`Tools → GBA → World Palette` (`Editor/WorldPaletteWindow.cs`) is how content gets placed now.
Arm a preset, click in the Scene view, Shift to keep stamping, Esc to disarm.

| Piece | File | What it does |
|---|---|---|
| The thing to place | `Data/PlacementPreset` | Label, category, icon, and either a `Prefab` or the recipe fields the old windows exposed. |
| How to build it | `Editor/PlacementBuilders` | Each old window's `Create…()` body, taking a position and a parent. |
| Where to build it | `Editor/WorldPaletteWindow` | Grid, arming, SceneView raycast, ghost, parenting. |
| A starting set | `Editor/StarterPresetGenerator` | `Tools → GBA → Content → Create Starter Presets`. Skips what exists; never overwrites. |

- **`PlacementCategory` is serialized by index — append only** (§7). So is
  **`PlacementPreset.CityRegion`** (`Assorted = 0`, `London = 1`, `Birmingham = 2`), added when the
  London cast made a single flat NPC grid unusable.
- **The NPC section is the only one split by region**, into one sub-heading per `CityRegion`. The
  split is drawn by iterating the enum rather than the presets, so **a region with nothing in it
  still shows its heading** — Birmingham is empty on purpose and the heading is the reminder that it
  is next. `Region` is read by nothing but this window: it never reaches `NpcFactory` and changes
  nothing about the NPC that gets built. `Assorted` is 0 so every preset authored before the field
  existed reads the go-anywhere default, which is right for the villager and the Nosey Parker.
- **Vehicles are not GameObjects here.** They are authored onto `MapChunkData.VehicleSpawns`, so
  the palette shows a target-chunk field and a click appends a spawn entry (§11).
- **Prefab Mode uses the stage's own physics scene** for the placement raycast. `Physics.Raycast`
  would hit the main scene's colliders, which are not even visible in the stage.
- **A placement of the palette's own is never the parent of the next one.** Placing selects what it
  made, and the parent is read from the selection, so a Shift-held run of five used to bury the
  fifth four levels deep. It reuses the parent that placement went into instead. Selecting anything
  else still re-targets.
- **A placement is a copy, not a link.** Editing a preset — or importing art that rewires it —
  changes what you place *next*. To update something already standing in a chunk, delete it and
  stamp it again. There is deliberately no resync tool; at current content volume restamping is
  cheaper than the tool would be.
- **A preset with a `Prefab` assigned short-circuits the whole recipe** — `PlacementBuilders.Build`
  checks `preset.Prefab != null` *before* the category switch, so `Category` is only a palette
  heading for those. `Preset_NoseyParker` is the worked example: `Prop`, pointing at
  `Prefabs/ModernBritain/NoseyParker.prefab`, placed with `PrefabUtility.InstantiatePrefab` so the
  prefab link and its persisted UnityEvents survive the stamp.
- The five `Place/…` windows still exist and still work. The gate for retiring them (the palette
  having authored real content) is now met — Mosley, the pharmacist and the e-bike spawn are all
  palette output — but they have not been removed, because none of them has been checked for
  anything the palette cannot yet do.

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

**On Linux, that is `python3`** — Mint has no bare `python`. The script itself is portable
(`#!/usr/bin/env python3`, `os.path` throughout, backslashes normalised), and
`.claude/settings.json` permits both spellings.

`--check-dangling` knows the build scene's built-in baseline (17 unresolved GUIDs) and fails only
above it. Run it before and after anything that deletes, moves or renames assets.

Everything else — does the scene load, is anything pink, do the mechanics behave — needs the
Unity editor and therefore needs a human. Say so plainly rather than implying otherwise.

A brace/paren balance scan over the `.cs` files is worth running when a change is large and
nothing can compile it. It catches a truncated edit; it says nothing about whether the code is
correct, or even whether it builds. Do not report it as though it were a compile.

**The four CS0618 warnings are suppressed on purpose — do not "modernise" them.** Both replacement
APIs live in packages this project does not have (`Packages/manifest.json` lists neither
`com.unity.ai.navigation` nor `com.unity.2d.sprite`), so the deprecated call is the only one that
exists here:

| Site | Deprecated | Replacement lives in | Why it stays |
|---|---|---|---|
| `EKNavMeshBaker.MarkObject`, `DiscoverEnglandSetup` ×2 | `StaticEditorFlags.NavigationStatic` | `com.unity.ai.navigation` | The baker calls built-in `UnityEditor.AI.NavMeshBuilder.BuildNavMesh()`, which is driven by this exact flag. Removing it stops the bake, it does not modernise it. |
| `ArtImportTool` slicing | `TextureImporter.spritesheet` | `com.unity.2d.sprite` | Still functional. `VerifySliced` already checks the sub-sprites actually appeared, so if it ever becomes a no-op the tool reports it rather than importing an undivided sheet. |

Each is a narrow `#pragma warning disable 618` / `restore 618` around the single statement, with
the reason at the site. Revisit if either package is ever added.

⚠️ **Changes made in the Inspector while Play mode is running are discarded when it stops.** This
has wasted real time: a value is tuned in play, it looks right, play stops, the old value returns,
the scene is saved over the top. When asking for an editor change, say whether Play must be
stopped first. Give the route through the UI as well as the field name — panel, menu path, which
object to select — not just what to set.

**There is no C# compiler in the agent environment either.** Reference integrity passing says
nothing about whether the project builds. Anything written without a Unity session is unverified
in both senses; §11 is the current example.

A rename to **GBA: England** (Great British Annals) has begun: `EKVibe.DisplayTitle` is now
"GBA: England" and the hub chunk is renamed `Home_Alvaston` → `Home_London` (Stage R — the
`ChunkName` was a save key, so `SaveGameManager.ReadSaveData` migrates the legacy string on
load; old saves survive). Still open: the `ExiledAlvaston` namespace appears in 46 `.cs`
files and **zero serialized assets**, so a namespace rename is safe — Unity binds scripts by
`.meta` GUID, not type name — but it is not done. `productName` in ProjectSettings is also
still "Exiled Alvaston".
A colon is illegal in Windows paths and git repo names, so any repo/folder would be
`gba-england` with `GBA: England` only as a display string.

---

## 11. Mounts and vehicles

Merged to `main`, compiled, and play-tested in the editor: mounting, dismounting, the boost, the
prompt flip and the visuals all work. **The data-driven spawner path has now been exercised too**
(2026-07-29): the hand-placed instance is deleted, `Home_London_Data.VehicleSpawns` is the only
source of the bike, and it was confirmed in the editor to spawn. Nothing in §11 is unverified any
more.

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
- **Riding is drawn by layering, and that is now the decision, not a fallback.** The `cycle` sheet
  is cancelled (2026-07-29): `WorldActorVisual.SetMounted` draws the vehicle sprite over the
  actor's feet whenever `MountedSprite` is null, which it is on every character, so any character
  reads as riding with no bespoke rider art. Leave `MountedSprite` unassigned — it writes
  `_sr.sprite`, which an Animator overwrites every frame, so the code has to suspend the animator
  to use it. Nothing does.
- **Riding plays the idle animation, by design.** `CombatController.ApplyLocomotionAnimation` holds
  `Speed` at 0 and sets `Cycling` only when the controller declares the parameter. With no `cycle`
  sheet there is no `Cycle` state and no `Cycling` parameter, so the rider idles under the bike
  sprite rather than running on the spot. No code change was needed to cancel the sheet.
- **Nicking does not persist**, by decision. `IsOwnedByNPC` is cleared on the instance, and the
  instance is replaced when the chunk reloads — so you re-nick and re-spike on every visit.
  Consistent with §6, where wanted level and ride state are not saved either (inventory is).
- ⚠️ **KNOWN ISSUE (found in Stage R play-test, 2026-07-29, open): death-respawn keeps you
  mounted.** A mounted vehicle unparents from its chunk, so `LoadWorld`'s destroy-and-rebuild
  never touches it, and nothing in the death path (`DeathScreenUI` → `ContinueFromSave`) calls
  `Dismount()` — you wake at your last save still on the bike. §6's "a load puts you on foot"
  is only true for an app-restart load. Fixing it properly is a design call (GTA would take
  the bike) plus real work: a bare `Dismount()` strands a scene-root bike at the death spot,
  and returning it to its authored spot means coordinating with `VehicleSpawner`'s instance
  tracking. Deferred to Stage F — needs the editor, and the owner's answer on intent.

**Moving off the hand-placed instance — two down, one to go:**

1. ~~Create `Limey_EBike_Data.asset`.~~ **Done.** It exists with `ChassisPrefab` resolving to
   `EBike.prefab`, committed in `37e90d7`.
2. ~~Author a spawn onto `Home_Alvaston_Data`.~~ **Done.** `VehicleSpawns` carries one entry at
   `(0.31, 0, 22.07)`, placed through the palette (`9b65d94`). (The asset has since been renamed
   `Home_London_Data` in Stage R.)
3. ~~Delete the hand-placed instance in `c.unity`.~~ **Done** on `fix/scene-root-props`. The
   scene-root `Moped` — a leftover name override from before the prefab was renamed, which is why
   searching the Hierarchy for "EBike" or "Limey" found nothing — is gone. `VehicleSpawner` and
   `Home_London_Data.VehicleSpawns` are now the only source of the bike, **and that path was
   confirmed working in the editor.** If no bike appears in Home_London, debug the spawner; there
   is no longer an instance to fall back on.

`EBike.prefab`'s sprite is `spr_vehicle_ebike` from the §12 pipeline — verified assigned on
2026-07-30, the only reference to that texture's GUID in the project. The code-generated
placeholder it replaced was deleted with the rename. (An earlier version of this line said no
sprite was assigned, which stopped being true when the art landed.)

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
error noted in §8. `Cycling` would hold a `Cycle` state while riding, but **no `cycle` sheet is
requested any more**, so no controller has that state and the parameter is never created — see
§11. The importer still supports the action; the pipeline just no longer asks for it.
Once a subject's sheets import, the tool points the player's Animator at the controller it built;
without that the sheets would import and the player would carry on playing `Bandit_Controller`.

`Assets/Sprites/Enemies` is the old craftpix content: 64×64 pixel art imported at PPU 100 with
**bilinear** filtering, which is why it looks mushy. It predates all of this and is not the
reference style.

### Where the art stands

Delivered and in the game:

- `spr_vehicle_ebike` — the hire e-bike, wired into `EBike.prefab`.
- `sheet_char_player_idle` (4 frames), `sheet_char_player_walk` (4 frames) and
  `sheet_char_player_hurt` (3 frames) — sliced, clipped, and driving `player_Controller`, which is
  assigned to the player's Animator in place of `Bandit_Controller`. The player is `Height 1.6`,
  `GroundOffset 0`, `ActorVisual` scale 1.

- `sheet_char_mosley_idle` and `sheet_char_pharmacist_idle` — 4 frames each, sliced, clipped, and
  built into `mosley_Controller` and `pharmacist_Controller`. Both wired into their presets by the
  importer, and both standing in `Home_London_Prefab` as the first NPCs authored end to end.

- `sheet_char_villager_idle` (4 frames, 6 fps) and `sheet_char_villager_walk` (3 frames, 6 fps) —
  the **first subject with a walk sheet**, which matters because `Preset_Villager` has `Roams: 1`
  and a roaming NPC without one slides along the ground. `villager_Controller` holds Idle and Run
  and exactly two transitions, the `Speed` pair. Two instances stand in `Home_London_Prefab`.

  ⚠️ **This art began life as a failed Daniel Pauls generation** — the brief asked for a stage
  magician in a pink Las Vegas suit and the generator returned a middle-aged bloke in a patterned
  shirt, cargo shorts and flip-flops. Rather than bin it, the frames were retiled under the
  `villager` subject, which already had a preset waiting with `ArtSubject: villager`. Two lessons
  worth keeping: a subject is chosen by which preset is waiting for it, not by what was asked for;
  and the delivered *sheet* was unusable (four byte-identical cells) while the *frames* behind it
  were fine, so check the frames before rejecting a delivery.

  The walk is three frames, not four, and **frame 3 is the weak one** — fill 85% against the other
  two at 90%, mean width 166 px against 174 and 187, and drawn more side-on, so he appears to
  shrink and half-turn on the third step. It passes the 1.4× width tolerance, so nothing refuses
  it. A fourth frame plus a redraw of 3 at the angle and scale of 1 and 2 is the fix.

Re-delivered 2026-07-30 and **imported**: the player's `attack`, `cast` and `death` sheets.
The earlier full-sheet generations (below) were abandoned in favour of **single-frame generation
+ local tiling**: six 512×512 frames per action generated one at a time (AI Studio, chained by
attaching the previous frame), converted/measured/re-aligned locally into `art_incoming/frames/`,
tiled to 3072×512 sheets by a local script, pre-checked by `Tools/precheck_sheets.py` (which
replicates the importer's checks, including a strict threshold-200 baseline pass — added after a
blurred shoe edge on `cast_6` passed the lenient check yet read 23 px high to the importer's
alpha-after-unmix feet measure). All three sheets sliced, clipped and added to
`player_Controller`. **The `cycle` sheet was rejected and has been discarded** — cancelled, not
pending (§11).

### `BuildController` used to wire the batch, not the controller (fixed and verified 2026-07-30)

Found because attack, cast and death imported perfectly — sheets sliced, clips built, states
created with the right motions, `PlayerAnimator` pointed at the controller, all six parameters
present — and **never played a frame in-game**. `player_Controller.controller` held six states and
exactly two transitions, both of them `Hit → Hurt`, the same one twice.

Two bugs, one cause: `BuildController` reasoned about the current import batch instead of about the
controller in front of it.

- **All transition wiring sat inside the `idle != null` branch**, where `idle` was only set if
  *this* batch contained an idle sheet. A batch of attack/cast/death alone added three states and
  no transitions (log line "controller built, but no idle sheet").
- **The one-shot loop skipped any action not in the batch's own clips**, so even a batch containing
  idle could not reach a state an earlier run had left orphaned. Between the two, no possible
  sequence of batches ever wired attack/cast/death.
- **Nothing checked whether a transition already existed**, so each idle-bearing re-run stacked
  another full set. That is where the duplicate `Hit → Hurt` came from; the shipped controller had
  every one of its four real transitions twice.

Now: states are resolved with `FindState` over the whole state machine, `idle` falls back to
`FindState(sm, "Idle")` and then to `sm.defaultState`, every add is guarded by
`HasConditionalTransition` / `HasUnconditionalTransition`, and `RemoveDuplicateTransitions` clears
existing duplicates through the controller API on each run (reported in the import log). Death
still gets no return transition. **Re-imported and play-tested** — attack and cast fire; all five
player sheets are archived to `art_incoming/processed/`, which only happens for a clean pair.

`Editor/EnemyPrefabSetup.cs` wires its controllers just as unguardedly and is **not** affected,
because `BuildPoseController` `DeleteAsset`s the controller and re-creates it every run — it never
sees its own output. That is the §7 delete-and-re-save hazard rather than this one, and it is why
the enemy controllers are safe to leave alone.

### The procedural melee swing now stands down where there is attack art

Attack firing revealed what had been hiding behind a broken state machine: `WorldActorVisual`
drew its **placeholder** melee effect on top of the real clip. Both call sites
(`CombatController.MeleeHitboxRoutine`, `EnemyAI.PerformAttack`) set the `MeleeAttack` trigger
*and* call `PlayMeleeSwing`, which is two attack visuals at once —

- `ApplySwingPose` rotates `ActorVisual/SwingRoot` by up to `SwingAngle` (55°) and lunges it: the
  sprite visibly tilts through the clip.
- `SpawnSlashArc` builds a `PrimitiveType.Quad` on an **`Unlit/Color`** material. That shader
  ignores alpha, so the intended translucent cream renders as an opaque near-white block and
  `FadeSlash`'s alpha ramp fades nothing at all — it simply vanishes when destroyed 0.18 s later.
  The quad is 0.2 units tall and yaw-oriented in billboard space, so it is near-invisible edge-on
  and a solid bar face-on: hence "appears sometimes".

`PlayMeleeSwing` now returns early when `HasAttackAnimation()` — `Animator.HasState(0, "Attack")`
on the `SwingRoot` animator. **Probe by state, not by the `MeleeAttack` parameter**: both
`ArtImportTool` and `EnemyPrefabSetup` declare that parameter unconditionally, so it says nothing
about whether art exists. `SetFacing` still runs first — it is what points the attack clip the
right way — and an in-flight swing is stopped and its pose cleared, since `NpcFactory` and
`MagicTutorial` can attach an Animator after the fact.

The procedural swing is **kept**, not deleted, and it is still the only attack tell for an actor
without art. `SwingAngle` / `SwingDuration` / `LungeDistance` stay as public serialized fields
(§7). Who this changes, checked prefab by prefab:

| Actor | Animator on `SwingRoot`? | Attack state? | Effect |
|---|---|---|---|
| Player | yes | `player_Controller` ✓ | procedural swing off — the fix |
| `Enemy_Orc1/2/3` | yes | `Orc_Controller` ✓ | off; plays its own craftpix attack clip |
| `Enemy_BotWheel` | yes | `BotWheel_Controller` ✓ | off; same |
| `Police_*` ×5 | **no Animator at all** | — | unchanged, still the only tell they have |
| Tutorial geezer (`underhoused`) | — | art now delivered (2026-08-03 correction — was "sheets not delivered"; whether it declares an `Attack` state was not re-verified) | unchanged |

The player's attack window and its clip happen to line up exactly: `MeleeHitDelay 0.15` +
`MeleeRecovery 0.35` = 0.50 s, and the clip is 6 frames @ 12 fps = 0.50 s, `loop: false`. Damage
lands on frame 2. Nothing needed retuning, but changing either number now desynchronises them.

**Why the first three full-sheet deliveries failed, measured rather than guessed** (2026-07-29,
replicating the importer's own checks outside Unity):

- **All three were laid out 6×2 — twelve drawings — while their JSON declared 6×1 of 512×512.**
  Both readings total 3072×512, so `ValidateSheetDimensions` passed and the importer sliced six
  cells each holding two stacked figures. This was the root cause; single-frame generation +
  local tiling eliminates the whole class of layout mismatch.
- The figure filled **50–73% of its cell height** against the accepted idle's **89%**, which is
  what tripped the width check. **"Drawn edge-on" was not what happened** — both failure modes
  are now described in §12 and `ART_PIPELINE.md` §3.
- Baseline drift at final size: `attack` 12.7 px, `cast` 43.0 px, `death` 57.0 px, against a
  2 px limit. `death` is exempt from the check by action, but the exemption is for the pose
  changing shape, not for the figure wandering around its cell.

`sheet_char_danielpauls_idle.json` — the manifest that sat in `art_incoming/` with no PNG beside
it — **has been deleted**. It was a delivery that never happened, and the importer reported it
every run. Daniel Pauls was then requested properly in the queue's band 2 — **and has since been
delivered**, along with the tracksuit geezer, so band 2 is done and neither subject needs
requesting again.

**`ART_PIPELINE.md` §7 is now a banded queue for the whole world, not a request list.** Five bands
in order: the three player redraws → ~~the tutorial cast (Daniel Pauls, the tracksuit geezer)~~
**(band 2 delivered — both subjects have idle sheets and controllers wired to their presets)** →
**21 world props** → the ambient cast (Mosley/pharmacist walks, villager, Nosey Parker, squirrel) →
the police tiers. Props are band 3 because `North_Wasteland`, `South_Slums`, `East_RetailPark` and
`West_Canal` contain a ground plane, four edge triggers and four boundary walls and **nothing
else** — that band is what unblocks world-building. `Home_London` is the only dressed chunk, and
it is dressed with 3D pack models rather than generated sprites.

⚠️ **Only the player, the e-bike, and NPC subjects named by a preset's `ArtSubject` are
auto-assigned** (`ArtImportTool.AutoAssign`). The police tiers, the Nosey Parker and the pub are
hand-built prefabs with `PlaceholderBody` primitives and no `SpriteRenderer`, so their art will
import and land nowhere until someone either gives them presets or wires the prefabs by hand.

**The importer now archives what it accepts.** A clean pair moves to `art_incoming/processed/`;
anything that reported a problem stays in `art_incoming/` so the next run shows only what is
still wrong. `rejected/` is the hand-sorted pile above. Neither subfolder is read by the importer,
which only ever looks at the top level.

**Animated NPCs are §13.** The Animator goes on `ActorVisual/SwingRoot` — the same GameObject as
the `SpriteRenderer` — because the importer binds every clip with an **empty path**. One level up
and the clips animate nothing while looking perfectly well wired in the Inspector.
`WorldActorVisual.AttachAnimator` owns that, and both the editor and the game call it.

---

## 13. The NPC pipeline

⚠️ **Written without a compiler — see the warning at the top of this file.**

Adding an NPC is meant to cost two clicks in Unity and no code at all:

1. Spec the subject in `ART_PIPELINE.md` §7.4 (the cast table) and §7.7 (the descriptions), and have
   the art agent deliver `sheet_char_<subject>_*.png` + JSON to `art_incoming/`.
2. Create a `PlacementPreset` (or let the starter generator make it): `Label`, `Category: NPC`,
   `Region`, `ArtSubject`, `AmbientLine` or a `Conversation`, `Roams` if it should wander,
   `Pickpocketable` if they should be robbable instead of talkable.
3. ⚑ `Tools → GBA → Art → Import Generated Art`. Sheets slice, clips build, a controller builds,
   and **the preset wires itself** — controller, resting sprite, palette icon, height.
4. ⚑ `Tools → GBA → World Palette`: arm it, click it into a chunk prefab.

| Piece | File | What it owns |
|---|---|---|
| What an NPC *is* | `Data/PlacementPreset` | Art subject, height, dialogue, temperament, quest key, whether they can be robbed. |
| Building one | `World/NpcFactory` | The recipe. **Runtime**, so the game can call it too. |
| Editor extras | `Editor/PlacementBuilders` | Undo, and the authoring capsule. Nothing else. |
| Wiring art to presets | `Editor/ArtImportTool` | `AutoAssign`, plus a re-runnable menu item. |
| Wandering | `AI/NPCWander` | Stroll, dwell, face, drive `Speed`. |
| Ambient dialogue | `Editor/PresetDialogueTools` | Generates `DialogueData` from a one-liner. |
| Runtime lookup | `Data/PlacementPresetLibrary` | The few presets code resolves by name. |

**Things that will catch you out:**

- **`NpcFactory` is runtime and must stay that way.** `Assets/Editor/` is stripped from builds, so
  a recipe living there is unreachable from anything spawning an NPC while the game runs — which
  is exactly how `MagicTutorial`'s characters ended up composed by hand, sharing one sprite between
  them. Nothing in `NpcFactory` may touch `UnityEditor`.
- **Dialogue is generated at authoring time, never at build time.** `AssetDatabase.CreateAsset`
  does not exist at runtime. `NpcFactory` only ever *reads* `preset.Conversation`.
- **`NpcHeight` of 0 means inherit** — the importer writes the subject's `worldHeight` there. No
  preset hardcodes a value, including the squirrel, who is 0.45 against a councillor's 1.35 and
  will read as a man in a squirrel suit until his sheets land.
- **The importer always wins on controller and sprite, never on height.** Those two are derived
  from the art, so a fresh import replaces placeholder wiring with no manual step; height is
  tunable, so a hand-set value survives. Point a preset at another subject's animations on purpose
  and the next import of its own subject reverts it.
- **`Wire Presets From Imported Art`** (`Tools/GBA/Content/`) exists because an import only knows
  the batch in front of it, and a clean batch is archived out of staging immediately. Art imported
  months ago, or a preset written after its subject arrived, is only reachable this way.
- **`NPCWander` is deliberately NavMesh-free.** `EKNavMeshBaker` bakes one mesh from whichever
  chunk is loaded, and all six instantiate at the same origin — right for one, wrong for five.
  `RuntimeNavMeshBaker` (which **does exist**, at `Assets/Scripts/World/RuntimeNavMeshBaker.cs`)
  would fix it at the cost of a runtime bake per chunk crossing on a mobile-first game. It probes
  ahead with a `SphereCast` and gives up on the stroll instead. Note that baker only removes its
  registered mesh in `OnDestroy` — see §5's suspension table.
- **`NPCWander` calls `SetFacing` every step.** Without it half of every wander is walked
  backwards, which reads as a rendering bug.
- **Tutorial presets must not carry a `Conversation`.** Daniel Pauls and the geezer run dialogue
  off quest state and own their own `Interactable`; a preset conversation would answer the same
  button press. `MagicTutorial.OwnInteraction` warns if it finds one.
- **`PlacementPresetLibrary` lives in `Resources/`; the presets do not.** Everything reachable from
  `Resources/` ships in the build, and the chest preset alone would drag in a 45 MB prop pack.
  Entries are keyed by an authored string, so renaming a preset asset is safe.
- ⚠️ **`UnityEvent.AddListener` does not survive being saved into a prefab.** It creates a
  *non-persistent* listener; only calls written through `UnityEditor.Events.UnityEventTools` are
  serialized. So an authoring tool that wires an `OnInteract` handler with `AddListener` looks
  correct in the Scene view and produces a prefab with the component present and nothing connected
  to it. This is why `PickpocketInteractable` **subscribes itself in `Awake`**, and why that `Awake`
  first walks `OnInteract.GetPersistentEventCount()` looking for a persistent call already pointing
  at itself: `NoseyParker.prefab` carries exactly such a call, written by `ModernBritainSetup`, and
  would otherwise be wired twice and rob the player twice per press. `NpcFactory` sets only
  serialized state — the component, its tuning, the prompt.
- **A preset is either a talker or a mark, never both.** `Pickpocketable` plus a `Conversation` is
  two listeners answering one button press, the same bug the `Conversation != null` guard exists to
  avoid. `NpcFactory.ApplyPickpocket` warns and **dialogue wins**, because the failure that leaves
  is a civilian you cannot rob rather than a quest giver who will not talk. A mark's prompt becomes
  "Pickpocket <name>" instead of "Talk to <name>", which is the player's only cue to crouch.
- **`EnemyAI.Animator` is a public field nothing assigns unless asked.** The geezer's attack, hurt
  and death sheets would import, build a controller, and never play a frame. `MagicTutorial` sets
  it from `WorldActorVisual.SpriteAnimator` when he turns hostile; anything else spawning an
  animated enemy in code needs the same line.

### The London cast — presets waiting on art

`Assets/Data/Presets/` holds eight new NPC presets for London, all `Region: London`: **Mayor
Swalls**, the **Quidland** and **F.U. Sports** clerks, **Commissioner Spencer**, **Officer Riggs**,
**Officer Murtaugh**, and **Ralph** and **Sanjeet** of the Croydon Spartans. Councillor Mosley and
Daniel Pauls were retagged London; the villager and the Nosey Parker stay `Assorted`, since they are
placed everywhere.

⚠️ **An earlier version of this section said none of them was placed and none had art. Both
stopped being true in `4f7dc62`** and the line was never updated. As of 2026-08-03:

- **Nine NPCs stand in `Home_London_Prefab`** — Mosley, the pharmacist, both clerks, Swalls,
  Riggs, Murtaugh, Ralph and Sanjeet — plus two villagers, so eleven in all. **Commissioner
  Spencer is the one cast member still unplaced.**
- **All eight have idle art**, wired by the importer through `ArtSubject`. Murtaugh also has a
  walk (he is the only one that `Roams`).
- ⚠️ **Not one of them can talk.** No `PlacementPreset` in the project has a `Conversation`
  assigned — checked across all 23. Every NPC in the game is currently scenery with a name.

That last point is the honest state of the content layer, and it is deliberate: the v1 dialogue
was deleted on 2026-08-03 so the quests could be written from scratch (§9). `ArtSubject` remains
the field that matters for the art pipeline — `ArtImportTool.AutoAssign` finds a preset by that
string, which is what makes step 3 above need no manual wiring.

- **Murtaugh is the only one that `Roams`**, so he is the only one queued for a walk sheet as well as
  an idle. The villager is the worked example of why (§12): a roamer with no walk sheet slides.
- **`Preset_FUSportsClerk.asset` does not match `Sanitise("F.U. Sports Clerk")`.** Nothing resolves
  these by path, so it is harmless — but `StarterPresetGenerator.BackfillNpcPresets` and
  `EnsureLibraryEntry` *do* look presets up as `Preset_{Sanitise(Label)}.asset`, so anything added to
  the generator later must either match or be found another way.
- **Neither clerk's name is settled**, and neither is Swalls' first name. They are placeholders.
- **The presets were hand-written, not generated**, so they are not in `StarterPresetGenerator`'s
  `StarterNpcs` list. Deleting one and re-running Create Starter Presets will not bring it back.
  What that tool *will* still do for them is `GenerateAmbientConversations`, which is ungated and
  runs over every preset — that is how these eight get their `DialogueData` assets, and it is one
  menu click, not eight.

**Three things these presets imply and do not build.** None of it exists; do not read the assets as
a claim that any of it does:

- **No vendor system.** Quidland sells weapons and F.U. Sports sells armour, and both clerks are
  currently just people who say a line. There is no shop UI, no buying, no selling, and no gold —
  §8 records that raw gold tracking does not exist at all yet, which is also why pickpocketing pays
  out in toasts.
- **No bounty pay-off for Riggs.** The intent is that he hands out missions and clears your wanted
  level on completion, announced as *"YOU'VE GOT DIPLOMATIC IMMUNITY! (it won't be revoked... this
  time)."* Nothing is wired to `WantedManager` from a preset.
- **No quest gate on Mayor Swalls.** He carries `QuestKey: mayor_swalls` so quest code can find the
  placed object, but the intent was that he stays unreachable until an earlier questline completes,
  and nothing hides him. There is no visibility-gating mechanism on presets at all;
  `RequireTutorialComplete` exists only on the Portal recipe. ⚠️ **The questline this was written
  against no longer exists** — Councillor Mosley's dialogue was deleted on 2026-08-03 so the quests
  could be written from scratch (§9), so this is a gate with nothing behind it yet.

---

## 14. Data-authored quests

**Exercised in the editor on 2026-08-03, and merged.** A throwaway `TestQuest` definition (single
`Kill` stage, one `ItemData` reward) driven by a temporary debug menu item confirmed quest start,
`Kill` tracking against a `QuestActor`-keyed enemy, completion, reward payment, and **persistence
across a chunk-crossing autosave — verified by reading `savegame.json` directly rather than
trusting the UI.** The test rig was deleted afterwards, deliberately: quests are meant to be
granted by an NPC or a world trigger, never by a menu item.

⚠️ **`TalkTo`, `Collect`, `Reach` and `Manual` have never been exercised, and neither has any
multi-stage quest.** The single-stage `Kill` path is the only one with editor evidence behind it.

⚠️ **There are still zero `QuestDefinition` assets in the project.** The system is inert until
someone authors one — no quest in the game behaves differently today. `escape_manor` and
`spark_of_talent` run on the bespoke tutorial code, not on this.

Dialogue still *starts* a quest (`DialogueChoice.GrantQuestId`) and, for a hand-in, still *finishes*
it (`CompleteQuestId`). What a `QuestDefinition` adds is the middle — ordered stages with objective
text, a condition per stage saying when it is done, and one reward on completion.

| Piece | File | What it owns |
|---|---|---|
| What a quest *is* | `Data/QuestDefinition` | `Id`, title/giver/location, the `QuestStage` list, one `QuestReward`. |
| Finding one | `Data/QuestDatabase` | `Find(id)` over `Resources/Quests`. A near-copy of `ItemDatabase`. |
| Watching one | `Quests/QuestConditionWatcher` | Binds the active stage's condition, advances it, pays the reward. Self-bootstraps like `VehicleSpawner`. |
| Where stage state lives | `Quests/QuestManager` | `QuestProgress.StageIndex` / `StageProgress` / `RewardsClaimed`, plus `SetStage` / `SetStageProgress`. |

**The containment rule is the whole safety argument. `QuestConditionWatcher` is completely inert
for any quest id with no definition asset.** `QuestDatabase.Find` returns null and every path bails
out. `escape_manor` and `spark_of_talent` deliberately have no definition, so `GameFlowController`,
`TutorialSequence` and `MagicTutorial` are untouched by all of this — none of those three files was
edited, and neither were `DialogueData` or `DialogueManager`. **Do not author a definition for
either tutorial quest** without working out what happens to the bespoke code that already drives it.

| `QuestConditionType` | Bound to | Advances when |
|---|---|---|
| `TalkTo = 0` | `Interactable.OnInteract` on the `QuestActor` keyed `QuestKey` | the player interacts |
| `Kill = 1` | `Health.OnDeath` on every `QuestActor` keyed `QuestKey` | `Count` of them have died |
| `Collect = 2` | `PlayerSession.OnInventoryChanged` | **never — see below** |
| `Reach = 3` | nothing; polled | the player is within `ReachRadius` (X/Z) of the keyed `SceneMarker`, or of a `QuestActor` if no marker matches |
| `Manual = 4` | nothing | never — bespoke code calls `CompleteQuest` itself |

`QuestConditionType` is serialized by index. **Append only** (§7).

**`Collect` tracks and reports; the hand-in is dialogue's job.** A `Collect` stage never completes
the quest, consumes the item, advances the stage or pays a reward. All it does is swap
`Objective` for `ObjectiveWhenMet` once the player is carrying enough — and swap it back if they
drop or sell it, which is why the text is *derived from the inventory every time* rather than
toggled once. The hand-in is `DialogueChoice.RequiredItem` + `RequiredItemQuantity` (greys the
choice out until they have it), `ConsumeRequiredItem` (takes the stack) and `CompleteQuestId`
(ends the quest) — machinery that already existed and already works. **A `Collect` stage in a
quest that no dialogue anywhere completes can never end**, and nothing checks that for you:
dialogue assets live outside `Resources/`, so they cannot be enumerated at runtime. The watcher
does warn if a `Collect` stage is not the last stage, since nothing after it is reachable.

**Rewards are scanned by completion state, not by "did I just complete this."** Any quest that is
`IsComplete && !RewardsClaimed` and has a definition gets paid, so a quest finished purely through
dialogue is rewarded identically to one the watcher advanced. `Reward.Item` goes through
`PlayerSession.AddItem`; `ClearsWantedLevel` calls the new `WantedManager.ClearWanted()` (the
reusable version of what `GameFlowController.ArrestRoutine` still does inline — that routine was
deliberately left alone). **`Reward.GoldAmount` warns and pays nothing** — there is no gold system
(§8), and this is not the commit that adds one.

**`ClearWanted()` despawns the police as well as clearing the meters**, and it has to. `SpawnPlod`
instantiates officers **unparented at the scene root**, so they survive a chunk transition; a
version that only zeroed the two meters dropped the HUD knife readout to zero and left Armed
Response hunting the player. That is exactly the shape of Officer Riggs' "diplomatic immunity"
reward (§13), which is the one authored use case for the flag. `ApplyReward` is the only caller —
`PubInteractable` and `ArrestRoutine` both still clear inline and are unaffected.

**A reward is claimed only once it has actually been paid.** `ApplyReward` returns a bool: it
checks every manager it needs *before* handing anything over, and pays nothing at all if one is
missing, so the caller leaves `RewardsClaimed` unset and the next `Update` retries. Checking up
front rather than half-way is what makes the retry safe — a partial payment followed by a retry
would grant the item twice. `ScanRewards` keeps `_rewardScanNeeded` true while any payment is
deferred; clearing it unconditionally would strand the reward until the next unrelated quest
event, which for the last quest in a run means never. An authored `Quantity` of 0 warns and
*claims*, since that can never pay and must not retry forever.

**Things that will catch you out:**

- **All quest-state mutation happens in `Update()`.** Event callbacks only set a flag or bump a
  counter. A `QuestManager` call from inside an `OnInteract` / `OnDeath` listener raises
  `OnQuestsChanged`, which rebinds listeners, from inside the listener list being invoked. Do not
  "simplify" the indirection away.
- **`Update` runs while the game is paused.** `PauseManager` only zeroes `Time.timeScale`, which
  stops `FixedUpdate`, not `Update`. That is why the reward scan explicitly defers while
  `DialogueManager.IsDialogueOpen`: `OnChoiceSelected` runs grant → complete → *consume the
  handed-over item* in that order, and a reward applied the instant the completion landed would
  fall inside a half-finished hand-in. Deferring loses nothing — `RewardsClaimed` is not set until
  the reward actually applies, so a quit mid-conversation pays on the next load.
- **Only the *first* active quest is watched.** The watcher binds `QuestManager.GetActiveQuest()`,
  which is the first active, incomplete entry — the same one the HUD tracker shows. Two quests
  active at once means the second one's conditions are not being watched at all, including if the
  first has no definition. This is a real limitation, not a subtlety.
- **Every rebind is a full teardown first, never an incremental top-up.** A `Health` subscribed
  twice counts one death as two, and a "kill 3" stage then finishes on the second kill. Unbinds
  null-check each entry before touching it, because a `Health` or `Interactable` destroyed with its
  chunk is Unity's fake null.
- **Chunk changes are polled**, against remembered `CurrentChunkData` *and* `CurrentChunkInstance`
  references, for the reason in §5 — seven writers across six files, so no single hook catches
  them all.
- **`Kill` targets respawn with their chunk.** The count is seeded from `QuestProgress.StageProgress`
  so it survives a crossing or a load, but the actors are re-instantiated fresh, so leaving and
  returning re-arms them: a "kill 3" stage can be finished by killing one respawning actor three
  times. **Author kill stages against targets in a single chunk** and expect nothing better.
- **`SetStageProgress` deliberately raises no `OnQuestsChanged`.** Nothing renders `StageProgress` —
  the journal and the HUD tracker both show `Objective` — so an event per kill would force a HUD
  layout rebuild for no visible change. If a counter ever appears in the UI, raise it there.
- **Do not author a quest that completes itself twice.** A last stage that completes the quest
  *and* a dialogue node with a matching `CompleteQuestId` is a double completion. It is harmless
  today — `CompleteQuest` early-returns on an already-complete quest and `RewardsClaimed` stops a
  double pay — but it is still wrong, and nothing warns. Progress and completion being *split* is
  fine and is exactly the shape `Collect` wants.
- **`Resources/Quests/` ships in the build**, like everything reachable from a `Resources/` folder.
  **Never add a `GameObject`, `Sprite`, `Prefab` or `AudioClip` field to `QuestDefinition`** — one
  prefab reference drags its whole dependency graph in. `ItemData` is already Resources-resident and
  is the only asset reference a definition may hold. Same reasoning as `PlacementPresetLibrary`
  keying by string (§13).
- **The three new `QuestProgress` fields are appended, and `SaveGameManager` needed no change** —
  see §6.
- **Re-granting a quest no longer rewinds its objective.** `DialogueManager` re-shows a
  conversation's starting node every time, so a `GrantQuestId` choice stays selectable forever.
  `StartQuest`'s existing-quest branch used to overwrite `Objective` unconditionally, so talking
  to the giver again mid-quest reverted the journal and the HUD tracker to stage 0's text while
  the watcher stayed bound to a later stage — the player followed an objective that could no
  longer complete, and the surviving `StageProgress` was invisible. It now only refreshes the
  objective while `StageIndex` and `StageProgress` are both 0. **Those are only ever non-zero for
  a definition-driven quest**, which is what keeps the tutorial's re-activation path (§6) working
  unchanged.

### Open issues, found in review and not fixed

None of these can corrupt a save. All were found reviewing the branch before merge.

- ⚠️ **`Stages[0].Objective` is never displayed.** The opening objective comes only from
  `DialogueChoice.GrantQuestObjective`, which — unlike `GrantQuestTitle` — has no empty-string
  fallback, and nothing reads the first stage's `Objective` at all. Leave that dialogue field
  blank and the HUD tracker shows an **empty objective line** until stage 0 happens to complete.
  `QuestDefinition`'s tooltip claims otherwise and is wrong for the first stage of every quest.
  **Until this is fixed, always fill in `GrantQuestObjective` on the granting dialogue choice**,
  and keep it identical to `Stages[0].Objective`.
- ⚠️ **A `TalkTo` final stage completes the quest on the interact, before any choice is picked.**
  `Update` runs while paused, so the advance lands a frame after the dialogue panel opens. If that
  same NPC also carries the `RequiredItem` + `ConsumeRequiredItem` + `CompleteQuestId` hand-in,
  the player walks up, presses Interact, backs out — and keeps the item, gets the reward, and
  never hands anything over. **Author hand-ins as `Collect` last + dialogue completes** (§14's
  recommended shape), never `TalkTo` last against the hand-in NPC. Nothing warns.
- **`QuestDefinition.Title` / `Giver` / `Location` are dead fields.** Nothing reads them; the
  journal reads `QuestProgress.Giver`/`.Location`, which come from the dialogue speaker name and
  `GrantQuestLocation`. Fill them in and the journal still shows "Unknown". Their tooltips lie.
- **The second active quest is invisible as well as unwatched.** `QuestTrackerUI` uses the same
  `GetActiveQuest()` the watcher binds, and `_quests` is insertion-ordered and never compacted —
  so whichever quest was accepted first holds both the tracker and the watcher until it ends.
  Accept a villager's side quest before a quest-giver's and the second one's objectives silently
  never advance. Nothing can hit this today — no quest is grantable at all — but with the
  eight-strong London cast queued (§13) it becomes likely the moment two of them can talk.
- **A kill can be dropped if a rebind lands in the same frame.** `Rebind` runs before
  `ApplyPending`, and `BindKill` re-seeds the count from `StageProgress`, which is one frame
  behind. Killing a target on the same frame as an edge crossing or an `OnQuestsChanged` discards
  that kill, silently. One-frame window, so rare.
- **`Assets/Resources/Quests/README.txt` ships in the build** as a `TextAsset` — 16 lines, so the
  cost is nil, but it is a doc file inside a `Resources` folder in the very system whose rule is
  that `Resources/` is not a place to put things. Move it to `docs/` when convenient.

---

## 15. Dialogue graphs

**Landed on `fix/dialogue-graph-ids`, and play-tested.** The owner ran the `spark_of_talent`
tutorial questline in the editor on this branch — the Daniel Pauls intro, the branch that grants
the quest, and the `TeachSpark` reward conversation — so the branch compiles, `MagicTutorial`'s
node building is correct, and `DialogueManager`'s id resolution works on a real branching
conversation. ⚠️ **The authoring surface is a different matter and is NOT exercised**: no
`DialogueData` asset has ever been hand-authored, convergence and cycles have never run, and
`PresetDialogueTools` has not been used since the flattening. The traps below were found by
review, not by play, and every one of them lands on the first person to write a conversation in
the Inspector.

`DialogueData` used to be a tree of `DialogueNode`
objects stored *by value* — `DialogueChoice.NextNode` was a nested `DialogueNode`, not a
reference — which made two problems structural rather than incidental: no two choices could ever
converge on the same node (no hub-and-spoke, the most common CRPG dialogue shape), and Unity
2022.3.20f1's nested custom-class serialization depth caps at 7, which a branching conversation
burns through in roughly three exchanges. Zero `DialogueData` assets existed anywhere in the
project at the time this was found — confirmed by a repo-wide GUID search — so this was a free
rename with nothing to migrate and no `[FormerlySerializedAs]` needed. That window is now closed;
any future rename of these fields needs the usual §7 treatment.

**The format is now flat.** `DialogueData.Nodes` is a `List<DialogueNode>`; each `DialogueNode`
carries a string `Id`. `DialogueChoice.NextNodeId` (a string, was `NextNode`, a nested object)
names the node a choice leads to. `DialogueData.StartNodeId` (default `"start"`,
`DialogueData.DefaultStartId`) names the opening node; `DialogueData.StartNode()` resolves it,
falling back to `Nodes[0]` and warning if `StartNodeId` is set but matches nothing.
`DialogueData.FindNode(id)` is a linear scan, deliberately — a conversation is tens of nodes, this
runs once per button press while the game is already paused, and a `Dictionary` would need
invalidating on every Inspector edit for a benefit too small to measure (§4's mobile-first
discipline applied even though this isn't a hot path). An empty or null `NextNodeId` is now the
**only** way a conversation ends — the old "or the next node has empty `DialogueText`" fallback
was deliberately dropped; nothing in the codebase relied on it.

- **Convergence is the point, and cycles are legal — but a cycle with no exit freezes the game.**
  Two choices can both name the same `NextNodeId`, and a node can eventually loop back to an
  earlier `Id` (hub-and-spoke, `A -> B -> A`, etc.) — `DialogueManager.DisplayNode` is driven by
  button clicks, never a recursive call stack, so there is no *call-stack* cycle guard and none is
  needed. ⚠️ **That says nothing about the exit.** `EndDialogue()` is private with exactly two
  call sites, both inside `OnChoiceSelected`; there is no Escape handler, no close button and no
  external caller, and `PauseManager` holds `Time.timeScale` at 0 throughout. So a conversation
  ends only via a choice with an empty `NextNodeId`, an unresolvable id, or the auto-generated
  "End conversation." button on a node with **no choices at all**. Author `hub -> shop -> hub`
  and forget a farewell on the hub, and the only way out is force-quitting the app, losing
  everything since the last autosave. **Rule: every cycle must contain at least one ungated choice
  that ends the conversation.** Nothing validates this. The same freeze is reachable without a
  cycle, and always has been: a node whose only choice is `RequiredStat`- or `RequiredItem`-gated
  renders `btn.interactable = false` with no other button.
- ⚠️ **An unset `Id` or `NextNodeId` silently means "end the conversation".** Unity serializes an
  unset string as `""`, not null, and `string.IsNullOrEmpty(nextNodeId)` is the *legitimate*
  terminator — so a hand-authored node whose two short string fields were never filled in looks
  fine, shows every choice button, and closes the chat on any of them, with every branch below it
  unreachable and **nothing logged**. The design is asymmetric in the wrong direction: a *typo'd*
  id warns loudly, an *unset* one says nothing at all. If `Nodes[0].Id` happens to be set to
  `"start"` (the natural thing, since `StartNodeId` already defaults to it) even the
  `StartNodeId`-mismatch warning disappears, leaving zero console signal.
- **A duplicate `Id` within one `DialogueData` is an authoring error nothing validates.**
  `FindNode` returns the first match by list order; every other node sharing that `Id` is silently
  unreachable. No importer or inspector check catches this — keep ids unique by hand until
  something does. ⚠️ Suspected, and worth one minute in the editor to confirm: Unity's list `+`
  button duplicates the **last element** rather than adding a blank one, which would make a
  duplicate `Id` the *default* outcome of adding a node — and would copy the source node's whole
  `Choices` list with it, including any `GrantQuestId` / `CompleteQuestId` /
  `ConsumeRequiredItem` side effects, onto a node they were never authored on.
- ⚠️ **A choice with `ConsumeRequiredItem` must never be reachable twice.** `RemoveItem` runs
  unconditionally whenever a selectable choice is picked, while `CompleteQuest` early-returns once
  the quest is complete (§14). Re-opening a conversation could already do this; what cycles add is
  that a hub can now be revisited *within a single conversation*. Hand over 5 of an item at a hub,
  loop back, and if the player was carrying 10 the choice re-renders as satisfiable — picking it
  again destroys 5 more, completes nothing, and reports nothing.
- **The twelve `DialogueChoice` side-effect fields are an existing §14 save/quest contract and must
  not be renamed without the usual serialized-field treatment (§7).** `RequiredStat`,
  `RequiredStatLevel`, `RequiredItem`, `RequiredItemQuantity`, `ConsumeRequiredItem`,
  `GrantQuestId`, `GrantQuestTitle`, `GrantQuestObjective`, `GrantQuestLocation`, `TeachSpark`,
  `CompleteQuestId`, plus `ChoiceText` itself — none of these changed name, type, attribute or
  order in the flattening; only `NextNode` → `NextNodeId` changed. `QuestConditionWatcher` and
  `QuestDefinition` document the `RequiredItem`/`ConsumeRequiredItem`/`CompleteQuestId` string
  contract in comments (§14) and were not touched by this work.
- **`MagicTutorial` builds its five conversations (`_intro`, `_nudge`, `_reward`, `_done`,
  `_underHousedTalk`) at runtime**, via local helpers (`Tree`/`Node`/`Choice`/`QuestChoice`/
  `RewardChoice`) that assign each node an id automatically (`"n" + a monotonic counter`) and
  collect them into the enclosing `Tree(...)`'s `Nodes` list. This relies on C# evaluating method
  arguments left-to-right and fully before the enclosing call runs: every nested `Node(...)` call
  inside one `Tree(...)` expression fires — pushing into a pending-nodes list — before `Tree()`
  itself runs and drains that list into the new `DialogueData`. **Keep every `Node()` call inside
  the `Tree(...)` argument list it belongs to** — a `Node()` called outside that expression, or a
  second `Tree(...)` started before the first one's nodes are drained, would misfile nodes between
  conversations. The dialogue prose in `BuildData()` itself is untouched by any of this; only the
  helper bodies below it changed.
- **Two things now catch the traps above — a runtime net and an author-time check.** Neither has
  run in the editor yet.
  - **`DialogueManager.CanEscapeFrom`** is a BFS over *currently pressable* choices from the node
    being displayed, looking for anything that ends the chat (empty `NextNodeId`, an id that
    resolves to nothing, or a node with no choices). If none is reachable, `DisplayNode` appends
    an "End conversation." button that the author did not write. It is a **safety net, not an
    authoring feature** — a graph that needs it is still wrong, and the player gets an ending
    nobody wrote. Gating is judged as it stands rather than structurally, because within one
    conversation the player's position only ever gets worse (`ConsumeRequiredItem` takes items,
    nothing gives any back), so a route shut now will still be shut on arrival. The visited set is
    keyed on **node identity, not `Id`** — duplicate ids are legal-but-broken (above), and keying
    on them would let one node stand in for another and cut the search short. Both collections are
    reused fields, per §4.
  - **`Assets/Editor/DialogueValidator.cs`** — `Tools/GBA/Content/Validate Dialogue` over every
    asset, plus `CONTEXT/DialogueData/Validate This Conversation` for the one in front of you.
    Errors: no nodes, a node with no `Id`, a duplicate `Id`, a dangling `NextNodeId`, and a node
    with no route out. Warnings: an unresolvable `StartNodeId`, an unreachable node, a node whose
    every exit is gated, and a `ConsumeRequiredItem` choice sitting on a node inside a cycle.
    **`DialogueValidator.Validate` is public and UI-free on purpose** — the plain-text importer is
    meant to call it and refuse a bad script rather than write the asset. Keep it that way.
  - **`PresetDialogueTools` no longer overwrites existing dialogue text at all.**
    `WriteConversation` adopts whenever any node already carries prose, blank incoming line or not.
    An earlier version of this line said it "no longer blanks prose", which was true only of the
    empty-string case and left the line-replaces-line route — an orphan asset holding a
    hand-rewritten one-liner, a preset with a filled `AmbientLine` and a null `Conversation` —
    still clobbering it. The cost of the wider guard is that regenerating an orphan means deleting
    it by hand; that is the right way round, since the alternative destroys writing silently.
    `EnsureAmbientConversation` now reports adoption through an `out bool` so Create Starter
    Presets lists it rather than leaving it to a console warning.
- **No `[SerializeReference]`.** It was considered and rejected: it serializes the target's
  assembly+namespace+class name into the asset, and §10 records an open, not-yet-done intention to
  rename the `ExiledAlvaston` namespace across 46 files — introducing `[SerializeReference]` here
  would make that future rename silently null every dialogue link. It also produces opaque
  `rid:`-keyed YAML (worse to diff) with no built-in Inspector support for polymorphic references.
  Per-node sub-assets and integer indices into `Nodes` were considered too, for the same
  reasons §7 already warns about with enums: reordering silently repoints edges, and a future
  plain-text importer wants to write `-> shop`, not `-> 7`.
- **`PresetDialogueTools.WriteConversation`** (the only tool that writes a `DialogueData` asset to
  disk) writes one node with `Id = DialogueData.DefaultStartId` and `StartNodeId` set to match, and
  now refuses to overwrite an asset that already holds more than that — `HasAuthoredContent` checks
  for more than one node, or a single node that already offers a choice, and bails with a warning
  instead of clobbering a hand-written branch the next time the ambient-line generator runs over
  the same preset.
  ⚠️ **The guard cannot see a hand-edited *one-liner*.** A conversation a human rewrote as a single
  node with no choices is byte-for-byte the same shape as generator output, so it reads as
  regenerable and `data.Nodes.Clear()` takes the prose with it. Reaching that needs
  `preset.Conversation` to be null first — nothing clears it automatically, so the route is narrow —
  but if you improve a line by editing the asset rather than the preset's `AmbientLine`, **update
  `AmbientLine` to match**, or add a second node so the guard can see it. `EnsureAmbientConversation`
  returns false when it adopts an existing conversation rather than writing one, so Create Starter
  Presets reports what actually happened instead of claiming it generated from the ambient line.
  ⚠️ **"Update `AmbientLine` to match" does not save you on the right-click route.**
  `CONTEXT/PlacementPreset/Create Dialogue` passes `""` when `AmbientLine` is blank, so it can
  overwrite hand-written prose with an **empty string** — the guard is structural and never sees
  the line at all. Seven of the fifteen NPC presets currently have a blank `AmbientLine`, so this
  is the live shape, not a corner. Its own doc comment claims it "mints an empty tree to start
  writing in"; what it actually mints is a one-node tree with empty text, which is precisely the
  shape `HasAuthoredContent` classifies as regenerable — so anything begun that way is unprotected
  until a second node or a choice is added.
  Also worth knowing before anyone tidies presets into subfolders: **`PathFor` keys the generated
  asset on the preset's filename only, not its path**, so two same-named presets in different
  folders would share one `Dialogue_<Name>.asset` and the second generation would overwrite the
  first. Unreachable today — all 23 presets are flat in `Assets/Data/Presets/`.
- **Adopting an existing conversation mutates the preset but is reported as nothing.**
  `EnsureAmbientConversation` returns false on the adopt path — correct, it did not write the
  line — but it still does `preset.Conversation = data; SetDirty(preset)`, and
  `StarterPresetGenerator.GenerateAmbientConversations` only lists presets when the return is
  true. So the end-of-run summary, which is the part actually read, omits that a preset was just
  wired to a conversation. The only trace is a `Debug.LogWarning` in a console that will also be
  carrying a "has no Speaker" warning per preset from the same run.
- **Corrections found while writing this section (2026-08-03):** the warning block near the top of
  this file said neither Daniel Pauls' nor the tutorial geezer's art existed yet — both now do,
  `Preset_DanielPauls` and `Preset_TracksuitGeezer` carry resolved `NpcSprite`/`NpcController`
  references (see the correction inline at §13's top-of-file warning). §12's "who this changes"
  table listed the tutorial geezer's row as "sheets not delivered" — same correction; whether that
  art declares an `Attack` state specifically was not re-verified.
