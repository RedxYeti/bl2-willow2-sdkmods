from mods_base import get_pc, hook, build_mod, ENGINE, Game, Mod, ObjectFlags, MODS_DIR, command,keybind,BoolOption,SliderOption
from unrealsdk import construct_object, find_all, find_class, make_struct, find_object
from unrealsdk.hooks import Type, add_hook, Block, remove_hook, prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct, UClass, WeakPointer, IGNORE_STRUCT

from ui_utils import show_hud_message
from typing import Any
from random import choice
from argparse import Namespace

GD_GLOBALS = find_object('GlobalsDefinition', 'GD_Globals.General.Globals')
FFYL_SETTINGS = find_object('Behavior_PostProcessOverlay', 'GD_PlayerShared.injured.PlayerInjuredDefinition:Behavior_PostProcessOverlay_0')
try:
    POST_PROCESS = find_object('UberPostProcessEffect','Transient.PostProcessChain_0:UberPostProcessEffect_0')
except AttributeError as error:
    print("Post Process Effect Not Found. Try resetting your graphics by backing up then deleting WillowEngine.ini in documents and restarting the game.")
    print(error)

BLACK_OUTLINES = None
try:
    BLACK_OUTLINES = find_object('EdgeDetectionPostProcessEffect', 'Transient.PostProcessChain_0:EdgeDetectionPostProcessEffect_0')
    BLACK_OUTLINES.ObjectFlags |= ObjectFlags.KEEP_ALIVE
except:
    print(f"[Advanced Visual Settings] Black Outlines not found. Recommend setting DefaultPostProcessName to WillowEngineMaterials.WillowScenePostProcess in WillowEngine.ini")
    pass

def send_scale_command(option:str, value:str):
    get_pc().ConsoleCommand(f"scale set {option} {value}")
    return


@BoolOption(
    "Bloom",
    False,
    "On",
    "Off",
    description="Enable or Disable Bloom."
).set_on_change(while_enabled=True)
def _bloom_setting(option:BoolOption, new_value:bool):
    send_scale_command("Bloom", str(new_value))


@BoolOption(
    "Light Shafts",
    True,
    "On",
    "Off",
    description="Enable or Disable Light Shafts."
).set_on_change(while_enabled=True)
def _lightshafts_setting(option:BoolOption, new_value:bool):
    send_scale_command("bAllowLightShafts", str(new_value))


@BoolOption(
    "Vignette",
    True,
    "On",
    "Off",
    description="Enable or Disable Vignette.",
).set_on_change(while_enabled=True)
def _vignette_setting(option:BoolOption, new_value:bool):
    if POST_PROCESS:
        POST_PROCESS.VignetteEnabled = new_value


@BoolOption(
    "Motion Blur",
    True,
    "On",
    "Off",
    description="Enable or Disable Motion Blur.",
).set_on_change(while_enabled=True)
def _motion_blur_setting(option:BoolOption, new_value:bool):
    _motion_blur_setting.value = new_value
    if POST_PROCESS:
        send_scale_command("MotionBlur", str(new_value))
        if new_value:
            POST_PROCESS.FullMotionBlur = True
            POST_PROCESS.MotionBlurAmount = 0.5
        else:
            POST_PROCESS.FullMotionBlur = False
            POST_PROCESS.MotionBlurAmount = 0

        on_post_process_option_changed()


@BoolOption(
    "Tonemapper",
    True,
    "On",
    "Off",
    description="Enable or Disable Tonemapper (Map Specific Effects).",
).set_on_change(while_enabled=True)
def _tonemapper_setting(option:BoolOption, new_value:bool):
    _tonemapper_setting.value = new_value
    if POST_PROCESS:
        if new_value:
            POST_PROCESS.TonemapperType = 2
        else:
            POST_PROCESS.TonemapperType = 0

        on_post_process_option_changed()


@BoolOption(
    "Depth of Field",
    True,
    "On",
    "Off",
    description="Enable or Disable Depth of Field.",
).set_on_change(while_enabled=True)
def _dof_setting(option:BoolOption, new_value:bool):
    _dof_setting.value = new_value
    if POST_PROCESS:
        if new_value:
            POST_PROCESS.bOverrideDOFSettings = True
        else:
            POST_PROCESS.bOverrideDOFSettings = False

        on_post_process_option_changed()


@BoolOption(
    "Desaturation",
    True,
    "On",
    "Off",
    description="Enable or Disable Desaturation.",
).set_on_change(while_enabled=True)
def _desaturation_setting(option:BoolOption, new_value:bool):
    _desaturation_setting.value = new_value
    on_post_process_option_changed()


@SliderOption(
    "Map Effect Strength",
    100,
    0,
    100,
    description="Set the strength of map effects."
).set_on_change(while_enabled=True)
def _map_effect_setting(option:SliderOption, new_value:bool):
    for volume in find_all("PostProcessVolume"):
        path = volume._path_name()
        if path in POST_PROCESS_VOLUMES:
            set_scene_strength(volume, path)


