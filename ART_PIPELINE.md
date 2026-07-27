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

### The style — photoreal source, crushed small

The game looks like **digitised sprites**: the early-90s technique where studios photographed real
actors and props and reduced them to a few dozen pixels. Grounded, slightly grubby, photographic —
never cartoon, never vector, never cel-shaded, no black outlines.

**So generate photorealistic images at high resolution.** Do not attempt to draw low-resolution or
pixel art. The reduction is done deterministically on import, which is what keeps every asset
consistent no matter how far apart they were generated — a generator asked for "64px pixel art"
produces a different pixel grid every time, and it looks wrong.

Think a photograph of the subject against a plain backdrop, lit evenly, then shrunk until it is
mostly suggestion. Your job is the photograph. The shrinking is ours.

**People must be synthetic, not real.** Do not source, trace or reproduce photographs of real
identifiable people — likeness rights survive any licence on the image, and the cast here is
fictional anyway. Generated faces are indistinguishable once reduced.

## 2. Resolution and size — read carefully, this is the part that goes wrong

**Deliver large. The importer reduces.** Every asset is area-averaged down to **48 pixels per world
unit** on import, so a 1.35-unit character finishes at ~65 px tall. You never produce that size
yourself.

Deliver single sprites at roughly **512 px tall**, or larger if the subject wants it. More
resolution costs nothing — sources stay outside the project and are never committed.

The one rule that trips everything up:

> Sizing is derived from the **full image height** after trimming, not from the canvas you drew
> on. The importer trims for you, so what matters is that the background is removable — see below.

The `worldHeight` in the JSON is what drives the reduction, so it must be right:

| Subject | `worldHeight` | Finishes at |
|---|---|---|
| Player, NPCs, police, civilians | 1.35 | ~65 px |
| E-bikes, mopeds and similar | 0.9 | ~43 px |
| Bushes | 0.9 | ~43 px |
| Small animals (squirrel) | 0.45 | ~22 px |
| Sheds | 2.2 | ~106 px |
| Trees | 2.2 | ~106 px |
| Office buildings | 6.0 | ~288 px |

Width follows whatever the subject needs — only height is normalised.

### Backgrounds — the rule that has failed twice now

A true alpha channel is ideal, but image generators are unreliable at producing one. So:

> **Put the subject on a flat, solid magenta background — `#FF00FF`, pure, no gradient, no
> vignette, no cast shadow, no floor.** The importer keys that colour out and trims to the subject.

Flat means *one colour*, edge to edge. A purple gradient is not flat and will be rejected rather
than half-removed. If your tool can emit real transparency instead, do that and skip the magenta.

Do not use magenta anywhere in the subject itself.

You do not need to trim — the importer crops to the subject after keying. Trim if you can; it is no
longer the failure it was.

Hard limits: **PNG.** No JPEG — its compression will smear the key colour and the backdrop will not
come out cleanly. Source files have no size cap, but do not deliver anything gratuitous — 8K
renders of a shed help nobody.

## 3. Sprite sheets and animation

A sheet must be a **uniform grid** — every cell identical in size, frames left to right, then top
to bottom. Unlike single sprites, sheet cells are **not** trimmed.

> **Every frame must share the same baseline.** The subject's feet land on the same row of pixels
> in every cell, and the figure stays the same height and scale throughout. Never crop, shrink or
> re-frame between frames. A walk cycle moves the *limbs*; the ground does not move.
>
> The importer measures this and refuses anything that would visibly bob. It is the single most
> common way a sheet fails, because it looks fine frame by frame and only shows up in motion.

Keep the full body in frame in every cell — no legs cut off at the bottom edge.

> **Every sheet of the same character must agree with every other one.** Same view angle, same
> body width, same height, same clothes. A character drawn three-quarter when idle and in profile
> when walking changes shape the moment they move. Generate `idle` first and use it as the visual
> reference for every other action — do not work from the text description twice.
>
> The importer compares sheets of the same subject and refuses ones that disagree.

Standard character cell at source resolution: **512×512**, subject filling most of the cell height,
horizontally centred. The importer reduces the whole sheet so each cell lands at ~65×65, and
recalculates the grid itself — you always work at source size.

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
  "frameWidth": 512,
  "frameHeight": 512,
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
| `cycle` | `Cycle` | `Cycling` bool, held while riding |

## 5. Naming

