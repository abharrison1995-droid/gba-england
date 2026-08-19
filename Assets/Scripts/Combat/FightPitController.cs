using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;
using GBHEngland.Dialogue;
using GBHEngland.Flow;
using GBHEngland.UI;
using GBHEngland.Vibe;
using GBHEngland.World;

namespace GBHEngland.Combat
{
    /// <summary>
    /// Manages the Castle Fight Pit tournament rounds, opponent spawning, level scaling,
    /// victory progression, between-round dialogue, cashing out, and defeat handling.
    /// </summary>
    public class FightPitController : MonoBehaviour
    {
        public static FightPitController ActiveInstance { get; private set; }

        [Header("Spawn Configuration")]
        [Tooltip("Transform positions where arena enemies spawn.")]
        public Transform[] SpawnPoints;

        private FightPitConfig _config;
        private int _currentRoundIndex = 0;
        private int _runningPurse = 0;
        private bool _isMatchLive = false;
        private Coroutine _pacingCoroutine;

        private GameObject _enemyHolder;
        private readonly List<GameObject> _aliveEnemies = new List<GameObject>();
        private DialogueData _runtimeDialogue;

        public bool IsMatchLive => _isMatchLive;
        public int CurrentRoundIndex => _currentRoundIndex;
        public int RunningPurse => _runningPurse;

        private void Awake()
        {
            if (ActiveInstance == null)
                ActiveInstance = this;
        }

        private void Start()
        {
            _config = FightPitConfig.Load();

            var baker = GetComponent<RuntimeNavMeshBaker>() 
                        ?? GetComponentInParent<RuntimeNavMeshBaker>() 
                        ?? FindObjectOfType<RuntimeNavMeshBaker>();

            if (baker != null && !baker.IsReady)
            {
                baker.OnBakeComplete += OnNavMeshBakeComplete;
            }
            else
            {
                BeginPendingMatch();
            }
        }

        private void OnDestroy()
        {
            if (ActiveInstance == this)
                ActiveInstance = null;

            if (_pacingCoroutine != null)
            {
                StopCoroutine(_pacingCoroutine);
                _pacingCoroutine = null;
            }

            if (_enemyHolder != null)
            {
                Destroy(_enemyHolder);
                _enemyHolder = null;
            }

            var baker = GetComponent<RuntimeNavMeshBaker>() 
                        ?? GetComponentInParent<RuntimeNavMeshBaker>() 
                        ?? FindObjectOfType<RuntimeNavMeshBaker>();
            if (baker != null)
                baker.OnBakeComplete -= OnNavMeshBakeComplete;

            if (_runtimeDialogue != null)
            {
                Destroy(_runtimeDialogue);
                _runtimeDialogue = null;
            }
        }

        private void Update()
        {
            if (!_isMatchLive || _aliveEnemies == null) return;

            bool pruned = false;
            for (int i = _aliveEnemies.Count - 1; i >= 0; i--)
            {
                if (_aliveEnemies[i] == null)
                {
                    _aliveEnemies.RemoveAt(i);
                    pruned = true;
                }
            }

            if (pruned && _aliveEnemies.Count == 0)
            {
                _isMatchLive = false;
                if (_pacingCoroutine != null)
                {
                    StopCoroutine(_pacingCoroutine);
                    _pacingCoroutine = null;
                }
                _pacingCoroutine = StartCoroutine(RoundVictoryRoutine());
            }
        }

        private void OnNavMeshBakeComplete()
        {
            var baker = GetComponent<RuntimeNavMeshBaker>() 
                        ?? GetComponentInParent<RuntimeNavMeshBaker>() 
                        ?? FindObjectOfType<RuntimeNavMeshBaker>();
            if (baker != null)
                baker.OnBakeComplete -= OnNavMeshBakeComplete;

            BeginPendingMatch();
        }

        private void BeginPendingMatch()
        {
            _currentRoundIndex = 0;
            _runningPurse = 0;
            BeginRound(_currentRoundIndex);
        }

