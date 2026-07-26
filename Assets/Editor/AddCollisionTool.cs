using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using ExiledAlvaston.World;

/// <summary>
/// Imported model-pack props (glb/fbx) never come with colliders, so they're pure visual
/// meshes until something adds one — the player and NavMeshAgent-driven enemies walk straight
/// through. This adds a BoxCollider (sized to the mesh bounds) + EnvironmentBlocker to every
/// renderer under the selection that doesn't already have a Collider, matching how the
/// hand-built walls elsewhere (e.g. Manor Cellars) are already set up. Re-bake the chunk's
/// NavMesh afterward (Tools > Exiled Alvaston > World > Bake Navigation Mesh) so enemy
/// pathing actually routes around the new solid geometry too.
/// </summary>
public static class AddCollisionTool
{
    [MenuItem("Tools/Exiled Alvaston/World/Add Collision To Selection")]
    public static void Run()
    {
        GameObject[] selection = Selection.gameObjects;
        if (selection == null || selection.Length == 0)
        {
            Debug.LogError("Nothing selected. Select the object(s) to make solid (e.g. the 'Neek Box' parent) and run again.");
            return;
        }

        int added = 0;
        foreach (GameObject root in selection)
        {
            foreach (MeshFilter mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh == null) continue;
                GameObject go = mf.gameObject;
                if (go.GetComponent<Collider>() != null) continue; // already solid — leave it alone

                Bounds bounds = mf.sharedMesh.bounds;
                BoxCollider col = Undo.AddComponent<BoxCollider>(go);
                col.center = bounds.center;
                col.size = bounds.size;

                if (go.GetComponent<EnvironmentBlocker>() == null)
                    Undo.AddComponent<EnvironmentBlocker>(go);

                added++;
            }
        }

        if (added == 0)
        {
            Debug.Log("AddCollisionTool: everything in the selection already has a Collider.");
            return;
        }

        foreach (GameObject root in selection)
            EditorSceneManager.MarkSceneDirty(root.scene.IsValid() ? root.scene : EditorSceneManager.GetActiveScene());

        Debug.Log($"AddCollisionTool: added BoxCollider + EnvironmentBlocker to {added} object(s). " +
                  "Now re-bake this chunk's NavMesh (Tools > Exiled Alvaston > World > Bake Navigation Mesh) " +
                  "so enemies path around it too, then save.");
    }
}
