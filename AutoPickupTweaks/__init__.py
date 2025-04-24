from typing import Any
from unrealsdk import find_object
from unrealsdk.hooks import Type, Block
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct, WeakPointer
from mods_base import hook, build_mod, Game, SliderOption, BoolOption, NestedOption

def ModOptionChanged(option, new_val) -> None:
    if option.identifier in ItemDictionary.keys():
        for item in ItemDictionary[option.identifier]:
            SetAutoPickup(item, new_val)
    return


oidChests = BoolOption(
    "Chest Items",
    True,
    "On",
    "Off",
    description="With this enabled, enabled options will be automatically picked up from chests.",
)

oidHealthVials = BoolOption(
    "Health Vials",
    True,
    "On",
    "Off",
    description="With this enabled, Health Vials will be automatically picked up.",
    on_change=ModOptionChanged
)

oidShieldBoosters = BoolOption(
    "Shield Boosters",
    False,
    "On",
    "Off",
    description="With this enabled, Shield Boosters will be automatically picked up after they have landed.",
    on_change=ModOptionChanged
)

oidMoney = BoolOption(
    "Money",
    True,
    "On",
    "Off",
    description="With this enabled, Money will be automatically picked up.",
    on_change=ModOptionChanged
)

oidEridium = BoolOption(
    "Eridium",
    False,
    "On",
    "Off",
    description="With this enabled, Eridium will be automatically picked up.",
    on_change=ModOptionChanged
)

oidSeraphCrystal = BoolOption(
    "Seraph Crystals",
    False,
    "On",
    "Off",
    description="With this enabled, Seraph Crystals will be automatically picked up.",
    on_change=ModOptionChanged
)

oidTorgueToken = BoolOption(
    "Torgue Tokens",
    False,
    "On",
    "Off",
    description="With this enabled, Torgue Tokens will be automatically picked up.",
    on_change=ModOptionChanged
)

oidMoonstones = BoolOption(
    "Moonstones",
    False,
    "On",
    "Off",
    description="With this enabled, Moonstones will be automatically picked up.",
    on_change=ModOptionChanged
)

oidPickupDistance = SliderOption(
    "Auto Pickup Distance",
    350,
    50,
    5000,
    1,
    description="Adjust the distance you want items to automatically be picked up. 350 is the vanilla distance.",
    on_change=ModOptionChanged
)

oidARBullets = BoolOption(
    "Assualt Rifle Bullets",
    True,
    "On",
    "Off",
    description="With this enabled, Assualt Rifle Bullets will be automatically picked up.",
    on_change=ModOptionChanged
)

oidSMGBullets = BoolOption(
    "SMG Bullets",
    True,
    "On",
    "Off",
    description="With this enabled, MG Bullets will be automatically picked up.",
    on_change=ModOptionChanged
)

oidShotgunShells = BoolOption(
    "Shotgun Shells",
    True,
    "On",
    "Off",
    description="With this enabled, Shotgun Shells will be automatically picked up.",
    on_change=ModOptionChanged
)

oidPistolBullets = BoolOption(
    "Pistol Bullets",
    True,
    "On",
    "Off",
    description="With this enabled, Pistol Bullets will be automatically picked up.",
    on_change=ModOptionChanged
)

oidSniperBullets = BoolOption(
    "Sniper Bullets",
    True,
    "On",
    "Off",
    description="With this enabled, Sniper Bullets will be automatically picked up.",
    on_change=ModOptionChanged
)

oidLaserCells = BoolOption(
    "Laser Cells",
    True,
    "On",
    "Off",
    description="With this enabled, Laser Cells will be automatically picked up.",
    on_change=ModOptionChanged
)

oidRockets = BoolOption(
    "Rockets",
    True,
    "On",
    "Off",
    description="With this enabled, Rocket Ammo will be automatically picked up.",
    on_change=ModOptionChanged
)

oidGrenades = BoolOption(
    "Grenades",
    True,
    "On",
    "Off",
    description="With this enabled, Grenades will be automatically picked up.",
    on_change=ModOptionChanged
)

oidAmmoNest = NestedOption (
    "Ammo Settings",
    [oidARBullets, oidSMGBullets, oidShotgunShells, oidPistolBullets,  
        oidSniperBullets, oidRockets, oidGrenades, oidLaserCells],
    description = "Choose which ammo types auto pickup.",
)

