from unrealsdk import find_class, make_struct#type:ignore
from mods_base import Game, SETTINGS_DIR #type:ignore

import json
import os

from legacy_compat import legacy_compat#type: ignore
with legacy_compat():
    from Mods import UserFeedback #type: ignore

AllLoadouts = []
CharacterDir = ""
SkillPointLevelDifference = -1
OutSkillStruct = make_struct("SkillTreeSkillStateData")
LastLoadoutConflictName = ""

def GetSkillPointLevelDifference() -> int:
   return 4 if Game.get_current() == Game.BL2 else 2


def ShowOKBox(WPCOwner, Message):
    dlg = WPCOwner.GFxUIManager.ShowDialog(True)
    dlg.AutoLocEnable("WillowMenu", "dlg")
    dlg.AppendButton('SkillTreeLoadoutsOKBox', 'OK')
    dlg.DlgCaptionMarkup = Message
    dlg.ApplyLayout()
    return


def ShowConflictDialog(WPCOwner):
    global LastLoadoutConflictName
    dlg = WPCOwner.GFxUIManager.ShowDialog(True)
    dlg.AutoLocEnable("WillowMenu", "dlg")
    dlg.AppendButton('OverwriteLoadout', 'Overwrite Loadout')
    dlg.AppendButton('LoadoutsCancel','Cancel')
    dlg.DlgCaptionMarkup = "Overwriting Loadout"
    dlg.DlgTextMarkup = f"\nAre you sure you want to overwrite the Loadout '{LastLoadoutConflictName}'?"
    dlg.ApplyLayout()
    return


def ShowTrainingError(WPCOwner, Message):
    WPCOwner.GFxUIManager.ShowTrainingDialog(Message, "Skill Tree Loadouts", 2)
    return


def GetBranchData(CurrentJson):
    BranchTotals = {}
    TotalCost = CurrentJson.get("TotalCost", 0)
    TotalSpent = 1

    for key, values in CurrentJson.items():
        if key != "TotalCost":
            Sum = sum(values.values())
            BranchTotals[key] = Sum
            TotalSpent += Sum
    
    return BranchTotals, TotalCost, TotalSpent


def OverwriteConflict(WPCOwner):
    SaveLoadout(LastLoadoutConflictName, WPCOwner)
    return


def SaveLoadout(Name, WPCOwner) -> None:
    #iterates over the branches and creates the json based off the branch/skill name. 
    #starts at 1 to manually add the actionskill point.

    if not Name:
        return

    global CharacterDir, OutSkillStruct
    PST = WPCOwner.PlayerSkillTree
    Loadout = {"TotalCost": 1}
    
    for Branch in PST.Branches:
        if Branch.Definition.BranchName:
            Loadout[Branch.Definition.BranchName] = {}
            for Tier in Branch.Definition.Tiers:
                for Skill in Tier.Skills:
                    Grade = PST.GetSkillState(Skill, OutSkillStruct)[1].SkillGrade
                    Loadout[Branch.Definition.BranchName][Skill.SkillName] = Grade
                    Loadout["TotalCost"] += Grade
    
    NewLoadout = os.path.join(CharacterDir, f"{Name}.json")
    with open(NewLoadout, "w") as file:
        json.dump(Loadout, file, indent=4)

    ShowOKBox(WPCOwner, "Loadout Saved!")
    return


def LoadLoadout(Name, WPCOwner):
    #does the same thing as SaveLoadout but in reverse

    global CharacterDir, SkillPointLevelDifference
    try:
        with open(os.path.join(CharacterDir, f"{Name}.json"), 'r') as CurrentFile:
            CurrentPreset = json.load(CurrentFile)
    except:
        ShowTrainingError(WPCOwner, "This Loadout is corrupted.\n\nCheck the json for errors.")
        return

    #i cant read peoples minds, so they need to have enough skill points to load a loadout
    if CurrentPreset["TotalCost"] > (WPCOwner.Pawn.GetExpLevel() - SkillPointLevelDifference):
        ShowTrainingError(WPCOwner, "You don't have enough skill points for this Loadout.\n\nYou can hide Loadouts you're ineligible for in the mod settings.")
        return
    
    if WPCOwner.GetSkillTreeResetCost() > WPCOwner.PlayerReplicationInfo.GetCurrencyOnHand(0):
        ShowTrainingError(WPCOwner, "You don't have enough money for a respec.")
        return
    
    from . import oidFreeLoadouts
    if oidFreeLoadouts.value:
        WPCOwner.PlayerReplicationInfo.GeneralSkillPoints += WPCOwner.ResetSkillTree(True)
        find_class('WillowLeviathanService').ClassDefaultObject.RecordPointsResetEventForPlayer(WPCOwner, 0, WPCOwner.PlayerReplicationInfo.GeneralSkillPoints)
        WPCOwner.PlayerReplicationInfo.bForceNetUpdate = True 
    else:
        WPCOwner.ServerPurchaseSkillTreeReset()

    PST = WPCOwner.PlayerSkillTree

    WPCOwner.ServerUpgradeSkill(PST.GetActionSkill())

    for Branch in PST.Branches:
        if Branch.Definition.BranchName:
            for Tier in Branch.Definition.Tiers:
                for Skill in Tier.Skills:
                    if CurrentPreset[Branch.Definition.BranchName][Skill.SkillName] > 0:
                        for i in range(CurrentPreset[Branch.Definition.BranchName][Skill.SkillName]):
                            WPCOwner.ServerUpgradeSkill(Skill)

    ShowOKBox(WPCOwner, "Loadout loaded!")
    return


