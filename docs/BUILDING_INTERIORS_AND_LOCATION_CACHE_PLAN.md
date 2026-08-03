# Building Interiors, Location Cache and Corpse Loot Plan

> **STATUS: APPROVED DESIGN — NOT IMPLEMENTED.**
>
> This document describes the intended architecture for enterable buildings, cached locations,
> corpse looting and repeatable-location resets. It records decisions for a later implementation;
> it does not claim that the runtime currently behaves this way.

## 1. Goal and first use case

The first use case is an enterable London police station:

1. A 3D police-station exterior sits inside `Home_London_Prefab`.
2. The player approaches its entrance and the existing USE interaction offers
   `Enter Police Station`.
3. USE suspends the exact live London instance and activates a compact, self-contained police
   station interior chunk.
4. USE at the interior exit resumes that same London instance and returns the player to a named
   marker immediately outside the original door.

The interior is a `MapChunkData`-backed prefab, but it is not an overworld grid square. It can be
small, needs no `ChunkEdge` triggers, and does not need to fill `EKVibe.ChunkSize`.

This architecture must also scale to quest buildings and future dungeons without allowing cache
eviction, app restart or door re-entry to regenerate rewards accidentally.

## 2. Scope

### In scope

- Explicit USE-to-enter building doors.
- Compact interior chunk prefabs.
- An active/suspended/evicted location lifecycle.
- A return stack that can restore the source doorway.
- Mobile-bounded caching: initially one active location plus one pinned suspended location.
- Explicit suspend/resume/evict hooks for location-owned systems.
- Corpse interaction that holds the final death frame until looted or the area is left.
- A lightweight encounter/loot ledger independent of the GameObject cache.
- Deliberate reset policies for story and repeatable locations.
- Save/load support for resuming inside a building.

### Out of scope for the first implementation

- Additive Unity scenes or Addressables.
- Keeping an unbounded number of locations alive.
- Seamless cutaway roofs or true walk-in 3D building shells.
- A general procedural-dungeon generator.
- Reworking the whole wanted system or making the police station the arrest destination.

## 3. Verified current baseline

The current runtime has useful pieces, but not the proposed cache:

- `World/DungeonPortal` uses the range-based `Interactable` system and calls
  `ChunkManager.TravelTo`.
- `ChunkManager.TravelRoutine` performs the full generic portal lifecycle: pause, wanted
  notification, instantiate destination, teleport, camera snap, destroy previous chunk and save.
- `InstanceDoor` is a Manor-Cellars-specific automatic trigger and its serialized
  `Destination` enum must not become a list of every building.
- `GameFlowController.EnterManorCellars`, `GameFlowController.LoadLondonAtWestGates`,
  `SaveGameManager.LoadWorld` and the legacy death-screen fallback still replace chunks directly.
- `Home_London_Prefab` contains a `Portal_Home_London` whose target is `Home_London_Data` itself.
  It reloads and resets Home; it is an authoring trap, not the model for an interior door.
- `Health.Die` currently destroys ordinary enemies after `DestroyDelay`.
- `LootOnDeath` currently opens the loot menu immediately and does not leave a reusable corpse.

No cache, return stack, encounter ledger or corpse-loot lifecycle described below exists yet.

## 4. Location model

Each location has three independent layers:

| Layer | Owns | Lifetime |
|---|---|---|
| Definition | `MapChunkData`, prefab, authored entrances and content | Asset lifetime |
| Live instance | GameObjects, AI, NPC positions, temporary effects, corpse visuals | Active or cached in memory |
| Runtime state | Stable enemy/chest/door state and reset eligibility | Session and, where required, save file |

Destroying the live instance must not imply that its runtime state resets. That separation is the
central protection against door-reentry and app-restart loot exploits.

### Location states

- **Active:** the one rendered/simulated location. Its physics, AI, interactables and NavMesh are
  registered.
- **Suspended:** retained in memory but not simulated or rendered. Mutable state is frozen, its
  interactables are unavailable, and its NavMesh is unregistered.
