# ART_PIPELINE.md — generated art contract

How art gets from a generation agent into the game. Read `AGENTS.md` first for the hard rules.

**Deliver to `art_incoming/`. One PNG plus one JSON per asset. Nothing else, nowhere else.**

**§7 is a banded queue. Work one whole band in a run.** Do not stop after one asset to check in —
the importer processes a folder at a time, and a batch of eight costs the same number of Unity
steps as a batch of one. Equally, do not run ahead into the next band: each one is drawn against
art the previous band established, and a band drawn against the wrong reference is a band
redrawn. If something in a request is unclear, put it in that asset's `"question"` field and keep
going.

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

Width follows whatever the subject needs — only height is normalised. **Every prop in the queue
carries its own `worldHeight` in §7.6** — that table is the authority for anything listed there,
and it goes up to 9.0 for a pylon.

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

> **One frame per cell, and the grid must be the grid the JSON declares.** If the JSON says
> `columns: 6, rows: 1` of `512×512`, the image is 3072×512 containing **six** drawings in a
> single row — not twelve drawings in two rows of half-height cells. This is not a cosmetic
> difference: the importer slices from the manifest, so a sheet laid out 6×2 and declared 6×1
> gives every frame two characters stacked on top of each other.
>
> The total image size is not enough to catch this — 6×2 cells of 512×256 and 6×1 cells of
> 512×512 are both 3072×512 — so the importer's dimension check passes and the sheet fails
> later, on width, for what looks like an unrelated reason. **Count the drawings in the image and
> make `frameCount` that number.**

> **Every frame must share the same baseline.** The subject's feet land on the same row of pixels
> in every cell, and the figure stays the same height and scale throughout. Never crop, shrink or
> re-frame between frames. A walk cycle moves the *limbs*; the ground does not move.
>
> The importer measures this and refuses anything that would visibly bob. It is the single most
> common way a sheet fails, because it looks fine frame by frame and only shows up in motion.

Keep the full body in frame in every cell — no legs cut off at the bottom edge.

> **Every sheet of the same character must agree with every other one.** Same view angle, same
> body width, same height, same clothes.
>
> **The check that keeps failing is body width**, measured as the subject's mean opaque width as
> a fraction of its cell. The importer refuses anything more than 1.4× narrower than the `idle`
> sheet, and it does not care how good the pose is.
>
> **Two different mistakes trip that one check, and they need different fixes.** Both have
> happened:
>
> 1. **Drawn edge-on.** The figure's own proportions are wrong — a walk drawn side-on was 47 px
>    wide against the idle sheet's 122. Fix: same three-quarter view as the idle sheet.
> 2. **Drawn too small in the cell.** The figure's proportions are fine but it occupies half its
>    cell, so its width *as a fraction of the cell* collapses. This is what the last four player
>    sheets did — measured at 50–73% of cell height where the accepted `idle` fills **89%** — and
>    it is the more common mistake, because each frame looks perfectly good on its own. Fix: scale
>    the figure up until it nearly fills the cell.
>
> **The subject fills ~90% of its cell height, with the feet a few pixels off the bottom edge.**
> That one number prevents mistake 2 outright, and it is measured, not judged.
>
> **Open the idle PNG and work from the image, not from this description.** Prompting the same
> text twice produces two different people.

Actions where the body legitimately changes shape — `death` (falling), `cycle` (sat on a bike) —
are exempt from the height and baseline checks, but not from the width one. Nothing makes a
character half as wide as they stand except drawing them from the wrong angle.

Standard character cell at source resolution: **512×512**, subject filling most of the cell height,
horizontally centred. The importer reduces the whole sheet so each cell lands at ~65×65, and
recalculates the grid itself — you always work at source size.

