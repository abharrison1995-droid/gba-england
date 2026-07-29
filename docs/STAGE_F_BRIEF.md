# Stage R + Stage F brief

Paste everything below the line into a new Claude Code session for this repo, and re-attach
the inventory mockup image if you still have it. The brief is written to work without the
image, but it helps.

Written 2026-07-29, at the point where `main` carries the art brief, the scene-root prop
fixes, the crouch button and the pickpocket preset.

---

Project: gba-england — Unity 2022.3 mobile RPG, isometric 3D world with billboarded 2D
sprites. Read CLAUDE.md first; it is code-verified and authoritative. Pay attention to
§4 (conventions), §6 (save keys), §7 (serialization hazards), §8 (consequence systems),
§9b (World Palette), §10 (verification), §13 (NPC pipeline).

STATE
`main` is the only branch and carries everything below. Cut a new branch before making
changes.

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

GOAL
Stage R (rename), then Stage F (inventory + loot overhaul). Stage G (gold payouts) is
gated behind F and is NOT in scope. Do R first: it is small, isolated, and touches a save
key, so it should be reviewed on its own rather than buried in F.

DECISIONS ALREADY MADE — DO NOT RE-OPEN
- Mobile-first. No hover, no right-click, no long-press anywhere. Tap is the only verb.
- Tap a bag tile = equip if wearable, consume if consumable. Drop-mode ON = tap drops.
- Dropped items land in a world "loot pile" that can be reopened and taken back. Enemy
  death drops use the SAME object. A pile dies when emptied or when the chunk changes.
- Bag is 24 slots with finger scroll.
- Reputation button is present but visually disabled and does nothing. No system exists.
- Skin is EKVibe parchment, matching the existing HUD. Not grey stone.
- The unlabelled box at the top of the reference mockup is dead space — do not build it.
- Gold storage lands in F1; gold payouts stay in Stage G.

THE SCREEN (opened by the HUD bag button)
Three panels side by side, plus header and footer:

    Header  — "GBA: England", and a back-to-game close button
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
- `InventoryController.EquipmentSlots` is a `public Dictionary<ItemType, Image>`. Unity
  cannot serialize a Dictionary, so it is empty at runtime and `EquipItem` is dead code.
  Replace it with a serializable structure; there is currently NO equipment model at all,
  only a UI field.
- The 20-slot bag cap is not a constant. `PopulateBackpack` loops over
  `BackpackGridContainer.childCount`, i.e. however many BagSlot GameObjects were dragged
  into `c.unity`. Building the grid in code removes the cap permanently.
- `CharacterData.CoreTraits` (Strength/Endurance/Agility/Intelligence/Awareness/Perception)
  and `CharacterData.Resistances` (Physical/Magic/Fire/Cold/Poison) already map 1:1 onto
  the left panel. "Armor" in the mockup is `Resistances.Physical`.
- `InventoryController` already carries serialized fields for `CharacterNameText`,
  `LevelText`, `CoreTraitsText`, `AttackStatsText`, `ResistancesText`, `CharacterPortrait`,
  `PaperDollContainer`, `TooltipPanel` and an `UnequipButton` that nothing calls.
- `SpellbookUI.Open()` and `QuestJournalUI.Toggle()` both exist as static entry points.
  Those two footer buttons are one line each.
- `ItemData` has only `Damage` and `Armor`. No per-resistance bonuses, no stack flag.
- `ItemType` has 9 values (Weapon, Shield, Head, Chest, Cloak, Ring, Boots, Consumable,
  Quest) and is a live serialized enum — APPEND ONLY (§7).
- `LootMenuUI.Show(title, entries, onClosed)` is generic and already shared by `LootChest`
  and `LootOnDeath`. `LootEntry` carries Name, Description, Icon, OnTaken, Taken.
- Precedent for building UI in code and deactivating the legacy scene objects:
  `UIManager.BuildActionButtons`. Follow it.
- Precedent for an object that dies with its chunk: `VehicleSpawner` parents instances to
  the live chunk instance (§11). Use the same trick for loot piles — no despawn logic
  needed.

STAGE R — rename, its own branch, its own commit
`Home_Alvaston` is a relic; it should be `Home_London`. The game's real name is
GBA: England. `Home_Alvaston` is a `ChunkName` and therefore a SAVE KEY (§6). Mapping
table:

    MapChunkData.ChunkName value    Home_Alvaston -> Home_London    ** SAVE KEY **
    Assets/Data/Chunks/Home_Alvaston_Data.asset       -> Home_London_Data.asset   (keep .meta)
    Assets/Prefabs/Chunks/Home_Alvaston_Prefab.prefab -> Home_London_Prefab.prefab (keep .meta)
    DeathScreenUI.cs:102   FindChunkByName("Home_Alvaston") -> "Home_London"
    DevZoneJump.cs:28      Jump("Home_Alvaston", ...)       -> "Home_London"
    ChunkArtMerge.cs:14, DiscoverEnglandSetup.cs:67 and :407 — path constants
    EKVibe.DisplayTitle    "Discover England" -> "GBA: England"

Add a migration in `SaveGameManager.Load()` mapping the legacy string `"Home_Alvaston"` to
`"Home_London"` before lookup, so existing saves survive.

Ask before changing `ProjectSettings` `productName` ("Exiled Alvaston"). The
`ExiledAlvaston` namespace is in 46 `.cs` files and zero serialized assets — safe to
rename but OUT OF SCOPE.

STAGE F — six commits, in this order

    F1  Equipment model, no UI. Serializable equipment on PlayerSession beside Inventory;
        Equip/Unequip/UnequipAll respecting ItemData.CanBeUsedBy; OnEquipmentChanged
        mirroring OnInventoryChanged; aggregate armour/damage totals. Append Neck, Legs,
        Gloves, Ammo to ItemType to reach 11 doll slots. EXTEND SaveGameManager, do not
        rebuild it — store ItemID per slot, EA_ prefix, exactly as inventory stores
        ItemID + quantity. Include gold storage here so the save format is extended once
        rather than twice.
    F2  Append Fire/Cold/Poison/Magic resist to ItemData so the armour summary is more
        than two numbers.
    F3  Build the screen in code; deactivate the legacy scene panel. Header, three panels,
        footer. REP disabled and inert.
    F4  Tap semantics and drop mode.
    F5  World/LootPile: holds stacks, carries an Interactable ("Search the pile"), parents
        to the live chunk instance so it dies with the chunk, self-destructs when emptied.
        LootOnDeath spawns one; dropping from the bag spawns or merges into one at the
        player's feet. LootChest is untouched.
    F6  LootMenuUI redrawn as tiles, keeping the LootEntry.OnTaken contract so LootChest
        does not change.

VERIFICATION
There is no test framework. Ask the user to open Unity and compile after F1 (where a
save-format mistake is cheapest to catch) and again after F3 — not only at the end.
When asking for an editor change, give the route through the UI, not just the field name,
and say whether Play must be stopped first (§10).

Existing saves will load after F1 with nothing equipped and no gold, because that data was
never written. That is correct behaviour, not a bug — tell the user so they expect it.

TWO OPEN QUESTIONS TO PUT TO THE USER EARLY
- Should `ProjectSettings` `productName` change from "Exiled Alvaston" to "GBA: England"?
- Should `Preset_Villager` get `Pickpocketable` ticked once band-4 art lands, so there is
  actually something in the world to rob? Nothing is robbable today except the Nosey
  Parker prefab.
