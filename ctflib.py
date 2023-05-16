import json
from math import cos, pi, sin, sqrt
import random
import time

from pygomas.agent import Agent
from typing import Dict, List, Tuple
from agentspeak import Actions, grounded


Vector3 = Tuple[float, float, float]
TroopType = int
PackType = int
PI = pi

COMM_FILE = "bdi_mem.json"
TIME_LOCALITY = 1
PERSISTENCE = 10

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
def _random_point_around(point: List[float], min_distance: float, max_distance: float, rng: random.Random):
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
    here = agent.here()
    dest = agent.movement.destination
    dest = [dest.x, dest.y, dest.z]
    safest = agent.safest_point()
    data = {
        "enemy_memory": [e.to_dict() for e in agent.enemy_memory.values()],
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

def attack_formation_around(center: Vector3, radius: float, count: int):
    pass


def _closest_recent_items_to_reference(position: Vector3, memory: Dict[int, Item]) -> List[Item]:
    now = time.time()
    candidates = []
    for id, item in memory.items():
        delta_t = now - item.last_seen
        weight_t = PERSISTENCE - delta_t
        if weight_t <= 0: continue
        distance = sqrt(vec_norm_squared(vec_sub(position, item.position)))
        weight = distance - weight_t * TIME_LOCALITY
        candidates.append((weight, id, item))
    candidates.sort()
    return [c[-1] for c in candidates]

def _closest_recent_items(position: Vector3, memory: Dict[int, Item]) -> List[Item]:
    return _closest_recent_items_to_reference(position, memory)

def closest_packs(position: Vector3, memory: Dict[int, Pack]) -> List[Pack]:
    return _closest_recent_items(position, memory)

def define_common_actions(agent: Agent, actions: Actions):
    @actions.add_function(".now", ())
    def _get_now():
        return time.time()
        