Name actions from this list so the importer can build the animator: `idle`, `walk`, `attack`,
`hurt`, `death`, `cast`, `cycle`. Anything else is fine but will be imported as a clip with no
state wiring. The full mapping to animator states is in §4.

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
  "columns": 4,
  "rows": 1,
  "frameCount": 4,
  "fps": 8,
  "loop": true,
  "description": "Four-frame walk cycle: contact, down, pass, up."
}
```

Those numbers are the real ones for a walk — the frame table in §7.3 is authoritative, and the
importer warns when a sheet deviates from it. Copy from the table, not from this example.

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
| `cycle` | `Cycle` | `Cycling` bool, held while riding — **cancelled, do not draw one** (§7.9) |

`cycle` still imports and still wires itself into a controller, which is why it is listed. Nothing
asks for one any more: riding is drawn by layering the bike sprite over the character.

## 5. Naming

- Single: `spr_<category>_<name>.png` → `spr_char_player.png`, `spr_vehicle_ebike.png`
- Sheet: `sheet_<category>_<name>_<action>.png` → `sheet_char_player_walk.png`

Lower case, underscores, no spaces, no version suffixes. Regenerating an asset **overwrites the
same filename** — do not create `_v2`.

## 6. Importing (Claude Code's side)

`Tools → GBA → Art → Import Generated Art` reads `art_incoming/`, and for each pair:

1. Keys out the backdrop, trims (singles only), and area-averages the image down to 48 px per
   world unit, writing the result to `Assets/Art/Generated/<category>/`.
2. Applies the import settings: Sprite (2D and UI), **48 PPU**, **Point** filtering, alpha is
   transparency, no mipmaps, uncompressed, max size 2048, NPOT scale None, Single or Multiple as
   the JSON says.
3. Slices sheets on the declared grid.
4. Generates an `AnimationClip` per sheet at the declared fps and loop flag.
5. Builds or updates an `AnimatorController` for a subject with recognised action names.
6. Reports what it wired and what it could not.
7. Moves the PNG and JSON of every asset that imported cleanly to `art_incoming/processed/`.
   Anything that reported a problem **stays where it is**, so a re-run shows only what is still
   wrong rather than re-reporting the whole folder.

PPU matches the reduction density, which is what lets a sprite sit at its natural size in the
scene with a scale factor of 1. Point filtering is the art direction, not an oversight — the
pixels are the art by that stage, and bilinear would smear the thing the reduction just made.

Two subfolders of `art_incoming/` are ignored by the importer, which only reads the top level:

- `processed/` — written automatically by step 7 above.
- `rejected/` — moved by hand, for sheets that failed a check and are waiting to be redrawn.

Nothing is imported automatically. `art_incoming/` is staging — files sit there until the tool runs.
Re-running is safe and idempotent: an asset of the same name overwrites in place, keeping its GUID
and every reference to it, which is why §5 forbids `_v2` filenames.

Clips land in `Assets/Animations/Generated/`, controllers as `<subject>_Controller.controller`.
The importer prints a summary to the Console listing what it wired, anything it could not, and any
`"question"` fields it found.

---

## 7. The generation queue

Everything the world needs, in the order it is needed. **One band per run** (see the note at the
top of this file). A band is finished when its assets have imported cleanly and been accepted —
not when they have been delivered.

| Band | What | Assets | Why this order |
|---|---|---|---|
| **1** | §7.3 The three refused player sheets | 3 sheets | Nothing else is drawn until the player is right — every other character is matched against them. |
| **2** | §7.5 The tutorial cast | 8 sheets | The opening quest is the only scripted content that exists; it currently runs with placeholder capsules. |
| **3** | §7.6 World props | 21 singles | Four of the six chunks are **completely empty** — ground, edges and nothing else. This is the band that unblocks world-building. |
| **4** | §7.7 The ambient cast | 11 sheets | Civilians and roamers. Needed before the consequence layer means anything, since Nosey Parkers are civilians. |
| **5** | §7.8 The consequence layer | 10 sheets | Police tiers, first two only. Last because they are five variations on one silhouette and the game is playable without them. |

### 7.1 Delivered — the visual reference, do not regenerate

The round trip works. These are in the game and are what every new asset is matched against:

| File | Notes |
|---|---|
| `spr_vehicle_ebike.png` | The hire e-bike, wired into `EBike.prefab`. |
| `sheet_char_player_idle.png` | 4 frames. **The canonical player.** |
| `sheet_char_player_walk.png` | 4 frames. |
| `sheet_char_player_hurt.png` | 3 frames. |
| `sheet_char_mosley_idle.png` | 4 frames. Councillor Mosley, standing in the world. |
| `sheet_char_pharmacist_idle.png` | 4 frames. The pharmacist, standing in the world. |

**Open `sheet_char_player_idle.png` before drawing any player sheet** and work from the image. It
defines the face, build, clothes, and — the part that keeps failing — how much of the cell the
figure fills. See §3.

Its measurements, which are the numbers every other sheet is scored against:

| | Value |
|---|---|
| Figure height | **89% of cell height** |
| Figure width | 26% of cell width |
| Figure aspect (w ÷ h) | 0.29 |
| Baseline drift across frames | **0 px** |

### 7.2 Standard frame counts

All source cells **512×512** unless stated, one drawing per cell, subject filling ~90% of the cell
height, feet near the bottom, facing camera-right. `worldHeight` 1.35 for people.

| Action | Frames | Columns | Rows | fps | Loop |
|---|---|---|---|---|---|
| `idle` | 4 | 4 | 1 | 6 | yes |
| `walk` | 4 | 4 | 1 | 8 | yes |
| `attack` | 6 | 6 | 1 | 12 | no |
| `cast` | 6 | 6 | 1 | 12 | no |
| `hurt` | 3 | 3 | 1 | 12 | no |
| `death` | 6 | 6 | 1 | 10 | no |

Frame counts are deliberately low. Every extra frame is another chance for the figure to drift in
scale or angle, and at 65 px the difference between a 4-frame and an 8-frame walk is barely
visible. Fewer, consistent frames beat more, inconsistent ones.

**`cycle` is cancelled** — see §7.9. Do not draw it for any character.

### 7.3 Band 1 — the three refused player sheets ✅ RESOLVED

**Delivered and imported 2026-07-30** via single-frame generation + local tiling (see §7.3a).
The original full-sheet deliveries were refused for the reasons recorded below; those notes are
kept because the failure modes still apply to any future full-sheet generation.

`sheet_char_player_attack`, `sheet_char_player_cast` and `sheet_char_player_death` were first
delivered as whole sheets, refused, and measured against `sheet_char_player_idle`; these are the
real numbers, not an impression.

**Every one of them was laid out as 12 drawings in a 6×2 grid while its JSON declared 6 columns ×
1 row of 512×512 cells.** The image really is 3072×512, so the importer's dimension check passed
and it sliced six cells each containing two stacked figures. That is the first thing to fix, and
it is a layout fix, not a redraw: **six drawings, one row, one drawing per 512×512 cell.**

The second thing is scale. Measured on the grid the pixels actually show:

| Sheet | Figure fills | Aspect vs idle | Empty cells | Fragment frames | Baseline drift |
|---|---|---|---|---|---|
| `attack` | **73%** of cell height | 0.85× (15% narrower) | 0 | 0 | 12.7 px at final size |
| `cast` | **54%** | 1.07× | 1 of 12 | 3 | 43.0 px |
| `death` | **50%** | 1.57× (prone, expected) | 2 of 12 | 4 | 57.0 px |

Read that table as three separate instructions:

- **Scale the figure up.** The accepted `idle` fills 89% of its cell height. These fill half to
  three-quarters, which is why the width check refused all three — a figure drawn at 60% scale is
  60% as wide, whatever its proportions. The drawings themselves are close to correctly
  proportioned; `attack` is only 15% narrower than the idle figure, which alone would have passed.
- **`cast` and `death` have broken frames.** `cast` has one completely empty cell and three more
  holding a fragment under half the height of the others; `death` has two empty and four
  fragments. Those are not poses, they are failed generations, and they must not be delivered as
  frames. Six good frames or fewer — say so in `frameCount` — beats six slots with gaps.
- **Baselines wander.** The limit is 2 px at final size. `attack` at 12.7 px is close enough that
  fixing the scale and layout may fix it; `cast` at 43 px and `death` at 57 px are frames drawn at
  unrelated positions in their cells. `death` is exempt from this check because a falling body
  legitimately changes shape — but the exemption is for the *pose*, not for the figure wandering
  around the cell between frames.

Requested, as `sheet_char_player_<action>.png`:

| Action | Notes |
|---|---|
| `attack` | Melee swing. 6 frames, one row. |
| `cast` | Casting a spell — this is a magic game, played straight. 6 frames, one row. |
| `death` | Falling. 6 frames, one row. The figure changes shape; it does not change position in the cell. |

Player sheets are **auto-assigned on import**, so use exactly those filenames.

### 7.3a The workflow that resolved band 1: single frames + local tiling

Whole-sheet generation kept failing on layout (6×2 vs declared 6×1), scale, broken frames and
wandering baselines — four independent failure modes per image. What worked instead, and is the
recommended route for any character whose sheets keep being refused:

1. **Generate one square frame at a time** (AI Studio / Nano Banana), chaining by attaching the
   previous frame to each prompt for consistency. Backgrounds come back near-magenta but not
   exactly — the player's idle frames sampled `(238, 12, 221)`, `(234, 9, 207)` and
   `(232, 10, 192)`, so **always corner-sample the background rather than assuming `#FF00FF`**.
   Assume it and nothing keys at all.
