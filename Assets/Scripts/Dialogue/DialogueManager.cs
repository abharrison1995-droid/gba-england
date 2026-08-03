using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections.Generic;
using ExiledAlvaston.Data;
using ExiledAlvaston.Vibe;

namespace ExiledAlvaston.Dialogue
{
    /// <summary>
    /// Exiled Kingdoms style dialogue UI. If the scene doesn't wire up a panel, one is
    /// built in code at runtime on its own overlay canvas (like LootMenuUI), so NPCs work
    /// with zero scene setup. Ensure() guarantees an instance exists.
    /// </summary>
    public class DialogueManager : MonoBehaviour
    {
        public static DialogueManager Instance { get; private set; }

        [Header("UI References (optional — built at runtime if left empty)")]
        public GameObject DialoguePanel;
        public Image PortraitImage;
        public TextMeshProUGUI SpeakerNameText;
        public TextMeshProUGUI MainDialogueText;
        public Transform ChoicesContainer;
        public GameObject ChoiceButtonPrefab;

        private CharacterData _currentPlayerData; // To evaluate stat checks
        private bool _dialogueActive;
        private string _currentSpeakerName;       // whoever's talking = quest giver if they grant one
        private bool _teachSparkOnClose;          // set by a TeachSpark choice; fires when the chat ends
        private DialogueData _currentData;        // which conversation is running, to resolve NextNodeId against

        // Reused by CanEscapeFrom so the freeze check costs no garbage per button press (§4).
        private readonly HashSet<DialogueNode> _escapeVisited = new HashSet<DialogueNode>();
        private readonly Queue<DialogueNode> _escapeFrontier = new Queue<DialogueNode>();

        /// <summary>True while a conversation is on screen — quest popups defer until it ends.</summary>
        public static bool IsDialogueOpen => Instance != null && Instance._dialogueActive;

        /// <summary>Creates a DialogueManager if the scene has none.</summary>
        public static DialogueManager Ensure()
        {
            if (Instance == null)
            {
                var go = new GameObject("DialogueManager");
                DontDestroyOnLoad(go);
                go.AddComponent<DialogueManager>();
            }
            return Instance;
        }

        private void Awake()
        {
            if (Instance == null) Instance = this;
            else if (Instance != this) Destroy(gameObject);
        }

        private void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        public void StartDialogue(DialogueData data, CharacterData playerData)
        {
            if (_dialogueActive) return;
            if (data == null) return;
            DialogueNode start = data.StartNode();
            if (start == null) return;

            EnsureUI();

            _currentPlayerData = playerData;
            DialoguePanel.SetActive(true);

            _dialogueActive = true;
            ExiledAlvaston.Systems.PauseManager.Push();

            _currentData = data;
            DisplayNode(start);
        }

        private void DisplayNode(DialogueNode node)
        {
            if (node.Speaker != null)
            {
                _currentSpeakerName = node.Speaker.CharacterName;
                if (SpeakerNameText != null)
                    SpeakerNameText.text = node.Speaker.CharacterName;
                if (PortraitImage != null)
                {
                    PortraitImage.sprite = node.Speaker.Portrait;
                    PortraitImage.enabled = node.Speaker.Portrait != null;
                }
            }
            else
            {
                // These fields are never cleared otherwise, and the panel is reused between
                // conversations — so a speakerless node showed the name and face of whoever you
                // last spoke to, attributing an anonymous line to a named character.
                _currentSpeakerName = null;
                if (SpeakerNameText != null) SpeakerNameText.text = "";
                if (PortraitImage != null)
                {
                    PortraitImage.sprite = null;
                    PortraitImage.enabled = false;
                }
            }

            if (MainDialogueText != null)
                MainDialogueText.text = node.DialogueText;

            foreach (Transform child in ChoicesContainer)
                Destroy(child.gameObject);

            if (node.Choices == null || node.Choices.Count == 0)
            {
                CreateChoiceButton("End conversation.", null, true);
            }
            else
            {
                for (int i = 0; i < node.Choices.Count; i++)
                {
                    DialogueChoice choice = node.Choices[i];

                    string displayText = $"{i + 1}. {choice.ChoiceText}";

                    if (!string.IsNullOrEmpty(choice.RequiredStat))
                    {
                        string color = MeetsStatRequirement(choice) ? "green" : "red";
                        displayText = $"<color={color}>({choice.RequiredStat} {choice.RequiredStatLevel})</color> {displayText}";
                    }

                    if (choice.RequiredItem != null)
                    {
                        string color = MeetsItemRequirement(choice) ? "green" : "red";
                        string label = choice.RequiredItemQuantity > 1
                            ? $"{choice.RequiredItem.ItemName} x{choice.RequiredItemQuantity}"
                            : choice.RequiredItem.ItemName;
                        displayText = $"<color={color}>({label})</color> {displayText}";
                    }

                    CreateChoiceButton(displayText, choice.NextNodeId, IsSelectable(choice), choice);
                }

                // Safety net, not an authoring feature. A conversation can only end through a
                // choice, so a node the player cannot leave freezes the game outright: the panel
                // is modal and PauseManager is holding Time.timeScale at 0, EndDialogue is private
                // with no external caller, and there is no Escape handler or close button. Two
                // authored shapes reach that — a hub that loops back with no farewell (which this
                // format newly permits, see CLAUDE.md §15) and a node whose every choice is
                // gated shut, which has always been possible. Rather than change what a
                // well-authored conversation looks like, add an exit only when there is not one.
                if (!CanEscapeFrom(node))
                    CreateChoiceButton("End conversation.", null, true);
            }
        }

