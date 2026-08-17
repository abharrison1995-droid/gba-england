# Vape Arc Build Guide — implementing the written quests

```
Last verified against: working tree, 2026-08-16 late (branch main, commit e63886a)
Verification scope:    PHASES 1a AND 2 ARE DONE. The art import ran and is confirmed good. The
                       owner has since placed all four arc buildings in London — the abandoned
                       church, Mosley's mansion, the Croyden Spartan traphouse and the bus station
                       — and play-tested combat alongside ALEX, the first companion, against a
                       placed Enemy_Spicehead. Several editor tool runs across 2026-08-16 prove
                       Assembly-CSharp compiles; nothing below is a behaviour claim.
                       STILL OWED, and all three block quest play:
                         1. Import Quests has NOT been re-run. Only 7 of the 9 QuestDefinitions
                            exist — gangbusters and ah_barnacles are missing — and
                            Preset_MadFisherman.Conversation is still {fileID: 0}.
                         2. The NavMesh is stale. Assets/c/NavMesh.asset predates all four
                            buildings and London has no RuntimeNavMeshBaker, so agents path
                            straight through them.
                         3. NO DungeonPortal EXISTS ANYWHERE (verified by script-GUID scan). All
                            four buildings are solid scenery. Nothing in the arc is enterable.
                       Verified present and correct by file inspection, not by play: all six
                       Collect items resolve; Mosley, Scrap Man, Daniel and the geezer have their
                       Conversation wired. Daniel is still NOT placed — only his spawn marker.
                       The five hand-authored interior shells have never been opened in Unity.
                       Phases 3, 5, 6, 7 remain unrun. Companion doc: the quest-script map.
```

The nine-quest arc — **Serendipity! → Chemical Castration Gone Wrong → Find the Magic Man →
Check Out the Church → Investigate the Weird Vape (pt 1 & 2) → WTF Mosley? → Gangbusters →
Ah, Barnacles** — is fully written in `quests/` and `quests/dialogue/`. The words are done. This is
the **content and wiring** that turns those text files into a playable chain, in the order it has to
happen.

## Four things that bite

1. **A silent import failure has already happened once.** When a preset's `Conversation` comes back
   `None` after an import, nothing is logged — read the Phase 1 note before assuming an import
   succeeded. Check the presets, not just the console.
2. **Don't re-run `Build Enemies From Generated Art` carelessly.** It rewrites every enemy prefab's
   YAML on its update path and would strip the geezer's hand-added components. Phase 7 needs one
   more run to build the Trap Branch Manager: do it on a clean tree, then immediately
   `git checkout -- Assets/Prefabs/Enemies/Enemy_UnderHoused.prefab`.
3. **Save keys are forever.** An `ItemID`, a quest id, a `QuestActor.Key` or a `ChunkName` that
   does not match *exactly* fails silently — the stage just never advances and nothing logs. Copy
   the strings from the reference tables below; don't retype from memory.
4. **A placement is a copy, not a link.** An NPC stamped into a chunk holds a *reference* to its
   dialogue asset (so re-importing that asset updates him), but every other preset field was baked
   in at stamp time. If in doubt after import, delete and re-stamp.

## The order

`0 Prep → 1 Import → 2 Geezer → 3 Place NPCs → 4 Locations → 5 Populate → 6 Play-test → 7 Quests
6-7.` Each phase depends on the one before it.

## Do these four first

Everything downstream assumes them. Exit Play mode and `Ctrl+S` before starting.

1. ~~`Tools → Art → Import Generated Art`~~ — ✅ **done**, 44 sheets at 86 px, walk cycle confirmed.
2. **`Tools → Content → Import Quests`** — the owed re-run, which also picks up quests 6 and 7.
3. **`Tools → World → Bake Navigation Mesh`** — see below.
4. **Wire the well** — phase 4, walkthrough included.

⚠️ **Why the bake.** `Home_London_Prefab` carries **no `RuntimeNavMeshBaker`**. Every interior shell
has one; **none of the six exteriors do** — they ride on the pre-baked `Assets/c/NavMesh.asset`.
**Four buildings** went into London on 2026-08-16 — mansion, church, traphouse, bus station — so that
NavMesh is badly stale and agents will path straight through all of them. Nothing warns you; enemies
and Alex simply walk through walls. Route: open `Assets/c.unity`, confirm the London chunk instance
is in the **Hierarchy**, then `Tools → World → Bake Navigation Mesh`. The console logs a vertex
count; *"produced no surface"* means the chunk is not loaded in the scene.

⚠️ **Item 3 is not optional before item 4.** A portal drops the player at an arrival marker, and
`MinMarkerClearance` is checked against the NavMesh — wiring doors onto a stale mesh means testing
travel against pathing that does not match the world you can see.

## Progress

