from unrealsdk import make_struct, find_object, construct_object, find_all, find_class#type:ignore
from unrealsdk.hooks import Type, Block, prevent_hooking_direct_calls #type:ignore
from unrealsdk.unreal import WeakPointer#type:ignore
from mods_base import get_pc, hook, build_mod,build_mod
from ui_utils import  OptionBox, OptionBoxButton

from .structs import pt_data, resource_data,new_gladiator,new_enforcer,new_lawbringer,new_fragtrap,new_doppelganger,new_baroness, weapon_data,get_item_data

selected_boosted_character:str = ""

frontend_movie = WeakPointer()

characters = {
    "Boosted Athena": 'GD_DefaultProfiles.Gladiator.Profile_Gladiator',
    "Boosted Wilhelm": 'GD_DefaultProfiles.Enforcer.Profile_Enforcer',
    "Boosted Nisha": 'GD_DefaultProfiles.Lawbringer.Profile_Lawbringer',
    "Boosted Claptrap": 'GD_DefaultProfiles.Prototype.Profile_Prototype',
    "Boosted Jack": 'GD_QuincePackageDef.Profiles.Profile_Doppelganger',
    "Boosted Aurelia": 'GD_CrocusPackageDef.Profiles.Profile_Baroness',
}

def load_character(box, selected_button):
    if selected_button.name == "Cancel":
        return
    
    original_save_game = find_object('PlayerSaveGame', characters[selected_boosted_character])
    new_save_game = construct_object('PlayerSaveGame', original_save_game, template_obj=original_save_game)

    new_save_game.ExpLevel = 28
    new_save_game.ExpPoints = 676325
    new_save_game.GeneralSkillPoints = 26
    new_save_game.MissionPlaythroughs[0] = pt_data
    new_save_game.ResourceData = resource_data
    new_save_game.WeaponData = weapon_data
    new_save_game.ItemData = get_item_data() #dlc classmods make me cry
    new_save_game.PlaythroughsCompleted = 1
    new_save_game.CurrencyOnHand = (350000,120,0,0,0,0,0,0,0,0,0,0,0)
    new_save_game.BlackMarketUpgrades = (2,2,2,2,2,2,2,3,2,2)
    new_save_game.InventorySlotData=make_struct("InventorySlotSaveGameData",InventorySlotMax_Misc=21,WeaponReadyMax=4,NumQuickSlotsFlourished=2)
    new_save_game.UIPreferences.CharacterName = selected_boosted_character

    get_pc().GetWillowGlobals().GetWillowSaveGameManager().SetCachedPlayerSaveGame(0, new_save_game)
    get_pc().LoadCachedSaveGame()

    frontend = frontend_movie()
    dlg = construct_object("WillowGFxDialogBox", get_pc())
    dlg.DialogResult = 'Dif2'
    frontend.OnChoosePlaythrough_Click(dlg, 0)#type:ignore

    ApplyInventorySaveGameData.enable()
    ApplyItemSaveGameData.enable()
    get_pc().openlArg("MoonShotIntro_P")
    return

def spawn_chests():
    definition = find_object('InteractiveObjectDefinition','GD_Balance_Treasure.InteractiveObjects.InteractiveObj_HyperionChest')
    loot_data = find_object('InteractiveObjectLootListDefinition', 'GD_Itempools.ListDefs.EpicChestHyperionLoot')
    loot_data = [item for item in loot_data.LootData]
    new_chest = get_pc().Spawn(find_class("WillowInteractiveObject"))
    new_chest.InteractiveObjectDefinition = definition
    new_chest.BalanceDefinitionState.BalanceDefinition = find_object('InteractiveObjectBalanceDefinition','GD_Balance_Treasure.ChestGrades.ObjectGrade_HyperionChest')
    new_chest.Loot = loot_data
    new_chest.GameStage = 28
    new_chest.Location = make_struct("Vector",X=-8275, Y=49188, Z= 300)
    new_chest.Rotation.Yaw = 16500 
    new_chest.PostBeginPlay()

    new_chest2 = get_pc().Spawn(find_class("WillowInteractiveObject"))
    new_chest2.InteractiveObjectDefinition = definition
    new_chest2.BalanceDefinitionState.BalanceDefinition = find_object('InteractiveObjectBalanceDefinition','GD_Balance_Treasure.ChestGrades.ObjectGrade_HyperionChest')
    new_chest2.BalanceDefinitionState.bGradeCustomizationsApplied = True
    new_chest2.Loot = loot_data
    new_chest2.GameStage = 28
    new_chest2.Location = make_struct("Vector",X=-9200, Y=49191, Z=300)
    new_chest2.Rotation.Yaw = 16500 
    new_chest2.PostBeginPlay()
    return

@hook("WillowGame.WillowGFxLobbyLoadCharacter:OnSlotClicked", Type.PRE)
def OnSlotClicked(obj, args, ret, func):
    selected_item = obj.DisplayedCharacterDataList[args.SlotIndex + obj.TopSlotDataIndex]
    if not selected_item.SaveDataId == -1:
        return

    if selected_item.CharName in characters.keys():
        global selected_boosted_character
        selected_boosted_character = selected_item.CharName
        boosted_character_box.show()
        return Block



@hook("WillowGame.WillowSaveGameManager:EndGetSaveGameDataFromList", Type.PRE)
def EndGetSaveGameDataFromList(obj, args, ret, func):
    with prevent_hooking_direct_calls():
        save_data_list:list = func(args)

        for char in [new_gladiator,new_enforcer,new_lawbringer,new_fragtrap,new_doppelganger,new_baroness]:
            save_data_list.append(char)

        return Block, save_data_list


@hook("WillowGame.WillowPlayerController:ApplyItemSaveGameData", Type.PRE)
def ApplyItemSaveGameData(obj, args, ret, func):
    ApplyItemSaveGameData.disable()
    return Block

@hook("WillowGame.WillowPlayerController:ApplyInventorySaveGameData", Type.PRE)
def ApplyInventorySaveGameData(obj, args, ret, func):
    spawn_chests()
    ApplyInventorySaveGameData.disable()
    return Block

@hook("WillowGame.FrontendGFxMovie:Start", Type.POST)
def FrontendGFxMovie(obj, args, ret, func):
    global frontend_movie
    frontend_movie = WeakPointer(obj)
    return


boosted_character_button_confirm = OptionBoxButton(
    name="Yes"
)
boosted_character_button_cancel = OptionBoxButton(
    name="Cancel"
)

boosted_character_box = OptionBox(
    title="Boosted Character",
    message=f"You are about to load a boosted character, continue?",
    buttons=[boosted_character_button_confirm, boosted_character_button_cancel],
    on_select=load_character
)

def set_frontend():
    global frontend_movie
    frontend_movie = find_all("FrontendGFxMovie")[-1]#type:ignore

build_mod(hooks=[FrontendGFxMovie,EndGetSaveGameDataFromList,OnSlotClicked],on_enable=set_frontend)