2. **Deliver frames to `art_incoming/frames/<action>_<n>.png`** (or
   `<subject>_<action>_<n>.png` when a batch covers more than one subject), numbered from 1 and
   contiguous.
3. **Tile them with `Tools/tile_frames.py <subject> <action>`** — not the art agent, see
   AGENTS.md. It corner-samples and normalises each backdrop to pure magenta, measures the feet,
   translates each frame vertically onto one shared baseline, tiles them into a single row, and
   writes the sheet and sidecar JSON into `art_incoming/`. It then re-measures the result and
   exits non-zero rather than leave a sheet the importer would refuse.

   Two things it enforces because each cost a round trip:

   - **It never scales a frame.** Scaling blurs dark edge pixels (shoe soles) into the backdrop,
     the importer's keyer drops them, and the feet read high — this is what got past the lenient
     check on `cast_6`. Tile at whatever size the frames arrived at and declare it with
     `--frame-size` (idle was 1024², attack 512²); do **not** downscale to make batches match.
     The importer reduces to 48 px per world unit either way, so both land on the same 65 px
     cell, and one area-averaged reduction beats two.
   - **It aligns on the strict feet measure**, importing `key_mask` from `precheck_sheets.py` at
     threshold 200 rather than reimplementing it. That is the measure the importer applies after
     key-and-unmix, so the alignment performed is the alignment Unity will see. Aligning on
     anything more lenient is precisely how `cast_6` slipped through.