| Phase | State | Where it stands |
|---|---|---|
| **0 — Prep** | ✅ **Done** (agent, 2026-08-15/16) | 5 `ItemData` assets authored, 2 quest keys set. Hand-authored YAML, unopened in Unity. |
| **1a — Art** | ✅ **Done** (owner, 2026-08-16) | 44 sheets at 86 px, all five class controllers on eight states. Walk cycle checked and good. |
| **1b — Quests** | 🔴 **STILL OWED — blocks everything** | Only 7 of 9 `QuestDefinition`s exist. **Gangbusters and Ah, Barnacles are missing.** `Preset_MadFisherman.Conversation` is still `{fileID: 0}`. |
| **2 — Geezer** | 🟡 **Built & wired** (owner + agent, 2026-08-16) | Prefab exists, all components on, `Conversation` confirmed wired. Only the hostile line is left — **your words**. |
| **3 — Place cast** | ⬜ Needs Unity | **Daniel has never been placed** — only `DanielPaulsSpawn`. Nothing in the arc works without him. Mosley, Scrap Man, Ralph & Sanjeet need re-stamping. |
| **4 — Locations** | 🟡 **All four buildings placed** (owner, 2026-08-16) | Exteriors are in London. **No `DungeonPortal` exists anywhere in the project** — every one is solid scenery. Interiors are still bare boxes. |
| **5 — Populate** | ⬜ Needs Unity | Enemies, quest keys, loot. All six Collect items verified present. |
| **6 — Play-test** | ⬜ Needs Unity | — |
| **7 — Quests 6-7** | 🟡 **Written, art in, not imported** (agent + owner, 2026-08-16) | Both quests authored and structurally checked. The boss prefab is the one build left; **no `Preset_TrapBranchManager` exists**. |

**The project compiles.** Running those tools loaded the editor assembly, which cannot happen unless
`Assembly-CSharp` built — so the 147-file namespace rename is through a compiler. That proves it
compiles and *nothing else*.

## Readiness — what an agent-side sweep confirms, 2026-08-16

Checked by reading the files, not by playing. Everything in the ✅ column is one less thing that can
fail silently mid-arc.

| Thing | State |
|---|---|
| **Collect items** — `cherry_mango_vape`, `makeshift_vape`, `blueberries`, `vending_machine_fungus`, `bus_station_barnacles`, `big_blue` | ✅ all six resolve to an `ItemData` in `Resources/Items/` |
| `Preset_CouncillorMosley.Conversation` | ✅ wired (survived the case-collision repair) |
| `Preset_Scrapman` — `Conversation` + `QuestKey: scrapman` | ✅ both set |
| `Preset_DanielPauls` — `Conversation` + `QuestKey: danielpauls` | ✅ both set — but **he is not placed** |
| `Preset_UnderHoused.Conversation` | ✅ wired |
| `Preset_MadFisherman.Conversation` | 🔴 `{fileID: 0}` — the owed import is what fills it |
| `Preset_TrapBranchManager` | 🔴 does not exist; Phase 7 builds it |
| `QuestDefinition` count | 🔴 **7 of 9**; `gangbusters` and `ah_barnacles` never imported |
| `DungeonPortal` instances, whole project | 🔴 **zero** |
| `Assets/c/NavMesh.asset` | 🔴 stale against four buildings |

⚠️ **`Preset_CouncillorMosley.QuestKey` is blank, and that is correct — do not "fix" it.** No stage
anywhere is `TALKTO mosley`; every one of his grants and completions is driven from his dialogue
choices in `quests/dialogue/councillormosley.quest`. A `QuestActor.Key` is only needed where a stage
names it. The four that are actually named by a stage are `scrapman`, `danielpauls`,
`mad_fisherman` and `trap_branch_manager`.

**The kill keys a stage names**, for Phase 5 and 7: `under_housed` (✅ on the prefab),
`tortured_neek`, `bus_station_neek` ×3, `trap_house_gang` ×5, `trap_branch_manager` ×1 — the last
four are yours to stamp.

---

## Phase 0 — Prep the ingredients ✅ DONE

*Completed by agent 2026-08-15 (items + keys) — commit `1d8e66e`. Nothing to do here; the checks
below are what to confirm on first open.*

- [x] **The 5 item assets exist** in `Assets/Resources/Items/`, hand-authored with correct `ItemID`s
  and their icons wired:
  - `MakeshiftVape.asset` (`makeshift_vape`) and `BigBlue.asset` (`big_blue`) — copied from
    `CherryMangoVape` (Type 8, not sellable, not stackable).
  - `Blueberries.asset`, `VendingMachineFungus.asset`, `BusStationBarnacles.asset` — copied from
    `Blackberry` (Type 7, stackable ×20, tradeable, heals 4 HP / 2 mana).
- [x] **`Preset_DanielPauls.QuestKey` = `danielpauls`** — was blank.
- [x] **`Preset_Scrapman.QuestKey` = `scrapman`** — was blank.

Setting those keys means the NPCs stamped in Phase 3 carry the right `QuestActor` automatically —
`PlacementBuilders.ApplyQuestKey` copies the preset's `QuestKey` onto whatever is stamped.

**Three things to confirm / decide when you open Unity:**

- ⚠️ **Hand-authored `.meta` GUIDs.** Confirm Unity keeps them rather than minting new ones. Even if
  it re-mints, nothing breaks — items resolve by `ItemID` *string*, not GUID.
- **`Description` is blank on all five** — the flavour text is the owner's words. They work fine
  blank; the bag just shows nothing until filled in.
- **The three forage items are a faithful `Blackberry` copy**, so they are `Tradeable: 1` — a player
  *could sell a quest ingredient*. Set **Tradeable = 0** on the three if you'd rather they can't.
  A balance call, deliberately not guessed.

- [ ] **Commit current work** before Phase 2 — `Build Enemies From Generated Art` rewrites every
  enemy prefab's YAML, so a clean tree makes a bad run one `git checkout` away.

## Phase 1 — Import the art, then the quests 🟡 TWO RUNS OWED

### 1a — the art

- [ ] **`Tools → Art → Import Generated Art`.** 44 player sheets are staged in `art_incoming/`.

All five player classes were internally inconsistent — some sheets at 65 px, some at 74. Every
sidecar is now pinned to `worldHeight: 1.8`, so this run re-does them **in place at 86 px**, GUIDs
intact, and no clip, controller or prefab reference moves.

