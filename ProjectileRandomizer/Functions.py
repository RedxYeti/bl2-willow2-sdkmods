from random import choice, uniform, randint
from typing import Any
from mods_base import get_pc, ENGINE, Game #type:ignore
from unrealsdk.hooks import Type, remove_hook 
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct, WeakPointer
from unrealsdk import find_class, find_all, load_package, construct_object, find_object, make_struct
import unrealsdk

from .Lists import BL2MapNames, TPSMapNames, AoDKMapNames, ExtraPacks #type: ignore
from .SaveSystem import GetSaveLocation, LoadFromJson, SaveToJson

LoadedFMAmount = 0
LoadedProjAmount = 0
PlayerID = -1

FinishedLoadingPackages = False

PlayerLoad = True
LoadFromText = True
IsNewGame = False

SavePath = None

ItemInfoDict = {'UniqueIDs': {}}
AIPawnProjectiles = {'AIPawns': {}}
AIPawnBeams = {'AIPawnBeams': {}}

GrenadeResource = find_object("ResourceDefinition", "D_Resources.AmmoResources.Ammo_Grenade_Protean")

Classnames = ["WillowWeapon", "WillowGrenadeMod"]
UniqueIDs = []
AllFiringModes = []
AllProjectiles = []
RecentlyUsedProj = []
RecentlyUsedFM = []
AllFMandProj = []

def KeepAlive(InObject:UObject) -> None:
    InObject.ObjectFlags |= 0x4000
    return

def MakeAttributeStruct(BaseValue: float) -> WrappedStruct:
    return make_struct('AttributeInitializationData',
                       BaseValueConstant=BaseValue,
                       BaseValueScaleConstant=1)


ResourceCost = MakeAttributeStruct(1)

def GenerateName(DefData: WrappedStruct, bWeapon: bool) -> str:
    if bWeapon:
        Item = ENGINE.GetCurrentWorldInfo().Spawn(find_class("WillowWeapon"))
    else:
        Item = ENGINE.GetCurrentWorldInfo().Spawn(find_class("WillowGrenadeMod"))
    Item.InitializeFromDefinitionData(DefData, None, True)
    return Item.GetInventoryCardString(False, True, True)

def CreateDictEntry(UniqueID, ItemPart, FiringMode, Projectile, Name):
    global ItemInfoDict
    for Object in [str(ItemPart), str(FiringMode), str(Projectile)]:
        if "&" in Object:
            return

    if UniqueID not in ItemInfoDict['UniqueIDs'].keys():#type:ignore
        ItemInfo = [str(ItemPart), str(FiringMode), str(Projectile), Name]
        ItemInfoDict['UniqueIDs'][UniqueID] = ItemInfo#type:ignore
    return


def PrepProjectileRando() -> None:
    global FinishedLoadingPackages, AllFiringModes, AllProjectiles, LoadFromText, PlayerLoad, LoadedFMAmount, LoadedProjAmount, AllFMandProj
    if FinishedLoadingPackages:
        return
    
    if Game.get_current() == Game.BL2:
        MaxPrintFM = 269
        MaxPrintProj = 760
        MapNames = BL2MapNames
    elif Game.get_current() == Game.TPS:
        MaxPrintFM = 182
        MaxPrintProj = 574
        MapNames = TPSMapNames
    elif Game.get_current() == Game.AoDK:
        MaxPrintFM = 146
        MaxPrintProj = 232
        MapNames = AoDKMapNames


    lists = find_all("LevelDependencyList")
    for Object in lists:
        for persistent in Object.LevelList:
            if str(persistent.PersistentMap) in MapNames:
                mainmap = persistent.PersistentMap
                load_package(str(mainmap))
                for map in persistent.SecondaryMaps:
                    load_package(str(map))

    
                FindAndKeepAlive("FiringModeDefinition", AllFiringModes)

                FindAndKeepAlive("ProjectileDefinition", AllProjectiles)

                get_pc().ConsoleCommand("obj garbage")
    
    for Pack in ExtraPacks:
        load_package(Pack)
        FindAndKeepAlive("FiringModeDefinition", AllFiringModes)
        FindAndKeepAlive("ProjectileDefinition", AllProjectiles)

        if Game.get_current() == Game.BL2 or Game.get_current() == Game.AoDK:  
            get_pc().ConsoleCommand("obj garbage")
        else:
            ENGINE.GetCurrentWorldInfo().ForceGarbageCollection(True)
    
    if Game.get_current() == Game.BL2:
        bpd = unrealsdk.find_object('BehaviorProviderDefinition', 'GD_Jack.Projectiles.Projectile_JackTurret:BehaviorProviderDefinition_0')
        bpd.BehaviorSequences[0].EventData2[1].OutputLinks.ArrayIndexAndLength = 458753
        AllProjectiles.remove(find_object('ProjectileDefinition','GD_Episode11Data.Projectiles.Ep11_AIDodgeHack'))
        AllProjectiles.remove(find_object('ProjectileDefinition','GD_Episode13Data.Projectiles.Ep13_FloorTrap_AIDodgeHack'))
        AllProjectiles.remove(find_object('ProjectileDefinition','GD_Episode13Data.Projectiles.Ep13_TeslaPole_AIDodgeHack'))
        AllProjectiles.remove(find_object('ProjectileDefinition','GD_SpiderantFire_Digi.Projectiles.Projectile_SapperBomb_Dummy'))
        AllProjectiles.remove(find_object('ProjectileDefinition','GD_SpiderantFire.Projectiles.Projectile_SapperBomb_Dummy'))

    print(f"Total Firing Modes: {len(AllFiringModes)}/{MaxPrintFM}")
    print(f"Total Projectiles: {len(AllProjectiles)}/{MaxPrintProj}")

    LoadedFMAmount = len(AllFiringModes)
    LoadedProjAmount = len(AllProjectiles)

    FinishedLoadingPackages = True
    LoadFromText = True
    PlayerLoad = True

    ENGINE.GetCurrentWorldInfo().ForceGarbageCollection(True)

    AllFMandProj = []
    return



