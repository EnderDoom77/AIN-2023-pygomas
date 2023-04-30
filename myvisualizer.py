import time
from typing import List, Tuple, Union
import pygame
from pygame import Color
import json

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
HEALTH_COLOR = (0,175,35)

def ints(*vals: List[float]):
    return tuple(int(v) for v in vals)

COMM_FILE = "status.json"
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
    for troop in data.get('enemy_memory', []):
        (tx,ty,tz) = ints(*troop['position'])
        t = (PERSISTENCE - now + troop['last_seen']) / PERSISTENCE
        if t < 0: t = 0
        pygame.draw.circle(screen, Color(255,0,0,a=int(230*t+25)), (tx*VW_SCALE,tz*VW_SCALE), 10)
        resource_bar((tx, tz), HEALTH_COLOR, troop['health'], MAX_HEALTH)
        img = font.render(str(troop['id']), True, WHITE)
        screen.blit(img, (tx*VW_SCALE-4,tz*VW_SCALE-4))
        
    for pack in data.get('pack_memory', []):
        (px,py,pz) = ints(*pack['position'])
        t = (PERSISTENCE - now + pack['last_seen']) / PERSISTENCE
        if t < 0: t = 0
        color = Color(0,255,0,a=int(230*t+25)) if pack['type'] == HEALTH_PACK else Color(255,255,0,a=int(230*t+25))
        pygame.draw.rect(screen, color, (px*VW_SCALE-8,pz*VW_SCALE-8, 16, 16))
        img = font.render(str(pack['id']), True, WHITE)
        screen.blit(img, (px*VW_SCALE-4,pz*VW_SCALE-4))
        
    (dx,dy,dz) = ints(*data.get('dest', [0,0,0]))
    pygame.draw.line(screen, WHITE, (x*VW_SCALE,z*VW_SCALE), (dx*VW_SCALE,dz*VW_SCALE))

    misc_info = {}
    if 'health' in data: misc_info['health'] = f"{data['health']:d} / {MAX_HEALTH}"
    if 'ammo' in data: misc_info['ammo'] = f"{data['ammo']:d} / {MAX_AMMO}"
    misc_info['state'] = f"{data.get('state', 'UNKNOWN')}"
    
    y = 5
    DELTA_Y = 16
    for name, val in misc_info.items():
        img = font.render(f"{name}: {val}", True, WHITE)
        screen.blit(img, (5, y))
        y += DELTA_Y

    pygame.display.flip()
    clock.tick(5)