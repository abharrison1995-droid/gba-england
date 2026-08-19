using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;

namespace GBHEngland.World
{
    /// <summary>
    /// One car type a route can spawn, with a relative weight. car_1 (Reliant Robin) is common,
    /// car_2 (Corsa) is rare — the weight is the dial.
    /// </summary>
    [System.Serializable]
    public class TrafficCarEntry
    {
        public VehicleData Car;
        [Tooltip("Relative spawn weight. Robin = 3, Corsa = 1.")]
        public int Weight = 1;
    }

    /// <summary>
    /// Ambient traffic for one road. Lives in the chunk prefab; its child transforms are the
    /// waypoints, read top-to-bottom as drive order. Spawns cars as its own children on a timer;
    /// each car drives the waypoints and destroys itself at the end, so the route is a constant
    /// stream with no persistence and no cross-chunk state.
    ///
    /// Chunk-owned by construction: this component is born and dies with the chunk instance, so
    /// none of the seven chunk-instantiation paths needs to change — a transition destroys the
    /// whole chunk, route and cars together.
    /// </summary>
    public class TrafficRoute : MonoBehaviour
    {
        [Tooltip("Ordered child transforms = waypoints. Cars spawn at index 0 and despawn past the last.")]
        public List<Transform> Waypoints = new List<Transform>();

        [Tooltip("Car types this route can spawn, weighted. Empty = no traffic.")]
        public List<TrafficCarEntry> Cars = new List<TrafficCarEntry>();

        [Tooltip("Villager presets for the fleeing driver on a successful theft. Empty = no driver.")]
        public List<PlacementPreset> DriverPresets = new List<PlacementPreset>();

        [Tooltip("Most cars alive on this route at once.")]
        public int MaxAlive = 2;

        [Tooltip("Base seconds between spawns.")]
        public float SpawnInterval = 12f;

        [Tooltip("Random jitter added to SpawnInterval, so traffic does not arrive in lockstep.")]
        public float SpawnJitter = 4f;

        private float _nextSpawnAt;
        private readonly List<TrafficCar> _activeCars = new List<TrafficCar>();

        /// <summary>
        /// Called when a car on this route is destroyed or stolen (converted to player vehicle).
        /// Removes the car from active tracking and repairs the leader chain for following cars.
        /// </summary>
        public void NotifyCarRemoved(TrafficCar car)
        {
            if (car == null) return;
            int idx = _activeCars.IndexOf(car);
            if (idx < 0) return;

            // Repair: the car behind this one (if any) should now follow this car's leader (if any).
            TrafficCar myLeader = idx > 0 ? _activeCars[idx - 1] : null;
            if (idx + 1 < _activeCars.Count && _activeCars[idx + 1] != null)
                _activeCars[idx + 1].SetLeader(myLeader);

            _activeCars.RemoveAt(idx);
        }

        private void Awake()
        {
            // Children are the waypoints; read them once so the Inspector list stays in sync with
            // the hierarchy without the author having to maintain two copies.
            Waypoints.Clear();
            for (int i = 0; i < transform.childCount; i++)
                Waypoints.Add(transform.GetChild(i));

            _nextSpawnAt = Time.time + SpawnInterval;
        }

        private void Update()
        {
            if (Cars == null || Cars.Count == 0) return;
            if (Waypoints == null || Waypoints.Count == 0) return;

            for (int i = _activeCars.Count - 1; i >= 0; i--)
            {
                if (_activeCars[i] == null)
                {
                    TrafficCar myLeader = i > 0 ? _activeCars[i - 1] : null;
                    if (i + 1 < _activeCars.Count && _activeCars[i + 1] != null)
                        _activeCars[i + 1].SetLeader(myLeader);

                    _activeCars.RemoveAt(i);
                }
            }

            if (_activeCars.Count >= MaxAlive) return;
            if (Time.time < _nextSpawnAt) return;

            _nextSpawnAt = Time.time + SpawnInterval + Random.Range(0f, SpawnJitter);
            SpawnCar();
        }

        private void SpawnCar()
        {
            TrafficCarEntry entry = PickWeighted();
            if (entry == null || entry.Car == null || entry.Car.ChassisPrefab == null) return;

            Transform start = Waypoints[0];
            Quaternion spawnRot = start.rotation;
            if (Waypoints.Count > 1 && Waypoints[1] != null)
            {
                Vector3 toNext = Waypoints[1].position - start.position;
                toNext.y = 0f;
                if (toNext.sqrMagnitude > 0.001f)
                    spawnRot = Quaternion.LookRotation(toNext.normalized, Vector3.up);
            }

            GameObject go = Instantiate(entry.Car.ChassisPrefab, start.position, spawnRot, transform);

            var car = go.GetComponent<TrafficCar>();
            if (car == null)
            {
                Debug.LogWarning($"TrafficRoute: {entry.Car.name}'s chassis has no TrafficCar component — destroyed.");
                Destroy(go);
                return;
            }

            car.Configure(entry.Car, this);

            // Chain: the new car follows the previous active car so it stops behind it
            // rather than clipping through.
            if (_activeCars.Count > 0 && _activeCars[_activeCars.Count - 1] != null)
                car.SetLeader(_activeCars[_activeCars.Count - 1]);

            _activeCars.Add(car);
        }

        private TrafficCarEntry PickWeighted()
        {
            int total = 0;
            foreach (TrafficCarEntry e in Cars)
                total += Mathf.Max(1, e.Weight);

            int roll = Random.Range(0, total);
            int running = 0;
            foreach (TrafficCarEntry e in Cars)
            {
                running += Mathf.Max(1, e.Weight);
                if (roll < running) return e;
            }
            return Cars.Count > 0 ? Cars[0] : null;
        }

        /// <summary>
        /// A random driver preset for the fleeing villager, or null if none are authored.
        /// </summary>
        public PlacementPreset PickDriver()
        {
            if (DriverPresets == null || DriverPresets.Count == 0) return null;
            return DriverPresets[Random.Range(0, DriverPresets.Count)];
        }

        private void OnDrawGizmos()
        {
            // Iterate the children directly rather than the Waypoints list: that list is only
            // populated in Awake, which does not run in edit mode, so reading it here would draw
            // nothing while the route is being authored in Prefab Mode.
            if (transform.childCount == 0) return;

            Gizmos.color = new Color(0.9f, 0.6f, 0.1f, 0.8f);
            Transform prev = null;
            for (int i = 0; i < transform.childCount; i++)
            {
                Transform wp = transform.GetChild(i);
                if (wp == null || !wp.name.StartsWith("WP_")) continue;

                Gizmos.DrawWireSphere(wp.position, 0.4f);
                if (prev != null)
                    Gizmos.DrawLine(prev.position, wp.position);
                prev = wp;
            }
        }
    }
}