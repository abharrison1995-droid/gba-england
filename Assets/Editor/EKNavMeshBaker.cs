using UnityEngine;
using UnityEditor;
using UnityEngine.AI;
using ExiledAlvaston.World;

/// <summary>
/// Marks active chunk geometry for navigation and bakes the NavMesh.
/// </summary>
public static class EKNavMeshBaker
{
    [MenuItem("Tools/Exiled Alvaston/World/Bake Navigation Mesh")]
    public static void Bake()
    {
        MarkChunkNavigationStatic();

        UnityEditor.AI.NavMeshBuilder.ClearAllNavMeshes();
        UnityEditor.AI.NavMeshBuilder.BuildNavMesh();

        var triangulation = NavMesh.CalculateTriangulation();
        int verts = triangulation.vertices != null ? triangulation.vertices.Length : 0;

        Debug.Log(verts > 0
            ? $"NavMesh baked ({verts} verts) from active chunk geometry."
            : "NavMesh bake produced no surface. Open a chunk scene (Tools/Setup Chunk Scene) and ensure Ground is Navigation Static.");
    }

    public static void MarkChunkNavigationStatic()
    {
        int marked = 0;

        // Prefer the live chunk instance
        ChunkManager mgr = Object.FindObjectOfType<ChunkManager>();
        if (mgr != null && mgr.CurrentChunkInstance != null)
            marked += MarkHierarchy(mgr.CurrentChunkInstance.transform);

        // Also mark any chunk prefab instances sitting in the scene
        foreach (var edge in Object.FindObjectsOfType<ChunkEdge>())
        {
            if (edge == null) continue;
            marked += MarkHierarchy(edge.transform.root);
        }

        // Fallback: any object named Ground
        foreach (var t in Object.FindObjectsOfType<Transform>())
        {
            if (t.name == "Ground")
                marked += MarkObject(t.gameObject, true);
        }

        // Walls / blockers
        foreach (var blocker in Object.FindObjectsOfType<EnvironmentBlocker>())
            marked += MarkObject(blocker.gameObject, true);

        if (marked == 0)
            Debug.LogWarning("Nothing marked Navigation Static. Load a chunk into the scene first.");
        else
            Debug.Log($"Marked {marked} object(s) Navigation Static.");
    }

    private static int MarkHierarchy(Transform root)
    {
        if (root == null) return 0;
        int count = 0;
        foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
        {
            string n = t.name;
            bool floor = n == "Ground" || n.Contains("Floor") || n.Contains("Path") || n.Contains("Road") || n.Contains("Asphalt");
            bool wall = n.Contains("Wall") || n.Contains("Building") || n.Contains("Fence") || n.Contains("Prop");
            bool skip = n.Contains("Edge") || n == "Visual" || n == "ActorVisual" || n == "Nameplate";
            if (skip) continue;

            // Name-based checks above are a fragile allowlist — any imported prop pack (houses,
            // urban pack, etc.) whose names don't match one of those words silently gets skipped
            // and the NavMesh bakes straight through it. A real (non-trigger) collider is a much
            // more reliable signal that something should block/carve the nav mesh.
            bool hasSolidCollider = HasSolidCollider(t);

            if (floor || wall || hasSolidCollider || t.GetComponent<EnvironmentBlocker>() != null)
                count += MarkObject(t.gameObject, true);
        }
        return count;
    }

    private static bool HasSolidCollider(Transform t)
    {
        var col = t.GetComponent<Collider>();
        return col != null && !col.isTrigger;
    }

    private static int MarkObject(GameObject go, bool navigationStatic)
    {
        if (go == null) return 0;
        StaticEditorFlags flags = GameObjectUtility.GetStaticEditorFlags(go);
        StaticEditorFlags next = flags | StaticEditorFlags.BatchingStatic;
        if (navigationStatic) next |= StaticEditorFlags.NavigationStatic;
        if (next == flags) return 0;
        GameObjectUtility.SetStaticEditorFlags(go, next);
        return 1;
    }
}
