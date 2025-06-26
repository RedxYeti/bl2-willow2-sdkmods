import math
from typing import Any
from mods_base import get_pc,hook, build_mod, BoolOption
from unrealsdk import find_class, find_object, construct_object, make_struct
from unrealsdk.hooks import Type, Block, prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from save_options.options import HiddenSaveOption
from save_options.registration import register_save_options

from .skill_effects import weapon_damage, reload_speed, fire_rate, accuracy, accuracy_max, accuracy_idle
from .skill_effects import weapon_damage_offhand, reload_speed_offhand, fire_rate_offhand, accuracy_offhand, accuracy_max_offhand, accuracy_idle_offhand
from .xp_table import xp_table

weapon_types = {
    "Shotgun": 0,
    "Assault Rifle": 0,
    "Pistol": 0,
    "Sub-Machine Gun": 0,
    "Sniper Rifle": 0,
    "Launcher": 0,
}

current_weapon_type = ""

saved_xp = HiddenSaveOption("saved_xp", weapon_types)

skill_default = find_class("SkillDefinition").ClassDefaultObject
shotgun_skill = construct_object("SkillDefinition", skill_default, "shotgun_skill")
shotgun_skill.ObjectFlags |= 0x4000
shotgun_skill.bAutoUpdateContexts=True
shotgun_skill.bCanBeToggledOff=False
shotgun_skill.bDoNotShiftPastCurrentTime=True
shotgun_skill.bSubjectToGradeRules=False
shotgun_skill.SkillEffectUpdateIterval=0.5
shotgun_skill.SkillName="Weapon Prof"
shotgun_skill.SkillType=0
shotgun_skill.DurationType=0
shotgun_skill.TrackedSkillType=0
shotgun_skill.TrackedSkillHUDSlot=0
shotgun_skill.InitialDuration=0.0
shotgun_skill.BaseRange=0.0
shotgun_skill.ActionSkillArchetype=None
shotgun_skill.SkillVisionModeCoordinatedEffect=None
shotgun_skill.DefaultStartingGrade=0
shotgun_skill.MaxGrade=50
shotgun_skill.PlayerLevelRequirement=0
shotgun_skill.SkillIcon=None
shotgun_skill.CustomStackCount=None
shotgun_skill.TrackedActiveSkill=None
shotgun_skill.BehaviorProviderDefinition=None

assault_rifle_skill = construct_object("SkillDefinition", skill_default, "assault_rifle_skill", template_obj=shotgun_skill)
pistol_skill = construct_object("SkillDefinition", skill_default, "pistol_skill", template_obj=shotgun_skill)
smg_skill = construct_object("SkillDefinition", skill_default, "smg_skill", template_obj=shotgun_skill)
sniper_skill = construct_object("SkillDefinition", skill_default, "sniper_skill", template_obj=shotgun_skill)
launcher_skill = construct_object("SkillDefinition", skill_default, "launcher_skill", template_obj=shotgun_skill)

all_prof_skills = [
    shotgun_skill,
    assault_rifle_skill,
    pistol_skill,
    smg_skill,
    sniper_skill,
    launcher_skill,
]

for skill in all_prof_skills:
    skill.ObjectFlags |= 0x4000

shotgun_skill.SkillEffectDefinitions = [weapon_damage,reload_speed,fire_rate]
assault_rifle_skill.SkillEffectDefinitions = [weapon_damage,reload_speed,accuracy]
pistol_skill.SkillEffectDefinitions = [weapon_damage,reload_speed,accuracy]
smg_skill.SkillEffectDefinitions = [weapon_damage,reload_speed,accuracy]
sniper_skill.SkillEffectDefinitions = [weapon_damage,reload_speed,fire_rate,accuracy_max,accuracy_idle]
launcher_skill.SkillEffectDefinitions = [weapon_damage,reload_speed,accuracy]

shotgun_skill_offhand = construct_object("SkillDefinition", skill_default, "shotgun_skill_offhand", template_obj=shotgun_skill)
assault_rifle_skill_offhand = construct_object("SkillDefinition", skill_default, "assault_rifle_skill_offhand", template_obj=shotgun_skill)
pistol_skill_offhand = construct_object("SkillDefinition", skill_default, "pistol_skill_offhand", template_obj=shotgun_skill)
smg_skill_offhand = construct_object("SkillDefinition", skill_default, "smg_skill_offhand", template_obj=shotgun_skill)
sniper_skill_offhand = construct_object("SkillDefinition", skill_default, "sniper_skill_offhand", template_obj=shotgun_skill)
launcher_skill_offhand = construct_object("SkillDefinition", skill_default, "launcher_skill_offhand", template_obj=shotgun_skill)