- [ ] **Check afterwards:** Project → `Assets/Art/Generated/characters/sheet_char_player_idle` →
  the Inspector preview reads **86 px**. Then enter Play for ten seconds and confirm the player is
  visible and animates — if the five class visual profiles did not refresh, that is where it shows.

⚠️ **Pixel size is resolution only.** Nothing gets bigger on screen: `WorldActorVisual.FitScaleToHeight`
computes `scaleY = Height / sprite.bounds.size.y`, normalising every sprite to its `Height` field.
Making a boss tower is a `Height` change on the prefab, and stays adjustable en masse afterwards.

### 1b — the quests

*The owner ran this on 2026-08-16. It wrote the 7 `QuestDefinition`s into `Resources/Quests/` and
two conversations — `Dialogue_danielpauls` and `Dialogue_underhoused` — and wired
`Preset_DanielPauls.Conversation`, which had been blank. Then it hit the defect below.*

**What went wrong.** The case-sensitivity risk this guide flagged landed, but worse than predicted.
`DialoguePathFor` builds `Dialogue_councillormosley.asset` from the lowercase `DIALOGUE` id.
**Unity's AssetDatabase is case-sensitive even on Windows**, so it never found the existing
`Dialogue_CouncillorMosley.asset`; `CreateAsset` then failed against the case-insensitive
filesystem, and the unsaved object was assigned to the preset — serializing as `{fileID: 0}`. It did
**not** make a second asset; it **nulled the link and wrote nothing**, in silence. `danielpauls` and
`underhoused` were unaffected, having no PascalCase asset to collide with.

**Already repaired** (commits `d4e8142`, `e6721a6`): both assets renamed to the lowercase names the
pipeline expects with their `.meta` moved so **GUIDs are unchanged** — the placed Mosley and Scrap
Man never lost their references — both presets' `Conversation` restored, and the importer fixed so
it resolves paths case-insensitively and updates in place.

- [ ] **Re-run `Tools → Content → Import Quests`.** Mosley's and Scrap Man's new lines are still
  unwritten. Now the filenames match, they update in place with GUIDs intact. The same run picks up
  **Gangbusters** and **Ah, Barnacles** — no extra step.
- [ ] **Confirm three presets** show a populated `Conversation` rather than `None`:
  `Preset_CouncillorMosley`, `Preset_Scrapman` and `Preset_MadFisherman` in `Assets/Data/Presets/`.
  The fisherman's was authored blank on purpose (`501746f`); this run is what fills it. **No
  `Preset_TrapBranchManager` exists yet**, so his conversation asset is written and a warning
  logged — wire it by hand once Phase 7 builds his prefab.
- [ ] **Confirm the placed pair still resolve** — select `NPC_Councillor Mosley` and Scrap Man in
  `Home_London_Prefab` and check `NPCDialogueInteractable → Conversation` is not `Missing`.
- [ ] **`Tools → Content → Validate Quests`** if you change any `.quest` file — checks every quest
  has a grant, every grant resolves, objectives aren't blank, each Collect stage is last with a
  completion route.

⚠️ **Sixteen PascalCase dialogue assets are still on disk**, including `Dialogue_Ralph` and
`Dialogue_Sanjeet` — Quest 6's cast. The importer fix protects them, but that fix has **never been
compiled**. If a future import ever nulls a preset again, this is the first thing to look at.

## Phase 2 — Build & wire the geezer 🟡 DONE BAR THE LINE

*The owner ran `Tools → Content → Build Enemies From Generated Art` on 2026-08-16. It created
`Enemy_UnderHoused.prefab` and `Preset_UnderHoused`, and rewrote the YAML of six enemy prefabs and
two police prefabs on its update path — expected churn, committed as `8bedd67`.*

The tool already delivered two of the three things this phase used to ask for: **`EnemyAI` present
but disabled**, and **`QuestActor.Key = under_housed`**. The remaining three components were
hand-written into the prefab YAML (in place, so the GUID is untouched):

| Component | Settings |
|---|---|
| `Interactable` | Prompt "Talk to the twitchy geezer", Range 3, Reusable ✓ |
| `NPCDialogueInteractable` | Conversation → `Dialogue_underhoused` |
| `HostileAfterDialogue` | `OnTalked` bound to `OnInteract`; **line blank** |

- [ ] **Type his hostile one-liner.** Prefab Mode on `Enemy_UnderHoused` → root →
  `HostileAfterDialogue` → **Turn Hostile Line**. Left blank deliberately — the words are yours.
- [ ] **First-open check.** That prefab has never been in an editor. Confirm all five components
  read correctly in the Inspector, and that `Interactable → On Interact ()` shows one entry pointing
  at `HostileAfterDialogue.OnTalked`.
- [ ] **Decide on his combat style.** The tool made him `RangedCaster` with `AttackRange 7` — the
  **only ranged enemy in the roster**; every other is `0` at `1.6`. Plausible for the magic quest's
  target, but it wants a deliberate yes rather than an inherited default.

⚠️ **Do not re-run `Build Enemies From Generated Art`.** It rewrites every enemy prefab's YAML on
its update path and would take the three hand-added components with it. If you ever must, check
`git diff` on `Enemy_UnderHoused.prefab` afterwards.

⚠️ Unverified Unity behaviour: if, once panicked, he stands still or sinks through the floor,
`Awake` didn't run while the AI was disabled — `HostileAfterDialogue` would need to snap him to the
NavMesh itself.

