// Initial Beliefs
center([128, 0, 128]).
damage_factor(2).
turn_angle(1.25).

low_health(50).
critical_health(15).
shot_burst(5).

/*
ITEM STRUCTURE: ID, Time, Position, Value
Value is Health recovery for HP, Ammo recovery for AP, and remaining Health for Enemies
*/

+flag(F): team(200)
  <-
  +centralize.

+centralize
  <-
  ?center(C);
  .goto(C);
  //.print("Moving towards the center: ", C);
  -+state(centralizing);
  -+rotating;
  -centralize.

+flee
  <-
  .should_flee(B);
  if (B) {
    .safest_point(P);
    .goto(P);
    //.print("Fleeing towards ", P);
    -+state(fleeing);
    -+rotating;
  } else {
    +reset;
  }
  -flee.

+attack
  <-
  ?attack_target(P);
  -rotating;
  .goto(P);
  //.print("Attacking position ", P);
  -+state(attacking);
  -attack.

+fetch
  <-
  ?fetching(_,P,_);
  -+rotating;
  .goto(P);
  //.print("Fetching pack at position ", P);
  -+state(fetching);
  -fetch.

+reset
  <-
  .reset_state;
  -reset.

+rotating
  <-
  ?turn_angle(A);
  .turn(A);
  .wait(1000);
  if (rotating) {
    -+rotating;
  }.

+target_reached(T): state(centralizing)
  <-
  -+rotating;
  -target_reached(T).

+target_reached(T): state(fetching) & fetching(FID,FPos,FType)
  <-
  -fetching(FID,FPos,FType);
  .pack_gone(FID);
  +reset_state;
  -target_reached(T).

+target_reached(T): state(attacking) & attack_target(AT)
  <-
  -attack_target(AT);
  +reset_state;
  -target_reached(T).

+target_reached(T): state(fleeing)
  <-
  +flee;
  -target_reached(T).

/*  
  +enemies_in_fov(ID, Type, Angle, Distance, Health, Position)
    <-
    .shoot(3,Position).
*/
  
+friends_in_fov(ID, Type, Angle, Distance, Health, Position)
  <-
  .seen_enemy(ID, Type, Health, Position);
  -friends_in_fov(ID, Type, Angle, Distance, Health, Position);
  +threat(ID, Health, Position).

+threat(ID, Health, Position): state(fleeing) & crit_health(CHP) & Health < CHP & ammo(Ammo) & Ammo * 0.55 > Health
  <-
  -+attack_target(Position);
  -+attack_id(ID);
  ?shot_burst(Burst);
  .shoot(Position, Burst);
  +attack.

+threat(ID, Health, Position): state(attacking) & attack_id(AID) & AID = ID
  <-
  .shoot(Position, Burst).

+packs_in_fov(ID, Type, Angle, Distance, Value, Position)
  <-
  //.print("Detecting a pack of type ", Type, " at position ", Position, " with value ", Value);
  .seen_pack(ID, Type, Value, Position);
  -packs_in_fov(ID, Type, Angle, Distance, Value, Position);
  +pack(ID, Type, Value, Position).

+pack(ID, Type, Value, Position): Type = 1001 & (state(fleeing) | state(centralizing) & health(HP) & HP < 100)
  <-
  +fetching(ID, Position, Type);
  .goto(Position).

// If we see a pack we are not currently going for
+pack(ID, Type, Value, Position): state(fetching) & fetching(FID, FPosition, FType) & not ID = FID
  <-
  ?position(Here);
  ?health(HP);
  ?ammo(Ammo);
  .closest_point(Here, [FPosition, Position], Closest);
  if (
    (Type = 1001 & (not FType = 1001 | Closest = Position) & HP < 100) |
    (Type = 1002 & FType == 1002 & Closest = Position & Ammo < 100)
  ) {
    +fetching(ID, Position, Type);
    .goto(Position);
  }.

+health(HP) : low_health(LHP) & HP < LHP & not low_health
  <-
  +low_health.

+health(HP) : low_health(LHP) & HP > LHP & low_health
  <-
  -low_health.

// If the agent reaches low health and it's not fetching a health pack
+low_health : not state(fetching) | (state(fetching) & fetching(FID, FPos, FType) & not FType = 1001)
  <-
  +flee.
