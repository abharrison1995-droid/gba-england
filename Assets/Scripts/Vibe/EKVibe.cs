using UnityEngine;

namespace GBHEngland.Vibe
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
        public const float CameraOrthoSize = 4f;
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
        /// <summary>Amber, for the stamina bar. Deliberately its own constant rather than a reuse
        /// of <see cref="XpBar"/>, which it currently matches — the two answer to different things
        /// and must be free to diverge without one silently dragging the other.</summary>
        public static readonly Color StaminaBar = new Color(0.85f, 0.7f, 0.15f, 1f);
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

        /// <summary>
        /// Runtime localScale for the top-left HUD cluster — portrait, HP/MP/concealment bars and
        /// their readouts. Applied by UIManager to the panel, never to a track or a fill.
        ///
        /// 1.6 sits between two bounds. The hard ceiling is the combat log: the cluster's right
        /// edge is 16 + 390*k and the log's left edge is 700 at the 1920x1080 reference, so
        /// ⚠ <b>anything above ~1.75 overlaps it</b> and needs the log moved, which is a scene edit.
        /// The floor is legibility — the rest of the HUD is built at 100-130 px with 20-26 pt
        /// labels, and the cluster was 28 px bars with an 18 pt readout. At 1.6 the bars are
        /// 44.8 px, the readout 28.8 pt and the portrait 153.6 px, level with the 130 px ATK
        /// button. Derived from geometry and parity, not measured on a device.
        /// </summary>
        public const float HudClusterScale = 1.6f;

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
        // --- Pickpocketing ---
        /// <summary>
        /// How long the player has, in seconds, once the pickpocket menu opens. Running out spikes
        /// the wanted level, so this is the difficulty dial for the whole mechanic.
        /// </summary>
        public const float PickpocketSeconds = 10f;

        /// <summary>How many pockets the minigame offers. Also how many times the band is rolled.</summary>
        public const int PickpocketSlots = 4;

        /// <summary>
        /// How far the player may drift from the victim before the attempt closes itself. Slightly
        /// beyond the Interactable range that opened it, so simply standing still cannot cancel it.
        /// </summary>
        public const float PickpocketRange = 3.5f;

        public static string FormatPounds(int amount) =>
            PoundSign + amount.ToString("N0", System.Globalization.CultureInfo.InvariantCulture);

        // --- Progression ---
        // Balance numbers, not save data. The player's level is *derived* from TotalXP every time
        // it is read and is never stored, so any of these may be retuned later without a save
        // migration — an existing save simply resolves to a different level under the new curve.
        // Treat them as tunable, not frozen.

        /// <summary>Hard cap on the player's level. The curve stops paying out above this.</summary>
        public const int MaxPlayerLevel = 25;

        /// <summary>
        /// Cumulative XP to reach level n is <c>XPCurveFactor * (n-1)^2</c>.
        /// L2 = 100, L5 = 1,600, L10 = 8,100, L25 = 57,600.
        /// </summary>
        public const int XPCurveFactor = 100;

        /// <summary>XP paid for killing a level-1 enemy.</summary>
        public const int KillXPBase = 25;

        /// <summary>Enemy MaxHealth multiplier per level above 1.</summary>
        public const float EnemyHealthPerLevel = 0.35f;

        /// <summary>Enemy damage multiplier per level above 1.</summary>
        public const float EnemyDamagePerLevel = 0.25f;

        /// <summary>Kill-XP multiplier per enemy level above 1.</summary>
        public const float EnemyXPPerLevel = 0.5f;

        /// <summary>
        /// Effective armour equal to this halves incoming damage. A *balance* constant: raising or
        /// lowering it retunes every piece of gear in the game at once, because every
        /// <see cref="Data.ItemData.Armor"/> value is an input to the curve rather than a number of
        /// points removed.
        ///
        /// 20 was chosen so the only armour value authored today (TestRing's 4) still reads as a
        /// meaningful 16.7% reduction and no existing asset needs re-authoring. Authoring guidance
        /// at this cap: a light piece ~3-5, a heavy piece ~8-12, a full endgame doll around 40-60
        /// effective, i.e. 67-75%.
        /// </summary>
        public const int ArmourSoftCap = 20;

        /// <summary>Ceiling on armour mitigation — never more than three-quarters off a hit.</summary>
        public const float ArmourMaxReduction = 0.75f;

        /// <summary>
        /// Fraction of incoming damage armour removes, as <c>armour / (armour + ArmourSoftCap)</c>
        /// capped at <see cref="ArmourMaxReduction"/>.
        ///
        /// Proportional on purpose. Armour used to be subtracted flat and floored at zero, which
        /// meant a couple of pieces made weak enemies literally unable to connect — and Phase 2's
        /// per-level damage scaling sharpened that cliff instead of smoothing it. A hit now always
        /// lands for something.
        /// </summary>
        public static float ArmourReduction(int armour)
        {
            if (armour <= 0) return 0f;
            return Mathf.Min(ArmourMaxReduction, (float)armour / (armour + ArmourSoftCap));
        }

        /// <summary>
        /// Perk points earned by reaching a level: one every two levels, at 2, 4, 6 … 24, so twelve
        /// across the cap of 25. Derived on every read and never stored, exactly like the level
        /// itself — retuning this needs no save migration, and a downward retune cannot leave a
        /// negative figure because <c>PlayerSession.UnspentPerkPoints</c> clamps at 0.
        /// </summary>
        public static int PerkPointsAtLevel(int level) => Mathf.Clamp(level, 1, MaxPlayerLevel) / 2;

        /// <summary>Cumulative XP needed to have reached the given level. Level 1 and below cost 0.</summary>
        public static int TotalXPForLevel(int level)
        {
            if (level <= 1) return 0;
            int steps = level - 1;
            return XPCurveFactor * steps * steps;
        }

        /// <summary>
        /// The level a cumulative XP total resolves to, clamped to [1, MaxPlayerLevel].
        ///
        /// Closed form rather than a loop, because the HUD polls this every frame. The two
        /// single-step corrections exist because <see cref="Mathf.Sqrt"/> is float: at an exact
        /// threshold it can land a hair under (sqrt(1) as 0.99999994) and floor to the level below,
        /// which would silently swallow a level-up at exactly 100 XP. They are ifs, not whiles —
        /// the error can never exceed one step.
        /// </summary>
        public static int LevelForXP(int totalXp)
        {
            if (totalXp <= 0) return 1;

            int level = 1 + Mathf.FloorToInt(Mathf.Sqrt((float)totalXp / XPCurveFactor));

            if (level < MaxPlayerLevel && TotalXPForLevel(level + 1) <= totalXp) level++;
            if (level > 1 && TotalXPForLevel(level) > totalXp) level--;

            return Mathf.Clamp(level, 1, MaxPlayerLevel);
        }

        /// <summary>How much of the current level's XP band has been earned.</summary>
        public static int XPIntoLevel(int totalXp)
        {
            if (totalXp <= 0) return 0;
            return totalXp - TotalXPForLevel(LevelForXP(totalXp));
        }

        /// <summary>
        /// XP still needed to reach the next level. Returns <c>0</c> at
        /// <see cref="MaxPlayerLevel"/> — UI must read a 0 here as "MAX", never as "0 XP needed".
        /// </summary>
        public static int XPForNextLevel(int totalXp)
        {
            int level = LevelForXP(totalXp);
            if (level >= MaxPlayerLevel) return 0;
            return TotalXPForLevel(level + 1) - Mathf.Max(0, totalXp);
        }

        /// <summary>
        /// The one shared scaling shape: <c>baseValue * (1 + K * (level - 1))</c>. The prefab's
        /// authored value is always the level-1 baseline.
        /// </summary>
        private static int Scaled(int baseValue, int level, float perLevel)
        {
            int clamped = Mathf.Max(1, level);
            return Mathf.RoundToInt(baseValue * (1f + perLevel * (clamped - 1)));
        }

        public static int ScaledHealth(int baseHealth, int level) => Scaled(baseHealth, level, EnemyHealthPerLevel);

        public static int ScaledDamage(int baseDamage, int level) => Scaled(baseDamage, level, EnemyDamagePerLevel);

        public static int ScaledKillXP(int baseXp, int level) => Scaled(baseXp, level, EnemyXPPerLevel);

        // --- Traffic and car theft ---
        // Appended at the very end, per §7. These are the global tuning dials for the ambient
        // traffic and hotwire systems; per-car values (ride speed, traffic speed, wires, clock)
        // live on VehicleData so the two cars can differ.

        /// <summary>How far ahead of a car the player must be (in the lane) for it to brake.</summary>
        public const float TrafficBrakeDistance = 6f;

        /// <summary>Half the lane width. A player inside this and ahead of the car stops it.</summary>
        public const float TrafficLaneHalfWidth = 1.6f;

        /// <summary>How long a stopped car waits after the player clears before driving on.</summary>
        public const float TrafficResumeDelay = 1.5f;

        /// <summary>Minimum gap between honk toasts while a car is blocked.</summary>
        public const float HonkIntervalSeconds = 4f;

        /// <summary>Least taps a single hotwire wire needs to come loose.</summary>
        public const int HotwireMinTaps = 2;

        /// <summary>Most taps a single hotwire wire needs to come loose.</summary>
        public const int HotwireMaxTaps = 4;

        /// <summary>How long a car stays hotwire-locked after a failed attempt, in seconds.</summary>
        public const float HotwireRetryLockoutSeconds = 30f;

        /// <summary>
        /// Visits a restockable container sits out before it refills. Counted per entry into its
        /// chunk, so 3 means "available on the third return" — loot it, come back, come back, come
        /// back. A container authored with a count of zero or less falls back to this.
        /// </summary>
        public const int DefaultContainerRespawnVisits = 3;

        /// <summary>
        /// How close the player has to be to use a container, in metres.
        ///
        /// ⚠ SpriteContainer and LootChest both hardcode 2.75 and are deliberately left alone —
        /// a different number is a different feel, and retuning two working components is not this
        /// constant's job. It is the default the container tool writes onto new containers.
        /// </summary>
        public const float DefaultContainerInteractRange = 2.5f;
    }
}