# Implementation plan — ambient traffic and car theft ("Grand Theft Corsa")

**Status: plan only, nothing implemented.** Ambient cars drive authored routes through a chunk;
the player can stop one, hotwire it via a minigame, and drive off — which triggers a police
response. Landed in phases, one verification pass in the editor.

```
Grounded against: main @ 1ac6ecf, working tree 2026-08-12.
Verification:     every claim carries the file and line it was read at. There is no C# compiler,
                  no Unity and no test framework here — see §10.
```

---

## 1. Scope

**In**

1. Chunk-owned ambient traffic: cars spawn from authored routes, drive waypoints, despawn at the
   route end, respawn on a jittered interval. `Home_London` only.
2. Player-blocking: a car brakes when the player stands in its lane, honks on a rate limit, waits,
   and resumes when the player moves.
3. Car theft: while stopped, the car is interactable; the hotwire minigame opens; success converts
   the car into a rideable vehicle and auto-mounts it; timeout raises the alarm.
4. A fleeing driver villager spawns on successful theft.
5. A police response: **2 knives** on success (two officers), **1 knife** on alarm timeout.
6. Driving presentation: the 3D model stays visible while ridden; the rider's sprite hides.
7. Two car tiers (`car_1` common, `car_2` better) with per-car hotwire difficulty and specs.

**Out**

- Police car pursuit. A future phase; the design leaves `WantedManager.SpawnPlod` untouched so a
  police car can be added cleanly later.
- Car damage, car health, collisions with NPCs. Villagers wander; cars would never move if they
  braked for them.
- Traffic outside `Home_London`. Other city chunks are future authoring — no code needed.
- Persisting owned cars. The recorded "Nicking does not persist" decision
  (`CONSEQUENCES_AND_MOUNTS.md`) stands: a stolen car is yours until the chunk reloads.
- Any witness system. Deliberately removed from the codebase; not reintroduced.
- Fixing the standing `IsPolice` defect on the five `Police_*.prefab` assets. That is the owner's
  Inspector pass, never this work.
- Any change to `WantedManager`, `MapChunkData`, the seven chunk-instantiation paths, or the
  police prefabs.

**New scripts:** three runtime (`TrafficRoute`, `TrafficCar`, `HotwireMenuUI`) and one editor
(`BuildTrafficCarPrefabTool`). Each new `.cs` ships with its `.meta` (hand-authored GUID if no
Unity is available — goes on the CLAUDE.md §5 ledger).

---

## 2. What was verified, and the constraints that shape this

### Confirmed

| Claim | Verified at |
|---|---|
| The mount/vehicle stack is complete and reusable: `MountController` owns ride state, `VehicleController` applies effects, `VehicleSpawner` spawns chunk-owned vehicles | `Assets/Scripts/World/MountController.cs`, `VehicleController.cs`, `VehicleSpawner.cs` |
| Mounting an `IsOwnedByNPC` vehicle already spikes knives and toasts | `VehicleController.OnMounted` `VehicleController.cs:174-209` |
| `VehicleController.VehicleName`'s default is literally `"Vauxhall Corsa"` — cars were always the intent | `VehicleController.cs:18` |
| `WantedManager.SpikeKnives()` raises knives by one, caps at 5, and spawns one officer per call | `Assets/Scripts/Systems/WantedManager.cs:78-86`, `:121-151` |
| The pickpocket minigame is the precedent: code-built Win95 canvas, no scene wiring, no pause push, single guarded `Close()`, `onClosed(expired)` callback | `Assets/Scripts/UI/PickpocketMenuUI.cs` |
| `PickpocketInteractable` self-subscribes to `Interactable.OnInteract` in `Awake` — the only route that survives serialization | `Assets/Scripts/World/PickpocketInteractable.cs:47-60` |
| `NpcFactory.Build` builds an NPC from a `PlacementPreset` at runtime, including `Roams` wander | `Assets/Scripts/World/NpcFactory.cs:29-66` |
| Riding is drawn by hiding `ParkedModel` and layering a sprite over the rider's feet | `VehicleController.OnMounted` `VehicleController.cs:193-199`; `WorldActorVisual.SetMounted` |
| A chunk-owned vehicle unparents on mount and rejoins the chunk on dismount | `VehicleController.cs:205-206`, `:220-228` |
| Chunk instances are destroyed on transition by all seven paths; anything parented to the instance dies with it | `CLAUDE.md` §3 "The chunk world" |
| `EKVibe` is the home for tuning constants | `CLAUDE.md` §2; `Assets/Scripts/Vibe/EKVibe.cs` |
| The art agent cannot produce 3D; car models arrive by the owner's route into `Assets/3DModels/` | `AGENTS.md`; `docs/art/ART_QUEUE.md` |
| A rusty double-decker bus GLB already exists as a test subject until cars land | `Assets/3DModels/out london rubbish/rusty+double+decker+bus+3d+model.glb` |

