using UnityEngine;
using System.Collections;
using ExiledAlvaston.Data;
using ExiledAlvaston.Combat;
using ExiledAlvaston.World;
using ExiledAlvaston.UI;
using ExiledAlvaston.Quests;
using ExiledAlvaston.Vibe;
using ExiledAlvaston.Dialogue;

namespace ExiledAlvaston.Flow
{
    /// <summary>
    /// "Spark of Talent" — the first magic quest. Daniel Pauls (Paul Daniels' step-nephew) clocks
    /// the player's aura and sends them to sound out a cagey "Under Housed" geezer in the city, who
    /// panics and zaps them. Kill him, return, and Daniel teaches the first spell (which the player
    /// names). Spawned at runtime on the London chunk like <see cref="TutorialSequence"/>; NPCs are
    /// built in code, and Daniel stands on the movable "DanielPaulsSpawn" marker in the prefab.
    /// </summary>
    public class MagicTutorial : MonoBehaviour
    {
        public const string QuestId = "spark_of_talent";
        public static MagicTutorial Instance { get; private set; }

        public enum Stage { NotMet, SeekUnderHoused, ReturnToDaniel, Done }
        public Stage CurrentStage = Stage.NotMet;

        /// <summary>
        /// Which presets these two are built from. These are keys into
        /// <see cref="PlacementPresetLibrary"/>, not asset names — so the presets can be renamed,
        /// re-arted, resized or given a different temperament without this file changing, which is
        /// the entire point of routing the tutorial through them.
        /// </summary>
        public const string DanielPresetKey = "DanielPauls";
        public const string GeezerPresetKey = "TracksuitGeezer";

        private CharacterData _danielData, _underHousedData;
        private DialogueData _intro, _nudge, _reward, _done, _underHousedTalk;
        private GameObject _daniel, _underHoused;

        private void Awake() { Instance = this; }

        private void OnDestroy()
        {
            if (QuestManager.Instance != null) QuestManager.Instance.OnQuestsChanged -= OnQuestsChanged;
            if (Instance == this) Instance = null;
        }

        /// <summary>
        /// Kick the quest off in London (called by GameFlow once the chunk is up).
        ///
        /// Takes no art any more. It used to be handed one sprite for both characters — which is
        /// why Daniel Pauls and the geezer looked identical, and identical to a bandit. Each now
        /// resolves its own preset, and looks like whatever that preset's subject was drawn as.
        /// </summary>
        public void Begin()
        {
            BuildData();

            // Resume from quest state so re-entering London shows the right beat.
            if (QuestManager.Instance != null)
            {
                QuestManager.Instance.OnQuestsChanged += OnQuestsChanged;
                var q = FindQuest();
                if (q != null && q.IsComplete) CurrentStage = Stage.Done;
                else if (q != null && q.IsActive) CurrentStage = Stage.SeekUnderHoused;
            }

            SpawnDaniel();
            if (CurrentStage == Stage.SeekUnderHoused)
                SpawnUnderHoused();
        }

        private QuestProgress FindQuest()
        {
            if (QuestManager.Instance == null) return null;
            foreach (var q in QuestManager.Instance.Quests)
                if (q.Id == QuestId) return q;
            return null;
        }

        private void OnQuestsChanged()
        {
            var q = FindQuest();
            if (q == null) return;

            if (q.IsComplete) { CurrentStage = Stage.Done; return; }

            // Player just accepted the quest from Daniel → the geezer appears in the city.
            if (CurrentStage == Stage.NotMet && q.IsActive)
            {
                CurrentStage = Stage.SeekUnderHoused;
                SpawnUnderHoused();
            }
        }

        /// <summary>Called by UnderHousedNPC when he dies.</summary>
        public void OnUnderHousedDead()
        {
            if (CurrentStage != Stage.SeekUnderHoused) return;
            CurrentStage = Stage.ReturnToDaniel;
            if (QuestManager.Instance != null)
                QuestManager.Instance.UpdateObjective(QuestId,
                    "You're crackling with it. Get back to Daniel Pauls and tell him what happened.");
            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("Something woke up in you. Back to Daniel Pauls.");
        }

        /// <summary>The mentor conversation that fits the current beat.</summary>
        public DialogueData MentorDialogueForStage()
        {
            switch (CurrentStage)
            {
                case Stage.SeekUnderHoused: return _nudge;
                case Stage.ReturnToDaniel:  return _reward;
                case Stage.Done:            return _done;
                default:                    return _intro;
            }
        }

        // ---------- content ----------

