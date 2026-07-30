# Daniel Pauls — frame-by-frame prompts (Band 2)

Workflow (per ART_PIPELINE.md §7.3a): generate **one 512×512 frame at a time**,
attaching the previous frame to each prompt after the first. Deliver frames to
`art_incoming/frames/idle_1.png`, `walk_1.png`, `cast_1.png`, etc. Claude Code
tiles them into sheets locally — never ask Gemini for a full sheet.

Sheets: `idle` (4 frames, loop), `walk` (4 frames, loop), `cast` (6 frames, no loop).
14 generations total.

---

## CHARACTER BLOCK — paste at the top of EVERY prompt

> A photorealistic full-body image of a fictional middle-aged British man, a faded
> stage magician named Daniel Pauls. He is bald, with a large pot belly straining
> against a short-sleeved button-up shirt that is clearly too small for him — the
> buttons pull and a strip of belly shows below the hem. He wears khaki cargo shorts
> and cheap flip-flops. Theatrical, slightly seedy showman energy; he carries himself
> like he is still on stage in Vegas, not a British council estate. Synthetic person,
> not a real identifiable individual.

## RULES BLOCK — paste after the character block in EVERY prompt

> Style and framing rules (strict):
> - Photorealistic, like a photograph of a real costume — NOT cartoon, NOT pixel art,
>   NOT illustration, no outlines.
> - Three-quarter view, seen slightly from above (camera looks down at ~30 degrees).
> - He faces to the RIGHT of the image (camera-right). Never left.
> - Flat solid magenta background, exactly #FF00FF, one colour edge to edge.
>   No gradient, no vignette, no floor, no ground plane, no cast shadow.
> - Full body in frame, feet included, nothing cropped.
> - He fills about 90% of the image height, feet a few pixels above the bottom edge.
> - His feet must land on the same horizontal line as the attached previous frame,
>   and he must be the same height, width, clothes and view angle as that frame.
> - Square image, 512×512.

(For the first frame of each sheet there is no previous frame — just say "this is
the reference frame that defines the character; later frames must match it.")

---

## SHEET 1 — `sheet_char_danielpauls_idle` (4 frames, subtle breathing loop)

**Frame 1** (reference frame):
> Pose: standing relaxed, weight even on both feet, arms resting loosely at his
> sides, shoulders slightly slumped, a faint self-satisfied half-smile. Neutral
> showman-at-rest.

**Frame 2**:
> Same man, same clothes, same framing as the attached frame. Pose: he has breathed
> in — chest and belly lifted slightly, shoulders risen a touch, chin up, as if
> about to address an audience. Feet and body otherwise identical to the attached
> frame.

**Frame 3**:
> Same man, same framing. Pose: settling the breath — shoulders dropped back down,
> and he has rested his right hand on top of his pot belly, left arm still at his
> side. Same foot positions as the attached frame.

**Frame 4**:
> Same man, same framing. Pose: nearly back to the neutral stance of frame 1, hand
> off the belly, but weight shifted subtly onto his left leg so the loop has a
> gentle sway. Must read as one small motion away from the first frame.

---

## SHEET 2 — `sheet_char_danielpauls_walk` (4 frames, standard walk cycle)

**Frame 1** (reference frame):
> Pose: mid-stride, right foot forward with the heel just touching down, left foot
> behind on the toe, arms swinging naturally opposite the legs (left arm forward,
> right arm back). Upright, unhurried stroll, belly leading slightly.

**Frame 2**:
> Same man, same clothes, same framing as the attached frame. Pose: right foot now
> flat on the ground carrying his weight, left leg swinging through beneath his
> body, knee bent, both arms passing close to his sides. Feet on the same baseline
> as the attached frame.

**Frame 3**:
> Same man, same framing. Pose: mirror of the first frame — left foot forward with
> the heel touching down, right foot behind on the toe, right arm forward, left arm
> back. Same stride length and body height as the attached frame.

**Frame 4**:
> Same man, same framing. Pose: mirror of the second frame — left foot flat carrying
> his weight, right leg swinging through beneath his body, knee bent, arms passing
> his sides. This frame must lead naturally back into the attached first frame so
> the walk loops smoothly.

---

## SHEET 3 — `sheet_char_danielpauls_cast` (6 frames, showman's flourish, no loop)

**Frame 1** (reference frame):
> Pose: neutral standing, arms at his sides, feet together-ish, a knowing grin —
> the pause before the trick. Relaxed, weight even.

**Frame 2**:
> Same man, same clothes, same framing as the attached frame. Pose: he has raised
> both arms out to his sides at shoulder height, palms up, presenting himself to
> the audience — the classic "behold" gesture. Belly proudly forward. Feet planted
> exactly as in the attached frame.

**Frame 3**:
> Same man, same framing. Pose: his right arm sweeps up high above his head, fingers
> spread, left hand dropped to rest on his belly, head tilted up following the right
> hand. Theatrical wind-up. Feet planted as in the attached frame.

**Frame 4**:
> Same man, same framing. Pose: both hands thrust forward together toward the right
> of the image, fingers splayed, a faint glow of pale blue-white magical light
> beginning to gather between his palms. Leaning slightly into it. Feet planted as
> in the attached frame.

**Frame 5**:
> Same man, same framing. Pose: full release — he leans forward, both arms fully
> extended to the right, and a bright burst of pale blue-white arcane energy
> erupts from his open palms, crackling a short distance past his fingertips.
> Magic played straight, real light, not cartoon sparks. Feet planted as in the
> attached frame.

**Frame 6**:
> Same man, same framing. Pose: follow-through — arms dropping back down, the light
> fading to a wisp at his fingertips, the start of a smug little showman's bow,
> weight still on the same feet as the attached frame.

---

## After generation

1. Corner-sample each PNG's background — Gemini rarely returns exact #FF00FF; note
   the actual colour if it's off.
2. Save as `art_incoming/frames/idle_1.png` … `cast_6.png`.
3. Tell Claude Code the frames are in — it re-baselines, normalises the magenta,
   tiles the sheets, writes the JSON, and runs `Tools/precheck_sheets.py` before
   import.
