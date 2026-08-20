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

`retro_house_pack` (0 / 59, 36 MB) was fully unreferenced — not "partial" as this table once said —
and has been deleted entirely, along with the four `Assets/Materials/RetroHouses/*.mat` that
pointed into it.

**Biggest remaining trim: `Animated Chest` — 45 MB for one decorative prop**, almost all
uncompressed TGA. It is committed only because `c.unity` references its `Chest.prefab`. Delete the
chest instance in the Unity editor and the whole pack goes with it. Next largest unreferenced:
`psx urban pack` (105 MB), `Characters_psx` (54 MB), `Magic+atk animations` (50 MB).

`Assets/3DModels/Sprites/` was deleted (1,998 files, 454 MB — the craftpix packs) after verifying
zero of its 2,123 assets were referenced. **Policy going forward: pull individual sprites in when a
system needs them, rather than carrying whole packs speculatively.**

Reference integrity carries three known dangling references, tracked deliberately in
`KNOWN_DANGLING` inside `Tools/asset_reachability.py` rather than silently tolerated: three
`Visual` SpriteRenderers with a missing `m_Sprite` (see CLAUDE.md §5). `--check-dangling` passes
clean only because these three are on the allow-list — anything not on it fails the run. No
tracked `__MACOSX` junk file remains.

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

**The name is `GBH: England`, and it is now unified.** The old working title `Exiled Alvaston` and
the older `Discover England` were swept out on 2026-08-16 — see
[docs/plans/NAME_UNIFICATION_PLAN.md](../plans/NAME_UNIFICATION_PLAN.md) for the survey and the
phase breakdown.

| Form | Where | Note |
|---|---|---|
| `GBH: England` | `EKVibe.DisplayTitle`, all prose | The player-facing title. Use the constant, not a literal |
| `GBH England` | `productName`, `metroPackageName`, `metroApplicationDescription` | **No colon** — `productName` becomes a real directory in `persistentDataPath` |
| `GBHEngland` | root C# namespace | One word — a C# identifier cannot hold a space or colon |
| `GBH England/Data/…` | `CreateAssetMenu` menu paths | Where `Create →` items sit |
| `gba-england` | the repo and its folder | Unchanged — a colon is illegal in paths and repo names |
| `EK` / Exiled Kingdoms | `EKVibe`, `EKNavMeshBaker` | **Deliberately kept.** Marks the *inspiration* game, not a stale title of this one |

⚠️ **`productName` is part of the save path.** `Application.persistentDataPath` is
`…/LocalLow/<companyName>/<productName>`, so changing it again silently orphans every save and all
`PlayerPrefs`. It was changed once, on 2026-08-16, when there was no save worth keeping. There is no
migration shim. `companyName` stays `DefaultCompany` for the same reason.

⚠️ **Three serialized files hold the namespace as a literal string**, in `m_TargetAssemblyTypeName`
(a `UnityEvent` persistent-call target): `EBike.prefab`, `Pub_TheWinchester.prefab` and `c.unity`.
They are **not** GUID-bound like normal script references, so any future namespace change must
rewrite them in lockstep — a miss breaks the binding with a clean console and no error.

*(An earlier version of this section claimed the namespace touched "46 `.cs` files and zero
serialized assets". Both numbers were wrong: it was 147 files, and those three assets. The grep that
found them is recorded in the plan.)*

## Structure facts worth knowing

- **There is one gameplay scene: `Assets/c.unity`.** Renaming it orphans `Assets/c/NavMesh.asset`,
  which is auto-linked by scene name.
- **No `.asmdef` files exist** in project code — everything compiles into `Assembly-CSharp` /
  `Assembly-CSharp-Editor`. `Assets/Editor/` is the only thing keeping editor code out of builds,
  so **editor-only code must live there**.
- `Assets/6twelve/` is a third-party pack with its own DEMO scene. Not our code.
