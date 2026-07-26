# ART_PIPELINE.md — generated art contract

How art gets from a generation agent into the game. Read `AGENTS.md` first for the hard rules.

**Deliver to `art_incoming/`. One PNG plus one JSON per asset. Nothing else, nowhere else.**

**Work the whole request list in §7 in one run.** Do not stop after one asset to check in — the
importer processes a folder at a time, and a batch of eight costs the same number of Unity steps
as a batch of one. If something in a request is unclear, put it in that asset's `"question"` field
and keep going.

**Suggested model: Gemini 3.1 Pro, high reasoning**, for a first batch or any request involving new
subject matter — the sizing and facing rules below are easy to violate plausibly. Once a batch has
come back correct, a faster model is fine for volume. This is set in Antigravity's own agent
configuration; nothing in this repo can select it for you.

---

## 1. What the game looks like

**Isometric 3D world, 2D billboarded sprites.** A fixed camera at pitch 30°, yaw −45°, orthographic
size 7. Sprites always turn to face the camera, so they are drawn once, in **three-quarter view**,
and the engine flips them horizontally for the other direction.

Consequences for every character and creature you draw:

- **Draw them facing camera-RIGHT.** Never draw a left-facing variant — `WorldActorVisual`
  flips the sprite for left. A left-facing source will appear mirrored and wrong.
- **Three-quarter view**, slightly from above, matching the camera's 30° downward pitch. Not a flat
  side-on view, not a top-down view.
- **No baked shadow** on the sprite itself, and no ground plane painted in. The sprite floats on a
  billboard; anything drawn under the feet will look like it is standing on a floating tile.

Setting: **modern Britain, slightly grim, slightly funny.** Council estates, retail parks, canals,
pubs, hi-vis, hoodies, mopeds. Not fantasy, despite the magic.

## 2. Resolution and size — read carefully, this is the part that goes wrong

Art is **hi-res 2D, not pixel art**: import is **100 pixels per unit, bilinear filtering**, matching
the sprites already in `Assets/Sprites/`.

The engine scales every sprite so its **full image height** becomes a fixed world height. It uses
the image bounds, not the visible pixels. So:

> **Trim single sprites tight to the artwork.** No transparent margin above or below. A sprite with
> 20% empty space at the top renders 20% smaller than one without, even at identical canvas size.

Target heights, and the resulting artwork height at 100 PPU:

| Subject | World height | Draw at |
|---|---|---|
| Player, NPCs, police, civilians | 1.35 units | **~200 px tall** after trimming |
| Moped and similar vehicles | 0.9 units | ~135 px tall after trimming |
| Bushes | 0.9 units | ~135 px |
| Trees | 2.2 units | ~320 px |
| Walls | 1.8 units | ~260 px |

Width follows whatever the subject needs — only height is normalised. Characters are roughly
0.85 units wide, so a character canvas ends up near **128×200**.

Hard limits: **PNG, RGBA with real alpha, max 2048 px on either side, under 2 MB.** No JPEG, no
flattened white background, no checkerboard "transparency" pattern drawn as pixels.

## 3. Sprite sheets and animation

A sheet must be a **uniform grid** — every cell identical in size, frames left to right, then top
to bottom. Unlike single sprites, sheet cells are **not** trimmed: the subject sits at a consistent
position inside a consistent cell, feet near the bottom, so the character does not jitter between
frames.

Standard character cell: **256×256**, subject ~200 px tall, horizontally centred.

Name actions from this list so the importer can build the animator: `idle`, `walk`, `attack`,
`hurt`, `death`, `cast`. Anything else is fine but will be imported as a clip with no state wiring.

## 4. The sidecar JSON

Every PNG needs a `.json` of the same name beside it.

Single sprite:

```json
{
  "name": "player",
  "type": "single",
  "category": "characters",
  "worldHeight": 1.35,
  "description": "Player in a grey hoodie, three-quarter view, facing camera-right."
}
```

Sheet:

```json
{
  "name": "player_walk",
  "type": "sheet",
  "category": "characters",
  "action": "walk",
  "worldHeight": 1.35,
  "frameWidth": 256,
  "frameHeight": 256,
  "columns": 8,
  "rows": 1,
  "frameCount": 8,
  "fps": 10,
  "loop": true,
  "description": "Eight-frame walk cycle, contact-down-pass-up ×2."
}
```

`category` is one of `characters`, `vehicles`, `props`, `fx`, `ui`. It decides the destination
folder. `frameCount` may be fewer than `columns × rows` if the last row is partly empty — say so.
Add `"question": "..."` if a request was ambiguous.

Two optional fields, both usually omitted:

- `"subject"` — groups sheets into one animator. Defaults to `name` minus the `_<action>` suffix,
  so `player_walk` and `player_attack` already land on the same `player` controller. Set it only
  when the names do not follow that pattern.
- `"rendererPath"` — animation binding path to the SpriteRenderer. Defaults to empty, meaning the
  renderer is on the same GameObject as the Animator, which is what every existing clip in this
  project uses. Leave it alone unless told otherwise.

Recognised `action` values map to animator states and to the parameter names the game already
calls. Anything outside this list still imports and still gets a clip — it just is not wired into
a state machine:

| `action` | State | Fired by |
|---|---|---|
| `idle` | `Idle` | default state |
| `walk` | `Run` | `Speed` float > 0.1 |
| `attack` | `Attack` | `MeleeAttack` trigger |
| `hurt` | `Hurt` | `Hit` trigger |
| `death` | `Death` | `Death` trigger, no return to idle |
| `cast` | `Cast` | `CastSpell` trigger |

## 5. Naming

- Single: `spr_<category>_<name>.png` → `spr_char_player.png`, `spr_vehicle_moped.png`
- Sheet: `sheet_<category>_<name>_<action>.png` → `sheet_char_player_walk.png`

