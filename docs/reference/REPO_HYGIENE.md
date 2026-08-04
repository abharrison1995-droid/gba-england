# Repo hygiene, assets and reference integrity

```
Last verified against: ccfa9c9
Verification scope:    tracked files and git state. The pruning described below was carried out
                       and verified with Tools/asset_reachability.py at the time.
```

## Line endings

**A `.gitattributes` does exist**, and it is not LFS: it pins `* text=auto` plus an explicit binary
list, so the repo stores LF and each working tree gets what it wants — CRLF on Windows, LF on
Linux.

This matters because Unity rewrites a whole YAML file whenever it touches one; without it, a line
ending difference and a real edit are indistinguishable in a 100,000-line diff.

⚠️ **A file hand-written by an agent lands LF in the Windows working tree.** It commits identically
but leaves the tree inconsistent. Normalise it:

```bash
rm <file> && git checkout -- <file>
```

## Size

`Assets/` is ~204 MB, down from 672 MB. `.psd`/`.fbx`/`.glb`/`.aseprite` are committed and there is
**no Git LFS**. Pruning will not shrink `.git` — history keeps the blobs.

### How the pruning was done, and how to redo it

Reachability is a **transitive GUID walk**, not a text search. Roots are:

- the build scene (`Assets/c.unity`)
- everything under `Resources/` — loaded by name at runtime, so never GUID-reachable
- everything under `Editor/` and `StreamingAssets/`
- all `.cs` / `.asmdef` / `.dll` — code is not GUID-reachable either
- GUIDs referenced from `ProjectSettings/`
- **hardcoded `"Assets/…"` strings inside `.cs`** — editor tools pass literal paths to
  `AssetDatabase.LoadAssetAtPath`. Miss these and you delete the tooling's dependencies.

Then verify: every unresolved GUID left in `c.unity` must be one that was *already* unresolved
before the deletion. There are **17 such built-in Unity GUIDs**; that is the expected baseline, not
a defect.

**Delete whole packs only where the reachable count is zero.** Partially used packs must be trimmed
per-file or left alone.

⚠️ **A pack's own demo scene is not a root.** An earlier ad-hoc check wrongly reported
`Assets/6twelve/` as heavily used; it was counting the pack's own `DEMO.unity` referencing its own
textures. Exclude those, or every pack looks used.

### Remaining opportunities, all partial

| Pack | Used / total | Size |
|---|---|---|
| `psx urban pack` | 10 / 1009 | 105 MB |
| `Animated Chest` | 6 / 7 | 46 MB |
| `retro_house_pack` | 6 / 69 | 36 MB |

**Biggest remaining trim: `Animated Chest` — 45 MB for one decorative prop**, almost all
uncompressed TGA. It is committed only because `c.unity` references its `Chest.prefab`. Delete the
chest instance in the Unity editor and the whole pack goes with it. Next largest unreferenced:
`psx urban pack` (105 MB), `Characters_psx` (54 MB), `Magic+atk animations` (50 MB).

`Assets/3DModels/Sprites/` was deleted (1,998 files, 454 MB — the craftpix packs) after verifying
zero of its 2,123 assets were referenced. **Policy going forward: pull individual sprites in when a
system needs them, rather than carrying whole packs speculatively.**

Reference integrity is clean: a full pass over every tracked `.unity`/`.prefab`/`.asset`/`.mat`/
`.controller`/`.anim` found exactly one dangling reference, since fixed. One tracked `__MACOSX`
junk file remains.

## Committing scripts

⚠️ **Commit a script's `.meta` with the script.** See
[SAVE_AND_SERIALIZATION.md](SAVE_AND_SERIALIZATION.md) — this has gone wrong twice and the failure
is silent on a fresh clone.

```bash
git ls-files 'Assets/**/*.cs' | while read f; do [ -f "$f.meta" ] || echo "NO META: $f"; done
```

## The four CS0618 warnings are suppressed on purpose

**Do not "modernise" them.** Both replacement APIs live in packages this project does not have —
`Packages/manifest.json` lists neither `com.unity.ai.navigation` nor `com.unity.2d.sprite` — so the
deprecated call is the only one that exists here.

| Site | Deprecated | Replacement lives in | Why it stays |
|---|---|---|---|
| `EKNavMeshBaker.MarkObject`, `DiscoverEnglandSetup` ×2 | `StaticEditorFlags.NavigationStatic` | `com.unity.ai.navigation` | The baker calls built-in `NavMeshBuilder.BuildNavMesh()`, driven by this exact flag. Removing it stops the bake, it does not modernise it. |
| `ArtImportTool` slicing | `TextureImporter.spritesheet` | `com.unity.2d.sprite` | Still functional. `VerifySliced` checks the sub-sprites actually appeared, so if it becomes a no-op the tool reports it. |

Each is a narrow `#pragma warning disable 618` / `restore 618` around the single statement, with
the reason at the site. Revisit if either package is ever added.

## Project naming

Three names are live and **must not be "unified" without an explicit task**:

| Name | Where | Status |
|---|---|---|
| `Exiled Alvaston` | `productName`, root C# namespace, most editor menus | The canonical internal one |
| `GBA: England` | `EKVibe.DisplayTitle` | The player-facing title |
| `Discover England` | `DiscoverEnglandSetup.cs` and its menu item | Editor-tool name only — **no longer the display title** |
| `EK` / Exiled Kingdoms | `EKVibe`, `EKNavMeshBaker` | The *inspiration* game, a deliberate reference |

A rename to **GBA: England** (Great British Annals) has begun. `EKVibe.DisplayTitle` is done, and
the hub chunk rename `Home_Alvaston` → `Home_London` shipped with a save-key migration.

Still open: the `ExiledAlvaston` namespace appears in **46 `.cs` files and zero serialized assets**,
so a namespace rename is safe — Unity binds scripts by `.meta` GUID, not type name — but it is not
done. `productName` is also still "Exiled Alvaston".

A colon is illegal in Windows paths and git repo names, so any repo or folder stays `gba-england`
with `GBA: England` only as a display string.

## Structure facts worth knowing

- **There is one gameplay scene: `Assets/c.unity`.** Renaming it orphans `Assets/c/NavMesh.asset`,
  which is auto-linked by scene name.
- **No `.asmdef` files exist** in project code — everything compiles into `Assembly-CSharp` /
  `Assembly-CSharp-Editor`. `Assets/Editor/` is the only thing keeping editor code out of builds,
  so **editor-only code must live there**.
- `Assets/6twelve/` is a third-party pack with its own DEMO scene. Not our code.
