# Rush Hour — what does not exist yet

```
Last verified against: working tree, 2026-08-17 (branch main, uncommitted)
Verification scope:    Written by file inspection and GUID scan on 2026-08-17, the day the quest
                       text landed. NOTHING HERE HAS BEEN COMPILED OR OPENED IN UNITY. Every
                       "does not exist" was checked against the tree; every "would behave like X"
                       is read from source and has not been run.
Owner:                 this file. The vape-arc guide routes here rather than repeating it.
```

Quest 8 is the first quest in the project that needs **new world, new mechanics and new art at the
same time**. The text is written and importable; nothing else about it exists. This is that list,
ordered so each item unblocks the next.

**Rule for everything below: the words are the owner's.** Where a line is owed, it is named as
owed and left blank. Do not draft it.

---

## 1 · Blocking — the quest cannot start without these

### 1.1 East York, the chunk

**Does not exist.** No `MapChunkData`, no prefab, not in `MapChunkRegistry` (which lists
seventeen). The guide's location table has it as `East York (0, -2)` — two chunks south of London
through `South_Slums`.

⚠️ **`ChunkName` is a save key from the first save made inside it.** Decide the string once, now,
while it is free. Note `Mosleys Lab Basement` uses spaces and `Manor Cellars` does too, while every
other chunk uses underscores — pick deliberately rather than by accident.

It is an **exterior**, which means two things the interior shells did not need:

- it has no `RuntimeNavMeshBaker` if it follows the other six exteriors, so it rides on
  `Assets/c/NavMesh.asset` and needs a bake;
- it needs chunk-edge adjacency wiring so `South_Slums` leads to it, which is the ordinary
  `MapChunkData` N/S/E/W path, not a portal.

### 1.2 The flats, west of East York

**Does not exist**, and it is not yet decided whether it is a chunk, an interior behind a portal,
or an open site inside East York itself. Zhao's line only says *"It's west from here."*

⚠️ **If it becomes an interior, it must not ship reward-bearing content until the location cache
lands** — `TravelRoutine` destroys and re-instantiates, so leaving and returning resets unsaved
NPC, enemy and chest state. See `BUILDING_INTERIORS_AND_LOCATION_CACHE_PLAN.md`.

### 1.3 Mayor Zhao

**No `PlacementPreset`, no `CharacterData`, no art.** `quests/rush_hour.quest` declares
`DIALOGUE mayorzhao`, so the importer will write `Dialogue_mayorzhao.asset` and then find no
preset to wire it to. It logs *"no preset matched"* and carries on — the asset is created and
nothing points at it.

Needed, in this order:

- [ ] Art subject `mayorzhao` through the usual pipeline — at minimum `idle`.
- [ ] `CharacterData` (an `NPC_MayorZhao.asset` beside the others in `Assets/Data/Dialogue/`) for
      the portrait and display name.
- [ ] `PlacementPreset` `Preset_MayorZhao`, with **`Speaker` set to that `CharacterData`**.
      ⚠️ Leaving `Speaker` empty is the trap that was just found on `Preset_Alex`: `ResolveSpeaker`
      falls back to the preset's own `Speaker`, so an empty one resolves to null and **every line
      loses its portrait and name silently.**
- [ ] `QuestKey` — only if a stage ever names him. Nothing does today.

### 1.4 `ProximityDialogueTrigger` — a new component

**Does not exist.** Every conversation in the project is opened by the player pressing USE on an
`Interactable`. Zhao's is meant to fire on approach.

The firing is easy — `ChunkEdge`, `InstanceDoor` and `TutorialExitGate` are three existing
`OnTriggerEnter` precedents to copy. ⚠️ **The re-fire is the hard part.** A chunk is destroyed and
rebuilt on every entry, so a plain "already seen" bool on the component **resets every time** and
Zhao ambushes the player forever.

