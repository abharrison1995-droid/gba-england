using UnityEngine;
using UnityEditor;
using ExiledAlvaston.World;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;

/// <summary>
/// Dev shortcut: teleport between the Manor Cellars tutorial dungeon and Home_Alvaston
/// during Play Mode, without replaying the title screen / tutorial exit gate each time.
/// Looks chunks up directly from disk rather than ChunkManager.AllChunks, so it works even
/// if that registry hasn't been refreshed since a new chunk was added.
/// </summary>
public static class DevZoneJump
{
    [MenuItem("Tools/Exiled Alvaston/Debug/Jump To Manor Cellars")]
    public static void JumpToManorCellars()
    {
        Vector3 spawn = GameFlowController.Instance != null
            ? GameFlowController.Instance.ManorSpawnPosition
            : new Vector3(0f, 0f, -8f);
        Jump("Manor Cellars", spawn);
    }

    [MenuItem("Tools/Exiled Alvaston/Debug/Jump To Home Alvaston")]
    public static void JumpToHomeAlvaston()
    {
        Jump("Home_Alvaston", Vector3.up);
    }

    private static void Jump(string chunkName, Vector3 spawnPos)
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("DevZoneJump: enter Play Mode first — this teleports the live player/chunk at runtime.");
            return;
        }

        ChunkManager chunkMgr = ChunkManager.Instance;
        CombatController player = CombatController.Instance;
        if (chunkMgr == null || player == null)
        {
            Debug.LogWarning("DevZoneJump: no live ChunkManager/CombatController found.");
            return;
        }

        MapChunkData chunk = FindChunkAsset(chunkName);
        if (chunk == null || chunk.ChunkPrefab == null)
        {
            Debug.LogWarning($"DevZoneJump: couldn't find a chunk named '{chunkName}' under Assets/Data/Chunks.");
            return;
        }

        if (chunkMgr.CurrentChunkInstance != null)
            Object.Destroy(chunkMgr.CurrentChunkInstance);

        chunkMgr.CurrentChunkData = chunk;
        GameObject instance = Object.Instantiate(chunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
        instance.name = chunk.ChunkPrefab.name;
        chunkMgr.CurrentChunkInstance = instance;

        chunkMgr.TeleportPlayer(spawnPos);

        Debug.Log($"DevZoneJump: teleported to {chunkName}.");
    }

    private static MapChunkData FindChunkAsset(string chunkName)
    {
        string[] guids = AssetDatabase.FindAssets("t:MapChunkData", new[] { "Assets/Data/Chunks" });
        foreach (string guid in guids)
        {
            var data = AssetDatabase.LoadAssetAtPath<MapChunkData>(AssetDatabase.GUIDToAssetPath(guid));
            if (data != null && data.ChunkName == chunkName) return data;
        }
        return null;
    }
}
