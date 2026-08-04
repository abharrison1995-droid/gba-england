# Sheet workflow — single-frame generation and local tiling

```
Last verified against: ccfa9c9
Verification scope:    the workflow below produced the player's attack, cast and death sheets,
                       which imported cleanly and were play-tested. The scripts it names live in
                       Tools/ and are tracked.
```

**Read this before generating a multi-frame sheet.** Generating a whole sheet in one image failed
three times in a row for reasons that were measured rather than guessed; this is what replaced it.
The contract itself is [`../../ART_PIPELINE.md`](../../ART_PIPELINE.md); what is wanted is
[`ART_QUEUE.md`](ART_QUEUE.md).

## The failure that produced this workflow

**Delivered and imported 2026-07-30** via single-frame generation + local tiling, described below.
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

## The workflow: single frames + local tiling

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
