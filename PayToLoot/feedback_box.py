from mods_base import get_pc
from unrealsdk.unreal import UObject
import PayToLoot.options as options
from .repo_spawner import remove_repo_men
from ui_utils import show_hud_message, TrainingBox

def show_loan_paid_off(menu_closing:bool, reason:str):
    match reason:
        case "repo":
            training_message = ("Your loan with Marcus has been forcefully reposessed!"
                                "\nDon't make us come and get it next time!")
            
        case "garnished":
            training_message = ("Your loan with Marcus has been paid off with garnished wages!")

        case "manual":
            training_message = ("You have successfully paid off your loan!")

    if menu_closing:
        loan_paid_box = TrainingBox(title="Pay to Loot",
                                    message=training_message,
                                    min_duration=0.1,
                                    pauses_game=True,
                                    )
        loan_paid_box.show()
    else:
        show_hud_message("Pay to Loot", training_message, 5)

    remove_repo_men()
    options.ingame_loanamount = 0
    options.ingame_paidtime = 0
    options.ingame_raidtime = 0
    options.oidLoan.value = 0
    options.oidLastPaidTime.value = 0
    options.oidLastRaidTime.value = 0
    options.save_all_options()


from legacy_compat import legacy_compat
with legacy_compat():
    from Mods import UserFeedback 

    
class loan_feedback_box(UserFeedback.TextInputBox):
    def __init__(self, amount = ""):
        super().__init__(Title=f"Enter Amount to Pay", DefaultMessage=f"You still have ${options.oidLoan.value:,} left to pay. \nHow much would you like to pay now?\n\n$")
        self.Show()

    def IsAllowedToWrite(self, Character: str, CurrentMessage: str, Position: int) -> bool:
        if Character not in ["0","1","2","3","4","5","6","7","8","9"]:
            return False
        if len(CurrentMessage) == 0 and Character == "0":
            return False
        return True
    
    def OnSubmit(self, amount) -> None:
        if amount == "":
            return


        amount = amount.split("$")[2]
        
        amount = int(amount)
        if amount <= get_pc().PlayerReplicationInfo.GetCurrencyOnHand(0):
            global oidLastPaidTime, oidLoan
            if amount >= options.oidLoan.value:
                amount_to_take = options.oidLoan.value
                options.ingame_loanamount = 0
                options.oidLoan.value = 0
            else:
                amount_to_take = amount
                options.ingame_loanamount = options.ingame_loanamount - amount
                options.oidLoan.value = options.oidLoan.value - amount
                paid_percent = amount/options.oidLoan.value

            if options.oidLoan.value > 0 and paid_percent > 0.10:
                options.ingame_paidtime = 0
                options.ingame_raidtime = 0
                options.ingame_raidmax= 1200
                options.oidLastPaidTime.value = 0
                options.oidLastRaidTime.value = 0
                options.oidRaidMaxTime.value = 1200

            get_pc().PlayerReplicationInfo.AddCurrencyOnHand(0, -amount_to_take)
            options.save_all_options()

            if options.oidLoan.value <= 0:
                show_loan_paid_off(True, "manual")