        public void BeginRound(int roundIndex)
        {
            if (_pacingCoroutine != null)
            {
                StopCoroutine(_pacingCoroutine);
                _pacingCoroutine = null;
            }

            _pacingCoroutine = StartCoroutine(RoundCountdownRoutine(roundIndex));
        }

        private IEnumerator RoundCountdownRoutine(int roundIndex)
        {
            if (UIManager.Instance != null)
            {
                UIManager.Instance.ShowToast($"Round {roundIndex + 1} - Get Ready!", 1.5f);
            }

            yield return new WaitForSeconds(1.5f);
            _pacingCoroutine = null;
            BeginRoundInternal(roundIndex);
        }

        private void BeginRoundInternal(int roundIndex)
        {
            _isMatchLive = true;

            if (_runtimeDialogue != null)
            {
                Destroy(_runtimeDialogue);
                _runtimeDialogue = null;
            }

            if (_enemyHolder != null)
            {
                Destroy(_enemyHolder);
                _enemyHolder = null;
            }

            if (roundIndex == 0 && Quests.QuestManager.Instance != null)
            {
                int pb = PlayerSession.Instance != null ? PlayerSession.Instance.HighestPitRound : 0;
                string pbStr = pb > 0 ? $" (Personal Best: Wave {pb})" : "";
                Quests.QuestManager.Instance.StartQuest("castle_arena_quest", "The Royal Oik Gauntlet", "Survive the Castle Fight Arena." + pbStr);
            }

            if (_config == null || _config.Rounds == null || roundIndex < 0 || roundIndex >= _config.Rounds.Count)
            {
                Debug.LogError($"FightPitController: Round index {roundIndex} is out of range or config is invalid.");
                ReturnOutside();
                return;
            }

            _currentRoundIndex = roundIndex;
            var round = _config.Rounds[roundIndex];

            _enemyHolder = new GameObject($"PitEnemies_Round_{roundIndex + 1}");
            _enemyHolder.transform.SetParent(transform);
            _enemyHolder.SetActive(false);

            _aliveEnemies.Clear();

            int levelOffset = FightPitEntryCoordinator.Instance != null 
                ? FightPitEntryCoordinator.Instance.PlayerLevelOffset 
                : 0;

            for (int i = 0; i < round.Opponents.Count; i++)
            {
                var opp = round.Opponents[i];
                if (opp == null || string.IsNullOrEmpty(opp.PresetKey)) continue;

                PlacementPreset preset = PlacementPresetLibrary.Get(opp.PresetKey);
                if (preset == null || preset.EnemyPrefab == null)
                {
                    Debug.LogError($"FightPitController: Preset or EnemyPrefab for '{opp.PresetKey}' could not be resolved.");
                    continue;
                }

                Vector3 spawnPos = GetSpawnPosition(i);
                Quaternion spawnRot = Quaternion.Euler(0f, 180f, 0f);

                GameObject enemyObj = Instantiate(preset.EnemyPrefab, spawnPos, spawnRot, _enemyHolder.transform);
                enemyObj.name = $"{preset.EnemyPrefab.name}_R{roundIndex + 1}_{i + 1}";

                // Enemy prefabs lack EnemyLevel; add or get it before activation so Health.Awake scales stats correctly.
                // Use an explicit Unity-null check, not `?? AddComponent` — `??` bypasses Unity's overloaded null
                // check and can skip the AddComponent, throwing MissingComponentException on the next line.
                var enemyLevel = enemyObj.GetComponent<EnemyLevel>();
                if (enemyLevel == null)
                    enemyLevel = enemyObj.AddComponent<EnemyLevel>();
                enemyLevel.Level = Mathf.Max(1, opp.BaseLevel + levelOffset);

                // Replicate PlacementPreset overrides if configured
                var hp = enemyObj.GetComponent<Health>();
                if (hp != null && preset.OverrideHealth)
                {
                    hp.MaxHealth = preset.Health;
                    hp.CurrentHealth = preset.Health;
                }

                var ai = enemyObj.GetComponent<EnemyAI>();
                if (ai != null && preset.OverrideDamage)
                {
                    ai.Damage = preset.Damage;
                }

                // Suppress KillXP and loot
                enemyObj.AddComponent<ArenaEnemy>();

                if (hp != null)
                {
                    GameObject trackedEnemy = enemyObj;
                    hp.OnDeath.AddListener(() => OnEnemyDied(trackedEnemy));
                }

                _aliveEnemies.Add(enemyObj);
            }

            // If a round resolved no opponents at all (every PresetKey missing / unregistered / null
            // EnemyPrefab), neither victory path can fire: OnEnemyDied never runs, and Update()'s
            // prune-then-check can't trigger on an already-empty list. The player would be sealed in a
            // live-but-empty pit with no UI to leave. Abort the run safely rather than soft-lock.
            if (_aliveEnemies.Count == 0)
            {
                Debug.LogError($"FightPitController: round {roundIndex + 1} resolved no opponents — aborting to avoid a soft-lock. " +
                               "Check the round's PresetKeys against PlacementPresetLibrary.");
                _isMatchLive = false;
                ReturnOutside();
                return;
            }

            // Activating holder invokes Health.Awake (which applies EnemyLevel) and EnemyAI.Awake synchronously
            _enemyHolder.SetActive(true);

            // Synchronously strip loot and configure fast corpse decay immediately so frame-1 kills drop no loot
            for (int i = 0; i < _aliveEnemies.Count; i++)
            {
                GameObject enemy = _aliveEnemies[i];
                if (enemy == null) continue;

                var loot = enemy.GetComponent<LootOnDeath>();
                if (loot != null)
                {
                    loot.Loot = null;
                    loot.Band = null;
                    loot.DespawnLootedDelay = 1.5f;
                    loot.DespawnUnlootedDelay = 1.5f;
                }
            }

            // Grant player 0.5s invulnerability and reset velocity on round start
            var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
            if (player != null)
            {
                player.GrantInvulnerability(0.5f);
                var rb = player.GetComponent<Rigidbody>();
                if (rb != null)
                    rb.velocity = Vector3.zero;
            }

            bool isFinalRound = _config != null && _config.Rounds != null && roundIndex == _config.Rounds.Count - 1;
            if (isFinalRound)
            {
                UnityEngine.Camera.main?.GetComponent<GBHEngland.World.IsometricCameraFollow>()?.Shake(0.6f, 0.4f);

                if (UIManager.Instance != null)
                {
                    UIManager.Instance.ShowToast($"FINAL ROUND {roundIndex + 1} - Championship Bout!", 2.5f);
                    UIManager.Instance.LogCombat($"--- FINAL ROUND {roundIndex + 1} (Championship Bout) Starts! (Purse: {EKVibe.FormatPounds(round.Purse)}) ---");
                }
            }
            else
            {
                if (UIManager.Instance != null)
                {
                    UIManager.Instance.ShowToast($"Round {roundIndex + 1} - Fight!", 2f);
                    UIManager.Instance.LogCombat($"--- Round {roundIndex + 1} Starts! (Purse: {EKVibe.FormatPounds(round.Purse)}) ---");
                }
            }
        }