all_prof_skills_offhand = [
    shotgun_skill_offhand,
    assault_rifle_skill_offhand,
    pistol_skill_offhand,
    smg_skill_offhand,
    sniper_skill_offhand,
    launcher_skill_offhand,
]

for skill in all_prof_skills_offhand:
    skill.ObjectFlags |= 0x4000

shotgun_skill_offhand.SkillEffectDefinitions = [weapon_damage_offhand,reload_speed_offhand,fire_rate_offhand]
assault_rifle_skill_offhand.SkillEffectDefinitions = [weapon_damage_offhand,reload_speed_offhand,accuracy_offhand]
pistol_skill_offhand.SkillEffectDefinitions = [weapon_damage_offhand,reload_speed_offhand,accuracy_offhand]
smg_skill_offhand.SkillEffectDefinitions = [weapon_damage_offhand,reload_speed_offhand,accuracy_offhand]
sniper_skill_offhand.SkillEffectDefinitions = [weapon_damage_offhand,reload_speed_offhand,fire_rate_offhand, accuracy_max_offhand, accuracy_idle_offhand]
launcher_skill_offhand.SkillEffectDefinitions = [weapon_damage_offhand,reload_speed_offhand,accuracy_offhand]

attr_def = find_class("AttributeInitializationDefinition").ClassDefaultObject
impossible_condidtion = construct_object("ChallengeConditionDefinition", find_class("ChallengeConditionDefinition").ClassDefaultObject)
impossible_condidtion.StatId = "STAT_PLAYER_AREAS_DISCOVERED"
impossible_condidtion.TargetValue = 9999999
shotgun_challenge = construct_object("ChallengeDefinition", find_class("ChallengeDefinition").ClassDefaultObject, "shotgun_challenge")
shotgun_challenge.Levels = [make_struct("ConditionLevel", ConditionDefinitions=[impossible_condidtion])]
shotgun_challenge.ChallengeName = "Shotgun Proficiency"
new_category = construct_object("ChallengeCategoryDefinition", shotgun_challenge)
new_category.CategoryName = "Weapon Proficiencies"
new_category.SortWeight = 500
shotgun_challenge.ChallengeCategoryDef = new_category
shotgun_challenge.ChallengeType = 0
shotgun_challenge.bSecret = False

assault_rifle_challenge = construct_object("ChallengeDefinition", shotgun_challenge, "assault_rifle_challenge", template_obj=shotgun_challenge)
assault_rifle_challenge.ChallengeName = "Assault Rifle Proficiency"

pistol_challenge  = construct_object("ChallengeDefinition", shotgun_challenge, "pistol_challenge", template_obj=shotgun_challenge)
pistol_challenge.ChallengeName = "Pistol Proficiency"

smg_challenge  = construct_object("ChallengeDefinition", shotgun_challenge, "smg_challenge", template_obj=shotgun_challenge)
smg_challenge.ChallengeName = "Sub-Machine Gun Proficiency"

sniper_challenge  = construct_object("ChallengeDefinition", shotgun_challenge, "sniper_challenge", template_obj=shotgun_challenge)
sniper_challenge.ChallengeName = "Sniper Rifle Proficiency"

launcher_challenge  = construct_object("ChallengeDefinition", shotgun_challenge, "launcher_challenge", template_obj=shotgun_challenge)
launcher_challenge.ChallengeName = "Launcher Proficiency"

challenges = [
    pistol_challenge,
    smg_challenge,
    shotgun_challenge,
    assault_rifle_challenge,
    sniper_challenge,
    launcher_challenge,
]

challenge_list = find_object('PlayerChallengeListDefinition', 'GD_Challenges.ChallengeList.List')
challenge_list.ObjectFlags |= 0x4000
challenge_names = []
for challenge in challenges:
    challenge_list.PlayerChallenges.append(challenge)
    challenge.ObjectFlags |= 0x4000
    challenge_names.append(challenge.ChallengeName)

base_skill = find_class("Skill").ClassDefaultObject

