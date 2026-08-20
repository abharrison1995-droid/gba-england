using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using GBHEngland.Data;
using GBHEngland.World;
using GBHEngland.Vibe;

/// <summary>
/// Drops a talkable NPC (billboard sprite + Interactable + NPCDialogueInteractable) into the
/// open scene or prefab. Assign the Conversation yourself — the sample-dialogue generator that
/// used to sit in this file was removed with the v1 cast it produced.
///
/// For anything with art behind it, prefer the World Palette (CLAUDE.md §9b): a PlacementPreset
/// carries the sprite, controller, height and dialogue, and NpcFactory builds the same shape.
/// </summary>
public class NPCPlacementTool : EditorWindow
{
    private string _npcName = "Villager";
    private Sprite _sprite;
    private DialogueData _conversation;

    [MenuItem("Tools/Place/NPC Placement")]
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
