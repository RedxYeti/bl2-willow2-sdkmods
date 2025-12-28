
from typing import Any
from mods_base import hook, build_mod, BoolOption, ENGINE
from unrealsdk import make_struct
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct
from random import choice

oidPickActionSkill = BoolOption("Action SKill First", 
                                True, 
                                "On", 
                                "Off",
                                description="With this on, the mod will always pick your action skill first.\n With it off, you'll have to wait for the randomizer to pick it.")


def GetRandomSkill(PC) -> list:
    PossibleSkills = []
    PST = PC.PlayerSkillTree
    for Skill in PST.Skills:
        Def = Skill.Definition
        if oidPickActionSkill.value and Def == PST.GetActionSkill() and Skill.Grade == 0:
            return [Def, 1]
        if Def.SkillIcon and Skill.Grade < Def.MaxGrade:
            PossibleSkills.append(Skill)
    return [choice(PossibleSkills).Definition, Skill.Grade + 1]


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST)
def AreaLoadSkillRandoThing(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if obj.WorldInfo.NetMode == 3:
        return
    
    for PRIInfo in ENGINE.GetCurrentWorldInfo().GRI.PRIArray:
        PC = PRIInfo.Owner
        PST = PC.PlayerSkillTree
        if PST:
            for Branch in PC.PlayerSkillTree.Branches:
                Branch.BranchPointsToUnlockNextBranch = 0

            for Tier in PST.Tiers:
                Tier.bUnlocked = True
    return


#respec
#for i in range(get_pc().PlayerReplicationInfo.GeneralSkillPoints):
#    if get_pc().HasPlayerEarnedAnySkillPoints():
#        get_pc().ServerUpgradeSkill(GetRandomSkill(get_pc()))

@hook("WillowGame.WillowPlayerController:OnExpLevelChange", Type.PRE)
def OnExpLevelChangeSKillRandoTHing(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if obj.Pawn.GetExpLevel() < 5:
        return


    if args.bNaturalLevelup:
        SkillToUpgrade = GetRandomSkill(obj)
        obj.ServerUpgradeSkill(SkillToUpgrade[0])
        HUDMovie = obj.GetHudMovie()
        if HUDMovie:
            HUDMovie.ClearTrainingText()
            Message = f"Upgraded {SkillToUpgrade[0].SkillName} to {SkillToUpgrade[1]}/{SkillToUpgrade[0].MaxGrade}"
            HUDMovie.AddTrainingText(Message, "Random Skill Selector", 5, make_struct("Color"), "", False, 0, obj.PlayerReplicationInfo, True)




build_mod()
