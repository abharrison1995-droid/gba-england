using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;
using ExiledAlvaston.Vibe;

/// <summary>
/// Drops a talkable NPC (billboard sprite + Interactable + NPCDialogueInteractable) into the
/// open scene or prefab. Pair with Tools/Exiled Alvaston/Content/Create Sample NPC Dialogues for
/// ready-made conversation assets.
/// </summary>
public class NPCPlacementTool : EditorWindow
{
    private string _npcName = "Villager";
    private Sprite _sprite;
    private DialogueData _conversation;

    [MenuItem("Tools/Exiled Alvaston/Place/NPC Placement")]
    public static void Open()
    {
        GetWindow<NPCPlacementTool>("NPC Placement");
    }

    private void OnGUI()
    {
        EditorGUILayout.HelpBox(
            "Creates a talkable NPC at the Scene view pivot (or under the selected object).\n" +
            "Works in a scene or in Prefab Mode. No sprite = brown capsule placeholder.",
            MessageType.Info);

        _npcName = EditorGUILayout.TextField("NPC Name", _npcName);
        _sprite = (Sprite)EditorGUILayout.ObjectField("Sprite", _sprite, typeof(Sprite), false);
        _conversation = (DialogueData)EditorGUILayout.ObjectField(
            new GUIContent("Conversation", "DialogueData asset — create via the sample generator or the Create menu."),
            _conversation, typeof(DialogueData), false);

        EditorGUILayout.Space();
        if (GUILayout.Button("Create NPC", GUILayout.Height(32)))
            CreateNPC();
    }

    private void CreateNPC()
    {
        PrefabStage stage = PrefabStageUtility.GetCurrentPrefabStage();
        Transform parent = Selection.activeTransform;
        if (parent == null && stage != null)
            parent = stage.prefabContentsRoot.transform;

        Vector3 pos = SceneView.lastActiveSceneView != null
            ? SceneView.lastActiveSceneView.pivot
            : Vector3.zero;
        pos.y = 0f;

        var go = new GameObject($"NPC_{_npcName}");
        Undo.RegisterCreatedObjectUndo(go, "Create NPC");
        if (parent != null)
            go.transform.SetParent(parent, true);
        go.transform.position = pos;

        var interactable = go.AddComponent<Interactable>();
        interactable.Prompt = $"Talk to {_npcName}";
        interactable.InteractRange = 3f;

        var talk = go.AddComponent<NPCDialogueInteractable>();
        talk.Conversation = _conversation;

        if (_sprite != null)
        {
            var visual = go.AddComponent<WorldActorVisual>();
            visual.ActorSprite = _sprite;
            visual.Height = EKVibe.CharacterHeight;
            visual.Width = EKVibe.CharacterWidth;
            visual.ApplyVisual();
        }
        else
        {
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = "PlaceholderBody";
            Object.DestroyImmediate(body.GetComponent<Collider>());
            body.transform.SetParent(go.transform, false);
            float h = EKVibe.CharacterHeight;
            body.transform.localPosition = new Vector3(0f, h * 0.5f, 0f);
            body.transform.localScale = new Vector3(0.5f, h * 0.5f, 0.5f);
            body.GetComponent<Renderer>().sharedMaterial =
                EditorMaterialLibrary.GetOrCreate("NPCPlaceholder", new Color(0.3f, 0.4f, 0.55f));
        }

        Selection.activeGameObject = go;
        EditorSceneManager.MarkSceneDirty(stage != null ? stage.scene : EditorSceneManager.GetActiveScene());
        Debug.Log($"NPCPlacementTool: created 'NPC_{_npcName}' at {pos}. Move into place, Ctrl+S." +
                  (_conversation == null ? " No Conversation assigned yet — the NPC will warn when talked to." : ""));
    }
}

