---
name: model-author
description: Build a low-poly 3D model for GBH England as a procedural Blender script — parametric boxes plus a painted pixel atlas, run headless, previewed at the game camera and exported to .glb. Studies reference art or an existing model first, then iterates on the render until it reads. Use when the user wants to create, rebuild or refine a 3D model, building shell or prop (band 6 London buildings and anything like them).
---

# Model author

You are building **one 3D model** as a Python script under `Tools/blender/assets/`. The script is
the asset — it is diffable, re-runnable, and regenerates the `.glb` and its preview on demand.
Nothing here costs credits and nothing leaves the machine.

This is the **approved band 6 delivery route** as of 2026-08-18 (`docs/art/ART_QUEUE.md`). It
replaced cloud image-to-3D; the old shop models are Tripo output at ~2,900 tris with photo-baked
textures, and the models you build should land near **100–400 tris** and read *better* at game
distance because the detail is authored pixel art rather than a muddy bake.

## Read first — do not re-derive the pipeline

- `Tools/blender/README.md` — the architecture, conventions and layout.
- `Tools/blender/assets/building_quidland.py` — the worked example. Copy its shape.
- `Tools/blender/lib/asset_kit.py` and `lib/atlas.py` — the helpers you have. Read them before
  writing anything by hand; nearly everything you need is already there.

## Run it like this

```bash
python Tools/blender/bpy_runner.py Tools/blender/assets/<name>.py
```

Blender 5.2 is installed and the runner finds it on its own — no `BLENDER_EXE` needed. Output
lands in `Tools/blender/out/` (gitignored): `<name>.glb`, `<name>_preview.png`, and the atlas PNG.
A Python exception exits non-zero, so a failure is never silent.

To study an existing `.glb` before rebuilding it — always worth doing when one exists:

```bash
python Tools/blender/bpy_runner.py Tools/blender/assets/inspect_glb.py -- "<path.glb>" <preview_name>
```

## The loop that actually works

1. **Gather the reference.** If the owner supplied images, read them. If an old model exists,
   `inspect_glb.py` it and *look at the render*. If neither, get the written spec (band 6 gives one
   line per building) and ask the owner for anything load-bearing you'd otherwise invent.
2. **Name the palette and the regions** — decide the atlas layout as pixel rects up front, as
   constants at the top of the script. Keep the atlas at 256px unless the model genuinely needs more.
3. **Paint, build, map, join, finalize, preview, export** — the Quidland script in that order.
4. **Read your own preview with the Read tool.** This is the step that matters and the one that is
   easy to skip. Do not report a model you have not looked at.
5. **Iterate on what the render actually shows.** Crop and enlarge a region when something looks
   off (`System.Drawing` via PowerShell, nearest-neighbour, is enough).

## Conventions that are not negotiable

- **1 unit = 1 metre**, and scale against the cast: NPCs are **1.55 m**, the player **1.8 m**. A
  shopfront door wants ~2.1–2.3 m. Build at real size — do not build small and scale in Unity.
- **Front faces −Y.** The preview camera is at 30° pitch / 45° yaw, matching `IsometricCameraFollow`,
  so −Y and +X are the two faces the player sees. Put the detail there and keep the back cheap.
- **`kit.finalize(obj)` before export** — applies modifiers, flat-shades, applies transforms, and
  puts the origin at **bottom-centre on the world origin** so a placed prefab rests on the floor.
- **One material, one atlas**, nearest-filtered. Detail belongs in the texture, never in geometry.
- **Exterior shells only** for buildings: opaque windows, no interior, no cutaway roof, and a
  **clearly readable door at ground level** — that threshold is where the USE prompt lives, and the
  inside is a separate Unity-side chunk prefab.
- Print `kit.report_stats(obj)` so the tri count is in the log, and mention it when you report back.

## Traps that have already cost time

- ⚠ **A sign that "looks sheared" in the preview is almost certainly correct.** Text on a wall
  descends at 30° under isometric projection. Before you go debugging UVs, render the same box
  straight on, or dump the face UVs, and confirm there is a real defect. This wasted a full
  debugging round once already.
- **Blender ignores `PYTHONPATH`.** The runner injects `lib/` via `--python-expr`; do not "fix"
  this by setting the env var.
- **`bpy.ops` acts on the selection**, so helpers that select (`join`, `finalize`) must not be
  interleaved with per-object work. Map every object's UVs first, then join, then finalize.
- **Blender's face-normal projection mirrors easily.** If a texture reads backwards on one side,
  it is the projection basis in `map_faces_to_region`, not the atlas.
- `atlas.FONT` is a 5×7 pixel font covering only the glyphs used so far. Add what you need; an
  unknown character silently advances a blank space.

## Hand off — you cannot finish this yourself

Getting a `.glb` into the game is a Unity step and it is the **owner's**, per §5 of CLAUDE.md.
Tell them plainly, and never claim the model "works in game":

1. Copy the `.glb` from `Tools/blender/out/` into `Assets/3DModels/…` — suggest placing it
   *alongside* the model it replaces, not over it, until they have seen it in the scene.
2. Let Unity import it, then **commit the `.glb` and its `.meta` together** — the GUID in that
   `.meta` is what binds any placement.
3. Swap the placed instance in the chunk prefab. Models built here are at **real scale**, so the
   instance wants **scale 1** — the old Tripo models were ~1 m and scaled up, so an in-place swap
   will look enormous until the scale is reset.
4. Look at it from the in-game camera and at the distance the player actually meets it.

Then update the band 6 table in `docs/art/ART_QUEUE.md` — "Built" there means the script exports a
`.glb`, **not** that the model is in the game.

## Never

- Place a `.glb` into `Assets/` yourself, or overwrite an existing model — the import, the `.meta`
  commit and the scene swap are the owner's.
- Claim a model renders correctly in Unity. You can show a Blender preview and a tri count; that is
  all you can honestly claim.
- Model an interior, a cutaway or rooms visible through windows on a building shell.
- Bake a photo texture or reach for a cloud image-to-3D service — the whole point of this route is
  that it is local, free and deterministic.
- Leave a preview unlooked-at. Read the render before you report.
