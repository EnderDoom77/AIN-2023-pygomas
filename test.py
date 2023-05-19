from ctflib import raycast

targets = [(11,0,10),(2,0,4),(1,0,3), (4,0,5)]
pos = (0,0,0)
dir = (1,0,1)

res = raycast(pos, dir, targets, 1)
print(res)