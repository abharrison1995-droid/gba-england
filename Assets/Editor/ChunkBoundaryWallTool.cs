using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Adds invisible solid walls just outside each chunk's four edge triggers.
///
/// Run via: Tools → World → Add Chunk Boundary Walls
///
/// The edge triggers sit at ±110.2 with a depth of 0.8 (inner face at ±109.8), and the ground
/// plane stops at ±110. The boundary walls sit at ±110.5 (inner face at ±110), so the player
/// contacts the trigger and the wall almost simultaneously. Where a neighbour exists, the
/// transition fires before the wall can block movement. Where no neighbour exists — a dead end,
/// a city lockout, the tutorial lock, the post-arrival grace window — the wall prevents the
/// player from walking off the world.
///
/// Not marked navigation static, so they take no part in the NavMesh bake.
///
/// Idempotent: walls are matched by name, so re-running updates existing ones rather than stacking
/// duplicates. Prefabs are edited in place via LoadPrefabContents/SaveAsPrefabAsset — never deleted
/// and re-created, which would mint a new GUID and orphan every instance (CLAUDE.md §7).
/// </summary>
public static class ChunkBoundaryWallTool
{
    private const string ChunkPrefabFolder = "Assets/Prefabs/Chunks";

    private const float WallThickness = 1f;

    /// <summary>
    /// Centre of the wall, placed so its **inner face lands exactly on the edge of the ground** at
    /// ±110 (the ground is a 220-unit plane).
    ///
    /// This has to be flush, not merely "outside". A wall standing clear of the ground stops the
    /// player's collider with its centre — and therefore its ground contact point — already past
    /// the edge of the floor, so they get blocked and fall anyway, which is the entire failure the
    /// wall exists to prevent.
    ///
    /// The edge triggers now overlap with the wall (inner face at ±109.8, wall inner face at ±110),
    /// so the player contacts both nearly at the same instant. Where a crossing is accepted, the
    /// transition fires before the wall fully arrests movement; where it is declined, OnTriggerStay
    /// keeps re-offering the crossing while the player stands blocked by the wall.
    /// </summary>
    private const float WallDistance = 110f + WallThickness * 0.5f;

    /// <summary>
    /// Longer than the chunk is wide so the four walls overlap at the corners — a gap there is
    /// exactly where the old lateral-carry bug used to push the player.
    /// </summary>
    private const float WallLength = 230f;

    private const float WallHeight = 6f;

    /// <summary>Spans y −0.5 to 5.5: buried slightly so nothing can clip under it at ground level.</summary>
    private const float WallCentreY = 2.5f;

    private static readonly (string Name, Vector3 Position, Vector3 Size)[] Walls =
    {
        ("BoundaryWall_North", new Vector3(0f, WallCentreY,  WallDistance), new Vector3(WallLength, WallHeight, WallThickness)),
        ("BoundaryWall_South", new Vector3(0f, WallCentreY, -WallDistance), new Vector3(WallLength, WallHeight, WallThickness)),
        ("BoundaryWall_East",  new Vector3( WallDistance, WallCentreY, 0f), new Vector3(WallThickness, WallHeight, WallLength)),
        ("BoundaryWall_West",  new Vector3(-WallDistance, WallCentreY, 0f), new Vector3(WallThickness, WallHeight, WallLength)),
    };

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  Edge Trigger Geometry
    // ═══════════════════════════════════════════════════════════════════════════════════════

    /// <summary>
    /// Centre of the edge trigger, just outside the ground plane. The trigger's inner face
    /// lands at ±109.8 so the player must physically reach the perimeter before a crossing fires.
    /// </summary>
    private const float EdgeTriggerDistance = 110.2f;

    /// <summary>Depth of each edge trigger volume along the direction of travel.</summary>
    private const float EdgeTriggerDepth = 0.8f;

    /// <summary>Height of each edge trigger volume.</summary>
    private const float EdgeTriggerHeight = 4f;

    /// <summary>
    /// Expected edge trigger names, keyed by <see cref="GBHEngland.World.Direction"/>.
    /// DiscoverEnglandSetup creates these; we refresh their geometry here.
    /// </summary>
    private static readonly (string Name, Vector3 Position, Vector3 Size)[] EdgeTriggers =
    {
        ("NorthEdge", new Vector3(0f, 1f,  EdgeTriggerDistance), new Vector3(220f, EdgeTriggerHeight, EdgeTriggerDepth)),
        ("SouthEdge", new Vector3(0f, 1f, -EdgeTriggerDistance), new Vector3(220f, EdgeTriggerHeight, EdgeTriggerDepth)),
        ("EastEdge",  new Vector3( EdgeTriggerDistance, 1f, 0f), new Vector3(EdgeTriggerDepth, EdgeTriggerHeight, 220f)),
        ("WestEdge",  new Vector3(-EdgeTriggerDistance, 1f, 0f), new Vector3(EdgeTriggerDepth, EdgeTriggerHeight, 220f)),
    };

    [MenuItem("Tools/World/Add Chunk Boundary Walls")]
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

                int edgesRefreshed = RefreshEdgeTriggers(contents.transform);

                PrefabUtility.SaveAsPrefabAsset(contents, path);
                string edgeNote = edgesRefreshed > 0 ? $", {edgesRefreshed} edge trigger(s) refreshed" : "";
                report.Add($"{System.IO.Path.GetFileNameWithoutExtension(path)}: {added} added, {updated} already present{edgeNote}");
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

    /// <summary>
    /// Repositions and resizes existing <see cref="GBHEngland.World.ChunkEdge"/> trigger colliders
    /// to match the current geometry constants. Only updates edges that already exist — creation
    /// is owned by DiscoverEnglandSetup.
    ///
    /// Returns the number of edge triggers that were refreshed.
    /// </summary>
    private static int RefreshEdgeTriggers(Transform root)
    {
        int refreshed = 0;
        foreach (var edge in EdgeTriggers)
        {
            Transform existing = root.Find(edge.Name);
            if (existing == null) continue;

            existing.localPosition = edge.Position;
            existing.localRotation = Quaternion.identity;

            var box = existing.GetComponent<BoxCollider>();
            if (box != null)
            {
                box.size = edge.Size;
                box.center = Vector3.zero;
            }

            refreshed++;
        }
        return refreshed;
    }
}
