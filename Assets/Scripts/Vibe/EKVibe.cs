using UnityEngine;

namespace ExiledAlvaston.Vibe
{
    /// <summary>
    /// Hard vibe lock for Exiled Kingdoms–style presentation.
    /// Muted earthy palette, fixed iso camera, parchment UI.
    /// </summary>
    public static class EKVibe
    {
        // Canonical display title. The title-screen builder consumes it directly; older scene
        // content may still contain the same string as authored TMP text.
        public const string DisplayTitle = "GBH: England";
        public const string CapitalCity = "London";
        public const string TutorialDungeon = "Manor Cellars";

        // --- Camera (fixed isometric, never free-look) ---
        public const float CameraPitch = 30f;
        public const float CameraYaw = -45f;
        public const float CameraOrthoSize = 7f;
        public const float CameraDistance = 18f;
        public const float IsometricMoveOffset = 45f;

        // --- World ---
        public static readonly Color GroundGrass = new Color(0.35f, 0.45f, 0.28f, 1f);
        public static readonly Color GroundStone = new Color(0.55f, 0.52f, 0.45f, 1f);
        public static readonly Color DungeonVoid = Color.black;
        public static readonly Color DirectionalLight = new Color(1f, 0.95f, 0.85f, 1f);

        // --- HUD / combat ---
        public static readonly Color HealthBar = new Color(0.75f, 0.15f, 0.12f, 1f);
        public static readonly Color ManaBar = new Color(0.2f, 0.35f, 0.75f, 1f);
        public static readonly Color XpBar = new Color(0.85f, 0.7f, 0.15f, 1f);
        public static readonly Color LevelBadge = new Color(0.9f, 0.75f, 0.2f, 1f);
        public static readonly Color DamageFloat = new Color(0.95f, 0.2f, 0.15f, 1f);
        public static readonly Color EnemyName = new Color(0.9f, 0.25f, 0.2f, 1f);
        public static readonly Color CombatLogText = new Color(0.95f, 0.92f, 0.85f, 1f);

        // --- Parchment inventory ---
        public static readonly Color ParchmentPanel = new Color(0.72f, 0.62f, 0.45f, 0.96f);
        public static readonly Color ParchmentDark = new Color(0.45f, 0.35f, 0.22f, 1f);
        public static readonly Color SlotFrame = new Color(0.38f, 0.3f, 0.2f, 1f);
        public static readonly Color SlotEmpty = new Color(0.55f, 0.48f, 0.35f, 0.85f);
        public static readonly Color ButtonBrown = new Color(0.5f, 0.38f, 0.22f, 1f);
        /// <summary>ButtonBrown, lit — a HUD toggle that is currently ON, e.g. the crouch button.</summary>
        public static readonly Color ButtonBrownActive = new Color(0.72f, 0.58f, 0.28f, 1f);
        public static readonly Color TextDark = new Color(0.15f, 0.1f, 0.05f, 1f);
        public static readonly Color TextLight = new Color(0.95f, 0.93f, 0.88f, 1f);

        // --- Touch targets (mobile) ---
        public const float JoystickRadius = 110f;
        public const float AttackButtonSize = 100f;
        public const float SkillButtonSize = 72f;
        public const float QuickSlotSize = 64f;

        // --- World presentation (small characters, wide view) ---
        public const float TileSize = 1f;
        /// <summary>World chunk edge length in meters (plane scale 22 → 220 units).</summary>
        public const float ChunkSize = 220f;
        public const float CharacterHeight = 1.55f;
        public const float CharacterWidth = 0.85f;
        public const float PropBushHeight = 0.9f;
        public const float PropTreeHeight = 2.2f;
        public const float WallHeight = 1.8f;
        public static readonly Color DungeonFloor = new Color(0.42f, 0.4f, 0.38f, 1f);
        public static readonly Color DungeonWall = new Color(0.62f, 0.55f, 0.42f, 1f);
        public static readonly Color PathStone = new Color(0.62f, 0.58f, 0.48f, 1f);
        public static readonly Color RoofTile = new Color(0.55f, 0.28f, 0.22f, 1f);

        // --- Currency ---
        /// <summary>
        /// What the police take off you on release. Clamped to what the player actually has, so a
        /// skint player is not driven negative.
        /// </summary>
        public const int ArrestFine = 50;

        /// <summary>
        /// Pound sign (U+00A3), written as an escape on purpose. This file is read and rewritten by
        /// several machines, and a literal pound sign is one bad encoding guess away from becoming
        /// mojibake in every readout that shows money.
        /// </summary>
        public const string PoundSign = "\u00A3";

        /// <summary>
        /// Money as the player sees it: <c>£1,250</c>. Whole pounds — the game has no pence and
        /// nothing should introduce them without deciding what a half-pence pickpocket means.
        /// Invariant culture, so the separator does not follow the device locale and turn
        /// <c>£1,250</c> into <c>£1.250</c> on a European handset.
        /// </summary>
        public static string FormatPounds(int amount) =>
            PoundSign + amount.ToString("N0", System.Globalization.CultureInfo.InvariantCulture);
    }
}
