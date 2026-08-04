# Quests and dialogue

```
Last verified against: ccfa9c9
Verification scope:    code; tracked dialogue/preset YAML (15 DialogueData assets read). A
                       single-stage Kill quest was exercised in the editor, including reward
                       payment and persistence across an autosave, verified by reading
                       savegame.json. The three quest fixes on main POSTDATE that session.
                       TalkTo, Collect, Reach and Manual have NEVER been exercised, and neither
                       has any multi-stage quest.
```

## Current content state

- **There are zero `QuestDefinition` assets.** `Assets/Resources/Quests/` holds only a README.
  The quest system is **inert** until someone authors one.
- **15 `DialogueData` assets exist**, in `Assets/Data/Dialogue/Generated/`, one per NPC, wired to
  15 of the 34 presets.
- **Every one of them is a single node with zero choices** — an ambient one-liner. So the cast
  talks; it does not branch.
- **No `GrantQuestId` exists anywhere**, so nothing can grant or complete a quest through dialogue.
- `escape_manor` and `spark_of_talent` run on bespoke tutorial code, not on this system.

⚠️ **Quest and dialogue writing is the owner's own work.** Build the machinery, leave the words.
The v1 quest cast was deleted deliberately so the quests could be written from scratch. Do not
generate NPC dialogue or quest prose unless asked — an empty slot is obviously unfinished, and
filler looks done.

---

## Data-authored quests

Dialogue *starts* a quest (`DialogueChoice.GrantQuestId`) and, for a hand-in, *finishes* it
(`CompleteQuestId`). A `QuestDefinition` adds the middle — ordered stages with objective text, a
condition per stage, and one reward on completion.

| Piece | File | What it owns |
|---|---|---|
| What a quest *is* | `Data/QuestDefinition` | `Id`, title/giver/location, the `QuestStage` list, one `QuestReward`. |
| Finding one | `Data/QuestDatabase` | `Find(id)` over `Resources/Quests`. |
| Watching one | `Quests/QuestConditionWatcher` | Binds the active stage's condition, advances it, pays the reward. Self-bootstraps. |
| Where stage state lives | `Quests/QuestManager` | `QuestProgress.StageIndex` / `StageProgress` / `RewardsClaimed`, plus `SetStage` / `SetStageProgress`. |

**The containment rule is the whole safety argument. `QuestConditionWatcher` is completely inert
for any quest id with no definition asset.** `QuestDatabase.Find` returns null and every path bails
out. `escape_manor` and `spark_of_talent` deliberately have no definition, so `GameFlowController`,
`TutorialSequence` and `MagicTutorial` are untouched. **Do not author a definition for either
tutorial quest** without working out what happens to the bespoke code that already drives it.

| `QuestConditionType` | Bound to | Advances when |
|---|---|---|
| `TalkTo = 0` | `Interactable.OnInteract` on the `QuestActor` keyed `QuestKey` | the player interacts |
| `Kill = 1` | `Health.OnDeath` on every `QuestActor` keyed `QuestKey` | `Count` of them have died |
| `Collect = 2` | `PlayerSession.OnInventoryChanged` | **never — see below** |
| `Reach = 3` | nothing; polled | the player is within `ReachRadius` (X/Z) of the keyed `SceneMarker`, or of a `QuestActor` if no marker matches |
| `Manual = 4` | nothing | never — bespoke code calls `CompleteQuest` itself |

**Serialized by index. Append only.**

### `Collect` tracks and reports; the hand-in is dialogue's job

A `Collect` stage never completes the quest, consumes the item, advances the stage or pays a
reward. It swaps `Objective` for `ObjectiveWhenMet` once the player is carrying enough — and swaps
it back if they drop or sell it, which is why the text is *derived from the inventory every time*
rather than toggled once.

The hand-in is `DialogueChoice.RequiredItem` + `RequiredItemQuantity` (greys the choice out),
`ConsumeRequiredItem` (takes the stack) and `CompleteQuestId` (ends the quest).

⚠️ **A `Collect` stage in a quest that no dialogue anywhere completes can never end**, and nothing
checks that for you: dialogue assets live outside `Resources/`, so they cannot be enumerated at
runtime. The watcher does warn if a `Collect` stage is not the last stage.