- **Evicted:** the GameObject root is destroyed. A later recreation must apply the lightweight
  runtime state before the player can interact with it.

For the first mobile implementation, keep at most:

- one active location; and
- one pinned suspended return location.

The immediate return location is pinned and cannot be removed by the normal LRU policy. After the
player returns to London, the police-station interior becomes unpinned and eligible for eviction.
Device profiling, rather than prefab count, decides whether a larger cache is ever justified.

## 5. Transition and return flow

### Enter building

1. Validate the door, destination, player and mounted-state policy.
2. Push a stable return frame.
3. Run leave/suspend hooks on the source location.
4. Suspend and pin the source instance.
5. Resume a cached destination or instantiate its prefab and apply its runtime-state ledger.
6. Set `CurrentChunkData` and `CurrentChunkInstance` to the destination.
7. Teleport the Rigidbody to a named entrance marker and apply authored facing.
8. Register the destination NavMesh and resume its location-owned systems.
9. Snap the camera, restore input and checkpoint the new return frame only after the state is
   coherent.

### Exit building

1. Run leave cleanup on the interior, including the corpse rule in §9.
2. Pop the return frame.
3. Suspend the interior.
4. Resume the cached source when present; otherwise instantiate it and apply its runtime state.
5. Resolve the named outside-door marker, teleport/facing the player there, then snap the camera.
6. Checkpoint after the source location, popped return frame and leave-cleanup ledger mutations are
   all coherent.

### Return frame

Save stable identifiers, not GameObject references:

- source `ChunkName`;
- source doorway/marker ID;
- fallback return position and facing;
- destination `ChunkName`; and
- optional encounter/run ID for repeatable content.

Arrest, death, new game, tutorial restart and an unrecoverable load fallback must explicitly clear
or replace this stack. A save made inside an interior must serialize enough of the frame to make
the exit work after a cold app restart, when no cached GameObject can exist.

## 6. Lifecycle hooks are required

Blindly calling `SetActive(false)` on a chunk root is unsafe in the current runtime:

| Current system | Suspension problem |
|---|---|
| `Interactable.Active` | Correctly unregisters on `OnDisable`; this part is already cache-friendly. |
| `EnemyAI` | Starts its perception coroutine only in `Start`; a root deactivate/reactivate stops it without starting it again. |
| `RuntimeNavMeshBaker` | Removes its registered NavMesh only in `OnDestroy`; an inactive cached chunk would leave an overlapping mesh at the shared origin. |
| Scene-baked London NavMesh | `Assets/c.unity` automatically registers `Assets/c/NavMesh.asset` for the life of the scene, so unregistering only runtime-baked interior meshes would still leave London navigation active under the station. |
| `EnemyNameplate` | Builds an unparented scene-root visual and removes it only when the enemy is destroyed. |
| `MagicTutorial` / `TutorialSequence` | Hold static `Instance` references that clear only on destruction. |
| Scene-root police | Are not owned by the chunk being suspended and can survive into another location. |

The implementation needs explicit lifecycle participation, conceptually:

```text
OnLocationSuspend
OnLocationResume
OnLocationEvict
```

The cache controller must call these around root activation. Suspension must unregister the
location's NavMesh, stop resumable routines, hide or suspend auxiliary visuals and detach no
state into the active location. Resume must reverse that work exactly once.

The first implementation must put **all** navigation data under the same location lifecycle. In
particular, preserve the existing `Assets/c/NavMesh.asset` GUID but replace its permanent
scene-level auto-registration with an explicitly registered `Home_London` NavMesh handle. Suspend
must remove that handle before an interior NavMesh is registered; resume adds it back. At no point
may the permanent scene NavMesh and a compact interior NavMesh be registered together at the
shared world origin. An alternative spatial-separation design would need its own reviewed plan;
it is not the default assumed here.

Do not treat this as permission to `SetActive(false)` a ridden vehicle root. Building entry should
be blocked while mounted (or use an explicitly designed dismount transaction) before the source
location is suspended.

## 7. Cache eviction is not a dungeon reset

