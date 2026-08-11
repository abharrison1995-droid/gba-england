# Alex companion — approved design and implementation plan

```
Last verified against: working tree, 2026-08-09
Verification scope:    design plus local art pre-check. No companion runtime, save fields, prefab,
                       preset or imported Alex art exists yet. `sheet_char_alex_idle`,
                       `sheet_char_alex_walk`, `sheet_char_alex_attack` and
                       `sheet_char_alex_cast`, `sheet_char_alex_hurt` and
                       `sheet_char_alex_death`, `sheet_char_alex_roll` and
                       `sheet_char_alex_knockback` are staged in
                       `art_incoming/` and passed
                       `Tools/precheck_sheets.py`; Unity has not imported or displayed them. The two
                       supplied likeness sheets live outside the repo and are references, not
                       importer-ready assets.
```

## 1. Approved player-facing design

Alex is an early paid companion who waits at a configurable home anchor outside a building that
has not been selected yet. The location is data, not code, so choosing or moving the building must
not require changing the companion machinery.

The paid lifecycle is:

`available at home -> pay £25 -> hired and following -> knocked out or dismissed -> available at home`

- The £25 price is provisional until the economy pass.
- One active companion at a time.
- The contract has no timer. It survives chunk transitions, portals, arrest, player death/reload,
  save and continue; Alex being knocked out or dismissed are its normal end conditions.
- Dismissal gives no refund.
- Knockout is not death: Alex gives no loot or XP, plays the `Death` animation as a knockout pose,
  stops fighting and returns to the authored home anchor ready to be hired again.
- Alex is an unarmed boxer. He responds to hostiles already fighting the player and does not
  independently attack civilians or police.
- Alex can cast a modest early-game heal, prioritising the badly injured player and otherwise
  healing himself. Initial recommendation: 20-second cooldown; heal magnitude remains tunable.
- Alex can dodge, but far less often than the player. Initial recommendation: an 8–10 second AI
  dodge cooldown versus the player's 1 second, overridable per companion definition.

Quest-bound companions use the same follower, combat, HUD and transition machinery. Their join and
leave conditions come from quest state instead of `SpendPounds`; no quest or dialogue prose is part
of this plan.

## 2. Art contract

The art subject id is **`alex`**. The supplied starter and attack images are likeness, wardrobe,
tattoo and choreography references only: both are 1254×1254 collages, not the uniform one-row grid
the importer slices.

Alex keeps the reference appearance: recognisable face, brown mullet, moustache, white T-shirt,
navy graphic shorts and closely reproduced tattoos. Bare feet are replaced by dark navy or black
unbranded Croc-style clogs. Tattoo fidelity is preserved at source resolution as closely as
generation allows; the final 74 px reduction will retain placement and tonal shapes more clearly
than fine linework.

This is an intentional exception to `ART_PIPELINE.md`'s fictional-person default: the owner stated
that the supplied person is them and requested this likeness for their own in-game character. The
source references remain outside the repository. Only the final PNG+JSON deliverables belong in
`art_incoming/`.

All frames are photoreal source images crushed small by the importer, three-quarter view from the
fixed isometric camera, facing camera-right, full body, no cast shadow or floor, on removable flat
magenta. Generate one square frame at a time and tile locally per `docs/art/SHEET_WORKFLOW.md`.

| Action | Frames | fps | Loop | Alex-specific read |
|---|---:|---:|---|---|
| `idle` | 4 | 6 | yes | relaxed lurking stance; small breathing/weight shifts |
| `walk` | 6 | 8 | yes | natural catch-up walk, fixed baseline |
| `attack` | 6 | 12 | no | unarmed straight-punch combination, supplied sheet as choreography reference |
| `cast` | 6 | 12 | no | grounded healing spell directed toward an ally |
| `hurt` | 3 | 12 | no | compact hit reaction |
| `death` | 6 | 10 | no | non-lethal knockout fall; runtime calls it knockout |
| `roll` | 6 | 14 | no | infrequent defensive dodge roll |
| `knockback` | 6 | 12 | no | launched, planted, then recovery |

