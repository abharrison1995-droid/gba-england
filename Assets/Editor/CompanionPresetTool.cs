using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEditor;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;
using ExiledAlvaston.Companions;
using ExiledAlvaston.AI;

/// <summary>
/// Builds the Alex companion instance end to end. Run via:
///   Tools -> Content -> Companions -> Build Alex Companion.
///
/// Alex's art was imported without any PlacementPreset ever claiming the 'alex' ArtSubject, so the
/// importer had nothing to wire his sprite/controller into. This tool closes that gap and then
/// builds the rest. All outputs are new-file-only / update-in-place, never delete-and-recreate
/// (GUID discipline); anything that already exists is left untouched so Inspector tuning survives:
///
///   - Assets/Data/Presets/Preset_Alex.asset — the PlacementPreset carrying ArtSubject 'alex',
///     wired to his generated controller and idle frame (the shared recipe for home and follower).
///   - Assets/Resources/Companions/Companion_alex.asset — the CompanionDefinition (strings +
///     numbers only, the Resources rule): id, stats, price.
///   - Assets/Prefabs/ModernBritain/Companions/CompanionHome_Alex.prefab — the "waiting to be
///     hired" Alex: NpcFactory.Build output stripped to hire-only plus a CompanionHomePresence.
///     **Drag this prefab** into Home_London where Alex should wait. It is a NEW prefab — the tool
///     never edits the committed Home_London chunk prefab. (The Companion_alex.asset is DATA — do
///     not drag it anywhere; CompanionDatabase loads it by id.)
///   - Assets/Data/Dialogue/NPC_Alex.asset + Generated/Dialogue_Alex.asset — the speaker and the
///     recruit conversation. Interacting with the home presence opens it; the "Come with me"
///     choice carries HireCompanionId and DialogueManager runs the hire. The prefab is rewired to
///     the conversation IN PLACE (PrefabUtility.LoadPrefabContents — the GUID never changes).
///
/// It also registers the preset in Assets/Resources/PlacementPresetLibrary.asset (in place, GUID
/// preserved). That registry is the ONLY way runtime code resolves a preset — the home-presence
/// prefab bakes its art in the editor, but the follow-the-player Alex is spawned at runtime by
/// CompanionManager from the library, so without this entry he spawns as the untextured fallback.
///
/// Hiring, following and saving are runtime behaviour — none of it is exercised until the owner
/// presses Play; this tool only authors assets.
/// </summary>
public static class CompanionPresetTool
{
    private const string CompanionId = "alex";
    private const string HomeChunk = "Home_London";

    private const string PresetPath = "Assets/Data/Presets/Preset_Alex.asset";
    private const string DefinitionFolder = "Assets/Resources/Companions";
    private const string DefinitionPath = DefinitionFolder + "/Companion_alex.asset";
    private const string PrefabFolder = "Assets/Prefabs/ModernBritain/Companions";
    private const string PrefabPath = PrefabFolder + "/CompanionHome_Alex.prefab";
    private const string LibraryAssetPath = "Assets/Resources/PlacementPresetLibrary.asset";

    private const string IdleSheetPath = "Assets/Art/Generated/characters/sheet_char_alex_idle.png";
    private const string ControllerPath = "Assets/Animations/Generated/alex_Controller.controller";
    private const float AlexHeight = 1.76f;   // owner's tuned size for Alex (was the 1.35 cast height)

    private const string SpeakerPath = "Assets/Data/Dialogue/NPC_Alex.asset";
    private const string DialoguePath = "Assets/Data/Dialogue/Generated/Dialogue_Alex.asset";
    private const string FollowerDialoguePath = "Assets/Data/Dialogue/Generated/Dialogue_Alex_Follower.asset";

