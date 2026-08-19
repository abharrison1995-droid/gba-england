using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
using GBHEngland.Combat;
using GBHEngland.Data;
using GBHEngland.World;

namespace GBHEngland.EditorTools
{
    /// <summary>
    /// Editor tool to construct and wire the Castle Fight Pit tournament system:
    /// - Creates FightPitConfig asset in Assets/Resources/
    /// - Registers tournament presets in PlacementPresetLibrary
    /// - Builds Castle_Fight_Arena_Prefab in Assets/Prefabs/Chunks/
    /// - Creates Castle_Fight_Arena_Data in Assets/Data/Chunks/ (SuppressCheckpointSaves = true)
    /// - Registers arena chunk in MapChunkRegistry
    /// - Updates Home_London_Prefab in-place with castle_arena_return spawn point and Prince Mandrew NPC.
    /// </summary>
    public static class BuildCastleFightArenaTool
    {
        private const string ResourcesFolder = "Assets/Resources";
        private const string ChunksDataFolder = "Assets/Data/Chunks";
        private const string ChunksPrefabFolder = "Assets/Prefabs/Chunks";
        private const string DialogueFolder = "Assets/Data/Dialogue/Generated";

        private const string ConfigAssetPath = ResourcesFolder + "/FightPitConfig.asset";
        private const string LibraryAssetPath = ResourcesFolder + "/PlacementPresetLibrary.asset";
        private const string RegistryAssetPath = ResourcesFolder + "/MapChunkRegistry.asset";
        private const string ArenaChunkDataPath = ChunksDataFolder + "/Castle_Fight_Arena_Data.asset";
        private const string ArenaPrefabPath = ChunksPrefabFolder + "/Castle_Fight_Arena_Prefab.prefab";
        private const string HomeLondonPrefabPath = ChunksPrefabFolder + "/Home_London_Prefab.prefab";
        private const string MandrewDialoguePath = DialogueFolder + "/Dialogue_PrinceMandrew.asset";

        private const string ArenaChunkName = "Castle Fight Arena";

        [MenuItem("Tools/Content/Castle Fight Pit/Build Castle Fight Arena")]
        [MenuItem("Tools/Content/Build Castle Fight Arena")]
        public static void BuildAll()
        {
            EnsureDirectories();

            BuildFightPitConfig();
            UpdatePlacementPresetLibrary();
            BuildArenaPrefab();
            BuildArenaChunkData();
            UpdateMapChunkRegistry();
            UpdateHomeLondonPrefab();

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("<color=green>Castle Fight Arena and Tournament System built successfully!</color>");
            EditorUtility.DisplayDialog("Castle Fight Pit", "Castle Fight Arena and Tournament assets created and configured successfully.", "OK");
        }

        private static void EnsureDirectories()
        {
            if (!Directory.Exists(ResourcesFolder)) Directory.CreateDirectory(ResourcesFolder);
            if (!Directory.Exists(ChunksDataFolder)) Directory.CreateDirectory(ChunksDataFolder);
            if (!Directory.Exists(ChunksPrefabFolder)) Directory.CreateDirectory(ChunksPrefabFolder);
            if (!Directory.Exists(DialogueFolder)) Directory.CreateDirectory(DialogueFolder);
        }

