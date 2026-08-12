using System.Collections.Generic;
using UnityEngine;
using ExiledAlvaston.Combat;
using ExiledAlvaston.Data;
using ExiledAlvaston.Flow;
using ExiledAlvaston.Systems;
using ExiledAlvaston.World;

namespace ExiledAlvaston.Quests
{
    /// <summary>
    /// Watches every active quest's current <see cref="QuestStage"/> and advances each when its
    /// condition is met. Bootstraps itself — nothing needs placing in the scene.
    ///
    /// <b>Multi-quest.</b> All active quests are bound, not just the first. Each active quest gets
    /// its own <see cref="QuestBinding"/> holding that quest's stage and per-condition state, so a
    /// "kill 3" in one quest and a "talk to X" in another run side by side. The HUD tracker shows
    /// only the focused quest, but the watcher advances every active one.
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
    ///
    /// <b>Allocation.</b> Each rebind allocates a fresh <see cref="QuestBinding"/> and its kill
    /// lists. Rebind runs on quest changes and chunk crossings — not per frame — so this is off
    /// the hot path; the per-frame <see cref="Update"/> path still allocates nothing.
    /// </summary>
    public class QuestConditionWatcher : MonoBehaviour
    {
        public static QuestConditionWatcher Instance { get; private set; }

        /// <summary>
        /// One active quest's binding: the stage being watched plus the per-condition state that
        /// stage owns. Rebuilt wholesale on every rebind.
        /// </summary>
        private class QuestBinding
        {
            public string QuestId;
            public int StageIndex = -1;
            public QuestStage Stage;

            // ── TalkTo ──
            public Interactable TalkTarget;
            public bool TalkFired;
            // The delegate is stored so UnbindBinding can remove the exact listener it added.
            public UnityEngine.Events.UnityAction TalkListener;

            // ── Kill ──
            // Per-binding lists, not shared: two quests can each be killing their own keyed actors.
            public readonly List<GameObject> KillCandidates = new List<GameObject>(8);
            public readonly List<Health> KillSubscriptions = new List<Health>(8);
            public int KillCount;
            public bool KillDirty;
            public UnityEngine.Events.UnityAction KillListener;

            // ── Collect ──
            public bool CollectDirty;

            // ── Reach ──
            public Transform ReachTarget;
        }

        // ── What we are currently bound to ──────────────────────────────────────────────────
        private readonly List<QuestBinding> _bindings = new List<QuestBinding>(4);
        // Reused across rebinds so enumerating active quests allocates nothing (CLAUDE.md §4).
        private readonly List<QuestProgress> _activeQuests = new List<QuestProgress>(4);

        // ── Chunk poll ──────────────────────────────────────────────────────────────────────
        private MapChunkData _boundChunkData;
        private GameObject _boundChunkInstance;

        // ── Rebind bookkeeping ──────────────────────────────────────────────────────────────
        private QuestManager _subscribedManager;
        private bool _rebindNeeded = true;
        private bool _rewardScanNeeded = true;

        // ── Collect ─────────────────────────────────────────────────────────────────────────
        // One flag for all Collect bindings: a single inventory change re-evaluates every quest
        // that is currently collecting something.
        private PlayerSession _subscribedSession;
        private bool _collectDirtyAll;

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
            if (_subscribedSession != null)
                _subscribedSession.OnInventoryChanged -= OnInventoryChanged;
            _subscribedSession = null;
            if (Instance == this) Instance = null;
        }

        private void Update()
        {
            EnsureSubscribed();
            EnsureSessionSubscribed();
            PollChunk();

            if (_rebindNeeded)
            {
                _rebindNeeded = false;
                Rebind();
            }

            ApplyPending();
            PollReach();
            ScanRewards();
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
            _rewardScanNeeded = true;
        }

