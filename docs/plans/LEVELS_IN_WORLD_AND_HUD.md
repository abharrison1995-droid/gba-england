# Implementation plan — authorable enemy levels, combat-gated nameplates, a bigger HUD cluster

**Status: plan only, nothing implemented.** Three related pieces of work, independent enough to
land separately but sharing one verification pass in the editor.

```
Grounded against: main @ 5ce3223, working tree 2026-08-08 (UI files modified but uncommitted).
Verification:     every claim carries the file and line it was read at. There is no C# compiler,
                  no Unity and no test framework here — see §10.
```

---

## 1. Scope

**In**

1. A level on `PlacementPreset`'s enemy recipe, attached as an `EnemyLevel` component by the
   placement path, plus a per-placement override in the World Palette itself.
2. Combat-gated nameplates for **enemies**, and a level badge on the **player's** floating bar.
3. A runtime scale for the top-left HUD cluster, driven by one `EKVibe` constant.

**Out**

- NPC and civilian nameplates. Owner's decision, and they carry no `EnemyNameplate` today anyway.
- Deciding any actual level values. This work makes levels authorable; authoring them is an owner
  editor pass (§10.3).
- Adding `EnemyLevel` to the six `Enemy_*.prefab` or the five `Police_*.prefab` assets. That would
  put a level on eleven prefabs whose levels nobody has chosen, which is the exact class of silent
  change `PROGRESSION_SYSTEM.md` chose option A to avoid.
- Any scene edit. All three items are code-only.
- Loot bands, perks, XP curve retuning. Phases 1-3 are merged and are not reopened.

**No new scripts.** Every change is an edit to a file that already exists, so no new `.meta` is
minted and the CLAUDE.md §3 GUID hazard does not apply to this work at all.

---

## 2. What was verified, and three things the briefs get wrong

### Confirmed

| Claim | Verified at |
|---|---|
| Nothing anywhere adds `EnemyLevel` | grep for `EnemyLevel` over `Assets/**/*.cs`: the only mentions are its own file, `Health.cs:34`, `KillXP.cs:43`, `EnemyNameplate.cs:77` and three comments |
| The enemy recipe has `OverrideHealth`/`Health`, `OverrideDamage`/`Damage`, `Loot` and no level | `Assets/Scripts/Data/PlacementPreset.cs:88-98` |
| The palette funnels every placement through one call | `Assets/Editor/WorldPaletteWindow.cs:357` is the only `PlacementBuilders.Build` call site in the repo |
| Both enemy build paths share one override method | `PlacementBuilders.cs:59` (prefab path) and `:99` (recipe path) both call `ApplyEnemyOverrides` at `:104-131` |
| `EnemyLevel.ApplyTo` scales `Health.MaxHealth` from whatever the prefab carries, and is inert at level 1 or less | `Assets/Scripts/Combat/EnemyLevel.cs:32-55` |
| It is called from `Health.Awake` above `CurrentHealth = MaxHealth` | `Assets/Scripts/Combat/Health.cs:29-36` |
| `EnemyNameplate` builds in `Awake` unconditionally and runs a full `LateUpdate` every frame | `Assets/Scripts/World/EnemyNameplate.cs:25-29`, `:31-54` |
| `Build()` reads `EnemyLevel` once and never refreshes | `EnemyNameplate.cs:77-80` |
| `PlayerHealthBar` shows on damage and hides on a `_hideAt` timer | `Assets/Scripts/World/PlayerHealthBar.cs:23-31, 44-59` |
| `UIManager` already does runtime fixups of scene UI | `RestyleSceneHudButtons` `UIManager.cs:87-109`, `EnsureDedicatedTrack` `:213-239` |
| `EnsureDedicatedTrack` exists because `ConcealmentBar`'s parent is the shared cluster | `UIManager.cs:196-212`; the scene confirms it — `ConcealmentBar` (GO 757388521) has parent `TopLeftPortraits`, which has four children |
| The player's two damage sites | `Assets/Scripts/Combat/CombatController.cs:540` (melee) and `:738` (spell), both already passing `gameObject` |

### Corrections

**(a) There are 32 `PlacementPreset` assets, not ~30, and only six are enemies.**
`Assets/Data/Presets/*.asset` = 32 files; `Category: 1` appears in six: `Preset_Neek`, `Preset_OG`,
`Preset_Roadman`, `Preset_Spicehead`, `Preset_Tainted`, `Preset_TorturedNeek`. The blast radius of
the appended field is 32 assets read, 6 that matter.

