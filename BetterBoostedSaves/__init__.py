from typing import Any
from random import choice

from mods_base import hook, build_mod, BoolOption
from unrealsdk import find_object, construct_object, make_struct, find_all, find_class
from unrealsdk.hooks import Type, Block, prevent_hooking_direct_calls
from unrealsdk.unreal import UObject, WeakPointer, WrappedStruct, BoundFunction
from ui_utils import OptionBox, OptionBoxButton

current_lobby = WeakPointer()
selected_item = None

original_saves = {
    "Zero30": 'GD_Level30Character.Assassin.Profile_Assassin30',
    "Gaige30":'GD_Level30Character.Mechromancer.Profile_Mechromancer30',
    "Salvador30":'GD_Level30Character.Mercenary.Profile_Mercenary30',
    "Krieg30":'GD_Level30Character.Psycho.Profile_Psycho30',
    "Maya30":'GD_Level30Character.Siren.Profile_Siren30',
    "Axton30":'GD_Level30Character.Soldier.Profile_Soldier30',
}

M_Ep1_Champion = make_struct("MissionStatusPlayerData",
                    MissionDef = find_object('MissionDefinition','GD_Episode01.M_Ep1_Champion'),
                    Status = 4,
                    ObjectivesProgress = [1],
                    ActiveObjectiveSet = find_object('MissionObjectiveSetDefinition', 'GD_Episode01.M_Ep1_Champion:OpenLockerSet'),
                    GameStage = 50,
                    bHeardKickoff = True
                )
M_Ep2_Henchman = make_struct("MissionStatusPlayerData",
                    MissionDef = find_object('MissionDefinition','GD_Episode02.M_Ep2_Henchman'),
                    Status = 4,
                    ObjectivesProgress = [1, 1, 1, 1, 1, 1, 0, 1, 1],
                    ActiveObjectiveSet = find_object('MissionObjectiveSetDefinition', 'GD_Episode02.M_Ep2_Henchman:WeaponEquippedSet'),
                    GameStage = 50,
                    bHeardKickoff = True
                )
M_Ep2a_MoreGuns = make_struct("MissionStatusPlayerData",
                    MissionDef = find_object('MissionDefinition','GD_Episode02.M_Ep2a_MoreGuns'),
                    Status = 1,
                    ObjectivesProgress = [0, 0, 0, 0, 0, 0, 0],
                    ActiveObjectiveSet = find_object('MissionObjectiveSetDefinition', 'GD_Episode02.M_Ep2a_MoreGuns:ReachKoldstoneSet1'),
                    GameStage = 50,
                    bHeardKickoff = True
                )

UVHM_missions = [M_Ep1_Champion, M_Ep2_Henchman, M_Ep2a_MoreGuns]

