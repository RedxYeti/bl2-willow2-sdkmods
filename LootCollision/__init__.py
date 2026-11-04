from typing import Any 
from mods_base import hook, build_mod, Game
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


    @hook("WillowGame.Behavior_SpawnItems:ApplyBehaviorToContext", Type.PRE)
    def LC_Behavior_SpawnItems(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
        item_offset = obj.ItemScatterOffset
        if item_offset.X > 0:
            item_offset.X += 25
    
        if item_offset.Y > 0:
            item_offset.Y += 25
    
        if item_offset.Z > 0:
            item_offset.Z += 25


build_mod()