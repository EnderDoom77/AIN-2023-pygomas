from ctflib import raycast, vec_sub


fire_position = (197, 0, 140)
#ally_positions = [(175, 0, 132)]
ally_positions = [(193, 0, 132)]
enemy_positions = [(163, 0, 144), (153, 0, 144), (149, 0, 136)]

for r in [1, 3, 5, 7.5, 7.75, 7.9, 8, 10, 15]:
    print(f"RADIUS = {r}")
    for target in enemy_positions:
        i = raycast(fire_position, vec_sub(target,fire_position), ally_positions + enemy_positions, r)
        if i < 0:
            print(f"\tERROR - Firing from {fire_position} to {target} does not register hit")
        elif i < len(ally_positions):
            print(f"\tFRIENDLY FIRE - Firing from {fire_position} to {target} hits ally at position {ally_positions[i]}")
        else:
            print(f"\tHIT - Firing from {fire_position} to {target} hits enemy at position {enemy_positions[i - len(ally_positions)]}")