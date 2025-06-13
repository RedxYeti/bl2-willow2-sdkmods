from mods_base import SliderOption, BoolOption, Game #type:ignore

oidDropWeapons = BoolOption(
    "Enemies Drop Weapons",
    False,
    "On",
    "Off",
    description="With this enabled, enemies will drop the weapons theyre using (even weapons that shouldn't drop). Leave this off if youre using Cold Dead Hands.",
)