### Constraints that shape the design

- **Chunk lifetime is the key constraint.** Anything parented to the chunk instance is destroyed
  on transition by all seven paths. Traffic wants exactly that: born and destroyed with the chunk,
  no persistence, no cross-chunk state. `TrafficRoute` lives in the chunk prefab and spawns cars as
  its own children, so **no chunk-instantiation path needs to change**.
- **Never `SetActive(false)` a vehicle root.** `OnDisable` clears the speed multiplier, so the
  vehicle cancels its own boost the instant it is mounted. The 3D-car presentation therefore hides
  the *rider's renderer*, never the vehicle root.
- **No per-frame allocation.** The braking check is pure math (`InverseTransformPoint`), no
  `FindObjectOfType` in loops.
- **No `Physics2D` / `Rigidbody2D`.** Movement is on X/Z with a kinematic `Rigidbody.MovePosition`
  in `FixedUpdate`.
- **Appends only.** No save keys, no enum reordering, no serialized-field renames. `VehicleData`
  gains fields with safe defaults; the EBike asset simply reads the defaults.

---

## 3. The gameplay loop

1. Cars spawn from `TrafficRoute`s in Home_London (weighted: `car_1` common, `car_2` rare), drive
   the waypoints, despawn at the route end, respawn on a jittered interval. Chunk-owned: born and
   destroyed with the chunk instance.
2. Player stands in the road → the car brakes (pure-math check), honks on a rate limit, waits.
   Player moves → the car resumes after a short delay.
3. While stopped, the car's `Interactable` is live: **"Nick the …"** → the hotwire window opens:
   N wires × 2–4 taps each against the car's clock. No pause push (pickpocket rule). Walking off
   closes it cleanly; the car drives on.
4. **Success:** the window closes → a driver villager spawns at the door and wanders off → the car
   converts to a rideable vehicle and auto-mounts (3D model stays visible, rider sprite hidden) →
   **2 knives, two officers**, toast.
5. **Timeout:** the alarm goes off → **1 knife**, the car is hotwire-locked for 30 s and pulls away.
6. The stolen car is then exactly the nicked e-bike: chunk-edge riding works, dismount rejoins the
   chunk, never saved.

---

## 4. Agreed decisions (owner-specified)

| # | Decision |
|---|---|
| A | Owner supplies `car_1` and `car_2` GLBs into `Assets/3DModels/`. `car_2` is the better car: higher ride speed, faster in traffic, rarer on the road, harder to hotwire. |
| B | Successful theft spawns a **random fleeing villager** (the dragged-out driver) beside the car. |
| C | Hotwire minigame mirrors `PickpocketMenuUI`, with **per-car difficulty** driven by fields on `VehicleData` (wires + clock), so better cars are harder. |
| D | `Home_London` only. Other chunks are future authoring, no code needed. |
| E | Routes are authored in the chunk prefab as `TrafficRoute` components with child waypoint transforms + gizmos. |
| F | Successful theft = **instant 2 knives** = two `SpikeKnives()` calls, which from a clean state spawns two officers (tier 1 PCSO, then tier 2 Bobby). If already wanted, each call caps at 5 as today. Alarm timeout = **1 knife** (attempted theft, lesser than success). |

---

## 5. New runtime code

### `World/TrafficRoute.cs`

Lives in the chunk prefab. Spawns cars as its own children on a timer; cars `Destroy` themselves at
the final waypoint. No singleton, no chunk polling — it is born and dies with the chunk instance.

```csharp
[System.Serializable]
public class TrafficCarEntry
{
    public Data.VehicleData Car;
    [Tooltip("Relative spawn weight. car_1 = 3, car_2 = 1.")]
    public int Weight = 1;
}

public class TrafficRoute : MonoBehaviour
{
    [Tooltip("Ordered child transforms = waypoints. Cars spawn at index 0 and despawn past the last.")]
    public List<Transform> Waypoints;   // populated from children in Awake
    public List<TrafficCarEntry> Cars;
    [Tooltip("Villager presets for the fleeing driver. Empty = no driver.")]
    public List<Data.PlacementPreset> DriverPresets;
    public int MaxAlive = 2;
    public float SpawnInterval = 12f;
    public float SpawnJitter = 4f;

    // Update: count live children; when below MaxAlive and the timer elapses, pick a weighted
    // entry, Instantiate its Car.ChassisPrefab at Waypoints[0], call car.Configure(entry.Car, this).
    // Gizmos: draw the waypoint path in Scene view.
}
```

