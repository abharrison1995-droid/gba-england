using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Data
{
    /// <summary>
    /// One thing the World Palette can stamp into the world. Replaces the per-type placement
    /// windows: instead of a window whose fields you fill in before every placement, a preset is
    /// an asset you configure once and then click to place, as many times as you like.
    ///
    /// Two ways to build: assign <see cref="Prefab"/> and the placement is an instantiate, or
    /// leave it empty and the recipe fields below are used to compose the object the way the old
    /// tools did.
    ///
    /// Create via Assets &gt; Create &gt; ExiledAlvaston &gt; Data &gt; Placement Preset, or generate
    /// a starter library with Tools &gt; GBA &gt; Content &gt; Create Starter Presets.
    /// </summary>
    [CreateAssetMenu(fileName = "NewPlacementPreset", menuName = "ExiledAlvaston/Data/Placement Preset")]
    public class PlacementPreset : ScriptableObject
    {
        /// <summary>
        /// Which section of the palette this appears under.
        ///
        /// ⚠ Serialized by integer index — APPEND ONLY. Inserting or reordering silently remaps
        /// every existing preset asset to the wrong category (CLAUDE.md §7).
        /// </summary>
        public enum PlacementCategory
        {
            NPC = 0,
            Enemy = 1,
            Prop = 2,
            Vehicle = 3,
            Chest = 4,
            Portal = 5,
            SpawnPoint = 6,
        }

        [Header("Palette")]
        public string Label = "New Preset";
        public PlacementCategory Category = PlacementCategory.Prop;

        [Tooltip("Optional. The palette falls back to the Label when this is empty.")]
        public Sprite Icon;

        [Header("Placement")]
        [Tooltip("If set, placing instantiates this prefab and the recipe fields below are ignored. " +
                 "The prefab link is preserved, so edits to the prefab still propagate.")]
        public GameObject Prefab;

        // ── NPC recipe ──────────────────────────────────────────────────────────────────────
        [Header("NPC (when no Prefab is set)")]
        public string NpcName = "Villager";

        [Tooltip("Static sprite. Ignored when NpcController is set, since the Animator drives the sprite.")]
        public Sprite NpcSprite;

        [Tooltip("Animator controller built by the art importer, e.g. player_Controller. Setting " +
                 "this gives the NPC an Animator on its sprite child so generated sheets play.")]
        public RuntimeAnimatorController NpcController;

        public DialogueData Conversation;

        // ── Enemy recipe ────────────────────────────────────────────────────────────────────
        [Header("Enemy (when no Prefab is set, this is the prefab used)")]
        public GameObject EnemyPrefab;

        public bool OverrideHealth;
        public int Health = 45;
        public bool OverrideDamage;
        public int Damage = 7;

        [Tooltip("Dropped on death. Empty means no LootOnDeath component is added at all.")]
        public List<LootDrop> Loot = new List<LootDrop>();

        // ── Chest recipe ────────────────────────────────────────────────────────────────────
        [Header("Chest")]
        public string ChestName = "Chest";

        [Tooltip("Optional. Needs an Animation component for its opening clip. Empty gives the " +
                 "plain procedural box and lid.")]
        public GameObject ChestVisualPrefab;

        [Tooltip("Chest contents. Separate from Loot, which is what an enemy drops when killed.")]
        public List<LootDrop> ChestLoot = new List<LootDrop>();

        // ── Portal recipe ───────────────────────────────────────────────────────────────────
        [Header("Portal")]
        public MapChunkData TargetChunk;
        public Vector3 PortalSpawnPosition = new Vector3(0f, 0f, -8f);
        public string PortalPrompt = "Enter";
        public bool RequireTutorialComplete;
        public bool AddDoorVisual = true;
        public Color DoorVisualColor = new Color(0.35f, 0.22f, 0.12f);

        // ── Vehicle ─────────────────────────────────────────────────────────────────────────
        [Header("Vehicle")]
        [Tooltip("Vehicles are authored onto a chunk's MapChunkData rather than into the scene — " +
                 "the palette writes a VehicleSpawn entry at the point you click.")]
        public VehicleData Vehicle;

        // ── Spawn point ─────────────────────────────────────────────────────────────────────
        [Header("Spawn Point")]
        [Tooltip("Blank for a chunk's default arrival point. Set an id when several doors or " +
                 "portals need different arrival points in the same chunk.")]
        public string SpawnPointId = "";

        // ── Shared ──────────────────────────────────────────────────────────────────────────
        [Header("Shared")]
        [Tooltip("Adds a QuestActor with this key so quest code can find this exact object.")]
        public string QuestKey = "";
    }
}