        private Vector3 GetSpawnPosition(int index)
        {
            if (SpawnPoints != null && SpawnPoints.Length > 0)
            {
                Transform pt = SpawnPoints[index % SpawnPoints.Length];
                if (pt != null) return pt.position;
            }

            Vector3 center = transform.position;
            switch (index % 4)
            {
                case 0: return center + new Vector3(0f, 0f, 8f);
                case 1: return center + new Vector3(-6f, 0f, 5f);
                case 2: return center + new Vector3(6f, 0f, 5f);
                case 3: return center + new Vector3(0f, 0f, 10f);
                default: return center + new Vector3(0f, 0f, 7f);
            }
        }

        private void OnEnemyDied(GameObject enemy)
        {
            if (!_isMatchLive) return;

            _aliveEnemies.Remove(enemy);

            for (int i = _aliveEnemies.Count - 1; i >= 0; i--)
            {
                if (_aliveEnemies[i] == null)
                    _aliveEnemies.RemoveAt(i);
            }

            if (_aliveEnemies.Count > 0)
            {
                if (UIManager.Instance != null)
                {
                    string plural = _aliveEnemies.Count == 1 ? "opponent" : "opponents";
                    UIManager.Instance.LogCombat($"Opponent defeated! {_aliveEnemies.Count} {plural} remaining.");
                }
            }
            else
            {
                _isMatchLive = false;
                if (_pacingCoroutine != null)
                {
                    StopCoroutine(_pacingCoroutine);
                    _pacingCoroutine = null;
                }
                _pacingCoroutine = StartCoroutine(RoundVictoryRoutine());
            }
        }