- Single: `spr_<category>_<name>.png` → `spr_char_player.png`, `spr_vehicle_ebike.png`
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
| `spr_vehicle_ebike.png` | single | A **public hire e-bike**, parked and unattended, side-on three-quarter view facing camera-right. The dockless rental sort you find dumped on British pavements: chunky step-through frame, fat tyres, basket on the front, battery pack on the down tube, a rear rack, small solar panel or branding plate. Scuffed and slightly abused. Photoreal, ~512 px tall. |

Two earlier attempts at this asset failed. The first came back as clean vector cartoon with heavy
black outlines — wrong style, see §1. The second had a purple gradient painted into the background
— wrong background, see §2. Photographic subject, flat magenta backdrop.

Do not brand it with a real hire company's livery. Invent one, or leave it unbranded.

### 7.2 The rest of the mount system

The mount system works but has no art at all — the code-generated placeholder was deleted with the
rename. `spr_vehicle_ebike` above plus these two are what fill it in.

| File | Type | Notes |
|---|---|---|
The player is **sheets, not singles** — they animate. One character serves all four classes; the
classes differ in stats only, so there are no per-class variants.

`sheet_char_player_<action>.png`, using the frame table in §7.3:

| Action | Notes |
|---|---|
| `idle` | Standing, small weight shift or breath. |
| `walk` | Walk cycle. |
| `attack` | Melee swing. |
| `cast` | Casting a spell — this is a magic game, played straight. |
| `hurt` | Taking a hit. |
| `death` | Falling. |
| `cycle` | **Sat on the e-bike, pedalling.** The whole cell is rider *and* bike as one image, so it must match `spr_vehicle_ebike.png`. Held for as long as the player is riding, so it loops. |

The player: a young modern Brit in street clothes — hoodie, tracksuit bottoms, trainers. Ordinary,
slightly scruffy. Same person in every sheet: same face, build, clothes and colours.

**Generate `idle` first and use it as visual reference for every other sheet.** Separately-prompted
photoreal humans will not be the same person unless told to be.

These three are **auto-assigned on import**, so use exactly those filenames.

### 7.3 Characters — sprite sheets

All source cells **512×512** unless stated, subject filling most of the cell height, feet near the
bottom, facing camera-right. `worldHeight` 1.35. Standard actions and frame counts:

| Action | Frames | Columns | fps | Loop |
|---|---|---|---|---|
| `idle` | 4 | 4 | 6 | yes |
| `walk` | 4 | 4 | 8 | yes |
| `attack` | 6 | 6 | 12 | no |
| `cast` | 6 | 6 | 12 | no |
| `hurt` | 3 | 3 | 12 | no |
| `death` | 6 | 6 | 10 | no |
| `cycle` | 6 | 6 | 12 | yes |

Frame counts are deliberately low. Every extra frame is another chance for the figure to drift in
scale or angle, and at 65 px the difference between a 4-frame and an 8-frame walk is barely
visible. Fewer, consistent frames beat more, inconsistent ones.

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
`death`. **`worldHeight` 0.45** — it finishes around 22 px, so source cells of 256×256 are plenty
rather than the usual 512. A genuinely furious grey squirrel. Comic menace, not cute.

**Roaming pharmacist** — `sheet_char_pharmacist_<action>.png`, actions: `idle`, `walk`.
A drug dealer with the bearing and costume of a high-street pharmacist — white coat, name badge,
clipboard, entirely straight-faced about it. The gag is deadpan; play it completely seriously.

### 7.4 Props — single sprites

Buildings are billboards, but the camera is **fixed** at pitch 30°, yaw −45° and never rotates, so
draw them **in that same isometric projection** — two faces of the box visible, seen from slightly
above. Not a flat straight-on elevation. Do not paint ground, shadow or surroundings.

| File | `worldHeight` | Notes |
|---|---|---|
| `spr_prop_office_building.png` | 6.0 | A sketchy, boxy low-rise office block. Plain, cheap, slightly grim — think a two- or three-storey building on a British retail park. Simple massing, few details. |
| `spr_prop_shed.png` | 2.2 | A small garden shed. Timber, weathered, single door, maybe one window. |

### 7.5 Later

Five police tiers (PCSO hi-vis yellow, Bobby navy, Armed Response black, Occult Agent trench-coat
brown, Occult Commander Ministry red), the Nosey Parker civilian, and the pub exterior — all
currently coloured capsules and primitives.