class LoadoutMenu(UserFeedback.OptionBox):
    WPCOwner = None
    AllLoadouts = []
    ShownLoadouts = []
    buttons = []

    def ValidateLoadouts(self, WPCOwner, PST):
        """
        iterates over the jsons to makes sure they load
        makes sure the TotalCost of the loadout lines up with the skill points spent in each branch
        and creates the buttons for the menu

        also creates a global list of all loadouts for the character class to avoid conflicts
        """
        global CharacterDir, SkillPointLevelDifference, AllLoadouts
        from . import oidHideIneligible
        for file in os.listdir(CharacterDir):
            if os.path.isfile(os.path.join(CharacterDir, file)) and file.endswith(".json"):
                try:
                    with open(os.path.join(CharacterDir, file), 'r') as CurrentFile:
                        CurrentPreset = json.load(CurrentFile)
                        BranchTotals, TotalCost, TotalSpent = GetBranchData(CurrentPreset)
                except:
                    print(f"Loadout file '{file}' is corrupted. Check the json for errors. Skipping.")
                    continue
                
                NameToAdd = str(os.path.splitext(file)[0])
                AllLoadouts.append(NameToAdd)

                if TotalCost < TotalSpent:
                    print(f"Loadout '{NameToAdd}' costs more skill points than the 'TotalCost' ({TotalCost}). This Loadout needs at least {TotalSpent}. Skipping.")
                    continue

                if SkillPointLevelDifference == -1:
                    SkillPointLevelDifference = GetSkillPointLevelDifference()

                if oidHideIneligible.value and TotalCost > (WPCOwner.Pawn.GetExpLevel() - SkillPointLevelDifference):
                    continue
                
                bSkipFile = False
                for Branch in PST.Branches:
                    if Branch.Definition.BranchName and not bSkipFile:
                        for Tier in Branch.Definition.Tiers:
                            for Skill in Tier.Skills:
                                if CurrentPreset[Branch.Definition.BranchName][Skill.SkillName] > Skill.MaxGrade:
                                    CurrentGrade = CurrentPreset[Branch.Definition.BranchName][Skill.SkillName]
                                    print(f"Loadout '{NameToAdd}' has the skill '{Skill.SkillName}' higher than what's allowed ({CurrentGrade}/{Skill.MaxGrade}). Skipping.")
                                    bSkipFile = True
                                    break

                if not bSkipFile:
                    self.ShownLoadouts.append(NameToAdd)
                    Branches = "/".join(str(Total) for Total in BranchTotals.values())
                    self.buttons.append(UserFeedback.OptionBoxButton(f"{NameToAdd} - {Branches} Cost: {TotalCost}"))
        return


    def __init__(self, WPCOwner=None):
        #before validating the loadouts it checks the player class, creates dirs if necessary
        #this helps keep loadouts organized, instead of sticking them all in 1 dir and having to check which character the loadout was made for
        global CharacterDir, AllLoadouts
        self.WPCOwner = WPCOwner

        LoadoutsDir = os.path.join(SETTINGS_DIR, "Skill Tree Loadouts")

        if not os.path.exists(LoadoutsDir):
            os.makedirs(LoadoutsDir)

        CharacterDir = os.path.join(LoadoutsDir, WPCOwner.GetCharacterClassDefaultName())

        if not os.path.exists(CharacterDir):
            os.makedirs(CharacterDir)

        AllLoadouts = []
        self.buttons = []
        self.ShownLoadouts = []
        self.ValidateLoadouts(WPCOwner, WPCOwner.PlayerSkillTree)

        if not len(self.buttons):
            self.buttons = [UserFeedback.OptionBoxButton("No Saved Loadouts...")]

        super().__init__(
            Title="Skill Tree Loadouts",
            Caption=f"Save or choose the loadout you want.\nYou have {self.WPCOwner.Pawn.GetExpLevel() - SkillPointLevelDifference} Skill Points to spend.",
            Tooltip="[Enter] Load  [N] Save  [C] Overwrite  [Escape] Exit",
            Buttons=self.buttons,
        )
        self.Show()

    def OnInput(self, key: str, event: int) -> None:
        if key == "N" and event == 1:
            self.Hide()
            CreateLoadout(WPCOwner=self.WPCOwner)
        elif key == "C" and event == 1 and self.GetSelectedButton().Name != "No Saved Loadouts...":
            global LastLoadoutConflictName
            LastLoadoutConflictName = self.ShownLoadouts[self.buttons.index(self.GetSelectedButton())]
            self.Hide()
            ShowConflictDialog(self.WPCOwner)

    def OnPress(self, button: UserFeedback.OptionBoxButton) -> None:
        if button.Name != "No Saved Loadouts...":
            LoadLoadout(self.ShownLoadouts[self.buttons.index(button)], self.WPCOwner)


class CreateLoadout(UserFeedback.TextInputBox):
    WPCOwner = None

    def __init__(self, name = "", WPCOwner=None):
        self.WPCOwner = WPCOwner
        super().__init__(Title="Enter Loadout Name", DefaultMessage=name)
        self.Show()

    def OnSubmit(self, name: str) -> None:
        if name != "":
            global AllLoadouts
            if str(name).lower() not in AllLoadouts:
                SaveLoadout(name, self.WPCOwner)
            else:
                global LastLoadoutConflictName
                LastLoadoutConflictName = name
                ShowConflictDialog(self.WPCOwner)