# myvisualizer.py
from math import cos, sin, sqrt
import time
from typing import List, Tuple, Union
import pygame
from pygame import Color
import json

# from ctflib import Item

PERSISTENCE = 7
HEALTH_PACK = 1001
AMMO_PACK = 1002
MAX_HEALTH = 100
MAX_AMMO = 100

# VISUALIZER CONSTANTS
VW_SCALE = 3
VISUALIZER = True
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
YELLOW = (255,255,0)
WHITE = (255,255,255)
ORANGE = (255,150,0)
PURPLE = (150,0,255)
HEALTH_COLOR = (0,175,35)

HEADING_LINE_LENGTH = 10

def ints(*vals: List[float]):
    return tuple(int(v) for v in vals)

COMM_FILE = "bdi_mem.json"
def import_data():
    with open(COMM_FILE, "r") as f:
        return json.load(f)

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((256*VW_SCALE, 256*VW_SCALE))
font = pygame.font.SysFont(None, 16)

BAR_BG = (50,50,50)
def resource_bar(pos: Tuple[float, float], color: Union[Tuple, pygame.Color], val: float, maxval: float):
    (x,z) = pos
    left = x * VW_SCALE - 8
    top = z * VW_SCALE + 10
    height = 5
    width = 16
    fillwidth = (val / maxval) * width
    pygame.draw.rect(screen, BAR_BG, (left, top, width, height))
    pygame.draw.rect(screen, color, (left, top, fillwidth, height))

def pointing_bar(pos: Tuple[float, float], color: Union[Tuple, pygame.Color], pointing: Tuple[float, float]):
    (x, z) = pos
    (hx, hz) = pointing 
    if (hx,hz) != (0,0):
        norm = sqrt(hx * hx + hz * hz)
        hx = x + hx * HEADING_LINE_LENGTH / norm
        hz = z + hz * HEADING_LINE_LENGTH / norm
        pygame.draw.line(screen, color, (x*VW_SCALE,z*VW_SCALE), (hx*VW_SCALE,hz*VW_SCALE))
        
def render_text(pos: Tuple[float, float], val: str, color: Union[Tuple, pygame.Color] = WHITE):
    x, y = pos
    img = font.render(val, True, color)
    screen.blit(img, (x*VW_SCALE - img.get_width()/2 ,y*VW_SCALE - img.get_height()/2))

def draw_troop(troop: dict, color: Union[Tuple, pygame.Color]):
    (tx,ty,tz) = ints(*troop['position'])
    t = (PERSISTENCE - now + troop['last_seen']) / PERSISTENCE
    if t < 0: t = 0
    pygame.draw.circle(screen, color, (tx*VW_SCALE,tz*VW_SCALE), 10)
    resource_bar((tx, tz), HEALTH_COLOR, troop['health'], MAX_HEALTH)
    angle = troop.get('angle', 0)
    (thx,thz) = (cos(angle), sin(angle))
    pointing_bar((tx,tz), PURPLE, (thx,thz))
    render_text((tx,tz), str(troop['id']))
    
running = True
while running:
    try:
        data = import_data()
    except:
        time.sleep(1)
        continue
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
    if not running: break       
    
    (x,y,z) = ints(*data.get('pos', [0,0,0]))
    now = data.get('time', time.time())
    screen.fill(BLACK)
    pygame.draw.circle(screen, BLUE, (x*VW_SCALE,z*VW_SCALE), 10)
    resource_bar((x,z),HEALTH_COLOR,data.get('health',0),MAX_HEALTH)
    
    (safex,safey,safez) = ints(*data.get('safest_point', [x,y,z]))
    pygame.draw.circle(screen, ORANGE, (safex*VW_SCALE,safez*VW_SCALE), 5)
    
    for troop in data.get('enemy_memory', []):
        draw_troop(troop, Color(255,0,0))
    
    for troop in data.get('ally_memory', []):
        draw_troop(troop, Color(0,255,0))
        
    for pack in data.get('pack_memory', []):
        (px,py,pz) = ints(*pack['position'])
        t = (PERSISTENCE - now + pack['last_seen']) / PERSISTENCE
        if t < 0: t = 0
        color = Color(0,150,0,a=int(230*t+25)) if pack['type'] == HEALTH_PACK else Color(100,100,0,a=int(230*t+25))
        pygame.draw.rect(screen, color, (px*VW_SCALE-8,pz*VW_SCALE-8, 16, 16))
        render_text((px,pz), str(pack['id']))
        
    (dx,dy,dz) = tuple(data.get('dest', [0,0,0]))
    pygame.draw.line(screen, WHITE, (x*VW_SCALE,z*VW_SCALE), (dx*VW_SCALE,dz*VW_SCALE))
    (hx,hy,hz) = tuple(data.get('heading', [0,0,0]))
    pointing_bar((x,z), PURPLE, (hx,hz))

    misc_info = {}
    if 'health' in data: misc_info['health'] = f"{data['health']:d} / {MAX_HEALTH}"
    if 'ammo' in data: misc_info['ammo'] = f"{data['ammo']:d} / {MAX_AMMO}"
    if 'idle_since' in data: misc_info['idle time'] = f"{now - data['idle_since']:.1f}s"
    misc_info['state'] = f"{data.get('state', 'UNKNOWN')}"
    
    y = 5
    DELTA_Y = 16
    for name, val in misc_info.items():
        img = font.render(f"{name}: {val}", True, WHITE)
        screen.blit(img, (5, y))
        y += DELTA_Y

    pygame.display.flip()
    clock.tick(5)