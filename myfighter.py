import json
import math
import random
from loguru import logger
from spade.behaviour import OneShotBehaviour
from spade.template import Template
from spade.message import Message
from pygomas.bditroop import BDITroop
from pygomas.bdisoldier import BDISoldier
from pygomas.ontology import HEALTH
from agentspeak import Actions, grounded
from agentspeak.runtime import Agent, Intention
from math import sqrt, PI, sin, cos
from typing import Dict, List, Tuple
from agentspeak.stdlib import actions as asp_action
import time

from pygomas.agent import LONG_RECEIVE_WAIT
Vector3 = Tuple[float, float, float]
TroopType = int

# General utility function generation
def _random_point_around(point: List[float], min_distance: float, max_distance: float, rng: random.Random) -> List[float]:
    angle = rng.random() * 2 * PI
    dist = min_distance + rng.random() * (max_distance - min_distance)
    return [
        point[0] + cos(angle) * dist,
        point[1],
        point[2] + sin(angle) * dist
    ]
    
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
    return vec_mult(v, norm / length)

MEMORY_TERM = 15
FLIGHT_DISTANCE = 10
MAX_FLIGHT_ATTEMPTS = 10
FLIGHT_SPREAD_DISTANCE_MIN = 5
FLIGHT_SPREAD_DISTANCE_MAX = 5
MAX_FLIGHT_SPREAD_ATTEMPTS = 3
class Troop:
    def __init__(self, type: TroopType, health: float, last_seen: float, position: Vector3):
        self.type = type
        self.health = health
        self.last_seen = last_seen
        self.position = position

class BDISurvivalist(BDISoldier):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.rng = random.Random()
        self.enemy_memory : Dict[int, Troop] = dict()
        
    def add_custom_actions(self, actions : Actions):
        super().add_custom_actions(actions)
        
        def random_point_around(self, point: Vector3, min_distance = 0.0, max_distance = float.MAX):
            return _random_point_around(point, min_distance, max_distance, self.rng)
        
        def get_walkable_point_along_ray(pos: Vector3, direction: Vector3) -> Vector3:
            target = pos
            attempts = 0
            point_stack = []
            # Attempt to find walkable points at equal intervals along the ray
            while attempts < MAX_FLIGHT_ATTEMPTS:
                target = [target[i] + d * FLIGHT_DISTANCE for i,d in enumerate(direction)]
                if self.check_static_position(target):
                    return target
                point_stack.insert(0, target)
                attempts += 1
            
            # Attempt to find walkable points AROUND previously attempted points, trying the furthest points first
            for prev_target in point_stack:
                spread_attempts = 0
                while spread_attempts < MAX_FLIGHT_SPREAD_ATTEMPTS:
                    target = self.random_point_around(prev_target, FLIGHT_SPREAD_DISTANCE_MIN, FLIGHT_SPREAD_DISTANCE_MAX)
                    if self.check_static_position(target):
                        return target
                    spread_attempts += 1
                    
            # If a generation along the ray fails, fallback to a random point within 50 units
            return self.generate_escape_position()
        
        @actions.add_function(".now", ())
        def _get_now():
            return time.time()
        
        @actions.add_function(".safest_point")
        def _safest_point() -> Vector3:
            now : float = _get_now()
            here : Vector3 = self.movement.position
            sum_weights = 0.0
            danger_peak = [0.0] * 3
            for enemy in self.enemy_memory.values():
                # Prioritize moving away from enemies seen RECENTLY at HIGH HP
                w = max(0.0, MEMORY_TERM - (now - enemy.last_seen)) * enemy.health # WEIGHT
                sum_weights += w
                danger_peak = vec_addmult(danger_peak, enemy.position, w)
            flight_direction = vec_addmult(here, danger_peak, -1 / sum_weights)
            # Flight direction is a vector pointing to the safest position
            # Target contains the tentative target location
            final_target = get_walkable_point_along_ray(here, vec_normalize(flight_direction))
            return final_target            
            
        @actions.add(".seen_enemy", 5)
        def _seen_enemy(agent: Agent, term, intention: Intention):
            # arg: ID, Type, Angle, Distance, Health, Position
            arg : tuple[int, TroopType, float, float, float, Vector3] = grounded(term.args, intention.scope)
            enemy_id : int = arg[0]
            enemy_pos = (arg[-1][0], arg[-1][1], arg[-1][2])
            self.enemy_memory[enemy_id] = Troop(arg[1], arg[-2], _get_now(), enemy_pos)
            
        @actions.add_function(".closest_point", (Vector3, List[Vector3]))
        def _closest_point(point : Vector3, candidates: List[Vector3]):
            res = candidates[0]
            best_dist_sq = vec_norm_squared(vec_sub(res, point))
            for p in candidates[1:]:
                dist_sq = vec_norm_squared(vec_sub(p, point))
                if dist_sq < best_dist_sq:
                    res = p
                    best_dist_sq = dist_sq
            return res
            

      
#        super().__init__(actions=example_agent_actions, *args, **kwargs)
