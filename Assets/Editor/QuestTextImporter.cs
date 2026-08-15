using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;

/// <summary>
/// Turns <c>quests/*.quest</c> text files into real assets: one <see cref="QuestDefinition"/> per
/// file (into <c>Resources/Quests/</c>) plus one <see cref="DialogueData"/> per <c>DIALOGUE</c>
/// block (into <c>Assets/Data/Dialogue/Generated/</c>), wired into the matching
/// <see cref="PlacementPreset"/>'s <c>Conversation</c>.
///
/// <b>The text file is the source of truth.</b> Re-importing regenerates the assets wholesale
/// (update-in-place, so GUIDs — and any prefab/scene references to them — survive). This is the
/// deliberate opposite of <c>PresetDialogueTools</c>, which never overwrites prose: that tool
/// guards hand-written assets, this pipeline owns its assets through the file. Writing lives in
/// the text file, never only in the asset.
///
/// Editor-only for the usual reason: <c>AssetDatabase.CreateAsset</c> does not exist at runtime.
/// See <c>docs/reference/QUEST_TEXT_FORMAT.md</c> for the format.
/// </summary>
public static class QuestTextImporter
{
    private const string QuestsRoot = "quests";
    /// <summary>
    /// Dialogue-only files: DIALOGUE blocks and no QUEST block. One file per NPC, holding every
    /// line they say across every quest, gated per quest id.
    /// </summary>
    private const string DialogueRoot = "quests/dialogue";
    private const string QuestAssetsFolder = "Assets/Resources/Quests";
    private const string DialogueAssetsFolder = "Assets/Data/Dialogue/Generated";

    // ── Parsed model ───────────────────────────────────────────────────────────────────────

    private sealed class ParsedQuest
    {
        public string Id;
        public string Title;
        public string Giver;
        public string Location;
        public readonly List<ParsedStage> Stages = new List<ParsedStage>();
        public ParsedReward Reward = new ParsedReward();
    }

    private sealed class ParsedStage
    {
        public QuestConditionType ConditionType;
        public string QuestKey;
        public int Count = 1;
        public string ItemId;
        public int Quantity = 1;
        public float ReachRadius = 3f;
        public string Objective;
        public string ObjectiveWhenMet;
        // Extra items for a multi-item COLLECT: the second and later (itemId x<qty>) pairs on the
        // STAGE line. The first pair is ItemId/Quantity above.
        public readonly List<ParsedCollectItem> AlsoCollect = new List<ParsedCollectItem>();
    }

    private sealed class ParsedCollectItem
    {
        public string ItemId;
        public int Quantity = 1;
    }

    private sealed class ParsedReward
    {
        public int Pounds;
        public int XP;
        public string ItemId;
        public int Quantity;
        public bool ClearsWanted;
    }

    private sealed class ParsedDialogue
    {
        public string NpcId;
        public string StartNodeId = DialogueData.DefaultStartId;
        public readonly List<ParsedNode> Nodes = new List<ParsedNode>();
    }

    private sealed class ParsedNode
    {
        public string Id;
        public string SpeakerId;
        public string Text;
        public readonly List<ParsedChoice> Choices = new List<ParsedChoice>();
    }

    private sealed class ParsedChoice
    {
        public string Text;
        public string NextNodeId;
        public string GrantQuestId;
        public string CompleteQuestId;
        public string RequiredItemId;
        public int RequiredItemQuantity = 1;
        public bool ConsumeRequiredItem;
        public QuestGateType QuestGate;
        public string QuestGateId;
        public int QuestGateStage;
        public bool TeachSpark;
        public string RequiredStat;
        public int RequiredStatLevel;
        public bool HasNext; // a choice with no "-> id" ends the conversation
    }

    // ── Menu ───────────────────────────────────────────────────────────────────────────────

