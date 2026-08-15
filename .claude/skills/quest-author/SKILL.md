---
name: quest-author
description: Talk a quest through and write it into a valid .quest file in quests/ — structure, wiring, and the dialogue the owner dictates. Asks the owner for every line and the conversation shape (how many nodes/choices), transcribes exactly what they give, and never invents a line they didn't. Then hands off the Validate → Import → place → play steps. Use when the user wants to create, draft, or wire up a quest for GBH: England.
---

# Quest author

You are helping the owner build **one `.quest` file** by talking it through. You produce the
**structure and wiring**; you never write the quest's prose. The `.quest` text file is the source
of truth — the importer regenerates assets from it wholesale.

## The one immovable rule

**You write the words the owner gives you — and only those.** The owner is still the author; you are
the typist. Ask them for every line — greetings, offers, objectives, farewells — and transcribe
**exactly** what they say into the file. This stays square with CLAUDE.md §3, which says to *ask for*
the words rather than draft them.

What you must never do is **originate** prose: do not invent, embellish, paraphrase, "improve", or
"just to get us started" write any line the owner has not dictated. If a line is missing, leave a
`[TODO: what this line is for]` and **ask for it** — never fill it yourself. Ids, keys, keywords,
stage logic and reward numbers are yours to propose freely; the human-facing sentences are the
owner's, transcribed verbatim.

## Read first — do not re-derive the format

Open these two, once, before writing anything:

- `docs/reference/QUEST_TEXT_FORMAT.md` — the authoritative grammar (keywords, conditions, reward,
  dialogue directives, import behaviour). Trust it over memory.
- `quests/_template.quest` — the starter shape to build from.

If either has a `Last verified against:` header naming an old state, treat its claims as leads and
confirm against `Assets/Editor/QuestTextImporter.cs` / `QuestContentValidator.cs`.

## The interview

Ask for these in order, one small batch at a time — never dump the whole list at once. Propose
sensible ids/keys yourself so the owner only has to approve them:

1. **Identity** — a short quest id (snake_case, this is the save key), and roughly what the job is
   in one line (so you can shape stages — you are *not* writing it into the file).
2. **The giver** — which NPC hands it out. Ask for the `PlacementPreset` name so `DIALOGUE <npc>`
   can match it (`Preset_` prefix and case are ignored). If they don't know, note it as a `[TODO]`
   id and flag that the preset must exist/be placed.
3. **Stages** — walk each step and pick a condition from the format doc:
   `TALKTO <key>` / `KILL <key> x<n>` / `COLLECT <itemId> x<n>` / `REACH <key> [r<rad>]` /
   `MANUAL`. Keep keys consistent and remind them each `<key>` needs a placed `QuestActor.Key`
   (set via a preset's `QuestKey`), and each `<itemId>` needs a real `ItemData.ItemID` in
   `Resources/Items`. For a *first* quest, suggest a single `TALKTO` pointed at the giver's own key.
4. **Reward** — `POUNDS` / `XP` / `ITEM` / `CLEARSWANTED`.
5. **Conversation shape, then the lines.** First the shape: how many nodes ("chat windows" — each
   `NODE` is one on-screen exchange), how they branch, how many choices per node, and where the
   wiring lands (the offer node's choice carrying `GRANT: <id>`, any hand-in node with
   `COMPLETE: <id>` and `ITEM: ... consume`, any `GATE:` / `STAT:` gated choices). Then, node by
   node, **ask the owner for the actual words** — the speaker's line and each choice's text — and
   transcribe them verbatim. Only a line the owner hasn't given yet stays a `[TODO:]`, which you
   then ask about.

## Emit the file

Write to `quests/<id>.quest` (repo root, **never** under `Assets/`). Rules:

- UPPERCASE keywords at line start; `KEY: value` splits on the first colon; `#` full-line comments.
- One quest per file; any number of `DIALOGUE` blocks.
- Every `<key>`, `<id>` and `<itemId>` must be internally consistent: the `QUEST <id>` matches its
  `GRANT: <id>`, a `TALKTO <key>` matches the `QuestKey` you tell them to stamp, and so on.
- Every human-facing string is the owner's own words, transcribed exactly as dictated. Use a
  `[TODO: hint]` **only** for a line the owner hasn't given yet — then ask for it before finishing.

## Before you hand back, self-check

Mirror what `Tools → Content → Validate Quests` will check, so the owner doesn't bounce off it:

- The quest id has exactly one `GRANT:` and it resolves.
- A `COLLECT` stage is last and has a `COMPLETE:` route in dialogue, or it can never end.
- Grant objective text exists (as a `[TODO]` is fine).
- `<npcId>` plausibly matches a preset; `<itemId>`s plausibly exist — flag any you can't verify.

## Hand off (do not run Unity — you can't)

Tell the owner the exact editor steps to finish, in order:

1. Write the prose into every `[TODO:]` slot.
2. `Tools → Content → Validate Quests` — read the Console, fix, repeat until clean.
3. `Tools → Content → Import Quests` — generates `Assets/Resources/Quests/<id>.asset` and
   `Assets/Data/Dialogue/Generated/Dialogue_<npc>.asset`, and wires the preset's `Conversation`.
4. Place the giver preset in the chunk (`Tools → World Palette`) and set its `QuestKey` to the
   stage key. For `KILL`/`REACH`/`COLLECT`, place the keyed actors / markers / items too.
5. Play, grant it in conversation, clear the stage, confirm the reward and that it survives a
   save+reload.

Remind them this pipeline has never compiled or run — the first Validate/Import is the real test,
and red Console errors should come back to the session to fix.

## Never

- Invent, embellish, paraphrase or "improve" a line the owner didn't dictate. Transcribe exactly;
  where a line is missing, leave `[TODO:]` and ask — never fill it yourself.
- Put a `.quest` file anywhere but the root `quests/` folder.
- Hand-edit a generated `QuestDefinition`/`DialogueData` asset — the file owns them; re-import.
- Claim the quest "works" — you can only confirm the file is well-formed, not that it runs.
