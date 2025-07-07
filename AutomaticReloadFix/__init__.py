
from mods_base import build_mod, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import UObject

@hook("Engine.PlayerController:StopFire", Type.POST)
@hook("Engine.PlayerController:StartFire", Type.POST)
def test2(obj:UObject, *_) -> None:
    if not obj or not obj.Pawn or not obj.Pawn.Weapon:
        return
    weapon = obj.Pawn.Weapon
    offhand = obj.Pawn.OffHandWeapon
    if weapon and weapon.NeedToReload():
        weapon.BeginReload(0)
    if offhand and offhand.NeedToReload():
        offhand.BeginReload(0)
    return

build_mod()