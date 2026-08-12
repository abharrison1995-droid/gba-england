# Consequences, police, stealth, mounts and vehicles

```
Last verified against: working tree, 2026-08-12
Verification scope:    code; tracked prefab YAML. Mounting, dismounting, the boost, the prompt
                       flip and the data-driven spawner were play-tested in an earlier editor
                       session. The IsPolice defect below is read from prefab YAML and has NOT
                       been observed in play. The snitch removal is verified by GUID search and
                       `--check-dangling` only. The pickpocket minigame is code-review only —
                       no compiler and no editor have seen either, and no LootBand asset exists
                       yet, so the band path has never been taken. The traffic and car theft
                       section below is code-review only — no compiler and no editor have seen
                       it, and no TrafficCar prefab or VehicleData asset exists yet (the builder
                       tool creates them).
```

The GTA layer. Components live inside the `Prefabs/ModernBritain/` prefabs, whose instances are
placed in `c.unity` or nested in chunk prefabs. `Editor/ModernBritainSetup.cs` generated this
content originally; the scene already holds its output, so **you do not need to run it** — and
running it is destructive (see the delete-and-re-save hazard in
[SAVE_AND_SERIALIZATION.md](SAVE_AND_SERIALIZATION.md)).

## `WantedManager` is the hub

Two coupled meters:

- **Knives (0–5)** — the wanted level. `SpikeKnives()` raises it and calls `SpawnPlod()`, which
  instantiates `PolicePrefabs[Knives-1]` near the player. All five tiers are assigned in the
  scene: PCSO → Bobby → Armed Response → Occult Agent → Occult Commander.
- **Concealment (0–100)** — regenerates at `ConcealmentRecoveryRate`/sec. `DrainConcealment(amount)`
  lowers it; hitting zero resets it to full and spikes Knives.

**Casting magic is the trigger.** `CombatController` calls `DrainConcealment(34f)` on spell cast —
three spells busts you. This is the design's "magic stands in for GTA's guns", and it is the
single most load-bearing line in the whole consequence loop.

`WantedManager.ClearWanted()` clears both meters **and despawns the police**, and it has to:
`SpawnPlod` instantiates officers unparented at the scene root, so they survive a chunk
transition. A version that only zeroed the meters dropped the HUD knife readout to zero and left
Armed Response hunting the player. `PubInteractable` and `GameFlowController.ArrestRoutine` both
still clear inline and are unaffected.

## The systems

| System | Script | Behaviour |
|---|---|---|
| Stealth | `World/StealthController` | Crouch toggle: halves move speed. |
| Pickpocketing | `World/PickpocketInteractable` + `UI/PickpocketMenuUI` | Requires crouch. Rolls `CatchChance` first; failure spikes Knives before anything opens. Authored by ticking `Pickpocketable` on a `PlacementPreset`. |
| Grand Theft E-Bike | `World/VehicleController` + `World/MountController` | Mounting an `IsOwnedByNPC` vehicle spikes Knives and grants `SpeedMultiplier`. |
| Pub safehouses | `World/PubInteractable` | A pint clears Knives + concealment, heals, and saves. |
| Arrest | `Flow/GameFlowController.ArrestRoutine` | Death dealt by an `EnemyAI.IsPolice` attacker (via `Health.LastAttacker`) arrests instead of killing: clears wanted level, despawns police, returns you to the cellars. |

### Pickpocketing has two shapes, chosen by one field

`PickpocketInteractable.PickpocketBand` (copied from `PlacementPreset.PickpocketBand` by
`NpcFactory`) decides which:

- **No band** — the original behaviour, and what every mark authored so far does. One roll between
  `MinPounds` and `MaxPounds`, straight into the wallet, one toast, done.
- **A band** — `UI/PickpocketMenuUI` opens: one pounds pocket plus up to `EKVibe.PickpocketSlots`
  rolls of the band, each needing its entry's `TapsToFree` taps to work loose, against
  `EKVibe.PickpocketSeconds` on the clock.

Things to know before touching it:

- **The catch roll happens first**, before anything opens. Failing it spikes Knives and there is no
  minigame; the minigame is what a *successful* approach gets you.
- **A mark is marked robbed when the menu opens**, not when it closes. Leaving early is the
  player's choice and does not buy a retry.
- **Each pocket banks the moment it comes free.** Time running out costs only what was still stuck.
- **Running the clock out is being caught** — it spikes Knives. Every other exit (banking the lot,
  CLOSE, the dimmer, walking beyond `EKVibe.PickpocketRange`, the mark being destroyed) is a clean
  getaway with what was banked.
- ⚠️ **The menu does not push a pause**, unlike `LootMenuUI`, and that is deliberate: a paused world
  with a running clock is a contradiction and a paused world with a stopped clock is a free win. The
  timer uses `Time.deltaTime`, so if something *else* pauses the world the attempt waits with it.
  **Do not copy `PauseManager.Push`/`Pop` in from the loot menu.**
- Every exit funnels through one private `Close()`, guarded on `IsOpen`, so two exits in the same
  frame cannot fire the callback twice.

### The snitch mechanic is gone