def PlayerLoaded() -> None:
    global SavePath, LoadFromText, UniqueIDs, ItemInfoDict, PlayerLoad, SaveID

    obj = get_pc()
    SaveID = obj.GetCachedSaveGame().SaveGameId
    if obj.GetCachedSaveGame().SaveGameId == -1:
        return

    if SaveID != -1:
       SavePath = GetSaveLocation(SaveID)

    if LoadFromText:
        UniqueIDs = []
        ItemInfoDict = LoadFromJson(SavePath)
        for key in ItemInfoDict['UniqueIDs'].keys(): #type:ignore
            UniqueIDs.append(key)
        LoadFromText = False

    ItemArray = []
    Inventory = obj.GetPawnInventoryManager()

    ItemToCheck = Inventory.ItemChain
    while ItemToCheck is not None:
        ItemArray.append(ItemToCheck)
        ItemToCheck = ItemToCheck.Inventory

    ItemToCheck = list(Inventory.Backpack)
    for items in ItemToCheck:
        if items is not None:
            ItemArray.append(items)

    for i in range(1,5):
        if Inventory.GetWeaponInSlot(i) is not None:
            ItemArray.append(Inventory.GetWeaponInSlot(i))

    for item in ItemArray:
        UniqueID = item.DefinitionData.UniqueID
        if UniqueID in ItemInfoDict['UniqueIDs'].keys():#type:ignore
            LoadFromDict(item, UniqueID)

    PlayerLoad = False
    return

def LoadFromDict(item: UObject, UniqueID: int) -> None:
    global ItemInfoDict, GrenadeResource
    if UniqueID not in ItemInfoDict['UniqueIDs'].keys():#type:ignore
        return
    
    ItemInfo = ItemInfoDict['UniqueIDs'][UniqueID]#type:ignore
    if item.Class.Name == "WillowWeapon":
        DefData = item.DefinitionData
        BarrelPart = FindObjectFromString(str(ItemInfo[0]))
        FiringMode:UObject = FindObjectFromString(str(ItemInfo[1]))
        Projectile = FindObjectFromString(str(ItemInfo[2]))

        if BarrelPart:
            NewBarrel = DupeObject(BarrelPart, "WeaponPartDefinition")
            DefData.BarrelPartDefinition = NewBarrel
            item.InitializeFromDefinitionData(DefData, None, True)
            if Projectile:
                newFM = DupeObject(FiringMode, "FiringModeDefinition")
                NewProjectile = DupeObject(Projectile, "ProjectileDefinition")

                NewProjectile.bUseCustomAimDirection = False

                if NewProjectile.SpeedFormula.BaseValueConstant <= 0.0:
                    NewProjectile.SpeedFormula = MakeAttributeStruct(uniform(1500, 4500))

                newFM.ProjectileDefinition = NewProjectile
                NewBarrel.CustomFiringModeDefinition = newFM
            else:
                NewBarrel.CustomFiringModeDefinition = FiringMode

    elif item.Class.Name == "WillowGrenadeMod":
        DefData = item.DefinitionData
        DeliveryPart = FindObjectFromString(str(ItemInfo[0]))
        Projectile = FindObjectFromString(str(ItemInfo[2]))

        if DeliveryPart and Projectile:
            NewDelivery = DupeObject(DeliveryPart, "GrenadeModPartDefinition")
            NewProjectile = GetProjectile(Projectile)[1]
            NewProjectile.Resource = GrenadeResource
            NewProjectile.ResourceCost = MakeAttributeStruct(1)
            NewProjectile.FlashIconName = "frag"
            NewDelivery.CustomProjectileDefinition = NewProjectile
            DefData.BetaItemPartDefinition = NewDelivery
            item.InitializeFromDefinitionData(DefData, None, True)

    return


