import json
from math import cos, pi, sin, sqrt
import random
import time
import numpy as np

from pygomas.agent import Agent
from pygomas.bditroop import BDITroop
from pygomas.sight import Sight
from pygomas.config import *
from pygomas.pack import PACK_MEDICPACK, PACK_AMMOPACK
from typing import Any, Callable, Dict, List, Tuple
from agentspeak import Actions, grounded

Vector3 = Tuple[float, float, float]
TroopType = int
PackType = int
PI = pi

COMM_FILE = "bdi_mem.json"
TIME_LOCALITY = 1
PACK_TIME_LOCALITY = 0.05
PERSISTENCE = 10

TROOP_RADIUS = 10

class Item:
    def __init__(self, id: int, last_seen: float, position: Vector3):
        self.id = id
        self.last_seen = last_seen
        self.position = position
        
    def to_dict(self):
        return {
            "id": self.id,
            "last_seen": self.last_seen,
            "position": self.position
        }
        
class Pack(Item):
    def __init__(self, id:int, last_seen: float, position: Vector3, type: PackType):
        super().__init__(id, last_seen, position)
        self.type = type
    
    def to_dict(self):
        base = super().to_dict()
        base['type'] = self.type
        return base

# General utility function generation
def random_point_around(point: List[float], min_distance: float, max_distance: float, rng: random.Random):
    angle = rng.random() * 2 * PI
    dist = min_distance + rng.random() * (max_distance - min_distance)
    return (
        point[0] + cos(angle) * dist,
        point[1],
        point[2] + sin(angle) * dist
    )
    
def vec_add(v1: Vector3, v2: Vector3) -> Vector3:
    return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])
def vec_mult(v: Vector3, m: float) -> Vector3:
    return (v[0] * m, v[1] * m, v[2] * m)
def vec_addmult(v1: Vector3, v2: Vector3, m: float) -> Vector3:
    return vec_add(v1, vec_mult(v2, m)) 
def vec_sub(v1: Vector3, v2: Vector3) -> Vector3: 
    return vec_addmult(v1, v2, -1)
def vec_norm_squared(v: Vector3) -> float:
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2]
def vec_normalize(v: Vector3, norm = 1.0) -> Vector3:
    length = sqrt(vec_norm_squared(v))
    if length == 0: return v
    return vec_mult(v, norm / length)