There used to be a sixth system: a "Nosey Parker" civilian (`AI/NoseyParkerAI` on
`Prefabs/ModernBritain/NoseyParker.prefab`) who noticed a below-max concealment meter within
`DetectionRadius`, spent `ReportTime` dialling 999 and then called `SpikeKnives()`. **The script,
the prefab, its material and `Preset_NoseyParker` have all been deleted.** Nothing observes the
player and reports them any more — concealment still drains on a cast and still spikes Knives when
it hits zero, but no NPC is part of that loop.

This is a deliberate regression. A redesigned **NPC witness system** — which civilians notice
what, at what range, and what they do about it — is planned as separate work and is not in the
codebase in any form. Do not read the remaining concealment plumbing as a half-built version of it.

Crouch is reachable on mobile: the HUD has a **CRO** button
(`HUDActionButton.ActionKind.Crouch` → `UIManager.OnCrouchPressed` →
`StealthController.ToggleStealth`), built in code beside ATK and USE. It shows its state —
`EKVibe.ButtonBrownActive` and the label **STAND** while crouched — repainted by
`UIManager.RefreshCrouchButton`, which `ToggleStealth` calls, so the key and the button can never
disagree. `KeyCode.C` still works and is how it gets tested in the editor. This is also what makes
pickpocketing reachable on mobile, since `TryPickpocket` requires `IsCrouched`.

## Open defects

- ⚠️ **No police officer has `IsPolice` set, so arrest never fires.** All five `Police_*` prefabs
  carry `EnemyAI`, but only `Police_PCSO.prefab` serializes `IsPolice` at all and it is `0`; the
  other four predate the field and take the C# default, also false. `ArrestRoutine` is keyed off
  it, so dying to the police kills you instead of arresting you, and `WantedManager.DespawnPolice`
  destroys nothing. **Fix is ticking the box on all five prefabs in the Inspector** — never by
  re-running `ModernBritainSetup`.
- **Both payouts are live.** Pickpocketing pays into `PlayerSession.Pounds` via `AddPounds`, and
  the arrest fine (`EKVibe.ArrestFine`, £50) is taken via `SpendPounds`. The fine is **clamped to
  what the player is carrying** before it is spent, because `SpendPounds` is all-or-nothing and
  would otherwise refuse to fine a skint player at all; the release message reports what was
  actually taken. Neither is Unity-verified.
- `AbilityData` has no "is magic" flag — the 34-point drain is hardcoded in `CombatController`
  rather than driven by ability data.
- `TagManager.asset` has `tags: []` and no custom layers. Nothing currently needs them, but do not
  assume a layer exists.

## Movement speed has exactly one owner

Modifiers are keyed by source via `CombatController.SetSpeedMultiplier` / `ClearSpeedMultiplier`,
and movement reads `EffectiveMovementSpeed`. **`MovementSpeed` is a read-only base — never
multiply it in place.**

---

# Mounts and vehicles

The stealable vehicle is a hire e-bike ("Limey E-Bike"). It was a Deliveroo moped until
`EBike.prefab` was renamed; "moped" in a comment is describing history.

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
*chunk-owned*: it dies with its chunk and respawns at its authored spot next visit, so it needs no
homing. It unparents on mount (so riding across an edge cannot destroy it under you) and rejoins
whichever chunk you abandon it in. A vehicle hand-placed in the scene is *not* chunk-owned and
uses `ReturnsHomeOnChunkChange` + `ReturnHome` instead. **Do not merge these.**

`Home_London_Data.VehicleSpawns` carries the only e-bike entry, at `(0.31, 0, 22.07)`. There is no
hand-placed instance to fall back on: if no bike appears in Home_London, debug the spawner.

## Things that will catch you out

- **Never `SetActive(false)` a vehicle root** to hide it. `OnDisable` clears the speed multiplier,
  so the vehicle would cancel its own boost the instant it was mounted. Hide `ParkedModel`.
- **A mounted vehicle rides at distance zero**, so it wins `PlayerInteractor.FindClosest` every
  time. `Interactable.LowPriority` is what stops it masking pubs, doors and NPCs; the mounted
  vehicle sets it.
- **`PlayerInteractor` compares the prompt string, not just the target.** An interactable that
  rewrites its own `Prompt` without the closest one changing — exactly what mounting does — would
  otherwise leave the HUD stale.
- **`VehicleSpawner` tracks what each spawn entry produced.** Without that, riding a chunk's
  vehicle out and back mints a second one from the same entry, once per round trip.
- **The player must not gain a stray `SpriteRenderer` lookup.** `WorldActorVisual.ActorRenderer`
  exists because `GetComponentInChildren<SpriteRenderer>()` starts returning the layered vehicle
  sprite once one exists.
- **Riding is drawn by layering, and that is the decision, not a fallback.** The `cycle` sheet is
  cancelled. `WorldActorVisual.SetMounted` draws the vehicle sprite over the actor's feet whenever
  `MountedSprite` is null, which it is on every character. **Leave `MountedSprite` unassigned** —
  it writes `_sr.sprite`, which an Animator overwrites every frame, so using it would mean
  suspending the animator, and nothing does.
