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
from pygomas.bdimedic import BDIMedic
from pygomas.bdifieldop import BDIFieldOp
from pygomas.ontology import HEALTH
from pygomas.pack import PACK_MEDICPACK, PACK_AMMOPACK
from agentspeak import Actions, grounded
from agentspeak.runtime import Agent, Intention
from math import sqrt, pi, sin, cos
from typing import Callable, Dict, List, Sized, Tuple
from agentspeak.stdlib import actions as asp_action
from termcolor import colored
from arena.survivalist import Troop

from ctflib import Pack, TroopType, Vector3, define_common_actions, get_compatible_item_or_new, get_positions_around, visualizer, common_init

class CTFCommander(BDIMedic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_init(self, *args, **kwargs)
        self.ally_memory = {}
        self.enemy_memory = {}
    
    @property
    def pack_memory(self):
        return {**self.health_pack_memory, **self.ammo_pack_memory}
        
    def update(self, *args):
        visualizer(self, *args)
    
    def info(self, text: str):
        print(f"{colored(f'{self.name}:', 'white', 'on_light_blue')} {text}")            
    def warn(self, text: str):
        print(f"{colored(f'{self.name}:', 'black', 'on_yellow')} {text}")    

    def add_custom_actions(self, actions : Actions):
        super().add_custom_actions(actions)
        
        define_common_actions(self, actions)
        
        @actions.add(".update", 1)
        def _update(agent, term, intention):
            args = grounded(term.args, intention.scope)
            try:
                self.update(args[0])
            except Exception as e:
                self.warn(f"Unable to run update: {traceback.format_exc(e)}")
            yield
        
        @actions.add(".register_position", 4)
        def _register_position(agent, term, intention):
            print("START Register position")
            args = grounded(term.args, intention.scope)
            # args -> (Agent, Position, Health, Type)
            ag, pos, hp, troop_type = tuple(args)
            ag = str(ag)
            mem : Dict[str, Troop] = self.ally_memory
            if ag in mem:
                mem[ag].last_seen = time.time()
                mem[ag].position = pos
                mem[ag].health = hp
            else:
                mem[ag] = Troop(len(mem),time.time(),pos,troop_type,hp,-1)
            print("END Register position")
            
        @actions.add(".register_enemy", 3)
        def _handle_enemy(agent, term, intention):
            args = grounded(term.args, intention.scope)
            # args -> (Position, Health, Type)
            pos, hp, troop_type = tuple(args)
            new_id = get_compatible_item_or_new(pos, self.enemy_memory, 15, lambda x: x.type == troop_type)
            t = Troop(new_id, time.now(), pos, troop_type, hp, -1)
            self.enemy_memory[id] = t
        
        @actions.add_function(".get_team", ())
        def _get_team():
            return self.ally_memory.keys()
        
        @actions.add_function(".get_circular_formation", (Tuple, float, Tuple))
        def _get_circular_formation(center: Vector3, radius: float, agents: Sized):
            return tuple(get_positions_around(center, radius, len(agents)))
            