### `World/TrafficCar.cs`

On the car prefab root alongside a dormant `VehicleController` + `Interactable` + kinematic
`Rigidbody` + `BoxCollider`.

```csharp
public class TrafficCar : MonoBehaviour
{
    public float BrakeDistance = 6f;        // EKVibe.TrafficBrakeDistance
    public float LaneHalfWidth = 1.6f;      // EKVibe.TrafficLaneHalfWidth
    public float ResumeDelay = 1.5f;        // EKVibe.TrafficResumeDelay
    public float HonkInterval = 4f;         // EKVibe.HonkIntervalSeconds

    private TrafficRoute _route;
    private VehicleController _vehicle;
    private Interactable _interactable;
    private int _waypointIndex;
    private float _cruiseSpeed;
    private bool _stopped;
    private float _resumeAt;
    private float _nextHonkAt;
    private bool _hotwireLocked;
    private float _lockoutUntil;

    public void Configure(Data.VehicleData data, TrafficRoute route) { ... }
    // FixedUpdate: MovePosition along waypoints, face travel direction, Destroy at route end.
    // Braking: InverseTransformPoint(player.position) — brake if the player is within BrakeDistance
    //   ahead and inside the lane half-width. Stopped => enable Interactable; blocked => honk toast
    //   per HonkInterval; clear => resume after ResumeDelay.
    // TryHotwire(): self-subscribed to OnInteract in Awake (PickpocketInteractable pattern).
    //   Opens HotwireMenuUI.Show(name, wires, seconds, onClosed).
    // ConvertToPlayerVehicle(): swap OnInteract to VehicleController.Toggle, MarkChunkOwned(),
    //   spawn driver, SpikeKnives() x2 + toast, MountController.Get().Mount(vehicle).
}
```

### `UI/HotwireMenuUI.cs`

Near-verbatim shape of `PickpocketMenuUI`: code-built Win95 canvas, no scene wiring, no
`PauseManager.Push`, single guarded `Close()`, `onClosed(expired)` callback. `Show` takes
`wires`/`seconds` **from the car**, not globals. Rows = wires; each wire rolls its taps from the
EKVibe min/max.

---

## 6. Data & spec changes

### `VehicleData.cs` — append-only

The EBike asset gains safe defaults; no mapping table needed.

```csharp
[Tooltip("Keep the 3D model visible while mounted, hiding the rider instead. For cars.")]
public bool KeepModelVisibleWhileMounted = false;

[Tooltip("Cruise speed while driving as traffic, in m/s.")]
public float TrafficSpeed = 7f;

[Tooltip("Hotwire minigame: number of wires to work loose.")]
public int HotwireWires = 3;

[Tooltip("Hotwire minigame: seconds on the clock.")]
public float HotwireSeconds = 6f;
```

### Spec table the builder tool seeds (tune in the Inspector)

| Field | Reliant Robin (common) | Vauxhall Corsa (better) |
|---|---|---|
| `SpeedMultiplier` (ridden) | 3.0 | 3.75 |
| `TrafficSpeed` | 7 | 8.5 |
| `HotwireWires` | 3 | 4 |
| `HotwireSeconds` | 6 | 5 |
| Route spawn weight | 3 | 1 |

### `EKVibe.cs` — global constants only

`HotwireMinTaps=2`, `HotwireMaxTaps=4`, `HotwireRetryLockoutSeconds=30`, `HonkIntervalSeconds=4`,
`TrafficBrakeDistance=6`, `TrafficLaneHalfWidth=1.6`, `TrafficResumeDelay=1.5`.

### `VehicleController.cs` — small edits

In `OnMounted`, when `KeepModelVisibleWhileMounted`: keep `ParkedModel` visible, instead call new
`WorldActorVisual.SetRiderHidden(true)` (disables `ActorRenderer` only). Un-hide in `OnDismounted`
**and** in the `OnDisable` cleanup path. The vehicle root is never deactivated; the standing rule
holds.

### `WorldActorVisual.cs` — one new method

`SetRiderHidden(bool)` — disables/enables `ActorRenderer` only. Never touches the vehicle root.

---

## 7. Editor tooling

### `Tools → Place → Build Traffic Car Prefab` (`Assets/Editor/`)

New files only, never overwrites. Takes the selected car model asset → builds
`Prefabs/ModernBritain/TrafficCar_<name>.prefab` (model child + the four components wired) and a
`VehicleData` asset beside the e-bike's, seeded from the spec table. Run once per car; `car_2`
values via a small prompt or by editing the asset after. This tool exists because the GLB GUIDs
don't exist until Unity imports them — the implementer must not hand-author prefab YAML against
unknown GUIDs.