        private void BuildData()
        {
            _danielData = ScriptableObject.CreateInstance<CharacterData>();
            _danielData.CharacterName = "Daniel Pauls";
            _underHousedData = ScriptableObject.CreateInstance<CharacterData>();
            _underHousedData.CharacterName = "Under Housed";

            _intro = Tree(Node(_danielData,
                "Oi— hold up. You've got a right glow comin' off you, mate. A proper aura. You not feel that?",
                Choice("What you on about? What you up to?", Node(_danielData,
                    "Bit of research, innit. Big uptick in... events round here. Sparks. Flashes. Folk actin' funny.",
                    QuestChoice("Actually — saw a bloke get zapped by some smackhead by the Jones' last week. Thought I'd had some dodgy bud.",
                        Node(_danielData, "That weren't the bud, son — that were magic. Do us a favour: walk into the city and have a word with that twitchy geezer over there. Careful, mind.")),
                    Choice("Right. I'll leave you to it.", null))),
                Choice("Not now, weirdo.", null)));

            _nudge = Tree(Node(_danielData,
                "You still here? Get into the city and find that twitchy geezer. Ask him about the sparks — and mind he don't spark you first."));

            _done = Tree(Node(_danielData,
                "Look at you, proper little Dynamo. Keep it out the city, yeah? Plebs get nervy, and the law gets nervier. I'll be in touch."));

            _reward = Tree(Node(_danielData,
                "There it is! You're buzzin' with it — I can see it comin' off you. He zapped you and you're still standin'. You're one of us now, son.",
                RewardChoice("So... what happens now?", Node(_danielData,
                    "Now you learn to sling it back. Hold your hand out... feel that? That's yours now. Go on — give it a name. Whatever you're happy shoutin' out loud."))));

            _underHousedTalk = Tree(Node(_underHousedData,
                "...You what? I ain't done nothin'. Move along, yeah?",
                Choice("Saw you near the Jones' the other night. Bit of a light show, weren't it?",
                    Node(_underHousedData, "I don't— I don't know what you're on about. Back off. I'm tellin' you, BACK OFF—")),
                Choice("Someone's been zappin' folk round here. That you, mate?",
                    Node(_underHousedData, "Nnnh— you shouldn't've said that. You shouldn't've—"))));
        }

        private static DialogueData Tree(DialogueNode start)
        {
            var d = ScriptableObject.CreateInstance<DialogueData>();
            d.StartingNode = start;
            return d;
        }

        private static DialogueNode Node(CharacterData who, string text, params DialogueChoice[] choices)
        {
            var n = new DialogueNode { Speaker = who, DialogueText = text };
            if (choices != null)
                foreach (var c in choices) if (c != null) n.Choices.Add(c);
            return n;
        }

        private static DialogueChoice Choice(string text, DialogueNode next)
            => new DialogueChoice { ChoiceText = text, NextNode = next };

        private DialogueChoice QuestChoice(string text, DialogueNode next) => new DialogueChoice
        {
            ChoiceText = text,
            NextNode = next,
            GrantQuestId = QuestId,
            GrantQuestTitle = "Spark of Talent",
            GrantQuestObjective = "Daniel Pauls reckons the sparks are real magic. Walk into the city and sound out the twitchy geezer he pointed you at.",
            GrantQuestLocation = "London"
        };

        private DialogueChoice RewardChoice(string text, DialogueNode next) => new DialogueChoice
        {
            ChoiceText = text,
            NextNode = next,
            TeachSpark = true,
            CompleteQuestId = QuestId
        };

        // ---------- NPC spawning ----------

        private void SpawnDaniel()
        {
            if (_daniel != null) return;
            Vector3 pos = SceneMarker.ResolveWorldPosition(ChunkRoot(), "DanielPaulsSpawn", new Vector3(-72f, 0f, 70f));
            _daniel = BuildNpc(DanielPresetKey, pos);
            if (_daniel == null) return;

            Interactable interactable = OwnInteraction(_daniel, "Talk to Daniel Pauls");
            var mentor = _daniel.AddComponent<MagicMentorNPC>();
            interactable.OnInteract.AddListener(mentor.Interact);
        }

        private void SpawnUnderHoused()
        {
            if (_underHoused != null) return;
            Vector3 basePos = _daniel != null ? _daniel.transform.position : Vector3.zero;
            _underHoused = BuildNpc(GeezerPresetKey, basePos + new Vector3(16f, 0f, -12f));
            if (_underHoused == null) return;

            Interactable interactable = OwnInteraction(_underHoused, "Talk to the twitchy geezer");
            var under = _underHoused.AddComponent<UnderHousedNPC>();
            under.Talk = _underHousedTalk;
            under.Data = _underHousedData;
            interactable.OnInteract.AddListener(under.Interact);
        }

        /// <summary>
        /// Builds one of the quest's characters from its preset, the same way the World Palette
        /// builds every other NPC in the game.
        ///
        /// This used to compose the character here — one sprite, a fixed height, a hand-rolled
        /// capsule when the sprite was missing — which is how these two ended up outside the preset
        /// system while everything else moved into it, and how they ended up identical to each
        /// other. Nothing about how they look or behave lives in this file now.
        /// </summary>
        private GameObject BuildNpc(string presetKey, Vector3 pos)
        {
            PlacementPreset preset = PlacementPresetLibrary.Get(presetKey);
            if (preset == null) return null;   // Get already said which of the three things was wrong

            GameObject chunk = ChunkRoot();
            return NpcFactory.Build(preset, pos, chunk != null ? chunk.transform : null);
        }

