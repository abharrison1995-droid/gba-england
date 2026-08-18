# Tools/blender — local, credit-free 3D asset pipeline

Procedural low-poly assets authored as `bpy` scripts, executed in a local
Blender, exported as `.glb` (the format the project already imports — see
`Assets/3DModels`). No cloud APIs, no credits, fully deterministic and
diffable: the asset *is* its script.

## Architecture

**Tier 1 (default): headless subprocess.** `bpy_runner.py` launches
`blender --background --factory-startup --python <script>` per job and captures
stdout/stderr. No addon, no server, no state between runs. An exception in the
script exits non-zero, so failure is never silent.

**Tier 2 (optional): live socket bridge.** When a human wants to watch the
viewport, run `bridge_addon.py` inside a GUI Blender (Scripting workspace →
Run Script); `bridge_client.py` then sends code into that live session over
localhost:8666. Same scripts work in both tiers.

An MCP server (e.g. blender-mcp) was considered and rejected: it needs `uv`
(not installed), an addon install, and a running GUI, and adds nothing over a
subprocess call from an agent that already has shell access.

## Layout

```
bpy_runner.py     # entry point: run an asset script headless, capture output
lib/asset_kit.py  # bpy helpers: palette materials, face painting, origin fix,
                  # iso preview render, GLB export (imported by asset scripts)
assets/           # one script per asset — prop_barrel.py is the template
out/              # renders + exports land here (gitignored)
bridge_addon.py   # optional live bridge (paste into a GUI Blender)
bridge_client.py  # talks to the live bridge
blender-portable/ # unzip a portable Blender here (gitignored), or set BLENDER_EXE
```

## Usage

```
python Tools/blender/bpy_runner.py Tools/blender/assets/prop_barrel.py
```

Produces `out/prop_barrel.glb` and `out/prop_barrel_preview.png` (isometric
Workbench render at the game camera's 30° pitch / 45° yaw, flat-lit — a fair
preview of the in-game look).

## The 2D branch: sprite sheets from a proxy rig

Same architecture, same runner, different output. A **subject** is a script in
`sprites/`; `lib/sprite_kit.py` builds a segmented humanoid, poses it from
parametric functions, and renders one PNG per frame through a fixed
orthographic camera. `Tools/pack_sprites.py` (plain CPython + Pillow, no
Blender) packs those into the sheet + sidecar JSON that `ART_PIPELINE.md`
specifies.

```
python Tools/blender/bpy_runner.py Tools/blender/sprites/char_proxy.py
python Tools/pack_sprites.py proxy
```

Writes `art_incoming/sheet_char_proxy_<action>.png` + `.json`, ready for
`Tools → Art → Import Generated Art`.

```
lib/sprite_kit.py        # rig, poses, camera, render (runs inside Blender)
sprites/char_proxy.py    # the template subject — copy this per character
out/sprites/<subj>/<action>/frame_NN.png + manifest.json
Tools/pack_sprites.py    # frames -> sheet + sidecar, and the contract checks
```

### Why this shape

- **Regeneration is the point.** Pose functions are parametric in `(frame_index,
  frame_count)`, so changing a frame count resamples the *same* motion rather
  than authoring a new one. A 6-frame walk and a 10-frame walk are the same
  walk, one sampled finer.
- **Scale is deterministic.** `fit_camera_to_poses` samples every pose function
  at a fixed rate (`FIT_SAMPLES`), never at the declared frame counts, so
  `ortho_scale` depends only on the rig and the camera. Verified: a subject
  re-rendered at 6 and at 10 frames fits to the same `1.727`. This is what
  keeps every sheet of a subject — and every subject of the same height —
  drawn at one scale, which is exactly what the importer's body-width check
  measures.
- **The baseline is pinned in camera space, not world Z.** At the contract's
  30° pitch the pixel-lowest point is whichever ground contact is nearest the
  camera, so in a walk it alternates feet. Snapping world Z left 23 px of
  drift; snapping in camera space gives 0.
- **Checks run before Unity.** `pack_sprites.py` exits 1 without writing when a
  sheet would be refused, so a failure costs seconds instead of an editor
  round trip.

### The checks mirror ArtImportTool — do not make them stricter

`pack_sprites.py` reimplements `MeasureCells` / `CheckFrameAlignment` /
`CheckSubjectConsistency` from `Assets/Editor/ArtImportTool.cs`. The constants
are duplicated at the top of the file and **must stay equal to the C#**:

