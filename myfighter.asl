// Initial Beliefs
center([128, 0, 120]).
damage_factor(2).
turn_angle(1.25).
idle_time(0).

low_health(75).
low_ammo(50).
critical_health(15).
default_shot_burst(5).
hp_pack_max_distance(25).

+flag(F): team(200)
  <-
  !!update;
  +centralize;
  ?threshold_shots(TSh);
  -+shot_burst(TSh).

+centralize
  <-
  -+idle_time(0);
  ?center(C);
  .random_point_around(C, 0, 10, RandomPos);
  .goto(RandomPos);
  .print("Moving towards the center: ", C);
  -+state(centralizing);
  if (not rotating) {
    +rotating;
  }
  -centralize.

+flee
  <-
  -+state(fleeing);
  -+idle_time(0);
  .should_flee(B);
  .closest_health_pack([ID, HPPos]);
  ?position(Here);
  .distance(Here, HPPos, Dist);
  ?hp_pack_max_distance(MaxDist);
  if (ID >= 0 & Dist < MaxDist) {
    -+fetching(ID, HPPos, 1001);
    +fetch;
  } else {
    if (B) {
      .safest_point(P);
      .print("Fleeing towards ", P);
      .goto(P);
      ?default_shot_burst(DSh);
      -+shot_burst(DSh);
      if (not rotating) {
        +rotating;
      }
    } else {
      +reset;
    }
  }
  -flee.

+attack
  <-
  ?attack_target(P);
  -+idle_time(0);
  -rotating;
  ?threshold_shots(TSh);
  -+shot_burst(TSh);
  .goto(P);
  .print("Attacking position ", P);
  -+state(attacking);
  -attack.

+fetch: not state(fetching)
  <-
  -+idle_time(0);
  ?fetching(_,P,_);
  if (not rotating) {
    +rotating;
  }
  .goto(P);
  .print("Fetching pack at position ", P);
  -+state(fetching);
  -fetch.

+reset
  <-
  .reset_state([]);
  -reset.

+!update
  <-
  ?idle_time(IT);
  -+idle_time(IT + 1);
  .update([]);
  .wait(500);
  if (rotating) {
    ?position(P);
    .random_point_around(P, 10, 10, RandomPos);
    .look_at(RandomPos);
  }
  if (idle_time(IT) & IT > 10) {
    +reset;
  }
  !update.

+target_reached(T): state(centralizing)
  <-
  if (not rotating) {
    +rotating;
  }
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

+threat(ID, Health, Position): state(fleeing) & ammo(Ammo) & Ammo > 0
  <-
  ?shot_burst(Burst);
  .min_ceil(Burst, Health * 0.55, CBurst);
  .shoot(CBurst, Position);
  if (crit_health(CHP) & Health < CHP & Ammo > Health * 0.55) {
    -+attack_target(Position);
    -+attack_id(ID);
    +attack;
  }.

// If we're not fleeing and we see a potential target, shoot it
+threat(ID, Health, Position): not state(fleeing) & ((ammo(Ammo) & Ammo > Health * 0.55) | (state(attacking) & attack_id(AID) & AID = ID))
  <-
  ?shot_burst(Burst);
  .min_ceil(Burst, Health * 0.55, CBurst);
  .shoot(CBurst, Position);
  if (state(centralizing)) {
    -+attack_target(Position);
    -+attack_id(ID);
    +attack;
  }
  if (Ammo == 0 & state(attacking)) {
    +reset;
  }.

+packs_in_fov(ID, Type, Angle, Distance, Value, Position)
  <-
  //.print("Detecting a pack of type ", Type, " at position ", Position, " with value ", Value);
  .seen_pack(ID, Type, Value, Position);
  -packs_in_fov(ID, Type, Angle, Distance, Value, Position);
  +pack(ID, Type, Value, Position).

+pack(ID, Type, Value, Position): Type = 1001 & (state(fleeing) | state(centralizing)) & health(HP) & HP < 100
  <-
  -+fetching(ID, Position, Type);
  +fetch.

+pack(ID, Type, Value, Position): Type = 1002 & state(centralizing) & low_ammo(LAmmo) & ammo(Ammo) & Ammo < LAmmo
  <-
  -+fetching(ID, Position, Type);
  +fetch.

// If we see a pack we are not currently going for
+pack(ID, Type, Value, Position): state(fetching) & fetching(FID, FPosition, FType) & not ID = FID
  <-
  ?position(Here);
  ?health(HP);
  ?ammo(Ammo);
  .closest_point(Here, [FPosition, Position], Closest);
  if (
    (Type = 1001 & ((not FType = 1001) | Closest = Position) & HP < 100) |
    (Type = 1002 & FType == 1002 & Closest = Position & Ammo < 100)
  ) {
    -+fetching(ID, Position, Type);
    .print("Changing Fetch Target To: ", Position);
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
