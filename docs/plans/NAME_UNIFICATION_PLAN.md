# Name Unification Plan — everything becomes GBH: England

```
Last verified against: working tree, 2026-08-16 (commit c3b5a38)
Verification scope:    Every claim below is from a grep of the tracked tree. The hazard survey
                       (SerializeReference, asmdef, m_EditorClassIdentifier, Type.GetType,
                       m_TargetAssemblyTypeName) was run and is reproduced with counts. NOTHING has
                       been changed yet and NOTHING has been compiled — there is no C# compiler or
                       Unity in the agent environment. This is a plan, not a result.
```

## The decision this reverses

`CLAUDE.md` §1 and `AGENTS.md` currently state the three live names are **"deliberately not
unified"**. The owner has reversed that: **`GBH: England` is the official name**, and the old ones
come out where they can. Those two sections are now decision records that are wrong, so they get
**rewritten, not find-replaced** (docs rule §7: replace a stale statement).

Owner's answers, 2026-08-16:
- **`productName` → change, accepting save loss.** No migration shim.
- **Namespace → full rename** to `GBHEngland`.

## What the survey actually found

### "GBA: England" does not exist

There is **no `GBA: England`, `GBA England` or `GBA:England` anywhere in the tree.** The only
matches for a bare `GBA` token are byte sequences inside two binary `.glb` models. **Nothing to
remove.** (Standing rule, unchanged: never sweep the bare token `GBA` — it lives inside `RGBA`.)

### "Exiled Alvaston" / "ExiledAlvaston" — the real surface

| Where | Count | Risk |
|---|---|---|
| `.cs` namespace decls | 115 files | Safe — see hazard survey |
| `.cs` `using` statements | 243 lines | Safe |
| `.cs` `CreateAssetMenu` menuName | 15 | Cosmetic — menu location only |
| `.cs` total (all forms) | 147 files / 473 lines | — |
| **`m_TargetAssemblyTypeName` in prefabs/scene** | **3** | ⚠️ **Silent breakage if missed** |
| `ProjectSettings.asset` | 3 lines | ⚠️ **Save-path breaking** |
| `.md` docs | 15 files | Safe |
| `README.txt` in `Resources/` | 2 | Safe |
| `Tools/*.py` hardcoded paths | 2 files | Dead paths, safe |

### Hazard survey — why the namespace rename is safer than it looks

A namespace rename is normally frightening in Unity because several things store a namespace as a
**string** rather than a GUID. All of them were checked:

| Hazard | Result |
|---|---|
| `[SerializeReference]` (stores `assembly namespace class`) | **0 uses** — the big one is absent |
| `.asmdef` files (assembly name in type strings) | **none** — everything is `Assembly-CSharp` |
| `m_EditorClassIdentifier` populated in assets | **0 of 227** — all blank |
| `Type.GetType` / `AddComponent("Name")` | **0 uses** |
| `m_TargetAssemblyTypeName` (UnityEvent targets) | ⚠️ **3 — must change in lockstep** |

Script bindings in prefabs and the scene are `{fileID: 11500000, guid: …}` — **GUID-based and
namespace-independent**. A namespace change does not touch them. Unity requires the *class* name to
match the *file* name; it has never required the namespace to match anything.

**So the entire risk of the namespace rename reduces to three lines**, all of which store the
namespace as a literal string in a `UnityEvent` persistent call:

| File | Stored string |
|---|---|
| `Assets/Prefabs/ModernBritain/EBike.prefab` | `ExiledAlvaston.World.VehicleController, Assembly-CSharp` |
| `Assets/Prefabs/ModernBritain/Pub_TheWinchester.prefab` | `ExiledAlvaston.World.PubInteractable, Assembly-CSharp` |
| `Assets/c.unity` | `ExiledAlvaston.UI.InventoryController, Assembly-CSharp` |

⚠️ **If one of these is missed, nothing throws.** The UnityEvent silently resolves to nothing: the
e-bike stops responding, the pub stops pouring, an inventory button stops working — with a clean
console. This is exactly the silent-failure class `CLAUDE.md` §3 exists to guard.

## ⚠️ The one irreversible thing: `productName`

`SaveGameManager.SavePath` is `Path.Combine(Application.persistentDataPath, "savegame.json")`, and
on Windows `persistentDataPath` is `%USERPROFILE%\AppData\LocalLow\<companyName>\<productName>`.

**Changing `productName` moves the save folder.** Every existing `savegame.json` is orphaned —
nothing errors, nothing logs, the game simply starts as if it had never been played. `PlayerPrefs`
(where `GraphicsPrefs` stores quality and shadows) is keyed the same way and is orphaned with it.

Owner has accepted this: the arc isn't playable yet, so there is no save worth keeping. **This is
the free moment** — it stops being free the day a real playthrough exists.

⚠️ **Use `GBH England` — no colon — for `productName`.** A colon is an illegal path character on
Windows/NTFS, and `productName` becomes a real directory name. `EKVibe.DisplayTitle` keeps the
colon: `"GBH: England"` is what the player reads, and it is not a path.

| Field | From | To |
|---|---|---|
| `productName` | `Exiled Alvaston` | `GBH England` |
| `metroPackageName` | `Exiled Alvaston` | `GBH England` |
| `metroApplicationDescription` | `Exiled Alvaston` | `GBH England` |
| `companyName` | `DefaultCompany` | *unchanged — also part of the save path; changing it too doubles the orphaning for no gain* |
| `EKVibe.DisplayTitle` | `GBH: England` | *unchanged — already correct* |

