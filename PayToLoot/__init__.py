
try:
    from legacy_compat import legacy_compat
    with legacy_compat():
        import Mods.UserFeedback as UserFeedback

except (AssertionError, ImportError) as ex:
    import webbrowser
    webbrowser.open("https://bl-sdk.github.io/willow2-mod-db/mods/userfeedback/")
    raise

from typing import Any 
from random import randint, choice
import math

from mods_base import hook, build_mod, ObjectFlags, get_pc, keybind
from unrealsdk import find_object,construct_object,make_struct,find_all,load_package,find_class
from unrealsdk.hooks import Type, Block, prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct, notify_changes
from ui_utils import show_hud_message, TrainingBox
from save_options import register_save_options

import PayToLoot.options as options
from .repo_spawner import spawn_repo_man, create_repo_spawner
from .feedback_box import loan_feedback_box, show_loan_paid_off


attr_init_def = find_class("AttributeInitializationDefinition").ClassDefaultObject
markup = None
markup_attr_struct = None
base_icon = find_object("InteractionIconDefinition", "GD_InteractionIcons.Default.Icon_DefaultUse")
loan_paid = False
raid_start_cash = 0

def create_purchase_icon() -> UObject:
    #from alt use vendors https://bl-sdk.github.io/willow2-mod-db/mods/alt-use-vendors/
    icon = construct_object(
        cls=base_icon.Class,
        outer=base_icon.Outer,
        name="Use",
        flags=ObjectFlags.KEEP_ALIVE,
        template_obj=base_icon,
    )

    icon.Icon = 4
    icon.Action = "Use"
    icon.Text = str(f"LOOT")
    return icon

def create_pickup_icon() -> UObject:
    icon = construct_object(
        cls=base_icon.Class,
        outer=base_icon.Outer,
        name="Use",
        flags=ObjectFlags.KEEP_ALIVE,
        template_obj=base_icon,
    )

    icon.Icon = 4
    icon.Action = "Use"
    icon.Text = str(f"PICK UP")
    return icon


def create_shop_icon() -> UObject:
    icon = construct_object(
        cls=base_icon.Class,
        outer=base_icon.Outer,
        name="shop",
        flags=ObjectFlags.KEEP_ALIVE,
        template_obj=base_icon,
    )
    icon.Icon = 4
    icon.Action = "UseSecondary"
    icon.Text = str(f"SHOP")
    return icon


def create_pay_loan_icon() -> UObject:
    icon = construct_object(
        cls=base_icon.Class,
        outer=base_icon.Outer,
        name="loan",
        flags=ObjectFlags.KEEP_ALIVE,
        template_obj=base_icon,
    )
    icon.Icon = 4
    icon.Action = "UseSecondary"
    icon.Text = str(f"PAY LOAN")
    return icon


def create_loan_icon(value:int) -> UObject:
    icon = construct_object(
        cls=base_icon.Class,
        outer=base_icon.Outer,
        name="loan",
        flags=ObjectFlags.KEEP_ALIVE,
        template_obj=base_icon,
    )
    loan_amount = int(value * 1.15)
    icon.Icon = 4
    icon.Action = "UseSecondary"
    icon.Text = str(f"PURCHASE LOAN (${loan_amount})")
    return icon


def create_loan_override(loan_amount:int) -> WrappedStruct:
       return make_struct(
        "InteractionIconWithOverrides",
        IconDef=create_loan_icon(loan_amount),
    )


def get_pickup_cost(inventory:UObject) -> int:
    #emulates the cost of an item in a vendor, loads bandit slaughter if theres no vendor on the map
    global markup, markup_attr_struct
    if not markup:
        try:
            markup = find_object("AttributeInitializationDefinition","GD_Economy.VendingMachine.Init_MarkupCalc_P1")
            markup.ObjectFlags = ObjectFlags.KEEP_ALIVE
        except:
            load_package("BanditSlaughter_P")
            markup = find_object("AttributeInitializationDefinition","GD_Economy.VendingMachine.Init_MarkupCalc_P1")
            markup.ObjectFlags = ObjectFlags.KEEP_ALIVE
            get_pc().WorldInfo.ForceGarbageCollection()

        markup_attr_struct = make_struct("AttributeInitializationData",
                                          BaseValueConstant=1,
                                          InitializationDefinition=markup,
                                          BaseValueScaleConstant=1)
    return int(inventory.MonetaryValue * attr_init_def.EvaluateInitializationData(markup_attr_struct, inventory))


