from typing import Any #type:ignore
from mods_base import hook, build_mod, BoolOption, ButtonOption, SETTINGS_DIR #type:ignore
from unrealsdk.hooks import Type, Block #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type:ignore
from .LoadoutsFeedback import LoadoutMenu, ShowTrainingError, SaveLoadout, OverwriteConflict
import os


@hook("WillowGame.WillowGFxDialogBox:OnClose", Type.PRE)
def OnCloseLoadout(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    #runs every time a dialog closes, uses the ButtonTags for filtering. see WillowGFxDialogBox:AppendButton
    DialogResult = obj.DialogResult

    if DialogResult in ["LoadoutMenu", "SkillTreeLoadoutsOKBox", "LoadoutsCancel"]:
        LoadoutMenu(WPCOwner=obj.WPCOwner)

    elif DialogResult == "OverwriteLoadout":
        OverwriteConflict(obj.WPCOwner)

    elif DialogResult == "NormalRespec":
        if obj.WPCOwner.PlayerReplicationInfo.GetCurrencyOnHand(0) >= obj.WPCOwner.GetSkillTreeResetCost():
            obj.WPCOwner.ServerPurchaseSkillTreeReset()
        else:
            ShowTrainingError(obj.WPCOwner, "You don't have enough money for a respec.")
    return


@hook("WillowGame.WillowPlayerController:VerifySkillRespec", Type.PRE)
def VerifySkillRespec(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    #Quick port of the hooked function, creating the option menu you see in-game
    dlg = obj.GFxUIManager.ShowDialog(True)
    dlg.AutoLocEnable("WillowMenu", "dlg")
    dlg.AppendButton('LoadoutMenu', 'Skill Tree Loadouts')
    dlg.AppendButton('NormalRespec', 'Normal Respec')
    dlg.AutoAppendButton('Cancel')
    dlg.CancelButtonTag = 'Cancel'

    dlg.AutoLocEnableCaption("WillowMenu", "pname", "RespecSkillTree")
    dlg.AutoLocEnablePrompt("WillowGame", "VendingMachineGFxMovie", "Confirm_Prompt")

    dlg.ReplaceDialogCaption("%s", "$")
    dlg.ReplaceDialogCaption("%d", str(obj.GetSkillTreeResetCost()))

    dlg.ApplyLayout()
    return (Block)


#Next 2 hooks are for stopping the menu from disabling the respec button
@hook("WillowGame.CustomizationGFxMovie:OnSkillTreeReset", Type.PRE)
def OnSkillTreeReset(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    obj.PlayUISound('SkillPointReset')
    obj.CacheSkillBranchDescriptions()
    obj.extInitRespecInfoCard()
    return (Block)


@hook("WillowGame.CustomizationGFxMovie:extCharacterCustomizationOnLoad", Type.PRE)
def extCharacterCustomizationOnLoad(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    if not obj.bHasSpentSkillPoints:
        obj.bHasSpentSkillPoints = True
    return

def OpenLoadoutFolder(ButtonInfo:Any):
    LoadoutsDir = os.path.join(SETTINGS_DIR, "Skill Tree Loadouts")
    if os.path.exists(LoadoutsDir):
        os.startfile(LoadoutsDir)
    return

oidHideIneligible: BoolOption = BoolOption(
    "Hide Ineligible Loadouts",
    False,
    "On",
    "Off",
    description="With this enabled, it will hide loadouts you dont have enough skill points for.",
)

oidFreeLoadouts: BoolOption = BoolOption(
    "Free Loadout Respecs",
    False,
    "On",
    "Off",
    description="With this enabled, changing Loadouts will not cost money.",
)

oidOpenLoadoutFolder: ButtonOption = ButtonOption(
    "Open Loadouts Folder",
    on_press=OpenLoadoutFolder,
    description="Click this to open your Loadouts folder.",
)


build_mod()