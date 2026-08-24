# Stage R + Stage F brief — REVISED (2026-07-29, code-verified)

> **STATUS: Stage R is DONE and committed. Stage F is outstanding and is why this file is
> still live.**
>
> Stage R shipped on 2026-07-29: both files renamed with `git mv` (`.meta` preserved),
> the `ChunkName` value updated, the save migration added in `SaveGameManager.ReadSaveData`,
> and all code and doc references updated. `Home_London` and `GBH: England` are the current
> names everywhere.
>
> ⚠️ **The Stage R mapping table below is a historical record, not a to-do list.** It still
> reads in the imperative and names `Dialogue_Mosley_Intro.asset`, which no longer exists —
> the v1 dialogue was deleted on 2026-08-03. **Paste only the Stage F parts into a new
> session.**

Revised from `docs/archive/STAGE_F_BRIEF.md` after a verification pass against the code.
Corrections are marked **[FIX]**, additions **[ADD]**. Everything not marked is
unchanged from the original brief and was verified correct.

Paste everything below the line into a new Claude Code session for this repo, and
re-attach the inventory mockup image if you still have it.

---

Project: gba-england — Unity 2022.3 mobile RPG, isometric 3D world with billboarded 2D
sprites. Read CLAUDE.md first; it is code-verified and authoritative. Pay attention to
§4 (conventions), §6 (save keys), §7 (serialization hazards), §8 (consequence systems),
§9b (World Palette), §10 (verification), §13 (NPC pipeline).

STATE
`main` is the only branch and carries everything below. Cut a new branch before making
changes — **[ADD]** two branches, `stage-r` then `stage-f` off the merged R, so R is
reviewed and merged on its own as the brief intends.

    6de4cda  art brief rewritten as a banded queue
    14c5d91  scene-root props removed          (VERIFIED in the editor)
    ebc2f66  a Nosey Parker stamped into Home_Alvaston
    b9d5124  HUD crouch button                 (compiled; not play-tested)
    7b620f0  four CS0618 warnings suppressed
    b1de7fd  Pickpocketable on PlacementPreset (NEVER COMPILED)

`b1de7fd` has not been through Unity. If the first import throws, that is the commit to
look at.

ENVIRONMENT
No C# compiler and no Unity available to you. The only mechanical checks are:

    python Tools/asset_reachability.py --check-dangling
    a brace/paren balance scan (catches truncated edits, nothing else)

Never imply code compiles. State exactly what ran and what did not.

**[FIX] SAVE SYSTEM FACTS — the original brief inherited a stale AGENTS.md line.**
Saves are NOT PlayerPrefs and there is NO `EA_` prefix anywhere in the codebase
(grep-verified). `SaveGameManager` writes one JSON file via `JsonUtility` to
`persistentDataPath/savegame.json` (`SaveGameManager.cs:44,84`). `SaveData` is a flat
`[Serializable]` class; inventory persists as `List<InventorySaveEntry>` of
`ItemID + Quantity` (`SaveGameManager.cs:11-35`), with ItemIDs resolved back through
ItemDatabase. AGENTS.md's "PlayerPrefs, EA_ prefix" description is stale and should be
corrected when R lands.

GOAL
Stage R (rename), then Stage F (inventory + loot overhaul). Stage G (shops and prices —
the payouts themselves are already done) is gated behind F and is NOT in scope. Do R first: it is small, isolated, and touches a
save key, so it should be reviewed on its own rather than buried in F.

DECISIONS ALREADY MADE — DO NOT RE-OPEN
- Mobile-first. No hover, no right-click, no long-press anywhere. Tap is the only verb.
- Tap a bag tile = equip if wearable, consume if consumable. Drop-mode ON = tap drops.
- Dropped items land in a world "loot pile" that can be reopened and taken back. Enemy
  death drops use the SAME object. A pile dies when emptied or when the chunk changes.
- Bag is 24 slots with finger scroll.
- Reputation button is present but visually disabled and does nothing. No system exists.
- Skin is EKVibe parchment, matching the existing HUD. Not grey stone.
- The unlabelled box at the top of the reference mockup is dead space — do not build it.
- Currency is POUNDS (£), not gold. Storage and payouts are both DONE — they landed
  together ahead of F1, so Stage G is now only about shops and prices.

