# The art importer and actor visuals

```
Last verified against: working tree, 2026-08-06
Verification scope:    code. Player-class profile refresh and creator preview wiring are
                       UNVERIFIED in Unity. The importer has done real round trips (Mosley, the pharmacist, the
                       player's five sheets, the London enemies) and the BuildController fix was
                       play-tested. Sprite sizing at the NEW 1.55/1.8 heights is UNVERIFIED —
                       nothing has been seen rendered since that change.
```

This document owns the **Unity side**: what `ArtImportTool` does to a delivered PNG, and how
`WorldActorVisual` sizes what comes out. The **contract with the art agent** — resolution, chroma
key, sheet layout, sidecar JSON, naming — is [`ART_PIPELINE.md`](../../ART_PIPELINE.md). What is
delivered and what is outstanding is [`../art/ART_QUEUE.md`](../art/ART_QUEUE.md).

## Where the entry points are

`Tools → GBH → Art → Import Generated Art` (`Editor/ArtImportTool.cs`) keys out the backdrop,
trims, reduces, sets import settings, slices sheets, builds clips and an `AnimatorController`,
then assigns known assets to what was waiting for them.

`Tools → GBH → Content → Wire Presets From Imported Art` re-runs only the assignment step, for art
that landed in an earlier batch.

## The art direction is a post-process, not a prompt

Sources arrive photoreal and large; the importer area-averages them down to **48 px per world
unit**, so a 1.55-unit character lands near 74 px. Filtering is **Point**.

This is deliberate: asking a generator for low resolution produces a different fake pixel grid
every time, whereas a deterministic reduction treats every asset identically however far apart
they were generated.

⚠️ Sheets imported before 2026-08-04 were sized against the old 1.35-unit adult and landed near
65 px. The reduction is per-import, so **they are not re-scaled** — the project holds both.

## Things learned the hard way, encoded in the tool

Do not undo these to simplify the code. Each cost a wasted generation cycle.

- **Chroma key globally, and unmix the edges.** Generators are unreliable at emitting real alpha
  and reliable at putting a subject on a plain backdrop, so the contract asks for flat magenta
  `#FF00FF`. A threshold alone is not enough: anti-aliased edges are a blend of backdrop and
  subject, and once averaged down they dominate thin structures — a bike arrived with magenta
  spokes. Partial pixels are unmixed via `P = a·S + (1−a)·K`. Keying is **global, not
  flood-filled from the border**, so backdrop trapped inside the subject goes too.
- **Trim in the tool, never in the prompt.** Sizing derives from full image height, so untrimmed
  art silently renders small.
- **Reduction is area-averaged**, not nearest-neighbour — point-sampling a photograph down to
  65 px is aliased noise. Colour is weighted by alpha through the average, or edges get a dark
  halo.
- **Sheets are never trimmed** — it would shift every cell off the grid.
- **Sheets are checked for a shared baseline.** A figure that drifts up its cell between frames
  bobs in motion while looking fine frame by frame. Refused above 2 px at final size.
- **Sheets of one subject are checked against each other.** Each can be internally perfect and
  still disagree — a walk drawn near edge-on was 47 px wide against the idle sheet's 122. Refused
  above 1.4× on width or 1.15× on height.
- ⚠️ **Never wrap the import loop in `AssetDatabase.StartAssetEditing`.** It defers `ImportAsset`,
  so `AssetImporter.GetAtPath` returns null for a file just written, every import setting is
  skipped, and assets land with Unity's defaults — no slices, no clips, no controller — **while
  appearing to succeed.** This cost a full round trip once already.

**The importer archives what it accepts.** A clean pair moves to `art_incoming/processed/`;
anything that reported a problem stays in `art_incoming/` so the next run shows only what is still
wrong. `rejected/` is a hand-sorted pile. Neither subfolder is read by the importer, which only
ever looks at the top level.

## Actor sprite sizing — two traps that cost a cycle each

- **Resize an actor with `WorldActorVisual.Height`, never by scaling its `ActorVisual` child.**
  `ApplyVisual` positions that child at `Height / 2` — the sprite's centre — assuming its scale is
  1. Scaling it grows the sprite about that centre and buries the feet below the floor.
  `GroundOffset` is for the small art-dependent nudge, not for resizing.
- **`FitScaleToHeight` refits in `LateUpdate` whenever the displayed sprite changes, and must keep
  doing so.** It divides the target height by the sprite's *bounds*, and an Animator swaps
  `m_Sprite` for frames whose pixel size and import PPU differ from whatever `ActorSprite` holds.
  Fitting once at Awake against a stale 48 px @ PPU 100 placeholder, then animating 65 px @ PPU 48
  frames, rendered the player at 4.5 units instead of 1.6 with the bottom 1.46 units underground.
  The giveaway is that it looks correct the instant any Inspector field is touched, because
  `OnValidate` refits against the sprite actually showing. It is a reference compare per frame.

`FitScaleToHeight` applies `Height / spriteBounds` uniformly as `(scale, scale, 1)`, so **`Height`
alone is the X and Y size**; `Width` is only a fallback when there is no sprite at all.