**Recommended shape, which needs no new save field:** gate the trigger on quest state — fire only
while `rush_hour` is active *and* on stage 0. Reaching the marker advances the stage, which
disarms the trigger by itself and keeps it disarmed across saves, because quest state is already
serialized. A "seen it" flag in `SaveData` would work too but is an appended save field for
something quest state already knows.

Also needs deciding at implementation time:

- it must not fire while another conversation, a merchant window or a pause is open;
- it must not fire while the player is mounted (the portal path already refuses for this reason);
- whether it fires during combat.

### 1.5 The Red Star Workers Brigade

**No enemy prefab, no art subject, no `QuestActor.Key`.** Stage 1 is `MANUAL` precisely because it
is not yet written whether they are fought, talked down or paid off — so what they need depends on
a decision the owner has not made. If they are fought, that is a new art subject through
`Build Enemies From Generated Art`.

⚠️ **That tool rewrites every enemy prefab's YAML on its update path.** Run it on a clean tree,
then `git checkout -- Assets/Prefabs/Enemies/Enemy_UnderHoused.prefab`, which carries three
hand-added components it would strip.

---

## 2 · Built today, and what is still owed on each

### 2.1 `red_star_cigarettes` — created, needs an icon and a number confirmed

`Assets/Resources/Items/RedStarCigarettes.asset` now exists: Consumable, `Stackable`,
`MaxStack: 20`, `UseAnimationTrigger: Smoke`.

**The pack-of-20 works with no new C#**, and this is why: `InventoryController.UseTooltipItem`
refuses anything that is not `ItemType.Consumable`, calls `RemoveItem(item, 1)`, and only heals
where `HealHP`/`HealMana` are above zero. One USE spends one cigarette. `SnarlboroughCig` already
uses exactly this shape — the convention was there, this follows it.

- [ ] **`Icon` is `{fileID: 0}`** — it will draw as an empty slot in the bag and in the shop.
- [ ] **`HealMana: 15` and `Value: 18` are copied from `SnarlboroughCig`, not specified.** Flagged
      rather than invented. With mana no longer regenerating, a smokeable that restores mana is a
      real economy decision, not flavour.
- [ ] **`Description` is deliberately blank** — the owner's to write.

### 2.2 Use animations — set on the data, absent from the art

`UseAnimationTrigger` now reads `Smoke` on the three smokeables and `Consume` on ten edibles.
**Neither animation exists.** `PlayUseAnimation` checks the controller declares the trigger and
returns quietly otherwise, so this is inert and safe until the art lands — no console errors.

Owed to `docs/art/ART_QUEUE.md` as two new player actions:

- [ ] **`smoke`** — a puff, then a cough.
- [ ] **`consume`** — a simple hand to mouth.

⚠️ **No vape can play either.** `makeshift_vape`, `big_blue` and `cherry_mango_vape` are all
`Type: 8` (Quest), and `UseTooltipItem` refuses non-Consumables outright — so a vape is never
"used" and the trigger would never fire. If tooting a vape is meant to be possible, the item type
has to change first. Not changed here: `Type` is what decides whether it can be dropped, sold and
consumed, and that is a design call.

### 2.3 Alex — wired, unexercised

`quests/dialogue/alex.quest` now owns his conversation, gated three ways on `rush_hour`
(greeting → free hire → paid hire). See §3 for the machinery this needed.

- [ ] **The free branch is re-takeable.** Hire free, dismiss, and while `rush_hour` is still
      active the free branch is offered again. Accepted deliberately over an appended save field.
- [ ] **His pre-quest state is now a dead end** — he cannot be hired at all until Rush Hour is
      complete. That is a deliberate change from "hireable from the start" and is worth feeling in
      play before it is settled.

---

## 3 · Machinery added for this, never compiled

All four changes are additive. **None has been through a compiler** — a brace-balance scan is not
a compile.