    [MenuItem("Tools/Content/Import Quests")]
    private static void ImportAll()
    {
        if (!Directory.Exists(QuestsRoot))
        {
            Debug.Log("Import Quests: no 'quests/' folder yet — nothing to import.");
            return;
        }

        string[] files = Directory.GetFiles(QuestsRoot, "*.quest", SearchOption.TopDirectoryOnly);

        // Dialogue-only files live one level down, in quests/dialogue/. An NPC who appears in
        // several quests keeps ALL their nodes in one file there, because each import regenerates
        // Dialogue_<npcId>.asset wholesale and two files declaring the same npcId would clobber
        // each other. The separate folder is deliberate: a quest file that has lost its QUEST line
        // to a typo must still be an ERROR, not silently reinterpreted as a dialogue file.
        string[] dialogueFiles = Directory.Exists(DialogueRoot)
            ? Directory.GetFiles(DialogueRoot, "*.quest", SearchOption.TopDirectoryOnly)
            : new string[0];

        if (files.Length == 0 && dialogueFiles.Length == 0)
        {
            Debug.Log("Import Quests: no .quest files found in 'quests/'.");
            return;
        }

        int ok = 0, skipped = 0;

        // Dialogue first: a quest file's GRANT/COMPLETE wiring is validated against ids, not
        // against the conversation, so order does not matter for correctness — but importing the
        // conversations first means a preset's Conversation is already wired when its quest lands.
        foreach (string file in dialogueFiles)
        {
            string name = Path.GetFileName(file);
            if (name.StartsWith("_")) continue;

            Debug.Log($"Import Quests: parsing dialogue/{name}...");
            if (ImportFile(file, dialogueOnly: true))
                ok++;
            else
                skipped++;
        }

        foreach (string file in files)
        {
            string name = Path.GetFileName(file);
            if (name.StartsWith("_")) continue; // scaffolds and notes are not quests

            Debug.Log($"Import Quests: parsing {name}...");
            if (ImportFile(file, dialogueOnly: false))
                ok++;
            else
                skipped++;
        }

        AssetDatabase.SaveAssets();
        Debug.Log($"Import Quests: {ok} quest(s) imported, {skipped} skipped (see above for errors).");
    }

    /// <param name="dialogueOnly">
    /// True for a file under <see cref="DialogueRoot"/>: it must declare conversations and no
    /// quest, and no <c>QuestDefinition</c> is written for it.
    /// </param>
    private static bool ImportFile(string path, bool dialogueOnly)
    {
        string text;
        try
        {
            text = File.ReadAllText(path);
        }
        catch (Exception e)
        {
            Debug.LogError($"Import Quests: could not read '{path}': {e.Message}");
            return false;
        }

        var quest = new ParsedQuest();
        var dialogues = new List<ParsedDialogue>();
        var errors = new List<string>();

        if (!Parse(text, quest, dialogues, errors))
        {
            LogErrors(path, errors);
            return false;
        }

        if (dialogueOnly)
        {
            // Refused rather than ignored: a quest block here would name a quest whose stages and
            // reward nothing would ever write, and it would read as authored.
            if (!string.IsNullOrEmpty(quest.Id))
            {
                Debug.LogError($"Import Quests: '{path}' is in {DialogueRoot}/ and declares " +
                               $"QUEST '{quest.Id}'. Dialogue files hold conversations only — " +
                               "move the quest to a file directly in quests/.");
                return false;
            }
            if (dialogues.Count == 0)
            {
                Debug.LogError($"Import Quests: '{path}' is in {DialogueRoot}/ but declares no " +
                               "DIALOGUE block.");
                return false;
            }
        }
        else if (string.IsNullOrEmpty(quest.Id))
        {
            Debug.LogError($"Import Quests: '{path}' has no QUEST id.");
            return false;
        }

        // Build the dialogue assets first so we can validate them before writing anything.
        var builtDialogues = new List<(ParsedDialogue parsed, DialogueData asset, PlacementPreset preset)>();
        foreach (ParsedDialogue dialogue in dialogues)
        {
            DialogueData asset = ScriptableObject.CreateInstance<DialogueData>();
            PlacementPreset preset = ResolvePreset(dialogue.NpcId);
            if (!BuildDialogue(dialogue, asset, preset, errors))
            {
                LogErrors(path, errors);
                UnityEngine.Object.DestroyImmediate(asset);
                return false;
            }

            // Refuse to write a conversation the validator flags as broken.
            List<DialogueValidator.Problem> problems = DialogueValidator.Validate(asset);
            foreach (DialogueValidator.Problem p in problems)
            {
                if (p.Severity == DialogueValidator.Severity.Error)
                    errors.Add($"Dialogue '{dialogue.NpcId}': [ERROR] {p.Message}");
            }
            if (errors.Count > 0)
            {
                LogErrors(path, errors);
                UnityEngine.Object.DestroyImmediate(asset);
                return false;
            }

            builtDialogues.Add((dialogue, asset, preset));
        }

        // Write the quest definition. A dialogue-only file has no quest to write — its
        // conversations still land below, and its GRANT:/COMPLETE: directives point at quests
        // defined in other files, which the validator's cross-file pass checks.
        if (!dialogueOnly)
        {
            QuestDefinition def = WriteQuestAsset(quest, errors);
            if (def == null)
            {
                Cleanup(builtDialogues);
                LogErrors(path, errors);
                return false;
            }
        }

        // Write the dialogue assets and wire their presets.
        foreach (var (parsed, asset, preset) in builtDialogues)
        {
            string dPath = DialoguePathFor(parsed.NpcId);
            EnsureFolder(DialogueAssetsFolder);
            SaveAsset(asset, dPath);

            if (preset != null)
            {
                preset.Conversation = asset;
                EditorUtility.SetDirty(preset);
            }
            else
            {
                Debug.LogWarning($"Import Quests: no preset matched '{parsed.NpcId}' — conversation " +
                                 $"written to '{dPath}' but not wired. Link it on the preset by hand.", asset);
            }
        }

        return true;
    }