4. **Pre-check with `Tools/precheck_sheets.py`** before opening Unity. It replicates the
   importer's checks, including the strict threshold-200 baseline pass. It defaults to the
   current band and takes sheet names as arguments, so a different batch needs no edit:

   ```
   python Tools/precheck_sheets.py sheet_char_villager_idle.png
   ```

   It also checks two things the importer does **not**, both added after a delivery got past
   everything else:

   - **Frames must differ from one another.** Every other check measures one cell at a time, so
     one drawing tiled six times reads as six flawless cells — which is how the first Daniel
     Pauls idle passed the dimension, layout, fill, baseline and width checks while being a
     still. Byte-identical cells are named against the cell they repeat; consecutive pairs are
     also measured, as changed pixels over mean subject size, and refused below 0.10. That
     threshold is calibrated, not guessed: because every frame is an independent generation,
     real pairs land above 1.0 (lowest in the project is the pharmacist's idle at 1.04), while
     a tiled duplicate measures exactly 0.00.
   - **The width reference is the subject's own idle sheet**, resolved from `processed/` then
     staging, because the importer compares sheets of one subject against each other. A subject
     with no idle yet has its width check skipped and says so.

Death is exempt from height/baseline checks (the pose changes shape) but **never** from the width
check. `tile_frames.py` reports drift for a death sheet but does not fail on it, matching the
importer.

### 7.4 The cast — who exists and what they still need

One table so nothing is drawn twice. ✅ delivered, ⬜ requested, — not wanted.

| Subject | `idle` | `walk` | `attack` | `hurt` | `death` | `cast` | Band |
|---|---|---|---|---|---|---|---|
| `player` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 1 |
| `danielpauls` | ⬜ | ⬜ | — | — | — | ⬜ | 2 |
| `underhoused` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | — | 2 |
| `mosley` | ✅ | ⬜ | — | — | — | — | 4 |
| `pharmacist` | ✅ | ⬜ | — | — | — | — | 4 |
| `villager` | ✅ | ✅ | — | — | — | — | 4 |
| `noseyparker` | ⬜ | ⬜ | — | — | — | — | 4 |
| `squirrel` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | — | 4 |
| `police_pcso` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | — | 5 |
| `police_bobby` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | — | 5 |
| `police_armed` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | — | later |
| `police_occultagent` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | — | later |
| `police_occultcommander` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | — | later |

A subject with no `walk` sheet slides along the ground when it moves, so a roaming character needs
one and a standing one does not.

### 7.5 Band 2 — the tutorial cast

The opening magic quest is the only scripted sequence in the game and both of its characters are
untextured capsules today.

**Daniel Pauls** — `sheet_char_danielpauls_<action>.png`, actions: `idle`, `walk`, `cast`.
A stage magician in a **pink jazzy Las Vegas suit** — sequins, wide lapels, ruffled shirt, far too
much for a British council estate, which is the joke. Middle-aged, theatrical. He teaches the
player their first spell, so `cast` should be a showman's flourish rather than a grim incantation.

**The tracksuit geezer** — `sheet_char_underhoused_<action>.png`, actions: `idle`, `walk`,
`attack`, `hurt`, `death`. Sketchy bloke in a full tracksuit, **wild unkempt hair**, twitchy. He
panics and zaps the player during the opening magic quest and is then killed, so he needs the full
hostile set. `attack` is a wild flailing magic zap, not a weapon swing.

### 7.6 Band 3 — world props

**This is the band that unblocks world-building.** `Home_London` is dressed with 3D models
(houses, trees, fences, a bus stop); `North_Wasteland`, `South_Slums`, `East_RetailPark` and
`West_Canal` contain a ground plane, four edge triggers and four boundary walls — nothing else.

Buildings are billboards, but the camera is **fixed** at pitch 30°, yaw −45° and never rotates, so
draw them **in that same isometric projection** — two faces of the box visible, seen from slightly
above. Not a flat straight-on elevation. Do not paint ground, shadow or surroundings.

Props are **single sprites**, not sheets: no grid, no baseline, no frame count. They are the
cheapest thing in this pipeline and the highest-value.

*Anywhere*

| File | `worldHeight` | Notes |
|---|---|---|
| `spr_prop_shed.png` | 2.2 | A small garden shed. Timber, weathered, single door, maybe one window. |
| `spr_prop_wheelie_bins.png` | 1.1 | Two or three council wheelie bins together, lids down, one slightly askew. |
| `spr_prop_dead_tree.png` | 2.2 | Bare, scrubby, half-dead. Not a picturesque winter tree. |

*North_Wasteland — edgeland scrub, fly-tipping, nothing maintained*

| File | `worldHeight` | Notes |
|---|---|---|
| `spr_prop_pylon.png` | 9.0 | Electricity pylon, steel lattice. Tall and thin — width follows the subject. |
| `spr_prop_burnt_car.png` | 1.5 | Burnt-out hatchback, no glass, blackened. |
| `spr_prop_flytip_pile.png` | 1.4 | Fly-tipped heap: a mattress, a fridge on its side, split bin bags. |
| `spr_prop_portacabin.png` | 2.6 | Site portacabin, grubby, one door and a barred window. |

*South_Slums — council estate*

| File | `worldHeight` | Notes |
|---|---|---|
| `spr_prop_lowrise_flats.png` | 7.5 | Three- or four-storey council block, walkway balconies, pebbledash. |
| `spr_prop_boarded_house.png` | 4.5 | Terraced house with steel security screens over the door and windows. |
| `spr_prop_lockup_garages.png` | 2.4 | A run of three or four lock-up garages, up-and-over doors, one dented. |
| `spr_prop_offlicence.png` | 3.6 | Corner off-licence, shutters half down, cluttered window, cheap signage. |

*East_RetailPark*

| File | `worldHeight` | Notes |
|---|---|---|
| `spr_prop_office_building.png` | 6.0 | A sketchy, boxy low-rise office block. Plain, cheap, slightly grim. Simple massing, few details. |
| `spr_prop_retail_unit.png` | 5.0 | Big-box retail shed, flat roof, glazed front, blank fascia — no real brand names. |
| `spr_prop_pylon_sign.png` | 4.5 | Tall illuminated retail-park sign on a pole, blank panels. |
| `spr_prop_trolley_bay.png` | 1.6 | Steel trolley bay with a few trolleys in it. |

*West_Canal*

| File | `worldHeight` | Notes |
|---|---|---|
| `spr_prop_narrowboat.png` | 1.8 | Moored narrowboat, painted, slightly shabby. Drawn side-on-ish to the camera like everything else. |
| `spr_prop_lock_gate.png` | 2.4 | Canal lock gate, black timber, white-tipped balance beam. |
| `spr_prop_canal_bridge.png` | 3.2 | Small brick humpback bridge over the cut. |
| `spr_prop_reeds.png` | 1.1 | A clump of canal-bank reeds. |

*Home_London*

| File | `worldHeight` | Notes |
|---|---|---|
| `spr_prop_pub_exterior.png` | 5.0 | A proper British estate pub — brick, hanging sign, frosted glass. **The pub is the game's manual save point**, so it must read as a pub at 240 px and from across the street. |
| `spr_prop_corner_shop.png` | 4.0 | Newsagent-style corner shop, awning, ice-cream A-board. |

> **Note for the Unity side, not the art agent:** props import to `Assets/Art/Generated/props/` and
> are wired by hand or by a `PlacementPreset`. Only the player, the e-bike and NPC subjects with a
> matching `ArtSubject` on a preset are auto-assigned.

### 7.7 Band 4 — the ambient cast

**Councillor Mosley** — `sheet_char_mosley_walk.png`. Idle is delivered; match it exactly.
Elderly UK city councillor, pensioner, ill-fitting grey suit, lanyard, comb-over, self-important
posture.

**Roaming pharmacist** — `sheet_char_pharmacist_walk.png`. Idle is delivered; match it exactly.
A drug dealer with the bearing and costume of a high-street pharmacist — white coat, name badge,
clipboard, entirely straight-faced about it. The gag is deadpan; play it completely seriously.

**Villager** — `sheet_char_villager_<action>.png`, actions: `idle`, `walk`.
The generic background human. Unremarkable on purpose: jeans, jacket, carrier bag. This one gets
placed dozens of times, so it must be forgettable rather than characterful.

**Nosey Parker** — `sheet_char_noseyparker_<action>.png`, actions: `idle`, `walk`.
A civilian who phones the police when they see you casting. **Must be recognisable at a glance and
distinct from the villager** — this is a gameplay signal, not decoration; the player has to learn
to spot one across a street. Suggested read: middle-aged, arms folded or phone already in hand,
net-curtain energy, a hi-vis "community watch" tabard if that helps them stand out.

**Angry squirrel** — `sheet_char_squirrel_<action>.png`, actions: `idle`, `walk`, `attack`,
`hurt`, `death`. **`worldHeight` 0.45** — it finishes around 22 px, so source cells of 256×256 are
plenty rather than the usual 512. A genuinely furious grey squirrel. Comic menace, not cute.

### 7.8 Band 5 — the consequence layer

Five police tiers escalate as the wanted level rises. All five are untextured capsules today.
Actions for each: `idle`, `walk`, `attack`, `hurt`, `death`. **Band 5 is the first two only** —
`police_pcso` and `police_bobby`. The rest are listed so the visual escalation can be designed as
a set, and are requested later.

| Subject | Tier | Look |
|---|---|---|
| `police_pcso` | 1 | Community support officer. Hi-vis yellow, no kit, apologetic. |
| `police_bobby` | 2 | Regular constable. Navy, stab vest, radio. |
| `police_armed` | 3 | Armed response. Black, helmet, carbine. |
| `police_occultagent` | 4 | Occult Agent. Brown trench coat, sigils where the insignia should be. |
| `police_occultcommander` | 5 | Occult Commander. Ministry red, ceremonial, unmistakably the worst thing that has happened to you. |

The escalation has to read at 65 px, so **separate the tiers by silhouette and colour block**, not
by detail: yellow → navy → black → brown → red, getting bulkier as they go.

### 7.9 Cancelled and not requested

- **`cycle` — cancelled.** The rider is drawn by layering the e-bike sprite over the ordinary
  character sprite, which is what the game already does. There is no `Cycle` animation state to
  fill. Do not draw a `cycle` sheet for the player or anyone else; the rejected
  `sheet_char_player_cycle` has been discarded rather than sent back.
- **`spr_char_player_ebike` — not requested.** An old version of this document asked for a single
  sprite of the player on the bike. Nothing consumes it.
- **Per-class player variants — not requested.** One character serves all four classes; the classes
  differ in stats only.