Lower case, underscores, no spaces, no version suffixes. Regenerating an asset **overwrites the
same filename** — do not create `_v2`.

## 6. Importing (Claude Code's side)

`Tools → Exiled Alvaston → Art → Import Generated Art` reads `art_incoming/`, and for each pair:

1. Moves the PNG to `Assets/Art/Generated/<category>/`.
2. Applies the import settings: Sprite (2D and UI), 100 PPU, bilinear, alpha is transparency,
   max size 2048, Single or Multiple as the JSON says.
3. Slices sheets on the declared grid.
4. Generates an `AnimationClip` per sheet at the declared fps and loop flag.
5. Builds or updates an `AnimatorController` for a subject with recognised action names.
6. Reports what it wired and what it could not.

Nothing is imported automatically. `art_incoming/` is staging — files sit there until the tool runs.
Re-running is safe and idempotent: an asset of the same name overwrites in place, keeping its GUID
and every reference to it, which is why §5 forbids `_v2` filenames.

Clips land in `Assets/Animations/Generated/`, controllers as `<subject>_Controller.controller`.
The importer prints a summary to the Console listing what it wired, anything it could not, and any
`"question"` fields it found.

---

## 7. Current requests

### 7.1 First run — this one asset, on its own

Nothing in this pipeline has been through a full round trip yet. Produce **only** this, then stop,
so the handoff can be checked before a batch is committed to.

| File | Type | Notes |
|---|---|---|
| `spr_vehicle_moped.png` | single | A moped, **parked, no rider**, side-on three-quarter view facing camera-right. Deliveroo-orange bodywork, food delivery box on the back. Slightly scruffy — this is a nicked moped in a British city. ~135 px tall trimmed. |

### 7.2 The rest of the mount system

The mount system works, but the art is a placeholder I generated in code: a crude 64×40 moped drawn
from coloured rectangles. `spr_vehicle_moped` above plus these two replace it entirely.

| File | Type | Notes |
|---|---|---|
| `spr_char_player.png` | single | The player. Modern British street clothes — hoodie, trackies, trainers. Neutral standing pose. ~200 px tall trimmed. |
| `spr_char_player_moped.png` | single | **The same character sat on the moped**, as one combined image. This drives `WorldActorVisual.MountedSprite`, which replaces the whole player sprite while riding — rider and bike must read as one silhouette. ~200 px tall trimmed. |

The parked moped and the ridden moped must be recognisably the same vehicle.

These three are **auto-assigned on import**, so use exactly those filenames.

### 7.3 Characters — sprite sheets

All cells **256×256** unless stated, subject ~200 px tall, feet near the bottom of the cell, facing
camera-right. World height 1.35 units. Standard actions and frame counts:

| Action | Frames | Columns | fps | Loop |
|---|---|---|---|---|
| `idle` | 4 | 4 | 6 | yes |
| `walk` | 8 | 8 | 10 | yes |
| `attack` | 6 | 6 | 12 | no |
| `cast` | 6 | 6 | 12 | no |
| `hurt` | 3 | 3 | 12 | no |
| `death` | 6 | 6 | 10 | no |

**Councillor Mosley** — `sheet_char_mosley_<action>.png`, actions: `idle`, `walk`.
An elderly UK city councillor. Pensioner, ill-fitting grey suit, lanyard, comb-over, self-important
posture. A quest-giver who stands and talks — no combat.

**Daniel Pauls** — `sheet_char_danielpauls_<action>.png`, actions: `idle`, `walk`, `cast`.
A stage magician in a **pink jazzy Las Vegas suit** — sequins, wide lapels, ruffled shirt, far too
much for a British council estate, which is the joke. Middle-aged, theatrical. He teaches the
player their first spell, so `cast` should be a showman's flourish rather than a grim incantation.

**The tracksuit geezer** — `sheet_char_underhoused_<action>.png`, actions: `idle`, `walk`, `attack`,
`hurt`, `death`. Sketchy bloke in a full tracksuit, **wild unkempt hair**, twitchy. He panics and
zaps the player during the opening magic quest and is then killed, so he needs the full hostile set.
`attack` is a wild flailing magic zap, not a weapon swing.

**Angry squirrel** — `sheet_char_squirrel_<action>.png`, actions: `idle`, `walk`, `attack`, `hurt`,
`death`. **Cells 128×128, world height 0.45** — this one is small, so ignore the 256/200 figures
above. A genuinely furious grey squirrel. Comic menace, not cute.

**Roaming pharmacist** — `sheet_char_pharmacist_<action>.png`, actions: `idle`, `walk`.
A drug dealer with the bearing and costume of a high-street pharmacist — white coat, name badge,
clipboard, entirely straight-faced about it. The gag is deadpan; play it completely seriously.

### 7.4 Props — single sprites

Buildings are billboards, but the camera is **fixed** at pitch 30°, yaw −45° and never rotates, so
draw them **in that same isometric projection** — two faces of the box visible, seen from slightly
above. Not a flat straight-on elevation. Do not paint ground, shadow or surroundings.

| File | World height | Notes |
|---|---|---|
| `spr_prop_office_building.png` | 6.0 units (~600 px) | A sketchy, boxy low-rise office block. Plain, cheap, slightly grim — think a two- or three-storey building on a British retail park. Simple massing, few details. |
| `spr_prop_shed.png` | 2.2 units (~220 px) | A small garden shed. Timber, weathered, single door, maybe one window. |

### 7.5 Later

Five police tiers (PCSO hi-vis yellow, Bobby navy, Armed Response black, Occult Agent trench-coat
brown, Occult Commander Ministry red), the Nosey Parker civilian, and the pub exterior — all
currently coloured capsules and primitives.