    private static void LogErrors(string path, List<string> errors)
    {
        if (errors.Count == 0) return;
        var sb = new System.Text.StringBuilder();
        sb.AppendLine($"Import Quests: '{path}' was not imported —");
        foreach (string e in errors) sb.AppendLine("  " + e);
        Debug.LogError(sb.ToString().TrimEnd());
    }

    private static void Cleanup(List<(ParsedDialogue, DialogueData, PlacementPreset)> built)
    {
        foreach (var (_, asset, _) in built)
            if (asset != null) UnityEngine.Object.DestroyImmediate(asset);
    }

    // ── Parser ─────────────────────────────────────────────────────────────────────────────

    /// <summary>Parses the file into a quest + dialogues. Collects errors, never throws.</summary>
    private static bool Parse(string text, ParsedQuest quest, List<ParsedDialogue> dialogues, List<string> errors)
    {
        string[] lines = text.Split((char)10); // LF
        int lineNo = 0;
        bool inQuest = false;
        bool inReward = false;
        ParsedDialogue currentDialogue = null;
        ParsedNode currentNode = null;
        ParsedChoice currentChoice = null;
        bool ok = true;

        void Err(string msg)
        {
            ok = false;
            errors.Add($"line {lineNo}: {msg}");
        }

        foreach (string raw in lines)
        {
            lineNo++;
            string line = raw.TrimEnd((char)13).Trim(); // strip CR from CRLF
            if (line.Length == 0) continue;
            if (line[0] == '#') continue;

            string upper = line.ToUpperInvariant();
            string keyword = upper.Split(' ')[0];

            switch (keyword)
            {
                case "QUEST":
                    currentDialogue = null; currentNode = null; currentChoice = null;
                    inQuest = true; inReward = false;
                    quest.Id = Rest(line, 5); // "QUEST "
                    break;

                case "DIALOGUE":
                    inQuest = false; inReward = false;
                    currentNode = null; currentChoice = null;
                    currentDialogue = new ParsedDialogue { NpcId = Rest(line, 8) };
                    dialogues.Add(currentDialogue);
                    break;

                case "STAGE":
                    if (!inQuest) { Err("STAGE outside a QUEST block"); break; }
                    inReward = false; currentChoice = null;
                    ParseStage(Rest(line, 5), quest, errors, lineNo);
                    break;

                case "REWARD":
                    if (!inQuest) { Err("REWARD outside a QUEST block"); break; }
                    inReward = true; currentChoice = null;
                    break;

                case "TITLE:":
                    if (!inQuest) { Err("TITLE outside a QUEST block"); break; }
                    quest.Title = Value(line);
                    break;

                case "GIVER:":
                    if (!inQuest) { Err("GIVER outside a QUEST block"); break; }
                    quest.Giver = Value(line);
                    break;

                case "LOCATION:":
                    if (!inQuest) { Err("LOCATION outside a QUEST block"); break; }
                    quest.Location = Value(line);
                    break;

                case "OBJECTIVE:":
                    if (!inQuest) { Err("OBJECTIVE outside a QUEST block"); break; }
                    if (quest.Stages.Count == 0) { Err("OBJECTIVE before any STAGE"); break; }
                    quest.Stages[quest.Stages.Count - 1].Objective = Value(line);
                    break;

                case "WHENMET:":
                    if (!inQuest) { Err("WHENMET outside a QUEST block"); break; }
                    if (quest.Stages.Count == 0) { Err("WHENMET before any STAGE"); break; }
                    quest.Stages[quest.Stages.Count - 1].ObjectiveWhenMet = Value(line);
                    break;

                case "POUNDS:":
                    if (!inReward) { Err("POUNDS outside a REWARD block"); break; }
                    quest.Reward.Pounds = ParseInt(Value(line), err: () => Err("POUNDS needs an integer"));
                    break;

                case "XP:":
                    if (!inReward) { Err("XP outside a REWARD block"); break; }
                    quest.Reward.XP = ParseInt(Value(line), err: () => Err("XP needs an integer"));
                    break;

                case "ITEM:":
                    if (currentChoice != null)
                    {
                        ParseItemRequirement(Value(line), currentChoice, errors, lineNo);
                    }
                    else if (inReward)
                    {
                        ParseRewardItem(Value(line), quest.Reward, errors, lineNo);
                    }
                    else
                    {
                        Err("ITEM outside a choice or REWARD block");
                    }
                    break;

                case "CLEARSWANTED":
                    if (!inReward) { Err("CLEARSWANTED outside a REWARD block"); break; }
                    quest.Reward.ClearsWanted = true;
                    break;

                case "NODE":
                    if (currentDialogue == null) { Err("NODE outside a DIALOGUE block"); break; }
                    inReward = false;
                    currentNode = new ParsedNode { Id = Rest(line, 4) }; // "NODE "
                    currentChoice = null;
                    currentDialogue.Nodes.Add(currentNode);
                    break;

                case "SPEAK:":
                    if (currentNode == null) { Err("SPEAK outside a NODE"); break; }
                    currentNode.Text = Value(line);
                    break;

                case "SPEAKER:":
                    if (currentNode == null) { Err("SPEAKER outside a NODE"); break; }
                    currentNode.SpeakerId = Value(line);
                    break;

                case "START:":
                    if (currentDialogue == null) { Err("START outside a DIALOGUE block"); break; }
                    currentDialogue.StartNodeId = Value(line);
                    break;

                case "CHOICE":
                    if (currentNode == null) { Err("CHOICE outside a NODE"); break; }
                    currentChoice = ParseChoice(Rest(line, 6), errors, lineNo); // "CHOICE "
                    currentNode.Choices.Add(currentChoice);
                    break;

                case "GRANT:":
                    if (currentChoice == null) { Err("GRANT outside a CHOICE"); break; }
                    currentChoice.GrantQuestId = Value(line);
                    break;

                case "COMPLETE:":
                    if (currentChoice == null) { Err("COMPLETE outside a CHOICE"); break; }
                    currentChoice.CompleteQuestId = Value(line);
                    break;

                case "GATE:":
                    if (currentChoice == null) { Err("GATE outside a CHOICE"); break; }
                    ParseGate(Value(line), currentChoice, errors, lineNo);
                    break;

                // No colon — a flag, like CLEARSWANTED. Teaches the first spell and opens the
                // naming popup once the conversation closes (DialogueManager.EndDialogue).
                case "TEACHSPARK":
                    if (currentChoice == null) { Err("TEACHSPARK outside a CHOICE"); break; }
                    currentChoice.TeachSpark = true;
                    break;

                case "STAT:":
                    if (currentChoice == null) { Err("STAT outside a CHOICE"); break; }
                    ParseStat(Value(line), currentChoice, errors, lineNo);
                    break;

                default:
                    // Anything unrecognised is a likely typo — flag it rather than silently ignore.
                    Err($"unrecognised keyword '{keyword}'");
                    break;
            }
        }

        if (quest.Stages.Count == 0 && dialogues.Count == 0)
            errors.Add("no QUEST or DIALOGUE block found");

        return ok;
    }

