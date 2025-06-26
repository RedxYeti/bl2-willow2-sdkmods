from mods_base import hook, build_mod, BoolOption
from unrealsdk.hooks import Type, Block, prevent_hooking_direct_calls


@hook("WillowGame.WillowVehicleBase:ExitAnimIsSafeToUse", Type.PRE)
def ExitAnimIsSafeToUse(*_):
    if oidTeleportOut.value:
        return Block, False

@hook("WillowGame.WillowVehicle:DriverEnter", Type.PRE)
def DriverEnter(obj, args, ret, func):
    if oidTeleportIn.value:
        if args.P.Class.Name == "WillowPlayerPawn" and not args.SkipAnim:
            with prevent_hooking_direct_calls():
                func(args.P, True)
                return Block
    
@hook("WillowGame.WillowVehicle:PlayTeleportIntoVehicleEffect", Type.PRE)
@hook("WillowGame.WillowVehicle:PlayTeleportEffectAtLocation", Type.PRE)
def PlayTeleportIntoVehicleEffect(*_):
    if oidEffect.value:
        return Block

oidEffect = BoolOption(
    "Disable Teleport Effects",
    False,
    "On",
    "Off",
    description="Disables the teleport effects that play when you enter/exit vehicles."
)

oidTeleportIn = BoolOption(
    "Teleport Into Vehicles",
    True,
    "On",
    "Off",
    description="Always teleport into vehicles."
)

oidTeleportOut = BoolOption(
    "Teleport out of Vehicles",
    True,
    "On",
    "Off",
    description="Always teleport out of vehicles."
)

build_mod(options=[oidTeleportIn, oidTeleportOut, oidEffect])