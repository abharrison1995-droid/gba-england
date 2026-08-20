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
        private const string MaterialsFolder = "Assets/Materials";

        private const string FloorMaterialPath = MaterialsFolder + "/mat_arena_regal_floor.mat";
        private const string WallMaterialPath = MaterialsFolder + "/mat_arena_regal_wall.mat";

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
            if (!Directory.Exists(MaterialsFolder)) Directory.CreateDirectory(MaterialsFolder);
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
                var baker = GetOrAdd<RuntimeNavMeshBaker>(root);
                var controller = GetOrAdd<FightPitController>(root);

                // Visible, collidable floor and walls. Regal deep-red velvet materials stand in for a
                // padded-pillow texture — a real bitmap can be dropped onto these two materials later.
                Mesh cubeMesh = GetBuiltinCubeMesh();
                Material floorMat = LoadOrCreateMaterial(FloorMaterialPath, new Color(0.55f, 0.06f, 0.10f), 0.12f);
                Material wallMat = LoadOrCreateMaterial(WallMaterialPath, new Color(0.34f, 0.03f, 0.06f), 0.10f);

                // Floor: 32 x 32, top surface at y = 0 so actors stand on it.
                EnsureBox(root.transform, "ArenaFloor", new Vector3(0f, -0.1f, 0f), new Vector3(32f, 0.2f, 32f), cubeMesh, floorMat);

                // Perimeter walls. The isometric camera sits on the +X / -Z side (offset from
                // EKVibe.Camera* works out to ~(+11, +9, -11)), so the East (+X) and South (-Z) walls
                // are camera-NEAR and kept low so they never occlude the player; the North (+Z) and
                // West (-X) walls are the far side and stay full height. A low wall still blocks a
                // grounded actor — there is no jumping here.
                EnsureBox(root.transform, "Wall_North", new Vector3(0f, 2f, 16f), new Vector3(32f, 4f, 1f), cubeMesh, wallMat);
                EnsureBox(root.transform, "Wall_West", new Vector3(-16f, 2f, 0f), new Vector3(1f, 4f, 32f), cubeMesh, wallMat);
                EnsureBox(root.transform, "Wall_East", new Vector3(16f, 0.5f, 0f), new Vector3(1f, 1f, 32f), cubeMesh, wallMat);
                EnsureBox(root.transform, "Wall_South", new Vector3(0f, 0.5f, -16f), new Vector3(32f, 1f, 1f), cubeMesh, wallMat);

                // Player arrival spawn point
                Transform playerSpawnT = root.transform.Find("PlayerSpawn_Arena");
                GameObject playerSpawn = playerSpawnT != null ? playerSpawnT.gameObject : new GameObject("PlayerSpawn_Arena");
                playerSpawn.transform.SetParent(root.transform);
                playerSpawn.transform.localPosition = new Vector3(0f, 0f, -10f);
                var spawnPoint = GetOrAdd<PlayerSpawnPoint>(playerSpawn);
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

        private const string MandrewPresetPath = "Assets/Data/Presets/Preset_PrinceMandrew.asset";

        /// <summary>
        /// Gives Prince Mandrew his billboard visual from the wired preset, mirroring
        /// <see cref="GBHEngland.World.NpcFactory"/>. The preset only carries an NpcSprite/NpcController
        /// after its ArtSubject matches the imported art and
        /// Tools > Content > Wire Presets From Imported Art has been run — until then this logs a
        /// warning and leaves the NPC bodyless rather than crashing the build.
        /// </summary>
        private static void EnsureMandrewVisual(GameObject npc)
        {
            if (npc == null) return;

            var preset = AssetDatabase.LoadAssetAtPath<PlacementPreset>(MandrewPresetPath);
            if (preset == null)
            {
                Debug.LogWarning($"BuildCastleFightArenaTool: {MandrewPresetPath} not found, so Prince Mandrew has no visual.");
                return;
            }

            if (preset.NpcSprite == null)
            {
                Debug.LogWarning(
                    "BuildCastleFightArenaTool: Preset_PrinceMandrew has no NpcSprite, so Prince Mandrew is invisible. " +
                    "Set its ArtSubject to match the imported art (your sheets are 'mandrew'), then run " +
                    "Tools > Content > Wire Presets From Imported Art, and re-run this tool.");
                return;
            }

            var visual = GetOrAdd<WorldActorVisual>(npc);
            visual.ActorSprite = preset.NpcSprite;
            visual.Height = NpcFactory.HeightFor(preset);
            visual.ApplyVisual();
            if (preset.NpcController != null)
                visual.AttachAnimator(preset.NpcController);
        }

        // Unity-null-aware get-or-add. The `GetComponent<T>() ?? AddComponent<T>()` idiom is unsafe:
        // `??` uses plain reference-null and bypasses Unity's overloaded null check, so a "fake-null"
        // component wrapper is treated as non-null and AddComponent is skipped, producing a
        // MissingComponentException on first access. Always test with `== null` (Unity's overload).
        private static T GetOrAdd<T>(GameObject go) where T : Component
        {
            T component = go.GetComponent<T>();
            if (component == null)
                component = go.AddComponent<T>();
            return component;
        }

        /// <summary>
        /// A visible, collidable box. Dimensions come from the transform scale on a unit cube mesh,
        /// so the BoxCollider size stays 1 (it inherits the scale) — matching mesh and collider
        /// exactly. Idempotent: re-running reconciles an existing collider-only box built by an
        /// earlier version of this tool.
        /// </summary>
        private static void EnsureBox(Transform parent, string name, Vector3 pos, Vector3 size, Mesh mesh, Material material)
        {
            Transform existing = parent.Find(name);
            GameObject go = existing != null ? existing.gameObject : new GameObject(name);
            go.transform.SetParent(parent);
            go.transform.localPosition = pos;
            go.transform.localRotation = Quaternion.identity;
            go.transform.localScale = size;

            var col = GetOrAdd<BoxCollider>(go);
            col.center = Vector3.zero;
            col.size = Vector3.one;

            var mf = GetOrAdd<MeshFilter>(go);
            mf.sharedMesh = mesh;

            var mr = GetOrAdd<MeshRenderer>(go);
            mr.sharedMaterial = material;
        }

        /// <summary>Unity's built-in unit cube mesh, borrowed from a throwaway primitive.</summary>
        private static Mesh GetBuiltinCubeMesh()
        {
            var temp = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Mesh mesh = temp.GetComponent<MeshFilter>().sharedMesh;
            Object.DestroyImmediate(temp);
            return mesh;
        }

        /// <summary>
        /// Loads the material at <paramref name="path"/> or creates it (built-in Standard shader,
        /// matching the project's other materials). Colour and smoothness are re-applied every run so
        /// a tuning change here reaches an already-created material.
        /// </summary>
        private static Material LoadOrCreateMaterial(string path, Color color, float smoothness)
        {
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null)
            {
                mat = new Material(Shader.Find("Standard"));
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.color = color;
            mat.SetFloat("_Glossiness", smoothness);
            mat.SetFloat("_Metallic", 0f);
            EditorUtility.SetDirty(mat);
            return mat;
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
                GameObject npc;
                if (npcTransform == null)
                {
                    npc = new GameObject("NPC_PrinceMandrew");
                    npc.transform.SetParent(root.transform);
                    npc.transform.localPosition = new Vector3(10f, 0f, 15f);

                    var interactable = GetOrAdd<Interactable>(npc);
                    interactable.Prompt = "Talk to Prince Mandrew";
                    interactable.InteractRange = 3f;
                    interactable.Reusable = true;

                    var dialogueInteractable = GetOrAdd<NPCDialogueInteractable>(npc);
                    dialogueInteractable.Conversation = dialogue;
                }
                else
                {
                    npc = npcTransform.gameObject;
                    var dialogueInteractable = npc.GetComponent<NPCDialogueInteractable>();
                    if (dialogueInteractable != null)
                        dialogueInteractable.Conversation = dialogue;
                }

                EnsureMandrewVisual(npc);

                PrefabUtility.SaveAsPrefabAsset(root, HomeLondonPrefabPath);
            }
            finally
            {
                PrefabUtility.UnloadPrefabContents(root);
            }
        }
    }
}
