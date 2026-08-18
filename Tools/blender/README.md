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