    private static void ParseStage(string spec, ParsedQuest quest, List<string> errors, int lineNo)
    {
        string[] t = spec.Split(new[] { ' ', (char)9 }, StringSplitOptions.RemoveEmptyEntries);
        if (t.Length == 0) { errors.Add($"line {lineNo}: EMPTY STAGE"); return; }

        var stage = new ParsedStage();
        switch (t[0].ToUpperInvariant())
        {
            case "TALKTO":
                if (t.Length < 2) { errors.Add($"line {lineNo}: TALKTO needs a key"); return; }
                stage.ConditionType = QuestConditionType.TalkTo;
                stage.QuestKey = t[1];
                break;
            case "KILL":
                if (t.Length < 3) { errors.Add($"line {lineNo}: KILL needs <key> x<count>"); return; }
                stage.ConditionType = QuestConditionType.Kill;
                stage.QuestKey = t[1];
                stage.Count = ParseCount(t[2], lineNo, errors);
                break;
            case "COLLECT":
                if (t.Length < 3) { errors.Add($"line {lineNo}: COLLECT needs <itemId> x<qty> [<itemId> x<qty> ...]"); return; }
                stage.ConditionType = QuestConditionType.Collect;
                stage.ItemId = t[1];
                stage.Quantity = ParseCount(t[2], lineNo, errors);
                // Additional (itemId x<qty>) pairs make this a multi-item "gather A, B and C" stage.
                // Each item needs a quantity: a dangling item with none is a typo, flagged rather
                // than dropped — the same stance the REACH radius and GATE index take.
                if ((t.Length - 1) % 2 != 0)
                    errors.Add($"line {lineNo}: COLLECT has an item with no 'x<qty>' — every item needs a quantity");
                for (int k = 3; k + 1 < t.Length; k += 2)
                    stage.AlsoCollect.Add(new ParsedCollectItem { ItemId = t[k], Quantity = ParseCount(t[k + 1], lineNo, errors) });
                break;
            case "REACH":
                if (t.Length < 2) { errors.Add($"line {lineNo}: REACH needs a key"); return; }
                stage.ConditionType = QuestConditionType.Reach;
                stage.QuestKey = t[1];
                if (t.Length >= 3)
                {
                    // A malformed radius is an error like every other bad token, not a silent
                    // fallback to the 3f default — an author who typed "x5" should be told.
                    string radiusToken = t[2].TrimStart('r', 'R');
                    if (radiusToken.Length == 0 || !float.TryParse(radiusToken, out float radius))
                        errors.Add($"line {lineNo}: REACH radius must be 'r<number>', got '{t[2]}'");
                    else
                        stage.ReachRadius = radius;
                }
                break;
            case "MANUAL":
                stage.ConditionType = QuestConditionType.Manual;
                break;
            default:
                errors.Add($"line {lineNo}: unknown condition '{t[0]}'");
                return;
        }
        quest.Stages.Add(stage);
    }