THE SCREEN (opened by the HUD bag button)
Three panels side by side, plus header and footer:

    Header  — "GBH: England", and a back-to-game close button
    Left    — character sheet: name, six core stats (STR/END/AGI/INT/AWA/PER), and
              resistances bottom-left (Armor/Fire/Cold/Poison/Magic)
    Middle  — 24-slot bag grid, scrollable, small items stack
    Right   — paper doll, 11 equipment slots in the classic layout, with two buttons
              underneath: armour-bonus summary (left) and unequip-all (right)
    Footer  — DROP (mode toggle) / SPELLS / STATS / JOURNAL / REP

LAYOUT — already costed, do not redo this
At the 1920x1080 reference canvas with 140px slots (~9mm on a 6in phone), the three
panels fit: 380 + 636 + 484 + gaps = ~1572 of 1920. HORIZONTAL IS NOT THE CONSTRAINT.
The main canvas uses `m_MatchWidthOrHeight: 0` (match width), so on a 20:9 phone in
landscape the available REFERENCE height is ~864px, not 1080. After header and footer
that leaves ~670 for the body — four rows of bag visible, 24 reachable by scroll.

FINDINGS THAT SHAPE THE WORK (all verified in code, do not re-derive)
- `InventoryController.EquipmentSlots` is a `public Dictionary<ItemType, Image>`
  (InventoryController.cs:29). Unity still cannot serialize a Dictionary — but it is no
  longer dead: it is a runtime cache populated by `BuildEquipmentSlots()` from the
  rebuilt paper doll, not a persistence surface. The real equipment model lives on
  `PlayerSession.Equipment` (`IReadOnlyDictionary<ItemType, ItemData>`) with
  `Equip`/`Unequip`/`UnequipAll`/`RestoreEquipment`, persisted as `SaveData.Equipment`
  and read live at the two use sites (weapon damage and armour). There is no `EquipItem`
  method any more. **F1 shipped all of this; F2–F6 remain.**
- The 20-slot bag cap is not a constant. `PopulateBackpack` loops over
  `BackpackGridContainer.childCount`, i.e. however many BagSlot GameObjects were dragged
  into `c.unity`. Building the grid in code removes the cap permanently.
- `CharacterData.CoreTraits` (Strength/Endurance/Agility/Intelligence/Awareness/Perception)
  and `CharacterData.Resistances` (Physical/Magic/Fire/Cold/Poison) already map 1:1 onto
  the left panel. "Armor" in the mockup is `Resistances.Physical`.
- `InventoryController` already carries serialized fields for `CharacterNameText`,
  `LevelText`, `CoreTraitsText`, `AttackStatsText`, `ResistancesText`, `CharacterPortrait`,
  `PaperDollContainer`, `TooltipPanel` and an `UnequipButton` that nothing calls.
- **[FIX]** `SpellbookUI.Open()` (SpellbookUI.cs:26) and `QuestJournalUI.Open()`
  (QuestJournalUI.cs:182) both exist as static entry points. The original brief said
  `QuestJournalUI.Toggle()` — no such method; it is `Open()`. Check whether `Open()`
  toggles or only opens before wiring the JOURNAL button; if it only opens, the button
  needs a close path too. Both footer buttons remain ~one line each.
- `ItemData` has only `Damage` and `Armor`. No per-resistance bonuses, no stack flag.
- `ItemType` has 9 values (Weapon, Shield, Head, Chest, Cloak, Ring, Boots, Consumable,
  Quest) and is a live serialized enum — APPEND ONLY (§7).
- **[ADD]** Slot maths, stated explicitly so nobody re-derives it wrong: appending
  Neck, Legs, Gloves, Ammo gives 13 `ItemType` values, of which exactly 11 are
  equippable (Consumable and Quest are not). That is the 11 doll slots, ONE slot per
  type — including a single Ring slot, not the classic two. The old
  `Dictionary<ItemType, Image>` shape already assumed 1:1 type↔slot, so keep that
  model. If the mockup shows two ring slots, that is a design change to raise, not to
  improvise around.
- **[ADD]** Ammo is speculative: nothing in the game is ranged today (LightningBolt is
  a spell, not a weapon). Keep the Ammo slot only if the mockup visibly has one;
  otherwise append Neck/Legs/Gloves only and leave a 10-slot doll. Flag whichever way
  the user answers.
- `LootMenuUI.Show(title, entries, onClosed)` is generic and already shared by
  `LootChest` and `LootOnDeath` (LootMenuUI.cs:38). `LootEntry` carries Name,
  Description, Icon, OnTaken, Taken.
- Precedent for building UI in code and deactivating the legacy scene objects:
  `UIManager.BuildActionButtons` (UIManager.cs:404). Follow it.
