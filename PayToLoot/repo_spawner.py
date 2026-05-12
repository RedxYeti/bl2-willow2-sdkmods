from mods_base import ObjectFlags, get_pc, ENGINE
from unrealsdk import find_object,make_struct,find_class,load_package,construct_object
from unrealsdk.unreal import IGNORE_STRUCT,UObject
import math

pop_def=None
region_def = None
smoke_template = None

default_pop_factory = find_class("PopulationFactoryBalancedAIPawn").ClassDefaultObject
pop_factory = construct_object("PopulationFactoryBalancedAIPawn", default_pop_factory, "default_factory", flags=ObjectFlags.KEEP_ALIVE)
ai_class = None

Gbx_globals = find_class('GearboxFramework.GearboxGlobals').ClassDefaultObject
emptyvec = make_struct("Vector")
emptyrot = make_struct("Rotator")


def get_pop_master():
    return Gbx_globals.GetGearboxGlobals().GetPopulationMaster()


def create_repo_spawner() -> None:
    global pop_def, region_def, smoke_template, ai_class

    if pop_def:
        return

    load_package('Fridge_P')
    load_package('Fridge_Combat')
    load_package("Boss_Volcano_Combat_Monster")



    vanilla_spawner = find_object('WillowPopulationDefinition', 'GD_Population_Bandit.Population.PopDef_BanditMix_Fridge')
    vanilla_spawner.ObjectFlags |= 0x4000

    smoke_template = find_object('ParticleSystem','FX_CREA_Rakk.Particles.Part_Rakkman_SmokeGrenade')
    smoke_template.ObjectFlags |= 0x4000
    
    pop_def = construct_object(
        "WillowPopulationDefinition",
        vanilla_spawner.Class.ClassDefaultObject,
        "repo_pop_def",
        flags=ObjectFlags.KEEP_ALIVE,
        template_obj=vanilla_spawner
    )

    spawn_factory = construct_object("PopulationFactoryBalancedAIPawn",
                                     pop_def.Class.ClassDefaultObject,
                                     "repo_spawn_factory",
                                     flags=ObjectFlags.KEEP_ALIVE,
                                     template_obj=vanilla_spawner.ActorArchetypeList[2].SpawnFactory
                                     )
    
    pawn_balance = construct_object("AIPawnBalanceDefinition",
                                    pop_def.Class.ClassDefaultObject,
                                    "repo_pawn_balance",
                                    flags=ObjectFlags.KEEP_ALIVE,
                                    template_obj=find_object('AIPawnBalanceDefinition','GD_Population_Rat.Balance.PawnBalance_RatThief')
                                    )
    
    ai_class = construct_object("AIClassDefinition",
                                pop_def.Class.ClassDefaultObject,
                               "repo_ai_class",
                                flags=ObjectFlags.KEEP_ALIVE,
                                template_obj=find_object('AIClassDefinition','GD_RatThief.Character.CharClass_RatThief')
                                )   
         
    ai_def = construct_object("WillowAIDefinition",
                                pop_def.Class.ClassDefaultObject,
                               "repo_ai_def",
                                flags=ObjectFlags.KEEP_ALIVE,
                                template_obj=find_object('WillowAIDefinition','GD_RatThief.Character.AIDef_RatThief')
                                )
    
    ai_class.AIDef = ai_def
    ai_def.NodeList[3] = ai_def.NodeList[5]
    
    ai_pawn = construct_object("WillowAIPawn",
                                pop_def.Class.ClassDefaultObject,
                               "repo_ai_pawn",
                                flags=ObjectFlags.KEEP_ALIVE,
                                template_obj=find_object('WillowAIPawn','GD_RatThief.Character.Pawn_RatThief')
                                )
    
    ai_pawn.AIClass = ai_class
    ai_pawn.ActorSpawnCost=0
    ai_pawn.Allegiance = find_object('PawnAllegiance', 'GD_FinalBoss.AI.Allegiance_FinalBoss')
    pawn_balance.AIPawnArchetype=ai_pawn
    spawn_factory.PawnBalanceDefinition = pawn_balance
    pawn_balance.PlayThroughs[0].DisplayName = "Repo Man"
    pawn_balance.PlayThroughs[1].DisplayName = "Repo Man"
    pop_def.ActorArchetypeList = [vanilla_spawner.ActorArchetypeList[2]]
    pop_def.ActorArchetypeList[0].SpawnFactory = spawn_factory
    pop_def.ActorArchetypeList[0].Probability.BaseValueConstant = 1

    get_pc().WorldInfo.ForceGarbageCollection()


def spawn_repo_man(rad: float, pc) -> bool:
    pawn = pc.Pawn

    #not coop safe, SpawnForMap might be
    opportunity = pc.Spawn(find_class("WillowPopulationOpportunityPoint"))
    opportunity.PopulationDef = pop_def
    opportunity.IsEnabled = True
    opportunity.bNoRespawning = True

    opportunity.Location.X = pawn.Location.X + math.cos(rad) * 250
    opportunity.Location.Y = pawn.Location.Y + math.sin(rad) * 250
    opportunity.Location.Z = pawn.Location.Z - 50

    opportunity.WorldInfo.MyEmitterPool.SpawnEmitter(smoke_template, opportunity.Location, IGNORE_STRUCT)

    opportunity.DoSpawning(get_pop_master())
    
    return opportunity.bActiveSpawn


def remove_repo_men():
    pawn = ENGINE.GetCurrentWorldInfo().PawnList
    while pawn:
        if hasattr(pawn, "AIClass") and pawn.AIClass == ai_class:
            _, items =  pawn.InvManager.GetItemList([])
            for item in items:
                if item.bDropOnDeath:
                    item.DropFrom(pawn.Location, pawn.GetItemTossVelocity(item.Class.Name == "WillowWeapon"))
            ENGINE.GetCurrentWorldInfo().MyEmitterPool.SpawnEmitter(smoke_template, pawn.Location, IGNORE_STRUCT)
            pawn.OutsideWorldBounds()

        pawn = pawn.NextPawn
