# Save format and Unity serialization

```
Last verified against: ccfa9c9
Verification scope:    code (read line by line); tracked prefab/asset YAML. Quest persistence
                       across an autosave was confirmed in an editor session by reading
                       savegame.json directly. The three quest fixes on main POSTDATE that
                       session and are UNVERIFIED.
```

**This is the highest-risk area in the repo.** A mistake here corrupts player saves silently —
nothing throws, nothing logs, the data is just gone.

## The format

`Assets/Scripts/Flow/SaveGameManager.cs`. **One JSON file**, written with `JsonUtility` to
`persistentDataPath/savegame.json`. Not PlayerPrefs. There is no `EA_` prefix anywhere.

`SaveData` holds: character name, class, `TutorialComplete`, chunk name, position, health, mana,
stamina, quest list, inventory, pounds.

`Pounds` was **appended** after the rest, so a save written before the wallet existed has no
`Pounds` key at all and `JsonUtility` reads it back as `0` — the correct opening balance, which is
why it needs no migration. It is restored by `GameFlowController.ContinueFromSave` through
`PlayerSession.RestorePounds`, alongside `RestoreInventory`.

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

## What is and is not saved

**Saved:** character name and class, `TutorialComplete`, chunk, position, health/mana/stamina,
quest state, inventory, pounds.

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
| `PickpocketInteractable.MinPounds` / `MaxPounds` | `MinGold` / `MaxGold` | `NoseyParker.prefab` |
| `QuestReward.PoundsAmount` | `GoldAmount` | nothing yet — no `QuestDefinition` assets exist |

Those `.asset` and `.prefab` files still carry the **old** key names on disk; the attribute remaps
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

Twelve live enums, from `grep -rn "public enum" --include="*.cs" Assets/Scripts`:

`Direction`, `AbilityResourceType`, `ItemType`, `PlayerClass`, `GameFlowState`,
`HUDActionButton.ActionKind`, `InstanceDoor.Destination`, `PlacementCategory`, `CityRegion`,
`QuestConditionType`, `MagicTutorial.Stage`, `TutorialSequence.Stage`.

`HUDActionButton.ActionKind` is the one with values proven live in serialized data: `c.unity`
holds six authored `HUDActionButton` components covering `Attack=0`, `Ability=1`, `Inventory=2`
and `Interact=3`. They belong to the legacy cluster that `BuildActionButtons` deactivates, but
they are still serialized, so a reorder would repoint them. `Crouch` was appended as 4.

## Asset cross-references

`Assets/Data/Chunks/*.asset` reference each other **by GUID** for adjacency. Deleting or
regenerating a `.meta` breaks the adjacency graph.

## ⚠️ Never rebuild an existing prefab by deleting and re-saving it

`ModernBritainSetup.BuildEBikePrefab` does `AssetDatabase.DeleteAsset(path)` then
`SaveAsPrefabAsset`. That takes the `.meta` with it and mints a fresh GUID, so **re-running that
tool orphans every EBike, Nosey Parker and Pub instance already placed** — they detach silently
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
