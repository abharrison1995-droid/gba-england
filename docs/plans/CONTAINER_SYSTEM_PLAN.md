# Container system plan — `WorldContainer` and visit-counted respawn

**Status:** in implementation, 2026-08-17.
**Verification header:** nothing in this plan has been seen by a compiler or an editor. Every
behavioural claim below is intent, not observation, until the §6 routes are walked.

---

## 1. What this is

A general-purpose container that attaches to any **3D** world object — a berry bush, a broken
vending machine, a heap of bus wreckage — and a `Tools → Place → Container Placement` editor
window that authors them, modelled on the portal tool.

It also converts the existing `SpriteContainer.Respawning` mode from "refills every visit" to the
same **visit-counted cooldown** the new component uses, so every restockable container in the
project replenishes on a delay rather than instantly.

`LootChest` is untouched. `SpriteContainer.Fixed` is untouched.

---

## 2. Three findings that shaped the plan

### 2.1 The three items already exist — do not rename their ids

`BusStationBarnacles`, `VendingMachineFungus` and `Blueberries` were authored for the vape arc.
Their `ItemID`s are `bus_station_barnacles`, `vending_machine_fungus`, `blueberries`, and those
strings appear as literals in four quest sources that `QuestTextImporter` resolves by id:

- `quests/investigate_weird_vape.quest` — `STAGE COLLECT blueberries x2 vending_machine_fungus x2 bus_station_barnacles x2`
- `quests/ah_barnacles.quest` — `STAGE COLLECT bus_station_barnacles x10`, `ITEM: bus_station_barnacles x10 consume`
- `quests/dialogue/danielpauls.quest` — `ITEM: blueberries x2`

`Import Quests` is an owed run. Renaming an id without editing all four files makes the importer
write `Item: {fileID: 0}` into the Collect stages — **nothing logs**, and the objective simply
never completes. **Decision: ids are kept. Only stats are retuned.**

### 2.2 `TravelRoutine` builds the chunk before `CurrentChunkData` is set

`ChunkManager.TravelRoutine` instantiates the destination and inspects it for the arrival marker
*before* committing anything — deliberate, so a broken marker id leaves the world untouched. But
every `Awake` in the new chunk runs synchronously inside that `Instantiate`, so anything reading
`ChunkManager.Instance.CurrentChunkData` during `Awake` sees **the chunk it just left**.

`SpriteContainer.SetUpFixed` does exactly that, so a container inside a portal-reached chunk builds
its save id as `"<origin chunk>/<name>"`. Latent — no `SpriteContainer` is placed anywhere and no
`DungeonPortal` exists — but the bus-station containers are portal-reached, which is the whole use
case.

Six of the seven instantiate paths assign `CurrentChunkData` before instantiating and are correct.
Only `TravelRoutine` does not. Moving the assignment earlier would destroy the abort safety, so the
fix is a separate `ChunkBeingBuilt` field consulted by a resolver.

### 2.3 A duplicate child GameObject name is the likeliest silent failure

`SpriteContainer` keys on `"<ChunkName>/<gameObject.name>"`. `WorldContainer` lives on a **child**
of a 3D model, so ten containers each called `Container` under ten different pillars are ten legal
GameObjects sharing one save key — loot one, all ten empty.

`WorldContainer` therefore carries an explicit `SaveId`, written and uniquified by the tool, falling
back to `gameObject.name` when blank. Nothing is authored yet, so this is the free moment.

---

## 3. Decisions taken

| # | Decision | Consequence |
|---|---|---|
| 1 | Keep the three `ItemID`s as they are | Only stats change; the owed `Import Quests` run stays safe |
| 2 | `SpriteContainer.Respawning` adopts the visit cooldown | One meaning of "Respawning" across both components; `WorldContainer` needs only two modes |
| 3 | Quest containers use fixed loot | `FixedLoot` guarantees exact quantities; `ah_barnacles` cannot leave the player short |

Decision 2 removes the `AlwaysRespawning` mode the brief asked for. `RespawnVisits = 1` expresses
the same thing — loot it, return once, it is full — without a third enum value or a second meaning
for a word already in use.

---

## 4. Mapping tables

### 4.1 New save field

