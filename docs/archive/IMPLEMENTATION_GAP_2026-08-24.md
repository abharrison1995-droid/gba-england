> ⚠️ **ARCHIVED SNAPSHOT, 2026-08-24. Do not read this as current.** Every count and
> placement claim below was checked against the repo on that date and will drift. Kept so
> the reasoning of the day can be traced. Current state lives in `CLAUDE.md`,
> `docs/reference/` and — for never-verified status — `docs/reference/VERIFICATION_LEDGER.md`.

# The implementation gap — 2026-08-24

> **What this is.** An audit of the distance between *"the code supports it"* and *"you can
> actually do it while playing"*. Produced by a four-agent swarm, then verified claim by
> claim — which mattered, because five of the swarm's findings were wrong. It is not a plan
> and it decides nothing.
>
> **Nothing here has been compiled or run.** There is no C# compiler and no Unity in the
> agent environment (CLAUDE.md §5). Every statement below is read off tracked files.

---

## The finding that matters

The gap is not half-written code. It is **whole subsystems that are complete in code and have
zero instances in the world.**

Each of these was checked by resolving the script's `.meta` GUID and searching every prefab
under `Assets/Prefabs/` and `Assets/c.unity`:

| System | Placements found | Consequence |
|---|---|---|
| `WorldContainer` / `SpriteContainer` | **0** | The entire container, foraging and visit-counted loot-respawn system is unreachable. There is nothing to search anywhere in the game. |
| `TrafficRoute` | **0** | No ambient traffic, nothing to hotwire. Compounded: no traffic car prefab exists either, so `BuildTrafficCarPrefabTool` has never been run. |
| `ProximityDialogueTrigger` | **0** | Stage-gated ambush dialogue cannot fire. The Mayor Zhao encounter is written and unreachable. |

A fourth case is the same shape but at content level rather than component level:
`Preset_MadFisherman` — the only preset whose dialogue grants `rush_hour` — is referenced by
**no chunk data and no prefab**, committed or on disk. The quest exists, is authored, and has
no giver in the world.

⚠️ Only Mad Fisherman was verified individually. The swarm claimed eleven-plus presets are in
the same state (Mayor Swalls, Mayor Zhao, Ralph, Sanjeet, Murtaugh, Riggs, Commissioner
Spencer, Neigel Fromage, the tracksuit geezer, Underhoused). **That list is unverified** and
should be checked before it is acted on.

---

## Blocked only on an editor tool run

Content-generating editor tools change nothing until a human runs the menu item.

- **`Tools → Content → Create Special Attack Assets`** — `Assets/Data/Abilities/` does not
  exist. Until it runs, `Special_spin.asset` and `Special_dash.asset` do not exist, the
  `SpecialAttacks` list on `CombatController` cannot be assigned, and the SPN/DSH buttons
  render dimmed and do nothing. This is the designed failure mode, not a bug.
- **`BuildTrafficCarPrefabTool`** — never run; no car prefab output exists.
- **`Tools → UI → Rebuild Inventory Panel (Win95)`** — per the ledger, the bag readout only
  binds after this runs once.

---

## Coded and playable, but invisible

Mechanics ship before art here on purpose — every animator call is guarded, so a missing
parameter no-ops rather than throwing.

- **The spinning attack has no animation on any class.** All nine `player_*` controllers
  declare the `SpecialAttack` trigger parameter; **none has a `Special` state**. The only
  `Special` state in the project belongs to `trap_branch_manager_Controller`. Requested as
  Band 12 in `docs/art/ART_QUEUE.md`; the attack is fully playable without it.
- **Three police tiers render as capsules.** `Police_ArmedResponse`, `Police_OccultAgent` and
  `Police_OccultCommander` each carry a `PlaceholderBody` with a built-in capsule mesh. These
  are what the player meets at wanted levels 3–5. PCSO and Bobby have full sheets.
- **Hostile knockback is mostly invisible.** Enemies can be knocked back in code but most
  render their `hurt` frame rather than a tumble; Band 10's hostile sheets are outstanding.

---

## Inert wiring

- `CombatController.SpecialAttacks` — unassigned, and absent from the scene YAML because the
  field postdates the last scene save. Unity writes it on next save.
- `CombatController.AttackPoint` — `{fileID: 0}`. Melee reach falls back to `MeleeRange`.
  There is no comment stating the intent, so whether this is deliberate or a forgotten
  wiring step is an open question for the owner.
- `UIManager.CompanionHUDTemplate` and `UIManager.CompanionHUDContainer` — two serialized
  fields whose only occurrences are their own declarations. Safe to delete; both are
  unassigned everywhere, so nothing loses a value. **The companion HUD itself is not
  missing** — `CompanionHUDUI` builds itself via `Ensure()` and registers through a static
  seam. These are orphaned fields, not a missing feature.

---

## Corrections — what the swarm got wrong

Recorded because a wrong finding acted on costs more than a missing one, and because it
calibrates how much to trust an unverified agent claim.

| Claim | Reality |
|---|---|
| The fight arena is a bare prefab with no match logic | `FightPitController`'s GUID **is** on `Castle_Fight_Arena_Prefab.prefab` |
| No `MerchantData` assets exist | **Five exist** in `Assets/Data/Merchants/` — the search was non-recursive |
| Murtaugh's walk clip was imported but never wired | Wired. `ArtImportTool.cs:49` maps the `walk` action to a state *named* `Run`; **no controller in the project has a `Walk` state**, by design |
| The companion HUD is dead code | Two orphaned `UIManager` fields are dead; `CompanionHUDUI` is implemented |
| 27 chunk assets vs CLAUDE.md's documented 19 | CLAUDE.md was correct for `main`; the count included nine then-untracked new chunks |

---

## What was true and is now fixed

At the time of the audit, nine new chunk data assets were **untracked** — no safety net at
all. Committed the same day as `59db411`, along with their prefabs, the Blender mass-gen
pipeline that produced their models, and the map rewire that dropped South Slums. The tree
went from ~500 uncommitted entries to clean across seventeen commits.

---

## What this snapshot does not cover

- Whether any of it compiles. Nothing here has been near a C# compiler.
- Whether the eleven-plus unplaced presets claim holds beyond Mad Fisherman.
- Anything the `VERIFICATION_LEDGER.md` owns — that file is the exclusive owner of
  never-verified status and should be read directly rather than summarised here.