- Precedent for an object that dies with its chunk: `VehicleSpawner` parents instances
  to the live chunk instance (§11). Use the same trick for loot piles — no despawn
  logic needed.

STAGE R — rename, its own branch (`stage-r`), its own commit
`Home_Alvaston` is a relic; it should be `Home_London`. The game's real name is
GBH: England. `Home_Alvaston` is a `ChunkName` and therefore a SAVE KEY (§6). Mapping
table (every row grep-verified 2026-07-29):

    MapChunkData.ChunkName value    Home_Alvaston -> Home_London    ** SAVE KEY **
      (lives in Assets/Data/Chunks/Home_Alvaston_Data.asset line 15 — edit in place)
    Assets/Data/Chunks/Home_Alvaston_Data.asset       -> Home_London_Data.asset   (keep .meta)
    Assets/Prefabs/Chunks/Home_Alvaston_Prefab.prefab -> Home_London_Prefab.prefab (keep .meta)
    DeathScreenUI.cs:102   FindChunkByName("Home_Alvaston") -> "Home_London"
    DevZoneJump.cs:28      Jump("Home_Alvaston", ...)       -> "Home_London"
    ChunkArtMerge.cs:14, DiscoverEnglandSetup.cs:67 and :407 — path constants
    EKVibe.cs:11 DisplayTitle    "Discover England" -> "GBH: England"

**[ADD] Rows the original table missed:**
- `DiscoverEnglandSetup.cs:75` — a comment saying "Keep ChunkName as Home_Alvaston —
  SaveGameManager/DeathScreenUI look chunks up by …". Becomes actively misleading;
  update or delete it in the same commit.
- `Home_Alvaston_Prefab.prefab:2410` — a GameObject named `Portal_Home_Alvaston`.
  COSMETIC ONLY: portal travel is component-based (`DungeonPortal.TargetChunk` is a
  serialized asset reference; nothing finds portals by name — grep-verified). Rename
  for tidiness if convenient, but note that `PortalPlacementTool` /
  `PlacementBuilders` name NEW portals `Portal_{ChunkName}`, so future portals will be
  `Portal_Home_London` regardless.
- `Assets/c.unity:23810` — scene-side name string `Home_Alvaston_Prefab`. Cosmetic
  (GUID references survive the file rename); rename only if already in the scene file.
- Docs sweep, same commit or a follow-up: CLAUDE.md (~15 mentions, including §6's
  save-key warning which should name the NEW key), AGENTS.md, ART_PIPELINE.md,
  docs/archive/STAGE_F_BRIEF.md. Do not leave the next agent grepping a dead name.
  Also fix the stale "PlayerPrefs / EA_ prefix" save description in AGENTS.md (see
  SAVE SYSTEM FACTS above).

**[FIX] Migration placement.** The original brief said migrate in
`SaveGameManager.Load()`. Put it in `ReadSaveData()` immediately after
`JsonUtility.FromJson` instead: `if (data.ChunkName == "Home_Alvaston") data.ChunkName
= "Home_London";`. `ReadSaveData()` (SaveGameManager.cs:93) is the single choke point —
both `Load()`/`LoadWorld()` and `GameFlowController.ContinueFromSave` consume the
`SaveData` it returns, so one mapping covers every consumer.

**[ADD] Use `git mv` for the two file renames** so history follows the files, and run
`python Tools/asset_reachability.py --check-dangling` after the rename to prove GUID
bindings survived.

**[ADD] Stage R failure mode is RUNTIME, not compile time.** If the `.asset` ChunkName
edit is missed, everything still compiles; `FindChunkByName("Home_London")` just
returns null and death-respawn silently fails. Compile checks prove nothing for R —
the play-test below is mandatory.

Ask before changing `ProjectSettings` `productName` ("Exiled Alvaston"). The
`ExiledAlvaston` namespace is in 46 `.cs` files and zero serialized assets — safe to
rename but OUT OF SCOPE.