def visualizer(agent: Agent, v: List[Tuple[str,any]]):
    here = agent.movement.position
    here = [here.x, here.y, here.z]
    dest = agent.movement.destination
    dest = [dest.x, dest.y, dest.z]
    try:
        safest = agent.safest_point()
    except:
        safest = [-1,-1,-1]
    data = {
        "enemy_memory": [e.to_dict() for e in agent.enemy_memory.values()],
        "ally_memory": [e.to_dict() for e in agent.ally_memory.values()],
        "pack_memory": [p.to_dict() for p in agent.pack_memory.values()],
        "time": time.time(),
        "pos": here,
        "dest": dest,
        "health": agent.health,
        "ammo": agent.ammo,
        "safest_point": safest
    }
    for (name, value) in v:
        data[name] = str(value).replace("(","[").replace(")","]")
        try: # Try to convert the data into its raw value, ideal for turning ASL tuples into JSON lists
            parsed = json.loads(data[name])
            data[name] = parsed
        except:
            pass
        
    try:
        with open(COMM_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        agent.warn(f"ERROR DUMPING VISUALIZER DATA INTO JSON FILE: {e}")
        return
    
def get_positions_around(center: Vector3, radius: float, count: int):
    for angle in [i * 2 * PI / count for i in range(count)]:
        yield (
            center[0] + cos(angle) * radius,
            center[1],
            center[2] + sin(angle) * radius
        )

def get_compatible_item_or_new(item: Item, item_memory: Dict[int, Item], locality: float, filter: Callable[[Item], bool] = lambda _: True):
        candidates = item_memory.values()
        candidates = [c for c in candidates if filter(c)]
        candidates.sort(key=lambda x: vec_norm_squared(vec_sub(x.position, item.position)))
        if candidates == []:
            return len(item_memory)
        
        most_likely = candidates[0]
        distance = sqrt(vec_norm_squared(vec_sub(most_likely.position, item.position)))
        dt = item.last_seen - most_likely.last_seen
        if dt * locality > distance:
            return most_likely.id
        
        return len(item_memory)

def _closest_recent_items_to_reference(position: Vector3, memory: Dict[int, Item], time_locality = 0) -> List[Item]:
    now = time.time()
    candidates = []
    for id, item in memory.items():
        delta_t = now - item.last_seen
        weight_t = PERSISTENCE - delta_t
        if weight_t <= 0: continue
        distance = sqrt(vec_norm_squared(vec_sub(position, item.position)))
        weight = distance - weight_t * time_locality
        candidates.append((weight, id, item))
    candidates.sort()
    return [c[-1] for c in candidates]

def closest_packs(position: Vector3, memory: Dict[int, Pack]) -> List[Pack]:
    return _closest_recent_items_to_reference(position, memory, PACK_TIME_LOCALITY)

def raycast(origin: Vector3, direction: Vector3, targets: List[Vector3], radius: float) -> int:
    """Casts a ray from the origin position in a given direction, and checks whether it would hit spheres located at targets with a given radius.

    Returns:
        int: The index within targets of the hit object, or -1 if none are hit
    """
    # flattening to two dimensions
    origin = np.array([origin[0],origin[2]])
    direction = np.array([direction[0],direction[2]])
    targets = [(i, np.array([t[0],t[2]])) for i,t in enumerate(targets)]
    targets_sorted = sorted(targets,key=lambda x: np.linalg.norm(origin - x[-1]))
    dirnorm = np.linalg.norm(direction)
    for i,t in targets_sorted:
        d = np.cross(direction, t - origin)/dirnorm
        if d <= radius:
            return i
    return -1
    
def common_init(agent: BDITroop, *args, **kwargs):
    agent.rng = random.Random()
    agent.health_pack_memory = {}
    agent.ammo_pack_memory = {}

def define_common_actions(agent: BDITroop, actions: Actions):
    def here() -> Vector3:
        r = agent.movement.get_position()
        return (r.x, r.y, r.z)
    
    @actions.add_function(".now", ())
    def _get_now():
        return time.time()
    
    @actions.add_function(".can_shoot", (Tuple, Tuple))
    def _can_shoot(pos: Vector3, target: Vector3) -> False:
        fov_objects : List[Sight] = agent.fov_objects
        friends : List[Vector3] = []
        enemies : List[Vector3] = []
        for o in fov_objects:
            if o.get_team() == TEAM_NONE:
                continue 
            v = o.get_position()
            vec3 = (v.x, v.y, v.z)
            if o.get_team() == agent.team:
                friends.append(vec3)
            else:
                enemies.append(vec3)
        
        all_positions = friends + enemies
        hit_index = raycast(pos, vec_sub(target,pos), all_positions, TROOP_RADIUS)
        
        value = hit_index < 0 or hit_index >= len(friends)
        if (not value):
            print(f"Soldier at position {pos} would hit friend at position {friends[hit_index]} if shooting {target}")
        return value
    
    @actions.add(".pack_taken", 2)
    def _pack_used(pos: Vector3, pack_type: PackType):
        mem = agent.health_pack_memory if pack_type == PACK_MEDICPACK else agent.ammo_pack_memory
        if pos in mem:
            del mem[pos]
        yield
    
    @actions.add_function(".random_point_around", (Tuple, float, float))
    def _random_point_around(pos: Vector3, min_dist: float, max_dist: float):
        return random_point_around(pos, min_dist, max_dist, agent.rng)
    
    @actions.add_function(".register_pack", (Tuple, int))
    def _handle_pack(pos: Vector3, pack_type: PackType):
        mem = agent.health_pack_memory if pack_type == PACK_MEDICPACK else agent.ammo_pack_memory
        if pos in mem:
            mem[pos].last_seen = time.time()
            return False
        
        p = Pack(0, time.time(), pos, pack_type)
        mem[pos] = p
        return True
    
    @actions.add_function(".nearest_health_pack", (Tuple,))
    def _nearest_health_pack(position: Vector3):
        return closest_packs(position, agent.health_pack_memory)
    
    @actions.add_function(".nearest_ammo_pack", (Tuple,))
    def _nearest_ammo_pack(position: Vector3):
        return closest_packs(position, agent.ammo_pack_memory)
    
    @actions.add_function(".distance", (Tuple, Tuple))
    def _distance(v_a: Vector3, v_b: Vector3):
        return sqrt(vec_norm_squared(vec_sub(v_a,v_b)))
    
    @actions.add_function(".str", (object,))
    def _str(obj: any):
        return str(obj)
        