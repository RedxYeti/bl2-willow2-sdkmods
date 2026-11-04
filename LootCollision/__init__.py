from typing import Any 
from mods_base import hook, build_mod, Game, BoolOption
from unrealsdk.hooks import Type, Block
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

if Game.get_tree() == Game.Willow1:
    @hook("WillowGame.WillowPickup:EnableRagdollCollision", Type.PRE)
    def LC_BL1_EnableRagdollCollision(obj:UObject, args:WrappedStruct, ret:Any, func:BoundFunction) -> Any:
        if not obj.CollisionComponent:
            return 
        obj.CollisionComponent.SetRBCollidesWithChannel(1, False)
        obj.CollisionComponent.SetRBCollidesWithChannel(2, False)
        obj.CollisionComponent.SetRBCollidesWithChannel(16, False)
        obj.CollisionType = 6
        return Block
    
else:
    @hook("WillowGame.WillowPickup:EnableRagdollCollision", Type.POST)
    def LC_EnableRagdollCollision(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
        if not obj.CollisionComponent:
            return 
            
        obj.CollisionComponent.SetRBCollidesWithChannel(16, False)#Dead pawns
        obj.CollisionComponent.SetRBCollidesWithChannel(24, False)#willow pickups
        return

    oidAddOffset =  BoolOption(
        "Add Item Offset",
        True,
        "On",
        "Off",
        description="Adds a small offset to spawned loot so large piles like Pyro Pete's loot pile are more spread out. Turn off if it's messing with the loot pile of you're farming."
    )

    @hook("WillowGame.Behavior_SpawnItems:ApplyBehaviorToContext", Type.PRE)
    def LC_Behavior_SpawnItems(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
        if not oidAddOffset.value:
            return

        item_offset = obj.ItemScatterOffset
        item_velocity = obj.ItemDropVelocity

        if item_velocity.X == 0 and item_velocity.Y == 0 and item_velocity.Z == 0:
            item_offset.X += 50
            item_offset.Y += 50
            item_offset.Z += 50


        if item_offset.X == 0 and item_offset.Y == 0 and item_offset.Z == 0:
            item_offset.X += 15
            item_offset.Y += 15
            item_offset.Z += 15
            return

        if item_offset.X > 0:
            item_offset.X += 15
    
        if item_offset.Y > 0:
            item_offset.Y += 15
    
        if item_offset.Z > 0:
            item_offset.Z += 15

build_mod()