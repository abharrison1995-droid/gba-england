# Chunk world

```
Last verified against: working tree, 2026-08-17; the ground/road visuals section added
                       2026-08-25
Verification scope:    code (read line by line); chunk prefabs and MapChunkData assets (tracked
                       YAML). Edge-crossing behaviour was play-tested in an earlier editor
                       session — but NOT since ChunkTravelKind was added on 2026-08-15, which
                       changed OnChunkTransition's signature and has never been compiled.
                       The 2026-08-04 height and EnemyAI changes are UNVERIFIED.
                       The portal-marker, mounted-refusal and MapChunkRegistry sections landed
                       2026-08-09 and have NEVER been compiled or run. "No DungeonPortal is
                       placed anywhere" was re-checked by GUID scan on 2026-08-15 and still holds.
                       "Ground and road visuals" is read from the prefab and material YAML and
                       has NOT been seen in an editor — see the ledger entry for the two parts
                       of it that are inference rather than fact.
                       ChunkBeingBuilt/ContentChunkName and the container-cooldown ticks landed
                       2026-08-17 and have NEVER been compiled or run.
                       Manor_Cellars' Coordinates (-1,-1 -> -1,-99) and the eleven off-grid
                       interiors' Coordinates (X: -2 -> -3) were edited directly in the tracked
                       YAML on 2026-08-20 to free the overworld region grid's West York column.
                       Read, not compiled or run. The MapOfBritainUI consequence for Manor_Cellars
                       (readable in this file's Manor_Cellars entry) is reasoned from its layout
                       code, not observed on screen.
```

Discrete chunks, **220×220 units** (`EKVibe.ChunkSize = 220f`). One chunk is live at a time.
Movement is on the X/Z plane; chunk edges are `pos.x` / `pos.z`.

## The data

`MapChunkData` (ScriptableObject, `Assets/Data/Chunks/`) holds `ChunkName`, `Coordinates`,
`IsCity`, `ChunkPrefab`, `VehicleSpawns`, and **explicit `NorthChunk` / `SouthChunk` /
`EastChunk` / `WestChunk` references**.

**Adjacency is authored by reference, not computed from `Coordinates`.** `Coordinates` is only a
dictionary key for city lockout timers. It is **not** a save key — `ChunkName` is.

**Eleven overworld chunks across the 5×5 Britain Region Grid:**
Centered around `Home_London` (0, 0 — the hub, `IsCity: 1`):
- `Hyde_Park_Jungle` (0, 1): Overgrown jungle parkland, yellowed dirt track.
- `Barren_Lands_MK` (-1, 0): Bleak Milton Keynes wasteland, yellowed dirt road.
- `Commie_Slum_Bolshevik` (1, 0): High-density brutalist towers, asphalt road.
- `Commie_Slum_Menshevik` (0, -1): Post-war council estates, asphalt crossroads.
- `The_Peaks` (-1, -1): Rugged mountains / Cornish folk, yellowed dirt track.
- `OpenData_Draughtlands` (1, -1): Tech compound / server perimeter, asphalt road.
- `East_York` (0, -2): Sino-Yorkshire hub (`IsCity: 1`), Yorkstone pavement.
- `Knob_Moor` (-1, -2): Wild moorland / Hob Moor spin, yellowed dirt road.
- `West_York` (-2, -2): Northern gritstone mill town (`IsCity: 1`), regular city roads.
- `Brighton` (2, -2): Coastal seaside hub (`IsCity: 1`), regular city roads.
- `Manor_Cellars` (-1, -99): Tutorial dungeon, reached by `InstanceDoor`.

