# Quest text format — authoring quests as plain text

```
Last verified against: working tree, 2026-08-15
Verification scope:    code + format. The importer (Assets/Editor/QuestTextImporter.cs) and
                       validator (Assets/Editor/QuestContentValidator.cs) are written and
                       brace-balanced but have NEVER been compiled or opened in the editor. Real
                       .quest files now exist under quests/ — five quests plus two quests/dialogue/
                       conversations — but nothing in this pipeline has been imported, so the parser
                       and validator have never run against them. On 2026-08-15, traced by hand not
                       run: the validator's cross-file pass (GRANT:/COMPLETE: gathered across quests/
                       and quests/dialogue/) was corrected, and multi-item COLLECT (a STAGE COLLECT
                       carrying several item pairs) was added to the importer, QuestStage and the
                       watcher.
                       See docs/plans/QUEST_PIPELINE_PLAN.md.
```

## The point

One `.quest` file on disk is one quest, end to end: the `QuestDefinition` (stages, conditions,
reward) **and** the dialogue that grants / advances / completes it. `Tools → Content → Import
Quests` turns the file into assets. You write the file in any text editor; you do not need Unity
open.

**The text file is the source of truth.** Re-importing regenerates the assets wholesale, so a
hand-edit made in the Unity Inspector to a file-backed quest is overwritten on the next import.
Writing lives in the text file, never only in the asset. This is the deliberate opposite of
`PresetDialogueTools`, which never overwrites prose — that tool guards hand-written assets; this
pipeline owns its assets through the file.

**Prose rule (CLAUDE.md): the owner writes the words.** The format carries prose, but a scaffold
should leave `[TODO: ...]` slots, not finished lines. The importer builds structure and wiring;
it does not invent dialogue.

Files live in the repo-root `quests/` folder — git-tracked, diffable, **outside `Assets/`** — so
nothing half-written ships in a build and Unity never imports the raw text.

## Two kinds of file

| Folder | Holds | Rule |
|---|---|---|
| `quests/*.quest` | one `QUEST` block, plus any `DIALOGUE` blocks | must declare a quest |
| `quests/dialogue/*.quest` | `DIALOGUE` blocks only | must **not** declare a quest |

**One `DIALOGUE <npcId>` block may exist across the whole folder tree.** Each import regenerates
`Dialogue_<npcId>.asset` wholesale, so two files declaring the same npcId clobber each other in
file order. An NPC who appears in several quests therefore keeps **every** line they say in one
file under `quests/dialogue/`, with branches gated per quest id — that is what this folder exists
for. A quest file may still carry its giver's conversation inline when that NPC appears in nothing
else.

The split is a separate folder rather than "a file with no QUEST block is a dialogue file" on
purpose: a quest file whose `QUEST` line is lost to a typo must stay an **error**, not be silently
reinterpreted as a conversation.

Dialogue files are imported first, so a preset's `Conversation` is already wired by the time its
quest lands. Their `GRANT:` and `COMPLETE:` ids take part in the same cross-file check as any
other, so a conversation may grant or complete a quest defined anywhere.

## File layout

```
QUEST <id>
TITLE: <text>
GIVER: <text>
LOCATION: <text>
STAGE <condition...>
OBJECTIVE: <text>
STAGE <condition...>
OBJECTIVE: <text>
WHENMET: <text>
REWARD
POUNDS: <int>
XP: <int>
ITEM: <itemId> x<qty>
CLEARSWANTED

DIALOGUE <npcId>
NODE <nodeId>
SPEAK: <line>
CHOICE <text> [-> <nodeId>]
GRANT: <questId>
NODE <nodeId>
...
```

- Keywords are UPPERCASE and start the line (leading whitespace is ignored).
- `#` starts a full-line comment.
- `KEY: value` splits on the first colon; the value is the trimmed remainder, so colons inside
  prose are fine.
- A blank line separates quests / dialogues / nodes for readability and is ignored.
- One quest per file. The file may hold any number of `DIALOGUE` blocks.

## `QUEST` block

| Line | Meaning |
|---|---|
| `QUEST <id>` | The quest id — the save key. Must match a `GRANT: <id>` somewhere. |
| `TITLE:` / `GIVER:` / `LOCATION:` | Fallbacks for the journal/tracker when dialogue leaves them blank. |
| `STAGE <condition>` | Opens a new stage. Further `OBJECTIVE:` / `WHENMET:` until the next `STAGE`. |
| `OBJECTIVE:` | The objective text shown while this stage is current. |
| `WHENMET:` | Collect only. Objective text once the player is carrying enough. |
| `REWARD` | Opens the reward block. `POUNDS:` / `XP:` / `ITEM:` / `CLEARSWANTED` until the next top-level keyword. |

### Conditions

| `STAGE` form | Meaning |
|---|---|
| `STAGE TALKTO <key>` | Interact with the `QuestActor` keyed `<key>`. |
| `STAGE KILL <key> x<count>` | Kill `<count>` `QuestActor`s keyed `<key>`. |
| `STAGE COLLECT <itemId> x<qty> [<itemId> x<qty> ...]` | Carry `<qty>` of the item. Extra `<itemId> x<qty>` pairs make it a "gather A, B and C" stage — the objective flips to `WHENMET:` only once **all** of them are carried. Reports only — the hand-in is dialogue. |
| `STAGE REACH <key> [r<radius>]` | Stand within `radius` (default 3) of the keyed `SceneMarker`. |
| `STAGE MANUAL` | Nothing watches it; bespoke code completes the quest. |