        // ---------- choice gating ----------
        // Split out so the buttons and CanEscapeFrom can never disagree about what is pressable:
        // an exit the guard counts on but the player cannot click would be worse than no guard.

        private bool MeetsStatRequirement(DialogueChoice choice)
        {
            if (string.IsNullOrEmpty(choice.RequiredStat)) return true;
            return _currentPlayerData != null && choice.MeetsRequirement(_currentPlayerData.BaseTraits);
        }

        private bool MeetsItemRequirement(DialogueChoice choice)
        {
            if (choice.RequiredItem == null) return true;
            return Flow.PlayerSession.Instance != null
                && Flow.PlayerSession.Instance.HasItem(choice.RequiredItem, choice.RequiredItemQuantity);
        }

        private bool IsSelectable(DialogueChoice choice)
            => MeetsStatRequirement(choice) && MeetsItemRequirement(choice);

        /// <summary>
        /// True if some run of *currently pressable* choices from <paramref name="node"/> reaches a
        /// point where the conversation ends — an empty NextNodeId, an id that resolves to nothing,
        /// or a node with no choices at all (which gets the automatic "End conversation." button).
        ///
        /// Gating is evaluated as it stands right now rather than structurally. Within a single
        /// conversation the player's position can only get worse — ConsumeRequiredItem takes items
        /// away and nothing hands any back — so a route that is shut now will still be shut when
        /// they arrive at it, and treating it as open would promise an exit that is not there.
        ///
        /// Runs once per DisplayNode, i.e. once per button press with the game already paused, over
        /// a conversation of tens of nodes. The two collections are reused rather than allocated per
        /// call, per §4.
        /// </summary>
        private bool CanEscapeFrom(DialogueNode node)
        {
            if (node == null) return true;   // nothing on screen to be trapped by
            if (_currentData == null) return false;

            _escapeVisited.Clear();
            _escapeFrontier.Clear();
            _escapeFrontier.Enqueue(node);

            while (_escapeFrontier.Count > 0)
            {
                DialogueNode current = _escapeFrontier.Dequeue();
                if (current == null) continue;

                // A node with no choices is an exit: DisplayNode gives it the automatic button.
                if (current.Choices == null || current.Choices.Count == 0) return true;

                for (int i = 0; i < current.Choices.Count; i++)
                {
                    DialogueChoice choice = current.Choices[i];
                    if (choice == null || !IsSelectable(choice)) continue;

                    // Both of these end the chat in OnChoiceSelected — the second one loudly.
                    if (string.IsNullOrEmpty(choice.NextNodeId)) return true;
                    DialogueNode next = _currentData.FindNode(choice.NextNodeId);
                    if (next == null) return true;

                    // Guard against revisiting by identity rather than by Id: a duplicate Id is an
                    // authoring error nothing validates (§15), and keying on it would let one node
                    // stand in for another and cut the search short.
                    if (_escapeVisited.Add(next))
                        _escapeFrontier.Enqueue(next);
                }
            }

            return false;
        }

