using System.Collections.Generic;
using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Quests
{
    /// <summary>
    /// Watches the active quest's current <see cref="QuestStage"/> and advances it when its
    /// condition is met. Bootstraps itself — nothing needs placing in the scene.
    ///
    /// <b>Containment.</b> A quest with no <see cref="QuestDefinition"/> asset under
    /// <c>Resources/Quests/</c> is never touched: <see cref="QuestDatabase.Find"/> returns null and
    /// every path here bails out. The tutorial quests (<c>escape_manor</c>, <c>spark_of_talent</c>)
    /// deliberately have no definition and keep running entirely off their own code.
    ///
    /// <b>All quest-state mutation happens in <see cref="Update"/>.</b> Event callbacks
    /// (<c>Interactable.OnInteract</c>, <c>Health.OnDeath</c>, inventory changes) only set a flag
    /// or bump a counter — they never call <see cref="QuestManager"/> and never apply a reward.
    /// Mutating from inside a listener would re-enter: the mutation raises
    /// <c>OnQuestsChanged</c>, which rebinds listeners, from inside the listener list currently
    /// being invoked. Deferring one frame costs nothing and removes the whole class of bug.
    ///
    /// <b>Chunk changes are polled, not hooked</b> — <c>CurrentChunkData</c> is written from seven
    /// places across six files (CLAUDE.md §5), so any single hook misses the others. Same pattern
    /// as <c>VehicleSpawner</c>.
    /// </summary>
    public class QuestConditionWatcher : MonoBehaviour
    {
        public static QuestConditionWatcher Instance { get; private set; }

        // ── What we are currently bound to ──────────────────────────────────────────────────
        private string _boundQuestId;
        private int _boundStageIndex = -1;
        private QuestStage _boundStage;

        // ── Chunk poll ──────────────────────────────────────────────────────────────────────
        private MapChunkData _boundChunkData;
        private GameObject _boundChunkInstance;

        // ── Rebind bookkeeping ──────────────────────────────────────────────────────────────
        private QuestManager _subscribedManager;
        private bool _rebindNeeded = true;

        // ── TalkTo ──────────────────────────────────────────────────────────────────────────
        private Interactable _talkTarget;
        private bool _talkFired;

        // ── Kill ────────────────────────────────────────────────────────────────────────────
        // Both lists are reused across every rebind rather than reallocated (CLAUDE.md §4).
        private readonly List<GameObject> _killCandidates = new List<GameObject>(8);
        private readonly List<Health> _killSubscriptions = new List<Health>(8);
        private int _killCount;
        private bool _killDirty;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void Bootstrap()
        {
            if (Instance != null) return;

            var go = new GameObject("~QuestConditionWatcher");
            DontDestroyOnLoad(go);
            go.AddComponent<QuestConditionWatcher>();
        }

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else Destroy(gameObject);
        }

        private void OnDestroy()
        {
            Unbind();
            if (_subscribedManager != null)
                _subscribedManager.OnQuestsChanged -= OnQuestsChanged;
            _subscribedManager = null;
            if (Instance == this) Instance = null;
        }

        private void Update()
        {
            EnsureSubscribed();
            PollChunk();

            if (_rebindNeeded)
            {
                _rebindNeeded = false;
                Rebind();
            }

            ApplyPending();
        }

        // ── Subscription ────────────────────────────────────────────────────────────────────

        /// <summary>
        /// QuestManager is a scene object, so it may not exist when this bootstraps and it is
        /// replaced by a scene reload. Re-checking each frame is a reference compare.
        /// </summary>
        private void EnsureSubscribed()
        {
            QuestManager mgr = QuestManager.Instance;
            if (mgr == _subscribedManager) return;

            if (_subscribedManager != null)
                _subscribedManager.OnQuestsChanged -= OnQuestsChanged;

            _subscribedManager = mgr;

            if (_subscribedManager != null)
                _subscribedManager.OnQuestsChanged += OnQuestsChanged;

            _rebindNeeded = true;
        }

        /// <summary>Flag only — Update does the work. See the re-entrancy note on the class.</summary>
        private void OnQuestsChanged()
        {
            _rebindNeeded = true;
        }

        private void PollChunk()
        {
            ChunkManager chunks = ChunkManager.Instance;
            MapChunkData data = chunks != null ? chunks.CurrentChunkData : null;
            GameObject instance = chunks != null ? chunks.CurrentChunkInstance : null;

            // Unlike VehicleSpawner this does NOT skip the null half of a transition: a chunk going
            // away is exactly when the actors we are subscribed to are destroyed, so it has to
            // unbind. The extra rebind that costs (one for the teardown, one for the new chunk) is
            // a couple of GetComponentsInChildren calls per crossing.
            if (data == _boundChunkData && instance == _boundChunkInstance) return;

            _boundChunkData = data;
            _boundChunkInstance = instance;
            _rebindNeeded = true;
        }

        // ── Bind / unbind ───────────────────────────────────────────────────────────────────

        /// <summary>
        /// Drops every subscription and re-resolves them for whatever quest and stage is active
        /// now. Always a full teardown, never an incremental top-up — a listener added twice
        /// counts twice, which is how a "kill 3" objective completes after 2.
        /// </summary>
        private void Rebind()
        {
            Unbind();

            QuestManager mgr = QuestManager.Instance;
            if (mgr == null) return;

            QuestProgress active = mgr.GetActiveQuest();
            if (active == null) return;

            // CONTAINMENT: no definition, no involvement. This is the line that keeps the tutorial
            // quests out of this system entirely.
            QuestDefinition def = QuestDatabase.Find(active.Id);
            if (def == null) return;

            if (def.Stages == null || def.Stages.Count == 0) return;
            if (active.StageIndex < 0 || active.StageIndex >= def.Stages.Count)
            {
                Debug.LogWarning($"QuestConditionWatcher: quest '{active.Id}' is on stage " +
                                 $"{active.StageIndex}, which '{def.name}' does not have " +
                                 $"({def.Stages.Count} stages). Nothing is being watched.");
                return;
            }

            _boundQuestId = active.Id;
            _boundStageIndex = active.StageIndex;
            _boundStage = def.Stages[active.StageIndex];

            switch (_boundStage.ConditionType)
            {
                case QuestConditionType.TalkTo:
                    BindTalkTo(_boundStage);
                    break;

                case QuestConditionType.Kill:
                    BindKill(_boundStage);
                    break;

                case QuestConditionType.Manual:
                    // Nothing to watch. Bespoke code calls QuestManager.CompleteQuest itself; the
                    // reward scan picks the completion up wherever it came from.
                    break;
            }
        }

        /// <summary>
        /// Releases every subscription. Called from a chunk change, a stage change, a quest
        /// completion and OnDestroy — i.e. before every possible rebind.
        /// </summary>
        private void Unbind()
        {
            UnbindTalkTo();
            UnbindKill();

            _boundQuestId = null;
            _boundStageIndex = -1;
            _boundStage = null;
        }

        /// <summary>Consumes flags set by event callbacks. The only place quest state is written.</summary>
        private void ApplyPending()
        {
            if (_boundStage == null) return;

            switch (_boundStage.ConditionType)
            {
                case QuestConditionType.TalkTo:
                    if (_talkFired)
                    {
                        _talkFired = false;
                        AdvanceStage();
                    }
                    break;

                case QuestConditionType.Kill:
                    if (_killDirty)
                    {
                        _killDirty = false;
                        if (_killCount >= Mathf.Max(1, _boundStage.Count))
                        {
                            AdvanceStage();
                        }
                        else if (QuestManager.Instance != null)
                        {
                            // Partial only. SetStageProgress deliberately raises no event —
                            // nothing renders the count, so a per-kill HUD rebuild would be waste.
                            QuestManager.Instance.SetStageProgress(_boundQuestId, _killCount);
                        }
                    }
                    break;
            }
        }

        /// <summary>
        /// Moves onto the next stage, or completes the quest if this was the last one. Unbinds
        /// afterwards so nothing can fire against a stage already behind us; the OnQuestsChanged
        /// raised by the mutation has already flagged a rebind for the next frame.
        /// </summary>
        private void AdvanceStage()
        {
            QuestManager mgr = QuestManager.Instance;
            if (mgr == null || string.IsNullOrEmpty(_boundQuestId))
            {
                Unbind();
                return;
            }

            string questId = _boundQuestId;
            QuestDefinition def = QuestDatabase.Find(questId);
            int next = _boundStageIndex + 1;

            if (def == null || def.Stages == null || next >= def.Stages.Count)
                mgr.CompleteQuest(questId);
            else
                mgr.SetStage(questId, next, def.Stages[next].Objective);

            Unbind();
        }

        // ── TalkTo ──────────────────────────────────────────────────────────────────────────

        private void BindTalkTo(QuestStage stage)
        {
            _talkFired = false;

            GameObject actor = QuestActor.Find(_boundChunkInstance, stage.QuestKey);
            if (actor == null) return; // Not in this chunk. Silent — it may be in another one.

            var interactable = actor.GetComponent<Interactable>();
            if (interactable == null)
            {
                Debug.LogWarning($"QuestConditionWatcher: QuestActor '{stage.QuestKey}' has no " +
                                 "Interactable, so a TalkTo stage can never complete.", actor);
                return;
            }

            _talkTarget = interactable;
            _talkTarget.OnInteract.AddListener(OnTalkTargetInteracted);
        }

        private void UnbindTalkTo()
        {
            // Unity's fake null: an Interactable destroyed with its chunk reads null here, and
            // touching it would throw. Skipping the removal is free — the object is gone.
            if (_talkTarget != null)
                _talkTarget.OnInteract.RemoveListener(OnTalkTargetInteracted);

            _talkTarget = null;
            _talkFired = false;
        }

        /// <summary>Flag only. Update advances the stage — see the re-entrancy note on the class.</summary>
        private void OnTalkTargetInteracted()
        {
            _talkFired = true;
        }

        // ── Kill ────────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Subscribes to every keyed actor's death in the live chunk. The running count is seeded
        /// from <c>QuestProgress.StageProgress</c>, which is where <see cref="ApplyPending"/> wrote
        /// it and what a save carries — otherwise a chunk crossing or a reload would silently
        /// restart the tally.
        ///
        /// ⚠️ Kill targets are re-instantiated with their chunk, so leaving and returning re-arms
        /// them while the count carries on: a "kill 3" stage can be finished by killing one
        /// respawning actor three times. Author kill stages against targets in a single chunk.
        /// </summary>
        private void BindKill(QuestStage stage)
        {
            _killDirty = false;
            _killCount = 0;

            QuestProgress progress = QuestManager.Instance != null
                ? QuestManager.Instance.Find(_boundQuestId)
                : null;
            if (progress != null)
                _killCount = Mathf.Max(0, progress.StageProgress);

            QuestActor.FindAll(_boundChunkInstance, stage.QuestKey, _killCandidates);

            for (int i = 0; i < _killCandidates.Count; i++)
            {
                var health = _killCandidates[i].GetComponent<Health>();
                if (health == null) continue;

                // Never subscribe the same Health twice — a doubled listener counts one death as
                // two, and a "kill 3" stage then completes on the second kill.
                if (_killSubscriptions.Contains(health)) continue;

                _killSubscriptions.Add(health);
                health.OnDeath.AddListener(OnKillTargetDied);
            }

            if (_killCandidates.Count > 0 && _killSubscriptions.Count == 0)
            {
                Debug.LogWarning($"QuestConditionWatcher: {_killCandidates.Count} QuestActor(s) keyed " +
                                 $"'{stage.QuestKey}' but none has a Health, so a Kill stage can " +
                                 "never progress.");
            }
        }

        private void UnbindKill()
        {
            for (int i = 0; i < _killSubscriptions.Count; i++)
            {
                Health health = _killSubscriptions[i];
                // Unity's fake null: a Health destroyed with its chunk (or by its own death
                // DestroyDelay) reads null here and must not be touched.
                if (health != null)
                    health.OnDeath.RemoveListener(OnKillTargetDied);
            }

            _killSubscriptions.Clear();
            _killCandidates.Clear();
            _killDirty = false;
        }

        /// <summary>Counter only. Update writes it through — see the re-entrancy note on the class.</summary>
        private void OnKillTargetDied()
        {
            _killCount++;
            _killDirty = true;
        }
    }
}