⚠️ **Death sheets shrink in figure height as the body goes prone.** Since the refit is per
displayed frame, verify in-editor that a prone corpse frame does not scale *up* to the target world
height and balloon.

## Current actor heights

| Actor | Height |
|---|---|
| Player | 1.8 |
| Adult NPC (`EKVibe.CharacterHeight`, and `NpcHeight: 0` inherits it) | 1.55 |
| Child | 1.3 |

`EnemyAI.Awake` takes `WorldActorVisual.Height` for the NavMesh agent and otherwise leaves the
prefab's authored value alone. It used to hardcode `1.35f`, so a taller enemy pathed as a 1.35
agent under its real collider. Agent **radius** stays a uniform `0.28` on purpose — a wider agent
gets stuck in doorways, and London now has buildings.

## Animator controllers

The generated controller defines `Speed`, `MeleeAttack`, `Hit`, `Death`, `CastSpell` and a
`Cycling` bool. `Cycling` would hold a `Cycle` state while riding, but **no `cycle` sheet is
requested any more**, so no controller has that state and the parameter is never created.

**The Animator goes on `ActorVisual/SwingRoot`** — the same GameObject as the `SpriteRenderer` —
because the importer binds every clip with an **empty path**. One level up and the clips animate
nothing while looking perfectly well wired in the Inspector. `WorldActorVisual.AttachAnimator` owns
that, and both the editor and the game call it.

### `BuildController` reasons about the controller, not the batch

This was a bug once and the shape of the fix is load-bearing. Attack, cast and death imported
perfectly — sheets sliced, clips built, states created, `PlayerAnimator` pointed at the controller
— and never played a frame, because all transition wiring sat inside an `idle != null` branch where
`idle` was only set if *this batch* contained an idle sheet.

Now: states are resolved with `FindState` over the whole state machine; `idle` falls back to
`FindState(sm, "Idle")` and then to `sm.defaultState`; every add is guarded by
`HasConditionalTransition` / `HasUnconditionalTransition`; and `RemoveDuplicateTransitions` clears
existing duplicates on each run. Death still gets no return transition.

`Editor/GeneratedEnemyPrefabTool.cs` builds the enemy controllers instead, and edits its prefabs in
place rather than deleting and re-saving them — the shape `ArtImportTool` uses. (The old
`EnemyPrefabSetup.cs` did delete and re-create its controller on every run; it was deleted with the
Orc and Bot Wheel subjects.)

⚠️ **A controller can exist, be wired, and still ignore a clip.** `murtaugh_Controller` holds only
an `Idle` state and never references the committed `sheet_char_murtaugh_walk` clip, so he slides
while roaming. `Tools/art_status.py` cannot see this — it reads filenames and GUIDs, not controller
contents.

## The procedural melee swing stands down where there is attack art

`PlayMeleeSwing` returns early when `HasAttackAnimation()` — `Animator.HasState(0, "Attack")` on
the `SwingRoot` animator. **Probe by state, not by the `MeleeAttack` parameter**: both
`ArtImportTool` and `GeneratedEnemyPrefabTool` declare that parameter unconditionally, so it says nothing
about whether art exists. `SetFacing` still runs first — it is what points the attack clip the
right way — and an in-flight swing is stopped and its pose cleared, since `NpcFactory` and
`MagicTutorial` can attach an Animator after the fact.

The procedural swing is **kept**, not deleted: it is still the only attack tell for an actor
without art (the four police tiers above PCSO have no Animator at all). `SwingAngle` /
`SwingDuration` / `LungeDistance` stay as public serialized fields.

What it looked like, for anyone tempted to reuse it: `ApplySwingPose` rotates
`ActorVisual/SwingRoot` by up to 55° and lunges it, and `SpawnSlashArc` builds a quad on an
**`Unlit/Color`** material — that shader ignores alpha, so the intended translucent cream renders
as an opaque near-white block and the alpha ramp fades nothing.

The player's attack window and its clip line up exactly: `MeleeHitDelay 0.15` + `MeleeRecovery 0.35`
= 0.50 s, and the clip is 6 frames @ 12 fps = 0.50 s, `loop: false`. Damage lands on frame 2.
**Changing either number desynchronises them.**

## What gets auto-assigned

The five player-class subjects are reserved and never wired into NPC presets: `player` maps to
Young Driller, followed by `player_stabmeister`, `player_mrhood`, `player_dynamo`, and
`player_bundabasher`. Import refreshes `PlayerClassVisualLibrary` in the open `Assets/c.unity`.
An idle sheet enables the creator preview; gameplay uses a class only when idle, walk, attack,
hurt, death, and cast all exist, otherwise the entire Young Driller profile is used.

The importer also assigns the e-bike and NPC subjects named by a preset's `ArtSubject`. The police tiers and the pub are hand-built prefabs
with `PlaceholderBody` primitives and no `SpriteRenderer`, so their art will import and land
nowhere until someone gives them presets or wires the prefabs by hand.

`Assets/Sprites/Enemies` is old craftpix content: 64×64 pixel art at PPU 100 with **bilinear**
filtering, which is why it looks mushy. It predates all of this and is not the reference style.
