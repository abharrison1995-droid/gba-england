# CLAUDE.md — Exiled Alvaston

Guidance for Claude Code sessions in this repo. Written from a codebase audit (2026-07-26),
revised the same day after the consequence mechanics were recovered from a stash and landed.
Facts here are verified against code, not against design docs. Where code and a design doc
disagree, this file records **what the code actually does**.

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
| `Discover England` | `EKVibe.DisplayTitle`, `DiscoverEnglandSetup.cs`, `Tools/Discover England/` menu | In-game title shown to player |
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
                      #   ItemData, DialogueData, PlayerClass
    Dialogue/         # DialogueManager
    Flow/             # GameFlowController, PlayerSession, SaveGameManager
    Quests/           # QuestManager
    Systems/          # PauseManager, WantedManager
    UI/               # UIManager, HUD, joystick, inventory, title/creator/death screens
    Vibe/             # EKVibe — central const/colour/tuning table
    World/            # ChunkManager, ChunkEdge, doors, nameplates, billboards
  Editor/             # editor-only tools (no asmdef — see below)
  Data/Chunks/        # 6 MapChunkData .asset files
  Prefabs/Chunks/     # 6 matching chunk prefabs
  Prefabs/ModernBritain/  # police tiers, Nosey Parker, moped, pub — see §6
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
- **Editor menu path**: `Tools/Exiled Alvaston/...` (existing tools also use
  `Tools/Combat`, `Tools/World`, `Tools/Art`, `Tools/Discover England` — inconsistent)
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

**Not saved:** `PlayerSession.TutorialComplete`, quest state, inventory, wanted level.
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
| Grand Theft Moped | `World/VehicleController` | Mounting an `IsOwnedByNPC` vehicle spikes Knives and grants `SpeedMultiplier`. |
| Pub safehouses | `World/PubInteractable` | A pint clears Knives + concealment, heals, and saves. |
| Arrest | `Flow/GameFlowController.ArrestRoutine` | Death dealt by an `EnemyAI.IsPolice` attacker (tracked via `Health.LastAttacker`) arrests instead of killing: clears wanted level, despawns police, returns you to the cellars. |

### Known issues in these systems (verified, all open)

- **Stealth is keyboard-only.** `StealthController.Update` reads `Input.GetKeyDown(KeyCode.C)`,
  with its own comment noting mobile needs a UI button. On a touchscreen-first game this makes
  stealth unreachable — and since `TryPickpocket` requires `IsCrouched`, **pickpocketing is
  unreachable on mobile too.**
- **`MovementSpeed` has no single owner.** `StealthController` and `VehicleController` both
  multiply `CombatController.MovementSpeed` in place and cache their own "original". Mount a
  moped while crouched and the restore writes back a corrupted base. `VehicleController` has
  no `Unmount`, so its 2× boost is permanent once taken.
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

Multi-agent workflow: **audit → issue → branch → plan structural risk → small single-concern
commits → review against plan → document why → close the loop.**

- Architect (Opus): scopes, produces plan/mapping table, flags structural risk. No code.
- Implementer (Sonnet): works strictly from the plan, small commits, no scope improvisation.
- Reviewer: reviews diff against the plan, hunting silent failure modes — orphaned references,
  broken GUIDs, save incompatibility — not just style.

Before any rename/refactor touching §6 or §7, produce an explicit mapping table first.

A rename to **GBA: England** (Great British Annals) is under consideration. Notes if it
proceeds: the `ExiledAlvaston` namespace appears in 46 `.cs` files and **zero serialized
assets**, so a namespace rename is safe — Unity binds scripts by `.meta` GUID, not type name.
What is *not* safe is `Home_Alvaston`, which is a `ChunkName` and therefore a save key (§6).
A colon is illegal in Windows paths and git repo names, so any repo/folder would be
`gba-england` with `GBA: England` only as a display string.
