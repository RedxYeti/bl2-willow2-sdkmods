from typing import Any 
from mods_base import get_pc, hook, build_mod, keybind, SETTINGS_DIR, BoolOption, ButtonOption, SliderOption, SpinnerOption, NestedOption, Game
from unrealsdk import find_object, find_all, load_package, make_struct, construct_object
from unrealsdk.hooks import Type, Block,prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct, IGNORE_STRUCT, WeakPointer
from ui_utils import show_hud_message, show_chat_message
from coroutines import start_coroutine_tick, WaitForSeconds

import json
import os
from random import randint, choice

if Game.get_current() in [Game.BL2, Game.AoDK]:
    char_classes = [
        "GD_Assassin.Character.CharClass_Assassin",
        "GD_Mercenary.Character.CharClass_Mercenary",
        "GD_Siren.Character.CharClass_Siren",
        "GD_Soldier.Character.CharClass_Soldier",
        "GD_Tulip_Mechromancer.Character.CharClass_Mechromancer",
        "GD_Lilac_PlayerClass.Character.CharClass_LilacPlayerClass",
    ]

    char_packs = [
        "GD_Assassin_Streaming_SF",
        "GD_Mercenary_Streaming_SF",
        "GD_Siren_Streaming_SF",
        "GD_Soldier_Streaming_SF",
        "GD_Tulip_Mechro_Streaming_SF",
        "GD_Lilac_Psycho_Streaming_SF",
    ]

    char_names = [
        "Zer0",
        "Salvador",
        "Maya",
        "Axton",
        "Gaige",
        "Krieg"
    ]
else:
    char_classes = [
        'GD_Enforcer.Character.CharClass_Enforcer',
        'GD_Gladiator.Character.CharClass_Gladiator',
        'GD_Lawbringer.Character.CharClass_Lawbringer',
        'GD_Prototype.Character.CharClass_Prototype',
        'Crocus_Baroness.Character.CharClass_Baroness',
        'Quince_Doppel.Character.charclass_doppelganger',
    ]

    char_packs = [
        "GD_Enforcer_Streaming_SF",
        "GD_Gladiator_Streaming_SF",
        "GD_Lawbringer_Streaming_SF",
        "GD_Prototype_Streaming_SF",
        "Crocus_Baroness_Streaming_SF",
        "Quince_Doppel_Streaming_SF",
    ]

    char_names = [
        "Wilhelm",
        "Athena",
        "Nisha",
        "Claptrap",
        "Aurelia",
        "Jack"
    ]

char_index:int = 0
current_save_id:str = ""
half_random_chars:list[int] = []

health_percent:float = 0
shield_percent:float = 0
shield_was_regen:bool = False
bleedout_time:float = 0
injured_time:float = 0
former_held_weapon: WeakPointer | None = None
former_weapon_slot:int = 0

sg: WeakPointer | None = None
location:WrappedStruct | None = None
rotation:WrappedStruct | None = None
velocity:WrappedStruct | None = None

swap_time:int = 0
mid_swap:bool = False
currently_swapping:bool = False 


def save_game(pc) -> None:
    pc.PlayersToSave.append(pc)
    pc.SavePlayer(pc)


