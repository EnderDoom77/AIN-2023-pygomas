// survivalist.asl

// Initial Beliefs
center([128, 0, 120]).
damage_factor(2).
turn_angle(1.6).
idle_since(0).
state("initial").

low_health(75).
low_ammo(50).
critical_health(15).
default_shot_burst(5).
hp_pack_max_distance(25).
last_shot(0).

+flag(F): team(200)
  <-
  !!update;
  ?threshold_shots(TSh);
  -shot_burst(_);
  +shot_burst(TSh);
  !recon;
  +centralize.

+!recon
  <-
  ?turn_angle(TAngle);
  -rotating;
  .wait(0.25);
  .turn(TAngle);
  .wait(0.25);
  .turn(TAngle);
  .wait(0.25);
  .turn(TAngle);
  .wait(0.25);
  .turn(TAngle);
  +rotating.

+centralize
  <-
  .now(Time);
  if (not state("centralizing") | (idle_since(IdleTime) & Time - IdleTime > 2.5)) {
    -idle_since(_);
    +idle_since(Time);
    ?center(C);
    .random_point_around(C, 0, 10, RandomPos);
    .goto(RandomPos);
    .print("Moving towards the center: ", RandomPos);
    -state(_);
    +state("centralizing");
    if (not rotating) {
      +rotating;
    }
  }
  -centralize.

+flee
  <-
  .now(Time);
  if (not state("fleeing") | (idle_since(IdleTime) & Time - IdleTime > 1.5)) {
    -state(_);
    +state("fleeing");
    .print("Considering flight...");
    -idle_since(_);
    +idle_since(Time);
    .should_flee(B);
    .closest_health_pack([ID, HPPos]);
    ?position(Here);
    .distance(Here, HPPos, Dist);
    ?hp_pack_max_distance(MaxDist);
    if (ID >= 0 & Dist < MaxDist) {
      -fetching(_,_,_);
      +fetching(ID, HPPos, 1001);
      +fetch;
    } else {
      if (B) {
        .safest_point(P);
        .print("Fleeing towards ", P);
        .goto(P);
        ?default_shot_burst(DSh);
        -shot_burst(_);
        +shot_burst(DSh);
        if (not rotating) {
          +rotating;
        }
      } else {
        !recon;
        +reset;
      }
    }
  }
  -flee.

+attack: not state("attacking")
  <-
  ?attack_target([AttX, AttY, AttZ]);
  ?position([X,Y,Z]);
  .print("Attacking target: ", [AttX, AttY, AttZ]);
  .now(Time);
  -idle_since(_);
  +idle_since(Time);
  -rotating;
  ?threshold_shots(TSh);
  -shot_burst(_);
  +shot_burst(TSh);
  .goto([(AttX + X)/2,(AttY + Y)/2,(AttZ + Z)/2]);
  -state(_);
  +state("attacking");
  -attack.

+fetch
  <-
  .now(Time);
  if (not state("fetching") | (idle_since(IdleTime) & Time - IdleTime > 2.0)) {
    -idle_since(_);
    +idle_since(Time);
    ?fetching(_,P,_);
    .print("Fetching pack at position ", P);
    if (not rotating) {
      +rotating;
    }
    .goto(P);
    -state(_);
    +state("fetching");
  }
  -fetch.

+reset
  <-
  ?state(PrevState);
  .print("Requesting state reset...");
  .reset_state(State);
  .print("Resettings from state", PrevState, "with", State);
  if (State = "centralize") {
    +centralize;
  }
  if (State = "fetch") {
    +fetch;
  }
  if (State = "attack") {
    +attack;
  }
  if (State = "flee") {
    +flee;
  }
  -reset.

+!update
  <-
  .now(Time);
  .print("Update cycle: ", Time);
  if (not idle_since(_)) { // For some reason, querying idle_since sometimes causes a plan failure
    +idle_since(Time);
  }
  if (not state(_)) {
    +state("reset");
  }
  if (not heading(_)) {
    +heading([0,0])
  }
  ?idle_since(IdleTime);
  ?heading(H);
  ?state(S);
  .update([["state", S], ["heading", H], ["idle_since", IdleTime]]);
  if (rotating) {
    ?position(P);
    .random_point_around(P, 10, 10, RandomPos);
    .look_at(RandomPos);
  }
  // If we fail to make progress towards meeting the goal of our state
  if ((state("attacking") & last_shot(LastShotTime) & Time - LastShotTime > 1) | (Time - IdleTime > 5)) {
    +reset;
  }
  .wait(500);
  !update.

