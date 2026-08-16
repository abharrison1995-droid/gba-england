using System;
using System.Collections.Generic;
using UnityEngine;
using GBHEngland.Data;

namespace GBHEngland.Quests
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
    /// Tiny quest list for GBH: England — start/complete/track active quests.
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

        /// <summary>
        /// Every active quest, in list order. The caller owns <paramref name="results"/> and it is
        /// cleared first, so the list can be reused across rebinds instead of allocating a fresh
        /// one each time (CLAUDE.md §4). The watcher binds ALL of these, not just the first.
        /// </summary>
        public void GetActiveQuests(List<QuestProgress> results)
        {
            if (results == null) return;
            results.Clear();
            for (int i = 0; i < _quests.Count; i++)
            {
                QuestProgress q = _quests[i];
                if (q != null && q.IsActive && !q.IsComplete)
                    results.Add(q);
            }
        }

        /// <summary>
        /// The id of the quest the HUD tracker shows. Player-chosen via the journal; a brand-new
        /// grant auto-focuses it. Null or stale falls back to the first active quest, so the
        /// tracker always has something to show while any quest is active.
        /// </summary>
        public string FocusedQuestId { get; private set; }

        /// <summary>
        /// The quest the tracker shows: the explicit focus if it is still an active quest,
        /// otherwise the first active quest (the old single-quest behaviour).
        /// </summary>
        public QuestProgress GetFocusedQuest()
        {
            if (!string.IsNullOrEmpty(FocusedQuestId))
            {
                QuestProgress focused = Find(FocusedQuestId);
                if (focused != null && focused.IsActive && !focused.IsComplete)
                    return focused;
            }
            return GetActiveQuest();
        }

        /// <summary>
        /// Points the tracker at a specific active quest. Refuses quests that aren't active —
        /// you can't focus a completed or never-started quest. Raises OnQuestsChanged so the
        /// tracker repaints.
        /// </summary>
        public void SetFocusedQuest(string id)
        {
            QuestProgress q = Find(id);
            if (q == null || !q.IsActive || q.IsComplete) return;
            if (FocusedQuestId == id) return;
            FocusedQuestId = id;
            OnQuestsChanged?.Invoke();
        }

        public void StartQuest(string id, string title, string objective, string giver = null, string location = null)
        {
            // Resolve the definition once so both branches can fall back to it. Null for
            // definition-less quests (the tutorial's), which keep their bespoke text — the
            // containment rule.
            QuestDefinition def = QuestDatabase.Find(id);

            // Landmine fallbacks: the journal reads QuestProgress.Giver/.Location and the HUD
            // tracker reads Objective. If the granting dialogue left one blank, fall back to the
            // definition's own fields (QuestDefinition.Title/Giver/Location and
            // Stages[0].Objective) so the journal and tracker never show an empty line.
            string resolvedTitle = string.IsNullOrEmpty(title) && def != null ? def.Title : title;
            string resolvedObjective = string.IsNullOrEmpty(objective) && def != null
                && def.Stages != null && def.Stages.Count > 0
                ? def.Stages[0].Objective : objective;
            string resolvedGiver = string.IsNullOrEmpty(giver) && def != null ? def.Giver : giver;
            string resolvedLocation = string.IsNullOrEmpty(location) && def != null ? def.Location : location;

            var existing = Find(id);
            if (existing != null)
            {
                if (existing.IsComplete) return;
                existing.IsActive = true;
                existing.Title = resolvedTitle;

                // Do not rewind the objective of a quest already in flight. DialogueManager
                // re-shows a conversation's starting node every time, so a GrantQuestId choice
                // stays selectable forever — talking to the giver again would otherwise revert
                // the journal and the HUD tracker to stage 0's text while QuestConditionWatcher
                // is still bound to a later stage, and the player would follow an objective that
                // can no longer complete. Stage state is only ever non-zero for a
                // QuestDefinition-driven quest, so the tutorial's re-activation path — which
                // relies on this refresh — is untouched.
                if (existing.StageIndex == 0 && existing.StageProgress == 0)
                    existing.Objective = resolvedObjective;

                if (!string.IsNullOrEmpty(resolvedGiver)) existing.Giver = resolvedGiver;
                if (!string.IsNullOrEmpty(resolvedLocation)) existing.Location = resolvedLocation;
            }
            else
            {
                var quest = new QuestProgress
                {
                    Id = id,
                    Title = resolvedTitle,
                    Objective = resolvedObjective,
                    Giver = resolvedGiver,
                    Location = resolvedLocation,
                    IsActive = true,
                    IsComplete = false
                };
                _quests.Add(quest);

                // A brand-new grant auto-focuses: the tracker switches to it immediately. The
                // player can re-focus journal-only.
                FocusedQuestId = id;

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

                // If the focused quest just completed, advance the focus to the next active quest
                // so the tracker doesn't keep pointing at a finished quest. GetActiveQuest returns
                // the first active one in list order; if none is left, the focus clears and the
                // tracker hides.
                if (FocusedQuestId == id)
                    FocusedQuestId = GetActiveQuest()?.Id;
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
            // Re-set by RestoreFocusedQuest after the list is restored; clearing here keeps a
            // stale focus from surviving a load that no longer contains its quest.
            FocusedQuestId = null;
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

        /// <summary>
        /// Restore the focused quest id from a save. Clears it if it no longer points at an
        /// active quest (a stale or completed focus), so the tracker falls back to the first
        /// active quest rather than showing nothing. Raises OnQuestsChanged so the tracker
        /// repaints even when the caller doesn't refresh it explicitly.
        /// </summary>
        public void RestoreFocusedQuest(string saved)
        {
            FocusedQuestId = saved;
            QuestProgress q = Find(saved);
            if (q == null || !q.IsActive || q.IsComplete)
                FocusedQuestId = null;
            OnQuestsChanged?.Invoke();
        }

        public void ClearAll()
        {
            _quests.Clear();
            FocusedQuestId = null;
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
