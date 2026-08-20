using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AI;
using UnityEditor;
using GBHEngland.Data;
using GBHEngland.World;

/// <summary>
/// Naming conventions shared by the authoring tool and the validator. Both sides must agree on
/// these or a re-run stops finding what it created and starts duplicating it instead, so they live
/// in one place rather than being spelled out twice.
/// </summary>
public static class LocationLinks
{
    /// <summary>Group all generated link objects sit under, inside a chunk prefab.</summary>
    public const string RootName = "LocationLinks";

    public const string PortalEnterName = "Portal_Enter";
    public const string PortalExitName = "Portal_Exit";

    /// <summary>Arrival marker just outside the exterior door — where exiting the interior lands.</summary>
    public static string OutsideMarkerId(string linkId) => linkId + "_outside";

    /// <summary>Arrival marker just inside the interior door — where entering lands.</summary>
    public static string InsideMarkerId(string linkId) => linkId + "_inside";

    public static string MarkerObjectName(string markerId) => "PlayerSpawn_" + markerId;

    public const string RegistryAssetPath = "Assets/Resources/MapChunkRegistry.asset";

    /// <summary>
    /// How far an arrival marker must sit from the portal that leads back the way you came.
    ///
    /// DungeonPortal shares a 1.5 s static cooldown across every portal, so a marker on top of the
    /// return door does not actually bounce the player straight back. It does leave them standing
    /// inside the return portal's interact radius with the USE prompt already lit, which reads as
    /// having failed to go anywhere.
    /// </summary>
    public const float MinMarkerClearance = 3.5f;

    /// <summary>A link id has to survive being pasted into object names, so keep it plain.</summary>
    public static bool IsValidLinkId(string linkId)
    {
        if (string.IsNullOrEmpty(linkId)) return false;
        foreach (char c in linkId)
            if (!char.IsLetterOrDigit(c) && c != '_' && c != '-') return false;
        return true;
    }
}

/// <summary>
/// Read-only audit of every portal, arrival marker and chunk registration in the project.
///
/// ⚠ It reports and never repairs. Several of the things it looks for — a chunk name that no
/// longer matches, a marker id that moved — are save keys or are referenced by them, and a tool
/// that "helpfully" rewrote one would orphan saves silently (CLAUDE.md §3). Every finding names
/// the asset and the field so a human can make the call.
/// </summary>
public static class LocationLinkValidator
{
    public enum Severity { Error, Warning, Info }

    public struct Finding
    {
        public Severity Level;
        public string Where;
        public string Message;

        public override string ToString()
        {
            string tag = Level == Severity.Error ? "ERROR" : Level == Severity.Warning ? "WARN " : "INFO ";
            return $"[{tag}] {Where}: {Message}";
        }
    }

