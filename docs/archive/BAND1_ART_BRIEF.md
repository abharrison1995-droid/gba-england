> ⚠️ **ARCHIVED.** Superseded and kept for history. Nothing here is outstanding work.

# Band-1 art brief — the three refused player sheets (paste into Gemini Antigravity)

> **STATUS (2026-08-03): COMPLETE — kept for method, not for work.** Band 1 is marked ✅ RESOLVED
> in the art queue; the player's attack, cast and death sheets were delivered, imported
> and play-tested, and the `cycle` sheet was cancelled outright. Nothing here is outstanding.
>
> It is kept because the **approach change below is the reusable part**: single-frame generation
> plus local tiling, which is how every sheet has been produced since. That workflow now lives in
> `docs/art/SHEET_WORKFLOW.md`. Read this only for the reasoning behind it.

> **APPROACH CHANGE (2026-07-29, second refusal):** the second batch came back with multiple
> figures per cell (stacked pairs, onion-skin ghosts) — this generator cannot be trusted to
> draw grids. **Do NOT generate sheets directly.** Generate 18 single-frame PNGs (six per
> action, one figure per 512×512 image) into `art_incoming/frames/` named
> `<action>_<n>.png` (`attack_1.png` … `death_6.png`). Kimi tiles each six into the
> 3072×512 sheet locally, runs the importer checks, and writes the sidecar JSONs. The frame
> prompts are being issued one at a time in chat; the pose lists per action are in that
> conversation. Everything else in this brief (background, style, fill, baselines, JSON
> values) still applies — it just applies to the final tiled sheet, which Kimi assembles.

You are the art agent for this project. Your standing contract is `ART_PIPELINE.md` (spec) and
`AGENTS.md` (hard rules) — read both. The short version of the hard rules: **write PNG +
sidecar JSON into `art_incoming/` and nothing else.** Never inside `Assets/`, never a `.meta`
file, never git, never Unity. One PNG per asset plus its `.json`; no intermediates, no `_v2`
files — regenerating overwrites the same filename.

## The task

Redraw the three refused player sheets. The previous attempts are in `art_incoming/rejected/`
— look at them to see what failed, but your primary visual reference is the **accepted**
`sheet_char_player_idle` / `sheet_char_player_walk` / `sheet_char_player_hurt` (§7.1). Same
person, same clothes, same three-quarter view facing camera-right, across all three new
sheets. Open the idle PNG and work from the image, not from a text description — prompting
the same text twice produces two different people.

Deliver exactly three pairs (exact filenames — player sheets are auto-assigned on import):

    sheet_char_player_attack.png + sheet_char_player_attack.json
    sheet_char_player_cast.png   + sheet_char_player_cast.json
    sheet_char_player_death.png  + sheet_char_player_death.json

- `attack` — melee swing. 6 frames.
- `cast` — casting a spell. This is a magic game, played straight. 6 frames.
- `death` — falling. 6 frames. The figure changes *shape* (it ends prone); it does not
  change *position* within the cell.

## Why the last attempts were refused — measured, not impressionistic

All three were refused on the importer's checks. These are the real numbers, and each maps
to a specific instruction:

1. **Layout was 6×2 (twelve drawings) while the JSON declared 6×1 of 512×512.** The image
   really was 3072×512, so the dimension check passed and the importer sliced six cells each
   holding two stacked figures. **Fix: six drawings, ONE row, one drawing per 512×512 cell.
   Total image 3072×512. Then count the drawings in the final image and make `frameCount`
   that number.**

2. **Figures drawn too small in the cell.** Measured fills: attack 73%, cast 54%, death 50%
   of cell height — against the accepted idle's **89%**. This, not "wrong proportions", is
   what tripped the width check (a figure at 60% scale is 60% as wide, whatever its pose).
   **Fix: the subject fills ~90% of its 512×512 cell height, feet a few pixels off the
   bottom edge, horizontally centred, in every frame.**

3. **Broken frames.** `cast` had 1 empty cell + 3 fragment frames; `death` had 2 empty + 4
   fragments. Those are failed generations, not poses. **Fix: six good frames, or fewer with
   `frameCount` set honestly — never ship an empty or fragment cell as a frame.**

4. **Baseline wander.** Feet must land on the same pixel row in every cell; the limit is
   2 px at final size. Previous drift: attack 12.7 px, cast 43 px, death 57 px. **Fix: same
   ground line every frame. A swing moves the arms; the ground does not move.** (`death` is
   exempt from height/baseline checks because a falling body changes shape — the exemption
   covers the *pose*, not the figure wandering around its cell.)

## Standing rules that apply (from ART_PIPELINE.md — do not skip)

- **Background: flat solid magenta `#FF00FF`**, pure, edge to edge — no gradient, no
  vignette, no cast shadow, no floor. (Real alpha instead is fine if your tool can do it.)
  Do not use magenta anywhere in the subject itself.
- **PNG only**, no JPEG. Deliver at source size (cells 512×512); the importer reduces to
  48 px/world-unit — never deliver the 65 px final size yourself.
- Sheets are **not** trimmed by the importer; every cell must be identical size, frames left
  to right in a single row, full body in frame (no feet cut off).
- Every sheet of the player must agree with the accepted sheets: same view angle, same body
  width, same height, same clothes. The width check refuses anything >1.4× narrower than the
  idle sheet and does not care how good the pose is.

## Sidecar JSONs

`type: "sheet"`, `category: "characters"`, `worldHeight: 1.35`, cells 512×512, one row:

| File | action | frameCount | columns | rows | fps | loop |
|---|---|---|---|---|---|---|
| `sheet_char_player_attack` | `attack` | 6 | 6 | 1 | 12 | false |
| `sheet_char_player_cast` | `cast` | 6 | 6 | 1 | 12 | false |
| `sheet_char_player_death` | `death` | 6 | 6 | 1 | 10 | false |

If you deliver fewer good frames, set `frameCount` to the real number (and keep
`columns × rows` matching the actual grid). If anything in this brief is ambiguous, add a
`"question": "..."` field to that asset's JSON and produce your best attempt anyway.

Example (`sheet_char_player_cast.json`):

```json
{
  "name": "player_cast",
  "type": "sheet",
  "category": "characters",
  "action": "cast",
  "worldHeight": 1.35,
  "frameWidth": 512,
  "frameHeight": 512,
  "columns": 6,
  "rows": 1,
  "frameCount": 6,
  "fps": 12,
  "loop": false,
  "description": "Six-frame spell cast, one row, one drawing per cell, subject filling ~90% of cell height, shared baseline, flat magenta #FF00FF background."
}
```

## Done means

Three PNG+JSON pairs at the top level of `art_incoming/` with the exact filenames above.
Claude Code runs the importer (`Tools → GBA → Art → Import Generated Art`), which keys the
magenta, slices from your JSON, runs the width/baseline/empty-cell checks described above,
and archives accepted pairs to `art_incoming/processed/`. Anything it refuses stays in
`art_incoming/` with the reason in its output.
