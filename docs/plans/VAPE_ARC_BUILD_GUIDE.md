# Vape Arc Build Guide — implementing the written quests

```
Last verified against: working tree, 2026-08-15
Verification scope:    Editor steps traced against code and tracked YAML — the placement of the
                       London cast (Mosley placed; Daniel only a DanielPaulsSpawn marker; Scrap
                       Man and the geezer unplaced), the enemy quest-key path
                       (PlacementBuilders.BuildEnemy -> ApplyQuestKey; all six enemy presets carry
                       a blank QuestKey), LootOnDeath, HostileAfterDialogue, NPCDialogueInteractable,
                       and the Portal Placement tool. NOTHING in this pipeline has been imported or
                       run — there is no compiler or Unity in the agent environment. Every step
                       below must be verified in the editor. Companion doc: the quest-script map.
```

The seven-quest arc — **Serendipity! → Chemical Castration Gone Wrong → Find the Magic Man →
Check Out the Church → Investigate the Weird Vape (pt 1 & 2) → WTF Mosley?** — is fully written in
`quests/` and `quests/dialogue/`. The words are done. This is the **content and wiring** that turns
those text files into a playable chain, in the order it has to happen.

## Four things that bite

1. **One editor session, no Play mode, for Phases 0–2.** `MagicTutorial` is deleted, so until the
   import runs, London has no working Daniel and no geezer. Compile → validate → import in one
   sitting; don't press Play in the middle.
2. **Commit before the enemy build tool.** `Build Enemies From Generated Art` rewrites every enemy
   prefab's YAML on its update path. Run it on a clean tree so a bad run is one `git checkout` away.
3. **Save keys are forever.** An `ItemID`, a quest id, a `QuestActor.Key` or a `ChunkName` that
   does not match *exactly* fails silently — the stage just never advances and nothing logs. Copy
   the strings from the reference tables below; don't retype from memory.
4. **A placement is a copy, not a link.** An NPC stamped into a chunk holds a *reference* to its
   dialogue asset (so re-importing that asset updates him), but every other preset field was baked
   in at stamp time. If in doubt after import, delete and re-stamp.

## The order

`0 Prep → 1 Import → 2 Geezer → 3 Place NPCs → 4 Locations → 5 Populate → 6 Play-test.` Each phase
depends on the one before it.

---

## Phase 0 — Prep the ingredients

- [ ] **Commit current work** so Phase 2's enemy tool has a clean tree.
- [ ] **Create the 5 item assets.** The icons are already imported; only the `ItemData` objects are
  missing. In `Assets/Resources/Items/`, right-click → `Create → ExiledAlvaston → Data → Item Data`,
  once per item. Set **ItemID** to the exact string, drag the matching `spr_ui_item_…` sprite into
  **Icon**, and copy the other fields from the template so Type/stacking are right:
  - `makeshift_vape` & `big_blue` → copy `CherryMangoVape.asset` (quest item; not sellable, not stackable).
  - `blueberries`, `vending_machine_fungus`, `bus_station_barnacles` → copy `Blackberry.asset` (forage; stackable, tradeable).
  - ⚠️ You have both a `blueberries` and a `red_berries` icon — the quest wants **`blueberries`**.
    `ItemName` / `Description` are the owner's words; leave them blank to fill in.
- [ ] **Set `Preset_DanielPauls.QuestKey` = `danielpauls`** (Investigate stage 1 is `TALKTO danielpauls`).
- [ ] **Set `Preset_Scrapman.QuestKey` = `scrapman`** (two quests use `TALKTO scrapman`).

Both keys are blank on disk today. Setting them now means the NPCs stamped in Phase 3 carry the
right `QuestActor` automatically — `PlacementBuilders.ApplyQuestKey` copies the preset's `QuestKey`
onto whatever is stamped.

## Phase 1 — Import the quests

- [ ] **Let it compile.** Console clean before continuing.
- [ ] **`Tools → Content → Validate Quests`** — checks every quest has a grant, every grant
  resolves, objectives aren't blank, each Collect stage is last with a completion route. Fix what it
  names. A missing **item** logged here means Phase 0 isn't finished.
- [ ] **`Tools → Content → Import Quests`** — writes 7 `QuestDefinition`s into `Resources/Quests/`,
  the `Dialogue_*.asset` conversations into `Data/Dialogue/Generated/`, and wires
  `Preset_DanielPauls.Conversation` (blank today) plus Mosley's and Scrap Man's. Read the log for
  "missing item" lines.
- [ ] **Confirm Mosley kept his link.** The placed `NPC_Councillor Mosley` references his dialogue
  asset by GUID, so an in-place re-import *should* give him the new lines.
  - ⚠️ **Case-sensitivity:** the existing asset is `Dialogue_CouncillorMosley.asset`; the importer
    writes `Dialogue_councillormosley` (lowercase, from the `DIALOGUE` block name). If Unity makes a
    *second* lowercase asset instead of overwriting, Mosley keeps his old one-liner. If so: set the
    placed Mosley's `NPCDialogueInteractable → Conversation` to the new asset, or delete and re-stamp.

## Phase 2 — Build & wire the geezer

The under-housed geezer is an **enemy that talks first, then turns hostile**. His prefab doesn't
exist yet; his full sheet set does.