@SliderOption(
    "Black Outline Thickness",
    2,
    0,
    5,
    1,
    description="Set the thickness of the black outlines, 0 is off."
).set_on_change(while_enabled=True)
def _outlines_setting(option:SliderOption, new_value:bool):
    if BLACK_OUTLINES:
        for chain in find_all("PostProcessChain"):
            if "Transient" not in str(chain):
                continue

            if new_value == 0:
                for index, effect in enumerate(chain.Effects):
                    if effect.Class.Name == "EdgeDetectionPostProcessEffect":
                        del chain.Effects[index]
                        break
            else:
                found_outlines = False
                for index, effect in enumerate(chain.Effects):
                    if effect.Class.Name == "EdgeDetectionPostProcessEffect":
                        found_outlines = True
                        break
                if not found_outlines:
                    chain.Effects.append(BLACK_OUTLINES)

                BLACK_OUTLINES.TexelOffset = new_value
    return


def set_scene_strength(volume:UObject, path:str):
    settings = volume.Settings
    vanilla = POST_PROCESS_VOLUMES[path]
    
    clamp = _map_effect_setting.value / 100.0
    
    vanilla_highlight = vanilla["highlights"]
    settings.Scene_HighLights.X = 1.0 + (vanilla_highlight["x"] - 1.0) * clamp
    settings.Scene_HighLights.Y = 1.0 + (vanilla_highlight["y"] - 1.0) * clamp
    settings.Scene_HighLights.Z = 1.0 + (vanilla_highlight["z"] - 1.0) * clamp

    vanilla_midtones = vanilla["midtones"]
    settings.Scene_MidTones.X = 1.0 + (vanilla_midtones["x"] - 1.0) * clamp
    settings.Scene_MidTones.Y = 1.0 + (vanilla_midtones["y"] - 1.0) * clamp
    settings.Scene_MidTones.Z = 1.0 + (vanilla_midtones["z"] - 1.0) * clamp

    vanilla_shadows = vanilla["shadows"]
    settings.Scene_Shadows.X = vanilla_shadows["x"] * clamp
    settings.Scene_Shadows.Y = vanilla_shadows["y"] * clamp
    settings.Scene_Shadows.Z = vanilla_shadows["z"] * clamp


def set_post_processing(post_process_settings:WrappedStruct):
    dof = _dof_setting.value
    post_process_settings.bEnableDOF = dof
    post_process_settings.bOverride_EnableDOF = dof
    POST_PROCESS.bOverrideDOFSettings = False if dof else True

    bloom = _bloom_setting.value
    post_process_settings.bEnableBloom = bloom
    post_process_settings.bOverride_EnableBloom = bloom

    motion_blur = _motion_blur_setting.value
    post_process_settings.bEnableMotionBlur = motion_blur
    post_process_settings.bOverride_EnableMotionBlur = motion_blur
    post_process_settings.MotionBlur_FullMotionBlur = motion_blur
    post_process_settings.MotionBlur_Amount = 0 if not motion_blur else 0.5

    desaturation = _desaturation_setting.value
    post_process_settings.bOverride_Scene_Desaturation = desaturation


def on_post_process_option_changed():
    set_post_processing(GD_GLOBALS.PPOverride)
    set_post_processing(FFYL_SETTINGS.OverlayParameters.DestPostProcessOverlay)

    for volume in find_all("PostProcessVolume"):
        set_post_processing(volume.Settings)


@hook("WillowGame.WillowPlayerController:ClearPostProcessChains", Type.POST)
def _AVS_ClearPostProcessChains(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    on_post_process_option_changed()


@hook("Engine.WorldInfo:PreBeginPlay", Type.POST)
def _AVS_WorldInfo_PreBeginPlay(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    set_post_processing(obj.DefaultPostProcessSettings)


POST_PROCESS_VOLUMES = {}
@hook("Engine.Volume:PostBeginPlay", Type.POST)
def _AVS_Volume_PostBeginPlay(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if obj.Class.Name != "PostProcessVolume":
        return
    global POST_PROCESS_VOLUMES

    settings = obj.Settings

    path = obj._path_name()

    if path not in POST_PROCESS_VOLUMES.keys():
        POST_PROCESS_VOLUMES[path] = {
            "highlights": {
                "x": settings.Scene_HighLights.X,
                "y": settings.Scene_HighLights.Y,
                "z": settings.Scene_HighLights.Z
            },
            "midtones": {
                "x": settings.Scene_MidTones.X,
                "y": settings.Scene_MidTones.Y,
                "z": settings.Scene_MidTones.Z
            },
            "shadows": {
                "x": settings.Scene_Shadows.X,
                "y": settings.Scene_Shadows.Y,
                "z": settings.Scene_Shadows.Z
            },
        }

    set_scene_strength(obj, path)
    
    set_post_processing(settings)


def set_options():
    for option in MOD_OPTIONS:
        option.on_change_while_enabled(option, option.value)


MOD_OPTIONS = [
    _outlines_setting,
    _bloom_setting,
    _dof_setting,
    _desaturation_setting,
    _lightshafts_setting,
    _map_effect_setting,
    _motion_blur_setting,
    #_tonemapper_setting,
    _vignette_setting,
]


build_mod(options=MOD_OPTIONS, on_enable=set_options)