"""Prototype subject on the photo-cutout path: Mandrew.

Proves sprite_kit's `part_images` seam — each body part is a camera-facing
textured card cut from one staged source image, animated by the same rig and
pose functions as the flat-colour proxy.

Source is the SYNTHETIC `mandrew_idle_1.png` already staged in
art_incoming/frames/, per ART_PIPELINE.md §1: generated people only, never a
photograph of a real identifiable person.

Run:
  python Tools/cut_parts.py art_incoming/frames/mandrew_idle_1.png mandrew
  python Tools/blender/bpy_runner.py Tools/blender/sprites/char_mandrew.py
  python Tools/pack_sprites.py mandrew
"""

import json
from pathlib import Path

import sprite_kit as sk

SUBJECT = "mandrew"
WORLD_HEIGHT = 1.55  # adult NPC — must equal WorldActorVisual.Height

ACTIONS = {
    "idle":   {"frames": 4, "fps": 6,  "loop": True},
    "walk":   {"frames": 6, "fps": 8,  "loop": True},
    "attack": {"frames": 6, "fps": 12, "loop": False},
    "hurt":   {"frames": 3, "fps": 12, "loop": False},
}

PARTS_JSON = sk.OUT_DIR / "parts" / SUBJECT / "parts.json"
if not PARTS_JSON.is_file():
    raise SystemExit(f"No cut parts at {PARTS_JSON}. Run Tools/cut_parts.py first.")
part_images = json.loads(Path(PARTS_JSON).read_text())

sk.render_subject(
    SUBJECT,
    world_height=WORLD_HEIGHT,
    part_images=part_images,
    actions=ACTIONS,
    resolution=512,
)
