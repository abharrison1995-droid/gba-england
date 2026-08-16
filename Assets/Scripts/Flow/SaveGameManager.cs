using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using GBHEngland.Combat;
using GBHEngland.Data;
using GBHEngland.World;
using GBHEngland.Quests;
using GBHEngland.Companions;

namespace GBHEngland.Flow
{
    /// <summary>One saved inventory stack — an item id (resolved via ItemDatabase) plus a quantity.</summary>
    [Serializable]
    public class InventorySaveEntry
    {
        public string ItemID;
        public int Quantity;
    }

    /// <summary>One saved equipment slot — the slot as an ItemType index plus the worn item's id.</summary>
    [Serializable]
    public class EquipSaveEntry
    {
        public int Slot;
        public string ItemID;
    }

    /// <summary>Everything a checkpoint needs to survive an app restart.</summary>
    [Serializable]
    public class SaveData
    {
        public string CharacterName;
        public int PlayerClass;
        public bool TutorialComplete;

        public string ChunkName;
        public float PosX, PosY, PosZ;
        public int Health;
        public int Mana;
        public int Stamina;

        public List<QuestProgress> Quests = new List<QuestProgress>();
        public List<InventorySaveEntry> Inventory = new List<InventorySaveEntry>();

        /// <summary>Worn gear, appended after Inventory. Absent in pre-equipment saves — restores treat null as empty.</summary>
        public List<EquipSaveEntry> Equipment = new List<EquipSaveEntry>();

        // Appended, per the rule in SAVE_AND_SERIALIZATION.md: a save written before the wallet
        // existed has no Pounds key at all, and JsonUtility reads it back as 0 — which is the
        // correct starting balance, so no migration is needed.
        public int Pounds;

        // Appended for the same reason and read back the same way: an older save has no
        // LootedContainers key and JsonUtility hands back an empty list, which correctly means
        // "nothing has been looted yet". Ids are "<ChunkName>/<GameObjectName>" and are compared
        // as plain strings — see SAVE_AND_SERIALIZATION.md before touching how they are built.
        //
        // A public FIELD, not a property: JsonUtility only serializes fields, and a property here
        // would silently never persist.
        public List<string> LootedContainers = new List<string>();

        // Appended for the Map of Britain, same append-only rule as the fields above: a pre-map
        // save has no VisitedChunks key, JsonUtility hands back an empty list, and the map simply
        // shows nothing discovered yet — no migration needed. Entries are ChunkName values,
        // compared verbatim.
        public List<string> VisitedChunks = new List<string>();

        // Appended for WIKIBRITAIN: EntryIDs of unlocked encyclopedia entries, same append-only
        // rule — a pre-wiki save reads back empty. EntryIDs are save keys: never rename one.
        public List<string> UnlockedWikiEntries = new List<string>();

        // Appended for progression, same append-only rule: a pre-progression save has no TotalXP
        // key, JsonUtility reads it back as 0, and 0 XP derives to level 1 — the correct starting
        // level, so no migration is needed. Nothing may be inserted above this line.
        //
        // ⚠ The field name IS the JSON key. JsonUtility knows nothing of [FormerlySerializedAs],
        // so renaming this silently reverts every existing player to level 1. Never rename it.
        //
        // The LEVEL is deliberately not stored — it is derived from this total on every read, so
        // the curve in EKVibe can be retuned without touching a single save file.
        public int TotalXP;

        // Appended for perks, same append-only rule again: a save written before perks existed has
        // no PerkIds key, JsonUtility hands back an empty list, and no perks are taken — correct
        // for a pre-perk save, so no migration is needed. Nothing may be inserted above this line.
        //
        // ⚠ Entries are PerkData.PerkId values and are SAVE KEYS, compared verbatim and resolved
        // through PerkDatabase. Changing a shipped PerkId orphans that perk silently. And as with
        // TotalXP, the field name IS the JSON key — JsonUtility knows nothing of
        // [FormerlySerializedAs], so renaming this un-spends every perk every player has taken.
        public List<string> PerkIds = new List<string>();

