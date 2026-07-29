using UnityEngine;
using System.Collections.Generic;
using ExiledAlvaston.Data;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Spawns each chunk's authored vehicles as children of the live chunk instance, so they exist
    /// only in the chunks that list them and are cleaned up by the same Destroy that removes the
    /// chunk. Re-entering a chunk gives you fresh vehicles at their authored spots.
    ///
    /// Bootstraps itself — nothing needs placing in the scene.
    /// </summary>
    public class VehicleSpawner : MonoBehaviour
    {
        public static VehicleSpawner Instance { get; private set; }

        private MapChunkData _spawnedFor;
        private GameObject _spawnedInto;

        // What each chunk's spawn entries produced last time, indexed to match VehicleSpawns.
        // A parked vehicle dies with its chunk and reads back as null here, so it respawns; one
        // you rode out on left its chunk and is still alive, so its entry stays occupied.
        private readonly Dictionary<MapChunkData, VehicleController[]> _live =
            new Dictionary<MapChunkData, VehicleController[]>();

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (Instance != null) return;

            var go = new GameObject("~VehicleSpawner");
            DontDestroyOnLoad(go);
            go.AddComponent<VehicleSpawner>();
        }

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        // Polls rather than hooking a transition, for the reason given on VehicleController.Update:
        // CurrentChunkData is written from seven places across six files, so any one hook would
        // miss the other transition paths. Watching the instance as well as the data catches a
        // reload of the same chunk — dying in Home_London and respawning into it, for one.
        private void Update()
        {
            var chunks = ChunkManager.Instance;
            if (chunks == null) return;

            MapChunkData data = chunks.CurrentChunkData;
            GameObject instance = chunks.CurrentChunkInstance;

            // Mid-transition the pair is briefly incomplete; wait rather than recording that state.
            if (data == null || instance == null) return;
            if (data == _spawnedFor && instance == _spawnedInto) return;

            _spawnedFor = data;
            _spawnedInto = instance;
            SpawnFor(data, instance);
        }

        private void SpawnFor(MapChunkData data, GameObject chunkInstance)
        {
            if (data.VehicleSpawns == null) return;

            int count = data.VehicleSpawns.Count;
            if (!_live.TryGetValue(data, out VehicleController[] live) || live.Length != count)
            {
                live = new VehicleController[count];
                _live[data] = live;
            }

            for (int i = 0; i < count; i++)
            {
                // Still alive means you rode this one out of the chunk and brought it back. Without
                // this check every round trip while mounted minted another one from the same entry.
                if (live[i] != null) continue;

                VehicleSpawn spawn = data.VehicleSpawns[i];

                if (spawn.Vehicle == null)
                {
                    Debug.LogWarning($"VehicleSpawner: {data.ChunkName} vehicle spawn {i} has no VehicleData — skipped.");
                    continue;
                }
                if (spawn.Vehicle.ChassisPrefab == null)
                {
                    Debug.LogWarning($"VehicleSpawner: {spawn.Vehicle.name} has no ChassisPrefab — skipped.");
                    continue;
                }

                GameObject go = Instantiate(
                    spawn.Vehicle.ChassisPrefab,
                    spawn.Position,
                    Quaternion.Euler(0f, spawn.YRotation, 0f),
                    chunkInstance.transform);

                var vehicle = go.GetComponent<VehicleController>();
                if (vehicle == null)
                {
                    Debug.LogWarning($"VehicleSpawner: {spawn.Vehicle.name}'s chassis has no VehicleController.");
                    continue;
                }

                vehicle.Apply(spawn.Vehicle);
                vehicle.MarkChunkOwned();
                live[i] = vehicle;
            }
        }
    }
}
