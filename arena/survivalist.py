# suvivalist.py
import json
import math
import random
import time
import traceback
from loguru import logger
from spade.behaviour import OneShotBehaviour
from spade.template import Template
from spade.message import Message
from pygomas.bditroop import BDITroop
from pygomas.bdisoldier import BDISoldier
from pygomas.ontology import HEALTH
from agentspeak import Actions, grounded
from agentspeak.runtime import Agent, Intention
from math import sqrt, pi, sin, cos
from typing import Callable, Dict, List, Tuple
from agentspeak.stdlib import actions as asp_action
from termcolor import colored

from pygomas.agent import LONG_RECEIVE_WAIT
Vector3 = Tuple[float, float, float]
TroopType = int
PackType = int
PI = pi

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

# Behavioural parameters
PERSISTENCE = 7  # How long it perceives threats and items in memory as still being relevant
TIME_LOCALITY = 1 # How much it thinks objects in memory are moving away per second in terms of value over distance
TROOP_TIME_LOCALITY = 25 # How fast it thinks troops are moving from their locations while not looking at them
FLIGHT_DISTANCE = 10
MAX_FLIGHT_ATTEMPTS = 10
FLIGHT_SPREAD_DISTANCE_MIN = 5
FLIGHT_SPREAD_DISTANCE_MAX = 5
MAX_FLIGHT_SPREAD_ATTEMPTS = 3
MAX_DISTANCE = 256
CENTER = (128, 0, 128)

MAX_HEALTH = 100
MAX_AMMO = 100
MIN_AMMO = 5
LOW_HEALTH = 75
LOW_AMMO = 65
VERY_LOW_HEALTH = 15
VERY_LOW_AMMO = 15

# Ontology
STATE = "state"
FETCHING = "fetching"
ATTACK_ID = "attack_id"
ATTACK_TARGET = "attack_target"

# State Action Ontology
CENTRALIZE = "centralize"
FLEE = "flee"
ATTACK = "attack"
FETCH = "fetch"
RESET = "reset"
STATES = [CENTRALIZE, FLEE, ATTACK, FETCH, RESET]

HEALTH_PACK = 1001
AMMO_PACK = 1002
HEALTH_PACK_RESTORE = 20
AMMO_PACK_RESTORE = 20

# VISUALIZER
VISUALIZER = True
COMM_FILE = "status.json"

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

class Troop(Item):
    def __init__(self, id: int, last_seen: float, position: Vector3, type: TroopType, health: float, angle: float):
        super().__init__(id, last_seen, position)
        self.health = health
        self.angle = angle
        self.type = type
    
    def to_dict(self):
        base = super().to_dict()
        base['health'] = self.health
        base['type'] = self.type
        base['angle'] = self.angle
        return base
        
class Pack(Item):
    def __init__(self, id:int, last_seen: float, position: Vector3, type: PackType):
        super().__init__(id, last_seen, position)
        self.type = type
    
    def to_dict(self):
        base = super().to_dict()
        base['type'] = self.type
        return base