`Manor_Cellars.Coordinates` was moved off `(-1,-1)` on 2026-08-20 to clear that cell for the
overworld region grid (see [NAME_UNIFICATION_PLAN.md](../plans/NAME_UNIFICATION_PLAN.md)-adjacent
region work) and parked at `Y: -99`, mirroring `Castle_Fight_Arena`'s existing convention for a
coordinate nothing else will ever claim. Unlike `Castle_Fight_Arena`, **`Manor_Cellars.EastChunk`
is wired to `Home_London`** (one-directional — `Home_London.WestChunk` is `Barren_Lands_MK`, not this),
so `MapOfBritainUI`'s BFS still reaches it whenever the player opens the map from inside it, and
draws it as a real, if distant, graph node rather than an isolated one. That view was already
non-orthogonal before this move (an "EastChunk" link diagonal to `(-1,-1)`); after this move the
same view's auto-fit will additionally compress every other visited node into a tight cluster
opposite `Manor_Cellars` for that one screen. **Unverified** — `MapOfBritainUI` has never been
compiled or run; this is read from its layout math, not observed.

**Six interior shells,** added 2026-08-09 and **empty apart from their shell**. Five are the named
London locations from [ART_QUEUE.md](../art/ART_QUEUE.md) band 6; `The_Winchester` is the sixth, and
is not in that list.

| Chunk | Coords | Floor | What it is |
|---|---|---|---|
| `Quidland` | (-3,-1) | 24×16 | Pound shop that sells weapons |
| `FU_Sports` | (-3,-2) | 26×18 | Sports shop that sells armour |
| `City_Hall` | (-3,-3) | 34×24 | Mayor Swalls and Councillor Mosley |
| `Police_Station` | (-3,-4) | 30×22 | Commissioner Spencer, Riggs, Murtaugh |
| `Gang_Hideout` | (-3,-5) | 18×14 | Ralph and Sanjeet — Sanjeet's mum's house |
| `The_Winchester` | (-3,-6) | 20×14 | The pub |

This table predates five more interiors added since (`Mosleys_Lab_Basement`,
`Abandoned_Bus_Station`, `Mosley_Mansion`, `DP_Academy`, `Abandoned_Church`) that share the same
off-grid column — moved to `X: -3` alongside the six above on 2026-08-20, still `Y: -7` through
`Y: -11` respectively, still all-null adjacency. Not re-tabulated here; this row count was already
stale before this edit and fixing it is a separate task.

Each is a floor, four walls at 3.2 m, a `RuntimeNavMeshBaker` on the root and one id-less
`PlayerSpawn`. All four adjacency slots are null and none carries a `ChunkEdge` — the only way in is
a portal, and **none is wired yet**. Their off-grid `Coordinates` are cosmetic: `Coordinates` is
only a key for city lockout timers, and those are gated on `IsCity`, which is 0 on all six.

**`IsCity: 0` on an interior is correct and does not launder the wanted level.** It once would
have: the evasion rule read `IsCity` alone, so a door out of London would have cleared the player's
knives. It now also requires the transition to be an edge crossing, and a portal is not one — see
[CONSEQUENCES_AND_MOUNTS.md](CONSEQUENCES_AND_MOUNTS.md). **Do not set `IsCity: 1` on an interior
to work around anything**; it would put the chunk on the lockout-timer path and make casting magic
inside drain concealment.

⚠️ **`The_Winchester` interior does not replace the pub as it works today.** `PubInteractable`
(`Pub_TheWinchester.prefab`, not currently placed in any chunk) clears the wanted level, heals and
saves from a single USE. Putting it behind a door is a design change nobody has made — the shell
exists, the decision does not.

## Seven runtime paths instantiate a chunk

Two do the full job. Five are direct replacements. `grep -rn "Instantiate(.*ChunkPrefab"` is how
this table is checked.

| Path | Entry point | Pauses | Notifies Wanted | Autosaves | Snaps camera | Ticks container cooldowns |
|---|---|---|---|---|---|---|
| Edge crossing | `ChunkManager.TransitionToChunkRoutine` | yes | yes, as `EdgeCrossing` | yes | yes | **yes** |
| USE door / portal | `DungeonPortal` → `ChunkManager.TravelTo` → `TravelRoutine` | yes | yes, as `Portal` | yes | yes | **yes**, given back on abort |
| Manor instance door | `GameFlowController.EnterManorCellars` | no | no | yes | no | no |
| Tutorial exit | `GameFlowController.LoadLondonAtWestGates` | no | no | yes | no | no |
| Continue / load | `SaveGameManager.LoadWorld` | no | no | no | no | no |
| New-game fallback | `DeathScreenUI.OnNewGame` | no | no | no | no | no |
| Cold boot | `ChunkManager.Start` | no | no | no | no | no |

