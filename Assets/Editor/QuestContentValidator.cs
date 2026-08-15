using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;

/// <summary>
/// Cross-checks the contract between <c>quests/*.quest</c> files and the assets they generate,
/// without re-importing: every <c>GRANT:</c> resolves to a quest, grant objectives are non-blank,
/// a <c>Collect</c> stage is last and has a <c>COMPLETE:</c> route, and no two files define a
/// <c>DIALOGUE</c> for the same NPC (which would clobber each other on import). Run via
/// <c>Tools -&gt; Content -&gt; Validate Quests</c>.
///
/// This reads the <b>text files</b> (the source of truth), not the generated assets, so it works
/// even before an import. It is deliberately UI-free and returns a problem list, so the future
/// plain-text importer can call it before writing and refuse a bad file.
/// </summary>
public static class QuestContentValidator
{
    public enum Severity { Error, Warning }

    public struct Problem
    {
        public Severity Severity;
        public string Message;
        public Problem(Severity severity, string message) { Severity = severity; Message = message; }
    }

    private const string QuestsRoot = "quests";

    /// <summary>What one .quest file declares, gathered for the cross-file pass.</summary>
    private sealed class FileInfo
    {
        public string Path;
        public string QuestId;
        public readonly List<string> GrantIds = new List<string>();
        public readonly List<string> DialogueIds = new List<string>();
    }

    [MenuItem("Tools/Content/Validate Quests")]
    private static void ValidateAllFiles()
    {
        if (!Directory.Exists(QuestsRoot))
        {
            Debug.Log("Validate Quests: no 'quests/' folder yet - nothing to check.");
            return;
        }

        List<Problem> problems = ValidateAll();
        if (problems.Count == 0)
        {
            Debug.Log("Validate Quests: all .quest files check out.");
            return;
        }

        var sb = new System.Text.StringBuilder();
        sb.AppendLine($"Validate Quests: {problems.Count} problem(s) -");
        foreach (Problem p in problems) sb.AppendLine($"  [{p.Severity}] {p.Message}");
        bool anyError = false;
        foreach (Problem p in problems) if (p.Severity == Severity.Error) anyError = true;
        if (anyError) Debug.LogError(sb.ToString().TrimEnd());
        else Debug.LogWarning(sb.ToString().TrimEnd());
    }

    /// <summary>Every problem across every .quest file, worst first. Empty = clean.</summary>
    public static List<Problem> ValidateAll()
    {
        var problems = new List<Problem>();
        // For the cross-file pass: every quest id and the grant ids its file references.
        var all = new List<FileInfo>();

        try
        {
            string[] files = Directory.GetFiles(QuestsRoot, "*.quest", SearchOption.TopDirectoryOnly);
            foreach (string file in files)
            {
                string name = Path.GetFileName(file);
                if (name.StartsWith("_")) continue;
                ValidateFile(file, all, problems);
            }
        }
        catch (Exception e)
        {
            problems.Add(new Problem(Severity.Error, "Could not scan quests/ : " + e.Message));
        }

        CrossReference(all, problems);
        return problems;
    }