class BDISurvivalist(BDISoldier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rng = random.Random()
        self.enemy_memory : Dict[int, Troop] = dict()
        self.pack_memory : Dict[int, Pack] = dict()
        self.next_id = 1
        
        self.update = lambda v: None
        if VISUALIZER:
            self.update = self.update_visualizer
            #loop = asyncio.get_event_loop()
            #asyncio.run_coroutine_threadsafe(self.update_visualizer(), loop)
            
    def info(self, text: str):
        print(f"{colored(f'{self.name}:', 'white', 'on_light_blue')} {text}")            
    def warn(self, text: str):
        print(f"{colored(f'{self.name}:', 'black', 'on_yellow')} {text}")
    
    def update_visualizer(self, v : List[Tuple[str,any]]):
        #self.info(f"Serializing: {v}")
        here = self.here()
        dest = self.movement.destination
        dest = [dest.x, dest.y, dest.z]
        safest = self.safest_point()
        data = {
            "enemy_memory": [e.to_dict() for e in self.enemy_memory.values()],
            "pack_memory": [p.to_dict() for p in self.pack_memory.values()],
            "time": time.time(),
            "pos": here,
            "dest": dest,
            "health": self.health,
            "ammo": self.ammo,
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
            self.warn(f"ERROR DUMPING VISUALIZER DATA INTO JSON FILE: {e}")
            return
    
    def here(self) -> Vector3:
        return (self.movement.position.x, self.movement.position.y, self.movement.position.z)
        
    def random_point_around(self, point: Vector3, min_distance = 0.0, max_distance = MAX_DISTANCE):
        return _random_point_around(point, min_distance, max_distance, self.rng)
    
    def get_walkable_point_along_ray(self, pos: Vector3, direction: Vector3) -> Vector3:
        target = pos
        attempts = 0
        point_stack = []
        # Attempt to find walkable points at equal intervals along the ray
        while attempts < MAX_FLIGHT_ATTEMPTS:
            target = [target[i] + d * FLIGHT_DISTANCE for i,d in enumerate(direction)]
            if self.check_static_position(target[0],target[2]):
                return target
            point_stack.insert(0, target)
            attempts += 1
        
        # Attempt to find walkable points AROUND previously attempted points, trying the furthest points first
        for prev_target in point_stack:
            spread_attempts = 0
            while spread_attempts < MAX_FLIGHT_SPREAD_ATTEMPTS:
                target = self.random_point_around(prev_target, FLIGHT_SPREAD_DISTANCE_MIN, FLIGHT_SPREAD_DISTANCE_MAX)
                if self.check_static_position(target[0],target[2]):
                    return target
                spread_attempts += 1
                
        # If a generation along the ray fails, fallback to a random point within 50 units
        return self.generate_escape_position()
    
    def safest_point(self):
        now : float = time.time()
        here : Vector3 = self.here()
        sum_weights = 0.0
        danger_peak = (0.0,0.0,0.0)
        for enemy in self.enemy_memory.values():
            # Prioritize moving away from enemies seen RECENTLY at HIGH HP
            w = max(0.0, PERSISTENCE - (now - enemy.last_seen)) * enemy.health # WEIGHT
            sum_weights += w
            danger_peak = vec_addmult(danger_peak, enemy.position, w)
        if sum_weights == 0:
            return self.random_point_around(CENTER, 0, 10)
        flight_direction = vec_normalize(vec_addmult(here, danger_peak, -1 / sum_weights))
        # Flight direction is a vector pointing to the safest position
        # Target contains the tentative target location
        final_target = self.get_walkable_point_along_ray(here, flight_direction)
        return tuple(final_target)
    
    def should_flee(self) -> bool:
        now = time.time()
        relevant_enemies = [e for e in self.enemy_memory.values() if e.last_seen + PERSISTENCE > now]
        return relevant_enemies == []
    
    def _closest_recent_items_to_reference(self, memory: Dict[int, Item], position: Vector3) -> List[Item]:
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
    
    def _closest_recent_items(self, memory: Dict[int, Item]) -> List[Item]:
        here = self.here()
        return self._closest_recent_items_to_reference(memory, here)
    
    def closest_recent_troops(self) -> List[Troop]:
        return self._closest_recent_items(self.enemy_memory)
        
    def closest_recent_packs(self) -> List[Pack]:
        return self._closest_recent_items(self.pack_memory)
    
    def closest_critical_troops(self):
        return [t for t in self.closest_recent_troops() if t.hp <= VERY_LOW_HEALTH]
    
    def closest_health_packs(self):
        return [p for p in self.closest_recent_packs() if p.type == HEALTH_PACK]
    
    def closest_ammo_packs(self):
        return [p for p in self.closest_recent_packs() if p.type == AMMO_PACK]
    
    def _get_compatible_item_or_new(self, item: Item, item_memory: Dict[int, Item], locality: float, filter: Callable[[Item], bool] = lambda _: True):
        candidates = self._closest_recent_items_to_reference(item_memory, item.position)
        candidates = [c for c in candidates if filter(c)]
        if candidates == []:
            self.next_id += 1
            return self.next_id - 1
        
        most_likely = candidates[0]
        distance = sqrt(vec_norm_squared(vec_sub(most_likely.position, item.position)))
        dt = item.last_seen - most_likely.last_seen
        if dt * locality > distance:
            return most_likely.id
        
        self.next_id += 1
        return self.next_id - 1
    
    def get_compatible_troop_or_new(self, item: Troop):
        min_time = time.time() - PERSISTENCE
        self.enemy_memory = {id: item for id, item in self.enemy_memory.items() if item.last_seen > min_time}
        return self._get_compatible_item_or_new(item, self.enemy_memory, TROOP_TIME_LOCALITY)
        
    def get_compatible_pack_or_new(self, item: Pack):
        min_time = time.time() - PERSISTENCE
        self.pack_memory = {id: item for id, item in self.pack_memory.items() if item.last_seen > min_time}
        return self._get_compatible_item_or_new(item, self.pack_memory, 0.01, lambda p: p.type == item.type)
        
    
    def add_custom_actions(self, actions : Actions):
        super().add_custom_actions(actions)
        
        @actions.add(".update", 1)
        def _update(agent, term, intention):
            args = grounded(term.args, intention.scope)
            try:
                self.update(args[0])
            except Exception as e:
                self.warn(f"Unable to run update: {traceback.format_exc(e)}")
            yield
        
        @actions.add_function(".now", ())
        def _get_now():
            return time.time()
        
        @actions.add_function(".min_ceil", (float, float))
        def _min_ceil(a,b) -> int:
            return min(math.ceil(a), math.ceil(b))
        
        @actions.add_function(".random_point_around", (tuple, float, float))
        def _random_point_around(pos: Vector3, mindist: float, maxdist: float):
            return self.random_point_around(tuple(pos), mindist, maxdist)
                
        @actions.add_function(".distance", (tuple, tuple))
        def _distance(a: Vector3, b: Vector3):
            return sqrt(vec_norm_squared(vec_sub(a, b)))
                
        @actions.add_function(".safest_point", ())
        def _safest_point() -> Vector3:
            return self.safest_point()
        
        @actions.add_function(".should_flee", ())
        def _should_flee() -> bool:
            return self.should_flee()
        
        @actions.add_function(".closest_health_pack", ())
        def _closest_health_pack() -> Tuple[int, Vector3]:
            candidates = self.closest_health_packs()
            if candidates == []:
                return (-1, (0, 0, 0))
            return (candidates[0].id, candidates[0].position)
        
        @actions.add(".seen_enemy", 5)
        def _seen_enemy(agent: Agent, term, intention: Intention):
            # arg: ID, Type, Health, Angle, Position
            arg : tuple[int, TroopType, float, float, Vector3] = grounded(term.args, intention.scope)
            #self.info(f"TROOP DETECTED: {arg}")
            enemy_id : int = int(arg[0])
            enemy_pos = (arg[-1][0], arg[-1][1], arg[-1][2])
            enemy_type = TroopType(arg[1])
            health = float(arg[2])
            angle = float(arg[3])
            
            troop = Troop(enemy_id, time.time(), enemy_pos, enemy_type, health, angle)
            id = self.get_compatible_troop_or_new(troop)
            troop.id = id
            self.enemy_memory[id] = troop
            yield
            
        @actions.add(".seen_pack", 4)
        def _seen_pack(agent: Agent, term, intention: Intention):
            # arg: ID, Type, Value, Position
            arg : tuple[int, PackType, float, Vector3] = grounded(term.args, intention.scope)
            #self.info(f"PACK DETECTED: {arg}")
            pack_id = int(arg[0])
            pack_type = PackType(arg[1])
            pack_pos = (arg[-1][0], arg[-1][1], arg[-1][2])
            
            pack = Pack(pack_id, time.time(), pack_pos, pack_type)
            id = self.get_compatible_pack_or_new(pack)
            pack.id = id
            self.pack_memory[id] = pack 
            yield
            
        @actions.add(".pack_gone", 1)
        def _pack_gone(agent: Agent, term, intention: Intention):
            # arg: ID
            arg: tuple[int] = grounded(term.args, intention.scope)
            pack_id = int(arg[0])
            del self.pack_memory[pack_id]
            yield
            
        @actions.add_function(".closest_point", (tuple, tuple))
        def _closest_point(point : Vector3, candidates: List[Vector3]):
            candidates = [tuple(c) for c in candidates] # convert lists into tuples
            res = candidates[0]
            best_dist_sq = vec_norm_squared(vec_sub(res, point))
            for p in candidates[1:]:
                dist_sq = vec_norm_squared(vec_sub(p, point))
                if dist_sq < best_dist_sq:
                    res = p
                    best_dist_sq = dist_sq
            return res
        
        @actions.add_function(".reset_state", ())
        def _state_reset() -> str:
            hp = self.get_health()
            if hp < MAX_HEALTH:
                hp_packs = self.closest_health_packs()
                if hp_packs != []:
                    self.bdi.set_belief(FETCHING, hp_packs[0].id, hp_packs[0].position, hp_packs[0].type)
                    self.info("RESET STATE TO FETCH HEALTH PACK")
                    return FETCH
            
            enemies = self.closest_recent_troops()
            if hp < LOW_HEALTH and self.should_flee():
                self.info("RESET STATE TO FLIGHT")
                return FLEE
            
            ammo = self.get_ammo()        
            if ammo > MIN_AMMO and enemies != [] and hp > LOW_HEALTH:
                most_relevant_enemy = enemies[0]
                dt = time.time() - most_relevant_enemy.last_seen 
                # Only attack enemies we think are still alive
                if most_relevant_enemy.health > PERSISTENCE * dt:
                    self.bdi.set_belief(ATTACK_TARGET, most_relevant_enemy.position)
                    self.bdi.set_belief(ATTACK_ID, most_relevant_enemy.id)
                    self.info("RESET STATE TO ATTACK")
                    return ATTACK
                
            if ammo < LOW_AMMO:
                ammo_packs = self.closest_ammo_packs()
                if ammo_packs != []:
                    self.bdi.set_belief(FETCHING, ammo_packs[0].id, ammo_packs[0].position, ammo_packs[0].type)
                    self.info("RESET STATE TO FETCH AMMO PACK")
                    return FETCH
                
            self.info("RESET STATE TO CENTRALIZE")
            return CENTRALIZE