**If you add or change transition behaviour you must touch all seven, or consolidate them first.**

`OnChunkTransition` takes a `ChunkTravelKind` (declared beside `Direction` in `ChunkManager.cs`)
saying **how** the player travelled, and it is a required parameter with no default. Only
`EdgeCrossing` can shake the police — a door is not an escape. An eighth path that wants to notify
the wanted system has to choose a kind deliberately; see
[CONSEQUENCES_AND_MOUNTS.md](CONSEQUENCES_AND_MOUNTS.md), which owns that rule.

`ChunkManager.Start` instantiates the scene's authored starting chunk when `CurrentChunkInstance`
is null and the flow state is `Playing`. It writes `CurrentChunkInstance` but **not**
`CurrentChunkData`.

Two editor tools also instantiate chunks: `PlaytestHubWindow` (`Tools → Debug → Playtest Hub` —
replaced `DevZoneJump` on 2026-08-20, consolidating it with the enemy/NPC spawner and the wanted
level debug tool into one window) and `DiscoverEnglandSetup`.

⚠️ **There is no `ChunkTransitionDoor` in this repository.** The generic USE-driven door is
`DungeonPortal`. It adds its own `Interactable` if one is missing and routes through
`TravelRoutine`, which does the same full lifecycle as an edge crossing — so it is a second
canonical path, not a shortcut, and the closest thing to a working model for a building door.

**No `DungeonPortal` is placed anywhere in the project.** Not in any chunk prefab, not in
`c.unity`. A GUID scan for `1208538c…` across `Assets/` returns nothing, and `git log -S` says the
last one — the self-targeting `Portal_Home_London` that earlier revisions of this document warned
about — was removed in `8bd1520` on 2026-08-05. The runtime path is therefore **entirely
unexercised**: it compiles and is wired, and nothing has ever pressed USE on it.

`Preset_PortaltoManorCellars.asset` is the one portal the palette can stamp, and it has never been
stamped.

## Portal travel: named markers

`DungeonPortal` has two ways to say where the player lands, and only one of them is worth
authoring:

| Field | Behaviour |
|---|---|
| `TargetSpawnPointId` | Resolves a `PlayerSpawnPoint` **by exact id** inside the newly instantiated destination, and takes its rotation as arrival facing. |
| `SpawnPosition` | A raw `Vector3`. Used only when `TargetSpawnPointId` is empty. |

A marker moves with the geometry it belongs to; a raw coordinate stops matching the building the
moment the building is nudged, and nothing says so. `TargetSpawnPointId` is the field to fill in.

⚠️ **A non-empty `TargetSpawnPointId` that does not resolve aborts the journey.** It does not fall
back to `SpawnPosition` — falling back is how a typo delivers the player into a wall in silence.
`ChunkManager.TravelRoutine` instantiates the destination, resolves the marker, and **commits
nothing until it has one**: wanted state, `CurrentChunkData`, the visited list, the encyclopedia
toast and the autosave all happen after the check, and the candidate instance is destroyed again on
failure. The player stays exactly where they were, with a `Debug.LogWarning` naming the chunk and
the id.

⚠️ **That ordering has a consequence the abort safety does not pay for: during the destination's
`Awake`, `CurrentChunkData` is still the chunk the player is leaving.** Every `Awake` in the new
chunk runs synchronously inside the `Instantiate`, which happens first. Content that resolves its
own chunk — a container building a save key, anything similar added later — would key itself under
the origin chunk, silently and only on this one path of the seven.

`ChunkManager.ChunkBeingBuilt` is set around that `Instantiate` and cleared in the routine's
`finally`, and **`ChunkManager.ContentChunkName` is what content must ask** — it prefers
`ChunkBeingBuilt` and falls back to `CurrentChunkData`. The other six paths assign
`CurrentChunkData` before they instantiate, so they need nothing; deliberately, only `TravelRoutine`
sets the field, because setting it in seven places is seven things to keep in step.