/// <summary>Generates two ready-to-use NPC conversation assets under Assets/Data/Dialogue.</summary>
public static class SampleDialogueGenerator
{
    [MenuItem("Tools/Exiled Alvaston/Content/Create Sample NPC Dialogues")]
    public static void Run()
    {
        const string folder = "Assets/Data/Dialogue";
        if (!AssetDatabase.IsValidFolder("Assets/Data"))
            AssetDatabase.CreateFolder("Assets", "Data");
        if (!AssetDatabase.IsValidFolder(folder))
            AssetDatabase.CreateFolder("Assets/Data", "Dialogue");

        // --- NPC 1: Gate Warden (stat-check example) ---
        CharacterData warden = GetOrCreateCharacter(folder, "Warden Alcott");
        var wardenTree = ScriptableObject.CreateInstance<DialogueData>();
        wardenTree.StartingNode = new DialogueNode
        {
            Speaker = warden,
            DialogueText = "Hold there, exile. London's gates don't open for cellar-rats. State your business.",
            Choices =
            {
                new DialogueChoice
                {
                    ChoiceText = "I fought my way out of the Manor Cellars. I've earned passage.",
                    NextNode = new DialogueNode
                    {
                        Speaker = warden,
                        DialogueText = "The cellars, eh? Then you're tougher than you look. Keep your blade sheathed inside the walls and we'll have no quarrel."
                    }
                },
                new DialogueChoice
                {
                    ChoiceText = "[Shove past him]",
                    RequiredStat = "STR",
                    RequiredStatLevel = 4,
                    NextNode = new DialogueNode
                    {
                        Speaker = warden,
                        DialogueText = "Oof— all right, all right! No need for that. Go on through, brute."
                    }
                },
                new DialogueChoice { ChoiceText = "Never mind." }
            }
        };
        SaveTree(folder, "Dialogue_WardenAlcott", wardenTree);

        // --- NPC 2: Beggar (flavor + rumor hook) ---
        CharacterData beggar = GetOrCreateCharacter(folder, "Old Tam");
        var beggarTree = ScriptableObject.CreateInstance<DialogueData>();
        beggarTree.StartingNode = new DialogueNode
        {
            Speaker = beggar,
            DialogueText = "Spare a coin for Old Tam? No? Then spare an ear — I hear things, sat here by the gates.",
            Choices =
            {
                new DialogueChoice
                {
                    ChoiceText = "What have you heard?",
                    GrantQuestId = "old_manor_rumors",
                    GrantQuestTitle = "Rats in the Manor",
                    GrantQuestObjective = "Old Tam claims someone is paying bandits to move back into the Manor Cellars, west of the gates. Return there and see who's squatting.",
                    NextNode = new DialogueNode
                    {
                        Speaker = beggar,
                        DialogueText = "Bandits been creeping back into the old manor west of here. Someone's paying them, mark me. Nobody squats in a ruin for free."
                    }
                },
                new DialogueChoice { ChoiceText = "Not today, Tam." }
            }
        };
        SaveTree(folder, "Dialogue_OldTam", beggarTree);

        AssetDatabase.SaveAssets();
        Debug.Log($"SampleDialogueGenerator: created Warden Alcott + Old Tam under {folder}. " +
                  "Assign them via Tools/Exiled Alvaston/Place/NPC Placement.");
    }

    private static CharacterData GetOrCreateCharacter(string folder, string name)
    {
        string path = $"{folder}/NPC_{name.Replace(" ", "")}.asset";
        var existing = AssetDatabase.LoadAssetAtPath<CharacterData>(path);
        if (existing != null) return existing;

        var data = ScriptableObject.CreateInstance<CharacterData>();
        data.CharacterName = name;
        data.MaxHealth = 20;
        data.MaxManaStamina = 10;
        AssetDatabase.CreateAsset(data, path);
        return data;
    }

    private static void SaveTree(string folder, string assetName, DialogueData tree)
    {
        string path = $"{folder}/{assetName}.asset";
        var existing = AssetDatabase.LoadAssetAtPath<DialogueData>(path);
        if (existing != null)
        {
            existing.StartingNode = tree.StartingNode;
            EditorUtility.SetDirty(existing);
            Object.DestroyImmediate(tree);
        }
        else
        {
            AssetDatabase.CreateAsset(tree, path);
        }
    }
}
