using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AI;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.World
{
    /// <summary>
    /// Bakes a NavMesh at runtime for the chunk this sits on, so NavMeshAgent enemies path around
    /// its buildings/props instead of walking straight into them. Uses Unity's low-level
    /// <see cref="NavMeshBuilder"/> (ships with the base engine — no AI Navigation package needed),
    /// which is required because chunks are instantiated at runtime and a scene-baked NavMesh can't
    /// cover them. Drop it on a chunk prefab root, or add it in code when a chunk loads.
    /// </summary>
    public class RuntimeNavMeshBaker : MonoBehaviour
    {
        [Tooltip("Match the enemy NavMeshAgent radius/height so paths fit through gaps correctly.")]
        public float AgentRadius = 0.3f;
        public float AgentHeight = 1.35f;
        public float AgentClimb = 0.5f;
        public float AgentSlope = 45f;

        private NavMeshDataInstance _instance;
        private NavMeshData _data;

        private void Start()
        {
            Rebake();
        }

        /// <summary>Collects the chunk's renderable geometry and (re)builds its NavMesh.</summary>
        public void Rebake()
        {
            var sources = new List<NavMeshBuildSource>();
            var markups = new List<NavMeshBuildMarkup>();
            // Colliders, not render meshes: imported building meshes often have Read/Write disabled,
            // which throws "mesh not readable" when baked. Colliders sidestep that.
            NavMeshBuilder.CollectSources(transform, ~0, NavMeshCollectGeometry.PhysicsColliders, 0, markups, sources);
            if (sources.Count == 0)
            {
                Debug.LogWarning($"RuntimeNavMeshBaker on {name}: no geometry to bake.");
                return;
            }

            var settings = NavMesh.GetSettingsByID(0); // default (Humanoid) agent — matches EnemyAI's agent
            settings.agentRadius = AgentRadius;
            settings.agentHeight = AgentHeight;
            settings.agentClimb = AgentClimb;
            settings.agentSlope = AgentSlope;

            float span = EKVibe.ChunkSize + 10f;
            var bounds = new Bounds(Vector3.zero, new Vector3(span, 80f, span));

            if (_instance.valid) _instance.Remove();
            _data = NavMeshBuilder.BuildNavMeshData(settings, sources, bounds, transform.position, transform.rotation);
            if (_data != null)
                _instance = NavMesh.AddNavMeshData(_data);
        }

        private void OnDestroy()
        {
            if (_instance.valid) _instance.Remove();
        }
    }
}
