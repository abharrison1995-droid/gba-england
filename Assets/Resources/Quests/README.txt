Drop QuestDefinition assets (Create > ExiledAlvaston > Data > Quest Definition) anywhere under
this folder. QuestDatabase finds them by Id automatically at runtime (Resources.LoadAll) — no
registration step needed.

The Id must match the DialogueChoice.GrantQuestId that starts the quest. Nothing here starts a
quest; a definition only describes one that dialogue already started, so an Id that matches
nothing is simply never used and nothing reports it.

A quest with no definition in here is completely untouched by QuestConditionWatcher — no stages,
no rewards, no interference. That is deliberate: escape_manor runs off TutorialSequence's own code
and must not get a definition.

spark_of_talent used to be the second such quest. It is now authored in
quests/spark_of_talent.quest and its definition is GENERATED into this folder by
Tools > Content > Import Quests — do not hand-edit it, the .quest file owns it and a re-import
overwrites whatever is here.

Everything reachable from a Resources folder ships in the build. Never reference a GameObject,
Sprite, Prefab or AudioClip from a QuestDefinition — one prefab reference drags its whole
dependency graph into the build. ItemData is already Resources-resident and is the only asset
reference a definition may hold.