    [MenuItem("Tools/Content/Companions/Build Alex Companion")]
    public static void Build()
    {
        var report = new StringBuilder("Build Alex Companion\n--------------------\n");

        CompanionDefinition definition = EnsureDefinition(report);
        PlacementPreset preset = EnsureAlexPreset(report);
        EnsureLibraryEntry(preset, report);
        EnsureHomePresencePrefab(definition, preset, report);

        CharacterData speaker = EnsureSpeaker(report, preset != null ? preset.NpcSprite : null);
        DialogueData dialogue = EnsureDialogue(report, speaker);
        WireHomePresenceDialogue(dialogue, report);

        DialogueData followerDialogue = EnsureFollowerDialogue(report, speaker);
        WireFollowerDialogue(preset, followerDialogue, report);

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log(report.ToString());
        EditorUtility.DisplayDialog("Build Alex Companion",
            "Done — detail in the Console.\n\nDrag CompanionHome_Alex (in Assets/Prefabs/ModernBritain/Companions) " +
            "into Home_London where Alex should wait, then press Play to test hiring.\n\n" +
            "(Companion_alex.asset is data — CompanionDatabase loads it; do not drag it into a scene.)",
            "OK");
    }

    /// <summary>Creates the definition with Alex's starter block, or returns the existing one untouched.</summary>
    private static CompanionDefinition EnsureDefinition(StringBuilder report)
    {
        EnsureFolder(DefinitionFolder);

        var existing = AssetDatabase.LoadAssetAtPath<CompanionDefinition>(DefinitionPath);
        if (existing != null)
        {
            report.AppendLine("= definition already exists, left alone (Inspector tuning preserved): " + DefinitionPath);
            return existing;
        }

        var def = ScriptableObject.CreateInstance<CompanionDefinition>();
        def.Id = CompanionId;
        def.DisplayName = "Alex";
        def.ArtSubject = CompanionId;
        def.ContractType = CompanionContractType.Paid;
        def.HomeChunkName = HomeChunk;
        def.HomeAnchorId = "";           // owner fills this when the home anchor's QuestKey is fixed
        def.PricePounds = 25;

        def.MaxHealth = 120;
        def.Damage = 8;
        def.MoveSpeed = 4.2f;
        def.AttackRange = 1.6f;
        def.AttackCooldown = 1.3f;
        def.AttackWindup = 0.3f;

        def.HealAmount = 18;
        def.HealCooldown = 20f;
        def.HealPlayerPriorityFraction = 0.4f;

        def.DodgeCooldown = 9f;

        def.Height = 1.76f;   // matches the preset, so the hired follower is the size the owner tuned
        def.Width = 1.62f;    // 1.35 uniform fit x the owner's 1.2 instance scale — NOT the inert 0.85 field

        AssetDatabase.CreateAsset(def, DefinitionPath);
        report.AppendLine("+ definition created: " + DefinitionPath);
        return def;
    }

    /// <summary>
    /// Returns the preset carrying ArtSubject 'alex', creating and wiring Preset_Alex if none
    /// exists. Art is wired exactly as ArtImportTool.WirePresetsForSubject does it: the generated
    /// controller, the idle sheet's frame zero as resting sprite + palette icon, and the cast height.
    /// </summary>
    private static PlacementPreset EnsureAlexPreset(StringBuilder report)
    {
        PlacementPreset existing = FindAlexPreset();
        if (existing != null)
        {
            report.AppendLine("= preset already carries ArtSubject 'alex', left alone: " +
                              AssetDatabase.GetAssetPath(existing));
            return existing;
        }

        var preset = ScriptableObject.CreateInstance<PlacementPreset>();
        preset.Label = "Alex";
        preset.NpcName = "Alex";
        preset.Category = PlacementPreset.PlacementCategory.NPC;
        preset.ArtSubject = CompanionId;

        var controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(ControllerPath);
        if (controller != null) preset.NpcController = controller;

        Sprite resting = LoadIdleFrameZero(IdleSheetPath);
        if (resting != null)
        {
            preset.NpcSprite = resting;
            preset.Icon = resting;
        }
        preset.NpcHeight = AlexHeight;

        AssetDatabase.CreateAsset(preset, PresetPath);
        report.AppendLine("+ preset created and wired: " + PresetPath);
        if (controller == null) report.AppendLine("  ! controller not found at " + ControllerPath + " — import the alex sheets first.");
        if (resting == null) report.AppendLine("  ! idle frame zero not found at " + IdleSheetPath + " — import the alex sheets first.");
        return preset;
    }

