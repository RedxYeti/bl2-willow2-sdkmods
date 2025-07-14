from typing import Any

from mods_base import get_pc,hook, build_mod, ObjectFlags, keybind, SpinnerOption

from unrealsdk import find_class, find_object, construct_object, find_all#type:ignore
from unrealsdk.hooks import Type, Block, log_all_calls#type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct#type:ignore

from save_options.options import HiddenSaveOption
from save_options.registration import register_save_options

icon = None
travel_station:str = ""
past_stations:list = []

def create_icon() -> None:
    #from alt use vendors https://bl-sdk.github.io/willow2-mod-db/mods/alt-use-vendors/

    global icon
    if not icon:
        base_icon = find_object(
            "InteractionIconDefinition",
            "GD_InteractionIcons.Default.Icon_DefaultUse",
        )

        icon = construct_object(
            cls=base_icon.Class,
            outer=base_icon.Outer,
            name="altusefasttravel",
            flags=ObjectFlags.KEEP_ALIVE,
            template_obj=base_icon,
        )

    if oidTravelType.value != "Current Objective":
        icon_text = f"RETURN TO {str(get_station(travel_station).StationDisplayName).upper()}" if travel_station else "" 
    else:
        icon_text = "TRAVEL TO OBJECTIVE"

    icon.Icon = 5
    icon.Action = "UseSecondary"
    icon.Text = icon_text
    return


def get_station(station_path:str) -> UObject:
    return find_object("FastTravelStationDefinition", station_path)


def get_specific_pt_option() -> HiddenSaveOption:
    match get_pc().GetCurrentPlaythrough():
        case 0:
            return oidSpecificStation
        case 1:
            return oidSpecificStationPT2
        case 2:
            return oidSpecificStationPT3
    return oidSpecificStation
        

def get_last_pt_option() -> HiddenSaveOption:
    match get_pc().GetCurrentPlaythrough():
        case 0:
            return oidLastStation
        case 1:
            return oidLastStationPT2
        case 2:
            return oidLastStationPT3
    return oidLastStation


def update_menu(obj:UObject, index:int) -> None:
    obj.PlaySpecialUISound("ResultSuccess")
    PlayUISound.enable()
    obj.HandleOpen()
    obj.FastTravelLocationListPanelClip.SetFloat("selectedIndex", float(index))
    OnClose.enable()
    return


def clear_station() -> None:
    global travel_station
    travel_station = ""
    get_specific_pt_option().value = ""
    return