    private static int ParseCount(string token, int lineNo, List<string> errors)
    {
        if (token.Length >= 2 && (token[0] == 'x' || token[0] == 'X')
            && int.TryParse(token.Substring(1), out int count))
            return Mathf.Max(1, count);
        errors.Add($"line {lineNo}: expected 'x<count>' but got '{token}'");
        return 1;
    }

    private static void ParseRewardItem(string value, ParsedReward reward, List<string> errors, int lineNo)
    {
        string[] t = value.Split(new[] { ' ', (char)9 }, StringSplitOptions.RemoveEmptyEntries);
        if (t.Length == 0) { errors.Add($"line {lineNo}: EMPTY ITEM"); return; }
        reward.ItemId = t[0];
        reward.Quantity = t.Length >= 2 ? ParseCount(t[1], lineNo, errors) : 1;
    }

    private static void ParseItemRequirement(string value, ParsedChoice choice, List<string> errors, int lineNo)
    {
        string[] t = value.Split(new[] { ' ', (char)9 }, StringSplitOptions.RemoveEmptyEntries);
        if (t.Length == 0) { errors.Add($"line {lineNo}: EMPTY ITEM"); return; }
        choice.RequiredItemId = t[0];
        choice.RequiredItemQuantity = t.Length >= 2 ? ParseCount(t[1], lineNo, errors) : 1;
        for (int i = 2; i < t.Length; i++)
            if (t[i].ToLowerInvariant() == "consume") choice.ConsumeRequiredItem = true;
    }