| What | Where | Risk |
|---|---|---|
| `DialogueChoice.HireCompanionFree` | `Scripts/Data/DialogueData.cs` | Appended field, initializer `false`. Every existing choice deserializes exactly as before. |
| `TryHireCompanion(id, free)` | `Scripts/Dialogue/DialogueManager.cs` | Passes the flag to `BeginContract`, which already took a `free` parameter nothing used. The "not enough money" toast is now suppressed on a free hire, where it would be a lie. |
| `HIRE: <id> [free]` | `Editor/QuestTextImporter.cs` | New directive, same shape as `MERCHANT:`. A second word other than `free` is an error, not a silent drop — a dropped `free` would charge for a gift and log nothing. |
| `HIRE:` validation | `Editor/QuestContentValidator.cs` | Errors outside a CHOICE, and resolves the companion id against `Resources/Companions` so a typo is caught at import rather than mid-conversation. |

### 3.1 The case-collision that was defused first

`Dialogue_Alex.asset` was renamed to `Dialogue_alex.asset` on 2026-08-17 — `git mv` in two hops,
`.meta` moved with it, **GUID unchanged** (`750c809e…`), `m_Name` aligned.

Without that rename, `DIALOGUE alex` would have targeted `Dialogue_alex.asset` in a folder already
holding `Dialogue_Alex.asset`, which is **exactly the bug that nulled `Preset_CouncillorMosley`
and `Preset_Scrapman`** in August. `QuestTextImporter.ResolveAssetPath` was written to survive it
and **has never run**; this removes the need to find out on the one companion conversation known
to work.

⚠️ **`Dialogue_Alex_Follower.asset` is still PascalCase in the same folder.** Nothing targets it
today. A future `DIALOGUE alex_follower` block would hit the same collision — rename it the same
way first, or leave follower dialogue out of the pipeline.

### 3.2 `Preset_Alex.Speaker` was empty and is now set

It resolved to null, so importing Alex's dialogue would have **stripped every line's portrait and
display name** with nothing logged. Now points at `NPC_Alex`. One line changed in the asset.

---

## 4 · Still undecided — questions, not tasks

- [ ] **How does Zhao hand over the cigarettes?** A `DialogueChoice`'s `ITEM:` is a *requirement*,
      not a grant; the only item payout that exists is a quest `REWARD`, which pays at completion.
      Either a `GIVE:` directive (the mirror of `HIRE:`, small) or a container at his feet. Until
      then he says *"Take this for help!"* and gives nothing.
- [ ] **How do the squatters resolve?** Stage 1 is `MANUAL` until this is answered.
- [ ] **Zhao's second conversation** — honouring the bargain, pointing at Ralph and Sanjeet.
- [ ] **Does Rush Hour grant a Quest 9?** `rush_hour.quest` has no `COMPLETE:` route yet.
- [ ] **Does `£`/curly punctuation render?** The £ glyph question is open (CLAUDE.md §5 item 9) and
      the same applies to any smart quote. The owner's prose was normalised to straight quotes and
      apostrophes on the way in, which sidesteps it for these items.

---

## 5 · The one-run check, once East York exists

In order, in one editor session:

1. `Tools → Content → Validate Quests` — expect the new `HIRE:` line to pass, and a
   *no preset matched* warning for `mayorzhao` until his preset exists.
2. `Tools → Content → Import Quests` — expect 8 `QuestDefinition`s (was 7) and
   `Dialogue_alex.asset` **keeping GUID `750c809e…`**.
3. Open `CompanionHome_Alex.prefab` and confirm its `Conversation` still resolves. If it shows as
   missing, the rename did not survive and that is the thing to fix before anything else.
4. Talk to Alex before Rush Hour: **one choice, "Hey up.", no hire offer.**
5. Take Rush Hour, talk to Alex: the deal plays, he joins, **and no pounds are spent.**
6. Complete Rush Hour, dismiss him, talk again: **"Come with me .. chap" charges £25.**