STAGE F — six commits, in this order (branch `stage-f`)

    F1  [DONE — landed on `main`.] Equipment model, no UI. Serializable equipment on
        PlayerSession beside Inventory; Equip/Unequip/UnequipAll respecting
        ItemData.CanBeUsedBy; OnEquipmentChanged mirroring OnInventoryChanged; aggregate
        armour/damage totals. ItemType was extended with `Legs`, `Belt` and `Junk` — this
        plan had speculated Neck/Legs/Gloves/Ammo, but what actually shipped is
        Legs = 9, Belt = 10, Junk = 11 (see ItemData.cs:5-19). The "slot maths" notes
        below are superseded by that landed shape.
        [FIX] SAVE FORMAT: extend the `SaveData` JSON — add
        `List<EquipmentSaveEntry> Equipment` (slot identifier + ItemID, mirroring
        InventorySaveEntry). `int Pounds` is DONE — it landed early with the wallet.
        There is NO EA_ prefix and NO PlayerPrefs; JsonUtility serializes the whole
        SaveData class, so new fields are additive and old saves load with empty
        equipment automatically. Store ItemID per slot exactly as inventory stores
        ItemID + quantity, and resolve through ItemDatabase on load.
        [ADD] Define load-time failure behaviour now: an ItemID that no longer resolves
        (item deleted from Resources) is SKIPPED with a Debug.LogWarning, never an
        exception — a corrupt save currently costs the player their whole inventory.
        [ADD] Define UnequipAll with a full bag: BLOCK with a HUD message ("No room in
        bag"). Do not silently drop to a loot pile in F1 — F5 does not exist yet.
        DONE, ahead of F1: `PlayerSession.Pounds` + `OnPoundsChanged`, the save field,
        and the payouts that were meant to wait for Stage G — pickpocketing, the arrest
        fine and `QuestReward.PoundsAmount` all move real money now. The currency is
        pounds, not gold, and the readout is bound in InventoryController. F3 inherits
        a wired `CurrencyText` rather than having to build one.
    F2  Append Fire/Cold/Poison/Magic resist to ItemData so the armour summary is more
        than two numbers.
    F3  Build the screen in code; deactivate the legacy scene panel. Header, three
        panels, footer. REP disabled and inert. JOURNAL uses QuestJournalUI.Open()
        (see FIX above — confirm close behaviour first).
    F4  Tap semantics and drop mode.
    F5  World/LootPile: holds stacks, carries an Interactable ("Search the pile"),
        parents to the live chunk instance so it dies with the chunk, self-destructs
        when emptied. LootOnDeath changes to SPAWN ONE at the corpse instead of opening
        LootMenuUI directly; dropping from the bag spawns or merges into one at the
        player's feet (define the merge radius — 2m suggested). LootChest is untouched.
        [ADD] Restate the accepted consequence so the reviewer sees it: loot dropped in
        chunk A is GONE if the player crosses an edge and returns, even within one
        session. That is the agreed design ("a pile dies when the chunk changes"), but
        it will feel like a bug in play-testing unless the drop-mode UI hints at it.
    F6  LootMenuUI redrawn as tiles, keeping the LootEntry.OnTaken contract so
        LootChest does not change.

VERIFICATION
There is no test framework. Compile-and-play gates:
- **[ADD] After R (mandatory play test, not just a compile):** (1) die in Home and
  confirm respawn lands in Home_London; (2) Tools/Debug dev jump still teleports;
  (3) keep a pre-rename save file, launch, and confirm it loads INTO Home_London
  (migration works); (4) `--check-dangling` clean. Compile alone proves nothing here.
- After F1 (where a save-format mistake is cheapest to catch): compile, then start a
  new game, equip nothing, cross a chunk edge (autosave), kill app, relaunch — confirm
  the save loads and the JSON now contains an `Equipment` field (`Pounds` is already there).
- After F3: compile plus a screen walk-through on a 20:9 aspect (the height constraint
  above).
When asking for an editor change, give the route through the UI, not just the field
name, and say whether Play must be stopped first (§10).

Existing saves will load after F1 with nothing equipped, because that data
was never written. That is correct behaviour, not a bug — tell the user so they expect
it. **[ADD]** The same is true after R: a migrated save shows chunk Home_London with
everything else identical.

FOUR OPEN QUESTIONS TO PUT TO THE USER EARLY
- Should `ProjectSettings` `productName` change from "Exiled Alvaston" to
  "GBH: England"?
- Should `Preset_Villager` get `Pickpocketable` ticked once band-4 art lands, so there
  is actually something in the world to rob? Nothing is robbable today except the
  Nosey Parker prefab.
- **[ADD]** Does the mockup show an Ammo slot and/or two ring slots? Ammo decides the
  4th appended enum value; two rings would break the 1:1 type↔slot model and needs an
  explicit design call before F1.
- **[ADD]** Should dying cost you a mounted vehicle? Found in the Stage R play-test:
  death-respawn keeps you on the bike (see CLAUDE.md §11 known issues). Fixing it is a
  design call plus VehicleSpawner coordination — decide intent before Stage F touches
  the death/loot path.