    private static void ValidateFile(string path, List<FileInfo> all, List<Problem> problems)
    {
        string[] lines;
        try { lines = File.ReadAllLines(path); }
        catch (Exception e) { problems.Add(new Problem(Severity.Error, path + " unreadable: " + e.Message)); return; }

        var info = new FileInfo { Path = path };
        int stageIndex = -1;
        int stageCount = 0;
        bool collectLast = false;      // the last stage is Collect
        bool manualLast = false;       // the last stage is Manual
        bool anyComplete = false;      // some choice COMPLETEs THIS quest

        // Per-choice, flushed at the next CHOICE/NODE and at end of file: a TEACHSPARK choice with
        // no gate can be re-picked forever, and SpellNamingUI.Show is called unconditionally when
        // the conversation closes, so the naming popup would reopen every time.
        bool choiceTeachSpark = false;
        bool choiceGated = false;

        // Stage indices referenced by "GATE: stage <thisQuestId> <n>", checked against the real
        // stage count once the whole file has been read.
        var gateStageRefs = new List<int>();

        // Dialogue context, mirroring the importer: a GRANT:/COMPLETE: only means something inside
        // a CHOICE, and a floating one is the kind of typo this validator is meant to catch.
        bool inDialogue = false;
        bool inChoice = false;

        foreach (string raw in lines)
        {
            string line = (raw ?? "").Trim();
            if (line.Length == 0 || line[0] == '#' ) continue;
            string upper = line.ToUpperInvariant();
            string kw = upper.Split(' ')[0];

            switch (kw)
            {
                case "QUEST":
                    info.QuestId = Rest(line, 5);
                    stageIndex = -1; stageCount = 0; collectLast = false; anyComplete = false;
                    manualLast = false; gateStageRefs.Clear();
                    choiceTeachSpark = false; choiceGated = false;
                    inDialogue = false; inChoice = false;
                    break;

                case "DIALOGUE":
                    inDialogue = true; inChoice = false;
                    info.DialogueIds.Add(Rest(line, 8));
                    break;

                case "STAGE":
                    if (info.QuestId == null) { problems.Add(new Problem(Severity.Error, path + ": STAGE before QUEST")); break; }
                    inChoice = false;
                    stageIndex++;
                    stageCount++;
                    collectLast = (upper.StartsWith("STAGE COLLECT", StringComparison.Ordinal));
                    manualLast = (upper.StartsWith("STAGE MANUAL", StringComparison.Ordinal));
                    break;

                case "NODE":
                    FlushChoice(path, info.QuestId, ref choiceTeachSpark, ref choiceGated, problems);
                    inChoice = false;
                    break;

                case "CHOICE":
                    FlushChoice(path, info.QuestId, ref choiceTeachSpark, ref choiceGated, problems);
                    inChoice = true;
                    break;

                case "TEACHSPARK":
                    if (info.QuestId == null) break;
                    if (!inDialogue || !inChoice)
                    {
                        problems.Add(new Problem(Severity.Error, $"{path}: TEACHSPARK outside a CHOICE - the importer rejects it."));
                        break;
                    }
                    choiceTeachSpark = true;
                    break;

                case "GATE:":
                    if (info.QuestId == null) break;
                    choiceGated = true;
                    ParseGateStageRef(Value(line), info.QuestId, gateStageRefs);
                    break;

                case "OBJECTIVE:":
                    if (info.QuestId == null) break;
                    if (stageIndex < 0) { problems.Add(new Problem(Severity.Error, path + ": OBJECTIVE before any STAGE")); break; }
                    if (string.IsNullOrWhiteSpace(Value(line)))
                        problems.Add(new Problem(Severity.Warning, $"{path}: quest '{info.QuestId}' stage {stageIndex} has an empty OBJECTIVE"));
                    break;

                case "GRANT:":
                    if (info.QuestId == null) break;
                    if (!inDialogue || !inChoice)
                    {
                        problems.Add(new Problem(Severity.Error, $"{path}: GRANT outside a CHOICE - the importer rejects it."));
                        break;
                    }
                    info.GrantIds.Add(Value(line));
                    break;

                case "COMPLETE:":
                    if (info.QuestId == null) break;
                    if (!inDialogue || !inChoice)
                    {
                        problems.Add(new Problem(Severity.Error, $"{path}: COMPLETE outside a CHOICE - the importer rejects it."));
                        break;
                    }
                    // Only a COMPLETE naming THIS quest makes the quest completable. A COMPLETE for
                    // a different quest (a multi-quest giver's file) must not satisfy the
                    // Collect-last check.
                    if (Value(line) == info.QuestId)
                        anyComplete = true;
                    break;
            }
        }

        FlushChoice(path, info.QuestId, ref choiceTeachSpark, ref choiceGated, problems);

        if (info.QuestId == null) { problems.Add(new Problem(Severity.Error, path + ": no QUEST block")); return; }

        // Registered for the cross-file pass so a GRANT can be checked against every quest.
        all.Add(info);

        // A quest with no stages is suspect.
        if (stageCount == 0)
            problems.Add(new Problem(Severity.Error, $"{path}: quest '{info.QuestId}' has no STAGEs."));

        // Collect stage must be last AND have a complete route.
        if (collectLast && !anyComplete)
            problems.Add(new Problem(Severity.Error, $"{path}: quest '{info.QuestId}' ends in a Collect stage but no dialogue COMPLETEs it - it can never finish."));

        // Same trap, different condition: nothing watches a Manual stage, so if it is last and no
        // dialogue completes the quest, it can never finish either.
        if (manualLast && !anyComplete)
            problems.Add(new Problem(Severity.Error, $"{path}: quest '{info.QuestId}' ends in a Manual stage but no dialogue COMPLETEs it - it can never finish."));

        // A stage gate pointing past the end gates a beat that can never be reached.
        foreach (int idx in gateStageRefs)
        {
            if (idx >= stageCount)
                problems.Add(new Problem(Severity.Error,
                    $"{path}: GATE stage {idx} for quest '{info.QuestId}', which has only {stageCount} stage(s) (0-{stageCount - 1}) - that choice can never show."));
        }
    }

