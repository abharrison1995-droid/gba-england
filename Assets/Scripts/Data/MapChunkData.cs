using UnityEngine;
using System.Collections.Generic;

namespace GBHEngland.Data
{
    [System.Serializable]
    public struct Vector2IntCoords
    {
        public int X;
        public int Y;
        
        public Vector2IntCoords(int x, int y)
        {
            X = x;
            Y = y;
        }
    }

    /// <summary>
    /// One vehicle placed in a chunk. Authored on the chunk asset rather than dropped into the
    /// chunk prefab, so every vehicle in the world is listed in one place.
    /// </summary>
    [System.Serializable]
    public struct VehicleSpawn
    {
        public VehicleData Vehicle;
        [Tooltip("World position. Chunks are all instantiated at the origin, so this is also local.")]
        public Vector3 Position;
        [Tooltip("Facing, in degrees around Y.")]
        public float YRotation;
    }

    /// <summary>
    /// Configuration for a world chunk in the grid matrix.
    /// </summary>
    [CreateAssetMenu(fileName = "NewMapChunkData", menuName = "GBH England/Data/Map Chunk Data")]
    public class MapChunkData : ScriptableObject
    {
        public string ChunkName;
        
        [Tooltip("The logical grid coordinates of this chunk")]
        public Vector2IntCoords Coordinates;

        [Header("Lockout System")]
        [Tooltip("Is this chunk a City? City chunks spawn police and are subject to Knife lockout timers.")]
        public bool IsCity;

        [Header("Tutorial / Dungeon")]
        [Tooltip("Opening tutorial dungeon (Manor Cellars).")]
        public bool IsTutorialDungeon;
        [Tooltip("While tutorial incomplete, block chunk-edge travel out of this chunk.")]
        public bool LockExitsUntilTutorialComplete;

        [Header("Assets")]
        public GameObject ChunkPrefab;
        
        [Header("Navigation Matrix (Logical adjacency)")]
        public MapChunkData NorthChunk;
        public MapChunkData SouthChunk;
        public MapChunkData EastChunk;
        public MapChunkData WestChunk;

        // Appended, never inserted — existing .asset files carry no value for this and Unity will
        // read it as an empty list, which is the correct default.
        [Header("Vehicles")]
        [Tooltip("Rideable vehicles spawned into this chunk each time it loads. Author them with " +
                 "Tools > Place > Vehicle Placement rather than by hand.")]
        public List<VehicleSpawn> VehicleSpawns = new List<VehicleSpawn>();

        [Header("Save Suppression")]
        [Tooltip("When true, ChunkManager skips checkpoint autosave on arrival.")]
        public bool SuppressCheckpointSaves;
    }
}