| Field | Type | Position | A pre-feature save reads | Correct? |
|---|---|---|---|---|
| `SaveData.ContainerCooldowns` | `List<ContainerCooldown>` | **appended after `SpellName`** | empty list | Yes — nothing is cooling down, every container is fresh |

⚠ The field name **is** the JSON key. `JsonUtility` ignores `[FormerlySerializedAs]`. Renaming it
later silently resets every cooldown.

### 4.2 New serialized field on an existing component

| Component | Field | Default | A pre-feature asset reads |
|---|---|---|---|
| `SpriteContainer` | `int RespawnVisits` | `EKVibe.DefaultContainerRespawnVisits` (3) | **0** — see the warning below |

⚠ **Appending an int to a component whose assets already exist gives those assets `0`, not the
field initializer.** Unity writes the initializer only when it next serializes the object. Two
`SpriteContainer` prefabs exist (`Container_Fixed`, `Container_Respawning`) and neither is placed
anywhere, so nothing is at risk today — but `RespawnVisits <= 0` must be treated as "use the
default" rather than "respawn instantly", or an untouched asset silently behaves as the old mode.

### 4.3 New enums — index frozen by the first authored container

| Enum | Values | Serialized into |
|---|---|---|
| `WorldContainer.ContainerMode` | `Fixed = 0`, `Respawning = 1` | every `WorldContainer` in every chunk prefab |
| `WorldContainer.TrapType` | `None = 0`, `Damage = 1`, `WantedSpike = 2` | same |

No existing enum is reordered. `QuestGateType` is reused unchanged — no value appended.

### 4.4 Save keys — a new key space

| Key | Shape | Written into |
|---|---|---|
| Looted (`Fixed`) | `"<ChunkName>/<SaveId>"` | `SaveData.LootedContainers` — **shared with `SpriteContainer`** |
| Cooldown (`Respawning`) | same string | `SaveData.ContainerCooldowns[].Id` |

Nothing has been saved in this key space, so `SaveId` values are free to choose until the first
play session that loots one.

### 4.5 Item retune — no id changes

| Asset | `ItemID` (unchanged) | Change |
|---|---|---|
| `BusStationBarnacles` | `bus_station_barnacles` | `Type` 7 → 11 (Junk), `MaxStack` 20 → 99, `Value` 1 → 8, heals cleared |
| `VendingMachineFungus` | `vending_machine_fungus` | `Type` 7 → 11 (Junk), `MaxStack` 20 → 99, `Value` 1 → 12, heals cleared |
| `Blueberries` | `blueberries` | `HealHP` 4 → 5, `HealMana` 2 → 8, `Value` 1 → 3 |

Descriptions stay blank — the owner's words (§3).

---

## 5. Which of the seven instantiate paths ticks a visit

| Path | Ticks? | Why |
|---|---|---|
| `ChunkManager.TransitionToChunkRoutine` (edge) | **Yes** | The canonical "you left and came back" |
| `ChunkManager.TravelRoutine` (portal) | **Yes, with compensation** | Incremented back on the abort branch, so a broken marker id costs nothing |
| `ChunkManager.Start` (cold boot) | No | Debug autoload; does not even write `CurrentChunkData` |
| `SaveGameManager.LoadWorld` | No | A reload must not advance a cooldown, or reload-spam is the fastest way to farm |
| `DeathScreenUI.OnNewGame` fallback | No | Dying is not a visit |
| `GameFlowController.EnterManorCellars` | No | One-shot; the arrest path lands here |
| `GameFlowController.LoadLondonAtWestGates` | No | One-shot tutorial exit |

**Counting, written down once:** loot at visit 0 with `RespawnVisits = 3` → return 1 leaves 2,
return 2 leaves 1, return 3 leaves 0 and it is full. So *N* means "available on the Nth return".

---

## 6. Verification

### Mechanical, available here

```bash
python3 Tools/asset_reachability.py --check-dangling
```

⚠ In the agent environment this exits **2 — "nothing was verified"** — because `Library/PackageCache`
is gitignored and absent. It is a check for the owner's machine, run before and after the asset
commits. A `2` is not a pass.

A brace/paren balance scan catches a truncated edit. **It is not a compile** and must not be
reported as one.

### Needs Unity and a human