        // Appended for the quest focus, same append-only rule as every field above: a save
        // written before the focus existed has no FocusedQuestId key, JsonUtility reads it back
        // as null, and QuestManager.RestoreFocusedQuest clears a null focus — so the tracker
        // falls back to the first active quest, exactly the pre-focus behaviour. No migration.
        public string FocusedQuestId;

        // Appended for the companion contract, same append-only rule as every field above: a save
        // written before companions existed has no ActiveCompanionId key, JsonUtility reads it back
        // as null, and CompanionManager.RestoreContract ignores a null/empty id — so an old save
        // simply loads with no companion, exactly the pre-companion behaviour. No migration.
        // ActiveCompanionId holds the CompanionDefinition.Id, which is a save key — never rename one.
        public string ActiveCompanionId;
        // The follower's health at save time; 0 or negative reads as "no companion" on restore.
        public int CompanionHealth;

        // Appended for the spellbook. AbilityID values are stable save keys resolved through
        // Resources/Abilities; the equipped list preserves its four positions with empty strings.
        // Pre-spellbook saves read both lists as empty, which correctly means no learned spells.
        public List<string> KnownSpellIds = new List<string>();
        public List<string> EquippedSpellIds = new List<string>();

        // The player-authored shout belongs to Spark. Old saves read null and restore the existing
        // "Spark Out" default through PlayerSession.SanitizeSpellName.
        public string SpellName;
    }

    /// <summary>
    /// Checkpoint save/load as JSON in persistentDataPath — auto-saves on every chunk
    /// transition. Session/quest restore is orchestrated by GameFlowController.ContinueFromSave;
    /// this class owns the file plus the world/player part of loading.
    /// </summary>
    public static class SaveGameManager
    {
        private static string SavePath => Path.Combine(Application.persistentDataPath, "savegame.json");

        public static bool HasSave => File.Exists(SavePath);

        public static void Save()
        {
            ChunkManager chunkMgr = ChunkManager.Instance;
            CombatController player = CombatController.Instance;
            if (chunkMgr == null || player == null || chunkMgr.CurrentChunkData == null) return;

            var data = new SaveData();

            PlayerSession session = PlayerSession.Instance;
            data.CharacterName = session != null ? session.CharacterName : "Vince";
            data.PlayerClass = session != null ? (int)session.Class : 0;
            data.TutorialComplete = session != null && session.TutorialComplete;
            data.Pounds = session != null ? session.Pounds : 0;
            data.TotalXP = session != null ? session.TotalXP : 0;
            data.SpellName = session != null ? session.SpellName : PlayerSession.DefaultSpellName;

            Vector3 pos = player.transform.position;
            data.ChunkName = chunkMgr.CurrentChunkData.ChunkName;
            data.PosX = pos.x;
            data.PosY = pos.y;
            data.PosZ = pos.z;
            data.Health = player.CurrentHealth;
            data.Mana = player.CurrentMana;
            data.Stamina = player.CurrentStamina;

            if (QuestManager.Instance != null)
            {
                data.Quests.AddRange(QuestManager.Instance.Quests);
                data.FocusedQuestId = QuestManager.Instance.FocusedQuestId;
            }

            // Companion contract, if one is active. CurrentCompanionId is null/empty and
            // CurrentFollowerHealth() is -1 when nobody is hired, which the restore path reads as
            // "no companion" — identical to a pre-companion save.
            if (CompanionManager.Instance != null)
            {
                data.ActiveCompanionId = CompanionManager.Instance.CurrentCompanionId;
                data.CompanionHealth = CompanionManager.Instance.CurrentFollowerHealth();
            }

            foreach (AbilityData ability in player.KnownSpells)
            {
                if (ability == null || string.IsNullOrWhiteSpace(ability.AbilityID)) continue;
                if (!data.KnownSpellIds.Contains(ability.AbilityID))
                    data.KnownSpellIds.Add(ability.AbilityID);
            }
            for (int i = 0; i < CombatController.SpellSlots; i++)
            {
                AbilityData equipped = player.EquippedAbilities != null && i < player.EquippedAbilities.Count
                    ? player.EquippedAbilities[i]
                    : null;
                data.EquippedSpellIds.Add(equipped != null ? equipped.AbilityID : "");
            }

            if (session != null)
            {
                foreach (InventoryStack stack in session.Inventory)
                {
                    if (stack?.Item == null || stack.Quantity <= 0) continue;
                    data.Inventory.Add(new InventorySaveEntry { ItemID = stack.Item.ItemID, Quantity = stack.Quantity });
                }

                foreach (var pair in session.Equipment)
                {
                    if (pair.Value == null) continue;
                    data.Equipment.Add(new EquipSaveEntry { Slot = (int)pair.Key, ItemID = pair.Value.ItemID });
                }

                data.LootedContainers.AddRange(session.LootedContainers);
                data.VisitedChunks.AddRange(session.VisitedChunks);
                data.UnlockedWikiEntries.AddRange(session.UnlockedWikiEntries);
                data.PerkIds.AddRange(session.SpentPerkIds);
            }

            try
            {
                File.WriteAllText(SavePath, JsonUtility.ToJson(data));
            }
            catch (Exception e)
            {
                Debug.LogWarning($"SaveGameManager: failed to write save — {e.Message}");
            }
        }