    /// <summary>Runs every check. Nothing is written; the returned list is the whole result.</summary>
    public static List<Finding> Run()
    {
        var findings = new List<Finding>();

        List<MapChunkData> chunks = AllChunkAssets();
        if (chunks.Count == 0)
        {
            Add(findings, Severity.Warning, "Project", "No MapChunkData assets found at all.");
            return findings;
        }

        CheckChunkNames(findings, chunks);
        CheckRegistry(findings, chunks);

        // linkId -> the prefabs carrying a LocationLinks group with that id. A pair is two.
        var linkOwners = new Dictionary<string, List<string>>();

        foreach (MapChunkData chunk in chunks)
        {
            string where = ChunkLabel(chunk);

            if (chunk.ChunkPrefab == null)
            {
                Add(findings, Severity.Error, where, "No ChunkPrefab assigned — nothing can travel here.");
                continue;
            }

            GameObject root = chunk.ChunkPrefab;
            CheckSpawnPointIds(findings, where, root);
            CollectLinkIds(linkOwners, where, root);
            CheckInterior(findings, chunk, chunks, root);

            foreach (DungeonPortal portal in root.GetComponentsInChildren<DungeonPortal>(true))
                CheckPortal(findings, chunk, portal);
        }

        foreach (var kv in linkOwners)
        {
            if (kv.Value.Count > 2)
            {
                Add(findings, Severity.Error, $"Link '{kv.Key}'",
                    $"Used in {kv.Value.Count} prefabs ({string.Join(", ", kv.Value)}). A link id names one " +
                    "pair of doors and must appear in exactly two — re-running the tool with a reused id " +
                    "rewires the wrong end.");
            }
            else if (kv.Value.Count == 1)
            {
                Add(findings, Severity.Warning, $"Link '{kv.Key}'",
                    $"Only found in {kv.Value[0]} — the other half of the pair is missing. Re-run " +
                    "Create Or Update Linked Pair with both chunks set.");
            }
        }

        if (findings.Count == 0)
            Add(findings, Severity.Info, "Project", "All location links check out.");

        return findings;
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  CHECKS
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private static void CheckChunkNames(List<Finding> findings, List<MapChunkData> chunks)
    {
        var seen = new Dictionary<string, MapChunkData>();
        foreach (MapChunkData chunk in chunks)
        {
            if (string.IsNullOrEmpty(chunk.ChunkName))
            {
                Add(findings, Severity.Error, ChunkLabel(chunk),
                    "ChunkName is empty. It is the save key — a save made here cannot be resolved back.");
                continue;
            }

            if (seen.TryGetValue(chunk.ChunkName, out MapChunkData other))
            {
                Add(findings, Severity.Error, ChunkLabel(chunk),
                    $"ChunkName '{chunk.ChunkName}' is also used by {other.name}. FindChunkByName returns " +
                    "the first match, so one of these two is unreachable. Renaming either orphans saves " +
                    "made in it — decide deliberately.");
            }
            else
            {
                seen[chunk.ChunkName] = chunk;
            }
        }
    }

    private static void CheckRegistry(List<Finding> findings, List<MapChunkData> chunks)
    {
        var registry = AssetDatabase.LoadAssetAtPath<MapChunkRegistry>(LocationLinks.RegistryAssetPath);
        if (registry == null)
        {
            Add(findings, Severity.Warning, "MapChunkRegistry",
                $"No registry asset at {LocationLinks.RegistryAssetPath}. Chunks then resolve only through " +
                "the scene ChunkManager's AllChunks list, so a save made in a chunk missing from that list " +
                "cannot be loaded after a restart. Creating a linked pair creates the registry.");
            return;
        }

        foreach (MapChunkData chunk in chunks)
        {
            if (string.IsNullOrEmpty(chunk.ChunkName)) continue; // already reported
            if (registry.Chunks != null && registry.Chunks.Contains(chunk)) continue;

            Add(findings, Severity.Warning, ChunkLabel(chunk),
                "Not in MapChunkRegistry. It will still load if the scene's AllChunks list has it; if it " +
                "does not, a save made here dies on restart.");
        }
    }

    private static void CheckSpawnPointIds(List<Finding> findings, string where, GameObject root)
    {
        var seen = new HashSet<string>();
        foreach (PlayerSpawnPoint sp in root.GetComponentsInChildren<PlayerSpawnPoint>(true))
        {
            if (string.IsNullOrEmpty(sp.Id)) continue; // the id-less default; several is odd but legal
            if (!seen.Add(sp.Id))
            {
                Add(findings, Severity.Error, where,
                    $"Two PlayerSpawnPoints share the Id '{sp.Id}'. FindExact returns whichever comes " +
                    "first in the hierarchy, so which door you arrive at is down to sibling order.");
            }
        }
    }

    private static void CollectLinkIds(Dictionary<string, List<string>> linkOwners, string where, GameObject root)
    {
        Transform linksRoot = root.transform.Find(LocationLinks.RootName);
        if (linksRoot == null) return;

        for (int i = 0; i < linksRoot.childCount; i++)
        {
            string id = linksRoot.GetChild(i).name;
            if (!linkOwners.TryGetValue(id, out List<string> owners))
            {
                owners = new List<string>();
                linkOwners[id] = owners;
            }
            owners.Add(where);
        }
    }

    private static void CheckPortal(List<Finding> findings, MapChunkData owner, DungeonPortal portal)
    {
        string where = $"{ChunkLabel(owner)} / {PathOf(portal.transform)}";

        if (portal.TargetChunk == null)
        {
            Add(findings, Severity.Error, where, "TargetChunk is empty — USE on it does nothing but log.");
            return;
        }
        if (portal.TargetChunk.ChunkPrefab == null)
        {
            Add(findings, Severity.Error, where,
                $"Targets '{portal.TargetChunk.ChunkName}', which has no ChunkPrefab.");
            return;
        }
        if (portal.TargetChunk == owner)
        {
            Add(findings, Severity.Error, where,
                "Targets its own chunk. Travelling destroys and re-instantiates the chunk you are " +
                "standing in, so this reloads the world and drops every unsaved thing in it.");
            // Still worth running the marker checks below.
        }

        GameObject targetRoot = portal.TargetChunk.ChunkPrefab;

        if (!string.IsNullOrEmpty(portal.TargetSpawnPointId))
        {
            PlayerSpawnPoint marker = FindMarker(targetRoot, portal.TargetSpawnPointId);
            if (marker == null)
            {
                Add(findings, Severity.Error, where,
                    $"TargetSpawnPointId '{portal.TargetSpawnPointId}' does not exist in " +
                    $"'{portal.TargetChunk.ChunkName}'. Travel aborts at runtime and the player stays put.");
            }
            else
            {
                CheckMarkerClearance(findings, where, owner, portal.TargetChunk, targetRoot, marker);
            }
        }
        else if (portal.SpawnPosition == Vector3.zero)
        {
            Add(findings, Severity.Warning, where,
                "No TargetSpawnPointId and a Spawn Position of (0,0,0) — the middle of the chunk, which " +
                "is rarely where a door leads. Give it a marker id.");
        }

        // Reciprocity. A one-way drop is legitimate, so this is a warning, not an error.
        bool hasReturn = false;
        foreach (DungeonPortal back in targetRoot.GetComponentsInChildren<DungeonPortal>(true))
        {
            if (back.TargetChunk == owner) { hasReturn = true; break; }
        }
        if (!hasReturn && portal.TargetChunk != owner)
        {
            Add(findings, Severity.Warning, where,
                $"'{portal.TargetChunk.ChunkName}' has no portal leading back to " +
                $"'{owner.ChunkName}'. One-way on purpose is fine; otherwise the player is stuck inside.");
        }
    }

    /// <summary>
    /// An arrival marker sitting on top of the door back out leaves the player standing in the
    /// return portal's interact radius with its prompt already lit.
    /// </summary>
    private static void CheckMarkerClearance(List<Finding> findings, string where, MapChunkData owner,
                                             MapChunkData targetChunk, GameObject targetRoot,
                                             PlayerSpawnPoint marker)
    {
        Vector3 markerLocal = RootRelative(targetRoot, marker.transform);

        foreach (DungeonPortal back in targetRoot.GetComponentsInChildren<DungeonPortal>(true))
        {
            if (back.TargetChunk != owner) continue;

            Vector3 backLocal = RootRelative(targetRoot, back.transform);
            Vector3 flat = backLocal - markerLocal;
            flat.y = 0f;
            float d = flat.magnitude;
            if (d >= LocationLinks.MinMarkerClearance) continue;

            Add(findings, Severity.Warning, where,
                $"Arrival marker '{marker.Id}' lands {d:0.00} m from the return portal " +
                $"'{PathOf(back.transform)}' in '{targetChunk.ChunkName}' — under the " +
                $"{LocationLinks.MinMarkerClearance:0.0} m clearance. The player arrives already inside " +
                "its USE range, which reads as not having gone anywhere.");
        }
    }

    /// <summary>
    /// Checks that only apply to interiors. "Interior" is inferred rather than flagged: a chunk
    /// with no N/S/E/W neighbours is not part of the overworld grid, so the only way in is a portal.
    /// Nothing on MapChunkData declares this, and adding a flag would be a serialized-field change
    /// for something derivable.
    /// </summary>
    private static void CheckInterior(List<Finding> findings, MapChunkData chunk,
                                      List<MapChunkData> allChunks, GameObject root)
    {
        bool inGrid = chunk.NorthChunk != null || chunk.SouthChunk != null
                   || chunk.EastChunk != null || chunk.WestChunk != null;
        if (inGrid) return;

        bool isPortalTarget = false;
        foreach (MapChunkData other in allChunks)
        {
            if (other.ChunkPrefab == null) continue;
            foreach (DungeonPortal p in other.ChunkPrefab.GetComponentsInChildren<DungeonPortal>(true))
            {
                if (p.TargetChunk == chunk) { isPortalTarget = true; break; }
            }
            if (isPortalTarget) break;
        }
        if (!isPortalTarget) return;

        string where = ChunkLabel(chunk);

        var edges = root.GetComponentsInChildren<ChunkEdge>(true);
        if (edges.Length > 0)
        {
            Add(findings, Severity.Warning, where,
                $"Interior carries {edges.Length} ChunkEdge trigger(s). Its four adjacency slots are " +
                "empty, so walking into one only ever produces \"There's nothing that way.\" Delete them.");
        }

        if (root.GetComponentsInChildren<Collider>(true).Length == 0)
        {
            Add(findings, Severity.Error, where,
                "Interior has no Collider anywhere — no floor. The player falls through, the void " +
                "catcher returns them to the spawn point, and they fall again. Give it a floor before " +
                "wiring a door to it.");
        }

        bool hasAgents = root.GetComponentsInChildren<NavMeshAgent>(true).Length > 0;
        bool hasBaker = root.GetComponentsInChildren<RuntimeNavMeshBaker>(true).Length > 0;
        if (hasAgents && !hasBaker)
        {
            Add(findings, Severity.Warning, where,
                "Interior holds NavMeshAgent-driven characters but no RuntimeNavMeshBaker. Chunks are " +
                "instantiated at runtime, so a scene-baked NavMesh does not cover them and the agents " +
                "will not move. Add RuntimeNavMeshBaker to the prefab root.");
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  SHARED
    // ═══════════════════════════════════════════════════════════════════════════════════════

    public static List<MapChunkData> AllChunkAssets()
    {
        var result = new List<MapChunkData>();
        foreach (string guid in AssetDatabase.FindAssets("t:MapChunkData"))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var chunk = AssetDatabase.LoadAssetAtPath<MapChunkData>(path);
            if (chunk != null) result.Add(chunk);
        }
        return result;
    }

    public static PlayerSpawnPoint FindMarker(GameObject root, string id)
    {
        if (root == null || string.IsNullOrEmpty(id)) return null;
        foreach (PlayerSpawnPoint sp in root.GetComponentsInChildren<PlayerSpawnPoint>(true))
            if (sp.Id == id) return sp;
        return null;
    }

    /// <summary>
    /// Position relative to the prefab root. Chunks are always instantiated at the origin, so this
    /// is what the runtime position will be — reading transform.position off a prefab asset would
    /// silently include whatever pose the root itself happens to carry.
    /// </summary>
    public static Vector3 RootRelative(GameObject root, Transform t)
    {
        return root.transform.InverseTransformPoint(t.position);
    }

    private static string ChunkLabel(MapChunkData chunk)
    {
        return string.IsNullOrEmpty(chunk.ChunkName) ? chunk.name : $"{chunk.name} ({chunk.ChunkName})";
    }

    private static string PathOf(Transform t)
    {
        string path = t.name;
        Transform p = t.parent;
        while (p != null)
        {
            path = p.name + "/" + path;
            p = p.parent;
        }
        return path;
    }

    private static void Add(List<Finding> findings, Severity level, string where, string message)
    {
        findings.Add(new Finding { Level = level, Where = where, Message = message });
    }
}