Every sheet uses `worldHeight: 1.55`. `cycle` is cancelled project-wide and is not requested.

## 3. Runtime shape

Keep the feature split by responsibility rather than turning a hostile `EnemyAI` toward the
player:

- **Companion definition data** — stable id, display name, art/controller, stats, price, home chunk
  and anchor id, heal/dodge tuning, and contract type.
- **Companion manager** — owns the single active contract, spawns the scene-root follower, observes
  `ChunkManager.CurrentChunkData`, and rejoins Alex beside the player after every chunk replacement
  path. It must not depend on only the two full transition routines.
- **Hire interaction** — calls `PlayerSession.SpendPounds(25)` atomically, refuses without changing
  state when funds are short, and cannot charge again for a contract restored from save.
- **Companion AI** — follows on the X/Z plane with 3D physics/navigation, keeps out of the player's
  body, catches up or warps when stranded, selects hostile targets, punches, heals and occasionally
  dodges. Never introduce 2D physics.
- **Knockout handler** — uses `Health` with `DestroyOnDeath = false`, disables combat/collision,
  triggers the `Death` state, ends the contract and returns availability to the home anchor. The
  existing `Health.Die` early return does not disable an actor when destruction is false, so the
  companion handler must own that shutdown explicitly.
- **Companion HUD** — fills the existing unused `UIManager.CompanionHUDTemplate` /
  `CompanionHUDContainer` seam with name and health. It appears only while a companion is active.

### World Palette authoring

Companions get their own **Companion** section in the World Palette rather than appearing among
ordinary NPCs or enemies. Append `Companion` to `PlacementPreset.PlacementCategory`; never insert
or reorder it because existing preset assets serialize the enum by integer index. The palette can
then group companion presets automatically and split them by `CityRegion`, just as it does NPCs.

A companion preset represents the recruitable **home presence**, not the active follower. It
references a `CompanionDefinition`, displays the imported idle frame as its palette icon and
resting sprite, and stamps a hire point/home anchor into a chunk prefab. The active companion is a
separate scene-root instance created by `CompanionManager`, so chunk replacement cannot destroy it.
The placement path validates that each definition has one stable home anchor id; it does not write
or infer a save key from the placed GameObject name.

The active companion must be a scene-root object, never parented under the current chunk root,
because every transition destroys that root. Reposition it only after the destination and player
arrival are valid. Do not suspend a chunk root or vehicle root with `SetActive(false)`.

## 4. Save and serialization mapping

Implementation touches saves and must follow the architect -> implementer -> reviewer workflow.
No existing key or serialized field is renamed.

| Existing value | Planned value | Rule |
|---|---|---|
| no companion save state | appended active companion id | empty means no active contract; ids become save keys once shipped |
| no companion health state | appended current companion HP | restore without healing; clamp against the resolved definition |
| no companion contract field | appended contract state/type if required | append fields; append enum members only, never insert |
| no persisted home location | definition-owned home chunk/anchor ids | author once and treat as stable identifiers after release |

Old saves read the appended fields as empty/zero and start with no active companion. Saving after a
knockout or dismissal clears active companion state before the next autosave. A loaded active hire
must not charge £25 again.

## 5. Implementation order and verification

1. Complete and pre-check the eight Alex sheets in `art_incoming/`; do not import automatically.
2. Architect the data/save mapping and all chunk/reload/arrest paths before code changes.
3. Implement definition, manager, AI, hire, knockout and HUD in small single-concern changes.
4. Build Alex's prefab/preset in place through Unity editor tooling; choose the home building and
   author its anchor separately.
5. Import art with `Tools -> Art -> Import Generated Art`, then wire the preset/prefab.
6. Run `python Tools/asset_reachability.py --check-dangling` and `python Tools/art_status.py`.

Unity verification must cover: insufficient funds, exactly £25, dismissal, knockout, rehire,
save/continue without another charge, all edge and portal transitions, arrest, player death/reload,
healing priority/cooldown, infrequent dodge, hostile targeting, no civilian/police initiation,
companion HUD, and returning to the eventual home anchor. Mechanical reference checks do not prove
that any of those behaviours work.