## Phase 3 — Re-place the cast

Do this **after** the imports, never before. Open `Tools → World Palette` and `Home_London_Prefab`
in Prefab Mode; arm a preset, click to stamp, Esc, `Ctrl+S`.

**Who is standing in London right now:** `NPC_Councillor Mosley`, `NPC_Scrapman`, `NPC_Ralph`,
`NPC_Sanjeet`, plus the Roaming Pharmacist and villagers. **Not** Daniel Pauls — only his empty
`DanielPaulsSpawn` marker exists.

**Why re-stamp rather than leave them.** A placement is a *copy, not a link*: the stamped NPC keeps
a reference to its dialogue asset — so a re-import does reach him — but every other preset field
(sprite, controller, height, quest key, merchant catalogue) was baked in at stamp time and never
updates. These four were stamped before the presets were finished. Delete, then stamp.

- [ ] **Councillor Mosley** — the vape-quest giver. Delete `NPC_Councillor Mosley`, then stamp
  `Preset_CouncillorMosley` outside his mansion, which only went in on 2026-08-16. His conversation
  is wired by the Phase 1 import.
- [ ] **Scrap Man** by the flatbed van / scrap props. Delete `NPC_Scrapman` first. Carries
  `QuestKey = scrapman`, his sell shop and his conversation. No separate chunk needed to function.
- [ ] **Daniel Pauls** at the `DanielPaulsSpawn` marker location — **he has never been placed at
  all**. Carries `QuestKey = danielpauls` and his Conversation, so the whole Daniel thread and
  Serendipity! light up together. The linchpin: nothing in the arc works without him.
- [ ] **The geezer** (`Enemy_UnderHoused`) just north of Daniel. **`Preset_UnderHoused` already
  exists** — the build tool created it, pointing at the prefab with the conversation attached, so
  just arm it. Leave the palette **Level** at 0.
  - Its own `QuestKey` is blank, which is correct and safe: `ApplyQuestKey` early-returns on a blank
    preset key, so the prefab's `under_housed` survives the stamp rather than being overwritten.
- [ ] **Move Ralph & Sanjeet out of London to their base house.** Delete `NPC_Ralph` and `NPC_Sanjeet` from
  `Home_London_Prefab` and stamp them inside their base-house prefab — the gang's trap house (the
  `Gang_Hideout` interior is the shell that fits), near the abandoned bus station. **Quest 6
  (Gangbusters) is written and needs them there** — it is only unimported, so this is no longer
  optional dressing.

## Phase 4 — Dress the locations & wire the doors

**The shells now exist.** All the interiors this arc needs are already built as chunks —
`Mosleys_Lab_Basement`, `Abandoned_Church`, `Abandoned_Bus_Station` — plus `Mosley_Mansion` and
`DP_Academy` for later beats. Each is a bare lit box: floor **with a MeshCollider**, four walls, a
`RuntimeNavMeshBaker`, and one id-less `PlayerSpawn`. So there is **no Empty Interior Bundle step
and no falling through the floor** — you dress the existing prefab and wire a door to it.

- [ ] **First-open sanity check (do this once).** The five shells above other than the basement were
  hand-authored as YAML and never opened in Unity. Open each `*_Prefab` in Prefab Mode once and
  confirm Unity accepts it rather than reimporting: one root with a `RuntimeNavMeshBaker`, six
  children (Floor, four Walls, PlayerSpawn), lit floor, no console error. Then confirm
  `Resources/MapChunkRegistry` lists **seventeen** chunks in its Inspector.
- [x] **All four exterior buildings placed in London** (owner, 2026-08-16). Mosley's mansion and its
  well, the abandoned church, the Croyden Spartan traphouse, and the bus station (×2). The well is
  intended to carry the portal both ways — down into the cellar lab and back out of the same well.

⚠️ **Exterior placement and interior dressing are two different jobs, and the same `.glb` serves
both.** What is done is the *outside*: the building you walk up to, standing in London. What the
checkboxes below ask for is the *inside*: dropping that same model into the bare `*_Prefab` shell so
the interior is not a grey box. Neither one puts a door between them — that is the wiring step, and
**no door exists anywhere yet.**
- [ ] **Wire the well, both ways** — the full walkthrough is the next section. It is the arc's first
  door and the **project's first `DungeonPortal` anywhere**, so it is also the first real exercise
  of portal travel, the arrival-marker lookup and the validator.
- [ ] **Dress & wire the Abandoned Church** (`Abandoned_Church_Prefab`; model
  `abandoned+church+3d+model.glb` is imported):
  - Open the prefab, drop the church model in as a child (the placeholder box floor/walls stay — they
    give you the collider and NavMesh surface; scale/hide walls to taste once the model reads right).
  - Wire a **London → church** linked pair, interior `Abandoned_Church`.
- [ ] **Dress & wire the Old Bus Station** (`Abandoned_Bus_Station_Prefab`; model
  `bus+station+3d+model.glb`) — same recipe, interior `Abandoned_Bus_Station`.
- [ ] **`Portal Placement → Validate All Location Links`** (read-only). Clear every error — a
  non-reciprocal pair or broken arrival marker is a building you enter and can't leave.

⚠️ **The five new ChunkNames are permanent save keys the instant a save is made inside one** —
`Abandoned_Church`, `Abandoned_Bus_Station`, `Mosley_Mansion`, `DP_Academy` (and the existing
`Mosleys Lab Basement`, note the spaces and no underscore). Nothing has saved in any of them yet, so
**now is the free moment to rename** — do it before the first play-test, or not at all.

