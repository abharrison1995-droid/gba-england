"""Reference sprite subject: the untextured proxy humanoid.

The template every character subject is copied from — the sprite-side
equivalent of assets/prop_barrel.py. A subject script is a few lines of
declaration; all the machinery lives in lib/sprite_kit.py.

Run:
  python Tools/blender/bpy_runner.py Tools/blender/sprites/char_proxy.py
  python Tools/pack_sprites.py proxy

Outputs frames under Tools/blender/out/sprites/proxy/<action>/, which
pack_sprites.py turns into art_incoming/sheet_char_proxy_<action>.png + .json.

To regenerate an existing sheet smoother or longer, change the frame count
below and re-run both commands. The pose functions are parametric in (i, n),
so an 8-frame walk is the same walk as the 6-frame one, sampled finer.
"""

import sprite_kit as sk

SUBJECT = "proxy"

# Must equal WorldActorVisual.Height for this actor: player 1.8, adult NPC
# 1.55 (EKVibe.CharacterHeight), child 1.3. See ART_PIPELINE.md §2 — a wrong
# value does not change how big the actor looks, only how many pixels get
# stretched to fill the space.
WORLD_HEIGHT = 1.55

# Frame counts default to the ART_PIPELINE.md §8 table. Override any action to
# resample it; omit an action entirely to skip rendering it.
ACTIONS = {
    "idle":   {"frames": 4, "fps": 6,  "loop": True},
    "walk":   {"frames": 6, "fps": 8,  "loop": True},
    "attack": {"frames": 6, "fps": 12, "loop": False},
    "hurt":   {"frames": 3, "fps": 12, "loop": False},
}

COLORS = {
    "skin":   (0.72, 0.57, 0.45),
    "top":    (0.35, 0.36, 0.38),
    "bottom": (0.14, 0.16, 0.20),
    "shoes":  (0.09, 0.09, 0.10),
}


sk.render_subject(
    SUBJECT,
    world_height=WORLD_HEIGHT,
    colors=COLORS,
    actions=ACTIONS,
    resolution=512,
)