@hook("WillowGame.WillowPlayerController:ReturnToTitleScreen", Type.PRE)
def ClassSwap_ReturnToTitleScreen(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    global mid_swap
    mid_swap = False
    ClassSwap_InitializeWorldMissionState.disable()
    ClassSwap_SaveGame.disable()
    ClassSwap_SpawnPlayerMovie.disable()
    

mission_state_calls:int = 0
@hook("WillowGame.WillowPlayerController:InitializeWorldMissionState", Type.PRE)
def ClassSwap_InitializeWorldMissionState(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    global mission_state_calls
    mission_state_calls += 1
    if mission_state_calls >= 2:
        mission_state_calls = 0
        ClassSwap_InitializeWorldMissionState.disable()
    return Block


@hook("WillowGame.WillowSaveGameManager:SaveGame", Type.PRE)
def ClassSwap_ManagerSaveGame(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    global current_save_id
    current_save_id = str(args.Filename).strip(".sav")


@hook("WillowGame.WillowPlayerController:SaveGame", Type.PRE)
def ClassSwap_SaveGame(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    ClassSwap_SaveGame.disable()
    return Block


@hook("WillowGame.WillowHUD:CreateWeaponScopeMovie", Type.POST)
def ClassSwap_SpawnPlayerMovie_FirstLoad(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    ClassSwap_SpawnPlayerMovie_FirstLoad.disable()
    save_game(get_pc())
    if current_save_id:
        load_loadout(get_pc())


def regen_shield():
    global mid_swap
    wait_for_shield = True
    while wait_for_shield:
        yield WaitForSeconds(0.2)
        pc = get_pc()
        if shield_was_regen:
            pc.Pawn.ShieldArmor.Data.PoolIdleDelayStartTime = 0
        wait_for_shield = False
        mid_swap = False


@hook("WillowGame.WillowPlayerController:ReturnToTitleScreen")
def ClassSwap_ReturnToTitleScreen_SwapBlock(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    if mid_swap:
        show_chat_message("Let the swap finish before quitting out!","VH Randomizer")
        return Block

@hook("WillowGame.WillowGameInfo:InitiateTravel")
def ClassSwap_InitiateTravel(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    if mid_swap:
        show_chat_message("Let the swap finish before traveling!","VH Randomizer")
        return Block


@hook("WillowGame.WillowHUD:CreateWeaponScopeMovie", Type.PRE)
def ClassSwap_SpawnPlayerMovie(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    global mid_swap
    ClassSwap_SpawnPlayerMovie.disable()
    pc = get_pc()

    if shield_percent > 0:
        pc.Pawn.SetShieldStrength(pc.Pawn.GetMaxShieldStrength() * shield_percent)
    else:
        pc.Pawn.SetShieldStrength(0)
    pc.Pawn.SetHealth(pc.Pawn.GetMaxHealth() * health_percent)

    if char_index == 5 and Game.get_current() in [Game.BL2, Game.AoDK]:
        Skill_PsychoCooldown = find_object('SkillDefinition', 'GD_Lilac_SkillsBase.ActionSkill.Skill_PsychoCooldown')
        pc.ServerActivateSkill(Skill_PsychoCooldown)

    save_game(pc)
    save_game(pc)

    if injured_time:
        pc.Pawn.flInjuredTargetedTime = injured_time
    if bleedout_time:
        pc.Pawn.TotalBleedoutTime = bleedout_time


    if velocity.X != 0 or velocity.Y != 0:#type: ignore
        pc.Pawn.AddVelocity(velocity, IGNORE_STRUCT, None, None)
        
    if former_held_weapon():#type: ignore
        pc.EquipWeaponFromSlot(former_weapon_slot)

    show_hud_message("VH Randomizer", f"New Character: {char_names[char_index]}", 3)
    mid_swap = False
    start_coroutine_tick(regen_shield())
    ClassSwap_InitializeWorldMissionState.disable()


def dissolve_dead_pawn(pawn_ptr):
    do_dissolve = True
    while do_dissolve:
        yield WaitForSeconds(6.5)
        if pawn_ptr():
            pawn = pawn_ptr()
            pawn.bKilledByTechEffect = True
            pawn.MyDeathDef.bUseCodeDrivenBodyDissolve = True
            willow_globals = get_pc().GetWillowGlobals()
            kill_vol = willow_globals.GetGlobalsDefinition().DigistructCoordinatedEffectKillVolume
            new_kill = construct_object("CoordinatedEffectDefinition", pawn, template_obj=kill_vol)
            new_kill.AudioEffects = []
            willow_globals.GetEffectCoordinator().PushEffect(pawn, new_kill, pawn)
            pawn.UpdateAndDestroyNonVisibleActor(pawn, 2, 2, "Destroy")
        do_dissolve = False

    
@hook("WillowGame.WillowPlayerController:NotifyReadyToLoadPendingSavegame", Type.POST)
def ClassSwap_NotifyReadyToLoadPendingSavegame(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    ClassSwap_NotifyReadyToLoadPendingSavegame.disable()
    ClassSwap_SpawnPlayerMovie.enable()

    pc = get_pc()

    load_loadout(pc)

    pc.Pawn.Location = location
    pc.Pawn.SetViewRotation(rotation)
    
    pc.WorldInfo.Game.bBossesRegenHealthOnReset = True

    for pawn in find_all("WillowPlayerPawn"):
        if pawn != pawn.Class.ClassDefaultObject and not pawn.Controller and "Loader" in str(pawn):
            pawn.Behavior_RegisterTargetable(True)
            if oidSillyRagdolls.value:
                if velocity.Z == 0:#type:ignore
                    pawn.AddVelocity(make_struct("Vector",X=velocity.X, Y=velocity.Y, Z=250), IGNORE_STRUCT, None, None)#type:ignore
                pawn.InjuredDeadState = 3
                pawn.ReplicatedEvent('InjuredDeadState')
                silly_speen = make_struct("Vector", X=randint(-5000,5000), Y=randint(-5000,5000), Z=randint(-5000,5000))
                pawn.Mesh.SetRBAngularVelocity(silly_speen, True)
                start_coroutine_tick(dissolve_dead_pawn(WeakPointer(pawn)))
            else:
                pawn.UpdateAndDestroyNonVisibleActor(pawn, 0.1, 0.1, "Destroy")


@hook("WillowGame.WillowPlayerController:SwitchPlayerClass", Type.PRE)
def ClassSwap_SwitchPlayerClass(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction):
    
    ClassSwap_SwitchPlayerClass.disable()
    ClassSwap_NotifyReadyToLoadPendingSavegame.enable()

    load_package(char_packs[char_index])

    global sg, location
    if args.NewPlayerClass != obj.PlayerClass:
        obj.bLoadingCharacterPackageForClassSwitch = False
    
    obj.PlayerClass = args.NewPlayerClass
    obj.CharacterClass = obj.PlayerClass
    loaded_pawn = obj.GetWillowGlobals().GetPlayerPawnDataManager().FindAlreadyLoadedObject(obj.PlayerClass.PawnArchetypePath)

    if loaded_pawn != None:
        obj.ClientNotifyClassChanged(obj.PlayerClass)
        obj.ApplyCharacterClassStartingValues(obj.CharacterClass)

        obj.Pawn.InvManager.DiscardInventory(True)
        obj.Pawn.Destroyed()
        obj.Pawn = None
        
        obj.bRespawnFromClassChange = False
        obj.WorldInfo.Game.bRestartLevel = False
        obj.WorldInfo.Game.RestartPlayer(obj)
        obj.WorldInfo.Game.bRestartLevel = False

        if obj.Pawn:
            sg().PlayerClassDefinition = find_object("PlayerClassDefinition", char_classes[char_index])#type: ignore
            obj.FinishSaveGameLoad(sg(), 1, True, False, True, True)#type: ignore
            obj.PlayerReplicationInfo.bSaveGameLoaded = True
            obj.ClientSetHUD(obj.WorldInfo.Game.HUDType)
            obj.PendingClassSwitchPawnArchetype = None
    return Block


def fix_sal() -> None:
    try:
        broken_branch = find_object('SkillTreeBranchDefinition', 'GD_Mercenary_Skills.SkillTree.Branch_Brawn')
        broken_branch.ObjectFlags |= 0x4000
    except:
        load_package("GD_Mercenary_Streaming_SF")
        broken_branch = find_object('SkillTreeBranchDefinition', 'GD_Mercenary_Skills.SkillTree.Branch_Brawn')
        broken_branch.ObjectFlags |= 0x4000
    if len(broken_branch.Tiers[2].Skills) == 4:
        del broken_branch.Tiers[2].Skills[3]


def save_loadout(pc:UObject):
    if not current_save_id or current_save_id == "Save0000" or current_save_id.endswith(".bak"):
        return
    main_dir = os.path.join(SETTINGS_DIR, "VHRandomizer")
    loadouts_dir = os.path.join(main_dir, current_save_id)

    if not os.path.exists(loadouts_dir):
        os.makedirs(loadouts_dir)

    name = pc.GetCharacterClassDefaultName()
    PST = pc.PlayerSkillTree
    loadout = {}

    if name == "Salvador":
        fix_sal()

    for skill in PST.Skills:
        if skill.Definition == PST.GetActionSkill():
            loadout["ActionSkill"] = (skill.Grade == 1)
            break

    loadout["ActionSkillCooldown"] = 0
    if loadout["ActionSkill"]:
        loadout["ActionSkillCooldown"] = pc.SkillCooldownPool.Data.GetCurrentValue()

    for Branch in PST.Branches:
        if Branch.Definition.BranchName:
            loadout[Branch.Definition.BranchName] = {}
            for Tier in Branch.Definition.Tiers:
                for Skill in Tier.Skills:
                    _, skill_state = PST.GetSkillState(Skill, IGNORE_STRUCT)
                    if skill_state.SkillDefinition:
                        loadout[Branch.Definition.BranchName][Skill.SkillName] = skill_state.SkillGrade

    loadout["Anarchy"] = 0
    if name == "Gaige":
        anarchy = find_object('DesignerAttributeDefinition', 'GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks')
        stacks, *_ = anarchy.GetValue(pc)
        loadout["Anarchy"] = stacks

    loadout["Critical"] = 0
    if name == "Zero":
        for skill in pc.WorldInfo.Game.GetSkillManager().ActiveSkills:
            if skill.Definition.Name == "CriticalAscention_Stack":
                loadout["Critical"] += 1

    loadout["Bloodlust"] = 0
    if name == "Krieg":
        bloodlust = find_object('DesignerAttributeDefinition', 'GD_Lilac_Skills_Bloodlust.Attributes.Att_Bloodlust_StackCount')
        stacks, *_ = bloodlust.GetValue(pc)
        loadout["Bloodlust"] = stacks
        

    loadout["QuickSelects"] = {}
    inv_manager = pc.Pawn.InvManager

    loadout["HeldWeapon"] = [0,0]

    for i in range(4):
        slot_num = i + 1
        weapon_in_slot = inv_manager.GetWeaponInSlot(slot_num)
        if weapon_in_slot:
            loadout["QuickSelects"][weapon_in_slot.DefinitionData.UniqueID] = slot_num
            if weapon_in_slot == pc.Pawn.Weapon:
                loadout["HeldWeapon"] = [slot_num, weapon_in_slot.DefinitionData.UniqueID]
        else:
            loadout["QuickSelects"][f"None_{i + 1}"] = slot_num

    loadout["Shield"] = 0
    loadout["Artifact"] = 0
    loadout["GrenadeMod"] = 0
    loadout["ClassMod"] = 0

    for item in list(pc.Pawn.EquippedItems):
        if item:
            match item.Class.Name:
                case "WillowShield":
                    loadout["Shield"] = item.DefinitionData.UniqueId

                case "WillowArtifact":
                    loadout["Artifact"] = item.DefinitionData.UniqueId

                case "WillowGrenadeMod":
                    loadout["GrenadeMod"] = item.DefinitionData.UniqueId

                case "WillowClassMod":
                    loadout["ClassMod"] = item.DefinitionData.UniqueId

    new_loadout = os.path.join(loadouts_dir, f"{name}.json")
    with open(new_loadout, "w") as file:
        json.dump(loadout, file, indent=4)


def find_gear_from_serial(serial:int, gear_list:list) -> UObject | None:
    for gear in gear_list:
        if gear.DefinitionData.UniqueID == serial:
            return gear
    return None


def check_item_equip(serial:int, item:UObject, item_list:list[UObject], inv_manager:UObject):
    gear = find_gear_from_serial(serial, item_list)
    if gear:
        if gear.bReadied:
            return

        if item.DefinitionData.UniqueID != serial:
            inv_manager.ReadyBackpackInventory(gear)
            
    elif item:
        inv_manager.InventoryUnreadied(item, True)


def load_loadout(pc:UObject):
    if not current_save_id or current_save_id == "Save0000" or current_save_id.endswith(".bak"):
        return
    main_dir = os.path.join(SETTINGS_DIR, "VHRandomizer")
    loadouts_dir = os.path.join(main_dir, current_save_id)
    class_json = os.path.join(loadouts_dir, f"{pc.GetCharacterClassDefaultName()}.json")

    if not os.path.exists(class_json):
        save_loadout(pc)

    with open(class_json, 'r') as loadout_file:
        char_loadout = json.load(loadout_file)

    name = pc.GetCharacterClassDefaultName()

    if name == "Salvador":
        fix_sal()


    cooldown = char_loadout["ActionSkillCooldown"]

    PST = pc.PlayerSkillTree
    if char_loadout["ActionSkill"]:
        pc.SkillCooldownPool.Data.SetCurrentValue(cooldown)
        pc.ServerUpgradeSkill(PST.GetActionSkill())

    for Branch in PST.Branches:
        if Branch.Definition.BranchName:
            for Tier in Branch.Definition.Tiers:
                for Skill in Tier.Skills:
                    if char_loadout[Branch.Definition.BranchName][Skill.SkillName] > 0:
                        for i in range(char_loadout[Branch.Definition.BranchName][Skill.SkillName]):
                            pc.ServerUpgradeSkill(Skill)


    if name == "Gaige":
        try:
            anarchy = find_object('DesignerAttributeDefinition', 'GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks')
            anarchy.ObjectFlags |= 0x4000
        except:
            load_package("GD_Tulip_Mechro_Streaming_SF")
            anarchy = find_object('DesignerAttributeDefinition', 'GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks')
            anarchy.ObjectFlags |= 0x4000
        anarchy.SetAttributeBaseValue(pc, char_loadout["Anarchy"])


    if name == "Zero":
        load_package("GD_Assassin_Streaming_SF")
        try:
            critical = find_object("SkillDefinition", "GD_Assassin_Skills.Sniping.CriticalAscention_Stack")
            critical.ObjectFlags |= 0x4000
        except:
            critical = find_object("SkillDefinition", "GD_Assassin_Skills.Sniping.CriticalAscention_Stack")
            critical.ObjectFlags |= 0x4000
        for i in range(char_loadout["Critical"]):
            pc.WorldInfo.Game.GetSkillManager().ActivateSkill(pc, critical)


    if name == "Krieg":
        try:
            bloodlust = find_object('DesignerAttributeDefinition', 'GD_Lilac_Skills_Bloodlust.Attributes.Att_Bloodlust_StackCount')
            bloodlust.ObjectFlags |= 0x4000
        except:
            load_package("GD_Lilac_Psycho_Streaming_SF")
            bloodlust = find_object('DesignerAttributeDefinition', 'GD_Lilac_Skills_Bloodlust.Attributes.Att_Bloodlust_StackCount')
            bloodlust.ObjectFlags |= 0x4000
        bloodlust.SetAttributeBaseValue(pc, char_loadout["Bloodlust"])

    inv_manager = pc.Pawn.InvManager

    _, weapon_list =  pc.Pawn.InvManager.GetWeaponList([], True, True)

    if not oidSharedWeapons.value:
        for weapon in weapon_list:
            weapon_serial = str(weapon.DefinitionData.UniqueID)
            if weapon_serial in char_loadout["QuickSelects"].keys():
                inv_manager.ReadyBackpackInventory(weapon, char_loadout["QuickSelects"][weapon_serial])

        for key,slot_num in char_loadout["QuickSelects"].items():
            gear_in_slot = inv_manager.GetWeaponInSlot(slot_num)
            if gear_in_slot:
                if str(key).startswith("None") or gear_in_slot.DefinitionData.UniqueID != gear_in_slot.DefinitionData.UniqueID:
                    inv_manager.InventoryUnreadied(inv_manager.GetWeaponInSlot(slot_num), True)

    


    global former_held_weapon, former_weapon_slot
    weapon_slot, weapon_serial = char_loadout["HeldWeapon"]
    former_held_weapon = WeakPointer(find_gear_from_serial(weapon_serial, weapon_list))
    if former_held_weapon():
        former_weapon_slot = weapon_slot


    equipped_items = pc.Pawn.EquippedItems
    _, item_list =  pc.Pawn.InvManager.GetItemList([])
    if Game.get_current() == Game.TPS:
        for item in inv_manager.Backpack:
            if hasattr(item.DefinitionData, "ItemDefinition"):
                item_list.append(item)
        for item in pc.Pawn.EquippedItems:
            if item:
                item_list.append(item)


    if not oidSharedShield.value:
        check_item_equip(char_loadout["Shield"], equipped_items[0], item_list, inv_manager)

    if not oidSharedGrenade.value:
        check_item_equip(char_loadout["GrenadeMod"], equipped_items[1], item_list, inv_manager)

    if not oidSharedArtifact.value:
        check_item_equip(char_loadout["Artifact"], equipped_items[3], item_list, inv_manager)

    gear = find_gear_from_serial(char_loadout["ClassMod"], item_list)
    if gear:
        inv_manager.ReadyBackpackInventory(gear)
   
    weapon_list = []
    item_list = []
    inv_manager.UpdateBackpackInventoryCount()


def pick_next_char(pc:UObject) -> int:
    try:
        current_char_index = char_names.index(pc.GetCharacterClassDefaultName())
    except:
        current_char_index = 0#zer0
    next_char_index = 0
    if oidSwapType.value == "Full Random":
        next_char_index = randint(0,5)
        next_char_index = 0
        while next_char_index == current_char_index:
            next_char_index = randint(0,5)
    elif oidSwapType.value == "Half Random":
        global half_random_chars
        if not len(half_random_chars):
            half_random_chars = [0,1,2,3,4,5]
            half_random_chars.remove(current_char_index)
        next_char_index = choice(half_random_chars)
        half_random_chars.remove(next_char_index)
    else:
        next_char_index = current_char_index + 1
        if next_char_index >= 6:
            next_char_index = 0

    return next_char_index

def do_swap():
    global sg, location, rotation, char_index, velocity, health_percent, shield_percent, shield_was_regen, bleedout_time, injured_time, mid_swap
    mid_swap = True
    pc = get_pc()

    location = pc.Pawn.Location
    rotation = pc.Pawn.GetViewRotation()
    pc.Pawn.SetPhysics(2)
    velocity = make_struct("Vector",X=pc.Pawn.Velocity.X,Y=pc.Pawn.Velocity.Y,Z=pc.Pawn.Velocity.Z)

    if pc.Pawn.GetShieldStrength() > 0:
        shield_percent = pc.Pawn.GetShieldStrength() / pc.Pawn.GetMaxShieldStrength()
    else:
        shield_percent = 0

    if pc.Pawn.ShieldArmor.Data:
        shield_was_regen = pc.Pawn.ShieldArmor.Data.WasRegenerating

    health_percent = pc.Pawn.GetHealth() / pc.Pawn.GetMaxHealth()

    if pc.Pawn.TotalBleedoutTime > 0:
        bleedout_time = pc.Pawn.TotalBleedoutTime
    if pc.Pawn.flInjuredTargetedTime:
        injured_time = pc.Pawn.flInjuredTargetedTime

    save_game(pc)
    sg = WeakPointer(pc.GetCachedSaveGame())

    save_loadout(pc)
    char_index = pick_next_char(pc)
    NewPlayerClass = find_object("PlayerClassDefinition", char_classes[char_index])

    if not oidSharedWeapons.value:
        _, weapon_list =  pc.Pawn.InvManager.GetWeaponList([], True, True)
        for weapon in weapon_list:
            if weapon.bReadied:
                pc.Pawn.InvManager.InventoryUnreadied(weapon, True)
                weapon.QuickSelectSlot = 0
        weapon_list = []
    save_game(pc)

    pc.PlayerReplicationInfo.GeneralSkillPoints += pc.ResetSkillTree(True)
    pc.bLoadingCharacterPackageForClassSwitch = True
    pc.WorldInfo.Game.bBossesRegenHealthOnReset = False
    ClassSwap_SwitchPlayerClass.enable()
    ClassSwap_SaveGame.enable()
    ClassSwap_InitializeWorldMissionState.enable()
    pc.GetWillowGlobals().GetPlayerPawnDataManager().LoadPlayerPawnDataAsync(NewPlayerClass.PawnArchetypePath, pc, NewPlayerClass, pc, 0, 0, 'SwitchPlayerClass')


@keybind("Swap Character")
def new_swap():
    global mid_swap
    pc = get_pc()
    if (not mid_swap
        and pc.GetHUDMovie()
        and not pc.GetThirdPersonMovie()
        and pc.Pawn 
        and not pc.Pawn.IsInjured() 
        and not pc.Pawn.IsDead() 
        and "Vehicle" not in str(pc.Pawn)):
        do_swap()

oidSharedWeapons = BoolOption(
    "Share Weapons",
    True,
    "ON",
    "OFF",
)

oidSharedShield = BoolOption(
    "Share Shield",
    True,
    "ON",
    "OFF",
)

oidSharedArtifact = BoolOption(
    "Share Artifact",
    True,
    "ON",
    "OFF",
)

oidSharedGrenade = BoolOption(
    "Share Grenade",
    True,
    "ON",
    "OFF",
)

oidSillyRagdolls = BoolOption(
    "Silly Ragdolls",
    True,
    "ON",
    "OFF",
    description="When the character swaps, it spawns a silly ragdoll of the previous character."
)

oidInterruptAS = BoolOption(
    "Interrupt Action Skills",
    False,
    "ON",
    "OFF",
    description="With this on, it will swap even while your action skill is active."
)

oidMainNest = NestedOption(
    "Character Options",
    [
    oidSharedShield,
    oidSharedArtifact,
    oidSharedGrenade,
    oidSharedWeapons,
    oidSillyRagdolls,
    oidInterruptAS,
    ]
)

def values_check():
    if oidMinSwap.value > oidMaxSwap.value:
        show_hud_message("VH Randomizer","Max Swap Time has to be higher than Min Swap Time. \nPlease lower min swap time.", 3)
        return False
    return True


def swap_routine():
    global swap_time,currently_swapping,mid_swap
    while currently_swapping:
        yield WaitForSeconds(swap_time)
        if not mod_instance.is_enabled or not currently_swapping:
            currently_swapping = False
            return None

        pc= get_pc()
        if (not mid_swap
            and pc.GetHUDMovie()
            and not pc.GetThirdPersonMovie()
            and pc.Pawn 
            and not pc.Pawn.IsInjured() 
            and not pc.Pawn.IsDead() 
            and "Vehicle" not in str(pc.Pawn)):

            if pc.bWasActionSkillRunning:
                if not oidInterruptAS.value:
                    swap_time = 1
                else:
                    swap_time = randint(int(oidMinSwap.value), int(oidMaxSwap.value))
                    do_swap()
            else:
                swap_time = randint(int(oidMinSwap.value), int(oidMaxSwap.value))
                do_swap()
        else:
            swap_time = 1

def _start_swapping(*_):
    global currently_swapping
    currently_swapping = True
    show_chat_message("Swapping Started!", "VH Randomizer")
    start_coroutine_tick(swap_routine())

def _stop_swapping(*_):
    global currently_swapping
    currently_swapping = False
    show_chat_message("Swapping Stopped!", "VH Randomizer")

def slider_values_changed(*_):
    global swap_time
    if oidMinSwap.value < oidMaxSwap.value:
        swap_time = randint(int(oidMinSwap.value), int(oidMaxSwap.value))


oidMinSwap = SliderOption(
    "Minimum Swap Time",
    30,
    1,
    599,
    description="Time in seconds the lowest amount of time between swaps. Recommend stopping the swap before changing.",
    on_change=slider_values_changed
)

oidMaxSwap = SliderOption(
    "Maximum Swap Time",
    180,
    5,
    600,
    description="Time in seconds the highest amount of time between swaps. Recommend stopping the swap before changing.",
    on_change=slider_values_changed
)
oidSwapType = SpinnerOption(
    "Swap Type",
    "Half Random",
    ["Full Random", "Half Random", "Linear"],
    description=("Full Random: No order, just picks a random class every time.\n"
                 "Half Random: Get one of every character before repeating, in a random order.\n" 
                 "Linear: Goes through the list of characters in order.")
)
oidStartButton = ButtonOption(
    "Start Swapping",
    description="Starts the swapping. Only press in one game.",
    on_press=_start_swapping
)
oidStopButton = ButtonOption(
    "Stop Swapping",
    description="Stops the swapping. Only works if you press in the same game you started the swapping.",
    on_press=_stop_swapping
)
        
oidAutoSwapNest = NestedOption(
    "Auto Swap Options",
    [
    oidMinSwap,
    oidMaxSwap,
    oidStartButton,
    oidStopButton,
    ]
)


@keybind("Toggle Auto Swap", description="Toggles Auto Swapping on and off on the fly.")
def pause_swapping():
    global currently_swapping, started_game
    swap_status = "off" if currently_swapping else "on"
    show_hud_message("VH Randomizer", f"Toggling swapping {swap_status}!", 5)
    if currently_swapping:
        _stop_swapping()
    else:
        _start_swapping()


@keybind("Mark All Items", description="Marks equipped items on all characters with a star and unequipped items with an x (theres no x in TPS)")
def drop_all():
    pc = get_pc()
    if pc.Pawn:
        _, weapon_list =  pc.Pawn.InvManager.GetWeaponList([], True, True)
        _, item_list =  pc.Pawn.InvManager.GetItemList([])

        if Game.get_current() == Game.TPS:
            for item in pc.Pawn.InvManager.Backpack:
                if hasattr(item.DefinitionData, "ItemDefinition"):
                    item_list.append(item)
            for item in pc.Pawn.EquippedItems:
                if item:
                    item_list.append(item)

        all_gear = weapon_list + item_list

        main_dir = os.path.join(SETTINGS_DIR, "VHRandomizer")
        loadouts_dir = os.path.join(main_dir, current_save_id)
        all_serials = []
        for char in [ "Zero", "Salvador", "Maya", "Axton", "Gaige", "Krieg", "Wilhelm", "Athena", "Nisha", "Claptrap", "Aurelia", "Jack"]: 
            class_json = os.path.join(loadouts_dir, f"{char}.json")
            if not os.path.exists(class_json):
                continue

            with open(class_json, 'r') as loadout_file:
                char_loadout = json.load(loadout_file)

            for key in char_loadout["QuickSelects"].keys():
                if not str(key).startswith("None"):
                    all_serials.append(int(key))

            if char_loadout["Shield"] != 0:
                all_serials.append(char_loadout["Shield"])

            if char_loadout["Artifact"] != 0:
                    all_serials.append(char_loadout["Artifact"])

            if char_loadout["GrenadeMod"] != 0:
                    all_serials.append(char_loadout["GrenadeMod"])

            if char_loadout["ClassMod"] != 0:
                    all_serials.append(char_loadout["ClassMod"])

        for gear in all_gear:
            if gear.DefinitionData.UniqueID in all_serials or gear.bReadied:
                gear.SetMark(2)
            else:
                if Game.get_current() == Game.TPS:
                    gear.SetMark(1)
                else:
                    gear.SetMark(0)

        show_hud_message("VH Randomizer", "Gear marked!", 3)


mod_options = [oidSwapType, oidMainNest, oidAutoSwapNest]
mod_instance = build_mod(options=mod_options, hooks = [ClassSwap_SpawnPlayerMovie_FirstLoad, ClassSwap_ManagerSaveGame, ClassSwap_InitiateTravel, ClassSwap_ReturnToTitleScreen_SwapBlock])

#TODO
#test critical
#ammo counts?