        private IEnumerator RoundVictoryRoutine()
        {
            yield return new WaitForSeconds(1.2f);
            _pacingCoroutine = null;
            OnRoundVictory();
        }

        private void OnRoundVictory()
        {
            _isMatchLive = false;

            // Between-round full heal & resource restore
            var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
            if (player != null)
            {
                Health playerHp = player.GetComponent<Health>();
                if (player.IsDead || (playerHp != null && playerHp.IsDead))
                {
                    player.ReviveFull();
                }
                else
                {
                    if (playerHp != null) playerHp.Heal(playerHp.MaxHealth);
                    player.CurrentHealth = playerHp != null ? playerHp.CurrentHealth : (player.PlayerData != null ? player.PlayerData.MaxHealth : 100);
                    player.CurrentMana = player.PlayerData != null ? player.PlayerData.MaxManaStamina : 50;
                    player.CurrentStamina = player.CurrentMana;
                }
            }

            int completedRound = _currentRoundIndex + 1;
            if (PlayerSession.Instance != null && completedRound > PlayerSession.Instance.HighestPitRound)
            {
                PlayerSession.Instance.HighestPitRound = completedRound;
                Quests.QuestManager.Instance?.UpdateObjective("castle_arena_quest", $"Survive the Castle Fight Arena. (Personal Best: Wave {completedRound})");
            }

            int roundPurse = (_config != null && _currentRoundIndex < _config.Rounds.Count) 
                ? _config.Rounds[_currentRoundIndex].Purse 
                : 0;
            _runningPurse += roundPurse;

            if (_config == null || _currentRoundIndex >= _config.Rounds.Count - 1)
            {
                // Final 10th round cleared — Tournament Victory!
                int totalPayout = _runningPurse;
                bool firstWin = PlayerSession.Instance != null && !PlayerSession.Instance.PitTournamentWon;
                int bonus = firstWin && _config != null ? _config.FirstCompletionBonus : 0;
                totalPayout += bonus;

                if (PlayerSession.Instance != null)
                {
                    PlayerSession.Instance.HighestPitRound = Mathf.Max(PlayerSession.Instance.HighestPitRound, 10);
                }

                UnityEngine.Camera.main?.GetComponent<GBHEngland.World.IsometricCameraFollow>()?.Shake(1.0f, 0.5f);

                int totalRounds = _config != null && _config.Rounds != null ? _config.Rounds.Count : (_currentRoundIndex + 1);
                if (UIManager.Instance != null)
                {
                    UIManager.Instance.ShowToast($"Tournament Champion! All {totalRounds} Rounds Cleared!", 4f);
                    UIManager.Instance.LogCombat($"Tournament Complete! Grand champion status achieved.");
                }

                // Construct and display the grand finale victory cutscene
                var victoryCutscene = ScriptableObject.CreateInstance<Data.CutsceneData>();
                victoryCutscene.Title = "The Royal Oik Gauntlet - Grand Champion";
                victoryCutscene.Slides = new List<Data.CutsceneSlide>
                {
                    new Data.CutsceneSlide
                    {
                        SpeakerName = "Prince Mandrew",
                        NarrativeText = "By Jove! You've actually flattened all ten waves of the realm's most unwashed brawlers and deserters! Absolutely sensational form! *dabs glistening brow with silk handkerchief*"
                    },
                    new Data.CutsceneSlide
                    {
                        SpeakerName = "Prince Mandrew",
                        NarrativeText = "Mother would be simply thrilled! Well, she'd likely have you transported to the colonies for blood on the cobblestones, but I am ecstatic! Here is your tournament purse plus 500 XP!"
                    },
                    new Data.CutsceneSlide
                    {
                        SpeakerName = "Prince Mandrew",
                        NarrativeText = "Furthermore, I hereby open Tier 3 in the Royal Vault! Speak with me outside and select ONE of our three sacred Crowns as your personal royal heirloom!"
                    }
                };

                UI.StoryCutsceneUI.Show(victoryCutscene, () =>
                {
                    if (PlayerSession.Instance != null)
                    {
                        if (firstWin)
                            PlayerSession.Instance.PitTournamentWon = true;
                        PlayerSession.Instance.AddPounds(totalPayout);
                        PlayerSession.Instance.GrantXP(500, "Castle Arena Grand Champion");
                    }
                    Quests.QuestManager.Instance?.CompleteQuest("castle_arena_quest");
                    ReturnOutside();
                });
            }
            else
            {
                // Offer Continue or Cash Out dialogue
                int cashOutAmount = Mathf.FloorToInt(_runningPurse / 2f);
                int totalRounds = _config != null && _config.Rounds != null ? _config.Rounds.Count : 10;

                UnityEngine.Camera.main?.GetComponent<GBHEngland.World.IsometricCameraFollow>()?.Shake(0.3f, 0.2f);

                if (UIManager.Instance != null)
                {
                    UIManager.Instance.ShowToast($"Round {_currentRoundIndex + 1}/{totalRounds} Cleared! Purse: {EKVibe.FormatPounds(_runningPurse)}", 2.5f);
                    UIManager.Instance.LogCombat($"Round {_currentRoundIndex + 1}/{totalRounds} cleared! Current purse: {EKVibe.FormatPounds(_runningPurse)}.");
                }

                if (_runtimeDialogue != null)
                {
                    Destroy(_runtimeDialogue);
                    _runtimeDialogue = null;
                }

                _runtimeDialogue = FightPitDialogue.CreateBetweenRoundDialogue(_currentRoundIndex, _runningPurse, cashOutAmount);
                DialogueManager.Ensure().StartDialogue(_runtimeDialogue, PlayerSession.Instance != null ? PlayerSession.Instance.RuntimeStats : null);
            }
        }

