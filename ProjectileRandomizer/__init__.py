from random import choice
from typing import Any
from mods_base import get_pc, hook, build_mod, ENGINE, Game #type:ignore
from unrealsdk.hooks import Type, add_hook, Block, remove_hook #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct, UClass #type:ignore
from unrealsdk import find_class#type:ignore
import unrealsdk#type:ignore

from .Lists import TPSNames 
from .Options import oidDropWeapons
from .SaveSystem import GetSaveLocation, PrepFiles
from .Functions import save, InitializeFromDefData, InitializeFromItemData, PlayerLoaded, LoadFromDict, GetProjectile, GetFM, DupeObject, UpdateBarrel, UpdateProjectile, PrepProjectileRando, UpdateDelivery
from .Functions import PlayerLoad, LoadFromText, SavePath, PlayerID, Classnames, UniqueIDs, ItemInfoDict, AIPawnProjectiles, AIPawnBeams,  AllFiringModes, AllProjectiles, IsNewGame


ActionSkillStateClass:UClass = find_class("ActionSkillStateExpressionEvaluator")

IsBL2:bool = (Game.get_current() == Game.BL2 | Game.get_current() == Game.AoDK)


@hook("WillowGame.WillowPlayerController:SaveGame", Type.PRE)
def GameSave(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    global PlayerID, SavePath
    PlayerID = obj.GetCachedSaveGame().SaveGameId
    if PlayerID == -1:
        return
    
    Inventory = get_pc().GetPawnInventoryManager()

    for i in range(1,5):
        if Inventory.GetWeaponInSlot(i):
            print(Inventory.GetWeaponInSlot(i).DefinitionData.BarrelPartDefinition)

    PlayerID = obj.GetCachedSaveGame().SaveGameId
    SavePath = GetSaveLocation(PlayerID)

    save(False)
    return


@hook("WillowGame.WillowGFxLobbyLoadCharacter:BeginClose", Type.PRE)
def CharacterChange(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    SaveID = obj.DisplayedCharacterDataList[obj.SelectedDataIndex].SaveDataId
    if SaveID != -1:
        global PlayerID, SavePath, LoadFromText, PlayerLoad
        PlayerID = int(SaveID)
        SavePath = GetSaveLocation(SaveID)
        LoadFromText = True
        PlayerLoad = True
    return



@hook("WillowGame.WillowPlayerController:ReturnToTitleScreen", Type.PRE)
def SaveQuitItems(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    global PlayerLoad, LoadFromText
    PlayerLoad = True
    LoadFromText = True
    save(True)
    return


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST)
def AreaLoaded(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    global AIPawnProjectiles, AIPawnBeams

    AIPawnProjectiles = {'AIPawns': {}}
    AIPawnBeams = {'AIPawnBeams': {}}

    if PlayerLoad:
        PlayerLoaded()
        
    for Pickup in get_pc().GetWillowGlobals().PickupList:
        if Pickup and Pickup.Inventory.Class.Name in Classnames:
            LoadFromDict(Pickup.Inventory, Pickup.Inventory.DefinitionData.UniqueID)
            
    return

@hook("WillowGame.VendingMachineExGFxMovie:Start", Type.PRE)
def CheckVendors(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    global ItemInfoDict
    obj = ENGINE.GamePlayers[0].Actor
    Objects = obj.GetWillowGlobals().ClientInteractiveObjects
    Keys = ItemInfoDict['UniqueIDs'].keys()#type:ignore

    for Object in Objects:

        if Object is None:
            continue

        if  Object.Class.Name != "WillowVendingMachine":
            continue

        VendingMachine = Object
        FeaturedItem = VendingMachine.FeaturedItem
        if VendingMachine.ShopType == 0:
            for item in VendingMachine.ShopInventory:
                if item is not None and item.Class.Name == "WillowWeapon": 
                    if item.DefinitionData.UniqueId not in Keys:
                        InitializeFromDefData(item)
                    else:
                        LoadFromDict(item, item.DefinitionData.UniqueId)

            if FeaturedItem is not None and FeaturedItem.Class.Name == "WillowWeapon": 
                if FeaturedItem.DefinitionData.UniqueId not in Keys:
                    InitializeFromDefData(FeaturedItem)
                else:
                    LoadFromDict(FeaturedItem, FeaturedItem.DefinitionData.UniqueId)


        elif VendingMachine.ShopType == 1:
            for item in VendingMachine.ShopInventory:
                if item is not None and item.Class.Name == "WillowGrenadeMod":
                    if item.DefinitionData.UniqueId not in Keys:
                        InitializeFromItemData(item)
                    else:
                        LoadFromDict(item, item.DefinitionData.UniqueId)
                        
            if FeaturedItem is not None and FeaturedItem.Class.Name == "WillowGrenadeMod":
                if FeaturedItem.DefinitionData.UniqueId not in Keys:
                    InitializeFromItemData(FeaturedItem)
                else:
                    LoadFromDict(FeaturedItem, FeaturedItem.DefinitionData.UniqueId)

    return


@hook("WillowGame.WillowPickup:InventoryAssociated", Type.POST)
def InventoryAssociated(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if not obj.Inventory:
        return

    if obj.Inventory.DefinitionData.UniqueID not in UniqueIDs:
        if obj.Inventory.Class.Name == "WillowWeapon":
            InitializeFromDefData(obj.Inventory)

        elif obj.Inventory.Class.Name == "WillowGrenadeMod":
            InitializeFromItemData(obj.Inventory)
    
    return


#Edits the definition data right before sending it to the ui
@hook("WillowGame.MissionRewardGFxObject:SetUpRewardsPage", Type.PRE)
def MissionReward(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    RewardData = obj.RewardData

    for i in range(2):
        if RewardData.WeaponRewards[i]:
            DefData = RewardData.WeaponRewards[i]
            DefData.BarrelPartDefinition = UpdateBarrel(DefData)

    for i in range(2):
        if RewardData.ItemRewards[i] and 'GrenadeModDefinition' in str(RewardData.ItemRewards[i].ItemDefinition):
            DefData = RewardData.ItemRewards[i]
            DefData.BarrelPartDefinition = UpdateDelivery(DefData)
            UpdateProjectile(DefData.BarrelPartDefinition.CustomProjectileDefinition)

    obj.RewardData = RewardData
    return


@hook("WillowGame.Behavior_IsObjectPlayer:ApplyBehaviorToContext", Type.PRE)
def Behavior_IsObjectPlayer(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if hasattr(args.ContextObject, "Instigator") and args.ContextObject.Instigator and args.ContextObject.Instigator.Class.Name == "WillowPlayerPawn":
        find_class('GearboxFramework.BehaviorKernel').ClassDefaultObject.ActivateBehaviorOutputLink(args.KernelInfo, 0)
    return


@hook("WillowGame.Behavior_AIThrowProjectileAtTarget:ApplyBehaviorToContext", Type.PRE)
def CombatProjectile(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    global AIPawnProjectiles, AllProjectiles
    PID = args.ContextObject.ConsumerHandle.PID

    if PID not in AIPawnProjectiles['AIPawns'].keys():
        NewProjectile = choice(AllProjectiles)
        NewProjectile = GetProjectile(NewProjectile)[1]
        AIPawnProjectiles['AIPawns'][PID] = [NewProjectile]

    obj.ProjectileDef = AIPawnProjectiles['AIPawns'][PID][0]
    return


@hook("WillowGame.Behavior_FireShot:ApplyBehaviorToContext", Type.PRE)
def CombatShot(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    PackageName = str(args.ContextObject.Outer).lower()
    if "bunker" in PackageName or "deathtrap" in PackageName:
        obj.FiringModeDefinition = choice(AllFiringModes)
    return 


@hook("WillowGame.Behavior_FireBeam:ApplyBehaviorToContext", Type.PRE)
def CombatBeam(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    PID = args.ContextObject.ConsumerHandle.PID
    global AIPawnBeams
    if PID not in AIPawnBeams['AIPawnBeams'].keys():
        NewFM = GetFM()
        NewFM = NewFM[0] if NewFM[1] is None else NewFM[1]
        AIPawnBeams['AIPawnBeams'][PID] = [NewFM]

    obj.FiringModeDefinition = AIPawnBeams['AIPawnBeams'][PID][0]
    return


@hook("WillowGame.Behavior_SpawnProjectile:ApplyBehaviorToContext", Type.PRE)
def SpawnedProjectile(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    ClassName = args.ContextObject.Class.Name
    global IsBL2, AllProjectiles
    if not IsBL2:
        if ClassName == "OzSupportDrone":
            return
        ProjName = str(obj.ProjectileDefinition).split("'")[1]
        if ProjName in TPSNames:
            return
        
    if ClassName == "WillowPlayerPawn" or ClassName == "WillowAIPawn":
        NewProjectile = choice(AllProjectiles)
        NewProjectile = DupeObject(NewProjectile, "ProjectileDefinition")
        UpdateProjectile(NewProjectile)
        obj.ProjectileDefinition = NewProjectile

    elif ClassName == "WillowPlayerController" and args.ContextObject.Pawn.IsInjured():
        if args.ContextObject.PlayerClass.Name == "CharClass_LilacPlayerClass":
            obj.ProjectileDefinition = GetProjectile(None)[1]
    return


@hook("WillowGame.Behavior_Conditional:ApplyBehaviorToContext", Type.PRE)
def Behavior_Conditional(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if Game.get_current() == Game.BL2:
        return

    if not args.SelfObject or args.SelfObject.Class.Name != "WillowAIPawn":
        return

    for condition in obj.Conditions:
        if not condition.Condition:
            continue

        if condition.Condition.Class._inherits(ActionSkillStateClass):
            condition.Condition = None
            return
        
    return



@hook("WillowGame.Behavior_AISpawn:SpawnActor", Type.PRE)
def SpawnActor(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if args.ContextObject != get_pc().Pawn:
        return
    
    SpawnerPawn = None
    pawn = ENGINE.GetCurrentWorldInfo().PawnList
    while pawn is not None:
        if pawn.AIClass is not None:
            SpawnerPawn = pawn
            break
        pawn = pawn.NextPawn

    if SpawnerPawn:
        with unrealsdk.hooks.prevent_hooking_direct_calls():
            obj.SpawnActor(SpawnerPawn, args.EffectivePopDef, args.SpawnLocationContext)
    return
    

@hook("WillowGame.WillowAIPawn:PostStartingInventoryAdded", Type.POST)
def PostPawnInventory(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    PawnWeapon = obj.Weapon
    if PawnWeapon is not None:
        DefData = PawnWeapon.DefinitionData
        DefData.BarrelPartDefinition = UpdateBarrel(DefData)
        DupedWeapon = ENGINE.GetCurrentWorldInfo().Spawn(find_class("WillowWeapon"))
        DupedWeapon.InitializeFromDefinitionData(DefData, None, True)

        if PawnWeapon.bDropOnDeath or oidDropWeapons.value:
            DupedWeapon.bDropOnDeath = True
            obj.InvManager.RemoveFromInventory(PawnWeapon)
        else:
            DupedWeapon.bDropOnDeath = False

        DupedWeapon.GiveTo(obj, True)
    return



@hook("WillowGame.WillowVehicle:PostBeginPlay", Type.PRE)
def SpawnVeh(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    global AllFiringModes
    if obj.VehicleDef and obj.VehicleDef.Seats:
        for seat in obj.VehicleDef.Seats:
            if seat.WeaponBalanceDefinition and seat.WeaponBalanceDefinition.InventoryDefinition:
                seat.WeaponBalanceDefinition.InventoryDefinition.DefaultFiringModeDefinition = choice(AllFiringModes)

    return


SanitizeName = lambda InputName: InputName.split('&')[0]
#most of this is from part notifier
@hook("WillowGame.ItemCardGFxObject:SetItemCardEx", Type.PRE)
def SetItemCardEx(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:

    #This function is called whenever an item card is created - exactly when we need to add
    #all the parts text.

    # If we don't actually have an item then there's no need to do anything special
    item = args.InventoryItem
    if item is None:
        return

    # Get the default text and convert it as needed
    text = args.InventoryItem.GenerateFunStatsText()
    if text is None:
        text = ""

    ClassName = item.Class.Name
    if ClassName not in Classnames:
        return

    if ClassName == "WillowWeapon":
        BarrelPart = item.DefinitionData.BarrelPartDefinition
        if BarrelPart is None:
            return

        FiringMode = item.DefinitionData.BarrelPartDefinition.CustomFiringModeDefinition
        if FiringMode is None:
            return
        else:
            Proj = FiringMode.ProjectileDefinition
            FiringModeName = SanitizeName(FiringMode.Name)
            if FiringModeName == "":
                FiringModeName = "Unnamed"
            if "explosive" in text and not IsBL2:
                text += "<br>"
            text += f"<font size='14' color='#CC0000'>Firing Mode:</font> <font size='14' color='#FFFFFF'> {str(FiringModeName)}</font>"
            if Proj is not None:
                text += "<br>"
                ProjName = SanitizeName(Proj.Name)
                text += f"<font size='14' color='#FF8000'>Projectile:</font> <font size='14' color='#FFFFFF'> {str(ProjName)}</font>"
    else:
        Delivery = item.DefinitionData.BetaItemPartDefinition
        if Delivery is None:
            return
        else:
            Proj = Delivery.CustomProjectileDefinition
            ProjName = SanitizeName(Proj.Name)
            text += f"<font size='14' color='#FF8000'>Projectile:</font> <font size='14' color='#FFFFFF'> {str(ProjName)}</font>"


    # `SetItemCardEx` is actually quite complex, so rather than replicate it, we'll just
    #  write our text, then let the it run as normal, but block it from overwriting the text
    def SetFunStats(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
        remove_hook("WillowGame.ItemCardGFxObject:SetFunStats", Type.PRE, "FunStats")
        return Block

    add_hook("WillowGame.ItemCardGFxObject:SetFunStats", Type.PRE, "FunStats", SetFunStats)

    with unrealsdk.hooks.prevent_hooking_direct_calls():
        obj.SetFunStats(text)
    return 


@hook("WillowGame.WillowPlayerController:ClientUnlockAchievement", Type.PRE)
def AchievementBlock(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    return Block


@hook("WillowGame.WillowScrollingListDataProviderFrontEnd:HandleClick", Type.PRE)
def ButtonPressed(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    if args.EventID == 0 or args.EventID == 6:
        if args.EventID == 6:
            global IsNewGame
            Functions.IsNewGame = True
        PrepProjectileRando()
        ButtonPressed.disable()
    return


build_mod(on_enable=PrepFiles)

"""
TODO
ProjectileDefinition'GD_Orchid_RaidShaman.Projectile.Projectile_Orchid_ShamanOrb'
sapperbomb dummy
bp_probe_plasma
"""