        private void CreateChoiceButton(string text, string nextNodeId, bool selectable, DialogueChoice choice = null)
        {
            GameObject btnObj;
            if (ChoiceButtonPrefab != null)
            {
                btnObj = Instantiate(ChoiceButtonPrefab, ChoicesContainer);
            }
            else
            {
                btnObj = BuildRuntimeChoiceButton();
            }

            TextMeshProUGUI btnText = btnObj.GetComponentInChildren<TextMeshProUGUI>();
            if (btnText != null) btnText.text = text;

            Button btn = btnObj.GetComponent<Button>();
            btn.interactable = selectable;
            btn.onClick.AddListener(() => OnChoiceSelected(nextNodeId, choice));
        }

        private void OnChoiceSelected(string nextNodeId, DialogueChoice choice)
        {
            // Quest grants fire on pick; the popup itself waits for the chat to close
            if (choice != null && !string.IsNullOrEmpty(choice.GrantQuestId)
                && Quests.QuestManager.Instance != null)
            {
                Quests.QuestManager.Instance.StartQuest(
                    choice.GrantQuestId,
                    string.IsNullOrEmpty(choice.GrantQuestTitle) ? choice.GrantQuestId : choice.GrantQuestTitle,
                    choice.GrantQuestObjective,
                    giver: _currentSpeakerName,
                    location: choice.GrantQuestLocation);
            }

            if (choice != null && !string.IsNullOrEmpty(choice.CompleteQuestId)
                && Quests.QuestManager.Instance != null)
            {
                Quests.QuestManager.Instance.CompleteQuest(choice.CompleteQuestId);
            }

            // Handing something over — only reached if the choice was selectable, i.e. already had enough.
            if (choice != null && choice.RequiredItem != null && choice.ConsumeRequiredItem
                && Flow.PlayerSession.Instance != null)
            {
                Flow.PlayerSession.Instance.RemoveItem(choice.RequiredItem, choice.RequiredItemQuantity);
            }

            // Teaching + naming waits for the chat to close so the popup isn't buried behind it.
            if (choice != null && choice.TeachSpark)
                _teachSparkOnClose = true;

            if (string.IsNullOrEmpty(nextNodeId))
            {
                EndDialogue();
                return;
            }
            DialogueNode next = _currentData != null ? _currentData.FindNode(nextNodeId) : null;
            if (next == null)
            {
                Debug.LogWarning($"DialogueManager: a choice points at node id '{nextNodeId}', which does not exist in the current conversation. Ending the chat.", _currentData);
                EndDialogue();
                return;
            }
            DisplayNode(next);
        }

        private void EndDialogue()
        {
            DialoguePanel.SetActive(false);
            if (_dialogueActive)
            {
                _dialogueActive = false;
                ExiledAlvaston.Systems.PauseManager.Pop();
            }
            _currentData = null;
            UI.QuestPopupUI.ShowPendingIfAny();

            if (_teachSparkOnClose)
            {
                _teachSparkOnClose = false;
                if (Combat.CombatController.Instance != null)
                    Combat.CombatController.Instance.LearnSpark();
                UI.SpellNamingUI.Show();
            }
        }

        // ---------- runtime-built UI (used when nothing is wired in the scene) ----------