@hook("WillowGame.TravelStation:SetUsability")
def SetUsability(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    func.func = find_class("WillowInteractiveObject")._find("SetUsability")#type:ignore ; this should be illegal
    func(args.bUsable, args.UsedType, args.UsedComponent)
    return Block


@hook("WillowGame.WillowInteractiveObject:InitializeFromDefinition", Type.POST)
def InitializeFromDefinition(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if obj.Class.Name != "FastTravelStation":
        return 

    if travel_station or oidTravelType.value == "Current Objective":
        if not icon:
            create_icon()
        args.Definition.HUDIconDefSecondary = icon
        obj.SetUsability(True, 1)
    return 


@hook("WillowGame.WillowPlayerController:ServerTeleportPlayerToStation", Type.POST)#type:ignore
def ServerTeleportPlayerToStation(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if oidTravelType.value == "Last Station":
        global past_stations, travel_station
        past_stations.append(args.StationDefinition._path_name())
        past_stations = past_stations[-2:]
        travel_station = past_stations[0] if len(past_stations) else ""
        if travel_station:
            if not icon:
                create_icon()
            icon.Text = f"RETURN TO {get_station(travel_station).StationDisplayName.upper()}"#type:ignore
    return


@hook("WillowGame.FastTravelStationGFxMovie:SetCurrentWaypoint", Type.POST)
def HandleOpen(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if oidTravelType.value != "Current Objective":
        HandleOpen.disable()
        return
    current_waypoint = obj.CurrentWaypointStationDef
    if current_waypoint and not current_waypoint.bSendOnly and current_waypoint.StationLevelName != get_pc().WorldInfo.GetMapName():
        get_pc().ServerTeleportPlayerToStation(obj.CurrentWaypointStationDef)
    HandleOpen.disable()


@hook("WillowGame.WillowPlayerController:PerformedSecondaryUseAction", Type.POST)#type:ignore
def PerformedSecondaryUseAction(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if obj.Role < 3 or not obj.CurrentUsableObject or not obj.CurrentInteractionIcon[1].IconDef:
        return 
    
    if not travel_station and oidTravelType.value != "Current Objective":
        return
    

    Station = obj.CurrentUsableObject
    if Station.Class.Name != "FastTravelStation":
        return 
    
    if oidTravelType.value != "Current Objective":
        obj.ServerTeleportPlayerToStation(get_station(travel_station))
    else:
        HandleOpen.enable()
        Station.UsedBy(obj.Pawn)
    return



@hook("GearboxFramework.GearboxGFxMovie:PlayUISound")
def PlayUISound(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    PlayUISound.disable()
    return Block
    
@hook("WillowGame.FastTravelStationGFxMovie:HandleInputKey")
def HandleInputKey(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if oidTravelType.value != "Specific Station":
        return

    if args.ukey == set_location.key and args.uevent == 0:
        global travel_station
        if not travel_station:
            create_icon()
            for station in find_all("FastTravelStation"):
                if station and station.InteractiveObjectDefinition:
                    station.InteractiveObjectDefinition.HUDIconDefSecondary = icon
                    station.SetUsability(True, 1)

        for station in find_all("FastTravelStationDefinition"):
            if station:
                station.StationDisplayName = station.StationDisplayName.split("*")[0]

        index = obj.PreviousSelectionIndex
        current_station = obj.LocationStationDefinitions[index]
        travel_station = current_station._path_name()

        if get_specific_pt_option().value and travel_station == get_specific_pt_option().value:
            clear_station()
            update_menu(obj, index)
            return
        
        get_specific_pt_option().value = travel_station
        current_station.StationDisplayName = current_station.StationDisplayName + "*"
        update_menu(obj, index)
    return


@hook("WillowGame.FastTravelStationGFxMovie:OnClose")
def OnClose(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if oidTravelType.value == "Current Objective":
        return
    
    if not get_specific_pt_option().value:
        for station in find_all("FastTravelStation"):
            if station and station.InteractiveObjectDefinition:
                station.InteractiveObjectDefinition.HUDIconDefSecondary = None
                station.SetUsability(False, 1)
        return

    if not icon:
        create_icon()
    icon.Text = f"RETURN TO {str(get_station(travel_station).StationDisplayName).split("*")[0].upper()}"#type:ignore
    OnClose.disable()
    return

        

def on_load() -> None:
    for station in find_all("FastTravelStationDefinition"):
        if station and "*" in station.StationDisplayName:
            station.StationDisplayName = station.StationDisplayName.split("*")[0]

    global travel_station, past_stations
    if get_specific_pt_option().value and oidTravelType.value == "Specific Station":
        travel_station = get_specific_pt_option().value
        create_icon()
        current_station = get_station(travel_station)
        current_station.StationDisplayName = current_station.StationDisplayName + "*"

    
    past_stations = get_last_pt_option().value
    if get_last_pt_option().value and oidTravelType.value == "Last Station":
        travel_station = past_stations[0]
        create_icon()

    return


def on_save() -> None:
    global travel_station
    if travel_station:
        get_specific_pt_option().value = travel_station
    
    if len(past_stations):
        get_last_pt_option().value = past_stations
    return


def changed_spinner(option, new_value) -> None:
    if get_pc().WorldInfo.bIsMenuLevel:
        return

    for station in find_all("FastTravelStationDefinition"):
        if station and "*" in station.StationDisplayName:
            station.StationDisplayName = station.StationDisplayName.split("*")[0]

    for station in find_all("FastTravelStation"):
        if station and station.InteractiveObjectDefinition:
            station.InteractiveObjectDefinition.HUDIconDefSecondary = None
            station.SetUsability(False, 1)

    if new_value == "Current Objective":
        if not icon:
            create_icon()
        
        icon.Text = "TRAVEL TO OBJECTIVE"

    elif get_specific_pt_option().value and new_value == "Specific Station":
        travel_station = get_specific_pt_option().value
        create_icon()
        current_station = get_station(travel_station)
        current_station.StationDisplayName = current_station.StationDisplayName + "*"

    elif new_value == "Last Station":
        past_stations = get_last_pt_option().value
        if get_last_pt_option().value:
            travel_station = past_stations[0]
            create_icon()

    if new_value == "Current Objective" or travel_station:
        for station in find_all("FastTravelStation"):
            if station and station.InteractiveObjectDefinition:
                station.InteractiveObjectDefinition.HUDIconDefSecondary = icon
                station.SetUsability(True, 1)
    
    return


@keybind("Set Fast Travel Location")
def set_location() -> None:
    return


oidSpecificStation:HiddenSaveOption = HiddenSaveOption("specific_station", "")
oidSpecificStationPT2:HiddenSaveOption = HiddenSaveOption("specific_station2", "")
oidSpecificStationPT3:HiddenSaveOption = HiddenSaveOption("specific_station3", "")
oidLastStation:HiddenSaveOption = HiddenSaveOption("last_station", [])
oidLastStationPT2:HiddenSaveOption = HiddenSaveOption("last_station2", [])
oidLastStationPT3:HiddenSaveOption = HiddenSaveOption("last_station3", [])


oidTravelType:SpinnerOption = SpinnerOption(
    "Alt Use Type",
    "Current Objective",
    ["Specific Station", "Last Station", "Current Objective"],
    True,
    description=("Choose either your current objective, the station you last traveled from, or a specific station."
                "\nSpecific and Last Station are saved per save, per playthrough level."
                "\nTo pick a specific station, set your hotkey and press that hotkey on the station you want in the fast travel menu."
                "\nSelecting the already active station will remove the location."),
    on_change=changed_spinner
)


mod = build_mod()
register_save_options(mod)

OnClose.disable()
PlayUISound.disable()
HandleOpen.disable()