def create_boosted_char(pc:UObject, character:str, level:int):
    original_save_game = find_object('PlayerSaveGame', original_saves[character])
    new_save_game = construct_object('PlayerSaveGame', original_save_game, template_obj=original_save_game)

    new_save_game.ExpLevel = level
    new_save_game.PlaythroughsCompleted = 1 if level == 32 else 2

    for item in new_save_game.ItemData:
        item.DefinitionData.ManufacturerGradeIndex = level
        item.DefinitionData.GameStage = level

    for weapon in new_save_game.WeaponData:
        weapon.WeaponDefinitionData.ManufacturerGradeIndex = level
        weapon.WeaponDefinitionData.GameStage = level

    kill_jack = new_save_game.MissionPlaythroughs[0].MissionData[-1]
    kill_jack.Status = 4
    kill_jack.ObjectivesProgress = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0]
    kill_jack.ActiveObjectiveSet =  find_object('MissionObjectiveSetDefinition','GD_Episode17.M_Ep17_KillJack:GetTheArtifactSet')
    
    if level >= 50:
        new_save_game.LastVisitedTeleporter = "WaterfrontToGlacial"
        
        new_save_game.MissionPlaythroughs[1] = new_save_game.MissionPlaythroughs[0]
        new_save_game.MissionPlaythroughs[1].PlayThroughNumber = 1

        new_save_game.MissionPlaythroughs[2].MissionData = UVHM_missions

    if level == 50:
        new_save_game.BlackMarketUpgrades = (4, 4, 4, 4, 4, 4, 4, 5, 5)
        new_save_game.CurrencyOnHand = (3000000, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    elif level == 80:
        new_save_game.BlackMarketUpgrades = (7, 7, 7, 7, 7, 7, 7, 9, 9)
        new_save_game.CurrencyOnHand = (15000000, 500, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)


    pc.GetWillowGlobals().GetWillowSaveGameManager().SetCachedPlayerSaveGame(0, new_save_game)
    pc.LoadCachedSaveGame()


def boosted_box_selection(box, selection):
    if not current_lobby():
        return

    lobby = current_lobby()
    pc = lobby.WPCOwner

    if selection == ffs_level_30:
        pc.LoadGame("default " + selected_item.CharName, None, True, False, 0)
        pc.ClearCustomizations()
        lobby.LaunchBoostedSave()
        BetterBoost_CreateWeaponScopeMovie.enable()

    elif selection == level_32:
        create_boosted_char(pc, selected_item.CharName, 32)
        pc.ClearCustomizations()

        dlg = construct_object("WillowGFxDialogBox", pc)
        dlg.DialogResult = 'Dif2'
        find_all("FrontendGFxMovie")[-1].OnChoosePlaythrough_Click(dlg, 0)
        pc.openlArg("Glacial_P")
        BetterBoost_CreateWeaponScopeMovie.enable()

    elif selection == level_50:
        create_boosted_char(pc, selected_item.CharName, 50)
        pc.ClearCustomizations()

        dlg = construct_object("WillowGFxDialogBox", pc)
        dlg.DialogResult = 'Dif3'
        find_all("FrontendGFxMovie")[-1].OnChoosePlaythrough_Click(dlg, 0)
        pc.openlArg("SouthernShelf_P")
        BetterBoost_CreateWeaponScopeMovie.enable()

    elif selection == level_80:
        create_boosted_char(pc, selected_item.CharName, 80)
        pc.ClearCustomizations()

        dlg = construct_object("WillowGFxDialogBox", pc)
        dlg.DialogResult = 'Dif3'
        find_all("FrontendGFxMovie")[-1].OnChoosePlaythrough_Click(dlg, 0)
        pc.openlArg("SouthernShelf_P")
        BetterBoost_CreateWeaponScopeMovie.enable()

    


ffs_level_30 = OptionBoxButton(
    "Vanilla Level 30 Start",
    "Normal FFS Level 30 Start"
)

level_32 = OptionBoxButton(
    "TVHM Level 32 Start",
    "Starts the character at level 32 at the beginning of TVHM."
)

level_50 = OptionBoxButton(
    "UVHM Level 50 Start",
    "Starts the character at level 50 at the beginning of UVHM."
)

level_80 = OptionBoxButton(
    "UVHM Level 80 Start",
    "Starts the character at level 80 at the beginning of UVHM."
)

boosted_box = OptionBox(
    title="Start Boosted Character",
    message="Choose which kind of character to start",
    buttons=[ffs_level_30, level_32, level_50, level_80],
    on_select=boosted_box_selection
)

@hook("WillowGame.WillowGFxLobbyLoadCharacter:OnSlotClicked", Type.PRE)
def BetterBoost_OnSlotClicked(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    SelectedIndex = args.SlotIndex + obj.TopSlotDataIndex
    SelectedItem = obj.DisplayedCharacterDataList[SelectedIndex]
    if SelectedItem.SaveDataID == -1 and SelectedItem.CharLevel == 30:
        global current_lobby,selected_item
        current_lobby = WeakPointer(obj)
        selected_item = SelectedItem
        boosted_box.show()
        return Block

@hook("WillowGame.LoadCharacterLobbyGFxObject:SetSlotData", Type.PRE)
def BetterBoost_SetSlotData(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    char_name = str(args.CharName)
    if "Create New Level 30" in char_name:
        with prevent_hooking_direct_calls():
            args.CharName = char_name.replace("Level 30", "Boosted")
            func(args)
            return Block

oidRandomizeGear = BoolOption(
    "Randomize Gear",
    False,
    "On",
    "Off",
    description="Removes the normal boosted gear and gives you random gear instead."
)

item_pool_default = find_class('ItemPool').ClassDefaultObject
def spawn_item(pool_def:UObject,pawn:UObject) -> UObject:
    _, new_items = item_pool_default.SpawnBalancedInventoryFromPool(
                    pool_def, pawn.GetGameStage(), 0, pawn, []
                    )
    return new_items[0]


@hook("WillowGame.WillowHUD:CreateWeaponScopeMovie", Type.POST)
def BetterBoost_CreateWeaponScopeMovie(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    if oidRandomizeGear.value:
        pawn = obj.WPlayerOwner.Pawn
        
        guns_Launchers = find_object('ItemPoolDefinition','GD_Itempools.Treasure_ChestPools.Pool_EpicChest_Weapons_Launchers')
        guns_Long = find_object('ItemPoolDefinition','GD_Itempools.Treasure_ChestPools.Pool_EpicChest_Weapons_LongGuns')
        guns_Pistols = find_object('ItemPoolDefinition','GD_Itempools.Treasure_ChestPools.Pool_EpicChest_Weapons_Pistols')
        Artifacts = find_object('ItemPoolDefinition', 'GD_Itempools.Treasure_ChestPools.Pool_EpicChest_Artifacts')
        ClassMods = find_object('ItemPoolDefinition', 'GD_Itempools.Treasure_ChestPools.Pool_EpicChest_ClassMods')
        GrenadeMods = find_object('ItemPoolDefinition', 'GD_Itempools.Treasure_ChestPools.Pool_EpicChest_GrenadeMods')
        Shields = find_object('ItemPoolDefinition', 'GD_Itempools.Treasure_ChestPools.Pool_EpicChest_Shields')

        pawn.InvManager.DiscardInventory(True)

        for i in range(5):
            com = spawn_item(ClassMods, pawn)
            pawn.InvManager.AddInventory(com, True)

            artifact = spawn_item(Artifacts, pawn)
            pawn.InvManager.AddInventory(artifact, True)

            grenade = spawn_item(GrenadeMods, pawn)
            pawn.InvManager.AddInventory(grenade, True)

            shield = spawn_item(Shields, pawn)
            pawn.InvManager.AddInventory(shield, True)

        for i in range(8):
            weapon = spawn_item(choice([guns_Long, guns_Pistols]), pawn)
            pawn.InvManager.AddInventory(weapon, True)

        for i in range(2):
            weapon = spawn_item(guns_Launchers, pawn)
            pawn.InvManager.AddInventory(weapon, False)

    BetterBoost_CreateWeaponScopeMovie.disable()


@hook("WillowGame.StatusMenuExGFxMovie:DisplayMarketingUnlockDialogIfNecessary", Type.PRE)
def BetterBoost_DisplayMarketingUnlockDialogIfNecessary(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    return Block
        
build_mod(hooks=[BetterBoost_OnSlotClicked, BetterBoost_SetSlotData, BetterBoost_DisplayMarketingUnlockDialogIfNecessary])