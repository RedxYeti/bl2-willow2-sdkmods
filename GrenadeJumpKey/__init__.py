from mods_base import get_pc, keybind, build_mod, hook #type:ignore
from unrealsdk.hooks import Type #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type:ignore
from typing import Any #type:ignore

UniqueID = None

@keybind("Throw Default Frag")
def ThrowDefaultFrag():
    PC = get_pc()
    
    if PC.CanThrowGrenade(PC.GetCurrentProjectileDefinition()):
        CurrentMod = GetItemInSlot(PC.GetPawnInventoryManager(), 1)
        if CurrentMod:
            global UniqueID
            UniqueID = CurrentMod.DefinitionData.UniqueID
            PC.GetPawnInventoryManager().InventoryUnreadied(CurrentMod, True)
            ThrowGrenade.enable()
            
        PC.Behavior_ThrowGrenade()
    return


@hook("WillowGame.WillowPlayerController:GrenadeThrowComplete", Type.PRE)
def ThrowGrenade(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    global UniqueID
    print("boop")
    Backpack = obj.GetPawnInventoryManager().Backpack
    for Item in Backpack:
        if Item.DefinitionData.UniqueID == UniqueID:
            obj.GetPawnInventoryManager().ReadyBackpackInventory(Item)
            break
    ThrowGrenade.disable()
    return


def GetItemInSlot(PlayerInventory, ItemSlot) -> UObject:
    ItemToCheck = PlayerInventory.ItemChain
    while ItemToCheck:
        if ItemToCheck.GetEquipmentLocation() == ItemSlot and ItemToCheck.bReadied:
            return ItemToCheck
        ItemToCheck = ItemToCheck.Inventory
    return None


build_mod(hooks=[])