        private void EnsureUI()
        {
            if (DialoguePanel != null && MainDialogueText != null && ChoicesContainer != null)
                return;

            var canvasGO = new GameObject("DialogueCanvas");
            canvasGO.transform.SetParent(transform, false);
            var canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 450;
            var scaler = canvasGO.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
            canvasGO.AddComponent<GraphicRaycaster>();

            // Bottom-anchored parchment panel, EK style
            GameObject panel = CreateImage("DialoguePanel", canvasGO.transform, EKVibe.ParchmentPanel);
            var prt = panel.GetComponent<RectTransform>();
            prt.anchorMin = new Vector2(0.5f, 0f);
            prt.anchorMax = new Vector2(0.5f, 0f);
            prt.pivot = new Vector2(0.5f, 0f);
            prt.anchoredPosition = new Vector2(0, 20);
            prt.sizeDelta = new Vector2(1100, 400);

            // Portrait box, top-left
            GameObject portraitFrame = CreateImage("PortraitFrame", panel.transform, EKVibe.ParchmentDark);
            var pfrt = portraitFrame.GetComponent<RectTransform>();
            pfrt.anchorMin = pfrt.anchorMax = new Vector2(0f, 1f);
            pfrt.pivot = new Vector2(0f, 1f);
            pfrt.anchoredPosition = new Vector2(16, -16);
            pfrt.sizeDelta = new Vector2(110, 110);

            GameObject portrait = CreateImage("Portrait", portraitFrame.transform, Color.white);
            var port = portrait.GetComponent<RectTransform>();
            port.anchorMin = Vector2.zero;
            port.anchorMax = Vector2.one;
            port.offsetMin = new Vector2(6, 6);
            port.offsetMax = new Vector2(-6, -6);
            PortraitImage = portrait.GetComponent<Image>();
            PortraitImage.enabled = false;

            SpeakerNameText = CreateTMP("SpeakerName", panel.transform, "", EKVibe.TextDark, 28,
                TextAlignmentOptions.TopLeft, FontStyles.Bold);
            var snrt = SpeakerNameText.GetComponent<RectTransform>();
            snrt.anchorMin = new Vector2(0f, 1f);
            snrt.anchorMax = new Vector2(1f, 1f);
            snrt.pivot = new Vector2(0f, 1f);
            snrt.anchoredPosition = new Vector2(142, -20);
            snrt.sizeDelta = new Vector2(-160, 36);

            MainDialogueText = CreateTMP("DialogueText", panel.transform, "", EKVibe.TextDark, 22,
                TextAlignmentOptions.TopLeft, FontStyles.Normal);
            var mrt = MainDialogueText.GetComponent<RectTransform>();
            mrt.anchorMin = new Vector2(0f, 1f);
            mrt.anchorMax = new Vector2(1f, 1f);
            mrt.pivot = new Vector2(0f, 1f);
            mrt.anchoredPosition = new Vector2(142, -60);
            mrt.sizeDelta = new Vector2(-160, 120);

            var choicesGO = new GameObject("Choices", typeof(RectTransform));
            choicesGO.transform.SetParent(panel.transform, false);
            var crt = choicesGO.GetComponent<RectTransform>();
            crt.anchorMin = new Vector2(0f, 0f);
            crt.anchorMax = new Vector2(1f, 1f);
            crt.offsetMin = new Vector2(24, 16);
            crt.offsetMax = new Vector2(-24, -190);
            var layout = choicesGO.AddComponent<VerticalLayoutGroup>();
            layout.spacing = 8;
            layout.childControlWidth = true;
            layout.childControlHeight = false;
            layout.childForceExpandHeight = false;
            layout.childAlignment = TextAnchor.LowerCenter;
            ChoicesContainer = choicesGO.transform;

            DialoguePanel = panel;
            DialoguePanel.SetActive(false);
        }

        private GameObject BuildRuntimeChoiceButton()
        {
            GameObject go = CreateImage("ChoiceButton", ChoicesContainer, EKVibe.ButtonBrown);
            go.GetComponent<RectTransform>().sizeDelta = new Vector2(0, 46);
            go.AddComponent<Button>();

            var tmp = CreateTMP("Label", go.transform, "", EKVibe.TextLight, 20,
                TextAlignmentOptions.Left, FontStyles.Normal);
            var trt = tmp.GetComponent<RectTransform>();
            trt.anchorMin = Vector2.zero;
            trt.anchorMax = Vector2.one;
            trt.offsetMin = new Vector2(16, 0);
            trt.offsetMax = new Vector2(-16, 0);
            return go;
        }

        private static GameObject CreateImage(string name, Transform parent, Color color)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.color = color;
            return go;
        }

        private static TextMeshProUGUI CreateTMP(string name, Transform parent, string text,
            Color color, float size, TextAlignmentOptions align, FontStyles style)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var tmp = go.AddComponent<TextMeshProUGUI>();
            tmp.text = text;
            tmp.color = color;
            tmp.fontSize = size;
            tmp.alignment = align;
            tmp.fontStyle = style;
            tmp.raycastTarget = false;
            return tmp;
        }
    }
}