- **Riding plays the idle animation, by design.** `CombatController.ApplyLocomotionAnimation` holds
  `Speed` at 0 and sets `Cycling` only when the controller declares the parameter. With no `cycle`
  sheet there is no `Cycle` state and no `Cycling` parameter, so the rider idles under the bike
  sprite rather than running on the spot.
- **Nicking does not persist**, by decision. `IsOwnedByNPC` is cleared on the instance, and the
  instance is replaced when the chunk reloads — so you re-nick and re-spike on every visit.

## ⚠️ Known issue: death-respawn keeps you mounted

A mounted vehicle unparents from its chunk, so `LoadWorld`'s destroy-and-rebuild never touches it,
and nothing in the death path (`DeathScreenUI` → `ContinueFromSave`) calls `Dismount()` — you wake
at your last save still on the bike. "A load puts you on foot" is only true for an app-restart
load.

Fixing it properly is a design call plus real work: a bare `Dismount()` strands a scene-root bike
at the death spot, and returning it to its authored spot means coordinating with
`VehicleSpawner`'s instance tracking. Deferred to Stage F.

---

# Traffic and car theft ("Grand Theft Corsa")

Ambient cars drive authored routes through a chunk as a background layer; the player can stop one,
hotwire it via a minigame, and drive off — which triggers a police response. Scope: `Home_London`
only. See [plans/TRAFFIC_AND_CAR_THEFT_PLAN.md](../plans/TRAFFIC_AND_CAR_THEFT_PLAN.md) for the
full spec, phasing and the owner check list.

| Piece | Script | What it does |
|---|---|---|
| Route | `World/TrafficRoute` | Lives in the chunk prefab; child transforms are waypoints. Spawns cars as its own children on a jittered timer; cars `Destroy` themselves at the route end. Chunk-owned by construction. |
| Car | `World/TrafficCar` | Drives waypoints via kinematic `MovePosition`; brakes for the player with a pure-math `InverseTransformPoint` check; offers the hotwire minigame while stopped; converts to a rideable vehicle on success. |
| Minigame | `UI/HotwireMenuUI` | The tap-the-wires clock, modelled on `PickpocketMenuUI`. Code-built, no pause push, proximity-closes if the player walks off. |
| Definition | `Data/VehicleData` | Name, ride `SpeedMultiplier`, `TrafficSpeed`, `KeepModelVisibleWhileMounted`, `HotwireWires`/`HotwireSeconds`. |
| Builder | `Editor/BuildTrafficCarPrefabTool` | `Tools → Place → Build Traffic Car Prefab`: builds the prefab + VehicleData from a GLB in `Assets/3DModels/Vehicles/`, seeded from the spec table. New files only. |

## How it behaves

- **Cars are chunk-owned.** `TrafficRoute` lives in the chunk prefab and spawns cars as its own
  children, so a chunk transition destroys the whole route at once — none of the seven
  chunk-instantiation paths needed to change.
- **Stopping.** The car brakes when the player is ahead of it and inside `LaneHalfWidth`, honks on
  a rate limit, and resumes after `TrafficResumeDelay`. The check is pure math
  (`InverseTransformPoint`), no physics queries, no per-frame allocation.
- **The theft.** While stopped and interactable, the car opens `HotwireMenuUI`. The car is frozen
  for the whole attempt (`_hotwiring`); the menu closes if the player walks out of
  `PickpocketRange` or the car is destroyed. Success converts the car into a normal rideable
  vehicle and auto-mounts it; timeout spikes one knife and hotwire-locks the car for
  `HotwireRetryLockoutSeconds`.
- **The police response.** Success spikes **two** knives (two officers — PCSO then Bobby). The
  stolen car is then exactly the nicked e-bike: it unparents on mount, rejoins the chunk on
  dismount, and "Nicking does not persist" stands.
- **A fleeing driver.** On success a random villager from `TrafficRoute.DriverPresets` (built via
  `NpcFactory`) hops out the side of the car and wanders off.
- **3D presentation.** Cars use `KeepModelVisibleWhileMounted`: the model stays visible while
  ridden and the rider's sprite is hidden via `WorldActorVisual.SetRiderHidden` — never
  `SetActive(false)` on the vehicle root.

## Things that will catch you out

- **The builder tool's authored `OnInteract → VehicleController.Toggle` call is dead wiring.**
  `TrafficCar.Awake` calls `RemoveAllListeners()` and subscribes `TryHotwire` while driving,
  swapping back to `Toggle` on conversion. The authored call is a sensible Inspector default only.
- **Don't hand-edit chunk-prefab YAML to fix a missing nested prefab.** A missing building model
  (e.g. the FU Sports model after the reorganisation) is an editor task: open the chunk prefab in
  Prefab Mode and re-point the "Missing Prefab" object to the surviving GLB.
- **The two cars differ only through `VehicleData`.** Reliant Robin (common): 3.0× / 7 m/s / 3
  wires / 6 s, weight 3. Vauxhall Corsa (better): 3.75× / 8.5 m/s / 4 wires / 5 s, weight 1.
- **Death-while-mounted on a stolen car** inherits the same deferred Stage F issue as the e-bike.