This is why the lookup is `PlayerSpawnPoint.FindExact` and not `PlayerSpawnPoint.Find` — `Find`
falls back to the id-less default point and then to the first point in the chunk, which is right
for "put the player somewhere sensible" and wrong for a named door.

Arrival facing is applied through `CombatController.FaceTowards`, not by writing
`transform.rotation`: the controller keeps its own facing vector and the billboarded sprite is
flipped from that, so a rotation set behind its back turns nothing and is reverted by the next
input.

⚠️ **A portal refuses while the player is mounted** — "Get off the vehicle first." The vehicle is a
separate root that would be stranded in a chunk about to be destroyed, and the obvious workaround
(hiding or disabling it) is the one thing that must never be done to a vehicle root.

## Resolving a chunk by name

`ChunkManager.FindChunkByName` consults two sources, in order:

1. **`ChunkManager.AllChunks`** — the array on the ChunkManager in `c.unity`. Authoritative for
   everything already authored there.
2. **`MapChunkRegistry`** (`Assets/Resources/MapChunkRegistry.asset`) — a `ScriptableObject` list
   loaded by `Resources.Load`.

The registry exists because `AllChunks` can only be edited with `c.unity` open, and interiors are
authored from Prefab Mode where it is not. `ChunkManager.EnsureKnownChunk` patches `AllChunks` at
runtime on arrival, but **only for that run** — a save made inside a chunk that reached the list
that way cannot be loaded after a restart. The registry is what closes that.

`Tools → Place → Portal Placement` adds both ends of a link to it automatically, and creates
the asset if it is missing.

## To react to a chunk change, poll — do not hook

`CurrentChunkData` is a public serialized field written from **eight places across six files**:
both `ChunkManager` routines, `GameFlowController` ×2, `SaveGameManager`, `DeathScreenUI`, and the
two editor tools. Any one hook misses the others.

Turning the field into a property to raise an event would stop Unity serialising the scene's
authored starting chunk, so that is not the fix either.

`VehicleSpawner` and `VehicleController` both compare against a remembered reference instead —
cheap, and it catches load-game and the arrest return for free. Watch `CurrentChunkInstance` too
if a reload of the *same* chunk matters to you (dying in Home_London and respawning into it).

## Edge crossings

All six chunk prefabs carry all four `ChunkEdge` triggers at ±109 (2 units deep, `IsTrigger`), and
every outer chunk links back to Home. The historic failures were behavioural and all had one
shape: **`OnPlayerHitEdge` declines a crossing and the trigger never fires again.**

Current behaviour:

- `ChunkEdge` re-offers the crossing from **`OnTriggerStay`** as well as `OnTriggerEnter`. The
  manager's `_isTransitioning` and grace-window guards dedupe, and arrival always lands 3.5 units
  clear of the perimeter, so it cannot ping-pong. **Never add a `Debug.Log` to that path** — it
  fires every physics tick.
- **Arrivals clamp the lateral axis.** Preserving the crossing's lateral coordinate used to land
  the player inside the new chunk's *perpendicular* edge trigger when crossing near a corner.
- Post-arrival grace is **0.25s**. A full second ate the return trip if you turned straight round.
- Dead ends, tutorial locks, and city lockouts all call `ShowWarning(...)`, **throttled to one
  every 3 s**, because the player now stands pinned against the boundary wall inside the trigger
  volume and `OnTriggerStay` re-fires every tick.
- Every chunk prefab carries `BoundaryWall_North/South/East/West` — invisible solid walls on all
  four sides, generated by `Tools/World/Add Chunk Boundary Walls` and committed. Edge triggers
  sit at ±110.2 (inner face at 109.8) and the boundary wall inner face is at 110, so the player
  contacts the trigger 0.2 units before hitting the wall. Where a neighbour exists, the transition
  fires before the wall blocks; where it is declined, the wall stops the player while
  `OnTriggerStay` keeps re-offering. The tool is idempotent, edits prefabs in place, and also
  refreshes edge trigger positions and sizes on existing prefabs.
- `ChunkManager.Update` teleports anyone below `y = -20` to the chunk's `PlayerSpawnPoint`,
  falling back to the origin.