*Not needed for this arc, but the shells are ready when you are:* `Mosley_Mansion` (the WTF Mosley?
confrontation could move upstairs from the basement), `DP_Academy` (Daniel's magic guild — he's
placed on the London street today, so the academy is optional), `FU_Sports` and `Quidland` (merchant
interiors, pre-existing shells). The northern trap house / `Gang_Hideout` is where Ralph & Sanjeet
go (Phase 3), and **Quest 6 that uses it is now written** — so it is on the critical path once the
import runs, not a later nicety.

## Phase 4a — Wiring the well, click by click

Down into Mosley's cellar lab and back out of the same well. **One tool run writes both ends.**

### What "both ways" actually means

The well carries **one** portal. You do *not* put two on it. The return trip is a separate portal at
the foot of the ladder down in the basement. Each end also gets an **arrival marker** — the pad you
land on — and the London one sits **beside** the well, not in it, which is what makes climbing out
read as climbing out. Each portal points at the *other* chunk's marker by id; that crossover is the
whole trick, and the tool does it for you.

### Before you touch anything

1. **Exit Play mode and press `Ctrl+S`.** Inspector changes made during Play are discarded when it
   stops, and this tool writes to prefab assets on disk.
2. **Decide the Link Id now: `mosley_basement`.** Letters, digits, `_` and `-` only
   (`LocationLinks.IsValidLinkId`). It names this pair permanently and appears inside four object
   names. Re-running with the *same* id updates what it made; a *different* id makes a second door
   beside the first.

### A — capture the London end

3. **Project panel → `Assets/Prefabs/Chunks/Home_London_Prefab` → double-click.** That opens Prefab
   Mode; the Hierarchy switches to this prefab's contents, with a back arrow at the top-left.
4. **Open `Tools → Place → Portal Placement`.** An amber banner reads *"Prefab Mode is open on
   Home_London_Prefab…"*. **That is correct here** — capturing poses is exactly what Prefab Mode is
   for. The Create button being greyed out is also correct; it stays that way until step 15.
5. **Fill in the top three fields.** Link Id `mosley_basement` · Exterior Chunk `Home_London_Data` ·
   Interior Chunk `Mosleys_Lab_Basement_Data`. Both are object fields — drag from
   `Assets/Data/Chunks/` or use the circle picker.
6. **Set the prompts and range.** *Exterior Prompt* is what you see at the well — "Climb down the
   well". *Interior Prompt* is what you see at the bottom — "Climb back up". *Interact Range* 3 is
   the project norm; the well is a big object, so 4 is defensible if the prompt feels hard to catch.
7. **Select the well in the Hierarchy, then press "From Selection" under Exterior Door.** It copies
   that object's position *and rotation*, converted to be relative to the prefab root. If the well
   is a nested GLB whose pivot sits somewhere unhelpful, make an empty child `WellMouth`, drag it to
   the lip, and capture that instead.
8. **Point the rotation away from the mansion.** The portal draws an **orange arrow** in the Scene
   view. That arrow is "the way out", and it is what the next step derives along. Type a Y rotation
   until it points at open, walkable ground — not into a wall, not off a kerb.
9. **Press "Derive From Door" under Outside Marker.** Puts the marker 3.5 m along that arrow, facing
   the same way, so you climb out already looking away from the well. A **green pad with a blue
   arrow** appears in the Scene view — check by eye that it is on flat ground. Nudge the numbers by
   hand if not; the window warns in amber below 3.5 m (`LocationLinks.MinMarkerClearance`).

### B — capture the basement end

10. **Leave Prefab Mode** (back arrow, top-left of the Hierarchy), **then open
    `Assets/Prefabs/Chunks/Mosleys_Lab_Basement_Prefab`.** The tool window keeps everything you have
    typed — its fields are `[SerializeField]` on an `EditorWindow` on purpose, so they survive
    prefab switches, recompiles and Play mode.
11. **Decide where the ladder comes down and put something there.** The shell is a bare box with a
    floor and four walls. With no ladder model yet, create an empty named `LadderFoot` against a
    wall — the portal has no renderer of its own, so an empty is perfectly valid and a model can be
    dropped on it later.
12. **Select it and press "From Selection" under Interior Door.** Or use **From Scene Pivot**: frame
    the spot in the Scene view and press it — position only, rotation stays as typed. Set the
    rotation so the orange arrow points *into the room*, not into the wall behind it.
13. **Press "Derive From Door" under Inside Marker.** 3.5 m into the room, facing into the room.
    That is where you land coming down the well.
14. **Confirm no amber clearance warnings are showing.** Two can appear, one per end. Both mean the
    same thing: the marker is close enough to the door back out that you would arrive standing
    inside its USE prompt, which reads as having failed to go anywhere.

### C — write it

15. **Leave Prefab Mode. The Create button lights up.** *Not optional.* Closed prefabs are edited in
    place via `LoadPrefabContents`, and doing that to one that is simultaneously open fights
    whatever the stage holds in memory. The tool refuses rather than risk it.
16. **Press "Create Or Update Linked Pair".** It writes the exterior end first, then the interior,
    then registers both chunks in `MapChunkRegistry` and saves.
17. **Read the console.** You want three lines starting `PortalPlacementTool: linked
    'mosley_basement'.` ⚠️ If instead it says the exterior end was written but the interior failed,
    **the pair is half done** — London has a well into a basement with no way out. Fix the cause and
    re-run before ever entering it.
