# Save format and Unity serialization

```
Last verified against: working tree on branch progression-perks, 2026-08-08
Verification scope:    code (read line by line); tracked prefab/asset YAML. The appended
                       BundaBasher=4 class mapping is code-reviewed but not Unity-tested. Quest persistence
                       across an autosave was confirmed in an editor session by reading
                       savegame.json directly. The three quest fixes on main POSTDATE that
                       session and are UNVERIFIED. The appended TotalXP and PerkIds fields are
                       code-read only — no compiler and no Unity have seen either, and no save has
                       been round-tripped with them present. PerkData.PerkId is documented from the
                       code that reads it; no PerkData asset exists yet, so no perk id has ever
                       been written to a save file.
```

**This is the highest-risk area in the repo.** A mistake here corrupts player saves silently —
nothing throws, nothing logs, the data is just gone.

## The format

`Assets/Scripts/Flow/SaveGameManager.cs`. **One JSON file**, written with `JsonUtility` to
`persistentDataPath/savegame.json`. Not PlayerPrefs. There is no `EA_` prefix anywhere.

`SaveData` holds, in declaration order: character name, class, `TutorialComplete`, chunk name,
position, health, mana, stamina, quest list, inventory, `Equipment`, `Pounds`, `LootedContainers`,
`VisitedChunks`, `UnlockedWikiEntries`, `TotalXP`, `PerkIds`.

Everything from `Equipment` onwards was **appended**, so a save written before that feature existed
has no such key at all and `JsonUtility` reads back the type's default — `0` for `Pounds` and
`TotalXP`, an empty list for the rest. Each of those defaults is the correct starting state, which
is why none of them needed a migration. All are restored by
`GameFlowController.ContinueFromSave` through the matching `PlayerSession.RestoreX` method,
alongside `RestoreInventory`.

⚠️ **`TotalXP` is the player's cumulative XP, and the level is derived from it, never stored.**
`EKVibe.LevelForXP` resolves the total on every read, so the curve constants in `EKVibe` may be
retuned freely without touching a save file. The field name **is** the JSON key —
`JsonUtility` ignores `[FormerlySerializedAs]` — so renaming it would silently revert every
existing player to level 1.

The same warning applies to `PerkIds` — see its own save-key section below.

## Five call sites write a save

| Site | When |
|---|---|
| `ChunkManager.TransitionToChunkRoutine` | every chunk edge crossing |
| `ChunkManager.TravelTo` → `TravelRoutine` | portal travel |
| `GameFlowController` (×2) | new-game start, and tutorial completion |
| `PubInteractable.HaveAPint()` | the deliberate manual save point |

## Save keys — changing one of these orphans existing saves

### `MapChunkData.ChunkName`

Stored as a **string** and resolved on load via `ChunkManager.FindChunkByName` against the
`ChunkManager.AllChunks` array.

- Editing the `ChunkName` **value** in any `Assets/Data/Chunks/*.asset` invalidates existing
  saves. The lookup fails, `ContinueFromSave` logs a warning and falls back to
  `GameFlowController.LoadLondonAtWestGates` — the run continues, but the saved chunk and
  position are gone.
- A chunk missing from `AllChunks` is unloadable even if the asset exists.
- `Manor_Cellars_Data` has `ChunkName: "Manor Cellars"` (a space) while every other chunk uses
  underscores. **Do not normalise this** — it is a save key.
- The `Home_Alvaston` → `Home_London` rename was done with a migration: `ReadSaveData` translates
  the legacy string on load, so old saves survive. Any future chunk rename needs the same.

### `ItemData.ItemID`

Inventory **is** saved: one `InventorySaveEntry` per stack as `ItemID` + `Quantity`, resolved back
through `Resources/Items` by `PlayerSession.RestoreInventory`.

- Changing an `ItemID` **value** on an existing item orphans it out of every save **silently** —
  the entry is read, the lookup fails, the item is dropped and nothing is reported.
- An item must stay reachable from `Resources/Items`, since that is how the load resolves it.

### `WikiEntryData.EntryID`

WIKIBRITAIN unlocks are saved as a plain `List<string>` of `EntryID` values in
`SaveData.UnlockedWikiEntries`, resolved back through `Resources/Wiki` by `WikiDatabase`. Changing a
shipped `EntryID` **value** relocks that entry for every existing save, silently.

### `PerkData.PerkId`

Spent perks are saved as a plain `List<string>` of `PerkId` values in `SaveData.PerkIds`, resolved
back through `Resources/Perks` by `PerkDatabase.Find`. Same never-rename rule as the three above.

