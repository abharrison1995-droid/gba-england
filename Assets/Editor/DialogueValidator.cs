using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEditor;
using GBHEngland.Data;

/// <summary>
/// Checks <see cref="DialogueData"/> graphs for the authoring mistakes that the flat, id-referenced
/// format made possible and nothing else catches. Every one of these was found by review rather
/// than by play, and every one of them is silent at runtime — see CLAUDE.md §15.
///
/// <see cref="Validate"/> is deliberately public and free of any UI: the plain-text dialogue
/// importer is meant to call it before it writes an asset, so a bad script is refused at import
/// rather than discovered in play. Keep it that way — no EditorUtility dialogs in here.
/// </summary>
public static class DialogueValidator
{
    public enum Severity { Error, Warning }

    public struct Problem
    {
        public Severity Severity;
        public string Message;

        public Problem(Severity severity, string message)
        {
            Severity = severity;
            Message = message;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════

    [MenuItem("Tools/Content/Validate Dialogue")]
    private static void ValidateAllAssets()
    {
        string[] guids = AssetDatabase.FindAssets("t:DialogueData");
        if (guids.Length == 0)
        {
            Debug.Log("Validate Dialogue: no DialogueData assets exist yet, so there is nothing to " +
                      "check. This is expected until the first conversation is written.");
            return;
        }

        int errors = 0, warnings = 0, cleanAssets = 0;

        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var data = AssetDatabase.LoadAssetAtPath<DialogueData>(path);
            if (data == null) continue;

            List<Problem> problems = Validate(data);
            if (problems.Count == 0)
            {
                cleanAssets++;
                continue;
            }

            var sb = new StringBuilder();
            sb.AppendLine($"Validate Dialogue — {path}");
            bool anyError = false;
            foreach (Problem p in problems)
            {
                if (p.Severity == Severity.Error) { errors++; anyError = true; }
                else warnings++;
                sb.AppendLine($"  [{p.Severity}] {p.Message}");
            }

            // Logged against the asset so clicking the console line selects it.
            if (anyError) Debug.LogError(sb.ToString().TrimEnd(), data);
            else Debug.LogWarning(sb.ToString().TrimEnd(), data);
        }

        Debug.Log($"Validate Dialogue: {guids.Length} asset(s) checked — {cleanAssets} clean, " +
                  $"{errors} error(s), {warnings} warning(s).");
    }

