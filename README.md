# AIN-2023-pygomas

## Agent Strategy
The agent implemented in this project has a set of behaviours dictated by states.
The agent starts in the centralizing state.
Due to the implementation of Free For All, friends are technically enemies. This description will refer to agents that may attack the local agent as "enemies".

### State - Centralizing
The goal of the agent is to get to the center of the map.
This state has the following transition conditions:
* If the agent's health drops below a threshold, it transitions to the fleeing state.
* If the agent sees an enemy on low health and has sufficient ammunition, it targets this enemy and transitions to the attacking state.
* If the agent sees a health pack and its health is missing at least as much health as a health pack recovers, it targets this health pack and transitions to the fetching state.
* If the agent sees an ammo pack and its ammo is missing at least as much ammo as an ammo pack restores, it targets this ammo pack and transitions to the fetching state.

### State - Fleeing
The goal of the agent is to remain as far away as possible from all enemies.
This state has the following transition conditions:
* If the agent sees an enemy on very low health and has sufficient ammunition, it targets this enemy and transitions to the attacking state.
* If the target sees a health pack, it targets this health pack and transitions to the fetching state.

### State - Attacking
The goal of the agent is to damage and kill its target.
This state has the following transition conditions:
* If the agent's ammunition drops to 0, it transitions to the reset state.
* If the agent's health drops below a threshold and the target's health is not very low, it transitions to the fleeing state.
* If the target is successfully killed or we lose track of it, it transitions to the reset state.

### State - Fetching
The goal of the agent is to collect a specific pack signaled by its target.
This state has the following transition conditions:
* If the target pack is collected by any agent (including itself), it transitions to the reset state.
* If the agent sees a health pack, it resets its target if any of the following conditions are true
    * The agent's health is not full and the new pack is closer
    * The agent's health is not full and the current target is an ammo pack
* If the agent sees an ammo pack, it resets its target if the following condition is true
    * The new pack is closer than its current target
* If the agent sees an enemy whose health is lower than its own and the agent's ammo is not 0, it transitions to the attacking state.

### State - Reset
The agent has no goal, it immediately transitions to another state given its situation.
* If the agent's health is not full and it knows of a health pack, it targets this memory and transitions to the fetching state.
* If the agent's health is low and it knows of enemies nearby, it transitions to the fleeing state.
* If the agent's ammo is not 0 and it knows of an enemy on very low health, it targets this memory and transitions to the attacking state.
* If the agent's ammo is low and it knows of an ammo pack, it targets this memory and transitions to the fetching state.
* The agent transitions to the centralizing state.

The idea of this strategy is to carefully balance risk-taking; the agent is opportunistic, because it takes advantage of situations where it can reduce risk to itself by eliminating enemies on low health and attempting to fetch resources.
Whenever such opportunities do not exist, the agent is careful and attempts to reach the center of the map to collect resources.
If the agent is at high risk, the agent prioritizes its own safety by attempting to fetch health packs, eliminating enemies at very low health that may attack it, and moving away from enemies.