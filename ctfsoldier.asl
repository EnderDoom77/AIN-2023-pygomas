state("initial").
my_station([0,0,0]).
low_health(50).

+flag(Pos) <-
    .get_service("commander");
    .register_service("guard");
    .now(T);
    +last_shot(T);
    !!update.

+!update <-
    if (my_commander(Comm)) {
        //.print("Soldier Reporting to", Comm);
        ?position([X,Y,Z]);
        ?health(HP);
        ?class(Class);
        .send(Comm, tell, teamdata([X, Y, Z, HP, Class]));
    }
    .now(Now);
    if (last_shot(LastShot) & Now - LastShot > 5 & state("attacking") & not enemies_in_fov(_,_,_,_,_,_)) {
        !retreat;
    }
    .wait(500);
    !update.

+commander(CommList): not CommList == [] <-
    .nth(0, CommList, X);
    .print("Registered commander,", X);
    +my_commander(X).

+commander([]) <-
    .wait(500);
    .get_service("commander").

+new_pack(X, Y, Z, Type) <-
    .print("Pack of type", Type, "registered by message at (", X, ",", Y, ",", Z, ")");
    .register_pack([X,Y,Z], Type, _).

+defend_position(Pos): state(State) & my_station(Station)
    <-
    -my_station(Station);
    +my_station(Pos);
    if (not State = "recovering") {
        -state(State);
        +state("defending");
        .goto(Pos);
        .print("Defending position", Pos);
    }.

+target_reached([X,Y,Z]): flag([FX,FY,FZ]) & state("defending")
    <-
    .look_at([2*X-FX, Y, 2*Z-FZ]).

+target_reached(Pos): fetching(FPos, FType) & state("recovering")
    <-
    .pack_taken(FPos, FType);
    if (my_commander(Comm)) {
        .send(Comm, tell, pack_taken(FPos, FType));
    }
    !reset.

+health(HP): low_health(LHP) & HP < LHP & not bloody
    <-
    +bloody.

+health(HP): low_health(LHP) & HP > LHP & bloody
    <-
    -bloody.

+bloody: state(State)
    <-
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

+!fetch_health : position(Pos) <-
    .nearest_health_pack(Pos, [PX,PY,PZ]);
    !fetch(PX,PY,PZ,1001).

+!fetch_ammo : position(Pos) <-
    .nearest_ammo_pack(Pos, [PX,PY,PZ]);
    !fetch(PX,PY,PZ,1002).

+!fetch(PX,PY,PZ, PackType) : state(State) <-
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

+!retreat : my_station(Pos) & state(State) <-
    -state(State);
    +state("defending");
    .goto(Pos).

+!attack([AX,AY,AZ]) : position(X,Y,Z) & state(State) <-
    -state(State);
    +state("attacking");
    .goto([X * 0.5 + AX * 0.5, AY, AZ * 0.5 + Z * 0.5]).

+attack_target(X,Y,Z) <-
    .print("Received command to attack", [X,Y,Z]);
    +attacking([X,Y,Z]).

+enemies_in_fov(ID,Type,Angle,Distance,Health,[X,Y,Z]) : last_shot(LastShot) <-
    .now(Now);
    ?position(MyPos);
    .print("Enemy detected at position ", [X,Y,Z]);
    if (my_commander(Comm)) {
        .send(Comm, tell, enemy_seen(X,Y,Z,Health,Type));
    }

    .can_shoot(MyPos, [X,Y,Z], CanShoot);
    if (CanShoot) {
        if (attacking(AttackPos)) {
            .distance([X,Y,Z], AttackPos, Dist);
            if (Dist < 5) {
                .shoot(10, [X,Y,Z]);
                -last_shot(LastShot);
                +last_shot(Now);
            } else {
                if (Now - LastShot > 1) {
                    .shoot(10, [X,Y,Z]);
                    !attack([X,Y,Z]);
                } 
            }
        } else {
            .shoot(10, Position);
        }
    }.
    