### Rewards

Scanned by **completion state**, not by "did I just complete this". Any quest that is
`IsComplete && !RewardsClaimed` and has a definition gets paid, so a quest finished purely through
dialogue is rewarded identically to one the watcher advanced.

`Reward.Item` goes through `PlayerSession.AddItem`. `ClearsWantedLevel` calls
`WantedManager.ClearWanted()`. **`Reward.GoldAmount` warns and pays nothing** — there is no gold
system.

**A reward is claimed only once it has actually been paid.** `ApplyReward` returns a bool: it
checks every manager it needs *before* handing anything over, and pays nothing at all if one is
missing, so the caller leaves `RewardsClaimed` unset and the next `Update` retries. Checking up
front rather than half-way is what makes the retry safe — a partial payment followed by a retry
would grant the item twice. An authored `Quantity` of 0 warns and *claims*, since it can never pay.

### Things that will catch you out

- **All quest-state mutation happens in `Update()`.** Event callbacks only set a flag or bump a
  counter. A `QuestManager` call from inside an `OnInteract` / `OnDeath` listener raises
  `OnQuestsChanged`, which rebinds listeners, from inside the listener list being invoked. **Do not
  "simplify" the indirection away.**
- **`Update` runs while the game is paused.** `PauseManager` only zeroes `Time.timeScale`, which
  stops `FixedUpdate`, not `Update`. That is why the reward scan defers while
  `DialogueManager.IsDialogueOpen`: `OnChoiceSelected` runs grant → complete → *consume the
  handed-over item* in that order, and a reward applied the instant completion landed would fall
  inside a half-finished hand-in.
- **Only the *first* active quest is watched.** The watcher binds `QuestManager.GetActiveQuest()`.
  Two quests active at once means the second one's conditions are not watched at all. A real
  limitation, not a subtlety.
- **Every rebind is a full teardown first.** A `Health` subscribed twice counts one death as two.
  Unbinds null-check each entry, because a `Health` destroyed with its chunk is Unity's fake null.
- **Chunk changes are polled**, against remembered `CurrentChunkData` *and* `CurrentChunkInstance`.
- **`Kill` targets respawn with their chunk.** The count is seeded from `StageProgress` so it
  survives a crossing, but the actors are re-instantiated fresh — so a "kill 3" stage can be
  finished by killing one respawning actor three times. **Author kill stages against targets in a
  single chunk.**
- **`SetStageProgress` deliberately raises no `OnQuestsChanged`.** Nothing renders `StageProgress`.
- **Re-granting a quest no longer rewinds its objective.** `StartQuest` only refreshes the
  objective while `StageIndex` and `StageProgress` are both 0.
- **`Resources/Quests/` ships in the build.** **Never add a `GameObject`, `Sprite`, `Prefab` or
  `AudioClip` field to `QuestDefinition`** — one prefab reference drags its whole dependency graph
  in. `ItemData` is already Resources-resident and is the only asset reference a definition may
  hold.

### Open issues, found in review and not fixed

None of these can corrupt a save.

- ⚠️ **`Stages[0].Objective` is never displayed.** The opening objective comes only from
  `DialogueChoice.GrantQuestObjective`, which has no empty-string fallback, and nothing reads the
  first stage's `Objective`. Leave that dialogue field blank and the HUD tracker shows an **empty
  objective line** until stage 0 completes. `QuestDefinition`'s tooltip claims otherwise and is
  wrong. **Always fill in `GrantQuestObjective` on the granting choice**, identical to
  `Stages[0].Objective`.
- ⚠️ **A `TalkTo` final stage completes the quest on the interact, before any choice is picked.**
  `Update` runs while paused, so the advance lands a frame after the dialogue panel opens. If that
  NPC also carries the hand-in, the player walks up, presses Interact, backs out — and keeps the
  item, gets the reward, and hands nothing over. **Author hand-ins as `Collect` last + dialogue
  completes**, never `TalkTo` last against the hand-in NPC. Nothing warns.
- **`QuestDefinition.Title` / `Giver` / `Location` are dead fields.** The journal reads
  `QuestProgress.Giver`/`.Location`, from the dialogue speaker name and `GrantQuestLocation`.