Evicting a cached instance frees GameObjects. Reinstantiating its prefab without state would
restore every authored enemy and chest, creating a farming exploit. Therefore eviction and reset
are separate operations.

Update the ledger in the same operation as every durable state mutation, and flush leave-cleanup
changes before suspension. Eviction takes a final consistency snapshot, but it is not the first
time state is captured. Record stable state such as:

```text
Location: PoliceStation_Interior
  Enemy_Reception_01 = defeated, loot forfeited
  Enemy_Cells_01 = alive
  Chest_Evidence_01 = entries 0 and 2 taken
  Door_Cells = unlocked
```

Every stateful authored object needs a stable ID within its location. Renaming an ID after release
is a persistence migration, not cosmetic cleanup.

### Reset policies

| Location type | Reset policy |
|---|---|
| Story building / one-off dungeon | Quest-controlled or never |
| Named unique reward | Consumed state persists in the save |
| Repeatable dungeon | Explicit new-run event or configured in-game cooldown |
| Ambient encounter | Deliberate area cooldown, if desired |

Neither cache eviction nor app restart is a reset event. A reset must clear the appropriate ledger
entries as an explicit gameplay operation.

Suspension is not durable storage: the app can close while an instance is merely cached. Defeating
an enemy, taking a loot entry, unlocking a durable door and forfeiting corpse loot on leave must
therefore update the ledger immediately. Reward mutations must also trigger an immediate save (or
an equally durable journal write) rather than waiting for a later LRU eviction.

## 8. Save-system requirements

`SaveGameManager` currently saves one `ChunkName` and player position. Interior support adds two
classes of durable state:

- return-stack data needed to exit after loading inside; and
- encounter/loot records whose rewards must not regenerate after restart.

Checkpoint rules are part of the transition contract:

- entry saves after the destination and pushed return frame are coherent;
- exit saves after the source is restored, the frame is popped and leave cleanup is recorded; and
- each durable reward mutation saves or journals its updated ledger record immediately.

This means a cold restart cannot recover a prefab state older than the last enemy defeat, loot
take or area-leave forfeiture merely because the live location had not yet been evicted.

Every interior must also be resolvable through the persistent chunk registry. Runtime-only
`EnsureKnownChunk` is insufficient after an app restart. New `ChunkName` values are permanent save
keys and must be frozen before assets ship.

Suggested first key, to confirm before authoring:

| Asset | Proposed `ChunkName` | Save consequence |
|---|---|---|
| `PoliceStation_Interior_Data` | `PoliceStation_Interior` | Permanent new key; must remain registered and must not be renamed without migration. |

Fields added to `MapChunkData`, save DTOs or other serialized types need new stable names and
backward-compatible defaults. Existing public field names stay unchanged, and serialized enums
are append-only because their numeric ordering is persistent.

## 9. Corpse and loot lifecycle

### Required player-visible behavior

1. Lethal damage stops combat, navigation and physical blocking.
2. The enemy enters its non-looping Death animation.
3. The animator reaches and holds the final death frame.
4. The enemy nameplate is hidden.
5. A dedicated range-based `Interactable` offers `Loot <name>`; it does not need the disabled
   combat collider.
6. Remaining loot entries live on the corpse and survive closing/reopening the menu.
7. Taking an entry updates inventory and its ledger record as one operation, then immediately
   checkpoints both; taking every entry removes the corpse after the final pose has been shown.
8. Enemies with no loot still remain on their final pose until the player leaves the location.
9. Active → Suspended is the definition of leaving: remaining corpses are removed and unclaimed
   corpse loot is forfeited.
10. The death operation immediately records the enemy as defeated, and leave cleanup records any
    remaining loot as forfeited/exhausted, until its location reset policy permits a new encounter.

The existing generated animation assets are compatible with the visual goal: death clips are
non-looping and their Death states have no return transition. The current blockers are lifetime
and interaction behavior, not the artwork.

### Current incompatibilities

- `Health.Die` schedules `Destroy(gameObject, DestroyDelay)` for ordinary enemies.
- It disables all child colliders, so corpse interaction must use the existing collider-free
  range interaction rather than reusing combat collision.