## A chunk root cannot be suspended with `SetActive(false)`

Chunks are only ever **destroyed**, never suspended, and the code reflects that. A bare
`SetActive(false)` on a chunk root breaks four systems at once:

| System | Cleans up in | What a deactivated root does |
|---|---|---|
| `EnemyAI` | — | `StartCoroutine(PerceptionRoutine())` runs **only in `Start`**. Deactivating stops it; reactivating does not re-run `Start`, so every enemy is permanently blind. |
| `RuntimeNavMeshBaker` | `OnDestroy` (and `Rebake`) | `_instance.Remove()` is never called on disable, so an inactive chunk keeps its NavMesh registered — and every chunk instantiates at the origin, so meshes overlap. |
| `TutorialSequence` | `OnDestroy` | Sets its static `Instance` in `Awake` and clears it only on destroy, so the singleton keeps pointing at a disabled object. |
| `EnemyNameplate` | `OnDestroy` | Builds an **unparented scene-root** `GameObject("Nameplate")`, so it is not a child of the chunk and does not hide with it. |

Two more things are not chunk-owned at all and would leak across any suspend:

- **Police.** `WantedManager` creates them with `Instantiate(prefab, spawnPos, Quaternion.identity)`
  and no parent.
- **`Assets/c/NavMesh.asset`.** `c.unity`'s single `NavMeshSettings` block registers it for the
  life of the scene regardless of which chunk is loaded. This is the hard structural obstacle:
  London's baked mesh and a compact interior mesh cannot both be registered at the shared origin,
  and nothing in code registers London's — the scene does.

`Interactable` is the one part already suspend-safe: `Active` is added on `OnEnable` and removed
on `OnDisable`.

Doing this properly needs explicit suspend/resume/evict hooks. That design — plus a location
cache, return stack, encounter ledger and corpse-loot lifecycle — is written up in
[../plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md](../plans/BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md).
**None of it is implemented.** Read it before touching chunk lifetime; treat its phases as
architect-first work.

## Ground and road visuals

An outdoor chunk's visuals are three things: a `Ground` plane at scale 22 (Unity's plane is 10x10,
so 220x220 m), optional strips under `Environment/Paths`, and an optional square patch under
`Environment/Details` covering the seam where two strips cross. All of it is built by
`Tools → World → Generate Chunk Prefab`.

⚠️ **Tiling belongs to the material, not the renderer.** A material assigned to two chunks tiles
identically on both, and there is no per-chunk override — Unity would need a MaterialPropertyBlock
or a material instance, and neither survives into a prefab as a serialized value. This has two
consequences that look like bugs if you do not know them:

- **A 1x1 ground material stretches one image across the whole 220 m plane.** Six chunks shipped
  with `Asphalt.mat` as their ground and therefore had a single enormous photograph of a road for a
  backdrop. Ground materials tile **80 x 80** — one tile per 2.75 m.
- **Strips of different lengths need different materials**, because the tiling that puts one tile
  per 10 m of a 220 m road puts one per 5 m of a 110 m one. Hence `Road_Asphalt` (22 x 1),
  `Road_Asphalt_Stem` (11 x 1) for East York's T-junction stem, and `Road_Asphalt_Patch` (2.8 x 2.8,
  plain tarmac with no markings) for the junction squares.

**Every strip runs along its local +X and is rotated about Y to point it**, rather than being
modelled along Z. A north-south road is scale `(220, 0.04, 10)` with a 90° yaw, not
`(10, 0.04, 220)` with none. That is what lets every road on every bearing share one material: the
tarmac in the texture runs along U, so it has to run along local X on the mesh.

Strips sit at `y=0.04` and junction patches at `y=0.06`. Two strips crossing at the same height are
coplanar and z-fight, which is the whole reason the patch exists.

⚠️ **A road `MeshRenderer` must be a complete block.** Sixteen of them were hand-written stubs that
stopped after `m_Materials`, and every one rendered magenta while the `Ground` beside it, carrying
the same material, rendered correctly. If you write prefab YAML by hand, copy a renderer Unity
wrote — do not write a minimal one and trust the defaults.