## Mapping table

| Old | New | Applies to |
|---|---|---|
| `ExiledAlvaston` | `GBHEngland` | C# namespace, `using`, the 3 UnityEvent strings |
| `"ExiledAlvaston/Data/…"` | `"GBH England/Data/…"` | 15 `CreateAssetMenu` menuName paths |
| `Exiled Alvaston` | `GBH England` | `productName` + 2 metro fields |
| `Exiled Alvaston` / `Discover England` | `GBH: England` | prose in docs and comments |
| `GBA: England` | — | **does not exist; no action** |
| `EK*`, `Exiled Kingdoms` | — | **out of scope — see Phase 5** |

⚠️ **Order matters in the `.cs` sweep.** The menuName strings contain the token `ExiledAlvaston`
too, but take a *different* replacement (`GBH England`, with a space). **Do the 15 menuName paths
first, then the bare-token sweep** — otherwise they become `GBHEngland/Data/…` and land in the wrong
Create-menu folder.

## The phases

Each is one commit, each independently revertible.

### Phase 1 — Cosmetics (zero risk, no compile needed)

- 15 `.md` docs. `CLAUDE.md` §1 and `AGENTS.md` are **rewritten** to record that the name is now
  unified, not find-replaced.
- `docs/reference/REPO_HYGIENE.md` — its naming table is a decision record; rewrite it.
- 2 × `Resources/**/README.txt` — the `Create >` path they quote.
- 2 × `Tools/*.py` — dead hardcoded `C:\Users\P50\Desktop\Exiled Alvaston\…` paths.
- `Discover England` in code *comments* and the title-screen label in `DiscoverEnglandSetup.cs:311`.
- Leave `docs/archive/` and completed `docs/plans/` alone — they are historical records.

### Phase 2 — `CreateAssetMenu` paths (low risk)

15 menuName strings → `GBH England/Data/…`. **Existing assets are unaffected** — menuName only
decides where the `Create` menu item sits. Do this before Phase 3 (see the order warning above).

### Phase 3 — The namespace (the big one)

- `ExiledAlvaston` → `GBHEngland` across 147 `.cs` files (115 namespace decls, 243 usings).
- **The 3 `m_TargetAssemblyTypeName` strings in the same commit.** Non-negotiable — they are the
  only silent-failure path here.
- Verify with `git grep -c ExiledAlvaston -- '*.cs' '*.prefab' '*.unity'` → must be **0**.
- Run `python Tools/asset_reachability.py --check-dangling` → must stay exit 0. ⚠️ This proves GUIDs
  resolve and **says nothing about whether the code compiles**.

### Phase 4 — `productName` (irreversible for saves)

The 3 `ProjectSettings.asset` lines. **Its own commit**, so it can be reverted alone if the new save
folder turns out wrong.

### Phase 5 — `EK*` and `Discover England` identifiers — recommend deferring

`EKVibe` (45 files) and `EKNavMeshBaker` are both `static class` — no GUID binding, no
`MonoBehaviour` — so renaming them is mechanically trivial. They are **deliberately excluded**
anyway:

- `EK` marks *Exiled Kingdoms*, the **inspiration game** — a lineage note, not a stale title of
  this project. It is not a wrong name in the way `Exiled Alvaston` is.
- `EKVibe` is the tuning-constants class named in `CLAUDE.md` §2 as the canonical home for every
  magic number. Renaming it churns 45 files and every future instruction that mentions it.
- Renaming `EKNavMeshBaker.cs` / `DiscoverEnglandSetup.cs` means renaming files, which means their
  `.meta` must move with them (`git mv`) — the one thing in this whole plan that can mint a fresh
  GUID and orphan a reference.

**Recommendation: leave Phase 5. Ask before doing it.** The player never sees `EKVibe`.

## Verification — and its hard limit

Mechanical, runnable here:

```bash
python Tools/asset_reachability.py --check-dangling
```

```bash
git grep -c "ExiledAlvaston" -- "*.cs" "*.prefab" "*.unity" "*.asset"
```

⚠️ **Neither is a compile.** `--check-dangling` proves GUIDs resolve; a zero grep proves the sweep
was complete. **Nothing here proves the project builds.** A namespace rename that misses a single
`using` is a compile error, and this environment cannot see it.

**The plan therefore ends at "pushed and unverified."** Confirm in Unity:

1. **It compiles.** Console clean on first open after the rename. This is the whole gate.
2. **The e-bike.** Mount it — `VehicleController`'s UnityEvent target string changed.
3. **The Winchester.** USE it — `PubInteractable`'s target string changed. (Note the pub prefab is
   not placed in any chunk, so this may need placing first.)
4. **The bag.** Open it and click the rebuilt buttons — `InventoryController`'s target string
   changed, and this one is in `c.unity` itself.
5. **The Create menu.** `Create → GBH England → Data → Item Data` exists and makes a working
   `ItemData`. Existing items still open fine in the Inspector.
6. **A save is written to the new folder.** After Phase 4, play once and confirm
   `…/LocalLow/DefaultCompany/GBH England/savegame.json` appears. The old
   `…/Exiled Alvaston/` folder is now dead — delete it by hand if you want it gone.
7. **Graphics settings reset once.** Expected, not a defect: `PlayerPrefs` moved with `productName`.

Items 2–4 are the ones that fail **silently**. If any is dead, its `m_TargetAssemblyTypeName` string
did not get rewritten — that is the first place to look, not the C#.