- **The second active quest is invisible as well as unwatched.** `QuestTrackerUI` uses the same
  `GetActiveQuest()`, and `_quests` is insertion-ordered and never compacted.
- **A kill can be dropped if a rebind lands in the same frame.** `Rebind` runs before
  `ApplyPending`, and `BindKill` re-seeds from `StageProgress`, one frame behind. Rare.
- **`Assets/Resources/Quests/README.txt` ships in the build** as a `TextAsset`. 16 lines, so the
  cost is nil, but move it to `docs/` when convenient.

---

## Dialogue graphs

**The format is flat.** `DialogueData.Nodes` is a `List<DialogueNode>`; each node carries a string
`Id`. `DialogueChoice.NextNodeId` names the node a choice leads to. `DialogueData.StartNodeId`
(default `"start"`) names the opening node; `StartNode()` resolves it, falling back to `Nodes[0]`
and warning if `StartNodeId` is set but matches nothing. `FindNode(id)` is a linear scan,
deliberately.

**An empty or null `NextNodeId` is the only way a conversation ends.**

It used to be a tree stored *by value* — `NextNode` was a nested `DialogueNode` — which made two
problems structural: no two choices could converge on the same node, and Unity 2022.3's nested
serialization depth caps at 7, which a branching conversation burns through in three exchanges.

⚠️ **The authoring surface is NOT exercised.** No `DialogueData` asset has ever been hand-authored
with choices, convergence and cycles have never run, and the traps below were found by review, not
by play. Every one of them lands on the first person to write a branching conversation.

### Authoring traps

- **Convergence is the point, and cycles are legal — but a cycle with no exit freezes the game.**
  `EndDialogue()` is private with two call sites, both inside `OnChoiceSelected`; there is no
  Escape handler, no close button, and `PauseManager` holds `Time.timeScale` at 0 throughout. So a
  conversation ends only via a choice with an empty `NextNodeId`, an unresolvable id, or the
  auto-generated "End conversation." button on a node with **no choices at all**. Author
  `hub → shop → hub` and forget a farewell, and the only way out is force-quitting.
  **Rule: every cycle must contain at least one ungated choice that ends the conversation.**
  The same freeze is reachable without a cycle: a node whose only choice is `RequiredStat`- or
  `RequiredItem`-gated renders `interactable = false` with no other button.
- ⚠️ **An unset `Id` or `NextNodeId` silently means "end the conversation".** Unity serializes an
  unset string as `""`, and `IsNullOrEmpty` is the legitimate terminator — so a hand-authored node
  whose short string fields were never filled in looks fine, shows every choice button, and closes
  the chat on any of them, with everything below it unreachable and **nothing logged**. A *typo'd*
  id warns loudly; an *unset* one says nothing.
- **A duplicate `Id` is an authoring error nothing validates.** `FindNode` returns the first match;
  every other node sharing that `Id` is silently unreachable. ⚠️ Suspected and worth a minute in
  the editor: Unity's list `+` button duplicates the **last element**, which would make a duplicate
  `Id` the *default* outcome of adding a node — and would copy the source node's whole `Choices`
  list, including any `GrantQuestId` / `CompleteQuestId` / `ConsumeRequiredItem` side effects.
- ⚠️ **A choice with `ConsumeRequiredItem` must never be reachable twice.** `RemoveItem` runs
  unconditionally whenever a selectable choice is picked, while `CompleteQuest` early-returns once
  complete. Hand over 5 at a hub, loop back carrying 10, and picking it again destroys 5 more,
  completes nothing, and reports nothing.
- **The twelve `DialogueChoice` side-effect fields are a save/quest contract** and must not be
  renamed without the usual serialized-field treatment: `RequiredStat`, `RequiredStatLevel`,
  `RequiredItem`, `RequiredItemQuantity`, `ConsumeRequiredItem`, `GrantQuestId`, `GrantQuestTitle`,
  `GrantQuestObjective`, `GrantQuestLocation`, `TeachSpark`, `CompleteQuestId`, `ChoiceText`.

### The two safety nets

