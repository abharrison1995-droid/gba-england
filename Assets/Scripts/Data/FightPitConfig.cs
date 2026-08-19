using System;
using System.Collections.Generic;
using UnityEngine;

namespace GBHEngland.Data
{
    [CreateAssetMenu(fileName = "FightPitConfig",
                     menuName = "GBH England/Data/Fight Pit Config")]
    public class FightPitConfig : ScriptableObject
    {
        public const string ResourcePath = "FightPitConfig";

        [Serializable]
        public class Opponent
        {
            public string PresetKey;
            public int BaseLevel = 1;
        }

        [Serializable]
        public class Round
        {
            public List<Opponent> Opponents = new List<Opponent>();
            public int Purse;
        }

        public List<Round> Rounds = new List<Round>();
        public int FirstCompletionBonus = 100;

        public static FightPitConfig Load()
        {
            var config = Resources.Load<FightPitConfig>(ResourcePath);
            if (config != null && config.Rounds != null && config.Rounds.Count >= 10) return config;
            return CreateDefaultConfig();
        }

        public static FightPitConfig CreateDefaultConfig()
        {
            var config = ScriptableObject.CreateInstance<FightPitConfig>();
            config.name = "Runtime_FightPitConfig";
            config.FirstCompletionBonus = 250;
            config.Rounds = new List<Round>
            {
                // Round 1 (Wave 1): 2 Tracksuit Geezers
                new Round { Purse = 20, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "TracksuitGeezer", BaseLevel = 1 },
                    new Opponent { PresetKey = "TracksuitGeezer", BaseLevel = 1 }
                }},
                // Round 2 (Wave 2): 2 Roadmen, 1 Geezer
                new Round { Purse = 35, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Roadman", BaseLevel = 1 },
                    new Opponent { PresetKey = "TracksuitGeezer", BaseLevel = 2 },
                    new Opponent { PresetKey = "Roadman", BaseLevel = 1 }
                }},
                // Round 3 (Wave 3 - Tier 1 Shop Unlock): 2 Roadmen, 1 Stabmeister, 1 Geezer
                new Round { Purse = 50, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Roadman", BaseLevel = 2 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 2 },
                    new Opponent { PresetKey = "TracksuitGeezer", BaseLevel = 2 },
                    new Opponent { PresetKey = "Roadman", BaseLevel = 2 }
                }},
                // Round 4 (Wave 4): 2 Stabmeisters, 2 Roadmen
                new Round { Purse = 70, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 3 },
                    new Opponent { PresetKey = "Roadman", BaseLevel = 3 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 3 },
                    new Opponent { PresetKey = "TracksuitGeezer", BaseLevel = 3 }
                }},
                // Round 5 (Wave 5): 2 Spiceheads, 2 Stabmeisters, 1 Roadman
                new Round { Purse = 95, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Spicehead", BaseLevel = 4 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 4 },
                    new Opponent { PresetKey = "Spicehead", BaseLevel = 4 },
                    new Opponent { PresetKey = "Roadman", BaseLevel = 4 },
                    new Opponent { PresetKey = "TracksuitGeezer", BaseLevel = 4 }
                }},
                // Round 6 (Wave 6): 3 Spiceheads, 2 Stabmeisters
                new Round { Purse = 125, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Spicehead", BaseLevel = 5 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 5 },
                    new Opponent { PresetKey = "Spicehead", BaseLevel = 5 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 5 },
                    new Opponent { PresetKey = "Roadman", BaseLevel = 5 }
                }},
                // Round 7 (Wave 7 - Tier 2 Shop Unlock): 2 Tainted, 2 Spiceheads, 2 Stabmeisters
                new Round { Purse = 160, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Tainted", BaseLevel = 6 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 6 },
                    new Opponent { PresetKey = "Spicehead", BaseLevel = 6 },
                    new Opponent { PresetKey = "Tainted", BaseLevel = 6 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 6 },
                    new Opponent { PresetKey = "Spicehead", BaseLevel = 6 }
                }},
                // Round 8 (Wave 8): 3 Tainted, 2 Tortured Neeks, 1 OG
                new Round { Purse = 200, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Tainted", BaseLevel = 7 },
                    new Opponent { PresetKey = "TorturedNeek", BaseLevel = 7 },
                    new Opponent { PresetKey = "Tainted", BaseLevel = 7 },
                    new Opponent { PresetKey = "TorturedNeek", BaseLevel = 7 },
                    new Opponent { PresetKey = "OG", BaseLevel = 7 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 7 }
                }},
                // Round 9 (Wave 9): 3 Tainted, 3 Tortured Neeks, 1 OG
                new Round { Purse = 250, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "Tainted", BaseLevel = 8 },
                    new Opponent { PresetKey = "TorturedNeek", BaseLevel = 8 },
                    new Opponent { PresetKey = "Tainted", BaseLevel = 8 },
                    new Opponent { PresetKey = "TorturedNeek", BaseLevel = 8 },
                    new Opponent { PresetKey = "OG", BaseLevel = 8 },
                    new Opponent { PresetKey = "Stabmeister", BaseLevel = 8 },
                    new Opponent { PresetKey = "Tainted", BaseLevel = 8 }
                }},
                // Round 10 (Wave 10 - Grand Champion & Tier 3 Crown Unlock): 2 OG, 3 Tainted, 2 Tortured Neeks
                new Round { Purse = 350, Opponents = new List<Opponent> {
                    new Opponent { PresetKey = "OG", BaseLevel = 10 },
                    new Opponent { PresetKey = "Tainted", BaseLevel = 9 },
                    new Opponent { PresetKey = "TorturedNeek", BaseLevel = 9 },
                    new Opponent { PresetKey = "Tainted", BaseLevel = 9 },
                    new Opponent { PresetKey = "TorturedNeek", BaseLevel = 9 },
                    new Opponent { PresetKey = "OG", BaseLevel = 10 }
                }}
            };

            return config;
        }
    }
}