oidMainNest = NestedOption (
    "Auto Pickup Tweaks Options",
    [oidChests, oidHealthVials, oidShieldBoosters, oidMoney, oidEridium,
    oidSeraphCrystal, oidTorgueToken, oidMoonstones, oidPickupDistance, oidAmmoNest],
    description = "All the settings for Auto Pickup Tweaks",
)


ShieldNames = ["Shield Booster", "IED Booster", "Slammer", "Big Boom Blaster Booster"]
InteractiveObjects = {}
ItemDictionary = {}

def SetAutoPickup(Pickupable, bAuto):
    if Pickupable:
        #print(f"setting {Pickupable.Name} to {bAuto}")
        Pickupable.bAutomaticallyPickup = bAuto
    return


def FindValueForOptionIdentifier(Identifier:str):
    for Option in oidMainNest.children:
        if Option.identifier == Identifier:
            return Option.value
    
    for Option in oidAmmoNest.children:
        if Option.identifier == Identifier:
            return Option.value



@hook("WillowGame.WillowGFxMoviePressStart:DlcRefreshComplete", Type.POST)
def DlcRefreshComplete(obj: UObject, __args: WrappedStruct, __ret: any, __func: BoundFunction) -> None:
    global ItemDictionary
    
    LaserCells = None
    SmallMoonstone = None
    LargeMoonstone = None

    SmallEridium = None
    LargeEridium = None
    SeraphCrystalsAster = None
    SeraphCrystalsIris = None
    SeraphCrystalsOrchid = None
    SeraphCrystalsAsterSage = None
    TorgueToken = None

    HealthVialRegen = find_object('UsableItemDefinition','GD_BuffDrinks.A_Item.BuffDrink_HealingRegen')
    HealthVialInstant = find_object('UsableItemDefinition','GD_BuffDrinks.A_Item.BuffDrink_HealingInstant')

    SmallMoney = find_object('UsableItemDefinition','GD_Currency.A_Item.Currency')
    LargeMoney = find_object('UsableItemDefinition','GD_Currency.A_Item.Currency_Big')
    CrystaliskMoney = find_object('UsableItemDefinition', 'GD_Currency.A_Item.Currency_Crystal')

    ARBulletsNormal = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Assault_Rifle_Bullets')
    ARBulletsBoss = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Assault_Rifle_Bullets')

    GrenadesNormal = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Grenade_Protean')
    GrenadesBoss = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Grenade_Protean')

    SMGBulletsNormal = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Patrol_SMG_Clip')
    SMGBulletsBoss = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Patrol_SMG_Clip')

    PistolBulletsNormal = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Repeater_Pistol_Clip')
    PistolBulletsBoss = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Repeater_Pistol_Clip')

    ShotgunShellsNormal = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Shotgun_Shells')
    ShotgunShellsBoss = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Shotgun_Shells')

    Rockets = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Rocket_Launcher')

    SniperBullets = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Sniper_Rifle_Cartridges')


    if Game.get_current() == Game.TPS:
        SmallMoonstone = find_object('UsableItemDefinition','GD_Currency.A_Item.Moonstone')
        LargeMoonstone = find_object('UsableItemDefinition','GD_Currency.A_Item.MoonstoneCluster')
        LaserCells = find_object('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Laser_Cells')
    else:
        SmallEridium = find_object('UsableItemDefinition','GD_Currency.A_Item.EridiumStick')
        LargeEridium = find_object('UsableItemDefinition','GD_Currency.A_Item.EridiumBar')

        SeraphCrystalsAster = find_object('UsableItemDefinition','GD_Aster_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        SeraphCrystalsIris = find_object('UsableItemDefinition','GD_Iris_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        SeraphCrystalsOrchid = find_object('UsableItemDefinition','GD_Orchid_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        SeraphCrystalsAsterSage = find_object('UsableItemDefinition','GD_Sage_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
    
        TorgueToken = find_object('UsableItemDefinition','GD_Iris_TorgueToken.UsableItems.Pickup_TorgueToken')
    
    ItemDictionary = {
            oidMoney.identifier: [SmallMoney, LargeMoney, CrystaliskMoney],
            oidEridium.identifier: [SmallEridium, LargeEridium],
            oidSeraphCrystal.identifier: [SeraphCrystalsAster, SeraphCrystalsIris, SeraphCrystalsOrchid, SeraphCrystalsAsterSage],
            oidTorgueToken.identifier: [TorgueToken],
            oidMoonstones.identifier: [SmallMoonstone, LargeMoonstone],
            oidARBullets.identifier: [ARBulletsNormal, ARBulletsBoss],
            oidSMGBullets.identifier: [SMGBulletsNormal, SMGBulletsBoss],
            oidShotgunShells.identifier: [ShotgunShellsNormal, ShotgunShellsBoss],
            oidPistolBullets.identifier: [PistolBulletsNormal, PistolBulletsBoss],
            oidGrenades.identifier: [GrenadesNormal, GrenadesBoss],
            oidLaserCells.identifier: [LaserCells],
            oidRockets.identifier: [Rockets],
            oidSniperBullets.identifier: [SniperBullets],
            oidHealthVials.identifier: [HealthVialInstant, HealthVialRegen],
        }

    for key in ItemDictionary.keys():
        for item in ItemDictionary[key]:
            SetAutoPickup(item, FindValueForOptionIdentifier(key))

    return


@hook("WillowGame.WillowPickup:UpdateTouchRadiusForAutomaticallyPickedUpInventory", Type.POST)
def UpdateTouchRadiusForAutomaticallyPickedUpInventory(obj: UObject, __args: WrappedStruct, __ret: any, __func: BoundFunction) -> None:
    if (((obj.IsPickupableInventoryAutomaticallyPickedUp()) or (obj.bIsMissionItem and not obj.bIsMissionDirector)) and obj.Components[1]):
        obj.Components[1].SetCylinderSize(oidPickupDistance.value, oidPickupDistance.value)
    return Block


@hook("WillowGame.WillowPickup:SetInteractParticles", Type.POST)
def InteractParticles(obj: UObject, __args: WrappedStruct, __ret: any, __func: BoundFunction) -> None:
    if not oidChests.value or not obj.Base or obj.Base.Class.Name != "WillowInteractiveObject":
        return

    if obj.Inventory and obj.Inventory.Class.Name == "WillowUsableItem" and not obj.Inventory.Class.Name == "WillowMissionItem":
        BaseIO = obj.Base.ConsumerHandle.PID
        if obj.Base.InteractiveObjectDefinition.Name == "InteractiveObj_MilitaryCrate":
            obj.AdjustPickupPhysicsAndCollisionForBeingDropped()
            obj.Components[1].SetCylinderSize(oidPickupDistance.value, oidPickupDistance.value)
        
        if BaseIO in InteractiveObjects.keys() and InteractiveObjects[BaseIO] and obj.bPickupable:
            CurrentController = InteractiveObjects[BaseIO]()
            if CurrentController and obj.Inventory.CanBeUsedBy(CurrentController.Pawn):
                CurrentController.TouchedPickupable(obj)
    return


@hook("WillowGame.WillowInteractiveObject:UsedBy", Type.POST)
def UsedBy(obj: UObject, __args: WrappedStruct, __ret: any, __func: BoundFunction) -> None:
    InteractiveObjects[obj.ConsumerHandle.PID] = WeakPointer(__args.User.Controller)
    return


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST)
def DisableLoadingMovie(obj: UObject, __args: WrappedStruct, __ret: any, __func: BoundFunction) -> None:
    global InteractiveObjects
    InteractiveObjects = {}
    return


@hook("WillowGame.WillowPlayerController:TouchedPickupable", Type.POST)
def TouchedPickup(obj: UObject, __args: WrappedStruct, __ret: any, __func: BoundFunction) -> None:
    if not __args.Pickup or not __args.Pickup.ObjectPointer or __args.Pickup.ObjectPointer.Base:
        return
    
    TouchedPickable = __args.Pickup.ObjectPointer
    if oidShieldBoosters.value and str(TouchedPickable.Inventory.ItemName) in ShieldNames and TouchedPickable.bPickupable:
        if TouchedPickable.ImpactEffectPlayCount >= 1 or TouchedPickable.bPickupAtRest:
            obj.PickupPickupable(TouchedPickable, True)
    return


build_mod(options = [oidMainNest], hooks=[TouchedPickup, DisableLoadingMovie, UsedBy, InteractParticles, UpdateTouchRadiusForAutomaticallyPickedUpInventory, DlcRefreshComplete])