        /// <summary>
        /// Continues to the next round of the tournament.
        /// </summary>
        public void ContinueToNextRound()
        {
            if (_runtimeDialogue != null)
            {
                Destroy(_runtimeDialogue);
                _runtimeDialogue = null;
            }

            _currentRoundIndex++;
            BeginRound(_currentRoundIndex);
        }

        /// <summary>
        /// Cashes out 50% of the accumulated purse and returns the player outside.
        /// </summary>
        public void CashOutAndExit()
        {
            _isMatchLive = false;

            if (_pacingCoroutine != null)
            {
                StopCoroutine(_pacingCoroutine);
                _pacingCoroutine = null;
            }

            if (_runtimeDialogue != null)
            {
                Destroy(_runtimeDialogue);
                _runtimeDialogue = null;
            }

            int payout = Mathf.FloorToInt(_runningPurse / 2f);
            if (payout > 0 && PlayerSession.Instance != null)
            {
                PlayerSession.Instance.AddPounds(payout);
            }

            if (UIManager.Instance != null)
            {
                UIManager.Instance.ShowToast($"Cashed out with {EKVibe.FormatPounds(payout)}!", 2.5f);
                UIManager.Instance.LogCombat($"Cashed out from fight pit: {EKVibe.FormatPounds(payout)}.");
            }

            ReturnOutside();
        }