- [ ] **`Tools → Content → Build Enemies From Generated Art`** → creates
  `Assets/Prefabs/Enemies/Enemy_UnderHoused.prefab`. ⚠️ This rewrites every enemy prefab's YAML —
  check `git status` after and `git checkout` anything unexpected.
- [ ] **Open it in Prefab Mode** and on the root:
  - **EnemyAI** — *untick* (disabled). He's harmless until talked to.
  - **Add `QuestActor`**, **Key** = `under_housed`. *(The kill target for Serendipity! — note the
    underscore; different string from the dialogue's `underhoused`. This is not in the CLAUDE.md
    wiring list and is required for the kill stage to bind.)*
  - **Add `Interactable`** — Prompt "Talk to the twitchy geezer", Interact Range 3, Reusable on.
  - **Add `NPCDialogueInteractable`** — Conversation = `Dialogue_underhoused.asset` (from the import).
  - **Add `HostileAfterDialogue`** — type his hostile one-liner into **Turn Hostile Line** (owner's words).
- [ ] **Hook the interact:** Interactable → **On Interact ()** → `+` → drag the GameObject in →
  `HostileAfterDialogue.OnTalked ()`. Save the prefab.
  - ⚠️ Unverified Unity behaviour: if, once panicked, he stands still or sinks through the floor,
    `Awake` didn't run while the AI was disabled — `HostileAfterDialogue` would need to snap him to
    the NavMesh itself.

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
- [ ] **The geezer** (`Enemy_UnderHoused`) just north of Daniel. Needs an Enemy preset pointing at
  the prefab — create `Preset_UnderHoused` (Category **Enemy**, **EnemyPrefab** = `Enemy_UnderHoused`)
  if none exists, or drag the prefab in by hand. Leave the palette **Level** at 0.
- [ ] **Relocate Ralph & Sanjeet to their base house.** Delete `NPC_Ralph` and `NPC_Sanjeet` from
  `Home_London_Prefab` and stamp them inside their base-house prefab — the gang's trap house (the
  `Gang_Hideout` interior is the shell that fits), near the abandoned bus station. Not needed to play
  the current arc (Quest 6 is unwritten), but it puts them where the story wants them.

## Phase 4 — Build the locations & wire the doors

- [ ] **London → Mosley's basement.** The chunk exists (`Mosleys_Lab_Basement_Prefab`, ChunkName
  `Mosleys Lab Basement`). `Tools → Place → Portal Placement` → author a **linked pair**: exterior
  `Home_London`, interior `Mosleys Lab Basement`, link id e.g. `mosley_basement`. Capture poses in
  Prefab Mode; create the link with no prefab stage open.
- [ ] **Abandoned Church chunk** (model `abandoned+church+3d+model.glb` is imported; no chunk yet):
  - `Portal Placement → Create Empty Interior Bundle` — empty `MapChunkData` + prefab, registered.
    Give it a ChunkName you'll never change (a save key).
  - Open the prefab, drop in the church model, **add a floor with a collider** (the bundle has none —
    the player falls through).
  - Confirm a `RuntimeNavMeshBaker` and one `PlayerSpawn` are present (add the baker if missing).
  - Wire a London → church door.
- [ ] **Old Bus Station chunk** (model `bus+station+3d+model.glb`, imported today) — same recipe.
- [ ] **`Portal Placement → Validate All Location Links`** (read-only). Clear every error — a
  non-reciprocal pair or broken arrival marker is a building you enter and can't leave.

*Not needed for this arc:* the northern trap house and a bespoke Scrap Man yard. WTF Mosley?
completes at Mosley, and Quest 6 (Ralph & Sanjeet) isn't written — skip both until then.

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

| ItemID | Status | Copy from | Icon |
|---|---|---|---|
| `cherry_mango_vape` | exists | — | done |
| `makeshift_vape` | make it | `CherryMangoVape` | `spr_ui_item_makeshift_vape` |
| `big_blue` | make it | `CherryMangoVape` | `spr_ui_item_big_blue` |
| `blueberries` | make it | `Blackberry` | `spr_ui_item_blueberries` |
| `vending_machine_fungus` | make it | `Blackberry` | `spr_ui_item_vending_machine_fungus` |
| `bus_station_barnacles` | make it | `Blackberry` | `spr_ui_item_bus_station_barnacles` |

### QuestActor keys

| Key | Goes on | Set how | Used by |
|---|---|---|---|
| `danielpauls` | Daniel Pauls NPC | `Preset_DanielPauls.QuestKey` | Investigate — TalkTo |
| `scrapman` | Scrap Man NPC | `Preset_Scrapman.QuestKey` | Investigate / Deliver — TalkTo |
| `tortured_neek` | Tortured Neek | `QuestActor` on instance (or its preset) | Chemical Castration — Kill ×1 |
| `bus_station_neek` | 3 bus-station Neeks | `QuestActor` per instance | Investigate — Kill ×3 |
| `under_housed` | the geezer | `QuestActor` on `Enemy_UnderHoused` | Serendipity! — Kill ×1 |

### Locations

| ChunkName | Status | Needs |
|---|---|---|
| `Mosleys Lab Basement` | chunk ✓ | Door from London; Tortured Neek + vape drop |
| Abandoned Church *(name it)* | build | Model ✓; Empty Interior Bundle → floor → NavMesh → door; a vape-dropping Neek |
| Old Bus Station *(name it)* | build | Model ✓; Empty Interior Bundle → floor → NavMesh → door; 3 keyed Neeks + forage |