+target_reached(T): state("centralizing")
  <-
  .print("Target reached from centralization: ", T);
  if (not rotating) {
    +rotating;
  }
  -target_reached(T).

+target_reached(T): state("fetching") & fetching(FID,FPos,FType)
  <-
  .print("Target reached from fetching: ", T);
  -fetching(FID,FPos,FType);
  -state(_);
  +state("reset");
  +reset;
  -target_reached(T).

+target_reached(T): state("attacking") & attack_target(AT)
  <-
  .print("Target reached from attack: ", T);
  -attack_target(AT);
  -state(_);
  +state("reset");
  +reset;
  -target_reached(T).

+target_reached(T): state("fleeing")
  <-
  .print("Target reached from flight: ", T);
  +flee;
  -target_reached(T).

/*  
  +enemies_in_fov(ID, Type, Angle, Distance, Health, Position)
    <-
    .shoot(3,Position).
*/
  
+friends_in_fov(ID, Type, Angle, Distance, Health, Position)
  <-
  .seen_enemy(ID, Type, Health, Angle, Position);
  -friends_in_fov(ID, Type, Angle, Distance, Health, Position);
  +threat(ID, Health, Position).

+threat(ID, Health, Position): state("fleeing") & ammo(Ammo) & Ammo > 0
  <-
  ?shot_burst(Burst);
  .min_ceil(Burst, Health * 0.55, CBurst);
  .shoot(CBurst, Position);
  .now(Time);
  -last_shot(_);
  +last_shot(Time);
  if (crit_health(CHP) & Health < CHP & Ammo > Health * 0.55) {
    -attack_target(_);
    +attack_target(Position);
    +attack_id(ID);
    +attack;
  }.

// If we're not fleeing and we see a potential target, shoot it
+threat(ID, Health, Position): not state("fleeing") & ((ammo(Ammo) & Ammo > Health * 0.55) | (state("attacking") & attack_id(AID) & AID = ID))
  <-
  ?shot_burst(Burst);
  .min_ceil(Burst, Health * 0.55, CBurst);
  .shoot(CBurst, Position);
  .now(Time);
  -last_shot(_);
  +last_shot(Time);
  if (state("centralizing") & not low_health) {
    -attack_target(_);
    +attack_target(Position);
    +attack_id(ID);
    +attack;
  }
  if ((Ammo == 0 | Health == 0) & state("attacking")) {
    +reset;
  }.

+packs_in_fov(ID, Type, Angle, Distance, Value, Position)
  <-
  //.print("Detecting a pack of type ", Type, " at position ", Position, " with value ", Value);
  .seen_pack(ID, Type, Value, Position);
  -packs_in_fov(ID, Type, Angle, Distance, Value, Position);
  +pack(ID, Type, Value, Position).

+pack(ID, Type, Value, Position): Type = 1001 & (state("fleeing") | state("centralizing")) & health(HP) & HP < 100
  <-
  -fetching(_,_,_);
  +fetching(ID, Position, Type);
  +fetch.

+pack(ID, Type, Value, Position): Type = 1002 & state("centralizing") & low_ammo(LAmmo) & ammo(Ammo) & Ammo < LAmmo
  <-
  -fetching(_,_,_);
  +fetching(ID, Position, Type);
  +fetch.

// If we see a pack we are not currently going for
+pack(ID, Type, Value, Position): state("fetching") & fetching(FID, FPosition, FType) & not ID = FID
  <-
  ?position(Here);
  ?health(HP);
  ?ammo(Ammo);
  .distance(Here, Position, NewDistance);
  .distance(Here, FPosition, OldDistance);
  if (
    (Type = 1001 & ((not FType = 1001) | NewDistance < OldDistance) & HP < 100) |
    (Type = 1002 & FType == 1002 & NewDistance < OldDistance & Ammo < 100)
  ) {
    -fetching(_,_,_);
    +fetching(ID, Position, Type);
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
+low_health : not state("fetching") | (state("fetching") & fetching(FID, FPos, FType) & not FType = 1001)
  <-
  +flee.