- Changing a shipped `PerkId` **value** orphans that perk: the id is read, the lookup fails, and the
  perk's effects silently stop existing.
- ⚠️ **Unresolvable ids are kept, not dropped** — deliberately the opposite of what
  `RestoreInventory` does with an unresolvable `ItemID`. Dropping them would look tidy and quietly
  refund the perk point, handing out a free respec whenever an asset was temporarily missing.
  `PlayerSession.RestorePerkIds` stores the raw string; `RecalculateDerivedStats` skips what
  `PerkDatabase.Find` cannot resolve, and `Find` logs it once. Re-adding the asset restores the perk.
- The player's **perk points are derived**, never stored: `EKVibe.PerkPointsAtLevel` computes them
  from the level, which is itself derived from `TotalXP`. So the cadence can be retuned without a
  save migration, exactly like the XP curve. `PlayerSession.UnspentPerkPoints` clamps at 0 so a
  downward retune cannot show a negative figure; the derivation still honours every spent id.
- `PerkEffectType` is serialized by integer index inside each `PerkData` asset. Append only.

### Container ids — `"<ChunkName>/<GameObjectName>"`

`SpriteContainer` in `Fixed` mode remembers being emptied. The key it uses is built in its `Awake`
as `CurrentChunkData.ChunkName + "/" + gameObject.name`, cached, and written into
`SaveData.LootedContainers` as a plain list of strings.

**This is a save key with no asset behind it**, which makes it easier to break than the other two:

- It is compared **verbatim**. Never trim, lower-case, slugify or otherwise normalise it —
  `Manor_Cellars_Data` has `ChunkName: "Manor Cellars"`, with a space, and normalising would orphan
  every container looted there.
- **Renaming a container GameObject in the Hierarchy refills it** for every existing save, silently.
  So does renaming its chunk.
- **Two containers with the same name in the same chunk share one id**, and looting either empties
  both. `SpriteContainer.Awake` warns when it sees a duplicate, naming both the chunk and the name.
- A container with no resolvable chunk cannot build an id at all. It warns and behaves as
  `Respawning` for that session rather than throwing in `Awake`.

Restore ordering matters and is load-bearing: `GameFlowController.ContinueFromSave` calls
`PlayerSession.RestoreLootedContainers` immediately after `RestorePounds`, **before** either
`EnterManorCellars` or `LoadWorld`. Every container reads the set in its own `Awake`, so a world
built first would refill everything the player had cleared.

`PlayerSession` holds the set as a private `HashSet<string>`, not a serialized field — it reaches
the file through `SaveData` only. `BeginNewGame` clears it beside `Inventory.Clear()`, so a New Game
in the same app session does not inherit the last playthrough's emptied bins.

## What is and is not saved

**Saved:** character name and class, `TutorialComplete`, chunk, position, health/mana/stamina,
quest state, inventory, pounds, the ids of emptied `Fixed` containers.

`PlayerClass` is stored as its integer enum value. The original mappings remain
`YoungDriller=0`, `EnGarde=1`, `MrHood=2`, `Dynamo=3`; `BundaBasher=4` was appended so existing
saves keep their class identity.

**Not saved:** wanted level, and whether you are riding anything. A load puts you on foot with
vehicles back at their authored spots, and a vehicle you had already nicked is nickable again.
(⚠️ One exception, and it is a known defect — see the death-respawn note in
[CONSEQUENCES_AND_MOUNTS.md](CONSEQUENCES_AND_MOUNTS.md).)

`TutorialComplete` is checkpointed the moment it happens, so it survives an app restart, and a
*mid*-tutorial save restarts the tutorial cleanly rather than resuming half-staged. Gates keyed
off `TutorialComplete` do **not** re-lock after a restart.

## Adding fields to save data

`QuestProgress` gained three fields — `StageIndex`, `StageProgress`, `RewardsClaimed` — and
`SaveGameManager` needed no change: it hands the whole `List<QuestProgress>` to `JsonUtility`, so
new fields are picked up automatically and an old save reads them as zero/false, which is the
correct default.

They are **public fields, not properties**. `JsonUtility` only serializes public fields; a
property there would silently never persist.

---

# Serialized-reference hazards

Renaming any of these breaks Unity serialization silently — fields go null, enums shift.

## Public serialized field names

Unity matches by name. Renaming any public field on a `MonoBehaviour` or `ScriptableObject` drops
its value in every prefab, scene and `.asset` unless you add `[FormerlySerializedAs]`.

**Appending a serialized field is safe; inserting is not.** `MapChunkData.VehicleSpawns` was added
after the adjacency block for this reason.