        private static void BuildFightPitConfig()
        {
            var config = AssetDatabase.LoadAssetAtPath<FightPitConfig>(ConfigAssetPath);
            bool isNew = false;
            if (config == null)
            {
                config = ScriptableObject.CreateInstance<FightPitConfig>();
                isNew = true;
            }

            config.FirstCompletionBonus = 100;
            config.Rounds = new List<FightPitConfig.Round>
            {
                // Round 1: 2 × Spicehead (1, 1) — £5
                new FightPitConfig.Round
                {
                    Purse = 5,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 },
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 }
                    }
                },
                // Round 2: 2 × Spicehead (1, 1) — £5
                new FightPitConfig.Round
                {
                    Purse = 5,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 },
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 }
                    }
                },
                // Round 3: 2 × Spicehead (1, 1) — £5
                new FightPitConfig.Round
                {
                    Purse = 5,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 },
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 }
                    }
                },
                // Round 4: 2 × Spicehead + 1 × OG (1, 1, 2) — £10
                new FightPitConfig.Round
                {
                    Purse = 10,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 },
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 },
                        new FightPitConfig.Opponent { PresetKey = "OG", BaseLevel = 2 }
                    }
                },
                // Round 5: 2 × Spicehead + 1 × OG (1, 1, 2) — £10
                new FightPitConfig.Round
                {
                    Purse = 10,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 },
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 1 },
                        new FightPitConfig.Opponent { PresetKey = "OG", BaseLevel = 2 }
                    }
                },
                // Round 6: 2 × Spicehead (2, 2) — £15
                new FightPitConfig.Round
                {
                    Purse = 15,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 2 },
                        new FightPitConfig.Opponent { PresetKey = "Spicehead", BaseLevel = 2 }
                    }
                },
                // Round 7: 1 × Tainted + 1 × Neek (3, 1) — £20
                new FightPitConfig.Round
                {
                    Purse = 20,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Tainted", BaseLevel = 3 },
                        new FightPitConfig.Opponent { PresetKey = "Neek", BaseLevel = 1 }
                    }
                },
                // Round 8: 1 × Tainted + 1 × Neek (4, 2) — £20
                new FightPitConfig.Round
                {
                    Purse = 20,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Tainted", BaseLevel = 4 },
                        new FightPitConfig.Opponent { PresetKey = "Neek", BaseLevel = 2 }
                    }
                },
                // Round 9: 2 × Tainted (4, 4) — £25
                new FightPitConfig.Round
                {
                    Purse = 25,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Tainted", BaseLevel = 4 },
                        new FightPitConfig.Opponent { PresetKey = "Tainted", BaseLevel = 4 }
                    }
                },
                // Round 10: 2 × Tainted + 1 × Neek (5, 5, 3) — £35
                new FightPitConfig.Round
                {
                    Purse = 35,
                    Opponents = new List<FightPitConfig.Opponent>
                    {
                        new FightPitConfig.Opponent { PresetKey = "Tainted", BaseLevel = 5 },
                        new FightPitConfig.Opponent { PresetKey = "Tainted", BaseLevel = 5 },
                        new FightPitConfig.Opponent { PresetKey = "Neek", BaseLevel = 3 }
                    }
                }
            };

            if (isNew)
                AssetDatabase.CreateAsset(config, ConfigAssetPath);
            else
                EditorUtility.SetDirty(config);
        }

        private static void UpdatePlacementPresetLibrary()
        {
            var library = AssetDatabase.LoadAssetAtPath<PlacementPresetLibrary>(LibraryAssetPath);
            if (library == null)
            {
                library = ScriptableObject.CreateInstance<PlacementPresetLibrary>();
                AssetDatabase.CreateAsset(library, LibraryAssetPath);
            }

            var map = new Dictionary<string, string>
            {
                { "Spicehead", "Assets/Data/Presets/Preset_Spicehead.asset" },
                { "Neek", "Assets/Data/Presets/Preset_Neek.asset" },
                { "OG", "Assets/Data/Presets/Preset_OG.asset" },
                { "Tainted", "Assets/Data/Presets/Preset_Tainted.asset" }
            };

            foreach (var kvp in map)
            {
                var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(kvp.Value);
                if (preset == null)
                {
                    Debug.LogWarning($"BuildCastleFightArenaTool: Preset at {kvp.Value} not found.");
                    continue;
                }

                bool found = false;
                foreach (var entry in library.Entries)
                {
                    if (entry != null && entry.Key == kvp.Key)
                    {
                        entry.Preset = preset;
                        found = true;
                        break;
                    }
                }

                if (!found)
                {
                    library.Entries.Add(new PlacementPresetLibrary.Entry
                    {
                        Key = kvp.Key,
                        Preset = preset
                    });
                }
            }

            EditorUtility.SetDirty(library);
        }

        private static void BuildArenaPrefab()
        {
            bool exists = File.Exists(ArenaPrefabPath);
            GameObject root = exists 
                ? PrefabUtility.LoadPrefabContents(ArenaPrefabPath) 
                : new GameObject("Castle_Fight_Arena_Prefab");

            try
            {
                var baker = root.GetComponent<RuntimeNavMeshBaker>() ?? root.AddComponent<RuntimeNavMeshBaker>();
                var controller = root.GetComponent<FightPitController>() ?? root.AddComponent<FightPitController>();

                // Floor collider: 32 x 32 arena
                Transform floorT = root.transform.Find("ArenaFloor");
                GameObject floor = floorT != null ? floorT.gameObject : new GameObject("ArenaFloor");
                floor.transform.SetParent(root.transform);
                floor.transform.localPosition = new Vector3(0f, -0.1f, 0f);
                var floorCol = floor.GetComponent<BoxCollider>() ?? floor.AddComponent<BoxCollider>();
                floorCol.size = new Vector3(32f, 0.2f, 32f);

                // Perimeter walls
                EnsureWall(root.transform, "Wall_North", new Vector3(0f, 2f, 16f), new Vector3(32f, 4f, 1f));
                EnsureWall(root.transform, "Wall_South", new Vector3(0f, 2f, -16f), new Vector3(32f, 4f, 1f));
                EnsureWall(root.transform, "Wall_East", new Vector3(16f, 2f, 0f), new Vector3(1f, 4f, 32f));
                EnsureWall(root.transform, "Wall_West", new Vector3(-16f, 2f, 0f), new Vector3(1f, 4f, 32f));

                // Player arrival spawn point
                Transform playerSpawnT = root.transform.Find("PlayerSpawn_Arena");
                GameObject playerSpawn = playerSpawnT != null ? playerSpawnT.gameObject : new GameObject("PlayerSpawn_Arena");
                playerSpawn.transform.SetParent(root.transform);
                playerSpawn.transform.localPosition = new Vector3(0f, 0f, -10f);
                var spawnPoint = playerSpawn.GetComponent<PlayerSpawnPoint>() ?? playerSpawn.AddComponent<PlayerSpawnPoint>();
                spawnPoint.Id = "arena_player";

                // Enemy spawn points
                Transform spawnsHolderT = root.transform.Find("EnemySpawns");
                GameObject spawnsHolder = spawnsHolderT != null ? spawnsHolderT.gameObject : new GameObject("EnemySpawns");
                spawnsHolder.transform.SetParent(root.transform);
                spawnsHolder.transform.localPosition = Vector3.zero;

                Transform sp0 = EnsureSpawnPoint(spawnsHolder.transform, "SpawnPoint_0", new Vector3(0f, 0f, 8f));
                Transform sp1 = EnsureSpawnPoint(spawnsHolder.transform, "SpawnPoint_1", new Vector3(-6f, 0f, 5f));
                Transform sp2 = EnsureSpawnPoint(spawnsHolder.transform, "SpawnPoint_2", new Vector3(6f, 0f, 5f));

                controller.SpawnPoints = new Transform[] { sp0, sp1, sp2 };

                PrefabUtility.SaveAsPrefabAsset(root, ArenaPrefabPath);
            }
            finally
            {
                if (exists)
                    PrefabUtility.UnloadPrefabContents(root);
                else
                    Object.DestroyImmediate(root);
            }
        }

        private static void EnsureWall(Transform parent, string name, Vector3 pos, Vector3 size)
        {
            Transform existing = parent.Find(name);
            GameObject wall = existing != null ? existing.gameObject : new GameObject(name);
            wall.transform.SetParent(parent);
            wall.transform.localPosition = pos;
            var col = wall.GetComponent<BoxCollider>() ?? wall.AddComponent<BoxCollider>();
            col.size = size;
        }

        private static Transform EnsureSpawnPoint(Transform parent, string name, Vector3 pos)
        {
            Transform existing = parent.Find(name);
            GameObject sp = existing != null ? existing.gameObject : new GameObject(name);
            sp.transform.SetParent(parent);
            sp.transform.localPosition = pos;
            return sp.transform;
        }

        private static void BuildArenaChunkData()
        {
            var chunkData = AssetDatabase.LoadAssetAtPath<MapChunkData>(ArenaChunkDataPath);
            bool isNew = false;
            if (chunkData == null)
            {
                chunkData = ScriptableObject.CreateInstance<MapChunkData>();
                isNew = true;
            }

            chunkData.ChunkName = ArenaChunkName;
            chunkData.SuppressCheckpointSaves = true;
            chunkData.IsCity = false;
            chunkData.Coordinates = new Vector2IntCoords(0, -99);
            chunkData.ChunkPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(ArenaPrefabPath);

            if (isNew)
                AssetDatabase.CreateAsset(chunkData, ArenaChunkDataPath);
            else
                EditorUtility.SetDirty(chunkData);
        }

        private static void UpdateMapChunkRegistry()
        {
            var registry = AssetDatabase.LoadAssetAtPath<MapChunkRegistry>(RegistryAssetPath);
            if (registry == null)
            {
                registry = ScriptableObject.CreateInstance<MapChunkRegistry>();
                AssetDatabase.CreateAsset(registry, RegistryAssetPath);
            }

            var arenaChunkData = AssetDatabase.LoadAssetAtPath<MapChunkData>(ArenaChunkDataPath);
            if (arenaChunkData != null && !registry.Chunks.Contains(arenaChunkData))
            {
                registry.Chunks.Add(arenaChunkData);
                EditorUtility.SetDirty(registry);
            }
        }

        private static void UpdateHomeLondonPrefab()
        {
            // Build / update Prince Mandrew dialogue asset
            var dialogue = AssetDatabase.LoadAssetAtPath<DialogueData>(MandrewDialoguePath);
            bool isDialogueNew = false;
            if (dialogue == null)
            {
                dialogue = ScriptableObject.CreateInstance<DialogueData>();
                isDialogueNew = true;
            }

            dialogue.StartNodeId = "start";
            dialogue.Nodes = new List<DialogueNode>
            {
                new DialogueNode
                {
                    Id = "start",
                    DialogueText = "Welcome to the Castle Fight Pit. Ten rounds of brutal combat. Defeat every challenger to build the purse.\n\nYou can cash out for 50% between rounds, and we'll patch you up. Push to the end for the full purse and a £100 Championship bonus. If you fall, you leave with nothing.\n\nAre you ready to enter?",
                    Choices = new List<DialogueChoice>
                    {
                        new DialogueChoice
                        {
                            ChoiceText = "Enter the Fight Pit.",
                            StartsFightPit = true
                        },
                        new DialogueChoice
                        {
                            ChoiceText = "Not right now."
                        }
                    }
                }
            };

            if (isDialogueNew)
                AssetDatabase.CreateAsset(dialogue, MandrewDialoguePath);
            else
                EditorUtility.SetDirty(dialogue);

            if (!File.Exists(HomeLondonPrefabPath)) return;

            GameObject root = PrefabUtility.LoadPrefabContents(HomeLondonPrefabPath);
            if (root == null) return;

            try
            {
                // Ensure castle_arena_return spawn point
                var existingSpawn = PlayerSpawnPoint.FindExact(root, "castle_arena_return");
                if (existingSpawn == null)
                {
                    GameObject returnSpawnObj = new GameObject("PlayerSpawn_CastleArenaReturn");
                    returnSpawnObj.transform.SetParent(root.transform);
                    returnSpawnObj.transform.localPosition = new Vector3(12f, 0f, 15f);
                    var sp = returnSpawnObj.AddComponent<PlayerSpawnPoint>();
                    sp.Id = "castle_arena_return";
                }

                // Ensure Prince Mandrew NPC
                Transform npcTransform = root.transform.Find("NPC_PrinceMandrew");
                if (npcTransform == null)
                {
                    GameObject npc = new GameObject("NPC_PrinceMandrew");
                    npc.transform.SetParent(root.transform);
                    npc.transform.localPosition = new Vector3(10f, 0f, 15f);

                    var interactable = npc.AddComponent<Interactable>();
                    interactable.Prompt = "Talk to Prince Mandrew";
                    interactable.InteractRange = 3f;
                    interactable.Reusable = true;

                    var dialogueInteractable = npc.AddComponent<NPCDialogueInteractable>();
                    dialogueInteractable.Conversation = dialogue;
                }
                else
                {
                    var dialogueInteractable = npcTransform.GetComponent<NPCDialogueInteractable>();
                    if (dialogueInteractable != null)
                        dialogueInteractable.Conversation = dialogue;
                }

                PrefabUtility.SaveAsPrefabAsset(root, HomeLondonPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }
    }
}
