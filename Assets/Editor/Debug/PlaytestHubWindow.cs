using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.AI;
using UnityEditor;
using GBHEngland.Combat;
using GBHEngland.Data;
using GBHEngland.Flow;
using GBHEngland.Systems;
using GBHEngland.UI;
using GBHEngland.World;

/// <summary>
/// One Play Mode dashboard: jump to any chunk, spawn any NPC/Enemy/Chest/Prop preset near the
/// player, and force the wanted level. Replaces DevZoneJump, BanditPracticeSpawner and
/// WantedLevelDebugTool, which each covered one of these and had to be extended by hand every time
/// a new chunk or enemy showed up. This reads both lists live from disk, so a new MapChunkData or
/// PlacementPreset asset appears here with no code change.
///
/// Spawning reuses PlacementBuilders.Build — the same recipe World Palette stamps into a chunk at
/// author time — so an NPC spawned here for testing is built exactly the way NpcFactory builds it
/// in the running game.
/// </summary>
public class PlaytestHubWindow : EditorWindow
{
    private static readonly PlacementPreset.PlacementCategory[] SpawnableCategories =
    {
        PlacementPreset.PlacementCategory.NPC,
        PlacementPreset.PlacementCategory.Enemy,
        PlacementPreset.PlacementCategory.Chest,
        PlacementPreset.PlacementCategory.Prop,
    };

    private MapChunkData[] _chunks = new MapChunkData[0];
    private PlacementPreset[] _presets = new PlacementPreset[0];

    /// <summary>
    /// -1 uses each enemy preset's own Enemy Level. 0 attaches no EnemyLevel component at all.
    /// Higher overrides. Mirrors World Palette's per-stamp level field, for the same reason: a
    /// preset is one asset, so a level living only on it would mean one preset per level band.
    /// </summary>
    private int _enemyLevel = -1;

    private Vector2 _scroll;

    /// <summary>Everything this window has spawned, so Clear Spawned only ever removes its own.</summary>
    private readonly HashSet<int> _spawned = new HashSet<int>();

    [MenuItem("Tools/Debug/Playtest Hub")]
    public static void Open()
    {
        GetWindow<PlaytestHubWindow>("Playtest Hub");
    }

    private void OnEnable() => Refresh();

    private void Refresh()
    {
        _chunks = AssetDatabase.FindAssets("t:MapChunkData")
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<MapChunkData>)
            .Where(c => c != null)
            .OrderBy(c => c.ChunkName)
            .ToArray();