def save(bCleanArray: bool) -> None:
    global ItemInfoDict, UniqueIDs, SavePath, PlayerID, LoadFromText,IsNewGame
    print(IsNewGame)
    if IsNewGame:
        LoadFromText = False

    if LoadFromText:
        print("load from text still true")
        return
    
    print("started saving")
    if not get_pc().GetPawnInventoryManager():
        return

    print(get_pc().GetPawnInventoryManager())
    ItemArray = []
    Inventory = get_pc().GetPawnInventoryManager()
    ItemToCheck = Inventory.ItemChain
    while ItemToCheck is not None:
        ItemArray.append(ItemToCheck)
        ItemToCheck = ItemToCheck.Inventory

    ItemToCheck = list(Inventory.Backpack)
    for items in ItemToCheck:
        if items is not None:
            ItemArray.append(items)

    for i in range(1,5):
        if Inventory.GetWeaponInSlot(i):
            ItemArray.append(Inventory.GetWeaponInSlot(i))

    print(ItemArray)

    IDs = [item.DefinitionData.UniqueID for item in ItemArray]
    SaveDict = ItemInfoDict['UniqueIDs'].copy()#type:ignore
    KeysToRemove = [key for key in SaveDict if key not in IDs]

    for key in KeysToRemove:
        del SaveDict[key]
        if bCleanArray and key in UniqueIDs:
            UniqueIDs.remove(key)

    print(SaveDict)

    PlayerID = get_pc().GetCachedSaveGame().SaveGameId
    if PlayerID == -1:#most likely a new character
        return
    SavePath = GetSaveLocation(PlayerID)

    print(SavePath)
    SaveToJson(SavePath, SaveDict)
    return


def InitializeFromDefData(Item: UObject) -> None:
    global UniqueIDs
    DefData = Item.DefinitionData
    if DefData.UniqueID not in UniqueIDs and DefData.BarrelPartDefinition:
        DefData.BarrelPartDefinition = UpdateBarrel(DefData)
        Item.InitializeFromDefinitionData(DefData, None, True)
    return


def InitializeFromItemData(Item: UObject) -> None:
    global UniqueIDs
    DefData = Item.DefinitionData
    if DefData.UniqueID not in UniqueIDs and DefData.BetaItemPartDefinition:
        DefData.BetaItemPartDefinition = UpdateDelivery(DefData)
        Item.InitializeFromDefinitionData(DefData, None, True)
    return
  

def FindAndKeepAlive(ClassName: str, AllTypesList: list) -> None:
    global AllFiringModes, AllProjectiles, AllFMandProj
    AllDefinitions = find_all(ClassName, False)
    for Definition in AllDefinitions:
        if Definition not in AllFMandProj:
            AllFMandProj.append(Definition)
            AllTypesList.append(Definition)
            KeepAlive(Definition)
    return

def FindObjectFromString(ObjectToFind:str) -> Any:
    if ObjectToFind and ObjectToFind != "None":
        SplitObjectString = ObjectToFind.split(f"'")
        Class = SplitObjectString[0]
        Object = SplitObjectString[1]
        return find_object(Class, Object)
    return None


def UpdateProjectile(Projectile:UObject) -> None:#basically just turns certain projectiles into grenade flight path
    if Projectile.SpeedFormula.BaseValueConstant == 0.0:
        Projectile.GravityScaling = 0.8
        Projectile.UpwardVelocityBonus = 270
        Projectile.SpeedFormula.BaseValueConstant = 1700
    return


