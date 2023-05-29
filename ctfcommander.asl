state("centralizing").
guard_radius(15).
last_attack(0).
low_health(75).

// INITIALIZATION

+flag(Pos) <-
    .register_service("commander");
    .print("Moving to", Pos);
    .goto(Pos);
    !!update;
    .wait(1000);
    !command_circle.

+!update
    <-
    .update([]);
    //.print("I'm alive");
    .wait(500);
    if (target_reached(_) & position(Pos)) {
        .random_point_around(Pos, 10, 10, RandPos);
        .look_at(RandPos);
    }
    !update.

// ################
// # COORDINATION #
// ################

+teamdata([X,Y,Z,Health,Class])[source(A)]
    <-
    //.print("Received status");
    .register_position(A, [X,Y,Z], Health, Class);
    if (not ally(A)) {
        +ally(A);
    }
    -teamdata(_,_,_,_,_).

+pack_seen([X,Y,Z,Type])
    <-
    .register_pack([X,Y,Z], Type, IsNew);
    if (IsNew) {
        .print("New pack of ", Type, "detected at", [X,Y,Z]);
        !broadcast(new_pack([X,Y,Z,Type]));
    }.

+pack_taken([FX,FY,FZ,FType]) <-
    .pack_taken([FX,FY,FZ],FType);
    !broadcast(pack_gone([FX,FY,FZ,FType])).

+enemy_seen([X,Y,Z,Health,Type]) <-
    .register_enemy([X,Y,Z], Health, Type);
    .now(Now);
    ?last_attack(LastAtt);
    if (Now - LastAtt > 3) {
        !schedule_attack([X,Y,Z]);
    }.

+!schedule_attack([X,Y,Z]) <-
    !broadcast(attack_target([X,Y,Z]));
    .now(Now);
    -last_attack(_);
    +last_attack(Now).

+!broadcast(Msg) <-
    .print("Broadcasting", Msg);
    for (ally(A)) {
        //.print("    Sending broadcast to", A);
        .send(A, tell, Msg);
    }.

+packs_in_fov(ID, Type, Angle, Distance, Value, [X,Y,Z]): Type < 1003
    <-
    //.print("Pack of type", Type, "in fov at", [X,Y,Z]);
    +pack_seen([X,Y,Z,Type]).

+!command_circle
    <-
    +guard_command("circle");
    .get_service("guard").

+guard(Guards): guard_command("circle") <-
    -guard_command("circle");
    ?flag(FlagPos);
    ?guard_radius(GRadius);
    .get_circular_formation(FlagPos, GRadius, Guards, Stations);
    +temp_var_i(0);
    for (.member(G,Guards)) {
        ?temp_var_i(I);
        .nth(I,Stations,Pos);
        .send(G,tell,defend_position(Pos));
        -temp_var_i(I);
        +temp_var_i(I+1);
    }
    .print("Commanded foot soldiers into defensive formation").

// ################################
// # GENERAL INDIVIDUAL BEHAVIOUR #
// ################################

+health(HP): low_health(LHP) & HP < LHP & not bloody
    <-
    +bloody.

+health(HP): low_health(LHP) & HP > LHP & bloody
    <-
    -bloody.

+bloody <-
    !fetch_health.

+!fetch_health : position(Pos) <-
    .nearest_health_pack(Pos, [PX,PY,PZ]);
    !fetch(PX,PY,PZ,1001).

+!fetch_ammo : position(Pos) <-
    .nearest_ammo_pack(Pos, [PX,PY,PZ]);
    !fetch(PX,PY,PZ,1002).

+!fetch(PX,PY,PZ,PackType) : state(State) <-
    if (PX >= 0 & PY >= 0 & PZ >= 0) {
        // remove all outstanding fetching positions
        for (fetching(AnyPos, AnyType)) {
            -fetching(AnyPos, AnyType);
        }
        -state(State);
        +state("fetching");
        +fetching([PX,PY,PZ], PackType);
        .goto(PackPos);
    } else {
        if (fetching(PrevPos, PrevType)) {
            .goto(PrevPos);
            .wait(250);
        } else {
            .wait(250);
            !reset;
        }
    }.

+!retreat : flag(FlagPos) <-
    -state(_);
    +state("centralizing");
    .goto(FlagPos).

+!reset : state(State) & health(HP) & ammo(Ammo) <-
    .now(Now);
    if (HP < 80) {
        !fetch_health;
    } else {
        if (Ammo < 25) {
            !fetch_ammo;
        } else {
            !retreat;
        }
    }.