    private static void ParseGate(string value, ParsedChoice choice, List<string> errors, int lineNo)
    {
        string[] t = value.Split(new[] { ' ', (char)9 }, StringSplitOptions.RemoveEmptyEntries);
        if (t.Length < 2) { errors.Add($"line {lineNo}: GATE needs <state> <questId>"); return; }
        switch (t[0].ToLowerInvariant())
        {
            case "not-started": choice.QuestGate = QuestGateType.NotStarted; break;
            case "active": choice.QuestGate = QuestGateType.Active; break;
            case "complete": choice.QuestGate = QuestGateType.Complete; break;
            case "stage":
                // GATE: stage <questId> <index> — active AND sitting on that stage.
                if (t.Length < 3)
                {
                    errors.Add($"line {lineNo}: GATE stage needs <questId> <stageIndex>");
                    return;
                }
                // Refused rather than defaulted, exactly like STAT and the REACH radius: a
                // mistyped index that silently became 0 would gate the wrong beat and look like
                // a content bug rather than a typo.
                if (!int.TryParse(t[2], out int stageIndex) || stageIndex < 0)
                {
                    errors.Add($"line {lineNo}: GATE stage index '{t[2]}' is not a non-negative integer");
                    return;
                }
                choice.QuestGate = QuestGateType.ActiveAtStage;
                choice.QuestGateStage = stageIndex;
                break;
            default: errors.Add($"line {lineNo}: unknown GATE state '{t[0]}'"); return;
        }
        choice.QuestGateId = t[1];
    }

    private static void ParseStat(string value, ParsedChoice choice, List<string> errors, int lineNo)
    {
        string[] t = value.Split(new[] { ' ', (char)9 }, StringSplitOptions.RemoveEmptyEntries);
        if (t.Length < 2) { errors.Add($"line {lineNo}: STAT needs <name> <level>"); return; }
        choice.RequiredStat = t[0];
        if (!int.TryParse(t[1], out choice.RequiredStatLevel))
            errors.Add($"line {lineNo}: STAT level must be an integer");
    }

    private static ParsedChoice ParseChoice(string spec, List<string> errors, int lineNo)
    {
        var choice = new ParsedChoice();
        string text = spec;
        int arrow = spec.IndexOf("->", StringComparison.Ordinal);
        if (arrow >= 0)
        {
            choice.HasNext = true;
            text = spec.Substring(0, arrow).Trim();
            string next = spec.Substring(arrow + 2).Trim();
            if (next.Length == 0) errors.Add($"line {lineNo}: CHOICE '->' with no node id");
            else choice.NextNodeId = next;
        }
        choice.Text = text.Trim();
        if (choice.Text.Length == 0)
            errors.Add($"line {lineNo}: CHOICE with no text");
        return choice;
    }

    // ── Asset builders ─────────────────────────────────────────────────────────────────────