- `LootOnDeath` builds entries in a local list, opens the menu immediately and supplies no
  persistent corpse interaction.
- `LootChest` state is also instance-local, so eviction requires ledger integration for any chest
  whose rewards must remain depleted.

Preserve the serialized `Health.DestroyOnDeath` and `Health.DestroyDelay` field names even if their
future use narrows; renaming or removing them would silently alter existing prefabs.

## 10. Police-station decisions

- The exterior art deliverable is only the outside shell, signage and a clear door/threshold
  anchor. The interior is a separate Unity-side chunk prefab.
- Entry is explicit USE, not automatic overlap teleportation.
- The interior is marked city-equivalent under the current `IsCity` model so entering it does not
  clear wanted level as city-to-wilderness evasion.
- Ridden vehicles cannot enter.
- Exterior pursuing police must not leak into the station as scene-root enemies. Interior guards
  own station enforcement; the exact pursuit/arrest response remains a gameplay decision.
- The exterior and interior each carry named spawn/return markers placed several units clear of
  the paired door to prevent immediate re-entry.
- Interior saves are supported, so return and reward state must be serialized.

## 11. Implementation sequence

1. **Transition foundation:** introduce stable destination/return markers and a return-frame data
   model; route generic doors through one canonical transition service.
2. **Cache lifecycle:** add active/suspended/evicted management with one pinned return instance and
   explicit lifecycle hooks; make AI, every NavMesh source, nameplates and chunk-owned controllers
   resume-safe.
3. **Encounter ledger:** assign stable state IDs, journal each durable mutation, flush on leave,
   restore after instantiation and implement explicit reset policies.
4. **Save integration:** persist return frames and durable reward state at entry, exit and reward
   mutation checkpoints; register every interior through the same source used by load.
5. **Corpse interaction:** replace timed destruction/automatic loot opening for lootable enemies
   with final-frame corpses and reusable loot interaction backed by the durable ledger.
6. **Police-station content:** create the data asset and compact interior prefab, add the exterior
   USE door and paired named markers, then populate the interior.
7. **Legacy consolidation:** move Manor entry/exit, load, death and arrest paths onto the same
   lifecycle or make their deliberate exceptions explicit.

Each phase needs architect → implementer → reviewer treatment. Do not combine the save/serialization
work with unrelated content or art commits.

## 12. Verification matrix

Command-line checks can prove only reference integrity:

```text
python Tools/asset_reachability.py --check-dangling
```

The following require Unity with Play stopped while authoring, followed by Play mode and an actual
mobile-device profile for performance:

| Scenario | Expected result |
|---|---|
| Enter station on foot | London suspends, station loads, player arrives inside clear of exit, camera snaps once. |
| Attempt entry mounted | Entry is blocked or completes the explicitly chosen dismount transaction; bike never appears indoors. |
| Exit station | Exact cached London instance resumes; NPC, chest and vehicle state matches pre-entry state. |
| Re-enter station | Cached or reconstructed station respects its encounter/loot ledger. |
| Kill enemy, wait | Death animation reaches and holds its final frame; no automatic loot menu. |
| Close corpse loot early | Corpse remains and offers only untaken entries on the next USE. |
| Loot corpse fully | Inventory receives each entry once and corpse is removed. |
| Leave corpse unlooted | Corpse is cleaned on suspend, loot is forfeited and enemy does not respawn before reset. |
| Evict and revisit | Fresh prefab applies ledger; depleted rewards do not return. |
| Save inside, restart, exit | Interior resolves, return frame restores the correct outside door and loot state remains exhausted. |
| Wanted entry/exit | Entering the London station does not clear wanted level or apply wilderness evasion. |
| AI after resume | Perception, movement and attacks work after suspend/resume; no duplicate coroutines. |
| NavMesh after repeated travel | Only the active location's NavMesh is registered; no overlap or accumulation. |
| Memory profile | One active plus one suspended location stays within target-device memory and avoids visible entry/exit hitches. |

No implementation should be described as verified until these editor/device checks have been run.