### Route authoring (owner, in-editor, Prefab Mode on `Home_London_Prefab` — edit in place)

Add two `TrafficRoute` children (one per direction along the high street pavement strips),
waypoint empties along each, endpoints tucked behind boundary walls/edge gates so despawn is
off-screen. The ortho view is small (`EKVibe.CameraOrthoSize = 4`), so this is achievable.

---

## 8. Hard-rule register for the implementer

- **No save keys, enums or renames touched.** Appends only, as listed. No save-format change at all.
- New `.cs` files ship with their `.meta` (hand-authored GUIDs if no Unity — goes on the §5 ledger).
- No `Physics2D`/`Rigidbody2D`; movement on X/Z; kinematic `Rigidbody.MovePosition` in `FixedUpdate`.
- No per-frame allocation: no `FindObjectOfType` in loops, braking check is pure math.
- Do **not** touch police prefabs or the standing `IsPolice` defect (owner's Inspector pass), the
  seven chunk paths, `WantedManager`, or `MapChunkData`.
- The fleeing driver is built by `NpcFactory` only — never hand-assembled — so it stays in step
  with the preset system.
- Toast strings are functional placeholders — owner wordsmiths (prose rule).
- Death-while-mounted is a **known, deferred issue** (Stage F) — inherited by cars, not fixed here.

---

## 9. Phasing

1. **Traffic ambience** — `TrafficRoute`, `TrafficCar` (drive/brake only), EKVibe constants, prefab
   builder tool, route authoring in Home_London. *(Playable: cars drive, stop for you, drive on.)*
2. **Theft** — `HotwireMenuUI`, `TryHotwire`, conversion, driver spawn, 2-knife wiring.
3. **Driving presentation** — `VehicleData` appends, `VehicleController` + `WorldActorVisual.SetRiderHidden`.
4. **Docs + verification** — below.

---

## 10. Verification (honest version)

**There is no C# compiler, no Unity, and no test framework in the agent environment.** Reference
integrity passing says nothing about whether the project builds. Everything below needs the Unity
editor and therefore needs a human. Say so plainly rather than implying otherwise.

### 10.1 Agent-runnable

```bash
python Tools/asset_reachability.py --check-dangling   # before and after; exits 1 on breakage
```

### 10.2 Owner check list (Unity editor)

1. **Compile on open.** Confirm Unity accepts the new scripts and their hand-authored `.meta` files
   rather than minting new ones.
2. **Run the builder tool twice** (`Tools → Place → Build Traffic Car Prefab`), once per car model.
   Confirm `TrafficCar_car_1.prefab` / `TrafficCar_car_2.prefab` and their `VehicleData` assets
   exist with the spec-table values.
3. **Author two routes** in Prefab Mode on `Home_London_Prefab` (edit in place — never
   delete-and-resave). Confirm the gizmos draw and the waypoints sit on the pavement strips.
4. **Traffic ambience.** Enter Home_London: cars spawn, drive the route, despawn at the end,
   respawn on the interval. `car_2` is visibly rarer and faster than `car_1`.
5. **Braking.** Stand in the road: the car brakes, honks (rate-limited), waits. Move away: it
   resumes after the delay. Stand in the lane again: it brakes again.
6. **Hotwire success.** While stopped, interact: the window opens with the car's wires/clock.
   Complete it: the driver villager spawns and wanders off, the car converts and auto-mounts, the
   3D model stays visible, the rider sprite hides, **2 knives** appear and **two officers** spawn.
7. **Hotwire timeout.** Let the clock run out: the alarm fires, **1 knife**, the car is
   hotwire-locked for 30 s and pulls away.
8. **Driving.** Ride the stolen car across a chunk edge and back; dismount; leave the chunk and
   return — the stolen car is gone, traffic has resumed fresh.
9. **Device Simulator.** Confirm the hotwire window is reachable with a thumb in landscape, and
   that the honk toast does not overlap the HUD cluster.
10. **`car_2` difficulty.** Confirm `car_2` has more wires and a shorter clock than `car_1`.

### 10.3 Documentation updates

- `docs/reference/CONSEQUENCES_AND_MOUNTS.md` (canonical owner): new "Traffic and car theft"
  section + verification-header downgrade (code-review only until an editor session).
- `docs/README.md`: add a row to the plans table.
- `CLAUDE.md` §5: ledger entry with the owner check routes above.

---

## 11. Explicitly out of scope

Police car pursuit (future phase — the design leaves `SpawnPlod` untouched so it can be added
cleanly), car damage, NPC braking, traffic outside Home_London, persisting owned cars, witness
systems, fixing the `IsPolice` prefab defect.