def UpdateBarrel(DefData: WrappedStruct) -> Any:
    global UniqueIDs
    UniqueIDs.append(DefData.UniqueID)
    NewFM = GetFM()
    Name = str(GenerateName(DefData, True))
    CreateDictEntry(DefData.UniqueID, DefData.BarrelPartDefinition, NewFM[0], NewFM[2], Name)
    NewBarrel = DupeObject(DefData.BarrelPartDefinition,  "WeaponPartDefinition")
    NewBarrel.CustomFiringModeDefinition = NewFM[0] if NewFM[1] is None else NewFM[1]
    return NewBarrel


def UpdateDelivery(DefData: WrappedStruct) -> UObject:
    global UniqueIDs, GrenadeResource
    UniqueIDs.append(DefData.UniqueID)
    NewDelivery = DupeObject(DefData.BetaItemPartDefinition, "GrenadeModPartDefinition")
    NewProjectile = GetProjectile(None)
    Name = str(GenerateName(DefData, False))
    CreateDictEntry(DefData.UniqueID, DefData.BetaItemPartDefinition, None, NewProjectile[0], Name)
    NewProjectile[1].Resource = GrenadeResource
    NewProjectile[1].ResourceCost = MakeAttributeStruct(1)
    NewProjectile[1].FlashIconName = "frag"
    NewDelivery.CustomProjectileDefinition = NewProjectile[1]
    return NewDelivery

WeaponPart = find_class("WeaponPartDefinition").ClassDefaultObject
def DupeObject(ObjectToDupe:UObject, ClassType: str) -> UObject:
    ObjectName = ObjectToDupe.Name if ObjectToDupe else ""
    NewName = f"{ObjectName}&{str(uniform(1,200000))}"#hack way of keeping names unique
    NewObject = construct_object(ClassType, WeaponPart, NewName, template_obj=ObjectToDupe)
    if hasattr(ObjectToDupe, "BodyComposition") and ObjectToDupe.BodyComposition:
        NewObject.BodyComposition.Attachments=list(ObjectToDupe.BodyComposition.Attachments)
        NewObject.BodyComposition.MaxExpectedComponents=ObjectToDupe.BodyComposition.MaxExpectedComponents
        NewObject.BodyComposition.HasHomingTargetComponents=ObjectToDupe.BodyComposition.HasHomingTargetComponents                          

    KeepAlive(NewObject)
    return NewObject


def GetFM() -> list:
    FiringMode = choice(AllFiringModes)
    if len(AllFiringModes) > round(LoadedFMAmount / 2):
        while FiringMode in RecentlyUsedFM:
            FiringMode = choice(AllFiringModes)

    if FiringMode not in RecentlyUsedFM:
        RecentlyUsedFM.append(FiringMode)

    if len(RecentlyUsedFM) >= round(LoadedFMAmount / 2):
        RecentlyUsedFM.pop(0)

    if randint(1,2) == 1:
        return [FiringMode, None, None]
    else:
        while FiringMode.ProjectileDefinition is None:
            FiringMode = choice(AllFiringModes)

        newFM = DupeObject(FiringMode, "FiringModeDefinition")

        NewProj = choice(AllProjectiles)
        if len(AllProjectiles) > round(LoadedProjAmount / 3):
            while NewProj in RecentlyUsedProj:
                NewProj = choice(AllProjectiles)

        if NewProj not in RecentlyUsedProj:
            RecentlyUsedProj.append(NewProj)

        if len(RecentlyUsedProj) >= round(LoadedProjAmount / 3):
            RecentlyUsedProj.pop(0)

        UpdateProj = DupeObject(NewProj, "ProjectileDefinition")

        UpdateProj.bUseCustomAimDirection = False

        if UpdateProj.SpeedFormula.BaseValueConstant <= 0.0:
            NewSpeed = MakeAttributeStruct(uniform(1500, 4500))
            UpdateProj.SpeedFormula = NewSpeed
        
        newFM.ProjectileDefinition = UpdateProj
        return [FiringMode, newFM, NewProj]
    

def GetProjectile(Projectile:UObject | None) -> Any:
    if Projectile is None:
        Projectile = choice(AllProjectiles)
        if len(AllProjectiles) > round(LoadedProjAmount / 3):
            while Projectile in RecentlyUsedProj:
                Projectile = choice(AllProjectiles)
                
        if Projectile not in RecentlyUsedProj:
            RecentlyUsedProj.append(Projectile)

        if len(RecentlyUsedProj) >= round(LoadedProjAmount / 3):
            RecentlyUsedProj.pop(0)

    newProj = DupeObject(Projectile, "ProjectileDefinition")#type:ignore

    UpdateProjectile(newProj)

    return [Projectile, newProj]