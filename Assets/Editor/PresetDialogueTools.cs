using System.IO;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;

/// <summary>
/// Turns a preset's one-line `AmbientLine` into a real <see cref="DialogueData"/> asset, and gives
/// you a starting point when a character deserves a written conversation instead.
///
/// This is editor-only for a reason worth stating: `AssetDatabase.CreateAsset` does not exist at
/// runtime, so generating a conversation while the game is building an NPC is not an option. It
/// happens when the preset is authored instead, and `NpcFactory` only ever reads the result. The
/// side benefit is that the generated asset is visible on the preset in the Inspector, so you can
/// see and edit what a character will say without placing one.
/// </summary>
public static class PresetDialogueTools
{
    private const string GeneratedFolder = "Assets/Data/Dialogue/Generated";

    /// <summary>
    /// Gives <paramref name="preset"/> a conversation built from its ambient line, if it wants one
    /// and has not got one. Returns true only if it actually wrote the line.
    ///
    /// Safe to call over every preset, every time: it does nothing unless a line has been typed and
    /// no conversation is linked, so it never overwrites a written conversation and never touches a
    /// preset that is not asking for this.
    ///
    /// Adopting an existing written conversation at the generated path counts as false, not true —
    /// the preset still gets linked to it, but the ambient line went unused, and a caller reporting
    /// "generated from its ambient line" would be describing something that did not happen. That is
    /// still a change to the preset though, so <paramref name="adopted"/> reports it separately
    /// rather than leaving it to a console warning nobody reads.
    /// </summary>
    public static bool EnsureAmbientConversation(PlacementPreset preset, out bool adopted)
    {
        adopted = false;

        if (preset == null) return false;
        if (preset.Conversation != null) return false;
        if (string.IsNullOrWhiteSpace(preset.AmbientLine)) return false;

        preset.Conversation = WriteConversation(preset, preset.AmbientLine.Trim(), out bool wroteLine);
        EditorUtility.SetDirty(preset);

        if (preset.Conversation == null) return false;
        if (wroteLine) return true;

        adopted = true;
        return false;
    }

