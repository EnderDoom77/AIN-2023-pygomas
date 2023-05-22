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

from ctflib import common_init, define_common_actions

class CTFMedic(BDIMedic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_init(self, *args, **kwargs)
        
    def add_custom_actions(self, actions : Actions):
        super().add_custom_actions(actions)
        define_common_actions(self, actions)