def show_reward_message(msg: str, pc:UObject) -> None:
    hud_movie = pc.GetHUDMovie()

    if hud_movie is None:
        return

    hud_movie.SingleArgInvokeS("p1.badassToken.gotoAndStop", "stop")
    hud_movie.SingleArgInvokeS("p1.badassToken.gotoAndPlay", "go")

    hud_movie.SingleArgInvokeS("p1.badassToken.inner.gotoAndStop", "token")


    hud_movie.PlayUISound("RewardCustomization")

    hud_movie.SetVariableString("p1.badassToken.inner.dispText.text", msg)
    return

def get_level_from_xp(xp) -> int:
    if xp <= 0:
        return 0  
    
    current_level:int = -1
    for value in xp_table.values():
        if xp < value:
            return current_level
        else:
            current_level += 1

    return current_level

def get_percent_finished(weapon_type: str) -> int:
    current_xp = weapon_types[weapon_type]
    level = get_level_from_xp(current_xp)

    xp_current_level = xp_table[level]
    xp_next_level = xp_table[level + 1]

    progress = current_xp - xp_current_level
    total = xp_next_level - xp_current_level
    
    return int((progress / total) * 100)

def activate_skill(pc:UObject, weapon_type:str) -> None:
    for skill in get_pc().WorldInfo.Game.GetSkillManager().ActiveSkills:
        if skill.Definition in all_prof_skills:
            skill.Deactivate()

    skill_index = list(weapon_types.keys()).index(weapon_type)
    pc.ServerActivateSkill(all_prof_skills[skill_index], None, get_level_from_xp(weapon_types[weapon_type]))
    return

def activate_skill_offhand(pc:UObject, weapon_type:str) -> None:
    if not oidZerker.value:
        return

    for skill in get_pc().WorldInfo.Game.GetSkillManager().ActiveSkills:
        if skill.Definition in all_prof_skills_offhand:
            skill.Deactivate()

    skill_index = list(weapon_types.keys()).index(weapon_type)
    pc.ServerActivateSkill(all_prof_skills_offhand[skill_index], None, get_level_from_xp(weapon_types[weapon_type]))
    return