def is_in_sanctuary() -> bool:
   return get_pc().WorldInfo.GetMapName() in ["Sanctuary_P", "SanctuaryAir_P"]


def get_random_backpack_item(player_pawn:UObject) -> None | UObject:
    #returns a random backback item if it can be dropped, marks the pickup message for when its dropped on death
    backpack_items = [item for item in player_pawn.InvManager.Backpack if item.CanInventoryBeDroppedByOwner()]

    if not len(backpack_items):
        return None
    
    chosen_item = choice(backpack_items)
    chosen_item.PickupMessage = "PtL_whitelist"
    chosen_item.bDropOnDeath = True

    return chosen_item


@hook("WillowGame.Behavior_SpawnItems:ApplyBehaviorToContext", Type.POST)
def PtL_Behavior_SpawnItems(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    if not args.ContextObject or not hasattr(args.ContextObject, "AIClass") or args.ContextObject.AIClass.Name != "CharClass_Torgue":
        return

    for item in args.ContextObject.Attached:
        if item.Class.Name == "WillowPickup":
            item.Inventory.PickupMessage = "PtL_Whitelist"
    

@hook("GearboxFramework.Behavior_CustomEvent:ApplyBehaviorToContext")
def PtL_CustomEvent(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #this is for marcus' alt use, handles the pay loan box
    if options.ingame_loanamount > 0:
        if hasattr(args.SelfObject, "AIClass") and args.SelfObject.AIClass._path_name() == "GD_Marcus.Character.CharClass_Marcus":
            loan_feedback_box()
            return Block
    else:
        set_marcus("shop")
        PtL_CustomEvent.disable()
    

@hook("WillowGame.WillowPawn:GetAWillowPawn", Type.POST)
def PtL_GetWillowPawn(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #adds marcus' pay loan icon
    if hasattr(obj, "AIClass") and obj.AIClass._path_name() == "GD_Marcus.Character.CharClass_Marcus":
        obj.SetInteractionIcon(create_pay_loan_icon(), 1)
        PtL_GetWillowPawn.disable()


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST)
def PtL_AreaLoaded(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #this gets the repo men ready to spawn if they havent already and preps marcus' stage
    create_repo_spawner()

    if options.ingame_loanamount > 0 and is_in_sanctuary():
        PtL_GetWillowPawn.enable()
        PtL_CustomEvent.enable()
    else:
        PtL_CustomEvent.disable()
    PtL_SetDangerousIconDifference.enable()


def set_marcus(icon_type:str = "") -> None:
    #sets marcus to either the loan or shop depending
    icon = create_shop_icon() if icon_type == "shop" else create_pay_loan_icon()
    for actor in find_all("WillowAIPawn"):
        if actor.Location.X != 0 and actor.AIClass._path_name() == "GD_Marcus.Character.CharClass_Marcus":
            actor.SetInteractionIcon(icon, 1)


loan_tutorial_box = TrainingBox(title="Pay to Loot",
                                message=("You've just taken out a loan with Marcus!"
                                         "\nThe loan is 15% more than the items value."
                                         "\n"
                                         "\nUntil you pay off the loan, quest rewards and items sold to vendors will be garnished by 25%."
                                         "\n"
                                         "\nYou can pay off your loan in parts to Marcus in Sanctuary."
                                         "\n"
                                         "\nBe warned, Marcus doesn't like to be kept waiting!"),
                                min_duration=5,
                                pauses_game=True)
@hook("WillowGame.WillowPlayerController:PerformedSecondaryUseAction")
def PtL_SecondUse(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #main loan functionality
    seen_item = obj.CurrentSeenPickupable

    if not seen_item or not seen_item.bCostsToPickup:
        return
    
    if options.ingame_loanamount > 0:
        seen_item.FailedPickup()
        show_hud_message("Pay to Loot", f"You already have a loan with Marcus!\nYou have ${options.oidLoan.value} left to pay off.", 3)
        return

    class_name = seen_item.Inventory.Class.Name
    if class_name in ["WillowWeapon", "WillowClassMod", "WillowGrenadeMod", "WillowArtifact", "WillowShield"]:

        if not obj.Pawn.InvManager.HasRoomInInventoryFor(seen_item):
            obj.ClientDisplayPickupFailedMessage()
            return


        with prevent_hooking_direct_calls():
            seen_item.bCostsToPickUp = False
            seen_item.Inventory.PickupMessage = "PtL_Whitelist"
            obj.PickupPickupable(seen_item, False)

        obj.PlayersToSave.append(obj)
        obj.SavePlayer(obj)

        options.ingame_paidtime = 0
        options.ingame_raidtime = 0
        options.ingame_raidmax = 300
        options.ingame_loanamount = int(seen_item.CostsToPickUpAmount * 1.15)
        options.save_all_options()

        if not options.oidSeenTutorial.value:
            options.oidSeenTutorial.value = True
            options.oidSeenTutorial.save()
            loan_tutorial_box.show()

        PtL_SetupBalancedPopulationActor.enable()

        if is_in_sanctuary():
            PtL_CustomEvent.enable()
            set_marcus()
    return 


@hook("WillowGame.WillowPickup:SpawnPickupParticles", Type.PRE)
def PtL_SpawnPickupParticles(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #handles the main cost to pickup logic, only adds it to equipable classes unless its been stolen by the repo men
    if not obj.Inventory:
        return

    seen_item_type = obj.Inventory.Class.Name

    if (seen_item_type in ["WillowWeapon", "WillowClassMod", "WillowGrenadeMod", "WillowArtifact", "WillowShield"]
        and obj.Inventory.PickupMessage != "PtL_whitelist"):

        cost = get_pickup_cost(obj.Inventory)
        obj.bCostsToPickUp = True
        obj.CostsToPickUpType = 0
        obj.CostsToPickUpAmount = cost
        obj.SetInteractionIcon(create_purchase_icon())
        return


@hook("WillowGame.WillowPlayerController:SawPickupable")
def PtL_PickupableLoan(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #adds the seconardary use loan, makes sure whitelisted items dont cost anything
    if not obj.GetHUDMovie() or not args.Pickup.bCostsToPickUp:
        return
    
    if args.Pickup.Inventory.PickupMessage == "PtL_Whitelist":
        args.Pickup.bCostsToPickUp = False
        args.Pickup.CostsToPickUpAmount = 0
        args.Pickup.SetInteractionIcon(create_pickup_icon())
        return

    seen_item_type = args.Pickup.Inventory.Class.Name
    if seen_item_type in ["WillowWeapon", "WillowClassMod", "WillowGrenadeMod", "WillowArtifact", "WillowShield"]:
        obj.GetHUDMovie().ShowToolTip(create_loan_override(get_pickup_cost(args.Pickup.Inventory)), 1)


@hook("WillowGame.WillowPlayerController:NotifyUnableToAffordPickupable", Type.PRE)
def PtL_NotifyUnableToAffordPickupable(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #literally just wanted the item to jump
    if obj.CurrentSeenPickupable:
        obj.CurrentSeenPickupable.FailedPickup()
        return


@hook("WillowGame.WillowScrollingListDataProviderFrontEnd:Populate", Type.POST)
def PtL_Populate(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #These next couple functions run on the player controller every x seconds from timers attached to the pc
    #this function and the next set UpdateSparkLocation to run every second instead of every 5 by changing the var
    #print(get_pc().Timers)
    if not get_pc():
        PtL_Populate.disable()
        return

    for timer in get_pc().Timers:
        if timer.FuncName == "UpdateSparkLocation":
            timer.rate = 1
            break
    PtL_Populate.disable()


@hook("WillowGame.WillowPlayerController:SetSparkTimers", Type.PRE)
def PtL_SetSparkTimers(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    with notify_changes():
        obj.PlayerLocationSparkPulseIntervalSeconds = 1


@hook("WillowGame.WillowPlayerController:UpdateSparkLocation", Type.POST)
def PtL_UpdateSparkLocation(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    
    if obj.WorldInfo.IsMenuLevel():
        return

    if options.ingame_loanamount > 0:
        options.ingame_paidtime += 1

        if options.ingame_raidtime < 1200:
            options.ingame_raidtime += 1



repo_tutorial_box = TrainingBox(title="Pay to Loot",
                                message=("Marcus has sent repo men to reposses what you owe!"
                                         "\nSome of the money they take is sent directly to Marcus towards your loan."
                                         "\n"
                                         "\nMake sure to pay off at least 10% of your loan in Sanctuary frequently so Marcus doesn't send them."
                                         "\n"
                                         "\nIf you don't, they might start taking more than money..."),
                                min_duration=5,
                                pauses_game=True)
@hook("WillowGame.WillowPlayerController:UpdateLcdFriendsList", Type.POST)
def PtL_UpdateLcdFriendsList(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #handles when repo men spawn
    #uses the combat music manager to make sure youre in combat and that the combat has been running for a few seconds
    if obj.WorldInfo.IsMenuLevel():
        return

    if options.ingame_loanamount <= 0:
        return

    combat_music_manager = obj.WorldInfo.Game.GetCombatMusicManager()

    current_combat_time = obj.WorldInfo.TimeSeconds - combat_music_manager.TimeOfNewCombatAction

    if combat_music_manager.CurrentThreatValue < 120 or current_combat_time < 5:
        return
    
    if "vehicle" in str(obj.Pawn).lower():
        return
    

    unpaid_time = options.ingame_paidtime

    if unpaid_time >= 600 and options.ingame_raidtime >= options.ingame_raidmax:
        if PtL_SetupBalancedPopulationActor.get_active_count() <= 0:
            PtL_SetupBalancedPopulationActor.enable()

        amount_to_spawn = int(unpaid_time / 900)
        if amount_to_spawn == 0:
            amount_to_spawn = 1
        if amount_to_spawn > 10:
            amount_to_spawn = 10

        if options.ingame_raidmax == 1200:
            amount_to_spawn = 1

        options.ingame_raidmax = randint(300, 600)

        angle_step = math.degrees(200 / 350)

        base_yaw = obj.Rotation.Yaw + 180 

        for i in range(amount_to_spawn):
            yaw = base_yaw + (i * angle_step)
            rad = math.radians(yaw)

            spawned_repo = spawn_repo_man(rad, obj)

            if i == 0:
                if spawned_repo:
                    global raid_start_cash
                    options.ingame_raidtime = 0
                    raid_start_cash = obj.PlayerReplicationInfo.GetCurrencyOnHand(0)
                else:
                    break


@hook("WillowGame.PopulationFactoryBalancedAIPawn:SetupBalancedPopulationActor", Type.POST)
def PtL_SetupBalancedPopulationActor(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #relevels the repo men
    if options.ingame_loanamount <= 0:
        PtL_SetupBalancedPopulationActor.disable()
        return

    if not args.SpawnedPawn or args.SpawnedPawn.GetTargetName('')[1] != "Repo Man":
        return
    
    if not options.ingame_seenraidtut:
        options.ingame_seenraidtut = True
        options.oidRaidTutorial.value = True
        options.save_all_options()
        repo_tutorial_box.show()
    
    repo_man = args.SpawnedPawn
    player = get_pc().Pawn
    if repo_man.GetExpLevel() < player.GetExpLevel():
        new_level = (player.GetExpLevel() + randint(0,2)) - repo_man.GetExpLevel()
        repo_man.ExpLevel += new_level
        repo_man.GameStage += new_level
        repo_man.NumLevelUps += new_level
        repo_man.MyWillowMind.RecalculateAttributeInitializedState()


def should_deal_damage(pc:UObject) -> bool:
    current_cash = pc.PlayerReplicationInfo.GetCurrencyOnHand(0)

    global raid_start_cash
    if raid_start_cash == 0:
        raid_start_cash = current_cash
    
    current_pt = pc.GetCurrentPlaythrough()
    match current_pt:
        case 0:
            slap_cash = 50
        case 1:
            slap_cash = 2500
        case 2:
            slap_cash = 125000

    if current_cash < slap_cash or current_cash/raid_start_cash < 0.15:
        return True

    return False

@hook("WillowGame.Behavior_AITakeMoney:ApplyBehaviorToContext", Type.POST)
def PtL_Behavior_AITakeMoney(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #this is the money stealing behavior shared by the repo men
    #this has random item stealing, damage if you dont have money, and 50/50 chance for the stolen money to go towards the loan
    if not options.ingame_loanamount > 0:
        return

    if not args.SelfObject or not args.ContextObject or args.SelfObject.GetTargetName('')[1] != "Repo Man":
        return

    player_pawn = args.ContextObject

    if player_pawn.Class.Name != "WillowPlayerPawn":
        return

    if options.ingame_paidtime > 1800 and randint(0,4) == 0:
        stolen_item = get_random_backpack_item(player_pawn)
        if stolen_item:
            player_pawn.InvManager.RemoveInventoryFromBackpack(stolen_item)
            player_pawn.InvManager.UpdateBackpackInventoryCount()
            stolen_item.GiveTo(args.SelfObject, False)

    
    if should_deal_damage(player_pawn.Controller):
        current_shield = player_pawn.GetShieldStrength()
        current_health = player_pawn.GetHealth()

        if current_shield > 0:
            damage = player_pawn.GetMaxShieldStrength() * 0.05

            if current_shield >= damage:
                player_pawn.SetShieldStrength(current_shield - damage)
            else:
                leftover = damage - current_shield
                player_pawn.SetShieldStrength(0)
                player_pawn.SetHealth(current_health - leftover)
        else:
            damage = player_pawn.GetMaxHealth() * 0.05
            player_pawn.SetHealth(current_health - damage)
        return

    _, items =  args.SelfObject.InvManager.GetItemList([])
    possible_money_drops = []
    for item in items:
        if item.Class.Name != "WillowUsableItem":
            continue
        if item.bDropOnDeath and item.MonetaryValueModifierTotal == 1 and item.DefinitionData.ItemDefinition.Name == "Item_RatShared_StolenMoney":
            possible_money_drops.append(item)

    
    for item in possible_money_drops:
        if randint(0,1) == 0:
            item.bDropOnDeath = False
            print(item)
            print(options.ingame_loanamount)
            print(item.MonetaryValue)
            options.ingame_loanamount -= item.MonetaryValue
            print(options.ingame_loanamount)
            if options.ingame_loanamount <= 0:
                show_loan_paid_off(False, "repo")
                break
        
        else:
            item.MonetaryValue = int(item.MonetaryValue / 2)
            item.MonetaryValueModifierTotal = 2


def garnish_wages(value: int, remove_value:bool = True) -> int:
    #handles removing garnished wages, but also is used for rewards screens showing the correct amount of money youll get
    global loan_paid
    payout = value
    if value > 0 and options.ingame_loanamount > 0:
        garnish = int(value * 0.25)
        if remove_value:
            if garnish >= options.ingame_loanamount:
                garnish = options.ingame_loanamount
                loan_paid = True
            else:
                options.ingame_loanamount -= garnish

        payout = value - garnish
    return payout


@hook("WillowGame.WillowPlayerController:PlayerSoldItem")
def PtL_PlayerSoldItem(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #garnished vendors
    if options.ingame_loanamount > 0 and args.FormOfCurrency == 0:
        with prevent_hooking_direct_calls():
            func(0, garnish_wages(args.Price))
            return Block


@hook("WillowGame.WillowPlayerReplicationInfo:AddCurrencyOnHand")
def PtL_AddCurrencyOnHand(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #garnished quests
    pc = get_pc()
    movie = pc.GFxUIManager.GetPlayingMovie()
    if movie and movie.Class.Name in ["QuestAcceptGFxMovie", "LatentRewardGFxMovie"]:
        with prevent_hooking_direct_calls():
            func(0, garnish_wages(args.AddValue))
    PtL_AddCurrencyOnHand.disable()


@hook("WillowGame.WillowPlayerController:ServerGrantMissionRewards")
def PtL_ServerGrantMissionRewards(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    # preps quest garnish
    if options.ingame_loanamount > 0 and args.Mission.GetCurrencyRewardType(args.bGrantAltReward) == 0:
        PtL_AddCurrencyOnHand.enable()


@hook("WillowGame.MissionDefinition:GetCurrencyReward")
def PtL_GetCurrencyReward(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #runs basically any time a quest currency reward is shown
    if options.ingame_loanamount > 0 and obj.GetCurrencyRewardType(args.bGetAltReward) == 0:
        with prevent_hooking_direct_calls():
            base_value = func(args)
            new_value = garnish_wages(base_value, False)
            return Block, new_value


@hook("WillowGame.MissionRewardGFxObject:SetUpRewardsPage", Type.PRE)
def PtL_SetUpRewardsPage(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #changes what it says above currency rewards
    if options.ingame_loanamount > 0 and obj.RewardData.Mission.GetCurrencyRewardType(args.bGrantAltReward) == 0:
        obj.Header_Money = f"<font size='20'>WAGES GARNISHED!</font>"
    else:
        obj.Header_Money = "MONEY"

#these block the new character free stuff
@hook("WillowGame.StatusMenuExGFxMovie:DisplayMarketingUnlockDialogIfNecessary")
def PtL_DisplayMarketingUnlockDialogIfNecessary(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    return Block

@hook("WillowGame.WillowPlayerController:GrantNewMarketingCodeBonuses")
def PtL_GrantNewMarketingCodeBonuses(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    return Block



@hook("WillowGame.WillowHUDGFxMovie:Start", Type.PRE)
def PtL_HUDMovieStart(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #handles showing garnished paid off messages as well as taking a dollar for the always on screen option
    #the only way i could find to show the money correctly was to take a dollar and then add one
    global loan_paid
    if loan_paid:
        show_loan_paid_off(True, "garnished")
        loan_paid = False

    if options.oidShowMoney.value:
        with prevent_hooking_direct_calls():
            obj.MoneyWidgetInterval=1000000
            PtL_SetDangerousIconDifference.enable()
            get_pc().PlayerReplicationInfo.AddCurrencyOnHand(0, -1)
    else:
        PtL_SetCredits.disable()
        PtL_PlayUISound.disable()
        PtL_SetDangerousIconDifference.disable()
        obj.MoneyWidgetInterval=4


@hook("WillowGame.WillowHUDGFxMovie:SetDangerousIconDifference", Type.POST)
def PtL_SetDangerousIconDifference(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #adds back the stolen dollar
    with prevent_hooking_direct_calls():
        get_pc().PlayerReplicationInfo.AddCurrencyOnHand(0, 1)
        obj.SetCredits(1)
        PtL_SetDangerousIconDifference.disable()
        return 
    

@hook("WillowGame.WillowHUDGFxMovie:SetCredits", Type.PRE)
def PtL_SetCredits(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #gives the player a dollar for the always on screen option, after eridum is picked up
    with prevent_hooking_direct_calls():
        get_pc().PlayerReplicationInfo.AddCurrencyOnHand(0, 1)
        PtL_SetCredits.disable()
        return Block


@hook("GearboxFramework.GearboxGFxMovie:PlayUISound", Type.POST)
def PtL_PlayUISound(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> Any:
    #handles reshowing the money after eridium is picked up
    if options.oidShowMoney.value:
        if args.UIEvent == "EridiumIn":
            obj.MoneyWidgetInterval=1000000
        elif args.UIEvent == "EridiumOut":
            with prevent_hooking_direct_calls():
                PtL_SetCredits.enable()
                get_pc().PlayerReplicationInfo.AddCurrencyOnHand(0, -1)


@hook("WillowGame.WillowPawn:TossInventory")
@hook("WillowGame.WillowPlayerController:ThrowInventory")
@hook("WillowGame.WillowPlayerController:ServerThrowInventory")
def PtL_ItemThrown(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction) -> None:
    #whitelists player dropped items
    if func.func.Name in ["ThrowInventory", "ServerThrowInventory"]:
        args.InventoryObject.PickupMessage = "PtL_whitelist"
    else:
        if obj.Class.Name == "WillowPlayerPawn":
            args.Inv.PickupMessage = "PtL_whitelist"



@keybind("repo test")
def repo_test() -> None:
    PtL_SetupBalancedPopulationActor.enable()
    options.ingame_loanamount = 10000
    options.ingame_paidtime = 15000
    options.ingame_raidtime = 10000
    amount_to_spawn = 1

    pc = get_pc()

    radius = 350.0
    spacing = 200.0

    # Convert spacing to angle step (radians → degrees)
    angle_step = math.degrees(spacing / radius)

    base_yaw = pc.Rotation.Yaw + 180  # behind the player

    for i in range(amount_to_spawn):
        yaw = base_yaw + (i * angle_step)
        rad = math.radians(yaw)

        spawned_actor = spawn_repo_man(rad, pc)

        if i == 0:
            if spawned_actor:
                print("spawned")


@keybind("Show Owed Load Amount")
def value_test():
    if options.ingame_loanamount > 0:
        message = f"Current loan amount owed: ${options.ingame_loanamount}"
    else:
        message = "You don't have a loan with Marcus."

    show_hud_message("Pay to Loot", message)
    #repo_tutorial_box.show()
    #print(f"loan value {options.ingame_loanamount}")
    #print(f"paid time {options.ingame_paidtime}")
    #print(f"raid time {options.ingame_raidtime}")
    #print(f"loan tut {options.oidSeenTutorial.value}")
    #print(f"raid tut {options.oidRaidTutorial.value}")
    #options.oidLoan.value = 168335
    #options.save_all_options()


def on_save():
    options.oidLoan.value = options.ingame_loanamount
    options.oidLastPaidTime.value = options.ingame_paidtime
    options.oidLastRaidTime.value = options.ingame_raidtime
    options.oidRaidMaxTime.value = options.ingame_raidmax

def on_load():
    options.ingame_loanamount = options.oidLoan.value
    options.ingame_paidtime = options.oidLastPaidTime.value
    options.ingame_raidtime = options.oidLastRaidTime.value
    options.ingame_raidmax = options.oidRaidMaxTime.value
    options.ingame_seenraidtut = options.oidRaidTutorial.value


mod = build_mod(
            keybinds = [value_test],
            options = [options.oidShowMoney],
            hooks= [
            PtL_SpawnPickupParticles,
            PtL_AreaLoaded,
            PtL_DisplayMarketingUnlockDialogIfNecessary,
            PtL_GrantNewMarketingCodeBonuses,
            PtL_HUDMovieStart,
            PtL_PlayUISound,
            PtL_Behavior_AITakeMoney,
            PtL_UpdateLcdFriendsList,
            PtL_SecondUse,
            PtL_PickupableLoan,
            PtL_SetUpRewardsPage,
            PtL_SetSparkTimers,
            PtL_UpdateSparkLocation,
            PtL_Populate,
            PtL_PlayerSoldItem,
            PtL_GetCurrencyReward,
            PtL_ServerGrantMissionRewards,
            PtL_ItemThrown,
            PtL_SetupBalancedPopulationActor,
            PtL_Behavior_SpawnItems,
            ])

register_save_options(mod, save_options=[
                                        options.oidLoan, 
                                        options.oidLastPaidTime, 
                                        options.oidLastRaidTime, 
                                        options.oidSeenTutorial,
                                        options.oidRaidTutorial,
                                        options.oidRaidMaxTime,
                                        ])

