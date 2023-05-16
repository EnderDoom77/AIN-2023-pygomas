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
from agentspeak import Actions, grounded
from agentspeak.runtime import Agent, Intention
from math import sqrt, pi, sin, cos
from typing import Callable, Dict, List, Tuple
from agentspeak.stdlib import actions as asp_action
from termcolor import colored

from ctflib import define_common_actions, visualizer

class CTFCommander(BDIMedic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_memory = {}
        self.health_pack_memory = {}
        self.ammo_pack_memory = {}
        
    def update(self, *args):
        visualizer(*args)
        
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
        
        @actions.add(".register_position", 2)
        def _register_position(agent, term, intention):
            args = grounded(term.args, intention.scope)
            # args -> (Agent, Position)
            ag, pos = tuple(args)
            print(type(ag))
            print(ag)
            print(json.dumps(ag))
            