@hook("WillowGame.WillowGameInfo:AwardCombatExperience", Type.PRE)
def KilledEnemy(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    if not args.KillerWPC:
        return

    if args.KillerWPC.Pawn and args.KillerWPC.Pawn.Class.Name == "WillowPlayerPawn" and args.KillerWPC.Pawn.Weapon:
        global weapon_types
        xp_amount = args.TotalExpPoints
        if args.KillerWPC.Pawn.OffhandWeapon:
            offhand = args.KillerWPC.Pawn.OffhandWeapon.DefinitionData.WeaponTypeDefinition.Typename
            xp_amount = round(xp_amount / 2)
            pre_xp_level = get_level_from_xp(weapon_types[offhand])
            if pre_xp_level < 50 or not oidGradeCap.value:
                weapon_types[offhand] += xp_amount
                post_xp_level = get_level_from_xp(weapon_types[offhand])
                if post_xp_level > pre_xp_level:
                    activate_skill_offhand(args.KillerWPC, offhand)
                    offhand = "SMG" if offhand == "Sub-Machine Gun" else offhand
                    show_reward_message(f"{offhand} Proficiency: Level {post_xp_level}", args.KillerWPC)

        weapon_type = args.KillerWPC.Pawn.Weapon.DefinitionData.WeaponTypeDefinition.Typename
        pre_xp_level = get_level_from_xp(weapon_types[weapon_type])
        if pre_xp_level < 50 or (not oidGradeCap.value and pre_xp_level < 80):
            weapon_types[weapon_type] += xp_amount
            post_xp_level = get_level_from_xp(weapon_types[weapon_type])
            if post_xp_level > pre_xp_level:
                activate_skill(args.KillerWPC, weapon_type)
                weapon_type = "SMG" if weapon_type == "Sub-Machine Gun" else weapon_type
                show_reward_message(f"{weapon_type} Proficiency: Level {post_xp_level}", args.KillerWPC)

    return 


@hook("WillowGame.WillowPlayerController:NotifyChangedWeapon", Type.PRE)
def NotifyChangedWeapon(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    if not args.NewWeapon:
        if args.bOffHandWeapon:
            for skill in get_pc().WorldInfo.Game.GetSkillManager().ActiveSkills:
                if skill.Definition in all_prof_skills_offhand:
                    skill.Deactivate()
        else:
            for skill in get_pc().WorldInfo.Game.GetSkillManager().ActiveSkills:
                if skill.Definition in all_prof_skills:
                    skill.Deactivate()
        return

    weapon_type = args.NewWeapon.DefinitionData.WeaponTypeDefinition.Typename
    if weapon_type not in weapon_types:
        return

    if not args.bOffHandWeapon:
        activate_skill(obj, weapon_type)
    else:
        activate_skill_offhand(obj, weapon_type)
    return


@hook("WillowGame.ChallengesPanelGFxObject:SetChallengeDescription", Type.PRE)
def SetChallengeDescription(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    if args.ChallengeName in challenge_names:
        ChallengeName = args.ChallengeName
        current_weapon = str(args.ChallengeName).split(f" Proficiency")[0]
        skill_index = list(weapon_types.keys()).index(current_weapon)
        weapon_level = get_level_from_xp(weapon_types[current_weapon])

        ChallengeDescription= f'Get kills while holding a {current_weapon}.'

        first_value = abs(base_skill.CalculateModifierValueFromDefinitionEffectArray(all_prof_skills[skill_index], 0, weapon_level, None)) * 100
        second_value = abs(base_skill.CalculateModifierValueFromDefinitionEffectArray(all_prof_skills[skill_index], 1, weapon_level, None)) * 100
        third_value = abs(base_skill.CalculateModifierValueFromDefinitionEffectArray(all_prof_skills[skill_index], 2, weapon_level, None)) * 100

        if current_weapon == "Sniper Rifle" or current_weapon == "Shotgun":
            third_presentation = "Rate of Fire"
        else:
            third_presentation = "Accuracy"

        third_value = math.ceil(third_value) if third_presentation != "Accuracy" else round(third_value)
        ChallengeLevels= f'<font color="#D27E02">Damage: +{math.ceil(first_value)}%<br>Reload Speed: +{math.ceil(second_value)}%<br>{third_presentation}: +{third_value}%</font>'
        
        if current_weapon == "Sniper Rifle":
            forth_value = abs(base_skill.CalculateModifierValueFromDefinitionEffectArray(all_prof_skills[skill_index], 3, weapon_level, None)) * 100
            fifth_value = abs(base_skill.CalculateModifierValueFromDefinitionEffectArray(all_prof_skills[skill_index], 4, weapon_level, None)) * 100
            ChallengeLevels += f'<font color="#D27E02"><br>Accuracy: +{round(forth_value)}%<br>Stability: +{math.ceil(fifth_value)}%</font>'

        RewardHeader = "Next Level:"
        Reward = f'{xp_table[weapon_level + 1] - int(weapon_types[current_weapon]):,} XP'
        with prevent_hooking_direct_calls():
            func(ChallengeName, ChallengeDescription, ChallengeLevels, RewardHeader, Reward)
            return Block
  
  
@hook("WillowGame.GFxTextListContainer:AddDataEntry", Type.PRE)
def AddDataEntry(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    if args.Entry in challenges:
        with prevent_hooking_direct_calls():
            weapon_type = str(args.Entry.ChallengeName.split(f" Proficiency")[0])
            current_level = get_level_from_xp(weapon_types[weapon_type])
            if current_level < 50 or (not oidGradeCap.value and current_level < 80):
                percent_finished = get_percent_finished(weapon_type)
            else:
                percent_finished = 100
            func(args.Entry,
                 f'{args.Entry.ChallengeName} % {percent_finished} % {current_level} % 0',
                 args.UnselectedTextColor,
                 args.IconFrameLabel)
            return Block

def on_save() -> None:
    saved_xp.value = weapon_types
    return

def on_load() -> None:
    global weapon_types
    weapon_types = saved_xp.value

    for challenge in challenges:
        if not get_pc().PlayerHasChallenge(challenge):
            get_pc().ClientReceiveChallenge(challenge)
    return

def cap_change(option, new_value):
    new_cap = 50 if new_value else 80
    for skill in all_prof_skills:
        skill.MaxGrade = new_cap
    for skill in all_prof_skills_offhand:
        skill.MaxGrade = new_cap
    return

oidZerker = BoolOption(
    "Offhand Weapon Buffs",
    True,
    "On",
    "Off",
    description=f"Enable or Disable the buffs for sals offhand weapons. Clearly this mod just makes him stronger. \nThis does not affect xp gain while gunzerking."
)

oidGradeCap = BoolOption(
    "Max Proficiency Level",
    True,
    "50",
    "80",
    description=f"Choose what level the proficiencies cap at.",
    on_change=cap_change
)

mod = build_mod()
register_save_options(mod)