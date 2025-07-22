
from mods_base import get_pc,build_mod, Library, command, Game
from argparse import Namespace
from unrealsdk import find_class, find_all
from unrealsdk.unreal import UObject, WrappedStruct
from random import choice
import math

actor_class = find_class("Actor")
is_bl2_type:bool = Game.get_current() in [Game.BL1, Game.BL2, Game.AODK, Game.TPS]

def get_distance(origin_loc:WrappedStruct,actor_loc:WrappedStruct):
    return math.sqrt(
        (origin_loc.x - actor_loc.x) ** 2
        + (origin_loc.y - actor_loc.y) ** 2
        + (origin_loc.z - actor_loc.z) ** 2
    )


def find_all_actors(max_distance:int, origin_object: UObject | None = None) -> list:
    """
    Finds every actor within a certain distance.

    Args:
        max_distance: the distance to search

    Optional:
        origin_object: the object from where to start the search from. None defaults to the player pawn
    """
    if not origin_object:
        origin_object = get_pc().Pawn



    actors:list = []
    for actor in find_all("Actor", False):
        if is_bl2_type:
            origin_location = origin_object.Location
            actor_location = actor.Location
        else:
            origin_location = origin_object.K2_GetActorLocation()
            actor_location = actor.K2_GetActorLocation()
        dist = get_distance(origin_location, actor_location)
        if dist <= max_distance:
            actors.append(actor)
    return actors


def is_actor_class(in_class:str) -> bool:
    return True if find_class(in_class)._inherits(actor_class) else False


def find_actors_of_type(actor_class:str, max_distance:int, origin_object: UObject | None = None) -> list:
    """
    Finds all actors of a specfic class within a certain distance.

    Args:
        actor_class: string name of the class you want to find
        max_distance: the distance to search

    Optional:
        origin_object: the object from where to start the search from. None defaults to the player pawn
    """

    if not is_actor_class(actor_class):
        raise AttributeError(f"{actor_class} is not an actor class")

    if origin_object:
        if not hasattr(origin_object, "Location"):
            raise AttributeError(f"{origin_object} has no attribute 'location'.")
    else:
        origin_object = get_pc().Pawn

    actors:list = []
    for actor in find_all(actor_class):
        if is_bl2_type:
            origin_location = origin_object.Location
            actor_location = actor.Location
        else:
            origin_location = origin_object.K2_GetActorLocation()
            actor_location = actor.K2_GetActorLocation()

        dist = get_distance(origin_location, actor_location)
        if dist <= max_distance:
            actors.append(actor)
    return actors


def get_random_actor_of_type(actor_class:str, max_distance:int, origin_object: UObject | None = None) -> UObject | None:
    """
    Finds a random actor of a chosen class within a certain distance.
    Returns none if no actor is found.

    Args:
        actor_class: string name of the class you want to find
        max_distance: the distance to search

    Optional:
        origin_object: the object from where to start the search from. None defaults to the player pawn
    """
    
    if not is_actor_class(actor_class):
        raise AttributeError(f"{actor_class} is not an actor class")

    if not origin_object:
        origin_object = get_pc().Pawn

    actors:list = []
    for actor in find_all(actor_class):
        if is_bl2_type:
            origin_location = origin_object.Location
            actor_location = actor.Location
        else:
            origin_location = origin_object.K2_GetActorLocation()
            actor_location = actor.K2_GetActorLocation()
        dist = get_distance(origin_location, actor_location)
        if dist <= max_distance:
            actors.append(actor)

    if len(actors):
        return choice(actors)
    
    return None


@command(splitter=lambda line: line.strip().split())
def find_actors(args: Namespace) -> None:
    if not get_pc().Pawn:
        return
    
    if args.class_type.lower() == "any":
        print(f"=======All actors found in range {args.distance} from player pawn=======")
        for actor in find_all_actors(int(args.distance)):
            print(actor)
    else:
        print(f"======={args.class_type} actors found in range {args.distance} from player pawn=======")
        for actor in find_actors_of_type(args.class_type, int(args.distance)):
            print(actor)
        

find_actors.add_argument("class_type", help="The class to search for. Use 'Any' for all classes.")
find_actors.add_argument("distance", help="The distance to check around the player.")

build_mod(cls=Library)


