from mods_base import build_mod#type:ignore
from typing import Any #type:ignore
from unrealsdk import make_struct, find_class#type:ignore
from mods_base import hook, build_mod  #type:ignore
from unrealsdk.hooks import Type, add_hook, Block, remove_hook #type:ignore
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct #type:ignore

ClassNames = ["WillowClassMod", "WillowGrenadeMod", "WillowArtifact", "WillowShield"]
IndexTracker = [10, False]
DialogBoxEventData = make_struct("EventData",Type="focusIn")

@hook("WillowGame.StatusMenuExGFxMovie:HandleInputKey")
def StatusMenuExGFxMovie(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:   
    Key = GetMovementKey(__args.ukey, obj.WPCOwner)
    InputFunc = obj.__OnInputKey__Delegate
    if Key:
        GlobalHandleInput(InputFunc, obj.GetControllerID(), Key, __args.uevent)
        return
    
    if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Use"):
        InputFunc(obj.GetControllerID(), "Enter", __args.uevent)
        return
    
    if obj.GetCurrentTab() == 3 and __args.uevent == 0:
        if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Reload"):
            Thing = obj.InventoryPanel.GetSelectedThing()
            if Thing:
                CycleMark(obj, Thing, True)
                return
        if obj.InventoryPanel.bInEquippedView:
            if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("UseSecondary"):
                InvPanel = obj.InventoryPanel
                Thing = InvPanel.GetSelectedThing()
                if Thing and InvPanel.SlotsUsed < InvPanel.MaxCapacity:
                    InvPanel.UnreadyThing(Thing)
                    obj.PlayUISound('UnEquip')
        else:
            movie = obj.InventoryPanel.BackpackPanel
            if __args.ukey == "Home":
                movie.SetSelectedIndexByThing(movie.GetThingByIndex(1))
            elif __args.ukey == "End":
                for i in range(obj.InventoryPanel.MaxCapacity + 1, -1, -1):
                    if movie.GetThingByIndex(i):
                        movie.SetSelectedIndexByThing(movie.GetThingByIndex(i))
                        break
        
    return

@hook("WillowGame.OptionsGFxMovie:HandleInputKey", Type.PRE)
def OptionsGFxMovie(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:
    global ListIndex
    ListIndex = obj.TheList.DataProviderStack[len(obj.TheList.DataProviderStack) - 1].SelectedIndex
    if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
        obj.__OnInputKey__Delegate(0, "Up", __args.uevent)
    elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
        obj.__OnInputKey__Delegate(0, "Down", __args.uevent)
    elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("StrafeLeft"):
        obj.__OnInputKey__Delegate(0, "Left", __args.uevent)
    elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("StrafeRight"):
        obj.__OnInputKey__Delegate(0, "Right", __args.uevent)

    #purchace
    elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Use") and __args.uevent == 1:
        obj.TheList.OnClikEvent(make_struct("EventData",Type="itemClick", Index=ListIndex))
    
    return


@hook("WillowGame.StatusMenuInventoryPanelGFxObject:StartEquip")
def StartEquip(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:   
    Thing = obj.GetSelectedThing()
    if not Thing or Thing.Class.Name not in ClassNames or obj.bInEquippedView:
        return

    if obj.CanReady(Thing):
        obj.BackpackPanel.SaveState()
        obj.CompleteEquip()
        obj.ParentMovie.RefreshInventoryScreen(True)
        obj.BackpackPanel.RestoreState()
        return Block
    return    


@hook("WillowGame.CustomizationGFxMovie:MainInputKey")
def CustomizationGFxMovie(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:   
    if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Reload") and __args.uevent == 1:
        PC = obj.WPCOwner
        if PC.GetSkillTreeResetCost() <= PC.PlayerReplicationInfo.GetCurrencyOnHand(0):
            PC.ServerPurchaseSkillTreeReset()
            MovieSounds = find_class('WillowGFxMovie').ClassDefaultObject.LookupFallbackAkEventFromGlobalsDefinition('ChaChing')
            if MovieSounds:
                obj.PlayUIAkEvent(MovieSounds)
            
            obj.BeginClosing()
    return

            
@hook("WillowGame.CustomizationGFxMovie:SetTooltips")
def SetTooltips(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:   
    VariableObject = obj.GetVariableObject(obj.TooltipsPath)
    obj.CharacterCustomizationInfoCard.DisplayRespecCard()
    if VariableObject:
        if obj.bSelectingFromList:
            return
        else:
            PC = obj.WPCOwner
            Cost = PC.GetSkillTreeResetCost()
            if Cost <= PC.PlayerReplicationInfo.GetCurrencyOnHand(0):
                LocalizedString = obj.ResolveDataStoreMarkup(obj.Localize("CharacterCustomization", "Tooltips", "WillowMenu"))
                String = f"{LocalizedString}   {GetRespecTip(PC, Cost)}"
                VariableObject.SetString("htmlText", String)
                return Block
    return


@hook("WillowGame.VendingMachineExGFxMovie:MainInputKey")
def VendingMachineExGFxMovie(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:   
    Key = GetMovementKey(__args.ukey, obj.WPCOwner)
    if Key:
        GlobalHandleInput(obj.MainInputKey, obj.GetControllerID(), Key, __args.uevent)
    
    elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("UseSecondary"):
        obj.MainInputKey(obj.GetControllerID(), "Enter", __args.uevent)

    elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("StatusMenu"):
        obj.TwoPanelInterface.NormalInputKey(obj.GetControllerID(), "Escape", 0)

    if obj.TwoPanelInterface and not obj.TwoPanelInterface.bOnLeftPanel and __args.uevent == 1:
        movie = obj.TwoPanelInterface.PlayerPanel
        if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Reload"):
            Thing = obj.TwoPanelInterface.GetSelectedThing()
            if Thing:
                CycleMark(obj, Thing, False)


        elif __args.ukey == "Home":
            movie.SetSelectedIndexByThing(movie.GetThingByIndex(1))
        elif __args.ukey == "End":
            Capacity = obj.WPCOwner.GetInventoryPawn().InvManager.GetUnreadiedInventoryMaxSize()
            for i in range(Capacity - 1, -1, -1):
                if movie.GetThingByIndex(i):
                    movie.SetSelectedIndexByThing(movie.GetThingByIndex(i))
                    break
            
    return


@hook("WillowGame.VehicleSpawnStationGFxMovie:HandleKeyDefaults")
def SharedInfoCardInputKey(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:   
    if obj.bChoosingFamily:
        if __args.uevent == 0 or __args.uevent == 2:
            Key = GetMovementKey(__args.ukey, obj.WPCOwner)
            if Key:
                GlobalHandleInput(obj.VehicleFamilyInputKey, obj.GetControllerID(), Key, __args.uevent)
    return


@hook("WillowGame.WillowGFxDialogBox:HandleInputKey")
def WillowGFxDialogBox(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None:   
    if __args.uevent == 0 or __args.uevent == 2:
        if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
            obj.OnWidget1Focused(DialogBoxEventData)
        elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
            obj.OnWidget0Focused(DialogBoxEventData)

    elif __args.uevent == 1 and __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Use"):
        obj.Accepted(obj.GetControllerID())
    return


@hook("WillowGame.QuestAcceptGFxMovie:HandleInputKey")
def QuestAcceptGFxMovie(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None: 
    Key = GetMovementKey(__args.ukey, obj.WPCOwner)
    if Key:
        GlobalHandleInput(obj.HandleInputKey, obj.GetControllerID(), Key, __args.uevent)
    
    if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Use") and __args.uevent == 1:
        obj.HandleInputKey(obj.GetControllerID(), "Enter", __args.uevent)
    return

@hook("WillowGame.QuestAcceptGFxMovie:HandleRewardInputKey", Type.PRE)
@hook("WillowGame.LatentRewardGFxMovie:HandleRewardInputKey", Type.PRE) 
def HandleRewardInputKey(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None: 
    if __args.uevent == 0:
        if obj.RewardObject.GetNumItems() > 1:
            if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
                obj.extOnFocusedChoice(0)
            elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
                obj.extOnFocusedChoice(1)

        if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Use"):
            obj.AcceptReward(obj.RewardObject.RewardChoiceFocused)
    return


@hook("WillowGame.FastTravelStationGFxMovie:HandleInputKey")
def FastTravelStationGFxMovie(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None: 
    if obj.PreviousSelectionIndex == 0 or obj.PreviousSelectionIndex == -1:
        obj.PreviousSelectionIndex = 1
    if __args.uevent == 0 or __args.uevent == 2:
        if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
            obj.ScrollLocationListUp(obj.PreviousSelectionIndex)
        elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
            obj.ScrollLocationListDown(obj.PreviousSelectionIndex)

        elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Use"):
                obj.extActivate(obj.PreviousSelectionIndex)
        
        elif __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("StatusMenu"):
            obj.HandleInputKey(obj.GetControllerID(), "Escape", 1)

    return


@hook("WillowGame.FrontendGFxMovie:DefaultHandleInputKey")
def FilterButtonInput(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None: 
    ListIndex = obj.TheList.GetSelectedIndex()
    global IndexTracker
    if IndexTracker[0] < 1: #this gross thing is here because when you hit an arrow key to wrap, it would go up/down an extra item because the arrow key was already down
        IndexTracker[0] += 1
        if IndexTracker[1]:
            obj.TheList.SetSelectedIndex(0)
        else:
            obj.TheList.SetSelectedIndex(len(obj.TheList.IndexToEventId) - 1)
    else:
        IndexTracker = [10, False]

    if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("Use") and __args.uevent == 1:
        obj.TheList.OnClikEvent(make_struct("EventData",Type="itemClick", Index=ListIndex))

    if __args.uevent == 0 or __args.uevent == 2:
        if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
            if ListIndex > 0:
                ListIndex -= 1
            else:
                ListIndex = len(obj.TheList.IndexToEventId) - 1
            obj.TheList.SetSelectedIndex(ListIndex)

        if __args.ukey == obj.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
            if ListIndex < len(obj.TheList.IndexToEventId) - 1:
                ListIndex += 1
            else:
                ListIndex = 0
            obj.TheList.SetSelectedIndex(ListIndex)

        if __args.ukey == "Up" and ListIndex == 0:
            IndexTracker = [0, False]

        if __args.ukey == "Down" and ListIndex == len(obj.TheList.IndexToEventId) - 1:
            IndexTracker = [0, True]
    return


@hook("WillowGame.TwoPanelInterfaceGFxObject:PanelInputKey")
def TwoPanelInterfaceGFxObject(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None: 
    if obj.ParentMovie.Class.Name == "VendingMachineExGFxMovie":
        return
    

    Key = GetMovementKey(__args.ukey, obj.ParentMovie.WPCOwner)
    if Key:
        GlobalHandleInput(obj.PanelInputKey, obj.ParentMovie.GetControllerID(), Key, __args.uevent)


    elif __args.ukey == obj.ParentMovie.WPCOwner.PlayerInput.GetKeyForAction("Use"):
        obj.PanelInputKey(obj.ParentMovie.GetControllerID(), "Enter", __args.uevent)

    elif __args.ukey == obj.ParentMovie.WPCOwner.PlayerInput.GetKeyForAction("StatusMenu"):
        obj.NormalInputKey(obj.ParentMovie.GetControllerID(), "Escape", 0)

    if __args.uevent == 1:
        if __args.ukey == obj.ParentMovie.WPCOwner.PlayerInput.GetKeyForAction("Reload") and obj.bOnLeftPanel:
            Thing = obj.GetSelectedThing()
            if Thing:
                CurrentMark = Thing.GetMark()
                CurrentMark += 1
                if CurrentMark > 2:
                    CurrentMark = 0
                obj.ParentMovie.PlayUISound('MenuBack')
                Thing.SetMark(CurrentMark)
                obj.RefreshRightPanel()
                return


        CurrentPanel = obj.StoragePanel if obj.bOnLeftPanel else obj.PlayerPanel
        if __args.ukey == "Home":
            CurrentPanel.SetSelectedIndexByThing(CurrentPanel.GetThingByIndex(1))
        elif __args.ukey == "End":
            if obj.bOnLeftPanel:
                try:
                    Capacity = obj.ParentMovie.BankStorage.GetMaxSize() + 1
                except:
                    Capacity = obj.ParentMovie.StashStorage.GetMaxSize() + 1
            else:
                Capacity = obj.ParentMovie.WPCOwner.GetInventoryPawn().InvManager.GetUnreadiedInventoryMaxSize() - 1
            for i in range(Capacity, -1, -1):
                if CurrentPanel.GetThingByIndex(i):
                    CurrentPanel.SetSelectedIndexByThing(CurrentPanel.GetThingByIndex(i))
                    break

    return


def GlobalHandleInput(Func, *Args) -> None:
    Func(*Args)
    return

def GetMovementKey(Key, PC) -> str:
    if Key == PC.PlayerInput.GetKeyForAction("MoveForward"):
        return "Up"
    elif Key == PC.PlayerInput.GetKeyForAction("MoveBackward"):
        return "Down"
    elif Key == PC.PlayerInput.GetKeyForAction("StrafeLeft"):
        return "Left"
    elif Key == PC.PlayerInput.GetKeyForAction("StrafeRight"):
        return "Right"
    else:
        return ""


def CycleMark(Movie, Thing, bInStatusMenu):
    CurrentMark = Thing.GetMark()
    Panel = None
    if bInStatusMenu:
        if not Movie.InventoryPanel.bInEquippedView:
            Panel = Movie.InventoryPanel.BackpackPanel
            Panel.SaveState()

    elif not Movie.IsCurrentSelectionSell():
        return

    if CurrentMark >= 2:
        CurrentMark = 0
    else:
        CurrentMark += 1

    def SetMark(obj: UObject, __args: WrappedStruct, __ret: Any, __func: BoundFunction) -> None: 
        if Panel:
            Panel.RestoreState()
        remove_hook("WillowGame.WillowGameViewportClient:Tick", Type.PRE, "SetMark")
        return

    Thing.SetMark(CurrentMark)
    Movie.PlayUISound('MenuBack')
    if bInStatusMenu:
        Movie.RefreshInventoryScreen(True)
    else:
        Movie.Refresh()
    add_hook("WillowGame.WillowGameViewportClient:Tick", Type.PRE, "SetMark", SetMark)
    return

def GetRespecTip(PC, Cost) -> str:
    Key = PC.PlayerInput.GetKeyForAction("Reload")
    return f"[{Key}] Respec: ${Cost}"

build_mod()