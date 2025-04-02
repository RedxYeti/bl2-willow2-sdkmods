from typing import Any #type:ignore
from mods_base import hook, keybind, get_pc, build_mod #type:ignore
from unrealsdk import make_struct, find_class #type:ignore
from unrealsdk.hooks import Type, Block #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type:ignore


CurrentLocation: WrappedStruct = make_struct("Vector")
CheckLocation: WrappedStruct = make_struct("Vector")

def CanBHop(PawnToCheck) -> bool:
    CurrentWeapon = PawnToCheck.Weapon
    if not CurrentWeapon:
        CurrentWeapon = PawnToCheck.Spawn(find_class("WillowWeapon"))

    global CurrentLocation, CheckLocation
    PawnLocation = PawnToCheck.Location

    CurrentLocation.X = PawnLocation.X
    CurrentLocation.Y = PawnLocation.Y
    CurrentLocation.Z = PawnLocation.Z

    CheckLocation.X = PawnLocation.X
    CheckLocation.Y = PawnLocation.Y
    CheckLocation.Z = PawnLocation.Z - 1000

    #from tracelib
    TraceInfo = CurrentWeapon.CalcWeaponFire(StartTrace=CurrentLocation,EndTrace=CheckLocation,bTestTrace=True,)[0]
    
    return TraceInfo.HitActor and (CurrentLocation.Z - TraceInfo.HitLocation.Z) < 130


@hook("WillowGame.WillowPlayerPawn:CanStuckJump", Type.PRE)
def CanStuckJump(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    if obj.Physics == 2 and CanBHop(obj):
        return Block, True
    

@hook("WillowGame.WillowPlayerController:PlayerTick", Type.PRE)
def PlayerTick(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    obj.PlayerInput.Jump()
    return


@keybind("Auto Hop Key", event_filter=None, description="Hold this button down to automatically bunny hop. This doesn't work very well, I suggest a macro or scrollwheel jump. Controller users I'd suggest setting your jump to repeating on hold in the steam controller settings.")
def AutoHop(InputEvent):
    if InputEvent == 0:
        PlayerTick.enable()
    elif InputEvent == 1:
        PlayerTick.disable()
    return


build_mod(hooks=[CanStuckJump])