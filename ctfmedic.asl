state("defending").

// INITIALIZATION

+flag(Pos) <-
    .get_service("commander");
    .register_service("medic");
    !move_around_flag;
    !!update.

+commander(CommList): not CommList == [] <-
    .nth(0, CommList, X);
    .print("Registered commander,", X);
    +my_commander(X).

+commander([]) <-
    .wait(500);
    .get_service("commander").

// PATROL

+target_reached(Pos): state("defending") <-
    -state("defending");
    +state("patrolling");
    !move_around_flag.

+target_reached(Pos): state("patrolling") <-
    !move_around_flag.

+!move_around_flag: flag(Pos) <-
    .random_point_around(Pos, 5, 20, PatrolPoint);
    .goto(PatrolPoint).

+!update <-
    if (my_commander(Comm)) {
        ?position([X,Y,Z]);
        ?health(HP);
        ?class(Class);
        //.print("Medic Reporting position", [X,Y,Z], "and health", HP, "to", Comm);
        .send(Comm, tell, teamdata([X, Y, Z, HP, Class]));
    }
    if (target_reached(_)) {
        .cure;
    }
    .wait(500);
    !update.
    
+enemies_in_fov(ID,Type,Angle,Distance,Health,[X,Y,Z]) <-
    .now(Now);
    ?position(MyPos);
    //.print("Enemy detected at position ", [X,Y,Z]);
    if (my_commander(Comm)) {
        .send(Comm, tell, enemy_seen([X,Y,Z,Health,Type]));
    }

    .can_shoot(MyPos, [X,Y,Z], CanShoot);
    if (CanShoot) {
        .shoot(10, [X,Y,Z]);
    }.

/*
 * COMMON BEHAVIOUR
 */

+packs_in_fov(ID,Type,Angle,Distance,Health,[X,Y,Z]): Type > 1000 & Type < 1003 <-
    .register_pack([X,Y,Z], Type, IsNew);
    if (IsNew & my_commander(Comm)) {
        .send(Comm, tell, pack_seen([X,Y,Z,Type]));
    }.

+new_pack([X,Y,Z,Type]) <-
    .register_pack([X,Y,Z],Type,_).

+!fetch_health : position(Pos) <-
    .nearest_health_pack(Pos, [PX,PY,PZ]);
    !fetch(PX,PY,PZ,1001).

+!fetch_ammo : position(Pos) <-
    .nearest_ammo_pack(Pos, [PX,PY,PZ]);
    !fetch(PX,PY,PZ,1002).

+!fetch(PX,PY,PZ, PackType) : state(State) <-
    .print("Fetching pack of type", PackType, "at position", [PX,PY,PZ]);
    if (PX >= 0 & PY >= 0 & PZ >= 0) {
        // remove all outstanding fetching positions
        for (fetching(AnyPos, AnyType)) {
            -fetching(AnyPos, AnyType);
        }
        -state(State);
        +state("fetching");
        +fetching([PX,PY,PZ], PackType);
        .goto([PX,PY,PZ]);
    } else {
        if (fetching(PrevPos, PrevType)) {
            .goto(PrevPos);
            .wait(250);
        } else {
            .wait(250);
            !reset;
        }
    }.

+health(HP): low_health(LHP) & HP < LHP & not bloody <-
    +bloody.

+health(HP): low_health(LHP) & HP > LHP & bloody <-
    -bloody.

+bloody: state(State) <-
    !reset.

+ammo(Ammo): Ammo < 10 & not bloody <-
    !reset.

+!reset: state(State) & health(HP) & ammo(Ammo) & last_shot(LastShot) <-
    .now(Now);
    if (HP < 80) {
        !fetch_health;
    } else {
        if (Ammo < 25) {
            !fetch_ammo;
        } else {
            if (Now - LastShot < 3 & attacking(AttackPos)) {
                !attack(AttackPos);
            } else {
                !retreat;
            }
        }
    }.

+!retreat : my_station(Pos) & state(State) & flag(FlagPos) <-
    -state(State);
    +state("defending");
    !move(Pos, FlagPos).

+!move([X,Y,Z]) : position([CurrentX, CurrentY, CurrentZ]) <-
    !move([X,Y,Z], [CurrentX, CurrentY, CurrentZ]).

+!move([X,Y,Z], [BiasX, BiasY, BiasZ]) <-
    .is_walkable([X,Y,Z], Walkable);
    if (Walkable) {
        .goto([X,Y,Z]);
    } else {
        !move([X * 0.8 + BiasX * 0.2, BiasY, Z * 0.8 + BiasZ * 0.2]);
    }.

/*
 * END COMMON BEHAVIOUR
 */
    