| Rule | Threshold | Notes |
|---|---|---|
| Opaque pixel | alpha **> 8** | strictly greater, as the C# does |
| Baseline drift | ≥ **2 px at final size** | `drift × worldHeight × 48 ÷ frameHeight`, *not* raw pixels |
| Body width vs idle | > **1.4×** narrower | idle is the reference sheet |
| Body height vs idle | > **1.15×** | shape-changing actions exempt |

There is **no absolute cell-fill rule.** An earlier version of this checker
invented one ("must fill ~90%") and rejected four sheets the importer would
have accepted. The ~90% figure in `ART_PIPELINE.md` is drawing guidance for a
generation agent; the importer only ever compares a sheet to its own idle.

Likewise, drift is judged *after* reduction to 48 px/unit. A 2 px wobble on a
512 px cell is 0.29 px in game, which the importer reports as "negligible at
final size" and imports. Chasing it to a literal 0 is chasing rasterisation.

## The photo-cutout path (`part_images`)

Prototyped end to end on `sprites/char_mandrew.py`:

```
python Tools/cut_parts.py art_incoming/frames/mandrew_idle_1.png mandrew
python Tools/blender/bpy_runner.py Tools/blender/sprites/char_mandrew.py
python Tools/pack_sprites.py mandrew
```

`cut_parts.py` keys the magenta backdrop, despills the anti-aliased fringe,
and slices the figure into 13 parts by the anatomical `BANDS` table, recording
each part's real position as `u/v` fractions of figure height. `build_cutout_rig`
rebuilds those as textured cards, so unposed the rig reassembles the source.

**⚠ It is a 2D paper doll, not a 3D figure.** Cards cannot foreshorten, so:

- The whole hierarchy hangs off a root empty rotated `azimuth + 90°` about Z.
  That puts local X on the camera's right axis (cards face the camera) and
  local Y on the view axis (the pose functions' `ry` swings limbs *in the
  screen plane*). The root deliberately gets **no** `matrix_parent_inverse` —
  that would cancel the very rotation it exists to apply.
- Cards need explicit depth (`CUTOUT_DEPTH`) or they draw in cut order. Without
  it the torso card's top edge painted the jacket collar across the face.
- Geometry checks use `_SILHOUETTE` probes, not the card rectangles. A rotated
  rectangle's lowest corner is usually transparent, which is worth 18 px of
  phantom drift.
- **Limbs that overlap the body in the source have no silhouette of their own.**
  An arm cut from against the jacket is a fully opaque rectangle, and at large
  swings it reads as a rotating black block. Subtle motion (idle, a modest
  walk) is what this path is good for; a full attack swing is not.

Bands are tuned to a front-on standing figure. A differently posed source needs
its own set — pass `--bands` a JSON override rather than editing the default.

### Adding a subject

Copy `sprites/char_proxy.py`, set `SUBJECT`, `WORLD_HEIGHT` (it must equal
`WorldActorVisual.Height` — player 1.8, adult NPC 1.55, child 1.3) and
`COLORS`. Frame counts default to the `ART_PIPELINE.md` §8 table.

To drive it from a photorealistic source instead of flat boxes, cut the source
into per-part PNGs with alpha and pass `part_images={"torso": "...", ...}` to
`render_subject`; each part becomes a camera-facing textured card and animates
identically. That path switches the engine to Cycles automatically (Workbench
ignores material alpha) and is **rendered but not yet exercised on real art**.

### Actions

`idle`, `walk`, `attack` and `hurt` have pose functions today. `death`, `roll`,
`knockback` and `cycle` are declared shape-changing in both `sprite_kit.py` and
`pack_sprites.py` — exempt from ground-snapping and from the baseline/fill
checks — but **have no pose function yet**; adding one is a function in `POSES`
and nothing else. Keep those two lists in step.

## Conventions every asset script must follow

- 1 unit = 1 metre. NPCs are 1.55 m, the player 1.8 m — scale props to that.
- Call `kit.finalize(obj)` before export: applies modifiers, flat-shades,
  applies transforms, sets the origin to **bottom-centre at the world origin**
  so a placed prefab rests on the floor.
- Colour via `kit.make_palette_material` + `kit.paint_faces` — one material,
  one tiny palette PNG, UVs snapped to texel centres. No per-object textures.
- Export with `kit.export_glb` (Y-up for Unity) and print `kit.report_stats`
  so the tri count is in the log.
- Getting a `.glb` into the game is still a Unity-side step: copy it under
  `Assets/3DModels/`, let Unity import it, and commit the `.meta` with it.