        _presets = AssetDatabase.FindAssets("t:PlacementPreset")
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<PlacementPreset>)
            .Where(p => p != null && SpawnableCategories.Contains(p.Category))
            .OrderBy(p => (int)p.Category)
            .ThenBy(p => p.Label)
            .ToArray();
    }

    private void OnGUI()
    {
        using (new EditorGUILayout.HorizontalScope())
        {
            EditorGUILayout.LabelField("Playtest Hub", EditorStyles.boldLabel);
            if (GUILayout.Button("Refresh", GUILayout.Width(70))) Refresh();
        }

        if (!Application.isPlaying)
            EditorGUILayout.HelpBox("Enter Play Mode first — every action here acts on the live scene.", MessageType.Info);

        _scroll = EditorGUILayout.BeginScrollView(_scroll);

        DrawChunkSection();
        EditorGUILayout.Space(10);
        DrawWantedSection();
        EditorGUILayout.Space(10);
        DrawSpawnSection();

        EditorGUILayout.EndScrollView();
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  JUMP TO CHUNK
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void DrawChunkSection()
    {
        EditorGUILayout.LabelField("Jump To Chunk", EditorStyles.boldLabel);

        if (_chunks.Length == 0)
        {
            EditorGUILayout.LabelField("(none found under Assets/Data/Chunks)", EditorStyles.miniLabel);
            return;
        }

        const int perRow = 3;
        for (int i = 0; i < _chunks.Length; i++)
        {
            if (i % perRow == 0) EditorGUILayout.BeginHorizontal();

            if (GUILayout.Button(_chunks[i].ChunkName))
                JumpTo(_chunks[i]);

            if (i % perRow == perRow - 1 || i == _chunks.Length - 1) EditorGUILayout.EndHorizontal();
        }
    }

    private void JumpTo(MapChunkData chunk)
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("Playtest Hub: enter Play Mode first — this teleports the live player/chunk at runtime.");
            return;
        }

        ChunkManager chunkMgr = ChunkManager.Instance;
        CombatController player = CombatController.Instance;
        if (chunkMgr == null || player == null)
        {
            Debug.LogWarning("Playtest Hub: no live ChunkManager/CombatController found.");
            return;
        }
        if (chunk.ChunkPrefab == null)
        {
            Debug.LogWarning($"Playtest Hub: '{chunk.ChunkName}' has no ChunkPrefab assigned.");
            return;
        }

        if (chunkMgr.CurrentChunkInstance != null)
            Object.Destroy(chunkMgr.CurrentChunkInstance);

        chunkMgr.CurrentChunkData = chunk;
        GameObject instance = Object.Instantiate(chunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
        instance.name = chunk.ChunkPrefab.name;
        chunkMgr.CurrentChunkInstance = instance;

        // Manor Cellars keeps its own authored arrival point — everything else drops just above
        // the origin, which is where every other chunk's playable area actually is.
        Vector3 spawn = chunk.ChunkName == "Manor Cellars" && GameFlowController.Instance != null
            ? GameFlowController.Instance.ManorSpawnPosition
            : Vector3.up;
        chunkMgr.TeleportPlayer(spawn);

        // The old chunk instance is gone, and anything spawned into it went with it.
        _spawned.Clear();

        Debug.Log($"Playtest Hub: teleported to {chunk.ChunkName}.");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  WANTED LEVEL
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void DrawWantedSection()
    {
        EditorGUILayout.LabelField("Wanted Level", EditorStyles.boldLabel);
        using (new EditorGUILayout.HorizontalScope())
        {
            for (int level = 0; level <= 5; level++)
            {
                if (GUILayout.Button(level == 0 ? "Clear" : level.ToString()))
                    SetWanted(level);
            }
        }
    }

    private void SetWanted(int level)
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("Playtest Hub: enter Play Mode first — this sets the live WantedManager at runtime.");
            return;
        }

        WantedManager wanted = WantedManager.Instance;
        if (wanted == null)
        {
            Debug.LogWarning("Playtest Hub: no live WantedManager found.");
            return;
        }

        wanted.CurrentKnives = level;
        if (UIManager.Instance != null)
            UIManager.Instance.UpdateKnivesUI(level);

        Debug.Log($"Playtest Hub: Knives set to {level}.");
    }

    // ═══════════════════════════════════════════════════════════════════════════════════════
    //  SPAWN NEAR PLAYER
    // ═══════════════════════════════════════════════════════════════════════════════════════

    private void DrawSpawnSection()
    {
        using (new EditorGUILayout.HorizontalScope())
        {
            EditorGUILayout.LabelField("Spawn Near Player", EditorStyles.boldLabel);
            if (GUILayout.Button($"Clear Spawned ({_spawned.Count})", GUILayout.Width(140)))
                ClearSpawned();
        }

        _enemyLevel = EditorGUILayout.IntField(
            new GUIContent("Enemy Level", "-1 uses each enemy preset's own Enemy Level. 0 attaches " +
                "no EnemyLevel component at all. Higher overrides. Only read for Enemy-category presets."),
            _enemyLevel);

        if (_presets.Length == 0)
        {
            EditorGUILayout.HelpBox(
                "No NPC/Enemy/Chest/Prop PlacementPreset assets found under Assets/Data/Presets.",
                MessageType.Warning);
            return;
        }

        foreach (var group in _presets.GroupBy(p => p.Category))
        {
            EditorGUILayout.LabelField(group.Key.ToString(), EditorStyles.miniBoldLabel);

            const int perRow = 3;
            List<PlacementPreset> row = group.ToList();
            for (int i = 0; i < row.Count; i++)
            {
                if (i % perRow == 0) EditorGUILayout.BeginHorizontal();

                if (GUILayout.Button(row[i].Label))
                    SpawnNearPlayer(row[i]);

                if (i % perRow == perRow - 1 || i == row.Count - 1) EditorGUILayout.EndHorizontal();
            }
        }
    }

    private void SpawnNearPlayer(PlacementPreset preset)
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("Playtest Hub: enter Play Mode first — this spawns into the live scene.");
            return;
        }

        CombatController player = CombatController.Instance;
        if (player == null)
        {
            Debug.LogWarning("Playtest Hub: no live CombatController found.");
            return;
        }

        Vector3 facing = player.FacingDirection.sqrMagnitude > 0.01f
            ? player.FacingDirection
            : player.transform.forward;
        facing.y = 0f;
        if (facing.sqrMagnitude < 0.01f) facing = Vector3.forward;
        facing.Normalize();

        Vector3 spawnPos = player.transform.position + facing * 3.5f;
        spawnPos.y = 0f;

        if (NavMesh.SamplePosition(spawnPos, out NavMeshHit navHit, 10f, NavMesh.AllAreas))
            spawnPos = navHit.position;
        else
            Debug.LogWarning("Playtest Hub: no NavMesh here — spawning anyway, but it may not path. " +
                              "Run Tools/World/Bake Navigation Mesh, or check RuntimeNavMeshBaker on this chunk.");

        // Parented under the live chunk instance so it is cleaned up the same way everything else
        // the chunk owns is — destroyed with the chunk, never orphaned. Only enemy presets read a
        // level override; everything else keeps -1's "use the preset" meaning, which is moot for
        // non-enemy categories since ApplyEnemyOverrides only acts on an enemy instance anyway.
        Transform parent = ChunkManager.Instance != null && ChunkManager.Instance.CurrentChunkInstance != null
            ? ChunkManager.Instance.CurrentChunkInstance.transform
            : null;

        GameObject created = PlacementBuilders.Build(preset, spawnPos, parent, _enemyLevel);
        if (created == null) return;

        _spawned.Add(created.GetInstanceID());
        Selection.activeGameObject = created;
        Debug.Log($"Playtest Hub: spawned '{created.name}' at {spawnPos}.");
    }

    private void ClearSpawned()
    {
        int removed = 0;
        foreach (int id in _spawned)
        {
            var obj = EditorUtility.InstanceIDToObject(id) as GameObject;
            if (obj == null) continue;
            Object.Destroy(obj);
            removed++;
        }
        _spawned.Clear();
        Debug.Log(removed > 0 ? $"Playtest Hub: cleared {removed} spawned object(s)." : "Playtest Hub: nothing to clear.");
    }
}