    private static QuestDefinition WriteQuestAsset(ParsedQuest parsed, List<string> errors)
    {
        string path = $"{QuestAssetsFolder}/{parsed.Id}.asset";
        EnsureFolder(QuestAssetsFolder);

        var def = AssetDatabase.LoadAssetAtPath<QuestDefinition>(path);
        if (def == null) def = ScriptableObject.CreateInstance<QuestDefinition>();

        def.Id = parsed.Id;
        def.Title = parsed.Title;
        def.Giver = parsed.Giver;
        def.Location = parsed.Location;

        if (def.Stages == null) def.Stages = new List<QuestStage>();
        def.Stages.Clear();
        foreach (ParsedStage ps in parsed.Stages) def.Stages.Add(BuildStage(ps, errors));

        def.Reward = BuildReward(parsed.Reward, errors);

        SaveAsset(def, path);
        return def;
    }

    private static QuestStage BuildStage(ParsedStage ps, List<string> errors)
    {
        var stage = new QuestStage
        {
            ConditionType = ps.ConditionType,
            QuestKey = ps.QuestKey,
            Count = ps.Count,
            Quantity = ps.Quantity,
            ReachRadius = ps.ReachRadius,
            Objective = ps.Objective,
            ObjectiveWhenMet = ps.ObjectiveWhenMet
        };

        if (ps.ConditionType == QuestConditionType.Collect)
        {
            if (!string.IsNullOrEmpty(ps.ItemId))
            {
                stage.Item = ItemDatabase.Find(ps.ItemId);
                if (stage.Item == null)
                    errors.Add($"Collect item '{ps.ItemId}' not found in Resources/Items");
            }

            foreach (ParsedCollectItem extra in ps.AlsoCollect)
            {
                ItemData item = ItemDatabase.Find(extra.ItemId);
                if (item == null)
                {
                    errors.Add($"Collect item '{extra.ItemId}' not found in Resources/Items");
                    continue;
                }
                stage.AlsoCollect.Add(new QuestCollectItem { Item = item, Quantity = extra.Quantity });
            }
        }

        return stage;
    }

    private static QuestReward BuildReward(ParsedReward pr, List<string> errors)
    {
        var reward = new QuestReward
        {
            PoundsAmount = pr.Pounds,
            XP = pr.XP,
            Quantity = pr.Quantity,
            ClearsWantedLevel = pr.ClearsWanted
        };
        if (!string.IsNullOrEmpty(pr.ItemId))
        {
            reward.Item = ItemDatabase.Find(pr.ItemId);
            if (reward.Item == null)
                errors.Add($"reward item '{pr.ItemId}' not found in Resources/Items");
        }
        return reward;
    }

    private static bool BuildDialogue(ParsedDialogue parsed, DialogueData asset, PlacementPreset preset, List<string> errors)
    {
        if (parsed.Nodes.Count == 0)
        {
            errors.Add($"Dialogue '{parsed.NpcId}': no NODEs");
            return false;
        }

        asset.StartNodeId = string.IsNullOrEmpty(parsed.StartNodeId) ? DialogueData.DefaultStartId : parsed.StartNodeId;
        if (asset.Nodes == null) asset.Nodes = new List<DialogueNode>();
        asset.Nodes.Clear();

        foreach (ParsedNode pn in parsed.Nodes)
        {
            var node = new DialogueNode
            {
                Id = pn.Id,
                Speaker = ResolveSpeaker(pn.SpeakerId, preset),
                DialogueText = pn.Text ?? ""
            };
            if (node.Choices == null) node.Choices = new List<DialogueChoice>();
            node.Choices.Clear();

            foreach (ParsedChoice pc in pn.Choices)
            {
                var choice = new DialogueChoice
                {
                    ChoiceText = pc.Text,
                    NextNodeId = pc.HasNext ? pc.NextNodeId : null,
                    GrantQuestId = pc.GrantQuestId,
                    CompleteQuestId = pc.CompleteQuestId,
                    RequiredItem = ResolveItem(pc.RequiredItemId, errors),
                    RequiredItemQuantity = Mathf.Max(1, pc.RequiredItemQuantity),
                    ConsumeRequiredItem = pc.ConsumeRequiredItem,
                    QuestGate = pc.QuestGate,
                    QuestGateId = pc.QuestGateId,
                    QuestGateStage = pc.QuestGateStage,
                    TeachSpark = pc.TeachSpark,
                    RequiredStat = pc.RequiredStat,
                    RequiredStatLevel = pc.RequiredStatLevel
                };
                node.Choices.Add(choice);
            }
            asset.Nodes.Add(node);
        }

        return true;
    }

