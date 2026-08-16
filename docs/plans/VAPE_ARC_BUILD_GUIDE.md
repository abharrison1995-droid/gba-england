# Vape Arc Build Guide — implementing the written quests

```
Last verified against: working tree, 2026-08-16 (branch quest/vape-arc-import-and-case-fix)
Verification scope:    PHASES 1 AND 2 HAVE NOW BEEN RUN. The owner ran Import Quests and Build
                       Enemies From Generated Art on 2026-08-16, which proves Assembly-CSharp
                       compiles (an editor tool cannot load otherwise) and produced 7
                       QuestDefinitions, 2 new DialogueData assets, Enemy_UnderHoused.prefab and
                       Preset_UnderHoused. The import ALSO hit a case-collision defect that
                       silently dropped Mosley's and Scrap Man's conversations — repaired, and the
                       importer fixed, but a re-import is still owed (phase 1). The geezer's three
                       missing components were hand-wired into the prefab YAML, verified only by
                       --check-dangling and an anchor scan; that prefab has never been opened in an
                       editor. The four interior shells (Abandoned_Church, Abandoned_Bus_Station,
                       Mosley_Mansion, DP_Academy) are still hand-authored YAML never opened in
                       Unity. Phases 3-6 remain entirely unrun. Companion doc: the quest-script map.
```

The seven-quest arc — **Serendipity! → Chemical Castration Gone Wrong → Find the Magic Man →
Check Out the Church → Investigate the Weird Vape (pt 1 & 2) → WTF Mosley?** — is fully written in
`quests/` and `quests/dialogue/`. The words are done. This is the **content and wiring** that turns
those text files into a playable chain, in the order it has to happen.

## Four things that bite

1. **A silent import failure has already happened once.** When a preset's `Conversation` comes back
   `None` after an import, nothing is logged — read the Phase 1 note before assuming an import
   succeeded. Check the presets, not just the console.
2. **Don't re-run `Build Enemies From Generated Art`.** It rewrites every enemy prefab's YAML on its
   update path and would strip the geezer's hand-added components. If you must, `git diff`
   `Enemy_UnderHoused.prefab` afterwards.
3. **Save keys are forever.** An `ItemID`, a quest id, a `QuestActor.Key` or a `ChunkName` that
   does not match *exactly* fails silently — the stage just never advances and nothing logs. Copy
   the strings from the reference tables below; don't retype from memory.
4. **A placement is a copy, not a link.** An NPC stamped into a chunk holds a *reference* to its
   dialogue asset (so re-importing that asset updates him), but every other preset field was baked
   in at stamp time. If in doubt after import, delete and re-stamp.

## The order

`0 Prep → 1 Import → 2 Geezer → 3 Place NPCs → 4 Locations → 5 Populate → 6 Play-test.` Each phase
depends on the one before it.

## Progress

| Phase | State | Where it stands |
|---|---|---|
| **0 — Prep** | ✅ **Done** (agent, 2026-08-15/16) | 5 `ItemData` assets authored, 2 quest keys set. Hand-authored YAML, unopened in Unity. |
| **1 — Import** | 🟡 **Ran, one re-run owed** (owner, 2026-08-16) | 7 quests + 2 dialogues written. Mosley's and Scrap Man's were dropped by a defect — now fixed, but **re-import to write them**. |
| **2 — Geezer** | 🟡 **Built & wired** (owner + agent, 2026-08-16) | Prefab exists, all components on. Only the hostile line is left — **your words**. |
| **3 — Place cast** | ⬜ Needs Unity | **Start here** once the re-import is done. `Preset_UnderHoused` already exists. |
| **4 — Locations** | 🟡 **Shells done** (agent, 2026-08-16) | All chunks exist. Dressing + doors need Unity. |
| **5 — Populate** | ⬜ Needs Unity | Enemies, quest keys, loot. |
| **6 — Play-test** | ⬜ Needs Unity | — |

**The project compiles.** Running those two tools loaded the editor assembly, which cannot happen
unless `Assembly-CSharp` built — so the 147-file namespace rename is through a compiler. That proves
it compiles and *nothing else*; no behaviour has been exercised.

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

## Phase 1 — Import the quests 🟡 RAN, ONE RE-RUN OWED

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
  unwritten. Now the filenames match, they update in place with GUIDs intact.