    /// <summary>
    /// One menu item that does the obvious thing: builds the conversation from the ambient line if
    /// there is one, and otherwise mints a one-node tree with empty text to start writing in.
    /// Either way the asset ends up linked and selected, so the next click is editing it.
    ///
    /// Note it mints a node rather than nothing — one node with no choices is exactly the shape
    /// <see cref="HasAuthoredContent"/> reads as regenerable, so anything begun this way is
    /// unprotected until it grows a second node or a choice.
    /// </summary>
    [MenuItem("CONTEXT/PlacementPreset/Create Dialogue")]
    private static void CreateDialogue(MenuCommand command)
    {
        var preset = command.context as PlacementPreset;
        if (preset == null) return;

        if (preset.Conversation != null)
        {
            EditorGUIUtility.PingObject(preset.Conversation);
            Selection.activeObject = preset.Conversation;
            return;
        }

        string line = string.IsNullOrWhiteSpace(preset.AmbientLine) ? "" : preset.AmbientLine.Trim();

        // An orphan at the generated path is adopted rather than overwritten, and that has to hold
        // even when there is no ambient line to write. Passing "" through would clear a one-line
        // conversation someone typed straight into the asset and replace it with empty text —
        // "keep AmbientLine in sync" is no defence against a route that never reads AmbientLine.
        preset.Conversation = WriteConversation(preset, line, out _);
        EditorUtility.SetDirty(preset);
        AssetDatabase.SaveAssets();

        if (preset.Conversation == null) return;

        EditorGUIUtility.PingObject(preset.Conversation);
        Selection.activeObject = preset.Conversation;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// Writes the one-line conversation for <paramref name="preset"/> and returns the asset.
    /// <paramref name="wroteLine"/> is false when an existing written conversation was adopted
    /// rather than regenerated, so callers can report what actually happened.
    /// </summary>
    private static DialogueData WriteConversation(PlacementPreset preset, string line, out bool wroteLine)
    {
        wroteLine = false;

        string path = PathFor(preset);
        if (string.IsNullOrEmpty(path)) return null;

        EnsureFolder(GeneratedFolder);

        // An orphan left at this path — from a preset whose Conversation was cleared, say — is
        // reused rather than duplicated with a " 1" suffix, which is how a folder fills with
        // near-identical assets nobody can tell apart.
        var data = AssetDatabase.LoadAssetAtPath<DialogueData>(path);
        bool isNew = data == null;
        if (isNew)
        {
            data = ScriptableObject.CreateInstance<DialogueData>();
        }
        else if (HasAuthoredContent(data))
        {
            Debug.LogWarning(
                $"PresetDialogueTools: '{path}' already holds a written conversation ({data.Nodes.Count} nodes). " +
                $"Linking it to '{preset.Label}' as-is and leaving the ambient line unused — delete the asset " +
                "by hand if you want it regenerated.", data);
            return data;
        }
        else if (string.IsNullOrWhiteSpace(line) && HasAnyProse(data))
        {
            // The structural guard above cannot tell a hand-edited one-liner from generator output,
            // and the Create Dialogue menu item passes "" whenever AmbientLine is blank — which is
            // the state most NPC presets are in. Together those would let one right-click replace
            // written prose with empty text. Nothing here has a line worth writing, so adopt.
            Debug.LogWarning(
                $"PresetDialogueTools: '{path}' already has dialogue text and '{preset.Label}' has no " +
                "AmbientLine to replace it with. Linking it as-is rather than blanking it — clear the " +
                "asset by hand if you did want to start over.", data);
            return data;
        }

        // HasAuthoredContent and HasAnyProse both allow for a null Nodes; this used to dereference
        // it regardless. Unity does not normally deserialize a List field as null, so only one of
        // those positions could be right — this makes them agree without betting on which.
        if (data.Nodes == null) data.Nodes = new System.Collections.Generic.List<DialogueNode>();

        data.Nodes.Clear();
        data.Nodes.Add(new DialogueNode
        {
            Id = DialogueData.DefaultStartId,
            // Without a speaker the panel keeps showing whoever talked last, so this is worth
            // setting even when it is null — DialogueManager blanks the field for us now.
            Speaker = preset.Speaker,
            DialogueText = line,
        });
        data.StartNodeId = DialogueData.DefaultStartId;
        wroteLine = true;

        // One node, no choices, on purpose. DialogueManager puts an "End conversation." button
        // under a node with none, so a one-liner closes cleanly without anything being authored
        // for it.

        if (isNew) AssetDatabase.CreateAsset(data, path);
        else EditorUtility.SetDirty(data);

        if (preset.Speaker == null)
        {
            Debug.LogWarning(
                $"PresetDialogueTools: '{preset.Label}' has no Speaker, so its dialogue panel will " +
                "show no name. Assign a CharacterData to the preset's Speaker field.", preset);
        }

        return data;
    }

    /// <summary>
    /// True if this looks like something a human wrote rather than a generated one-liner: more
    /// than one node, or a single node that offers a choice.
    /// </summary>
    private static bool HasAuthoredContent(DialogueData data)
    {
        if (data == null || data.Nodes == null) return false;
        if (data.Nodes.Count > 1) return true;
        return data.Nodes.Count == 1 && data.Nodes[0] != null
            && data.Nodes[0].Choices != null && data.Nodes[0].Choices.Count > 0;
    }

    /// <summary>
    /// True if any node already carries dialogue text. Weaker than <see cref="HasAuthoredContent"/>
    /// on purpose: it cannot tell who wrote the line, so it only ever guards against replacing a
    /// line with nothing, never against replacing one line with another.
    /// </summary>
    private static bool HasAnyProse(DialogueData data)
    {
        if (data?.Nodes == null) return false;
        foreach (var node in data.Nodes)
            if (node != null && !string.IsNullOrWhiteSpace(node.DialogueText)) return true;
        return false;
    }

    /// <summary>
    /// Keyed on the preset's own asset filename rather than its Label: two presets are allowed to
    /// share a label, and renaming one would otherwise orphan the asset generated for it.
    /// </summary>
    private static string PathFor(PlacementPreset preset)
    {
        string presetPath = AssetDatabase.GetAssetPath(preset);
        if (string.IsNullOrEmpty(presetPath)) return null;   // not saved to disk yet

        string name = Path.GetFileNameWithoutExtension(presetPath);
        if (name.StartsWith("Preset_")) name = name.Substring("Preset_".Length);

        return $"{GeneratedFolder}/Dialogue_{name}.asset";
    }

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
}