### Reward

| Line | Meaning |
|---|---|
| `POUNDS: <int>` | Payout into the wallet. |
| `XP: <int>` | XP granted on completion. |
| `ITEM: <itemId> x<qty>` | Item granted. |
| `CLEARSWANTED` | Clears the wanted level on completion. |

## `DIALOGUE` block

One `DIALOGUE <npcId>` block becomes one `DialogueData` asset. `<npcId>` maps to a
`PlacementPreset` by label or filename (case-insensitive, `Preset_` prefix ignored); the importer
wires the generated conversation into that preset's `Conversation` field and uses the preset's
`Speaker` for the nodes. If no preset matches, the asset is still generated and a warning is
logged — wire it by hand.

| Line | Meaning |
|---|---|
| `DIALOGUE <npcId>` | Opens a conversation for that NPC. |
| `NODE <nodeId>` | Opens a node. Further `SPEAK:` / `SPEAKER:` / `CHOICE` until the next `NODE`. |
| `SPEAK: <line>` | The line the speaker says. |
| `SPEAKER: <npcId>` | Optional — who says this node's line. Defaults to the dialogue's NPC. |
| `CHOICE <text> [-> <nodeId>]` | A choice. `-> id` names the next node; omitted ends the conversation. Further directives until the next `CHOICE` / `NODE`. |

### Choice directives

| Line | Meaning |
|---|---|
| `GRANT: <questId>` | Picking the choice starts this quest. |
| `COMPLETE: <questId>` | Picking the choice completes this quest. |
| `ITEM: <itemId> x<qty> [consume]` | Requires the item (greys until carried); `consume` removes it on pick. |
| `GATE: <state> <questId>` | Shows the choice only while the quest is `not-started` / `active` / `complete`. |
| `GATE: stage <questId> <index>` | Shows the choice only while the quest is active **and** sitting on stage `<index>` (0-based). |
| `STAT: <name> <level>` | Requires the trait (STR / INT / Personality) at or above `level`. |
| `TEACHSPARK` | No colon. Teaches the first spell and opens the naming popup once the chat closes. |

`GATE: stage` exists because `active` cannot tell one beat of a multi-stage quest from another —
a "go find him" nudge and a "you did it" payoff are both `active`. It is the only way one
conversation can offer a different branch per stage. A non-integer or negative index is refused
with a line number rather than defaulting to 0, and the validator errors on an index past the
quest's last stage.

⚠️ **Gate a `TEACHSPARK` choice.** `DialogueManager.EndDialogue` opens the naming popup every time
a conversation closes on one, and `LearnSpark` is idempotent — so an ungated one stays pickable and
reopens the popup forever. The validator warns.

`GRANT:` and `GATE:` are the two ways one conversation branches per quest: a grant starts a
quest, and a gate hides a choice until that quest is in the right state.

## Example

```
QUEST find_the_ledger
TITLE: The Ledger
GIVER: Councillor Mosley
LOCATION: F.U. Sports
STAGE KILL estate_lads x3
OBJECTIVE: [TODO: the lads have the ledger]
STAGE COLLECT item_ledger x1
OBJECTIVE: [TODO: find the ledger]
WHENMET: [TODO: take the ledger back to Mosley]
REWARD
POUNDS: 40
XP: 60

DIALOGUE mosley
NODE start
SPEAKER: mosley
SPEAK: [TODO: greeting]
CHOICE [TODO: about the ledger] -> offer
CHOICE [TODO: leave] -> end
NODE offer
SPEAKER: mosley
SPEAK: [TODO: offer the quest]
CHOICE [TODO: take it] -> end
GRANT: find_the_ledger
NODE end
SPEAKER: mosley
SPEAK: [TODO: farewell]
```

## Import behaviour

`Tools → Content → Import Quests` parses every `quests/*.quest` file. For each:

- Parse error → log, skip that file, write nothing for it.
- `DialogueValidator.Validate` error on a generated conversation → log, skip that file.
- Otherwise write the `QuestDefinition` to `Assets/Resources/Quests/<id>.asset` and each
  `DialogueData` to `Assets/Data/Dialogue/Generated/Dialogue_<npcId>.asset`, updating in place
  (GUID preserved — never delete-and-recreate), and wire the preset's `Conversation`.

Missing items are logged and left null — resolve the `ItemID` in `Resources/Items` first.

## Cross-checks

`Tools → Content → Validate Quests` (see `Assets/Editor/QuestContentValidator.cs`) checks the
contract between quests and dialogue without re-importing: every quest id has a `GRANT:` somewhere,
every `GRANT:` resolves, grant objectives are non-blank, and a `Collect` stage is last and has a
`COMPLETE:` route. (The stage-`QuestKey`-to-placed-actor/marker scan is deferred — it needs loading
chunk prefabs at editor time.)
