# Mobile performance pass

```
Landed on:            main
Verification scope:   Tools/asset_reachability.py --check-dangling only. No compiler, no Unity,
                      no test framework in this environment (CLAUDE.md §5). Nothing below has
                      been seen by either.
```

## Why

The project had never been configured for mobile or iOS: no texture anywhere carried an
Android/iOS import override, Android quality defaulted to Medium (shadows + anisotropic filtering
on), and 36 MB of the 3D model budget was a completely unreferenced asset pack. This pass fixes
the mechanical parts of that — texture compression, quality tiers, a device-preference settings
menu — without touching gameplay code or the chunk-lifecycle constraints in CLAUDE.md §3.

## What landed

1. **Deleted `retro_house_pack`** (36 MB) and the four `Assets/Materials/RetroHouses/*.mat` that
   pointed into it. Confirmed 0/59 reachable before deletion, `--check-dangling` clean before and
   after. `docs/reference/REPO_HYGIENE.md` corrected — it previously said 6/69 used.
2. **`Tools/Art/Apply Mobile Texture Settings`** (`Assets/Editor/MobileTextureSettingsTool.cs`)
   — sets Android + iPhone platform texture overrides (ASTC 6×6, capped max size, mipmaps per
   folder). Deliberately skips `Assets/Art/Generated/` and `Assets/Art/Placeholders/` — that's
   `ArtImportTool`'s territory, and its `npotScale: None` is load-bearing for sprite-sheet slicing.
   **Creating the tool changed nothing.** See §10.3 check 2 below for what running it does.
3. **Quality tiers retuned** (`ProjectSettings/QualitySettings.asset`): Android and iPhone moved
   from Medium (index 2) to Low (index 1). Medium's `shadowDistance` and `anisotropicTextures`
   trimmed slightly, since it's still reachable manually from the settings menu on a device that
   can afford it. No level added, removed or reordered.
4. **`GraphicsPrefs`** (`Assets/Scripts/Systems/GraphicsPrefs.cs`) — the project's first
   `PlayerPrefs` usage, deliberately kept out of `SaveGameManager`/`savegame.json` since this is
   device preference, not game state. Quality stored by name, not index. Applies on
   `RuntimeInitializeOnLoadMethod(BeforeSceneLoad)`.
5. **`SettingsWindowUI`** (`Assets/Scripts/UI/SettingsWindowUI.cs`) — Win95-skinned, modelled on
   `PerkWindowUI`. Opened from a title-screen button cloned from `NewGameButton` in
   `TitleScreenUI.BuildSettingsButton()` — no new serialized field, no scene edit, no builder
   re-run needed.

## What did NOT land (by design)

- Chunk pooling or any `SetActive(false)` on a chunk root — forbidden by CLAUDE.md §3 regardless
  of performance benefit.
- `Animated Chest` was not deleted — it's referenced in `c.unity` and `Preset_Chest.asset`. Its
  weight (three uncompressed TGAs, ~45 MB of the pack) is addressed by the texture tool once run,
  not by removing the content.
- ARM64 + IL2CPP — not scriptable, Unity regenerates toolchain state on the change. Owner action,
  §10.3 check 9 below.
- `CombatController.FindSpellTarget`'s allocating `Physics.OverlapSphere` — left as-is. One
  allocation per spell cast isn't a per-frame mobile problem, and it can't safely reuse the
  existing 10-slot melee buffer without silently truncating spell target selection in a crowd.
- Other confirmed-dead 3D packs found in passing (tube station, `DarkGothicStone_Seamless.png`,
  out london rubbish, 5 stray `.glb` files) — the user may still have plans for some of these.
  Left alone entirely, not scheduled.

## §10.3 — never verified, check the next time Unity is open

1. **The project still compiles.** Two new runtime scripts (`GraphicsPrefs`, `SettingsWindowUI`)
   and one new editor script (`MobileTextureSettingsTool`) — none has been near a compiler.
   `.cs.meta` files for all three were hand-authored with fresh GUIDs (no Unity available to
   generate them); confirm on first open that Unity accepts them rather than minting new ones.
2. **The texture tool has never been run.** `Tools → Art → Apply Mobile Texture Settings
   (Dry Run)` first, read the Console summary — confirm nothing under `Assets/Art/Generated/`
   appears in the applied list. Then run the real pass; expect ~50-60 `.meta` files to change.
   If any character sheet shows compression artifacts or wrong slicing afterward, revert its
   `.meta` from git — the sprite folders should have been skipped entirely.
3. **The Chest textures have never been inspected post-compression.** After running the tool,
   check `Assets/3DModels/Animated Chest/OldChest/ModelAndTexture/Chest.tga`'s Android platform
   tab (Override on, 512, ASTC 6×6), then look at the chest in `c.unity` at normal camera distance
   — it went from three ~2048² uncompressed TGAs to 512² ASTC, arithmetic says ~64 MB → ~0.5 MB in
   VRAM, but nobody has looked at the actual result.
4. **The settings button has never been seen.** Play from the title screen — `Settings` should
   appear directly above `Quit`, cloned styling intact. Wrong height/position means the sibling-
   index insert landed in the wrong parent.
5. **Open/close the settings window twice.** A `PauseManager` push/pop imbalance shows up as the
   game staying frozen after close, or another menu refusing to open afterward.
6. **Shadows-then-quality ordering has never run.** Turn Shadows OFF, then cycle Quality — shadows
   must **stay** off. `QualitySettings.SetQualityLevel` overwrites `.shadows` as a side effect;
   `GraphicsPrefs.Apply()` re-applies the shadow override after the quality call specifically to
   guard this, but it's untested.
7. **Persistence has never run.** Set Very Low, stop Play, start Play — must still read Very Low.
   This is the only thing that proves the `BeforeSceneLoad` boot hook actually fires.
8. **Render scale has never been seen at a non-1.0 value.** 60% should visibly soften the frame
   without breaking any UI layout.
9. **ARM64 + IL2CPP is still not done.** Android is currently ARMv7-only with scripting backend
   unset (falls through to Mono) — the project cannot currently publish to the Play Store,
   independent of this pass. Route: `Edit → Project Settings → Player`, Android tab → Other
   Settings → Scripting Backend: IL2CPP, Target Architectures: tick ARM64, Texture compression
   format: ASTC. iOS tab → confirm Scripting Backend reads IL2CPP. Play mode stopped, `Ctrl+S`.
10. **No Android or iOS build has ever been produced with any of this.** Nothing in this pass
    proves the game actually ships until one is.

## Cannot be proved without a device

Whether ASTC 6×6 at 512 looks acceptable on a real screen. Whether Low is the right default tier —
the settings window exists partly so this becomes something a player can correct empirically. Any
actual frame-time or memory number; the VRAM estimates above are arithmetic from texture format and
dimensions, not profiler readings.