**(b) An appended field on these assets does not necessarily read back 0.**
`Preset_Neek.asset` has no `PickpocketBand` key at all — appended fields are simply absent from the
YAML, and Unity constructs the object (running C# field initialisers) before applying the keys that
are present. `PlacementPreset.cs:169-173` and `:193-197` both assert exactly this, and the
`Region: 0` / `PickpocketMinGold: 5` shape of the existing assets is consistent with it. **I cannot
prove it here** — it needs Unity. The design in §4 is deliberately correct under either reading,
which is the safe answer to the question the brief asked.

**(c) No enemy is placed anywhere in the game.**
A GUID scan of all six `Assets/Prefabs/Enemies/*.prefab.meta` GUIDs across
`Assets/Prefabs/Chunks/*.prefab` and `Assets/c.unity` returns zero hits. The only `EnemyAI` in the
scene is the `PCSO` actor (GO 2022723104). So:

- "whether existing placed instances in chunk prefabs need anything" — **there are none**. Nothing
  to migrate; no chunk prefab is touched by this work.
- It also explains why the Phase 2 gap is total rather than partial: there is no authored enemy in
  the world to have been given a level.
- `docs/reference/WORLD_AUTHORING_AND_NPCS.md` should say this. Its header already flags that the
  six London enemy prefabs have never been seen in play; it does not say they are unplaced.

### One live bug found in passing

`Assets/Scripts/Flow/TutorialSequence.cs:173-174`:

```csharp
var plate = bandit.AddComponent<EnemyNameplate>();
plate.Level = 1;
```

`AddComponent` runs `Awake` synchronously, and `EnemyNameplate.Awake` calls `Build()`
(`EnemyNameplate.cs:25-29`), which renders the badge text from `Level` at `:80`. The assignment on
the next line lands **after** the badge has already been drawn with the field default of **3**, so
the tutorial bandit shows a "3". `BanditPracticeSpawner.cs:76` and `ModernBritainSetup.cs:141` do
the same thing but are editor tools, where `Awake` does not run, so they are correct.

**The lazy build in §5.2.2 fixes this for free** — building on first show means the assignment
always precedes the render. No separate fix needed; say so in the commit message so it is not
rediscovered later as a regression.

---

## 3. Mapping table — serialized fields, save keys, enums

**No renames. No insertions. No enum changes. No save-key values touched. Every row is an append or
a non-serialized addition.**

| # | Change | Kind | Files holding data | Blast radius if got wrong |
|---|---|---|---|---|
| 1 | `PlacementPreset.EnemyLevel` (`int`, initialiser `0`), appended at the very end of the class, after `PickpocketBand` | new serialized field on a ScriptableObject | 32 `Assets/Data/Presets/*.asset` (key absent in all of them) | Absent gives 0, which §4.1 defines as "attach nothing" — today's behaviour exactly. If it were ever **renamed**, every authored level silently reverts to no component; it would need `[FormerlySerializedAs]`, as `PickpocketMinPounds` already carries (`PlacementPreset.cs:182`) |
| 2 | `EnemyLevel` component attached at placement time | new component on a prefab instance inside a chunk prefab | none yet | Saved as an added-component override in the chunk prefab. If an enemy prefab later gains its own `EnemyLevel`, an instance could carry two — guard with `GetComponent ?? AddComponent` (§5.1.2) |
| 3 | `EnemyAI.HasAggro` | get-only property, not serialized | none | None |
| 4 | `EnemyNameplate` internal state (`_hideAt`, `_built`, `_ai`) | private | none | None. `public int Level` and `public float HeightOffset` are untouched — 11 prefabs and `c.unity` store them |
| 5 | `PlayerHealthBar` gains private fields and one public `Ping()` | not serialized | `c.unity` (component on `Player`, GO 861987723) | None. No public field renamed, so the scene's `HeightOffset` and `VisibleDuration` survive |
| 6 | `EKVibe.HudClusterScale` (`const float`) | compile-time constant | none | None |
| 7 | `MapChunkData.ChunkName`, `ItemData.ItemID`, `PerkData.PerkId`, `WikiEntryData.EntryID`, `SaveData.*` | untouched | — | — |

`savegame.json` is not read or written differently by any of this. The player's level still derives
from `PlayerSession.TotalXP`; enemy levels are authored data and are never saved.

---

## 4. Work item 1 — the design decisions, stated plainly

### 4.1 What 0 means: no component at all

`public int EnemyLevel = 0;` with a tooltip that spells out:

> 0 leaves the enemy exactly as its prefab authors it — no `EnemyLevel` component is added at all.
> 1 or more attaches one at that level; the prefab's Health and Damage are the level-1 baseline.

Why this rather than "0 means level 1":

- It is correct whether or not the field initialiser survives a missing YAML key (§2b). Under both
  readings, a preset authored before today places what it places today.
- Attaching a level-1 `EnemyLevel` would **not** be inert, despite `ApplyTo` returning early at
  `EnemyLevel.cs:42`. Two things change: `EnemyNameplate.Build` starts reading the component
  (`:77-80`), so every badge flips from the prefab's authored "3" to "1"; and `KillXP` switches from
  `EKVibe.KillXPBase` to `ScaledKillXP(level.BaseXP, 1)` (`KillXP.cs:43-46`). Those are the same
  number today, but the coupling is real and buys nothing.
- The distinction is visible to the author: the component is either on the placed object or it is
  not, which is exactly what the Inspector shows.

The cost is that "level 1" and "unlevelled" cannot be told apart in the preset. They are the same
thing behaviourally, so nothing is lost.

### 4.2 Order of operations with OverrideHealth / OverrideDamage

**The override wins first, then the level multiplies it.** Concretely:

1. `ApplyEnemyOverrides` runs in the **editor**, at placement time, and bakes
   `health.MaxHealth = preset.Health` into the placed instance (`PlacementBuilders.cs:108-122`).
2. `EnemyLevel.ApplyTo` runs at **runtime**, in `Health.Awake`, and multiplies whatever `MaxHealth`
   the instance carries (`EnemyLevel.cs:45`).

A preset with `OverrideHealth = 100` and `EnemyLevel = 5` therefore yields
`ScaledHealth(100, 5) = 100 * (1 + 0.35*4) = 240` at runtime. **The override is the level-1
baseline.** That is the only order that composes: scaling first and overriding second would make
the override silently cancel the level, which is the worse failure because it is invisible.

This needs **no ordering code**. It falls out of one running in the editor and the other at runtime.
What it needs is documentation, because the Inspector will read `MaxHealth: 100` on an enemy that
has 240 HP in play. Put that sentence in three places: the `EnemyLevel` tooltip on `PlacementPreset`,
the `Level` tooltip on `EnemyLevel` itself, and `docs/reference/WORLD_AUTHORING_AND_NPCS.md`.

### 4.3 Where the level is actually chosen — flagged for the owner

**The brief's design (level on the preset) does not on its own deliver the stated goal.** The goal is
"the same enemy type appearing at different strengths in different chunks". A preset is a single
asset, and `WorldPaletteWindow.Refresh` (`:63-73`) lists them all — so a level that lives only on
the preset means either one preset per level band (`Preset_Roadman_Lv2`, `_Lv6`, ... six enemies by
three bands is 18 new assets) or editing the preset asset between placements, which is a hidden mode
switch nobody will remember they are in.

**Recommendation: keep the preset field as the default, and add a transient level field to the
palette itself.** Editor-only, stored on the `EditorWindow` and therefore in no asset, drawn only
when the armed preset is `Category.Enemy`, initialised from the preset each time one is armed. Stamp
five Lv2 Roadmen in Alvaston, retype 6, stamp five more in London. That is about fifteen lines in
`WorldPaletteWindow.cs` and one optional parameter on `PlacementBuilders.Build`.

If the owner would rather have only one place a level can come from, drop commit 3; the preset field
alone still works, it is just slower to author with.

---

## 5. File-by-file change list

### Work item 1 — authorable levels

#### 5.1.1 `Assets/Scripts/Data/PlacementPreset.cs` — append only

At the very **end** of the class, after `PickpocketBand` (`:212`), a new commented block in the house
style of the four blocks above it, explaining that it is appended for the same reason they were:

```
// ── Enemy — level ───────────────────────────────────────────────────────────────────
[Header("Enemy — level")]
public int EnemyLevel = 0;
```

Tooltip: the two paragraphs from §4.1 and §4.2. Do **not** move it up beside the enemy recipe at
`:88-98` — appending is this file's own stated convention, and the Inspector groups by header anyway.

⚠ The field name `EnemyLevel` collides with the type name `ExiledAlvaston.Combat.EnemyLevel` inside
`PlacementBuilders.cs`, which has `using ExiledAlvaston.Combat;` (`:5`). This compiles — member
access and type lookup are separate — but the implementer must not name a local variable
`EnemyLevel` in that method. If the reviewer finds it too clever, `EnemyLevelToPlace` is the escape
hatch; decide **before commit 1**, because changing it afterwards is a serialized-field rename.

#### 5.1.2 `Assets/Editor/PlacementBuilders.cs`

In `ApplyEnemyOverrides` (`:104-131`), after the damage block and before the loot block:

- return early when the level is below 1;
- require an `EnemyAI` on the instance before attaching anything. Two reasons: scaling `Damage` is
  meaningless without one, and `ApplyEnemyOverrides` is also called from `BuildFromPrefab` (`:59`)
  for **every** category — a chest or NPC preset with a stray level would otherwise get an
  `EnemyLevel`, whose `[RequireComponent(typeof(Health))]` (`EnemyLevel.cs:14`) would silently add a
  `Health` to a chest. Log a warning naming the preset when a level is set and no `EnemyAI` is found,
  rather than failing quietly;
- `GetComponent<EnemyLevel>() ?? AddComponent<EnemyLevel>()`, then set `Level`. Never a bare
  `AddComponent`: Unity permits duplicate components without `[DisallowMultipleComponent]`, and two
  `EnemyLevel`s would both run `ApplyTo` and compound the scale (`_applied` is per component,
  `EnemyLevel.cs:24`);
- leave `BaseXP` alone. Its initialiser is `EKVibe.KillXPBase` (`EnemyLevel.cs:22`), and
  `AddComponent` runs initialisers.

Plain `AddComponent`, not `Undo.AddComponent`, matching the `LootOnDeath` line immediately below
(`:128`) — the whole instance is already undo-registered at `:221`, so undo removes the object.

#### 5.1.3 `WorldPaletteWindow.cs` and the `Build` signature (optional, recommended — §4.3)

- `PlacementBuilders.Build(preset, position, parent, int enemyLevelOverride = -1)` as a **default
  parameter**, so the existing call shape still compiles and -1 means "use the preset's value".
  Thread it into `ApplyEnemyOverrides` as an extra argument.
- In `WorldPaletteWindow`, a `private int _enemyLevel;` drawn as an `IntField` in `OnGUI` only when
  `_armed != null && _armed.Category == Enemy`, reset to `_armed.EnemyLevel` at the moment a preset
  is armed, so it never silently carries a level over from the last enemy stamped. Pass it at `:357`.
- Clamp typed input to 0 or more, so -1 cannot be entered and read as "use the preset".

#### 5.1.4 `Assets/Editor/EnemyPlacementTool.cs` — parity

The legacy `Tools/GBH/Place/Enemy Placement` window duplicates the recipe by hand (`:111-127`). Add a
`_level` int beside the health/damage overrides and the same `GetComponent ?? AddComponent` block
after `:120`. Six lines. Without it the two placement paths disagree, which is the kind of thing
found six months later by someone wondering why their enemy is level 1.

#### 5.1.5 `Assets/Scripts/Combat/EnemyLevel.cs` — comment only

Its class summary says "Absent means level 1". Extend it to name the placement path now that one
exists, and to state the override-then-level ordering from §4.2. No code change.

### Work item 2 — combat-gated nameplates and a player level badge

#### 5.2.1 `Assets/Scripts/Combat/EnemyAI.cs` — expose aggro, push proximity

`_target` is private with no accessor (`:40`). Add `public bool HasAggro => _target != null;`.

`PerceptionRoutine` (`:124-153`) already ticks every 0.2 s and already computes the distance to the
player in `TryAcquireTarget` (`:160`). At the end of each tick, push both signals to the nameplate:
`_plate?.SetEngaged(_target != null || playerWithinSight)`. Cache the `EnemyNameplate` in `Awake`
via `GetComponent` — it may legitimately be null, since a hand-built enemy need not have one.

**Push at 5 Hz rather than polling per frame.** That is the whole mobile argument: nothing is added
to any `Update` or `LateUpdate`, and the routine this hangs off already exists and already does the
distance maths.

⚠ `PerceptionRoutine` is a `while(true)` coroutine on the enemy, so it dies with the object: no
unsubscribe, no static state, nothing to leak across a chunk transition. This is deliberately **not**
a static aggro counter — a counter has to be decremented in `OnDestroy`, and a chunk teardown that
destroys thirty aggroed enemies in one frame is precisely where such a counter drifts and never
recovers.

#### 5.2.2 `Assets/Scripts/World/EnemyNameplate.cs` — gate, and build lazily

1. **Do not build in `Awake`** (`:25-29`). Cache `_health` only, and move `Build()` behind a `_built`
   flag called from the first show. This saves five GameObjects, two `TextMeshPro`s and three
   material lookups for every enemy that never fights, and it fixes the `TutorialSequence` bug in §2.

2. **A `_hideAt` timer copied from `PlayerHealthBar`** (`PlayerHealthBar.cs:21, 44-59`) — same shape,
   same `VisibleDuration` field name so the two read alike. Entry points:
   - `SetEngaged(bool)`, pushed from `EnemyAI` at 5 Hz. True extends `_hideAt`; false does nothing,
     because the timer runs out on its own.
   - a `Health.OnTakeDamage` listener added in `Awake` and removed in `OnDestroy` — the pairing
     `EnemyAI.cs:51-55` / `:79-86` models it. This covers a hit from something that has no aggro,
     e.g. a spell from out of sight.
   - a `Health.OnDeath` listener that hides immediately, so a corpse lingering for
     `DestroyDelay = 1.2 s` (`Health.cs:17`) does not keep a plate over it.

   "Deals damage" needs no separate trigger for enemies: an `EnemyAI` cannot swing without a
   `_target` (`EnemyAI.cs:105, 231`), so aggro strictly precedes it.

3. **`LateUpdate` returns immediately when hidden.** Its first statement becomes a check of
   `_root == null || !_root.gameObject.activeSelf` — one bool — after which the existing body runs
   unchanged. **This makes the hot path cheaper than it is today**, not more expensive: an idle
   enemy currently pays a `Camera.main` lookup, a position write, a rotation write, a string compare
   and a health division every frame (`:31-54`). Hidden, it pays one bool.

   The timer itself goes in `Update` as a single `Time.time >= _hideAt` compare while visible,
   exactly as `PlayerHealthBar.Update` does (`:55-59`).

Hide the **root**, not the component: `_root` is a scene-root GameObject created with
`new GameObject("Nameplate")` and never parented (`:58`), so `SetActive(false)` on it touches nothing
else. This is not the CLAUDE.md §3 prohibition — that covers chunk roots and vehicle roots, both of
which have `OnDisable` behaviour that breaks. A plate quad has none.

`Level` and `HeightOffset` stay public and keep their values on all eleven prefabs. The level read at
`:77-80` stays exactly as it is: an enemy's level does not change at runtime, and building lazily
means it is read later, not more often.

#### 5.2.3 `Assets/Scripts/World/PlayerHealthBar.cs` — the level badge

- `Build()` (`:79-100`) gains a level badge modelled on `EnemyNameplate.Build`'s (`:65-80`): a Quad
  in `EKVibe.LevelBadge` with its collider destroyed, and a `TextMeshPro` child in `EKVibe.TextDark`.
  Offset it to the left of the track so it never covers the fill. `EnemyNameplate.CreateTmp` is
  private and static in another class — copy the six lines rather than making it public. Two
  billboards with slightly different needs are not worth a shared helper, and `PlayerHealthBar`
  already duplicates `SetUnlit` for the same reason (`:105-121`).

- ⚠ **The player's level changes at runtime, so the badge must refresh.** Cache
  `private int _shownLevel = -1;` and, in `LateUpdate` **after** the existing `!activeSelf` early
  return (`:63`), compare `PlayerSession.Instance?.Level` to it and rewrite the text only on a
  change. This is the pattern `UIManager` already uses for the HUD badge (`UIManager.cs:112-130`),
  and its comment explains why: `level.ToString()` allocates, so an unconditional per-frame write is
  a mobile-hot-path allocation. Behind the `activeSelf` return it costs nothing while hidden.

  Do **not** subscribe to `PlayerSession.OnLevelUp`. Polling avoids binding to a `DontDestroyOnLoad`
  singleton that may not exist when `Awake` runs, and avoids an unsubscribe that, if missed, keeps a
  destroyed bar receiving events across a reload.

- `public void Ping()` — sets `_hideAt = Time.time + VisibleDuration` and activates the root, i.e.
  the body of `OnDamaged` (`:44-48`) extracted; `OnDamaged` then calls it.

#### 5.2.4 `Assets/Scripts/Combat/CombatController.cs` — the player deals damage

Cache `private PlayerHealthBar _bar;` in `Awake` via `GetComponent` — the component is on the
`Player` GameObject in `c.unity` (GO 861987723, verified by GUID `6e020ae1...`). Call `_bar?.Ping()`
at the two sites that already attribute damage: `:540` (melee) and `:738` (spell). Two lines.

⚠ Not `FindObjectOfType` per hit, and not a static. `GetComponent` in `Awake` is what `EnemyAI` does
for its own `Health` and `WorldActorVisual` (`EnemyAI.cs:47-49`).

#### 5.2.5 Aggro for the player's bar — the cheapest safe option

The owner's trigger list includes "an `EnemyAI` has aggro on the player". For an enemy's own plate
that is local state. For the player's bar it is a global question, and the two obvious answers are a
static counter (leaks on chunk teardown — §5.2.1) or a scan (allocates, and runs on the player every
frame).

**Use the push that already exists.** In the same 0.2 s `PerceptionRoutine` tick, when `_target` is
the player, call `CombatController.Instance?.PingHealthBar()` — a one-line pass-through to `_bar`.
Five calls a second per aggroed enemy, none per frame, no static, nothing to unwind. The bar then
stays up for the whole fight and fades `VisibleDuration` after the last enemy loses interest.

#### 5.2.6 One objection to the owner's decision, stated rather than implemented around

**Combat-gating hides the enemy's level exactly when the player needs it: before choosing to fight.**
The point of `PROGRESSION_SYSTEM.md`'s enemy levels is that a Lv6 Roadman in London is not a Lv2
Roadman in Alvaston, and Exiled Kingdoms — the presentation model this project follows — shows plates
always, so a fight can be judged before it starts. Gating strictly on damage-or-aggro means the level
is learned from the first hit.

That is why §5.2.1 pushes `_target != null || player within SightRadius` rather than aggro alone. It
costs nothing (the distance is already computed at `EnemyAI.cs:160`) and the plate appears as you
approach — before contact, but only for enemies actually near you.

**Owner decision 2026-08-08: keep the sight-radius term.** The plate shows on aggro *or* when the
player is within `SightRadius`, so a fight can be judged before it is taken. This reverses the
earlier "damaged or aggroed" answer deliberately. Dropping the second term later is a one-word
change if it proves too noisy in play.

### Work item 3 — the HUD cluster

#### 5.3.1 What the scene actually contains (read from `c.unity`)

| Object | Anchor | Pivot | Anchored pos | Size |
|---|---|---|---|---|
| `TopLeftPortraits` (the `TopLeftPortraitPanel` field) | (0,1) | (0,1) | 16, -16 | 390 x 116 |
| `PlayerPortrait` | (0,1) | (0,1) | 6, -6 | 96 x 96 |
| `HPTrack` | (0,1) | (0.5,0.5) | 244, -22 | 260 x 28 |
| `MPTrack` | (0,1) | (0.5,0.5) | 244, -58 | 260 x 28 |
| `ConcealmentBar` | (0,1) | (0.5,0.5) | 244, -86 | 260 x 28 |
| `CombatLog` | (0.5,1) | (0.5,0.5) | 0, -12 | 520 x 100 |

`UICanvas` `CanvasScaler`: Scale With Screen Size, reference **1920 x 1080**, match **0.5**.
`LevelBadge` / `LevelText` are children of `PlayerPortrait` (28 x 28 at 4,4), so the HUD level badge
scales with the cluster automatically.

Three things the brief did not know:

- **`ConcealmentBar` has a stray child GameObject named `MPFill`** (GO 870412552, stretched
  0,0-1,1) — a copy-paste leftover from the mana bar. `PlayerConcealmentFill` points at
  `ConcealmentBar` itself, so once `EnsureDedicatedTrack` wraps it, that stray child shrinks with the
  fill and renders as a solid overlay on it. Cosmetic, pre-existing, **out of scope** — but worth
  deleting while the owner is in there (§10.3).
- **There is no `SafeAreaFitter` anywhere in the HUD.** The only two `SafeArea` objects in `c.unity`
  sit under `GeneratedTitleLayout` and `GeneratedCharacterCreator`. The gameplay HUD has never been
  safe-area aware.
- The cluster's left edge is x = 16; `CombatLog`'s left edge is 1920/2 - 260 = **700**.

#### 5.3.2 The mechanism: one localScale on the panel

In `UIManager.Start` (`:75-80`), after `RestyleSceneHudButtons()`, a new `ScaleHudCluster()`:

```
if (TopLeftPortraitPanel != null)
    TopLeftPortraitPanel.localScale = Vector3.one * EKVibe.HudClusterScale;
```

Why this and not the alternatives:

- **Scale the panel, not the elements.** The four children are positioned with absolute
  `anchoredPosition` inside the panel, so scaling the panel preserves the authored layout exactly.
  Resizing each element individually would mean re-deriving every offset, and would fight
  `EnsureDedicatedTrack`.
- **`localScale` touches no anchor, pivot or `sizeDelta`**, so it cannot interact with
  `EnsureDedicatedTrack` (`UIManager.cs:213-239`), which copies `anchorMin/Max`, `pivot`,
  `anchoredPosition` and `sizeDelta` between rects — every one of them independent of ancestor
  scale. That is the specific hazard the brief asked about, and the answer is that this approach
  cannot trip it. ⚠ It only holds because we scale the **panel**, never a track or a fill.
- **The panel's pivot is (0,1) with an anchor at (0,1)**, so it grows right and down from the
  screen's top-left corner. The corner does not move, so its safe-area exposure is unchanged.
- **Assign, never multiply.** `localScale = one * k`, not `*= k`. If anything ever runs it twice — a
  HUD rebuild, a second `UIManager` — an assignment is idempotent and a multiply is not, and a
  cluster at 2.56x would be a baffling bug report.
- TMP is SDF, so scaled text stays crisp. The portrait is an `Image` and will soften if its source
  sprite is small; flag it in §10.3 as something to look at, not a blocker.

Not chosen: lowering the `CanvasScaler` reference resolution (it would scale the action buttons too,
and those are already sized for a thumb at 100-130 px); a new editor tool (owner said no); a scene
edit (owner said no).

#### 5.3.3 `Assets/Scripts/Vibe/EKVibe.cs` — the constant and its derivation

Add to the mobile-HUD group near `JoystickRadius` (`:51-54`):

```
public const float HudClusterScale = 1.6f;
```

**Where 1.6 comes from — two bounds, and it sits between them.**

*Upper bound, hard:* the cluster must not reach `CombatLog`. Its right edge is `16 + 390 * k`, and
`CombatLog`'s left edge is 700, so `k < (700 - 16) / 390 = 1.754`. At 1.6 the right edge is 640 — a
60 px margin at the reference resolution.

*Lower bound, legibility:* the rest of the HUD is the in-project reference for "sized for a phone",
and it is all built at 100-130 px with 20-26 pt labels (`UIManager.cs:520-540`). The cluster is not:
28 px bars with an 18 pt readout (`EnsureBarLabel`, `:265`). At 1.6 the bars become 44.8 px, the
readout 28.8 pt — level with the action-button labels — and the portrait 153.6 px, level with the
130 px ATK button. That is the derivation: **parity with the HUD's own already-mobile-sized controls,
capped by the combat log.**

Height check: the cluster grows 116 -> 186 px from the top. `LocationTime` is anchored bottom-left at
y = 290 (790 from the top) and `QuestTracker` is top-right. Nothing sits under it.

⚠ Anything above ~1.75 also requires moving `CombatLog`, which is a scene edit and out of scope. Put
that number in the constant's comment so the next person raising it knows where the wall is.

#### 5.3.4 Safe area — a separate, optional commit

The cluster sits 16 px from the left edge. On a notched phone held in landscape that is exactly where
the notch or the rounded corner lands, and iOS reports up to 44 pt (about 130 px at this reference)
of inset. Growing the cluster does not make this worse — the corner does not move — but it does make
the thing being clipped more important.

`SafeAreaFitter` (`Assets/Scripts/UI/SafeAreaFitter.cs`) is a drop-in: it sets `anchorMin/Max` to the
safe-area fractions and zeroes both offsets (`:44-47`), and `HUDPanel` is already a full stretch with
zero offsets and zero `anchoredPosition`. So, in `UIManager.Start`:

```
Transform hud = FindChildRecursive(transform, "HUDPanel");
if (hud != null && hud.GetComponent<SafeAreaFitter>() == null)
    hud.gameObject.AddComponent<SafeAreaFitter>();
```

⚠ This moves the **whole** HUD, including the runtime-built `ActionButtons` (`:511-518`) and the
joystick. That is wanted — the bottom-right buttons are as exposed to a home indicator as the cluster
is to a notch — but it is a bigger behavioural change than the rest of this work, and it is invisible
in a 16:9 Game view. It must be its own commit that can be reverted alone. It is also the one change
here that cannot be verified without the Device Simulator or a real phone (§10.3).

Recommend landing it; recommend landing it last.

---

## 6. Commits, in dependency order

Each is coherent alone and leaves nothing half-wired.

| # | Commit | Contents | Notes |
|---|---|---|---|
| 1 | Add an enemy level to the placement recipe | §5.1.1 | Serialized append. No behaviour — nothing reads it yet |
| 2 | Attach EnemyLevel when placing an enemy | §5.1.2 + §5.1.5 | The feature. Neutral for all 32 existing presets, which read 0 |
| 3 | Let the palette override an enemy's level per stamp | §5.1.3 | Optional, per §4.3. Editor-only |
| 4 | Give the legacy enemy window the same level field | §5.1.4 | Parity. Skip only if that window is about to be retired |
| 5 | Update the world-authoring reference | §9 | Presets, ordering, and the "no enemy is placed anywhere" correction |
| 6 | Publish enemy aggro and push it to the nameplate | §5.2.1 | Property plus a 5 Hz push. Nothing consumes it yet — inert |
| 7 | Show an enemy's nameplate only in combat | §5.2.2 | Depends on 6. Also fixes the tutorial "3" badge (§2) — say so in the message |
| 8 | Show the player's level on their health bar | §5.2.3 | Independent of 6 and 7 |
| 9 | Raise the player's bar when they deal damage or draw aggro | §5.2.4 + §5.2.5 | Depends on 8 for `Ping()` |
| 10 | Scale the top-left HUD cluster for mobile | §5.3.2 + §5.3.3 | Wholly independent of 1-9 |
| 11 | Keep the HUD inside the device safe area | §5.3.4 | Optional, last, revertible alone |

Commits 1-5 are work item 1, 6-9 item 2, 10-11 item 3. The three groups touch disjoint files, so
they can be reordered or split across branches freely.

---

## 7. Silent failure modes, and how the implementer avoids each

| # | Failure | Why it is silent | Guard |
|---|---|---|---|
| 1 | Every existing preset starts attaching a level-1 `EnemyLevel` | Nothing throws; badges quietly change from 3 to 1 and kill XP changes source | §4.1: below 1 means attach nothing; the initialiser is 0 |
| 2 | An appended field is assumed to read back its initialiser, and does not | Unverifiable here (§2b) | The design is correct under both readings: 0 and "absent" both mean attach nothing |
| 3 | A chest or NPC preset with a stray level silently gains a `Health` | `[RequireComponent]` adds it with no log; a chest with Health can then be "killed" | §5.1.2: require an `EnemyAI` before attaching, and warn if a level is set without one |
| 4 | Two `EnemyLevel`s on one instance, scaling compounded | `_applied` is per component, so both run; 1.35 squared, nothing logged | §5.1.2: `GetComponent ?? AddComponent` |
| 5 | The override cancels the level, or the reverse | A designer sets Health 100 and Level 5 and gets 100 | §4.2: the editor-then-runtime ordering is inherent; document it in three places so nobody "fixes" it |
| 6 | The palette carries a level over from the last enemy stamped | You place ten Lv6 Neeks meaning to place Lv1 | §5.1.3: reset the field to the preset's value on arming |
| 7 | A nameplate never appears again | Gating with a trigger left unwired reads as "nameplates are broken" | Three independent triggers (§5.2.2), and commit 6 lands before 7 |
| 8 | A plate hangs over a corpse, or over nothing after a chunk change | `_root` is a scene-root object (`EnemyNameplate.cs:58`), so it does not die with a parent | The `OnDeath` listener hides it; `OnDestroy` (`:102-106`) already destroys `_root` |
| 9 | The `LateUpdate` gate is added but the body still runs | No visible symptom; the saving simply does not happen | Reviewer check: the `activeSelf` test must be the **first** statement, above the `_root.position` write |
| 10 | Per-frame `ToString()` on the player's level badge | Nothing fails; it allocates every frame on a mobile hot path, against CLAUDE.md §2 | §5.2.3: `_shownLevel` int compare, behind the `activeSelf` return |
| 11 | The level badge shows a stale level | `Build()` reads once (`EnemyNameplate.cs:77-80`); copying that shape to the player would freeze their level at first damage | §5.2.3 refresh. This is the one real difference between the two actors |
| 12 | A listener leak on `Health.OnTakeDamage` | A destroyed nameplate keeps receiving events | Add in `Awake`, remove in `OnDestroy`; `EnemyAI.cs:51-55` / `:79-86` models the pairing |
| 13 | The cluster scale is applied twice | 1.6 becomes 2.56; reads as a layout bug, not a double call | §5.3.2: assign, never multiply |
| 14 | The cluster grows into the combat log | Two overlapping panels, both semi-transparent | §5.3.3: 1.754 is the wall, 1.6 is the choice, and the number is in the comment |
| 15 | Rescaling a **track** instead of the panel | The concealment-bar bug all over again | §5.3.2: only `TopLeftPortraitPanel.localScale` is ever written. Reviewer should grep for any other `localScale` write in `UIManager` |
| 16 | `SafeAreaFitter` moves the HUD in a way nobody sees until a device build | A 16:9 editor Game view reports no inset | §5.3.4 is its own commit; §10.3 gives the Device Simulator route |

---

## 8. What is not changed, deliberately

- `EnemyNameplate.Level` and its default of 3 on eleven prefabs. Untouched, per option A.
- The six `Enemy_*.prefab` and five `Police_*.prefab` assets. No file under `Assets/Prefabs/` is
  edited by this plan.
- `Assets/c.unity`. No scene edit.
- `savegame.json` and every save key.
- `GeneratedEnemyPrefabTool` and `StarterPresetGenerator`. Both refuse to overwrite an existing
  preset (`GeneratedEnemyPrefabTool.cs:429-434`; `StarterPresetGenerator.cs:161` says so
  explicitly), so a re-run can never wipe an authored level.

---

## 9. Documentation changes (part of the work)

- **`docs/reference/WORLD_AUTHORING_AND_NPCS.md`** — owns the preset recipe and the palette. Add the
  enemy level field, the override-then-level ordering (§4.2), the palette's per-stamp override, and
  the correction that **no enemy prefab is placed in any chunk prefab or in `c.unity`** (§2c). Update
  its `Last verified against:` header, keeping the scope honest: code and tracked YAML read, nothing
  opened in Unity.
- **`docs/plans/PROGRESSION_SYSTEM.md`** — Phase 2 says "Level is set per placed instance in the
  Inspector". That is now one of two routes and no longer the expected one. Replace the sentence; do
  not annotate beside it (CLAUDE.md §7).
- **`docs/README.md`** — add this file to the active plans table.
- **CLAUDE.md §5 ledger** — add the §10.3 checks as entries, and delete each as it is confirmed.
  Nothing here adds a string save key, so §3 is untouched.
- **No** update to `SAVE_AND_SERIALIZATION.md`: nothing here changes the save format.

---

## 10. Verification

### 10.1 What can be proved in this environment

```bash
python Tools/asset_reachability.py --check-dangling   # before AND after; exit 0 is clean
```

Nothing here adds, deletes, moves or renames an asset, and no new script is created, so the result
must read **identically** before and after. A newly dangling GUID would mean something unexpected
touched an asset. On a machine without `Library/` the tool exits 2 — "couldn't verify", not a pass.

A brace/paren balance scan of the edited `.cs` files catches a truncated edit. **It is not a compile
and must not be reported as one.**

### 10.2 What cannot be proved here

Everything else. No C# compiler, no Unity, no test framework. Specifically unprovable:

- that the project builds;
- that a missing YAML key falls back to the C# field initialiser (§2b) — the design does not depend
  on it, but the claim itself stays unverified;
- every behaviour in §10.3;
- that 1.6 is the right scale on a real phone. It is derived (§5.3.3), not measured.

### 10.3 Owner checks in the editor, with routes

⚠ **Stop Play mode before any Inspector edit — changes made during Play are discarded.**

1. **It compiles.** Unity, wait for the recompile, then Window → General → Console → Clear, and
   confirm no red. Nothing below means anything until this passes.

2. **Existing presets are unchanged.** Project → `Assets/Data/Presets/` → select `Preset_Roadman` →
   Inspector. Under the new **Enemy — level** header, **Enemy Level** must read **0**. Then check
   further up that **Pickpocket Min/Max Pounds** still read **5 / 25** and **Health / Damage** read
   **45 / 7**. If any of those went to 0, the append disturbed the asset and the fix is
   `git checkout Assets/Data/Presets/`, not retyping 32 assets.

3. **Placing a levelled enemy.** Open a chunk prefab first: Project →
   `Assets/Prefabs/Chunks/South_Slums_Prefab.prefab` → double-click for Prefab Mode. Then Tools →
   GBH → World Palette, arm **Roadman**, set the palette's **Level** field to **5**, click in the
   Scene view, Ctrl+S. Hierarchy → select the placed Roadman → Inspector: it must carry an **Enemy
   Level** component reading **5**, and **Health → Max Health** must still read the prefab's **45**
   — the scale happens at runtime, not at placement (§4.2).

4. **It actually scales.** Play into that chunk. The Lv5 Roadman should take noticeably longer to
   kill than the prefab default (45 → 108 HP) and hit harder (7 → 14), and its badge should read
   **5**. ⚠ If it dies in the same number of hits, `ApplyTo` is not running — check that
   `Health.Awake` still calls it *above* `CurrentHealth = MaxHealth` (`Health.cs:29-36`).

5. **Level 0 stays inert.** Place a second Roadman with the palette's Level at **0**. It must have
   **no** `EnemyLevel` component at all, and its badge must read whatever the prefab's nameplate says
   — **3** on the six existing enemy prefabs, which is pre-existing display state, not a level.

6. **Nameplates are gated.** Play and walk toward that enemy. The plate should appear as you come
   within its sight radius, stay through the fight, and fade a few seconds after you break off. It
   must **not** be visible from across the chunk. Kill it: the plate must vanish at death, not linger
   over the corpse for the 1.2 s destroy delay.

7. **The tutorial badge.** Play the tutorial through to the cellar bandit. Its badge should now read
   **1**, not 3 — that is the §2 bug fixed by the lazy build. If it still reads 3, `Build()` is still
   running inside `Awake`.

8. **The player's badge tracks the real level.** Take a hit so the bar appears; the badge should show
   the same level as the bag readout. Then gain a level **while the bar is on screen** (kill
   something mid-fight) and confirm the number changes without the bar hiding and reappearing. That
   is the one thing `EnemyNameplate`'s build-once approach would have got wrong.

9. **The player's bar responds to dealing damage.** Attack a container or an enemy without being hit
   back. The bar should appear.

10. **The HUD cluster.** Play and look at the top left. The portrait, the three bars and their
    "current / max" readouts should be visibly larger and legible at arm's length. Check the right
    end of the bars does **not** touch the combat log at top-centre. Check the concealment bar is
    still its own 260-wide strip under the mana bar and has **not** stretched across the cluster —
    that is CLAUDE.md §5 ledger item 2, still unconfirmed, and this is a good moment to close it.

11. **While you are in there:** Hierarchy → `UICanvas / HUDPanel / TopLeftPortraits / ConcealmentBar`
    has a stray child called **MPFill** (§5.3.1). Delete it, Ctrl+S. Not part of this work, but it is
    a leftover rendering on top of the concealment fill.

12. **Safe area (commit 11 only).** Window → General → Device Simulator, choose a notched device
    (e.g. iPhone 14 Pro) in landscape. The whole HUD should inset away from the notch and the home
    indicator. In a plain 16:9 Game view nothing changes, which is expected and is **not** evidence
    that it works.

### 10.4 Known gaps

- The scale factor is derived from reference-resolution geometry and parity with the action buttons,
  not measured on a device. If it reads too small on a real phone, `EKVibe.HudClusterScale` is one
  number with a documented ceiling of 1.75.
- The interaction between a combat-gated plate and a chunk transition mid-fight is exercised by none
  of the checks above. `OnDestroy` already destroys `_root` (`EnemyNameplate.cs:102-106`), so it
  should be fine, but it is untested — leave it in the ledger.