    /// <summary>
    /// Registers the preset in the PlacementPresetLibrary so the RUNTIME follower can resolve his
    /// art. Without this the library scan in CompanionManager.ResolveCompanionPreset misses him and
    /// he spawns as the untextured fallback capsule. In place, idempotent, GUID preserved.
    /// </summary>
    private static void EnsureLibraryEntry(PlacementPreset preset, StringBuilder report)
    {
        if (preset == null) return;

        var library = AssetDatabase.LoadAssetAtPath<PlacementPresetLibrary>(LibraryAssetPath);
        if (library == null)
        {
            report.AppendLine("! no PlacementPresetLibrary at " + LibraryAssetPath +
                              " — the runtime follower will fall back to a capsule until one exists.");
            return;
        }

        foreach (PlacementPresetLibrary.Entry e in library.Entries)
        {
            if (e != null && e.Preset == preset)
            {
                report.AppendLine("= preset already registered in the PlacementPresetLibrary.");
                return;
            }
        }

        library.Entries.Add(new PlacementPresetLibrary.Entry { Key = CompanionId, Preset = preset });
        EditorUtility.SetDirty(library);
        report.AppendLine("+ registered 'alex' in the PlacementPresetLibrary (runtime follower can now resolve his art).");
    }

    /// <summary>Creates the droppable home-presence prefab from the preset, or leaves the existing one alone.</summary>
    private static void EnsureHomePresencePrefab(CompanionDefinition definition, PlacementPreset preset, StringBuilder report)
    {
        if (AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath) != null)
        {
            report.AppendLine("= home presence prefab already exists, left alone: " + PrefabPath);
            return;
        }

        if (preset == null)
        {
            report.AppendLine("! no preset to build the home presence from — prefab skipped.");
            return;
        }

        EnsureFolder(PrefabFolder);

        GameObject root = NpcFactory.Build(preset, Vector3.zero, null);
        if (root == null)
        {
            report.AppendLine("! NpcFactory.Build returned null for the alex preset — no prefab written.");
            return;
        }