    /// <summary>
    /// Closes off the choice just parsed. A TEACHSPARK choice with no gate stays pickable after
    /// the spell has been learnt, and DialogueManager.EndDialogue opens the naming popup every
    /// time the conversation closes on one — so the popup would reappear indefinitely.
    /// </summary>
    private static void FlushChoice(string path, string questId, ref bool teachSpark, ref bool gated,
                                    List<Problem> problems)
    {
        if (teachSpark && !gated)
            problems.Add(new Problem(Severity.Warning,
                $"{path}: a TEACHSPARK choice in '{questId}' has no GATE, so it stays pickable after the spell is learnt and reopens the naming popup each time."));
        teachSpark = false;
        gated = false;
    }

    /// <summary>
    /// Records the stage index from a "GATE: stage &lt;questId&gt; &lt;index&gt;" line, but only when it
    /// names the quest this file defines — a gate on another file's quest cannot be range-checked
    /// here. Malformed values are left to the importer, which refuses them with a line number.
    /// </summary>
    private static void ParseGateStageRef(string value, string questId, List<int> into)
    {
        string[] t = value.Split(new[] { ' ', (char)9 }, StringSplitOptions.RemoveEmptyEntries);
        if (t.Length < 3) return;
        if (!string.Equals(t[0], "stage", StringComparison.OrdinalIgnoreCase)) return;
        if (t[1] != questId) return;
        if (int.TryParse(t[2], out int idx) && idx >= 0) into.Add(idx);
    }

    // Cross-file pass: match every GRANT id against every QUEST id, flag orphan quests and
    // duplicate DIALOGUE npcIds.
    private static void CrossReference(List<FileInfo> all, List<Problem> problems)
    {
        var questIds = new HashSet<string>();
        foreach (var info in all) if (!string.IsNullOrEmpty(info.QuestId)) questIds.Add(info.QuestId);

        // Every GRANT must resolve to a quest.
        foreach (var info in all)
        {
            foreach (string g in info.GrantIds)
            {
                if (string.IsNullOrEmpty(g)) continue;
                if (!questIds.Contains(g))
                    problems.Add(new Problem(Severity.Error, $"{info.Path}: GRANT references quest '{g}' which has no QUEST block."));
            }
        }

        // An orphan quest can never start. Warning, not error: a quest can legitimately be granted
        // by a hand-authored DialogueData asset outside the text pipeline, which this validator
        // cannot see.
        foreach (var info in all)
        {
            if (string.IsNullOrEmpty(info.QuestId)) continue;
            bool granted = false;
            foreach (var other in all)
            {
                if (other.GrantIds.Contains(info.QuestId)) { granted = true; break; }
            }
            if (!granted)
                problems.Add(new Problem(Severity.Warning, $"{info.Path}: quest '{info.QuestId}' has no GRANT: anywhere - it can never start."));
        }

        // Two files defining the same NPC's DIALOGUE clobber each other on import: each
        // regenerates Dialogue_<npcId>.asset wholesale and the last one wins. One file must own an
        // NPC's whole conversation.
        var dialogueOwner = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var info in all)
        {
            foreach (string npcId in info.DialogueIds)
            {
                if (string.IsNullOrEmpty(npcId)) continue;
                if (dialogueOwner.TryGetValue(npcId, out string first))
                {
                    problems.Add(new Problem(Severity.Error,
                        $"{info.Path}: DIALOGUE '{npcId}' is also defined in '{first}'. Re-importing " +
                        "clobbers the other - give this NPC all its dialogue in one file."));
                }
                else
                {
                    dialogueOwner[npcId] = info.Path;
                }
            }
        }
    }

    private static string Value(string line)
    {
        int colon = line.IndexOf(':');
        return colon < 0 ? "" : line.Substring(colon + 1).Trim();
    }

    private static string Rest(string line, int skipAfter)
    {
        if (line.Length <= skipAfter) return "";
        return line.Substring(skipAfter).Trim();
    }
}