        /// <summary>
        /// PlayerSession survives scene loads but is created by the flow, so it may not exist when
        /// this bootstraps. Same reference-compare-per-frame deal as <see cref="EnsureSubscribed"/>.
        /// The subscription is lifetime-scoped rather than stage-scoped: the callback only raises a
        /// flag, which nothing but a bound Collect stage ever reads.
        /// </summary>
        private void EnsureSessionSubscribed()
        {
            PlayerSession session = PlayerSession.Instance;
            if (session == _subscribedSession) return;

            if (_subscribedSession != null)
                _subscribedSession.OnInventoryChanged -= OnInventoryChanged;

            _subscribedSession = session;

            if (_subscribedSession != null)
                _subscribedSession.OnInventoryChanged += OnInventoryChanged;

            _collectDirtyAll = true;
        }

        /// <summary>Flag only — Update does the work. See the re-entrancy note on the class.</summary>
        private void OnQuestsChanged()
        {
            _rebindNeeded = true;
            _rewardScanNeeded = true;
        }

        /// <summary>Flag only. Fires on every pickup, drop, hand-in and load.</summary>
        private void OnInventoryChanged()
        {
            _collectDirtyAll = true;
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
        /// Drops every subscription and re-resolves them for whatever quests and stages are active
        /// now. Always a full teardown, never an incremental top-up — a listener added twice
        /// counts twice, which is how a "kill 3" objective completes after 2.
        /// </summary>
        private void Rebind()
        {
            Unbind();

            QuestManager mgr = QuestManager.Instance;
            if (mgr == null) return;

            mgr.GetActiveQuests(_activeQuests);

            for (int i = 0; i < _activeQuests.Count; i++)
            {
                QuestProgress active = _activeQuests[i];

                // CONTAINMENT: no definition, no involvement. This is the line that keeps the
                // tutorial quests out of this system entirely.
                QuestDefinition def = QuestDatabase.Find(active.Id);
                if (def == null) continue;

                if (def.Stages == null || def.Stages.Count == 0) continue;
                if (active.StageIndex < 0 || active.StageIndex >= def.Stages.Count)
                {
                    Debug.LogWarning($"QuestConditionWatcher: quest '{active.Id}' is on stage " +
                                     $"{active.StageIndex}, which '{def.name}' does not have " +
                                     $"({def.Stages.Count} stages). Nothing is being watched.");
                    continue;
                }

                var binding = new QuestBinding
                {
                    QuestId = active.Id,
                    StageIndex = active.StageIndex,
                    Stage = def.Stages[active.StageIndex]
                };
                _bindings.Add(binding);

                switch (binding.Stage.ConditionType)
                {
                    case QuestConditionType.TalkTo:
                        BindTalkTo(binding, binding.Stage, def);
                        break;

                    case QuestConditionType.Kill:
                        BindKill(binding, binding.Stage);
                        break;

                    case QuestConditionType.Collect:
                        BindCollect(binding, binding.Stage, def);
                        break;

                    case QuestConditionType.Reach:
                        BindReach(binding, binding.Stage);
                        break;

                    case QuestConditionType.Manual:
                        // Nothing to watch. Bespoke code calls QuestManager.CompleteQuest itself;
                        // the reward scan picks the completion up wherever it came from.
                        break;
                }
            }
        }

        /// <summary>
        /// Releases every subscription. Called from a chunk change, a stage change, a quest
        /// completion and OnDestroy — i.e. before every possible rebind.
        /// </summary>
        private void Unbind()
        {
            for (int i = 0; i < _bindings.Count; i++)
                UnbindBinding(_bindings[i]);
            _bindings.Clear();
        }

        /// <summary>
        /// Releases one binding's subscriptions. Used both by the full teardown and by
        /// <see cref="AdvanceStage"/>, which removes a single quest's binding without disturbing
        /// the others.
        /// </summary>
        private void UnbindBinding(QuestBinding b)
        {
            if (b == null) return;

            // Unity's fake null: an Interactable destroyed with its chunk reads null here, and
            // touching it would throw. Skipping the removal is free — the object is gone.
            if (b.TalkTarget != null && b.TalkListener != null)
                b.TalkTarget.OnInteract.RemoveListener(b.TalkListener);
            b.TalkTarget = null;
            b.TalkListener = null;
            b.TalkFired = false;

            for (int i = 0; i < b.KillSubscriptions.Count; i++)
            {
                Health health = b.KillSubscriptions[i];
                // Unity's fake null: a Health destroyed with its chunk (or by its own death
                // DestroyDelay) reads null here and must not be touched.
                if (health != null && b.KillListener != null)
                    health.OnDeath.RemoveListener(b.KillListener);
            }
            b.KillSubscriptions.Clear();
            b.KillCandidates.Clear();
            b.KillListener = null;
            b.KillDirty = false;

            b.ReachTarget = null;
            b.CollectDirty = false;
        }

        /// <summary>Consumes flags set by event callbacks. The only place quest state is written.</summary>
        private void ApplyPending()
        {
            // A single inventory change re-evaluates every Collect binding.
            if (_collectDirtyAll)
            {
                _collectDirtyAll = false;
                for (int i = 0; i < _bindings.Count; i++)
                {
                    QuestBinding b = _bindings[i];
                    if (b.Stage != null && b.Stage.ConditionType == QuestConditionType.Collect)
                        b.CollectDirty = true;
                }
            }

            // Backwards so AdvanceStage can remove the binding it advanced without disturbing the
            // iteration.
            for (int i = _bindings.Count - 1; i >= 0; i--)
            {
                QuestBinding b = _bindings[i];
                if (b.Stage == null) continue;

                // Safety net: a quest completed through dialogue (CompleteQuestId) while we are
                // still bound to it must not be advanced or written to. The rebind flagged by the
                // completion will drop this binding next frame; until then, skip it.
                if (QuestManager.Instance == null || !QuestManager.Instance.IsActive(b.QuestId))
                    continue;

                switch (b.Stage.ConditionType)
                {
                    case QuestConditionType.TalkTo:
                        if (b.TalkFired)
                        {
                            b.TalkFired = false;
                            AdvanceStage(b);
                        }
                        break;

                    case QuestConditionType.Kill:
                        if (b.KillDirty)
                        {
                            b.KillDirty = false;
                            if (b.KillCount >= Mathf.Max(1, b.Stage.Count))
                            {
                                AdvanceStage(b);
                            }
                            else if (QuestManager.Instance != null)
                            {
                                // Partial only. SetStageProgress deliberately raises no event —
                                // nothing renders the count, so a per-kill HUD rebuild would be waste.
                                QuestManager.Instance.SetStageProgress(b.QuestId, b.KillCount);
                            }
                        }
                        break;

                    case QuestConditionType.Collect:
                        if (b.CollectDirty)
                        {
                            b.CollectDirty = false;
                            ApplyCollectObjective(b);
                        }
                        break;
                }
            }
        }

        /// <summary>
        /// Moves one quest onto its next stage, or completes it if this was the last one. Unbinds
        /// that quest's binding so nothing can fire against a stage already behind us; the
        /// OnQuestsChanged raised by the mutation has already flagged a rebind for the next frame,
        /// which rebuilds the remaining bindings.
        /// </summary>
        private void AdvanceStage(QuestBinding binding)
        {
            QuestManager mgr = QuestManager.Instance;
            if (mgr == null || binding == null || string.IsNullOrEmpty(binding.QuestId))
            {
                if (binding != null) UnbindBinding(binding);
                _bindings.Remove(binding);
                return;
            }

            string questId = binding.QuestId;
            QuestDefinition def = QuestDatabase.Find(questId);
            int next = binding.StageIndex + 1;

            if (def == null || def.Stages == null || next >= def.Stages.Count)
                mgr.CompleteQuest(questId);
            else
                mgr.SetStage(questId, next, def.Stages[next].Objective);

            UnbindBinding(binding);
            _bindings.Remove(binding);
        }

        // ── TalkTo ──────────────────────────────────────────────────────────────────────────

        private void BindTalkTo(QuestBinding b, QuestStage stage, QuestDefinition def)
        {
            b.TalkFired = false;

            GameObject actor = QuestActor.Find(_boundChunkInstance, stage.QuestKey);
            if (actor == null) return; // Not in this chunk. Silent — it may be in another one.

            var interactable = actor.GetComponent<Interactable>();
            if (interactable == null)
            {
                Debug.LogWarning($"QuestConditionWatcher: QuestActor '{stage.QuestKey}' has no " +
                                 "Interactable, so a TalkTo stage can never complete.", actor);
                return;
            }

            b.TalkTarget = interactable;
            // Closure captures the binding so the listener knows which quest fired. Allocated per
            // bind, not per frame — see the allocation note on the class.
            b.TalkListener = () => OnTalkTargetInteracted(b);
            b.TalkTarget.OnInteract.AddListener(b.TalkListener);

            // Landmine warning: a TalkTo final stage completes the quest on the interact, before
            // any dialogue choice is picked. If this NPC also carries the hand-in, the player can
            // walk up, press Interact, back out — and keep the item, get the reward, and hand
            // nothing over. Author hand-ins as Collect last + dialogue completes, never TalkTo
            // last against the hand-in NPC. def is the definition Rebind already resolved.
            if (def != null && def.Stages != null && b.StageIndex == def.Stages.Count - 1)
            {
                Debug.LogWarning($"QuestConditionWatcher: quest '{b.QuestId}' has a TalkTo final " +
                                 "stage. It completes on the interact, before any dialogue choice. " +
                                 "If this NPC also carries the hand-in, author the hand-in as a " +
                                 "Collect last stage + a dialogue CompleteQuestId instead.", b.TalkTarget);
            }
        }

        /// <summary>Flag only. Update advances the stage — see the re-entrancy note on the class.</summary>
        private void OnTalkTargetInteracted(QuestBinding b)
        {
            b.TalkFired = true;
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
        private void BindKill(QuestBinding b, QuestStage stage)
        {
            b.KillDirty = false;
            b.KillCount = 0;

            QuestProgress progress = QuestManager.Instance != null
                ? QuestManager.Instance.Find(b.QuestId)
                : null;
            if (progress != null)
                b.KillCount = Mathf.Max(0, progress.StageProgress);

            QuestActor.FindAll(_boundChunkInstance, stage.QuestKey, b.KillCandidates);

            // One delegate per binding, added to every keyed Health, so a single death knows which
            // quest it belongs to. Stored so UnbindBinding can remove the exact listener.
            b.KillListener = () => OnKillTargetDied(b);

            for (int i = 0; i < b.KillCandidates.Count; i++)
            {
                var health = b.KillCandidates[i].GetComponent<Health>();
                if (health == null) continue;

                // Never subscribe the same Health twice — a doubled listener counts one death as
                // two, and a "kill 3" stage then completes on the second kill.
                if (b.KillSubscriptions.Contains(health)) continue;

                b.KillSubscriptions.Add(health);
                health.OnDeath.AddListener(b.KillListener);
            }

            if (b.KillCandidates.Count > 0 && b.KillSubscriptions.Count == 0)
            {
                Debug.LogWarning($"QuestConditionWatcher: {b.KillCandidates.Count} QuestActor(s) keyed " +
                                 $"'{stage.QuestKey}' but none has a Health, so a Kill stage can " +
                                 "never progress.");
            }
        }

        /// <summary>Counter only. Update writes it through — see the re-entrancy note on the class.</summary>
        private void OnKillTargetDied(QuestBinding b)
        {
            b.KillCount++;
            b.KillDirty = true;
        }

        // ── Collect ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// A Collect stage <b>tracks and reports, and nothing else</b>. It never completes the
        /// quest, never consumes the item, never applies a reward and never advances the stage —
        /// all it does is swap the objective text once the player is carrying enough.
        ///
        /// The hand-in is existing, proven dialogue machinery: a <c>DialogueChoice</c> with
        /// <c>RequiredItem</c> + <c>RequiredItemQuantity</c> (which greys the choice out until the
        /// player has them), <c>ConsumeRequiredItem</c> (which removes the stack on pick) and
        /// <c>CompleteQuestId</c> (which ends the quest). <b>A Collect stage whose quest has no
        /// such dialogue choice anywhere can never end.</b> That cannot be checked here — dialogue
        /// assets live outside <c>Resources/</c> and are not loadable at runtime — so it is a rule
        /// to follow rather than a guard that catches you.
        /// </summary>
        private void BindCollect(QuestBinding b, QuestStage stage, QuestDefinition def)
        {
            b.CollectDirty = true; // Evaluate once on bind, so arriving already-carrying reads right.

            if (stage.Item == null)
            {
                Debug.LogWarning($"QuestConditionWatcher: Collect stage {b.StageIndex} of " +
                                 $"'{def.name}' has no Item, so it will never read as met.", def);
            }

            if (def.Stages != null && b.StageIndex < def.Stages.Count - 1)
            {
                Debug.LogWarning($"QuestConditionWatcher: Collect stage {b.StageIndex} of " +
                                 $"'{def.name}' is not the last stage. A Collect stage only reports " +
                                 "progress and never advances, so every stage after it is " +
                                 "unreachable.", def);
            }
        }

        /// <summary>
        /// Derives the objective text from what the player is currently carrying and writes it only
        /// if it differs from what the journal is already showing. Derived rather than toggled once
        /// so that dropping or selling the item <i>reverts</i> the text — a one-shot flip would
        /// leave "take it back to Mosley" showing over an empty bag.
        ///
        /// The write raises OnQuestsChanged, which flags a rebind, which re-flags this — but the
        /// second pass finds the text already correct and writes nothing, so it settles.
        /// </summary>
        private void ApplyCollectObjective(QuestBinding b)
        {
            QuestManager mgr = QuestManager.Instance;
            if (mgr == null || b.Stage == null) return;

            QuestProgress progress = mgr.Find(b.QuestId);
            if (progress == null) return;

            bool met = b.Stage.Item != null
                       && PlayerSession.Instance != null
                       && PlayerSession.Instance.HasItem(b.Stage.Item, Mathf.Max(1, b.Stage.Quantity));

            string desired = met && !string.IsNullOrEmpty(b.Stage.ObjectiveWhenMet)
                ? b.Stage.ObjectiveWhenMet
                : b.Stage.Objective;

            if (progress.Objective == desired) return;

            mgr.UpdateObjective(b.QuestId, desired);
        }

        // ── Reach ───────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Caches the destination transform: a <see cref="SceneMarker"/> first, since a "go here"
        /// objective usually points at empty ground, falling back to a <see cref="QuestActor"/> for
        /// "go to where this thing is". Silent if neither is in the live chunk — the destination is
        /// very often in a chunk the player has not walked into yet.
        /// </summary>
        private void BindReach(QuestBinding b, QuestStage stage)
        {
            b.ReachTarget = SceneMarker.Find(_boundChunkInstance, stage.QuestKey);
            if (b.ReachTarget != null) return;

            GameObject actor = QuestActor.Find(_boundChunkInstance, stage.QuestKey);
            if (actor != null) b.ReachTarget = actor.transform;
        }

        /// <summary>
        /// The one polled condition — <see cref="SceneMarker"/> has no collider, trigger or event,
        /// so there is nothing to subscribe to. Costs a squared-distance compare per frame per
        /// bound Reach stage, and only while such a stage is actually bound with its destination
        /// resolved in the live chunk. Allocates nothing (CLAUDE.md §4).
        /// </summary>
        private void PollReach()
        {
            CombatController player = CombatController.Instance;
            if (player == null) return;

            for (int i = 0; i < _bindings.Count; i++)
            {
                QuestBinding b = _bindings[i];
                if (b.Stage == null || b.Stage.ConditionType != QuestConditionType.Reach) continue;
                if (b.ReachTarget == null) continue;

                // Safety net, same as ApplyPending: a quest completed through dialogue while we are
                // still bound to it must not be advanced.
                if (QuestManager.Instance == null || !QuestManager.Instance.IsActive(b.QuestId))
                    continue;

                // Horizontal only: movement is on the X/Z plane, Y is up (CLAUDE.md §2). Comparing
                // in 3D would refuse an arrival standing on a step or a kerb.
                Vector3 delta = player.transform.position - b.ReachTarget.position;
                delta.y = 0f;

                float radius = Mathf.Max(0.1f, b.Stage.ReachRadius);
                if (delta.sqrMagnitude > radius * radius) continue;

                AdvanceStage(b);
                // AdvanceStage removed b from the list; step back so the next binding is visited.
                i--;
            }
        }

        // ── Rewards ─────────────────────────────────────────────────────────────────────────

        /// <summary>
        /// Pays out any completed-but-unpaid quest that has a definition. Scans by completion
        /// state rather than by "did I just complete this", so a quest finished entirely through
        /// dialogue — with no involvement from this watcher at all — still gets its reward the
        /// moment someone authors a definition for it. That generality is the point.
        ///
        /// Quests with no definition are skipped, which is the containment rule again.
        /// </summary>
        private void ScanRewards()
        {
            if (!_rewardScanNeeded) return;

            QuestManager mgr = QuestManager.Instance;
            if (mgr == null) return;

            // Defer while a conversation is open. DialogueManager.OnChoiceSelected runs
            // grant -> complete -> consume RequiredItem in that order, so a reward applied the
            // instant the completion landed would fall inside a half-finished hand-in. Waiting
            // costs nothing: RewardsClaimed is not set until the reward is actually applied, so
            // even quitting mid-conversation just pays it on the next Update after the panel
            // closes, or on the next load. Note Update still runs while paused — PauseManager
            // only zeroes Time.timeScale — which is what makes this deferral necessary rather
            // than automatic.
            if (Dialogue.DialogueManager.IsDialogueOpen) return;

            // Stays true if any payment had to be deferred, so the scan re-runs next frame.
            // Clearing it unconditionally would strand a deferred reward until the next unrelated
            // quest event — which for the last quest in a run means never.
            bool deferred = false;

            // Indexed for, not foreach: Quests is an IReadOnlyList, and foreach over an interface
            // boxes the enumerator and allocates on every call (CLAUDE.md §4).
            IReadOnlyList<QuestProgress> quests = mgr.Quests;
            for (int i = 0; i < quests.Count; i++)
            {
                QuestProgress q = quests[i];
                if (q == null || !q.IsComplete || q.RewardsClaimed) continue;

                QuestDefinition def = QuestDatabase.Find(q.Id);
                if (def == null) continue;

                // Claimed only once the reward has actually been delivered. ApplyReward checks
                // everything it needs up front and pays nothing if a piece is missing, so a
                // retry can never double-pay — and a reward is never silently lost to a
                // singleton that happened to be absent for one frame.
                if (!ApplyReward(def, q))
                {
                    deferred = true;
                    continue;
                }

                q.RewardsClaimed = true;
            }

            _rewardScanNeeded = deferred;
        }

        /// <summary>
        /// Pays a quest's authored reward. Returns false if it could not be paid *yet* — a
        /// manager it needs is missing this frame — in which case nothing at all has been
        /// granted and the caller leaves RewardsClaimed unset so the next Update retries.
        ///
        /// Every precondition is checked before anything is handed over, deliberately: a partial
        /// payment followed by a retry would grant the item twice.
        /// </summary>
        private bool ApplyReward(QuestDefinition def, QuestProgress quest)
        {
            QuestReward reward = def.Reward;
            if (reward == null) return true;

            bool paysItem = reward.Item != null && reward.Quantity > 0;
            bool paysPounds = reward.PoundsAmount > 0;
            bool paysXP = reward.XP > 0;

            // XP belongs in this guard for the same reason the other two do: without it an
            // XP-only reward would return true, the caller would set RewardsClaimed, and the XP
            // would be lost for good with nothing logged.
            if ((paysItem || paysPounds || paysXP) && PlayerSession.Instance == null) return false;
            if (reward.ClearsWantedLevel && WantedManager.Instance == null) return false;

            if (paysItem)
                PlayerSession.Instance.AddItem(reward.Item, reward.Quantity);

            if (paysPounds)
                PlayerSession.Instance.AddPounds(reward.PoundsAmount);

            if (paysXP)
                PlayerSession.Instance.GrantXP(reward.XP, quest.Id);

            if (reward.ClearsWantedLevel)
                WantedManager.Instance.ClearWanted();

            // An item with no quantity is an authoring slip, not a deferral — claiming it stops
            // the scan retrying forever over a reward that can never pay.
            if (reward.Item != null && reward.Quantity <= 0)
            {
                Debug.LogWarning($"QuestConditionWatcher: '{quest.Id}' is authored to reward " +
                                 $"'{reward.Item.name}' with Quantity {reward.Quantity} — " +
                                 "nothing was granted. Set a Quantity of 1 or more.", def);
            }

            return true;
        }
    }
}
