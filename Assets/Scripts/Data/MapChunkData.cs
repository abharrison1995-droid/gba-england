using UnityEngine;
using System.Collections.Generic;

namespace ExiledAlvaston.Data
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
    /// Configuration for a world chunk in the grid matrix.
    /// </summary>
    [CreateAssetMenu(fileName = "NewMapChunkData", menuName = "ExiledAlvaston/Data/Map Chunk Data")]
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
    }
}
