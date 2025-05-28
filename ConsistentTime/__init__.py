from typing import Any #type:ignore
from mods_base import get_pc, hook, build_mod, SliderOption, BoolOption #type:ignore
from unrealsdk import find_all, find_class #type:ignore
from unrealsdk.hooks import Type #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type:ignore


LastTime: float = 0
DayNightCycle: UObject = find_class('WillowSeqAct_DayNightCycle').ClassDefaultObject


def ChangeTime():
    DayNightCycle.SetTimeOfDay(LastTime)
    return


@hook('Engine.SequenceOp:Activated', Type.POST)
def SequenceOp(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if obj.Class.Name == "WillowSeqAct_DayNightCycle":
        obj.SetTimeOfDay(LastTime)
        SequenceOp.disable()
    return


@hook("WillowGame.PauseGFxMovie:Start", Type.PRE)
def Start(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if len(list(find_all("WillowSeqVar_TimeOfDay"))) >= 2:
        global LastTime
        LastTime = get_pc().WorldInfo.GRI.TimeOfDay
    return


@hook("WillowGame.WillowGameInfo:InitiateTravel", Type.PRE)
def InitiateTravel(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if len(list(find_all("WillowSeqVar_TimeOfDay"))) >= 2:
        global LastTime
        LastTime = obj.WorldInfo.GRI.TimeOfDay
        SequenceOp.enable()
    return


@hook("WillowGame.WillowScrollingListDataProviderFrontEnd:HandleClick", Type.PRE)
def MainMenuPress(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if args.EventID == 0 or args.EventID == 6:#0 is Continue button, 6 is new game
        global LastTime
        LastTime = get_pc().WorldInfo.GRI.TimeOfDay
        SequenceOp.enable()
    return


@hook("Engine.GameInfo:StartMatch")
def SaveQuitSet(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if obj.WorldInfo.IsMenuLevel():
        if oidResetSaveQuit.value:
            global LastTime
            LastTime = oidTimeOfDay.value
        ChangeTime()
    return


@hook("WillowGame.WillowPlayerController:PlayerTick", Type.PRE)
def ForceTimeTicks(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    ChangeTime()
    return


def TODSettingChanged(Setting, NewValue):
    global LastTime
    LastTime = NewValue
    ChangeTime()
    return


def ForceTimeSettingChanged(Setting, NewValue):
    if NewValue:
        ForceTimeTicks.enable()
    else:
        ForceTimeTicks.disable()
    return


oidTimeOfDay: SliderOption = SliderOption(
    "Default Time of Day",
    0,
    0,
    200,
    1,
    False,
    on_change=TODSettingChanged,
    description="Sets the starting default Time of Day. Also changes the current time.",
)

oidForceTime: BoolOption = BoolOption(
    "Force Time",
    False,
    "On",
    "Off",
    on_change=ForceTimeSettingChanged,
    description="With this enabled, the time will stay Default Time of Day setting until you turn it off.",
)

oidResetSaveQuit: BoolOption = BoolOption(
    "Reset on Save Quit",
    False,
    "On",
    "Off",
    description="With this enabled, the time will reset to the Default Time of Day setting after save quitting.",
)

build_mod(options=[oidTimeOfDay,oidResetSaveQuit,oidForceTime])