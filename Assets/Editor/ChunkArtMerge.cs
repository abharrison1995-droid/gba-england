using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

/// <summary>
/// Chunk art utilities:
/// 1) Merge whatever is SELECTED in the Hierarchy into Home_Alvaston_Prefab (so scene-built
///    decoration loads/unloads with the chunk instead of floating over every chunk).
/// 2) Fix magenta/missing materials inside chunk prefabs (in-memory materials created by the
///    old setup scripts don't survive being saved into a prefab).
/// </summary>
public static class ChunkArtMerge
{
    const string HomePrefabPath = "Assets/Prefabs/Chunks/Home_Alvaston_Prefab.prefab";

    [MenuItem("Tools/Exiled Alvaston/World/Merge Selected Into Home Alvaston Prefab")]
    public static void MergeSelected()
    {
        GameObject[] selection = Selection.gameObjects;
        if (selection == null || selection.Length == 0)
        {
            Debug.LogError("Nothing selected. In the Hierarchy, select your art root(s) — e.g. 'Houses' — then run this again.");
            return;
        }

        foreach (GameObject go in selection)
        {
            if (go.scene.IsValid()) continue;
            Debug.LogError($"'{go.name}' is an asset, not a scene object — select the copy in the Hierarchy instead.");
            return;
        }

        GameObject prefabRoot = PrefabUtility.LoadPrefabContents(HomePrefabPath);
        if (prefabRoot == null)
        {
            Debug.LogError($"Could not open {HomePrefabPath}.");
            return;
        }

        try
        {
            foreach (GameObject sceneObj in selection)
            {
                // Re-running with the same selection replaces instead of duplicating
                Transform previous = prefabRoot.transform.Find(sceneObj.name);
                if (previous != null)
                    Object.DestroyImmediate(previous.gameObject);

                GameObject copy = Object.Instantiate(sceneObj, prefabRoot.transform);
                copy.name = sceneObj.name;
                // Chunks always spawn at world origin, so world placement == prefab-local placement
                copy.transform.localPosition = sceneObj.transform.position;
                copy.transform.localRotation = sceneObj.transform.rotation;
                copy.transform.localScale = sceneObj.transform.lossyScale;
                copy.SetActive(true);
            }

            PrefabUtility.SaveAsPrefabAsset(prefabRoot, HomePrefabPath);
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(prefabRoot);
        }

        // Disable (don't delete) the scene originals so the user can verify first
        foreach (GameObject sceneObj in selection)
        {
            Undo.RegisterFullObjectHierarchyUndo(sceneObj, "Merge selected art into prefab");
            sceneObj.SetActive(false);
            if (!sceneObj.name.EndsWith("(merged - safe to delete)"))
                sceneObj.name += " (merged - safe to delete)";
            EditorSceneManager.MarkSceneDirty(sceneObj.scene);
        }

        Debug.Log($"Merged {selection.Length} object(s) into {HomePrefabPath} and disabled the scene copies. " +
                  "Verify in Play Mode, then delete the disabled objects and save the scene. " +
                  "Re-run Tools/Bake Navigation Mesh if props should block walking.");
    }

    [MenuItem("Tools/Exiled Alvaston/Repair/Fix Missing Materials In Chunk Prefabs")]
    public static void FixMissingMaterials()
    {
        Material dungeonMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Placeholders/mat_dungeon_wall.mat");
        Material stoneMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Placeholders/mat_stone.mat");
        if (dungeonMat == null && stoneMat == null)
        {
            Debug.LogError("No placeholder materials found in Assets/Art/Placeholders — run Tools/Exiled Alvaston/Repair/Generate Placeholder Art first.");
            return;
        }

        int totalFixed = 0;
        foreach (string guid in AssetDatabase.FindAssets("t:Prefab", new[] { "Assets/Prefabs/Chunks" }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            bool isDungeon = path.Contains("Manor_Cellars");
            Material replacement = isDungeon ? (dungeonMat ?? stoneMat) : (stoneMat ?? dungeonMat);

            GameObject root = PrefabUtility.LoadPrefabContents(path);
            try
            {
                int fixedHere = 0;
                foreach (Renderer r in root.GetComponentsInChildren<Renderer>(true))
                {
                    Material[] mats = r.sharedMaterials;
                    bool changed = false;
                    for (int i = 0; i < mats.Length; i++)
                    {
                        // Null slot, or a material whose shader failed to load → renders magenta
                        if (mats[i] == null || mats[i].shader == null
                            || mats[i].shader.name == "Hidden/InternalErrorShader")
                        {
                            mats[i] = replacement;
                            changed = true;
                        }
                    }
                    if (changed)
                    {
                        r.sharedMaterials = mats;
                        fixedHere++;
                    }
                }

                if (fixedHere > 0)
                {
                    PrefabUtility.SaveAsPrefabAsset(root, path);
                    Debug.Log($"{path}: fixed {fixedHere} renderer(s).");
                    totalFixed += fixedHere;
                }
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }

        Debug.Log(totalFixed > 0
            ? $"Fixed {totalFixed} broken renderer(s) across chunk prefabs."
            : "No broken materials found in chunk prefabs.");
    }
}
