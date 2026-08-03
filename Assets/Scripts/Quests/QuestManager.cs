using System;
using System.Collections.Generic;
using UnityEngine;

namespace ExiledAlvaston.Quests
{
    [Serializable]
    public class QuestProgress
    {
        public string Id;
        public string Title;
        public string Objective;
        [Tooltip("Who handed out the quest (NPC name). Shown under the title in the journal.")]
        public string Giver;
        [Tooltip("Where the quest sends you. Shown on the quest detail page.")]
        public string Location;
        public bool IsActive;
        public bool IsComplete;

        // ── Appended for QuestDefinition-driven quests. Appending is safe; inserting is not —
        // this whole class is serialized wholesale into savegame.json by JsonUtility (CLAUDE.md
        // §6/§7). Public fields, not properties: JsonUtility only serializes public fields, so a
        // property here would silently never persist.
        [Tooltip("Which stage of the quest's QuestDefinition is current. 0 for quests with no definition.")]
        public int StageIndex;
        [Tooltip("Partial progress within the current stage (e.g. 2 of 3 killed).")]
        public int StageProgress;
        [Tooltip("Set once QuestConditionWatcher has paid out this quest's reward, so it pays once.")]
        public bool RewardsClaimed;
    }

    /// <summary>
    /// Tiny quest list for Discover England — start/complete/track active quests.
    /// </summary>
    public class QuestManager : MonoBehaviour
    {
        public static QuestManager Instance { get; private set; }

        public event Action OnQuestsChanged;

        private readonly List<QuestProgress> _quests = new List<QuestProgress>(8);

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
        }

        public IReadOnlyList<QuestProgress> Quests => _quests;

        public QuestProgress GetActiveQuest()
        {
            for (int i = 0; i < _quests.Count; i++)
            {
                if (_quests[i].IsActive && !_quests[i].IsComplete)
                    return _quests[i];
            }
            return null;
        }

        public void StartQuest(string id, string title, string objective, string giver = null, string location = null)
        {
            var existing = Find(id);
            if (existing != null)
            {
                if (existing.IsComplete) return;
                existing.IsActive = true;
                existing.Title = title;

                // Do not rewind the objective of a quest already in flight. DialogueManager
                // re-shows a conversation's starting node every time, so a GrantQuestId choice
                // stays selectable forever — talking to the giver again would otherwise revert
                // the journal and the HUD tracker to stage 0's text while QuestConditionWatcher
                // is still bound to a later stage, and the player would follow an objective that
                // can no longer complete. Stage state is only ever non-zero for a
                // QuestDefinition-driven quest, so the tutorial's re-activation path — which
                // relies on this refresh — is untouched.
                if (existing.StageIndex == 0 && existing.StageProgress == 0)
                    existing.Objective = objective;

                if (!string.IsNullOrEmpty(giver)) existing.Giver = giver;
                if (!string.IsNullOrEmpty(location)) existing.Location = location;
            }
            else
            {
                var quest = new QuestProgress
                {
                    Id = id,
                    Title = title,
                    Objective = objective,
                    Giver = giver,
                    Location = location,
                    IsActive = true,
                    IsComplete = false
                };
                _quests.Add(quest);

                // Brand-new quest only — re-activations (e.g. tutorial restart) stay quiet
                UI.QuestPopupUI.Show(quest);
            }

            OnQuestsChanged?.Invoke();
        }

        public void UpdateObjective(string id, string objective)
        {
            var q = Find(id);
            if (q == null || q.IsComplete) return;
            q.Objective = objective;
            OnQuestsChanged?.Invoke();
        }

        /// <summary>
        /// Moves an already-started quest onto a new stage of its <c>QuestDefinition</c>: records
        /// the stage index, clears any partial progress carried over from the previous stage, and
        /// swaps in that stage's objective text. Does nothing for an id that isn't in the list —
        /// callers only ever reach here for a quest they've already confirmed active.
        /// </summary>
        public void SetStage(string id, int stageIndex, string objective)
        {
            var q = Find(id);
            if (q == null) return;
            q.StageIndex = stageIndex;
            q.StageProgress = 0;
            q.Objective = objective;
            OnQuestsChanged?.Invoke();
        }

        /// <summary>
        /// Records partial progress inside the current stage (e.g. 2 of 3 bandits down) so it
        /// survives a save. Deliberately does NOT raise <see cref="OnQuestsChanged"/>: nothing
        /// displays <c>StageProgress</c> — the journal and the HUD tracker both render
        /// <c>Objective</c> — so an event here would force a HUD layout rebuild per kill for no
        /// visible change. If a counter ever appears in the UI, raise it here as well.
        /// </summary>
        public void SetStageProgress(string id, int progress)
        {
            var q = Find(id);
            if (q == null) return;
            q.StageProgress = progress;
        }

        public void CompleteQuest(string id)
        {
            var q = Find(id);

            // Already done — say nothing and change nothing. Two things can legitimately try to
            // complete the same quest (a definition's last stage and a dialogue node carrying a
            // matching CompleteQuestId), and a second OnQuestsChanged for a no-op change would
            // re-run every subscriber's refresh for nothing.
            if (q != null && q.IsComplete) return;

            if (q == null)
            {
                _quests.Add(new QuestProgress
                {
                    Id = id,
                    Title = id,
                    Objective = "",
                    IsActive = false,
                    IsComplete = true
                });
            }
            else
            {
                q.IsComplete = true;
                q.IsActive = false;
            }
            OnQuestsChanged?.Invoke();
        }

        public bool IsComplete(string id)
        {
            var q = Find(id);
            return q != null && q.IsComplete;
        }

        /// <summary>True if this quest id has been started and isn't complete yet.</summary>
        public bool IsActive(string id)
        {
            var q = Find(id);
            return q != null && q.IsActive && !q.IsComplete;
        }

        /// <summary>Replace all quest state with a saved snapshot (load game).</summary>
        public void RestoreQuests(List<QuestProgress> saved)
        {
            _quests.Clear();
            if (saved != null)
            {
                foreach (var q in saved)
                {
                    if (q != null && !string.IsNullOrEmpty(q.Id))
                        _quests.Add(q);
                }
            }
            OnQuestsChanged?.Invoke();
        }

        public void ClearAll()
        {
            _quests.Clear();
            OnQuestsChanged?.Invoke();
        }

        /// <summary>The live progress record for an id, or null if the quest was never started.</summary>
        public QuestProgress Find(string id)
        {
            for (int i = 0; i < _quests.Count; i++)
            {
                if (_quests[i].Id == id) return _quests[i];
            }
            return null;
        }
    }
}
