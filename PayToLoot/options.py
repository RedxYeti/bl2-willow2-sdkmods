from save_options import HiddenSaveOption
from mods_base import BoolOption, get_pc

oidLoan = HiddenSaveOption("loan_amount", 0)
oidLastPaidTime = HiddenSaveOption("loan_payments", 0)
oidLastRaidTime = HiddenSaveOption("raid_tracker", 0)
oidSeenTutorial = HiddenSaveOption("loan_tutorial", False)
oidRaidTutorial = HiddenSaveOption("raid_tutorial", False)
oidRaidMaxTime = HiddenSaveOption("raid_max", 0)

ingame_loanamount = 0
ingame_paidtime = 0
ingame_raidtime = 0
ingame_raidmax = 0
ingame_seenraidtut = False



def save_all_options() -> None:
    PC = get_pc()
    PC.PlayersToSave.append(PC)
    PC.SavePlayer(PC)


oidShowMoney = BoolOption(
    "Show Money on HUD",
    False,
    "On",
    "Off",
    description="With this on, the money spinner will always be visible on your HUD when the HUD is active.",
)