    private static ItemData ResolveItem(string id, List<string> errors)
    {
        if (string.IsNullOrEmpty(id)) return null;
        ItemData item = ItemDatabase.Find(id);
        if (item == null) errors.Add($"item '{id}' not found in Resources/Items");
        return item;
    }

    private static CharacterData ResolveSpeaker(string speakerId, PlacementPreset fallbackPreset)
    {
        if (string.IsNullOrEmpty(speakerId))
            return fallbackPreset != null ? fallbackPreset.Speaker : null;

        PlacementPreset speaker = ResolvePreset(speakerId);
        if (speaker != null && speaker.Speaker != null) return speaker.Speaker;
        return fallbackPreset != null ? fallbackPreset.Speaker : null;
    }

    // ── Preset resolution ──────────────────────────────────────────────────────────────────

    /// <summary>
    /// Finds a <see cref="PlacementPreset"/> for an npcId by label or asset filename, case-
    /// insensitive and ignoring the <c>Preset_</c> filename prefix. Best-effort — the importer
    /// still writes the dialogue if this returns null, it just isn't wired.
    /// </summary>
    private static PlacementPreset ResolvePreset(string npcId)
    {
        if (string.IsNullOrEmpty(npcId)) return null;
        string needle = npcId.Trim().ToLowerInvariant();

        string[] guids = AssetDatabase.FindAssets("t:PlacementPreset");
        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(path);
            if (preset == null) continue;

            string fileName = Path.GetFileNameWithoutExtension(path);
            if (fileName.StartsWith("Preset_")) fileName = fileName.Substring("Preset_".Length);
            if (fileName.Trim().ToLowerInvariant() == needle) return preset;
            if (preset.Label != null && preset.Label.Trim().ToLowerInvariant() == needle) return preset;
        }
        return null;
    }

    // ── Asset save helpers ─────────────────────────────────────────────────────────────────

    private static void SaveAsset(ScriptableObject asset, string path)
    {
        // Update-in-place: load-then-dirty preserves the GUID (and any references to it). The
        // builders already loaded the existing asset before mutating it, so this only creates
        // when the asset is genuinely new.
        var existing = AssetDatabase.LoadAssetAtPath<ScriptableObject>(path);
        if (existing != null)
        {
            EditorUtility.SetDirty(asset);
        }
        else
        {
            AssetDatabase.CreateAsset(asset, path);
        }
    }

    private static string DialoguePathFor(string npcId) => $"{DialogueAssetsFolder}/Dialogue_{npcId}.asset";

    private static void EnsureFolder(string assetFolder)
    {
        if (AssetDatabase.IsValidFolder(assetFolder)) return;

        string[] parts = assetFolder.Split('/');
        string running = parts[0];
        for (int i = 1; i < parts.Length; i++)
        {
            string next = $"{running}/{parts[i]}";
            if (!AssetDatabase.IsValidFolder(next))
                AssetDatabase.CreateFolder(running, parts[i]);
            running = next;
        }
    }

    // ── Small text helpers ─────────────────────────────────────────────────────────────────

    private static string Value(string line)
    {
        int colon = line.IndexOf(':');
        return colon < 0 ? "" : line.Substring(colon + 1).Trim();
    }

    /// <summary>Everything after the leading keyword (which is <paramref name="skipAfter"/> chars).</summary>
    private static string Rest(string line, int skipAfter)
    {
        if (line.Length <= skipAfter) return "";
        return line.Substring(skipAfter).Trim();
    }

    private static int ParseInt(string value, Action err)
    {
        if (int.TryParse(value, out int result)) return result;
        err?.Invoke();
        return 0;
    }
}