18. **Press "Validate All Location Links"** and read the panel underneath. Read-only, safe any time.
    Errors are real breakage; registry warnings are worth clearing too.
19. **Open `c.unity` and press "Register Both Chunks With Scene ChunkManager", then `Ctrl+S`.**
    Optional but tidy — the registry already covers loading, but `AllChunks` is consulted first and
    keeping the scene list honest makes what the game can reach visible in the Inspector. The button
    warns if you are still in Prefab Mode.
20. **Open both prefabs once more and check the tree matches:**

```
Home_London_Prefab
└─ LocationLinks
   └─ mosley_basement
      ├─ Portal_Enter                          ← at the well · DungeonPortal + Interactable
      └─ PlayerSpawn_mosley_basement_outside   ← where you land coming back up

Mosleys_Lab_Basement_Prefab
└─ LocationLinks
   └─ mosley_basement
      ├─ Portal_Exit                           ← at the ladder foot
      └─ PlayerSpawn_mosley_basement_inside    ← where you land going down
```

⚠️ **Never wire `Interactable → On Interact ()` yourself.** It will look empty and wrong, and it is
meant to. `DungeonPortal.Awake` adds its own listener at runtime; a persistent editor-time entry
sits *alongside* it, so one press sends you on two journeys. The tool deliberately leaves it blank.

### Notes

- **Re-running is how you adjust it.** Same Link Id, change what you want, press Create again — it
  finds everything by name under `LocationLinks/<linkId>/` and updates in place, so no GUID changes
  and no second door appears. To change only a prompt or the range while keeping positions you have
  since nudged in the prefab, turn **Overwrite Poses On Update** `OFF` first.
- **`Mosleys Lab Basement` — spaces, no underscore.** The asset is `Mosleys_Lab_Basement_Data` but
  its `ChunkName` has spaces, like `Manor Cellars`. That string is the save key. Nothing has ever
  saved in there, so renaming is still free; after the first in-interior save it is permanent.
- **Leave `Require Tutorial Done` OFF.** On, the well is barred until the Manor Cellars tutorial is
  finished and answers "The way is barred for now."
- **Two refusals that are working as intended.** The portal refuses while you are riding anything —
  *"Get off the vehicle first."* — because a vehicle is a separate root that would be stranded in a
  chunk about to be destroyed. And every portal shares a 1.5 s cooldown, so you cannot bounce back.
- ⚠️ **The wanted level does NOT clear going down the well.** That is the point of a fix that landed
  2026-08-15 and has **never run**, because no portal existed to run it. The first trip down is its
  first exercise: commit a crime in London, drop down the well, and check the knives readout does
  *not* move and the console logs "Slipped indoors…". Walking out to `North_Wasteland` over a chunk
  edge should still clear it.
- **Coming back up rebuilds London from the prefab.** `TravelRoutine` destroys and re-instantiates,
  so dropped items, dead NPCs and opened chests in London reset. Inventory and quest state are safe.
  Known and scoped out deliberately — see `BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md`.
- **A deliberately broken test, if you want proof the safety net works.** Set the well's
  `Target Spawn Point Id` to something that does not exist and press USE: you should stay put with a
  warning naming the chunk and the id — not a black screen, not a half-loaded chunk. Put it back.

## Phase 5 — Populate: enemies, keys & loot