The live `[FormerlySerializedAs]` cases, all from the gold→pounds rename, are the ones to copy:

| Field now | Was | Authored in |
|---|---|---|
| `PlacementPreset.PickpocketMinPounds` / `MaxPounds` | `PickpocketMinGold` / `MaxGold` | 25 `Preset_*.asset` |
| `PickpocketInteractable.MinPounds` / `MaxPounds` | `MinGold` / `MaxGold` | nothing on disk — `NoseyParker.prefab` was the only holder and has been deleted |
| `QuestReward.PoundsAmount` | `GoldAmount` | nothing yet — no `QuestDefinition` assets exist |

Those `.asset` files still carry the **old** key names on disk; the attribute remaps
them on load and Unity rewrites them on its next save of each file. That is the intended state, not
an unfinished migration — **do not hand-edit the YAML to "finish" it**, and do not delete the
attributes afterwards, because any copy of those assets that has not been re-saved still needs them.

The live proof that appending is safe: `EnemyAI.IsPolice` was added after four of the five
`Police_*` prefabs were written. Those four carry no `IsPolice` key at all and load the C#
default rather than breaking. (That they all read *false* is a separate live defect — see
[CONSEQUENCES_AND_MOUNTS.md](CONSEQUENCES_AND_MOUNTS.md).)

## Class names and script GUIDs

The `.cs` filename must match the `MonoBehaviour` class name, and script GUIDs in `.meta` files
bind prefabs and the scene to the script. **Rename via Unity, not the filesystem.**

⚠️ **Commit a script's `.meta` with the script.** This has gone wrong twice. `PlacementPreset.cs`
went in without one, and that file holds the GUID every `Preset_*.asset` binds to via `m_Script` —
a fresh clone would have minted a new GUID and silently detached every preset.

Unity writes metas on its next open, so a session that adds a script without opening Unity leaves
the meta missing entirely. If two machines then open it independently they mint different GUIDs,
and whatever binds to the script resolves on one and is null on the other.

```bash
git ls-files 'Assets/**/*.cs' | while read f; do [ -f "$f.meta" ] || echo "NO META: $f"; done
```

## Enums are serialized by integer index

Reordering or inserting values silently remaps existing data. **Always append.**

Fifteen live enums, from `grep -rn "public enum" --include="*.cs" Assets/Scripts`:

`Direction`, `AbilityResourceType`, `ItemType`, `PlayerClass`, `GameFlowState`,
`HUDActionButton.ActionKind`, `InstanceDoor.Destination`, `PlacementCategory`, `CityRegion`,
`QuestConditionType`, `MagicTutorial.Stage`, `TutorialSequence.Stage`,
`SpriteContainer.ContainerMode` (`Fixed = 0`, `Respawning = 1`), `WikiCategory`,
`PerkEffectType`.

`HUDActionButton.ActionKind` is the one with values proven live in serialized data: `c.unity`
holds six authored `HUDActionButton` components covering `Attack=0`, `Ability=1`, `Inventory=2`
and `Interact=3`. They belong to the legacy cluster that `BuildActionButtons` deactivates, but
they are still serialized, so a reorder would repoint them. `Crouch` was appended as 4.

`PlayerClass` is also live in the JSON save as an integer. `BundaBasher` is appended at index 4;
never insert a future class before it or reorder the five existing values.

## Asset cross-references

`Assets/Data/Chunks/*.asset` reference each other **by GUID** for adjacency. Deleting or
regenerating a `.meta` breaks the adjacency graph.

## ⚠️ Never rebuild an existing prefab by deleting and re-saving it

`ModernBritainSetup.BuildEBikePrefab` does `AssetDatabase.DeleteAsset(path)` then
`SaveAsPrefabAsset`. That takes the `.meta` with it and mints a fresh GUID, so **re-running that
tool orphans every EBike and Pub instance already placed** — they detach silently
and the scene keeps empty prefab stubs.

To change an existing prefab, edit it in place:

```
PrefabUtility.LoadPrefabContents → modify → SaveAsPrefabAsset → UnloadPrefabContents
```

`ArtImportTool` and `GeneratedEnemyPrefabTool` are the worked examples — both edit in place. The
counter-example used to be `EnemyPrefabSetup.BuildPoseController`, which deleted and re-created its
controller every run; it was deleted along with the Orc and Bot Wheel subjects. The remaining
rebuild-from-scratch tools all sit under `Danger Zone` and confirm before they run.

## Before any rename or refactor touching this document

Produce an explicit **mapping table** first: old name → new name → every file that binds it.
