from typing import Any #type:ignore
import unrealsdk #type:ignore
from mods_base import get_pc, hook, build_mod #type:ignore
from unrealsdk.hooks import Type #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type:ignore


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST)
def SancDoor(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    if obj.WorldInfo.GetMapName() in ["Sanctuary_P", "SanctuaryAir_P"]:
        MapName = obj.WorldInfo.GetMapName().strip("_P")
        
        raiders = unrealsdk.find_object("WillowInteractiveObject", f"{MapName}_Dynamic.TheWorld:PersistentLevel.WillowInteractiveObject_36")
        zed = unrealsdk.find_object("WillowInteractiveObject", f"{MapName}_Dynamic.TheWorld:PersistentLevel.WillowInteractiveObject_88")
        scooter = unrealsdk.find_object("WillowInteractiveObject", f"{MapName}_Dynamic.TheWorld:PersistentLevel.WillowInteractiveObject_7")
        
        for io in [zed, raiders, scooter]:
            io.UsedBy(get_pc().Pawn)
    
    return
    
build_mod()
