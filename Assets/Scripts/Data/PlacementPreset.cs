using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Serialization;

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
    /// a starter library with Tools &gt; GBH &gt; Content &gt; Create Starter Presets.
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

        /// <summary>
        /// Which city this character belongs to. Only the palette reads it: the NPC section is
        /// split into sub-headings so a cast of dozens stays navigable, and nothing about how an
        /// NPC is built or behaves depends on it. <see cref="Assorted"/> is the go-anywhere
        /// default — a villager belongs in every chunk.
        ///
        /// ⚠ Serialized by integer index — APPEND ONLY, same rule as
        /// <see cref="PlacementCategory"/> (CLAUDE.md §7). Assorted is 0 so every preset authored
        /// before this field existed reads the right default.
        /// </summary>
        public enum CityRegion
        {
            Assorted = 0,
            London = 1,
            Birmingham = 2,
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
        // More NPC fields live in the "NPC — art pipeline and behaviour" block at the bottom.
        // They are down there rather than here because §7 asks for appends: a field added to the
        // end of the class is the shape existing .asset files can be read against without
        // surprises. Inspector order follows declaration order, so the split is visible.
        [Header("NPC (when no Prefab is set)")]
        public string NpcName = "Villager";

        [Tooltip("The sprite shown when no Animator is driving one — in the Scene view while you " +
                 "author, and before the controller takes over at runtime. Not optional for an " +
                 "animated NPC: Animators do not evaluate in edit mode, so a preset with a " +
                 "controller and no sprite places something you cannot see.")]
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

        // ── NPC — art pipeline and behaviour ────────────────────────────────────────────────
        // Appended rather than slotted in beside the NPC recipe above, per §7.
        [Header("NPC — art pipeline and behaviour")]
        [Tooltip("The art importer's subject for this character — 'mosley' for the sheets named " +
                 "sheet_char_mosley_idle, sheet_char_mosley_walk and so on. When that subject's " +
                 "art imports, the importer fills in NpcController, NpcSprite, NpcHeight and Icon " +
                 "on every preset carrying this subject. Leave empty for an NPC with no generated art.")]
        public string ArtSubject = "";

        [Tooltip("World height of the sprite, in units. Leave at 0 to inherit: the importer writes " +
                 "the art's own worldHeight here when it lands, and until then the shared " +
                 "EKVibe.CharacterHeight is used. Set it by hand only to override the art — a " +
                 "value above 0 is treated as deliberate and the importer will not touch it.")]
        public float NpcHeight = 0f;

        [Tooltip("Wanders around the spot it was placed instead of standing still. Needs a walk " +
                 "animation to look right; an idle-only character will slide.")]
        public bool Roams = false;

        [Tooltip("How far from its placed position a roaming NPC will stray.")]
        public float RoamRadius = 6f;

        [Tooltip("Who the dialogue panel says is talking. Without one the panel keeps showing " +
                 "whoever spoke last, so an ambient NPC should always have this set.")]
        public CharacterData Speaker;

        [Tooltip("One line of throwaway chat, for an NPC that does not warrant a written " +
                 "conversation. A DialogueData asset is generated from it and written into " +
                 "Conversation above; if Conversation is already set, this is ignored.")]
        [TextArea(2, 4)]
        public string AmbientLine = "";

        // ── NPC — pickpocketing ─────────────────────────────────────────────────────────────
        // Appended, per §7. Existing .asset files carry no value for these, and Unity runs the
        // field initializers before applying serialized data, so they read the defaults below —
        // which are PickpocketInteractable's own defaults, so nothing changes for anything already
        // authored.
        [Header("NPC — pickpocketing")]
        [Tooltip("Makes this civilian robbable: the placed NPC gets a PickpocketInteractable wired " +
                 "to its Interactable. Mutually exclusive with dialogue — a mark cannot also be a " +
                 "talker, because both would answer the same button press. If a Conversation or " +
                 "AmbientLine is set, dialogue wins and NpcFactory warns.")]
        public bool Pickpocketable = false;

        [Tooltip("Least they can be carrying, in pounds.")]
        [FormerlySerializedAs("PickpocketMinGold")]
        public int PickpocketMinPounds = 5;

        [Tooltip("Most they can be carrying, in pounds.")]
        [FormerlySerializedAs("PickpocketMaxGold")]
        public int PickpocketMaxPounds = 25;

        [Tooltip("Chance of being caught, which spikes the wanted level instead of paying out.")]
        [Range(0f, 1f)]
        public float PickpocketCatchChance = 0.3f;

        // ── NPC — region ─────────────────────────────────────────────────────────────────────
        // Appended, per §7 — and appended at the very end rather than beside the other NPC fields
        // for the same reason the two blocks above it are: existing .asset files carry no value
        // for it, and Unity applies the field initializer, so every preset already authored reads
        // Assorted. That is the correct default for the villagers, which are placed everywhere.
        [Header("NPC — region")]
        [Tooltip("Which city sub-heading this appears under in the World Palette's NPC section. " +
                 "Palette organisation only — it changes nothing about the NPC that gets built. " +
                 "Leave on Assorted for a character who belongs in any chunk.")]
        public CityRegion Region = CityRegion.Assorted;

        // ── NPC — pickpocket contents ────────────────────────────────────────────────────────
        // Appended at the very end, per §7, for the same reason as every block above it: no preset
        // already authored carries a value for it, so they all read null and keep the pounds-only
        // pickpocket they have always had.
        [Header("NPC — pickpocket contents")]
        [Tooltip("What is in this mark's pockets, on top of the pounds roll. Set one and " +
                 "pickpocketing them opens the tap-to-lift minigame; leave it empty and it stays " +
                 "the single instant pounds roll. Only read when Pickpocketable is on.")]
        public LootBand PickpocketBand;

        // ── Enemy — level ────────────────────────────────────────────────────────────────────
        // Appended at the very end, per §7, for the same reason as every block above it: no preset
        // already authored carries a value for it, so they all read 0 — which means "attach
        // nothing", i.e. exactly what they place today.
        [Header("Enemy — level")]
        [Tooltip("0 leaves the enemy exactly as its prefab authors it — no EnemyLevel component is " +
                 "added at all. 1 or more attaches one at that level.\n\n" +
                 "The prefab's Health and Damage are the level-1 baseline, and Override Health / " +
                 "Override Damage above replace that baseline before the level multiplies it. So " +
                 "Override Health 100 with a level of 5 is 240 HP in play, and the Inspector on the " +
                 "placed enemy still reads 100 — the scale happens at runtime, not at placement.")]
        public int EnemyLevel = 0;
    }
}