    [MenuItem("CONTEXT/DialogueData/Validate This Conversation")]
    private static void ValidateOne(MenuCommand command)
    {
        var data = command.context as DialogueData;
        if (data == null) return;

        List<Problem> problems = Validate(data);
        if (problems.Count == 0)
        {
            Debug.Log($"Validate Dialogue: '{data.name}' is clean.", data);
            return;
        }

        var sb = new StringBuilder();
        sb.AppendLine($"Validate Dialogue — {data.name}");
        bool anyError = false;
        foreach (Problem p in problems)
        {
            if (p.Severity == Severity.Error) anyError = true;
            sb.AppendLine($"  [{p.Severity}] {p.Message}");
        }

        if (anyError) Debug.LogError(sb.ToString().TrimEnd(), data);
        else Debug.LogWarning(sb.ToString().TrimEnd(), data);
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// Every problem found in <paramref name="data"/>, worst first. An empty list means the graph
    /// is sound — it says nothing about whether the writing is any good.
    /// </summary>
    public static List<Problem> Validate(DialogueData data)
    {
        var problems = new List<Problem>();

        if (data == null)
        {
            problems.Add(new Problem(Severity.Error, "The DialogueData asset is null."));
            return problems;
        }

        if (data.Nodes == null || data.Nodes.Count == 0)
        {
            problems.Add(new Problem(Severity.Error,
                "The conversation has no nodes, so StartDialogue returns immediately and the NPC " +
                "appears to ignore the player."));
            return problems;
        }

        // ---- ids ------------------------------------------------------------------------

        // An unset Id is worth an error of its own rather than only surfacing as a dangling
        // reference: Unity serializes an unset string as "", and "" on a NextNodeId is the
        // legitimate way to end a conversation, so the two failures look identical from the
        // outside and neither logs anything at runtime.
        var seen = new HashSet<string>();
        var duplicated = new HashSet<string>();
        for (int i = 0; i < data.Nodes.Count; i++)
        {
            DialogueNode node = data.Nodes[i];
            if (node == null)
            {
                problems.Add(new Problem(Severity.Error, $"Node {i} is null."));
                continue;
            }

            if (string.IsNullOrEmpty(node.Id))
            {
                problems.Add(new Problem(Severity.Error,
                    $"Node {i} has no Id, so no choice can reach it. If a choice was meant to lead " +
                    "here, note that an empty NextNodeId means \"end the conversation\" instead."));
            }
            else if (!seen.Add(node.Id) && duplicated.Add(node.Id))
            {
                problems.Add(new Problem(Severity.Error,
                    $"Id '{node.Id}' is used by more than one node. FindNode returns the first " +
                    "match by list order, so every later node with this Id is unreachable. Watch " +
                    "for this after using the Inspector's list + button, which copies the last " +
                    "element — Id, Choices and any quest side effects included."));
            }
        }

        // ---- start node -----------------------------------------------------------------

        DialogueNode start = null;
        if (!string.IsNullOrEmpty(data.StartNodeId))
        {
            start = data.FindNode(data.StartNodeId);
            if (start == null)
            {
                problems.Add(new Problem(Severity.Warning,
                    $"StartNodeId is '{data.StartNodeId}', which matches no node. The conversation " +
                    $"will open on Nodes[0] ('{IdOf(data.Nodes[0])}') instead."));
            }
        }
        if (start == null) start = data.Nodes[0];

        // ---- dangling edges -------------------------------------------------------------

        foreach (DialogueNode node in data.Nodes)
        {
            if (node?.Choices == null) continue;
            for (int c = 0; c < node.Choices.Count; c++)
            {
                DialogueChoice choice = node.Choices[c];
                if (choice == null)
                {
                    // Worth an error rather than a skip: DisplayNode reads choice.ChoiceText with
                    // no null check, so this is a NullReferenceException the moment the node shows.
                    problems.Add(new Problem(Severity.Error,
                        $"Node '{IdOf(node)}' choice {c} is null. Displaying this node throws."));
                    continue;
                }
                if (string.IsNullOrEmpty(choice.NextNodeId)) continue;
                if (data.FindNode(choice.NextNodeId) == null)
                {
                    problems.Add(new Problem(Severity.Error,
                        $"Node '{IdOf(node)}' choice {c} points at '{choice.NextNodeId}', which " +
                        "matches no node. At runtime this warns and ends the conversation."));
                }
            }
        }

        // ---- merchant actions ----------------------------------------------------------

        foreach (DialogueNode node in data.Nodes)
        {
            if (node?.Choices == null) continue;
            for (int c = 0; c < node.Choices.Count; c++)
            {
                DialogueChoice choice = node.Choices[c];
                if (choice == null) continue;

                bool hasMerchant = choice.Merchant != null;
                bool hasAction = choice.MerchantAction != MerchantActionType.None;
                if (hasMerchant == hasAction) continue;

                problems.Add(new Problem(Severity.Error,
                    $"Node '{IdOf(node)}' choice {c} must set both Merchant and MerchantAction, " +
                    "or neither. As authored, selecting it cannot open a usable shop."));
            }
        }

        // ---- reachability ---------------------------------------------------------------

        HashSet<DialogueNode> reachable = ReachableFrom(data, start);
        foreach (DialogueNode node in data.Nodes)
        {
            if (node == null || reachable.Contains(node)) continue;
            problems.Add(new Problem(Severity.Warning,
                $"Node '{IdOf(node)}' cannot be reached from the opening node. Its lines will " +
                "never be shown."));
        }

        // ---- the freeze ------------------------------------------------------------------

        // The most serious thing in here. A conversation can only end through a choice, the panel
        // is modal, and PauseManager holds Time.timeScale at 0 — so a node with no route out
        // freezes the game and force-quitting is the only escape. DialogueManager now adds a
        // fallback exit when it detects this, but a graph that needs the fallback is still wrong:
        // the player gets an ending the author never wrote, in the middle of a conversation.
        foreach (DialogueNode node in reachable)
        {
            if (!CanEscapeFrom(data, node, ungatedOnly: false))
            {
                problems.Add(new Problem(Severity.Error,
                    $"There is no way out of node '{IdOf(node)}' — no run of choices from it ever " +
                    "ends the conversation. Give the loop a farewell choice with an empty " +
                    "NextNodeId. Without one this would freeze the game outright; DialogueManager " +
                    "catches it at runtime and appends an exit, but that is a safety net, not the " +
                    "shape you want."));
            }
            else if (!CanEscapeFrom(data, node, ungatedOnly: true))
            {
                problems.Add(new Problem(Severity.Warning,
                    $"Every route out of node '{IdOf(node)}' passes through a choice gated on a " +
                    "stat, an item or a quest state. A player who fails those checks has no way to " +
                    "end the conversation, and gating only gets tighter as it runs — " +
                    "ConsumeRequiredItem takes items away and nothing hands any back. A quest gate " +
                    "is the strongest case: the choice is hidden entirely until its quest reaches " +
                    "the right state, so a node whose only exit is quest-gated is a dead end until " +
                    "then."));
            }
        }

        // ---- double spend ----------------------------------------------------------------

        // RemoveItem runs unconditionally whenever a selectable choice is picked, while
        // CompleteQuest early-returns once the quest is done — so a hand-in a player can walk back
        // into destroys the items a second time, completes nothing, and reports nothing.
        foreach (DialogueNode node in reachable)
        {
            if (node.Choices == null) continue;
            bool consumes = false;
            for (int c = 0; c < node.Choices.Count && !consumes; c++)
            {
                DialogueChoice choice = node.Choices[c];
                consumes = choice != null && choice.RequiredItem != null && choice.ConsumeRequiredItem;
            }
            if (!consumes) continue;

            if (IsInCycle(data, node))
            {
                // Deliberately hedged. A player carrying exactly the required amount hands it over,
                // comes back, and finds the choice greyed out by its own item check — that graph is
                // fine, and calling it broken is how a validator teaches you to ignore it. Only
                // surplus stock makes it a real double spend, and nothing here can know that.
                problems.Add(new Problem(Severity.Warning,
                    $"Node '{IdOf(node)}' takes an item with ConsumeRequiredItem and can be reached " +
                    "again from itself. That is fine for a player carrying exactly what is asked " +
                    "for — the choice greys itself out afterwards — but one carrying spare can hand " +
                    "over twice in a single conversation, destroying the second lot for nothing. " +
                    "Move the hand-in onto a node the conversation cannot return to if that matters."));
            }
        }

        // Errors first, but keeping the order they were found in within each band — ids, then the
        // start node, then dangling edges, then reachability, then the freeze. List.Sort is
        // introsort and unstable, so it would scramble that deliberate reading order.
        var ordered = new List<Problem>(problems.Count);
        foreach (Problem p in problems) if (p.Severity == Severity.Error) ordered.Add(p);
        foreach (Problem p in problems) if (p.Severity != Severity.Error) ordered.Add(p);
        return ordered;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static string IdOf(DialogueNode node)
        => node == null ? "<null>" : (string.IsNullOrEmpty(node.Id) ? "<no id>" : node.Id);

    private static bool IsUngated(DialogueChoice choice)
        => string.IsNullOrEmpty(choice.RequiredStat) && choice.RequiredItem == null
           && choice.QuestGate == QuestGateType.None;

    /// <summary>
    /// Mirrors <c>DialogueManager.CanEscapeFrom</c>. An exit is an empty NextNodeId, an id that
    /// resolves to nothing, or a node with no choices — the three things that end a conversation.
    /// With <paramref name="ungatedOnly"/> the search ignores choices behind a stat or item check,
    /// which answers the harder question of whether a player who fails every check can still leave.
    /// </summary>
    private static bool CanEscapeFrom(DialogueData data, DialogueNode from, bool ungatedOnly)
    {
        if (from == null) return true;

        var visited = new HashSet<DialogueNode>();
        var frontier = new Queue<DialogueNode>();
        frontier.Enqueue(from);

        while (frontier.Count > 0)
        {
            DialogueNode current = frontier.Dequeue();
            if (current == null) continue;
            if (current.Choices == null || current.Choices.Count == 0) return true;

            foreach (DialogueChoice choice in current.Choices)
            {
                if (choice == null) continue;
                // A quest-gated choice is NOT skipped here. The hard-error check (ungatedOnly:
                // false) must treat it as potentially available — the quest state is dynamic and
                // the player may reach the right state, so a node whose only exit is quest-gated
                // is not a permanent dead end. Only the ungatedOnly warning treats it as gated,
                // via IsUngated, which is the correct "not always available" judgement.
                if (ungatedOnly && !IsUngated(choice)) continue;

                if (string.IsNullOrEmpty(choice.NextNodeId)) return true;
                DialogueNode next = data.FindNode(choice.NextNodeId);
                if (next == null) return true;

                if (visited.Add(next)) frontier.Enqueue(next);
            }
        }

        return false;
    }

    private static HashSet<DialogueNode> ReachableFrom(DialogueData data, DialogueNode from)
    {
        var visited = new HashSet<DialogueNode>();
        if (from == null) return visited;

        var frontier = new Queue<DialogueNode>();
        visited.Add(from);
        frontier.Enqueue(from);

        while (frontier.Count > 0)
        {
            DialogueNode current = frontier.Dequeue();
            if (current?.Choices == null) continue;

            foreach (DialogueChoice choice in current.Choices)
            {
                if (choice == null || string.IsNullOrEmpty(choice.NextNodeId)) continue;
                DialogueNode next = data.FindNode(choice.NextNodeId);
                if (next != null && visited.Add(next)) frontier.Enqueue(next);
            }
        }

        return visited;
    }

    /// <summary>True if <paramref name="node"/> can be reached again from itself in one or more steps.</summary>
    private static bool IsInCycle(DialogueData data, DialogueNode node)
    {
        if (node?.Choices == null) return false;

        var visited = new HashSet<DialogueNode>();
        var frontier = new Queue<DialogueNode>();

        // Seeded from the successors rather than from the node itself, so "reachable from itself"
        // means a real round trip rather than the trivially true zero-step case.
        foreach (DialogueChoice choice in node.Choices)
        {
            if (choice == null || string.IsNullOrEmpty(choice.NextNodeId)) continue;
            DialogueNode next = data.FindNode(choice.NextNodeId);
            if (next != null && visited.Add(next)) frontier.Enqueue(next);
        }

        while (frontier.Count > 0)
        {
            DialogueNode current = frontier.Dequeue();
            if (current == node) return true;
            if (current?.Choices == null) continue;

            foreach (DialogueChoice choice in current.Choices)
            {
                if (choice == null || string.IsNullOrEmpty(choice.NextNodeId)) continue;
                DialogueNode next = data.FindNode(choice.NextNodeId);
                if (next != null && visited.Add(next)) frontier.Enqueue(next);
            }
        }

        return false;
    }
}
