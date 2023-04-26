// Initial Beliefs
center([128, 0, 128]).
damage_factor(2).
turn_angle(1.25).

/*
ITEM STRUCTURE: ID, Time, Position, Value
Value is Health recovery for HP, Ammo recovery for AP, and remaining Health for Enemies
*/

+flag(F): team(200)
  <-
  +rotating;
  +centralize.

+centralize
  <-
  ?center(C);
  .goto(C);
  .print("Moving towards the center: ", C);
  -+state(centralizing);
  -+rotating;
  -centralize.

+flee
  <-
  .safest_point(P);
  .goto(P);
  .print("Fleeing towards ", P);
  -+state(fleeing);
  -+rotating;
  -flee.

+attack
  <-
  ?attack_target(P);
  -rotating;
  .goto(P);
  .print("Attacking position ", P);
  -+state(attacking);
  -attack.

+fetch
  <-
  ?fetch_target(P);
  -+rotating;
  .goto(P);
  .print("Fetching pack at position ", P);
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

+target_reached(T): state(fetching) & fetch_target(FT)
  <-
  -fetch_target(FT);
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

+packs_in_fov(ID, Type, Angle, Distance, Value, Position)
  <-
  .seen_pack(ID, Type, Value, Position);
  -packs_in_fov(ID, Type, Angle, Distance, Value, Position);
  .print("Detecting a pack of type ", Type, " at position ", Position, " with value ", Value);
  +pack(ID, Type, Value, Position).

+threshold_health(HP) : not state(fetching)
  <-
  +flee.

+threshold_health(HP) : state(fetching) & fetching(ID, 103, Pos)
  <-
  -fetching(ID, 103, Pos);
  +reset.