from typing import Any
from mods_base import get_pc, ENGINE, SETTINGS_DIR #type:ignore
from unrealsdk.hooks import Type, add_hook, remove_hook #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type:ignore
from unrealsdk import find_object#type:ignore
from ui_utils import show_hud_message#type:ignore
import os
import json
import time

lasttime = 0

def ButtonCreated(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if args.Caption == "$WillowMenu.WillowScrollingListDataProviderFrontEnd.Play_Continue":
        message = f"Your save json has a broken entry! <br>You need to fix your json before continuing!"
        get_pc().GFxUIManager.ShowTrainingDialog(message, "Projectile Randomizer", 5)
        remove_hook("WillowGame.WillowScrollingList:AddListItem", Type.PRE, "ButtonCreated")
    return

def HudLoaded(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    remove_hook("WillowGame.WillowHUDGFxMovie:Start", Type.PRE, "HudLoaded")
    Hud = get_pc().GetHUDMovie()
    PRI = ENGINE.GamePlayers[0].Actor.PlayerReplicationInfo
    if Hud and PRI:
        Hud.ClearTrainingText()
        Message = f"<font size='20'>Your current save json is read only!</font>"
        show_hud_message("Projectile Randomizer", Message, 5)
    return

def SaveToJson(FilePath, unique_ids_data):
    global lasttime
    if os.path.exists(FilePath) and not os.access(FilePath, os.W_OK):
        #read only
        if time.time() - lasttime > 60:
            lasttime = time.time()
            add_hook("WillowGame.WillowHUDGFxMovie:Start", Type.PRE,"HudLoaded", HudLoaded)
        return
    
    data = {}
    for unique_id, values in unique_ids_data.items():
        item_entry = {
            "Item Name": values[3],  
            "Item Part": str(values[0]),
            "Firing Mode": str(values[1]),
            "Projectile": str(values[2])
        }
        data[unique_id] = item_entry
    
    with open(FilePath, 'w') as file:
        json.dump(data, file, indent=4)


def LoadFromJson(FilePath):
    with open(FilePath, 'r') as file:
        try:
            data = json.load(file)
        except:
            get_pc().ReturnToTitleScreen(True)
            add_hook("WillowGame.WillowScrollingList:AddListItem", Type.PRE, "ButtonCreated", ButtonCreated)
            return    
    
    SavedIDs = {'UniqueIDs': {}}
    for unique_id, entry in data.items():
        NewList = []
        
        item_part = entry["Item Part"]
        firing_mode = entry["Firing Mode"]
        projectile = entry["Projectile"]
        Name = entry["Item Name"]

        value_list = [item_part, firing_mode, projectile]
        
        for value in value_list:
            if not value or value == "None":
                NewList.append(None)
            else:
                try:
                    split_parts = value.split(f"'")
                    part1 = split_parts[0]
                    part2 = split_parts[1]
                    NewObject = find_object(part1, part2)
                    NewList.append(NewObject)
                except:
                    continue

        NewList.append(Name)

        SavedIDs['UniqueIDs'][int(unique_id)] = NewList
    return SavedIDs


def append_to_file(TextFile, entry):
    base_dir = SETTINGS_DIR
    FilePath = os.path.join(base_dir, f'ProjectileRandomizer\\Saves',TextFile)
    with open(FilePath, 'a') as file:
        file.write(entry + '\n')

def PrepFiles():
    subdir = f'ProjectileRandomizer\\Saves'
    base_dir = SETTINGS_DIR
    dir_path = os.path.join(base_dir, subdir)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    

def GetSaveLocation(PlayerSaveID):
    subdir = f'ProjectileRandomizer\\Saves'
    base_dir = SETTINGS_DIR
    dir_path = os.path.join(base_dir, subdir)

    FilePath = os.path.join(dir_path, f"{PlayerSaveID}.json")

    if not os.path.exists(FilePath):
        with open(FilePath, 'w') as file:
            json.dump({}, file, indent=4)

    return FilePath

SanitizeName = lambda InputName: InputName.split('&')[0]