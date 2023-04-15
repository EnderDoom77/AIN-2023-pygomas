import json
from loguru import logger
from spade.behaviour import OneShotBehaviour
from spade.template import Template
from spade.message import Message
from pygomas.bditroop import BDITroop
from pygomas.bdisoldier import BDISoldier
from pygomas.ontology import HEALTH
from agentspeak import Actions
from agentspeak import grounded
from math import sqrt
from typing import List
from agentspeak.stdlib import actions as asp_action
import time

from pygomas.agent import LONG_RECEIVE_WAIT

MEMORY_TERM = 15
FLIGHT_DISTANCE = 10
MAX_FLIGHT_ATTEMPTS = 10
FLIGHT_SPREAD_DISTANCE = 5
MAX_FLIGHT_SPREAD_ATTEMPTS = 3
class BDISurvivalist(BDISoldier):

     def add_custom_actions(self, actions):
        super().add_custom_actions(actions)
        
        def get_walkable_point_along_ray(pos: List[float], direction: List[float]) -> List[float]:
            target = [pos[i] + d * FLIGHT_DISTANCE for i,d in enumerate(direction)]
            attempts = 0
            point_stack = []
            while attempts < MAX_FLIGHT_ATTEMPTS:
                if self.check_static_position(target):
                    return target
                point_stack.insert(0, target)
                attempts += 1
                target = [target[i] + d * FLIGHT_DISTANCE for i,d in enumerate(direction)]


        
        @actions.add_function(".now", ())
        def _get_now():
            return time.time()
        
        @actions.add_function(".safest_point", (List[(int, float, List[int], int)]))
        def _safest_point(enemy_list : List[(int, float, List[int], int)]) -> List[int]:
            now : float = _get_now()
            here : List[float] = self.get_belief("position")
            sum_weights = 0.0
            danger_peak = [0.0] * 3
            for (id, time, pos, hp) in enemy_list:
                # Prioritize moving away from enemies seen RECENTLY at HIGH HP
                w = max(0.0, MEMORY_TERM - (now - time)) * hp
                sum_weights += w
                for i in range(3):
                    danger_peak[i] += pos[i] * w
            neg_danger_peak_delta = [0.0] * 3
            distance_sq = 0.0
            for i in range(3):
                val = here[i] - danger_peak[i] / sum_weights
                neg_danger_peak_delta[i] = val
                distance_sq += val * val
            # Negative danger peak delta is a vector pointing to the safest position
            # Target contains the tentative target location
            dist = sqrt(distance_sq)
            attempts = 0
            final_target = get_walkable_point_along_ray(here, [n / dist for n in neg_danger_peak_delta])
            
            
        @actions.add(".seen_enemy")
        def _seen_enemy(agent, term, intention):
            
        @actions.add_function(".closest_point", (List[int], List[List[int]]))
            

      
#        super().__init__(actions=example_agent_actions, *args, **kwargs)