- [ ] **Mosley's basement — Tortured Neek.** Stamp `Preset_TorturedNeek`. On the instance:
  - `QuestActor`, **Key** = `tortured_neek`.
  - `LootOnDeath`, Loot → Item = `CherryMangoVape`, Quantity 1 (the "tainted vape" the Collect stage wants).
  - *(Tortured Neek is a unique subject, so `QuestActor Key = tortured_neek` can instead live on
    `Preset_TorturedNeek` once. Don't do that with the shared Neek preset.)*
- [ ] **Church — a vape-dropping Neek.** Stamp `Preset_Neek`; no kill key (the stage is Collect).
  Add `LootOnDeath` → Item = `makeshift_vape`, Quantity 1.
- [ ] **Bus station — three keyed Neeks + forage.** Stamp `Preset_Neek` ×3. On **each**:
  - `QuestActor`, **Key** = `bus_station_neek` (all three share it — the "kill 3" target).
  - `LootOnDeath` — split the forage so killing all three yields the set: `blueberries` ×2,
    `vending_machine_fungus` ×2, `bus_station_barnacles` ×2.
  - ⚠️ Kill targets must live in **one chunk** — respawns re-arm the count on a crossing.

## Phase 6 — Play-test the chain

1. **Talk to Mosley** → accept → *Chemical Castration Gone Wrong* starts. *(Silent? His dialogue
   didn't update — Phase 1 case-sensitivity check.)*
2. **Basement:** kill the Tortured Neek, loot the vape, return to Mosley → he takes it, points you
   at Daniel → *Find the Magic Man* starts. *(Kill didn't count? Wrong `QuestActor Key`. No vape?
   Wrong `LootOnDeath` item/ID.)*
3. **Talk to Daniel** → sends you to the church → *Check Out the Church* starts. *(He also offers
   Serendipity! here.)* *(Daniel silent/absent? Not placed, or Conversation didn't wire.)*
4. **Church** → loot the makeshift vape → back to Daniel → *Investigate the Weird Vape* starts.
5. **Scrap Man → Daniel → bus station:** kill 3 Neeks, gather 6 forage → Daniel brews the **Big
   Blue** (reward into the bag) → *Deliver the Big Blue* starts. *(Stuck on "talk to Scrap Man"?
   Wrong key. No Big Blue? Missing `big_blue` ItemData.)*
6. **Hand the Big Blue to Scrap Man** (consumed) → reveal → back to Daniel → *WTF Mosley?* starts,
   and Scrap Man's **Sell shop** unlocks.
7. **Confront Mosley** → confession → *Gangbusters* is granted from his closing line (Phase 7).
8. **Reload a save mid-arc** — kill count survives, Big Blue still in the bag, no console errors.

## Phase 7 — Quests 6-7, the Ralph & Sanjeet trail

*Written by agent 2026-08-16 (`5cb332c`): `quests/gangbusters.quest` and `quests/ah_barnacles.quest`.
Structurally checked, never imported. Both characters' art imported the same day (`94b1cad`).*

The chain is now closed end to end. Mosley's existing closing line ("a little place near the
abandoned bus station") gained a `GRANT: gangbusters`; the Trap Branch Manager grants *Ah, Barnacles*
as he gives up the name; the Mad Fisherman's last choice completes it. **No new items** — Quest 7
reuses `bus_station_barnacles`.

- [x] **Art imported for both new characters, and `Preset_MadFisherman` authored** (2026-08-16).
  The Trap Branch Manager arrived with a full six-action set including his **Sludge Bomb**, which
  needed the importer taught a new `special` action (`1ca1998`) before it would wire into a
  controller at all — `trap_branch_manager_Controller` now carries a `Special` state.
  `Preset_MadFisherman` and its `CharacterData` speaker went in as `501746f`.
- [ ] **Build the Trap Branch Manager prefab.** `Tools → Content → Build Enemies From Generated Art`
  creates `Enemy_TrapBranchManager.prefab` and `Preset_TrapBranchManager`. ⚠️ That tool rewrites the
  YAML of every enemy prefab on its update path, which would strip the geezer's three hand-added
  components. **Run it on a clean tree**, then immediately restore him with
  `git checkout -- Assets/Prefabs/Enemies/Enemy_UnderHoused.prefab` and re-check his components.
- [ ] **Set the three prefab fields that carry the "knocked out, not dead" beat.** He talks, fights,
  then talks again from the floor. That needs **no new code**, but it rests on:
  - `Health.DestroyOnDeath` = **false** — keeps the body. `Health.Die` still fires `OnDeath` and
    awards XP *before* its early return, so the Kill stage still counts. `EnemyAI` then stops on its
    own; every loop early-returns on `IsDead`.
  - `HostileAfterDialogue.DisableInteractionWhenHostile` = **false**, or the talk prompt is switched
    off when he turns on you and he can never be spoken to again.
  - The death clip must **hold its last frame** rather than loop.
  - *Cost of that second one:* the talk prompt stays visible during the fight, and using it opens a
    conversation with no valid choice. A small mirror-of-`HostileAfterDialogue` component would fix
    it properly — not built, deliberately.
  - *Also note:* the `!DestroyOnDeath` path returns **before** colliders and the NavMeshAgent are
    disabled, so his body keeps its collider and may stand rather than lie. Don't leave him in a
    doorway.
- [ ] **Dress the trap house** — the `Gang_Hideout` shell is the interior;
  `Croyden+spartan+traphouse+3d+model.glb` is committed and is the building. Same recipe as the
  church. This is also where **Ralph & Sanjeet** go (Phase 3's last step), so both jobs in one visit.
- [ ] **Place the Mad Fisherman.** The brief is "the chunk to the right of London", which is
  `East_RetailPark` at `(1, 0)`. **Worth a decision:** a fisherman in a retail park is an odd fit,
  and `West_Canal` is the water chunk but sits on the wrong side. His objective text deliberately
  says nothing more precise than the direction, so a new coastal chunk east of London also works
  without a rewrite.
- [ ] **Stamp the trap-house gang** — Roadmen and Neeks, all keyed `trap_house_gang`, one count for
  the lot. ⚠️ **The count in the file is 5 and is a placeholder** — it must equal the number of
  keyed actors actually stamped, or the stage can never clear. Same one-chunk rule as always.
- [ ] **Place ten barnacle containers** in the bus station, with
  `Tools → Place → Container Placement`. Attach one to each piece of wreckage: Mode **Fixed**,
  **Fixed Loot** = `BusStationBarnacles` ×1, prompt "Search wreckage". Shift-click stays armed for
  the run. ⚠️ **Fixed Loot, not `LootBand_BusBarnacles`** — the band can roll nothing, and the stage
  wants exactly ten. Then press **Validate All Containers** and confirm no duplicate save ids.
  ⚠️ **Respawn is no longer free.** Container state is saved now, so a Fixed container stays empty
  and a Respawning one sits out `RespawnVisits` entries to the chunk — re-entering does not reset
  either. ⚠️ **Quest 4 leaves two of these in the bag** and never consumes them, so a player
  arriving here starts at 2/10, not 0/10. Not a miscount — flagged so it doesn't look like one.
- [ ] **Fill the `[TODO:]` lines** — nine **player** lines across the two files, four in Gangbusters
  and five in Ah, Barnacles. Every NPC line the owner sent is in verbatim; only the player's side is
  placeholder where the script had none. The quests import and run with them in place; they just
  read as brackets on screen. The Mad Fisherman's `[...]` is the owner's own speechless beat, kept
  verbatim, and is **not** a TODO.

⚠️ **The Sludge Bomb has art and an animation state and does nothing.** Nothing decides what it
fires or what it does on landing. That mechanic is an open question for the owner.

### Quest 8 — Rush Hour (TBC)

No file written; it needs prose first. What it will need building:

| Needs | State | Note |
|---|---|---|
| East York chunk at `(0, -2)` | not built | Two south, straight through `South_Slums`. A new `MapChunkData` + prefab + registry entry — same shape as the interior shells, but an exterior with edges. |
| Alex as a hired companion | half there | `Preset_Alex` exists and the whole companion system is written, but **no `CompanionDefinition` asset exists anywhere**, so none of it has ever run. Alex would be its first exercise. |
| Alex's "free for this one" offer | needs words | Owner's prose. He normally charges; this mission he doesn't. |
| Mayor Zhao + forced approach dialogue | new | Nothing starts a conversation on proximity today — every conversation is USE-driven. This is the one genuinely new mechanic Quest 8 needs. |

---

## Reference — save keys (copy exactly)

### Items

All six now exist as assets in `Assets/Resources/Items/`. Nothing to create.

| ItemID | Asset | Modelled on | Icon |
|---|---|---|---|
| `cherry_mango_vape` | `CherryMangoVape` ✓ | — | ✓ |
| `makeshift_vape` | `MakeshiftVape` ✓ (2026-08-15) | `CherryMangoVape` | ✓ |
| `big_blue` | `BigBlue` ✓ (2026-08-15) | `CherryMangoVape` | ✓ |
| `blueberries` | `Blueberries` ✓ (2026-08-15) | `Blackberry` | ✓ |
| `vending_machine_fungus` | `VendingMachineFungus` ✓ (2026-08-15) | `Blackberry` | ✓ |
| `bus_station_barnacles` | `BusStationBarnacles` ✓ (2026-08-15) | `Blackberry` | ✓ |

*The `red_berries` icon is unused — the quest wants `blueberries`. All five new ones have a blank
`Description` awaiting the owner's words, and the three forage items inherited `Tradeable: 1`.*

### QuestActor keys

| Key | Goes on | Set how | Used by |
|---|---|---|---|
| `danielpauls` | Daniel Pauls NPC | `Preset_DanielPauls.QuestKey` ✓ **set** | Investigate — TalkTo |
| `scrapman` | Scrap Man NPC | `Preset_Scrapman.QuestKey` ✓ **set** | Investigate / Deliver — TalkTo |
| `tortured_neek` | Tortured Neek | `QuestActor` on instance (or its preset) | Chemical Castration — Kill ×1 |
| `bus_station_neek` | 3 bus-station Neeks | `QuestActor` per instance | Investigate — Kill ×3 |
| `under_housed` | the geezer | `QuestActor` on `Enemy_UnderHoused` ✓ **set** | Serendipity! — Kill ×1 |
| `trap_house_gang` | every Roadman & Neek in the trap house | `QuestActor` per instance | Gangbusters — Kill ×5 (**count is a placeholder**) |
| `trap_branch_manager` | the boss | `QuestActor` on his prefab | Gangbusters — TalkTo, then Kill ×1 |
| `mad_fisherman` | Mad Fisherman NPC | `Preset_MadFisherman.QuestKey` ✓ **set** | Ah, Barnacles — TalkTo |

### Dialogue assets — filenames are case-sensitive to the importer

One `DIALOGUE` block per npcId across the whole `quests/` tree, and the asset filename must match
the id **exactly**, including case. All six live ids do:

| `DIALOGUE` id | Asset |
|---|---|
| `councillormosley` | `Dialogue_councillormosley.asset` (renamed 2026-08-16, GUID kept) |
| `danielpauls` | `Dialogue_danielpauls.asset` |
| `scrapman` | `Dialogue_scrapman.asset` (renamed 2026-08-16, GUID kept) |
| `underhoused` | `Dialogue_underhoused.asset` |
| `trapbranchmanager` | `Dialogue_trapbranchmanager.asset` (new — written by the owed import) |
| `madfisherman` | `Dialogue_madfisherman.asset` (new — written by the owed import) |

*Neither new id has a PascalCase asset on disk, so neither can hit the case-collision defect.*

### Locations

| ChunkName | Status | Needs |
|---|---|---|
| `Mosleys Lab Basement` | shell ✓, **well placed in London** | Wire the pair (Phase 4a); then Tortured Neek + vape drop. Note the spaces — the asset is `Mosleys_Lab_Basement_Data` but the save key is not |
| `Abandoned_Church` | shell ✓ (2026-08-16) | First-open check; drop church model in; door from London; a vape-dropping Neek |
| `Abandoned_Bus_Station` | shell ✓ (2026-08-16) | First-open check; drop bus-station model in; door from London; 3 keyed Neeks + forage |
| `Mosley_Mansion` | shell ✓ (2026-08-16) | Not required by this arc — ready for the WTF Mosley? finale if wanted |
| `DP_Academy` | shell ✓ (2026-08-16) | Not required by this arc — Daniel's guild interior, optional |
| `Gang_Hideout` | shell ✓ | **Quest 6.** Croyden traphouse model; door; keyed gang + the boss. Ralph & Sanjeet live here |
| `East_RetailPark` | exists | **Quest 7.** The chunk east of London — the Mad Fisherman goes here, subject to the fit question in Phase 7 |
| East York `(0, -2)` | not built | **Quest 8.** Two chunks south, through `South_Slums`. Nothing exists yet |

*Shells created 2026-08-16 by cloning the Quidland shell (fresh GUIDs, registered, `--check-dangling`
clean). Never opened in Unity — first-open check in Phase 4. `FU_Sports` and `Quidland` shells
already existed. Rename any ChunkName **before** its first in-interior save; after that it's a save key.*