        /// <summary>
        /// Takes over the Interactable <see cref="NpcFactory"/> already put on the NPC rather than
        /// adding a second one beside it. Both of these characters run their conversations off
        /// quest state, so the tutorial owns what pressing Interact does.
        /// </summary>
        private static Interactable OwnInteraction(GameObject npc, string prompt)
        {
            var interactable = npc.GetComponent<Interactable>();
            if (interactable == null) interactable = npc.AddComponent<Interactable>();

            interactable.Prompt = prompt;
            interactable.InteractRange = 3f;
            interactable.Reusable = true;

            // The factory adds this when a preset carries a Conversation — right for an ordinary
            // NPC, wrong for these two, where it would answer the same button press with a fixed
            // line while the quest script is trying to run a scene.
            if (npc.GetComponent<NPCDialogueInteractable>() != null)
            {
                Debug.LogWarning(
                    $"MagicTutorial: '{npc.name}' was built from a preset with a Conversation " +
                    "assigned. Clear it — this character's dialogue comes from quest state, and the " +
                    "preset's line will fire alongside it.", npc);
            }

            return interactable;
        }

        private GameObject ChunkRoot()
        {
            if (ChunkManager.Instance != null && ChunkManager.Instance.CurrentChunkInstance != null)
                return ChunkManager.Instance.CurrentChunkInstance;
            return transform.parent != null ? transform.parent.gameObject : null;
        }
    }

    /// <summary>Daniel Pauls' talk button — shows whichever conversation fits the quest beat.</summary>
    public class MagicMentorNPC : MonoBehaviour
    {
        public void Interact()
        {
            var t = MagicTutorial.Instance;
            if (t == null) return;
            var convo = t.MentorDialogueForStage();
            if (convo == null) return;
            var playerData = CombatController.Instance != null ? CombatController.Instance.PlayerData : null;
            DialogueManager.Ensure().StartDialogue(convo, playerData);
        }
    }

    /// <summary>Talk to the geezer, he panics and turns hostile (a low-HP lightning caster).</summary>
    public class UnderHousedNPC : MonoBehaviour
    {
        public DialogueData Talk;
        public CharacterData Data;

        private bool _hostile;
        private bool _talking;

        public void Interact()
        {
            if (_hostile || _talking || Talk == null) return;
            _talking = true;
            var playerData = CombatController.Instance != null ? CombatController.Instance.PlayerData : null;
            DialogueManager.Ensure().StartDialogue(Talk, playerData);
            StartCoroutine(WaitThenHostile());
        }

        private IEnumerator WaitThenHostile()
        {
            yield return null; // let the panel open
            while (DialogueManager.IsDialogueOpen) yield return null;
            _talking = false;
            TurnHostile();
        }

        private void TurnHostile()
        {
            if (_hostile) return;
            _hostile = true;

            var interactable = GetComponent<Interactable>();
            if (interactable != null) interactable.enabled = false;

            if (GetComponent<Collider>() == null)
            {
                var col = gameObject.AddComponent<CapsuleCollider>();
                col.height = EKVibe.CharacterHeight;
                col.radius = 0.4f;
                col.center = new Vector3(0f, EKVibe.CharacterHeight * 0.5f, 0f);
            }
            if (GetComponent<Rigidbody>() == null)
            {
                var rb = gameObject.AddComponent<Rigidbody>();
                rb.isKinematic = true;
            }

            var health = gameObject.AddComponent<Health>();
            health.MaxHealth = 40;
            health.CurrentHealth = 40;
            health.DisplayName = "Under Housed";
            health.DestroyOnDeath = true;
            health.OnDeath.AddListener(OnDied);

            gameObject.AddComponent<UnityEngine.AI.NavMeshAgent>();
            var ai = gameObject.AddComponent<EnemyAI>();
            ai.RangedCaster = true;
            ai.AttackRange = 7f;
            ai.SightRadius = 16f;
            ai.AttackCooldown = 1.6f;
            ai.Damage = 8;

            // EnemyAI's Animator is a public field nothing assigns unless asked, so without this the
            // geezer fights through his whole attack, hurt and death animations without playing any
            // of them — the art imports, the controller builds, and nothing moves.
            var visual = GetComponent<WorldActorVisual>();
            if (visual != null) ai.Animator = visual.SpriteAnimator;

            if (UIManager.Instance != null)
                UIManager.Instance.LogCombat("Under Housed panics — and throws a bolt!");
        }

        private void OnDied()
        {
            MagicTutorial.Instance?.OnUnderHousedDead();
        }
    }
}