        try
        {
            root.name = "CompanionHome_Alex";

            // Hire-only: a home presence must not also talk, be robbed, or wander off. Strip whatever
            // the preset would have added; keep the Interactable, the visual and the QuestActor.
            Remove<NPCDialogueInteractable>(root);
            Remove<PickpocketInteractable>(root);
            Remove<NPCWander>(root);

            var presence = root.AddComponent<CompanionHomePresence>();
            presence.Definition = definition;

            // CompanionHomePresence.RefreshPrompt overwrites this at runtime; set a readable default
            // so the object is self-describing in the editor. (No £ glyph — the TMP font lacks it.)
            var interactable = root.GetComponent<Interactable>();
            if (interactable != null)
                interactable.Prompt = "Hire " + (definition != null ? definition.DisplayName : "Alex");

            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            report.AppendLine("+ home presence prefab created: " + PrefabPath +
                              "\n  -> drag it into Home_London where Alex should wait.");
        }
        finally
        {
            Object.DestroyImmediate(root);
        }
    }

    /// <summary>
    /// The CharacterData Alex speaks with in the recruit dialogue (name + his idle frame as the
    /// portrait). New-file-only; an existing asset is left alone so a real portrait survives.
    /// </summary>
    private static CharacterData EnsureSpeaker(StringBuilder report, Sprite portrait)
    {
        var existing = AssetDatabase.LoadAssetAtPath<CharacterData>(SpeakerPath);
        if (existing != null)
        {
            report.AppendLine("= speaker already exists, left alone: " + SpeakerPath);
            return existing;
        }

        var speaker = ScriptableObject.CreateInstance<CharacterData>();
        speaker.CharacterName = "Alex";
        speaker.Portrait = portrait;
        speaker.MaxHealth = 120;
        speaker.MaxManaStamina = 10;

        EnsureFolder(System.IO.Path.GetDirectoryName(SpeakerPath).Replace('\\', '/'));
        AssetDatabase.CreateAsset(speaker, SpeakerPath);
        report.AppendLine("+ speaker created: " + SpeakerPath);
        return speaker;
    }

    /// <summary>
    /// The recruit conversation, with the owner's lines. One node, two exits: "Come with me ..
    /// chap" carries HireCompanionId so DialogueManager runs the hire (the Paid charge still
    /// happens in CompanionManager.BeginContract); "Nah I'm okay" just ends the chat.
    /// New-file-only — once it exists, the words belong to the owner, not the tool.
    /// </summary>
    private static DialogueData EnsureDialogue(StringBuilder report, CharacterData speaker)
    {
        var existing = AssetDatabase.LoadAssetAtPath<DialogueData>(DialoguePath);
        if (existing != null)
        {
            report.AppendLine("= dialogue already exists, left alone: " + DialoguePath);
            return existing;
        }

        var data = ScriptableObject.CreateInstance<DialogueData>();
        data.StartNodeId = DialogueData.DefaultStartId;
        data.Nodes.Add(new DialogueNode
        {
            Id = DialogueData.DefaultStartId,
            Speaker = speaker,
            DialogueText = "Uhh, easy chap. Need a hand? No! Not like that.. christ mate.",
            Choices = new List<DialogueChoice>
            {
                new DialogueChoice { ChoiceText = "Come with me .. chap", NextNodeId = "", HireCompanionId = CompanionId },
                new DialogueChoice { ChoiceText = "Nah I'm okay", NextNodeId = "" },
            },
        });

        EnsureFolder(System.IO.Path.GetDirectoryName(DialoguePath).Replace('\\', '/'));
        AssetDatabase.CreateAsset(data, DialoguePath);
        report.AppendLine("+ dialogue created: " + DialoguePath);
        return data;
    }

    /// <summary>
    /// Points the home presence at the conversation and swaps its prompt to "Talk to Alex".
    /// Edits the EXISTING prefab in place via LoadPrefabContents — never delete-and-recreate,
    /// which would mint a fresh GUID and orphan the instance already placed in Home_London.
    /// </summary>
    private static void WireHomePresenceDialogue(DialogueData dialogue, StringBuilder report)
    {
        if (dialogue == null) return;

        GameObject root = PrefabUtility.LoadPrefabContents(PrefabPath);
        if (root == null)
        {
            report.AppendLine("! could not open " + PrefabPath + " for the dialogue rewire.");
            return;
        }

        try
        {
            bool dirty = false;

            var presence = root.GetComponent<CompanionHomePresence>();
            if (presence != null && presence.Conversation == null)
            {
                presence.Conversation = dialogue;
                dirty = true;
            }

            var interactable = root.GetComponent<Interactable>();
            if (interactable != null && interactable.Prompt != null && interactable.Prompt.StartsWith("Hire "))
            {
                interactable.Prompt = "Talk to Alex";
                dirty = true;
            }

            if (dirty)
            {
                PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
                report.AppendLine("+ home presence rewired to the recruit dialogue (in place, GUID preserved).");
            }
            else
            {
                report.AppendLine("= home presence already wired to the recruit dialogue.");
            }
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(root);
        }
    }

    /// <summary>
    /// The conversation the FOLLOWING Alex offers (combat commands, dismiss). Two nodes: the
    /// greeting with Back me / Chill / head home / Nevermind, and a dismiss confirmation. The
    /// command choices carry CompanionCommand; DialogueManager applies them after the chat closes.
    /// New-file-only - once it exists, the words belong to the owner, not the tool.
    /// </summary>
    private static DialogueData EnsureFollowerDialogue(StringBuilder report, CharacterData speaker)
    {
        var existing = AssetDatabase.LoadAssetAtPath<DialogueData>(FollowerDialoguePath);
        if (existing != null)
        {
            report.AppendLine("= follower dialogue already exists, left alone: " + FollowerDialoguePath);
            return existing;
        }

        var data = ScriptableObject.CreateInstance<DialogueData>();
        data.StartNodeId = DialogueData.DefaultStartId;
        data.Nodes.Add(new DialogueNode
        {
            Id = DialogueData.DefaultStartId,
            Speaker = speaker,
            DialogueText = "What's up, chap?",
            Choices = new List<DialogueChoice>
            {
                new DialogueChoice { ChoiceText = "Back me. *Fight beside you*", NextNodeId = "", CompanionCommand = CompanionCommandType.FightBesideMe },
                new DialogueChoice { ChoiceText = "Chill a minute. *Stop fighting*", NextNodeId = "", CompanionCommand = CompanionCommandType.StopFighting },
                new DialogueChoice { ChoiceText = "You should head home.", NextNodeId = "confirm_dismiss" },
                new DialogueChoice { ChoiceText = "Nevermind.", NextNodeId = "" },
            },
        });
        data.Nodes.Add(new DialogueNode
        {
            Id = "confirm_dismiss",
            Speaker = speaker,
            DialogueText = "You sure, mate? I'll head back.",
            Choices = new List<DialogueChoice>
            {
                new DialogueChoice { ChoiceText = "Yeah, off you go.", NextNodeId = "", CompanionCommand = CompanionCommandType.Dismiss },
                new DialogueChoice { ChoiceText = "Actually, stay.", NextNodeId = DialogueData.DefaultStartId },
            },
        });

        EnsureFolder(System.IO.Path.GetDirectoryName(FollowerDialoguePath).Replace('\\', '/'));
        AssetDatabase.CreateAsset(data, FollowerDialoguePath);
        report.AppendLine("+ follower dialogue created: " + FollowerDialoguePath);
        return data;
    }

    /// <summary>
    /// Points the preset at the follower conversation so CompanionManager.SpawnFollower can wire it
    /// onto the runtime follower. Edits the existing preset in place (SetDirty, GUID preserved).
    /// </summary>
    private static void WireFollowerDialogue(PlacementPreset preset, DialogueData dialogue, StringBuilder report)
    {
        if (preset == null || dialogue == null) return;

        if (preset.FollowerConversation == dialogue)
        {
            report.AppendLine("= preset already wired to the follower dialogue.");
            return;
        }

        preset.FollowerConversation = dialogue;
        EditorUtility.SetDirty(preset);
        report.AppendLine("+ preset wired to the follower dialogue (FollowerConversation).");
    }

    /// <summary>The PlacementPreset carrying ArtSubject 'alex', wherever it lives.</summary>
    private static PlacementPreset FindAlexPreset()
    {
        foreach (string guid in AssetDatabase.FindAssets("t:PlacementPreset"))
        {
            var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(AssetDatabase.GUIDToAssetPath(guid));
            if (preset != null &&
                string.Equals(preset.ArtSubject != null ? preset.ArtSubject.Trim() : null,
                              CompanionId, System.StringComparison.OrdinalIgnoreCase))
                return preset;
        }
        return null;
    }

    /// <summary>Frame zero of a sliced sheet — the resting pose, same frame ArtImportTool picks.</summary>
    private static Sprite LoadIdleFrameZero(string sheetPath)
    {
        return AssetDatabase.LoadAllAssetRepresentationsAtPath(sheetPath)
            .OfType<Sprite>()
            .FirstOrDefault(s => s.name.EndsWith("_0", System.StringComparison.Ordinal));
    }

    private static void EnsureFolder(string folder)
    {
        if (AssetDatabase.IsValidFolder(folder)) return;
        string parent = System.IO.Path.GetDirectoryName(folder).Replace('\\', '/');
        string leaf = System.IO.Path.GetFileName(folder);
        if (!string.IsNullOrEmpty(parent) && !AssetDatabase.IsValidFolder(parent))
            EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, leaf);
    }

    private static void Remove<T>(GameObject go) where T : Component
    {
        var c = go.GetComponent<T>();
        if (c != null) Object.DestroyImmediate(c);
    }
}