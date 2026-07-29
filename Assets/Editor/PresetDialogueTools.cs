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
    /// and has not got one. Returns true if it wrote something.
    ///
    /// Safe to call over every preset, every time: it does nothing unless a line has been typed and
    /// no conversation is linked, so it never overwrites a written conversation and never touches a
    /// preset that is not asking for this.
    /// </summary>
    public static bool EnsureAmbientConversation(PlacementPreset preset)
    {
        if (preset == null) return false;
        if (preset.Conversation != null) return false;
        if (string.IsNullOrWhiteSpace(preset.AmbientLine)) return false;

        preset.Conversation = WriteConversation(preset, preset.AmbientLine.Trim());
        EditorUtility.SetDirty(preset);
        return preset.Conversation != null;
    }

    /// <summary>
    /// One menu item that does the obvious thing: builds the conversation from the ambient line if
    /// there is one, and otherwise mints an empty tree to start writing in. Either way the asset
    /// ends up linked and selected, so the next click is editing it.
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
        preset.Conversation = WriteConversation(preset, line);
        EditorUtility.SetDirty(preset);
        AssetDatabase.SaveAssets();

        if (preset.Conversation == null) return;

        EditorGUIUtility.PingObject(preset.Conversation);
        Selection.activeObject = preset.Conversation;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static DialogueData WriteConversation(PlacementPreset preset, string line)
    {
        string path = PathFor(preset);
        if (string.IsNullOrEmpty(path)) return null;

        EnsureFolder(GeneratedFolder);

        // An orphan left at this path — from a preset whose Conversation was cleared, say — is
        // reused rather than duplicated with a " 1" suffix, which is how a folder fills with
        // near-identical assets nobody can tell apart.
        var data = AssetDatabase.LoadAssetAtPath<DialogueData>(path);
        bool isNew = data == null;
        if (isNew) data = ScriptableObject.CreateInstance<DialogueData>();

        data.StartingNode = new DialogueNode
        {
            // Without a speaker the panel keeps showing whoever talked last, so this is worth
            // setting even when it is null — DialogueManager blanks the field for us now.
            Speaker = preset.Speaker,
            DialogueText = line,
        };

        // No choices on purpose. DialogueManager puts an "End conversation." button under a node
        // with none, so a one-liner closes cleanly without anything being authored for it.

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
