using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Adds invisible solid walls just outside each chunk's four edge triggers.
///
/// Run via: Tools → GBA → World → Add Chunk Boundary Walls
///
/// The edge triggers sit at ±109 and are only 2 units deep, and the ground plane stops at ±110.
/// Any crossing ChunkManager declines — a dead end, a city lockout, the tutorial lock, the
/// post-arrival grace window — used to leave the player walking straight through the trigger and
/// off the world, with no kill floor to catch them. These walls are the physical backstop.
///
/// Where a neighbour exists the teleport at 109 fires long before the wall at 111 is reached, so
/// they are inert on every working crossing. They are outside the ground plane and are not marked
/// navigation static, so they take no part in the NavMesh bake.
///
/// Idempotent: walls are matched by name, so re-running updates existing ones rather than stacking
/// duplicates. Prefabs are edited in place via LoadPrefabContents/SaveAsPrefabAsset — never deleted
/// and re-created, which would mint a new GUID and orphan every instance (CLAUDE.md §7).
/// </summary>
public static class ChunkBoundaryWallTool
{
    private const string ChunkPrefabFolder = "Assets/Prefabs/Chunks";

    /// <summary>Just outside the edge triggers at ±109, which are 2 units deep (so they end at 110).</summary>
    private const float WallDistance = 111f;

    /// <summary>
    /// Longer than the chunk is wide so the four walls overlap at the corners — a gap there is
    /// exactly where the old lateral-carry bug used to push the player.
    /// </summary>
    private const float WallLength = 230f;

    private const float WallHeight = 6f;
    private const float WallThickness = 1f;

    /// <summary>Spans y −0.5 to 5.5: buried slightly so nothing can clip under it at ground level.</summary>
    private const float WallCentreY = 2.5f;

    private static readonly (string Name, Vector3 Position, Vector3 Size)[] Walls =
    {
        ("BoundaryWall_North", new Vector3(0f, WallCentreY,  WallDistance), new Vector3(WallLength, WallHeight, WallThickness)),
        ("BoundaryWall_South", new Vector3(0f, WallCentreY, -WallDistance), new Vector3(WallLength, WallHeight, WallThickness)),
        ("BoundaryWall_East",  new Vector3( WallDistance, WallCentreY, 0f), new Vector3(WallThickness, WallHeight, WallLength)),
        ("BoundaryWall_West",  new Vector3(-WallDistance, WallCentreY, 0f), new Vector3(WallThickness, WallHeight, WallLength)),
    };

    [MenuItem("Tools/GBA/World/Add Chunk Boundary Walls")]
    public static void Run()
    {
        string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { ChunkPrefabFolder });
        if (guids.Length == 0)
        {
            EditorUtility.DisplayDialog("Chunk Boundary Walls",
                $"No prefabs found in {ChunkPrefabFolder}.", "OK");
            return;
        }

        var report = new List<string>();

        foreach (string guid in guids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            GameObject contents = PrefabUtility.LoadPrefabContents(path);
            try
            {
                int added = 0, updated = 0;
                foreach (var wall in Walls)
                {
                    if (ApplyWall(contents.transform, wall.Name, wall.Position, wall.Size)) added++;
                    else updated++;
                }

                PrefabUtility.SaveAsPrefabAsset(contents, path);
                report.Add($"{System.IO.Path.GetFileNameWithoutExtension(path)}: {added} added, {updated} already present");
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(contents);
            }
        }

        AssetDatabase.SaveAssets();

        var log = new System.Text.StringBuilder();
        log.AppendLine("Chunk Boundary Walls");
        log.AppendLine("────────────────────");
        foreach (string line in report) log.AppendLine("  " + line);
        Debug.Log(log.ToString());

        EditorUtility.DisplayDialog("Chunk Boundary Walls",
            $"{report.Count} chunk prefab(s) processed.\n\nDetail in the Console.", "OK");
    }

    /// <summary>Creates or refreshes one wall. Returns true if it had to be created.</summary>
    private static bool ApplyWall(Transform root, string name, Vector3 position, Vector3 size)
    {
        Transform existing = root.Find(name);
        bool created = existing == null;

        GameObject go;
        if (created)
        {
            go = new GameObject(name);
            go.transform.SetParent(root, false);
        }
        else
        {
            go = existing.gameObject;
        }

        go.transform.localPosition = position;
        go.transform.localRotation = Quaternion.identity;
        go.transform.localScale = Vector3.one;

        // No renderer: the wall is felt, not seen. The isometric camera looks down at the chunk
        // from outside its own edge, so a visible wall would sit between the camera and the player.
        var box = go.GetComponent<BoxCollider>();
        if (box == null) box = go.AddComponent<BoxCollider>();
        box.isTrigger = false;
        box.size = size;
        box.center = Vector3.zero;

        return created;
    }
}