Exit Play mode and `Ctrl+S` first.

1. **It compiles.** Everything below depends on it.
2. **Unity accepts the hand-authored `.meta` files** — two scripts, three loot bands. `git diff` the
   metas after the reimport; the GUIDs must be unchanged.
3. **The tool draws.** `Tools → Place → Container Placement` with nothing selected must show a
   refusal, not an exception.
4. **Attach one.** Open `Abandoned_Bus_Station_Prefab` in Prefab Mode, select an object in the
   Hierarchy, click a point on it in the Scene view, set Mode `Fixed`, band `LootBand_BusBarnacles`,
   prompt "Search wreckage", press Create. Confirm a child at the clicked point carrying
   `WorldContainer` + `Interactable`, with `SaveId` filled in.
5. **Attach a second to the same object.** The tool must load the existing config for editing, not
   add a second child.
6. **Shift-click run.** Three objects in one armed session → three distinct `SaveId`s.
7. **The validator fires.** Force a duplicate `SaveId` and confirm it is named. Clear both loot
   sources and confirm that rule fires. Point `EmptyVisual` at the prefab root and confirm refusal.
8. **`Fixed` persists.** Blocked behind authoring a `DungeonPortal`, which has never existed in this
   project. Once wired: loot it empty, cross a chunk edge, return, confirm still empty and showing
   `EmptyVisual`. Then quit, `Continue`, confirm still empty. **That last step is the only proof the
   save round-trips**, and it is the one most likely to fail.
9. **The portal path uses the right chunk name.** Loot a `Fixed` container reached *by portal*, quit,
   reload, confirm still empty. If it refills, the resolver did not take — and nothing will say so.
   Cross-check by reading `LootedContainers` in `savegame.json`: it must read
   `Abandoned_Bus_Station/<SaveId>`, not `Home_London/<SaveId>`.
10. **`Respawning` counts down.** `RespawnVisits = 2`, loot it, return once (still empty), return
    again (full). Read `ContainerCooldowns` in the JSON between the two.
11. **A reload does not advance a cooldown.** Loot one, save, quit, reload twice, still empty.
12. **A pre-feature save loads.** Hand-delete the `ContainerCooldowns` key and `Continue`. Must
    arrive with no error and every container fresh.
13. **New Game in the same app session.** Loot a `Respawning` container, return to the title screen
    without quitting, start a New Game, confirm it is fresh. This is the `BeginNewGame` clear, and
    it fails silently.
14. **The visual swap.** `EmptyVisual` on, `FullVisual` off after the close — and correct on arrival
    in a chunk where the container is already spent.
15. **A half-emptied container reopens** with the rest still inside, and records nothing.
16. **An empty roll retires it.** Expected behaviour, not a bug — searching it counts.
17. **The prompt reaches the HUD**, and a container behind a wall does not steal the prompt from
    something nearer (`PlayerInteractor` is distance-only, no line of sight).

---

## 7. Commit sequence

| # | Commit |
|---|---|
| 1 | Resolve a container's chunk while the chunk is still being built |
| 2 | Append container cooldowns to the save |
| 3 | Tick container cooldowns on the two paths that are a visit |
| 4 | Move `SpriteContainer` respawning onto the visit cooldown |
| 5 | Two container tuning constants |
| 6 | `WorldContainer`: a container for any 3D object |
| 7 | Container Placement tool |
| 8 | Three forage loot bands |
| 9 | Retune the three forage items |
| 10 | Docs |

---

## 8. Explicitly out of scope

- Any behaviour for `TrapType`, `TrapChance`, `TrapDamage`, `TrapKnives`, `Locked`,
  `LockDifficulty`, `QuestGate`, `QuestKey`, `QuestStage`. Declared and inert. The tool says so on
  screen, because the failure mode of a back-pocket field is an author ticking `Locked` and
  shipping an unlocked container.
- The lockpick minigame.
- `LootChest`, `LootMenuUI`, `LootBand`, `LootDrop` — unchanged.
- `PlacementPreset` — no new field, no new `PlacementCategory`. The tool attaches to objects already
  in a prefab; the palette does not need to know.
- Placing any container, and the three 3D models. Authoring is a Unity session.
- Any `Description` prose — the owner's words.