        /// <summary>Parses the save file; null if missing or corrupt.</summary>
        public static SaveData ReadSaveData()
        {
            if (!HasSave) return null;
            try
            {
                var data = JsonUtility.FromJson<SaveData>(File.ReadAllText(SavePath));
                // Legacy save-key migration: the hub chunk was renamed Home_Alvaston -> Home_London.
                if (data != null && data.ChunkName == "Home_Alvaston")
                    data.ChunkName = "Home_London";
                return data != null && !string.IsNullOrEmpty(data.ChunkName) ? data : null;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"SaveGameManager: unreadable save — {e.Message}");
                return null;
            }
        }

        /// <summary>
        /// Restores the world/player part of a checkpoint into the current scene: chunk, position,
        /// health/mana/stamina. Session and quests are restored by GameFlowController.ContinueFromSave.
        /// </summary>
        public static bool Load()
        {
            SaveData data = ReadSaveData();
            if (data == null) return false;
            return LoadWorld(data);
        }

        public static bool LoadWorld(SaveData data)
        {
            if (data == null) return false;

            ChunkManager chunkMgr = ChunkManager.Instance;
            CombatController player = CombatController.Instance;
            if (chunkMgr == null || player == null) return false;

            Data.MapChunkData chunk = chunkMgr.FindChunkByName(data.ChunkName);
            if (chunk == null || chunk.ChunkPrefab == null) return false;

            if (chunkMgr.CurrentChunkInstance != null)
                UnityEngine.Object.Destroy(chunkMgr.CurrentChunkInstance);

            chunkMgr.CurrentChunkData = chunk;
            PlayerSession.Instance?.MarkChunkVisited(chunk.ChunkName);
            // Silent: loading a save must not pop a toast for the chunk it lands in.
            UI.WikiUnlock.GrantForChunk(chunk.ChunkName, silent: true);
            GameObject instance = UnityEngine.Object.Instantiate(chunk.ChunkPrefab, Vector3.zero, Quaternion.identity);
            instance.name = chunk.ChunkPrefab.name;
            chunkMgr.CurrentChunkInstance = instance;

            chunkMgr.TeleportPlayer(new Vector3(data.PosX, data.PosY, data.PosZ));

            player.ReviveFull();
            Health health = player.GetComponent<Health>();
            int savedHealth = Mathf.Max(1, data.Health);
            if (health != null)
            {
                health.Revive(savedHealth);
                player.CurrentHealth = health.CurrentHealth;
            }
            player.CurrentMana = data.Mana;
            player.CurrentStamina = data.Stamina;

            return true;
        }

        public static void ClearSave()
        {
            try
            {
                if (File.Exists(SavePath))
                    File.Delete(SavePath);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"SaveGameManager: failed to delete save — {e.Message}");
            }
        }
    }
}