Both compile and the tutorial plays through unchanged, but **neither has been shown to do its
job.** The 15 existing assets are single nodes with no choices, so none can hold a cycle, a
dangling id, a duplicate or an inescapable node. Treat both as untested the first time a
**branching** conversation goes through them.

- **`DialogueManager.CanEscapeFrom`** is a BFS over *currently pressable* choices from the node
  being displayed, looking for anything that ends the chat. If none is reachable, `DisplayNode`
  appends an "End conversation." button the author did not write. It is a **safety net, not an
  authoring feature** — a graph that needs it is still wrong. Gating is judged as it stands rather
  than structurally, because within one conversation the player's position only gets worse. The
  visited set is keyed on **node identity, not `Id`**, because duplicate ids are legal-but-broken.
- **`Assets/Editor/DialogueValidator.cs`** — `Tools/GBA/Content/Validate Dialogue`, plus
  `CONTEXT/DialogueData/Validate This Conversation`. Errors: no nodes, a node with no `Id`, a
  duplicate `Id`, a dangling `NextNodeId`, a node with no route out. Warnings: an unresolvable
  `StartNodeId`, an unreachable node, a node whose every exit is gated, a `ConsumeRequiredItem`
  choice inside a cycle. **`Validate` is public and UI-free on purpose** — a plain-text importer is
  meant to call it and refuse a bad script. Keep it that way.

### `MagicTutorial` builds five conversations at runtime

`_intro`, `_nudge`, `_reward`, `_done`, `_underHousedTalk`, via local helpers that assign each node
an id automatically and collect them into the enclosing `Tree(...)`'s `Nodes` list. This relies on
C# evaluating method arguments left-to-right and fully before the enclosing call runs.

**Keep every `Node()` call inside the `Tree(...)` argument list it belongs to** — a `Node()` called
outside that expression, or a second `Tree(...)` started before the first one's nodes are drained,
would misfile nodes between conversations.

### `PresetDialogueTools` and overwriting

- **It no longer overwrites existing dialogue text at all.** `WriteConversation` adopts whenever
  any node already carries prose. Regenerating an orphan means deleting it by hand; that is the
  right way round, since the alternative destroys writing silently.
- **`HasAuthoredContent` cannot see a hand-edited one-liner.** A conversation rewritten as a single
  node with no choices is byte-for-byte the same shape as generator output. Reaching that needs
  `preset.Conversation` to be null first, so the route is narrow — but if you improve a line by
  editing the asset rather than the preset's `AmbientLine`, **update `AmbientLine` to match**, or
  add a second node.
- ⚠️ **That does not save you on the right-click route.** `CONTEXT/PlacementPreset/Create Dialogue`
  passes `""` when `AmbientLine` is blank, so it can overwrite prose with an **empty string** — the
  guard is structural and never sees the line.
- **`PathFor` keys the generated asset on the preset's filename only, not its path**, so two
  same-named presets in different folders would share one `Dialogue_<Name>.asset`. Unreachable
  today — all 34 presets are flat in `Assets/Data/Presets/`.
- **Adopting an existing conversation mutates the preset but is reported as nothing.**
  `EnsureAmbientConversation` returns false on the adopt path, and
  `StarterPresetGenerator.GenerateAmbientConversations` only lists presets when the return is true.
  The end-of-run summary omits that a preset was just wired to a conversation.
- ⚠️ **`Create Starter Presets` runs `GenerateAmbientConversations` over *every* preset.** It bails
  when `Conversation` is already set **or** `AmbientLine` is blank. **Fill in a blank `AmbientLine`
  and the next run of that tool will generate that character's dialogue.** Leave it blank until the
  owner's own conversation is attached.

### No `[SerializeReference]`

Considered and rejected: it serializes the target's assembly + namespace + class name into the
asset, and there is an open intention to rename the `ExiledAlvaston` namespace across 46 files —
introducing it here would make that rename silently null every dialogue link. It also produces
opaque `rid:`-keyed YAML with no Inspector support for polymorphic references. Per-node sub-assets
and integer indices into `Nodes` were rejected too: reordering silently repoints edges, and a
future plain-text importer wants to write `-> shop`, not `-> 7`.