- [ ] **Confirm the two presets** show a populated `Conversation` rather than `None`:
  `Preset_CouncillorMosley` and `Preset_Scrapman` in `Assets/Data/Presets/`.
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

## Phase 3 — Place the cast (assume nothing is placed)

Treat London as empty of the arc's cast and place each one fresh. A placement is a **copy, not a
link**, so if an older copy is already standing — Mosley, Ralph and Sanjeet sit in
`Home_London_Prefab` today — **delete it first**, then stamp a new one so it picks up the current
preset wiring. Open `Tools → World Palette` and `Home_London_Prefab` in Prefab Mode; arm a preset,
click to stamp, save the prefab.

- [ ] **Councillor Mosley** — the vape-quest giver. Delete any existing `NPC_Councillor Mosley`,
  then stamp `Preset_CouncillorMosley`. His conversation is wired by the Phase 1 import.
- [ ] **Daniel Pauls** at the `DanielPaulsSpawn` marker location. Carries `QuestKey = danielpauls`
  and his Conversation, so the whole Daniel thread and Serendipity! light up. The linchpin — nothing
  in the arc works without him.
- [ ] **Scrap Man** by the flatbed van / scrap props. Carries `QuestKey = scrapman`, his sell shop
  and his conversation. No separate chunk needed for him to function.
- [ ] **The geezer** (`Enemy_UnderHoused`) just north of Daniel. **`Preset_UnderHoused` already
  exists** — the build tool created it, pointing at the prefab with the conversation attached, so
  just arm it. Leave the palette **Level** at 0.
  - Its own `QuestKey` is blank, which is correct and safe: `ApplyQuestKey` early-returns on a blank
    preset key, so the prefab's `under_housed` survives the stamp rather than being overwritten.
- [ ] **Relocate Ralph & Sanjeet to their base house.** Delete `NPC_Ralph` and `NPC_Sanjeet` from
  `Home_London_Prefab` and stamp them inside their base-house prefab — the gang's trap house (the
  `Gang_Hideout` interior is the shell that fits), near the abandoned bus station. Not needed to play
  the current arc (Quest 6 is unwritten), but it puts them where the story wants them.

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
- [ ] **London → Mosley's basement.** `Tools → Place → Portal Placement` → author a **linked
  pair**: exterior `Home_London`, interior `Mosleys Lab Basement`, link id e.g. `mosley_basement`.
  Capture poses in Prefab Mode; create the link with no prefab stage open.
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
go (Phase 3), but Quest 6 that uses it isn't written — skip until then.

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
7. **Confront Mosley** → confession → arc completes (dead-ends into unwritten Quest 6).
8. **Reload a save mid-arc** — kill count survives, Big Blue still in the bag, no console errors.

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

### Dialogue assets — filenames are case-sensitive to the importer

One `DIALOGUE` block per npcId across the whole `quests/` tree, and the asset filename must match
the id **exactly**, including case. All four live ids do:

| `DIALOGUE` id | Asset |
|---|---|
| `councillormosley` | `Dialogue_councillormosley.asset` (renamed 2026-08-16, GUID kept) |
| `danielpauls` | `Dialogue_danielpauls.asset` |
| `scrapman` | `Dialogue_scrapman.asset` (renamed 2026-08-16, GUID kept) |
| `underhoused` | `Dialogue_underhoused.asset` |

### Locations

| ChunkName | Status | Needs |
|---|---|---|
| `Mosleys Lab Basement` | shell ✓ | Door from London; Tortured Neek + vape drop |
| `Abandoned_Church` | shell ✓ (2026-08-16) | First-open check; drop church model in; door from London; a vape-dropping Neek |
| `Abandoned_Bus_Station` | shell ✓ (2026-08-16) | First-open check; drop bus-station model in; door from London; 3 keyed Neeks + forage |
| `Mosley_Mansion` | shell ✓ (2026-08-16) | Not required by this arc — ready for the WTF Mosley? finale if wanted |
| `DP_Academy` | shell ✓ (2026-08-16) | Not required by this arc — Daniel's guild interior, optional |

*Shells created 2026-08-16 by cloning the Quidland shell (fresh GUIDs, registered, `--check-dangling`
clean). Never opened in Unity — first-open check in Phase 4. `FU_Sports` and `Quidland` shells
already existed. Rename any ChunkName **before** its first in-interior save; after that it's a save key.*