        /// <summary>
        /// Intercepts player defeat, revives them, restores entry vitals, awards £0, and returns outside.
        /// </summary>
        public void HandlePlayerDefeat()
        {
            _isMatchLive = false;
            _runningPurse = 0;

            if (_pacingCoroutine != null)
            {
                StopCoroutine(_pacingCoroutine);
                _pacingCoroutine = null;
            }

            if (_runtimeDialogue != null)
            {
                Destroy(_runtimeDialogue);
                _runtimeDialogue = null;
            }

            if (_enemyHolder != null)
            {
                Destroy(_enemyHolder);
                _enemyHolder = null;
            }

            if (UIManager.Instance != null)
            {
                UIManager.Instance.ShowToast("Knocked out in the fight pit! No purse awarded.", 3f);
                UIManager.Instance.LogCombat("Defeated in the fight pit. You leave with nothing.");
            }

            _pacingCoroutine = StartCoroutine(PlayerDefeatRoutine());
        }

        private IEnumerator PlayerDefeatRoutine()
        {
            yield return new WaitForSeconds(1.8f);
            _pacingCoroutine = null;

            var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
            if (player != null)
            {
                player.ReviveFull();
                foreach (var col in player.GetComponentsInChildren<Collider>())
                    col.enabled = true;
            }

            ReturnOutside();
        }

        private void ReturnOutside()
        {
            if (_pacingCoroutine != null)
            {
                StopCoroutine(_pacingCoroutine);
                _pacingCoroutine = null;
            }

            if (_enemyHolder != null)
            {
                Destroy(_enemyHolder);
                _enemyHolder = null;
            }

            if (_runtimeDialogue != null)
            {
                Destroy(_runtimeDialogue);
                _runtimeDialogue = null;
            }

            var player = CombatController.Instance ?? FindObjectOfType<CombatController>();
            if (FightPitEntryCoordinator.Instance != null && player != null)
            {
                FightPitEntryCoordinator.Instance.RestoreVitalsToPlayer(player);
            }

            MapChunkData returnChunk = ChunkManager.Instance != null
                ? (ChunkManager.Instance.FindChunkByName("Home_London") ?? ChunkManager.Instance.FindChunkByName("Home_London_Data"))
                : null;

            if (returnChunk != null && ChunkManager.Instance != null)
            {
                // Prefer the named arrival marker so the player pops out beside Prince Mandrew, but
                // only if it actually exists in the return chunk's prefab. A named TravelTo whose
                // marker does not resolve ABORTS the journey (ChunkManager.TravelRoutine, by design),
                // which would trap the player in the pit forever. When the marker is missing, fall
                // back to the lenient id-less travel, which lands them at Home London's default spawn.
                bool hasReturnMarker = returnChunk.ChunkPrefab != null
                    && PlayerSpawnPoint.FindExact(returnChunk.ChunkPrefab, "castle_arena_return") != null;

                if (hasReturnMarker)
                    ChunkManager.Instance.TravelTo(returnChunk, "castle_arena_return", Vector3.zero);
                else
                {
                    Debug.LogWarning("FightPitController: no 'castle_arena_return' PlayerSpawnPoint in Home London; " +
                                     "returning to the default spawn instead. Add that marker beside Prince Mandrew for a tidy arrival.");
                    ChunkManager.Instance.TravelTo(returnChunk, Vector3.zero);
                }
            }
            else if (ChunkManager.Instance != null && ChunkManager.Instance.CurrentChunkData != null)
            {
                Debug.LogWarning("FightPitController: 'Home_London' chunk lookup failed; attempting fallback travel to active chunk origin.");
                ChunkManager.Instance.TravelTo(ChunkManager.Instance.CurrentChunkData, Vector3.zero);
            }
            else
            {
                Debug.LogError("FightPitController: 'Home_London' chunk not found for return travel!");
            }
        }
    }
}
