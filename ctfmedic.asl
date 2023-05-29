state("defending").

+flag(Pos) <-
    .get_service("commander");
    .register_service("medic");
    !move_around_flag;
    !!update.

+commander(CommList): not CommList == [] <-
    .nth(0, CommList, X);
    //.print("Registered commander,", X);
    +my_commander(X).

+commander([]) <-
    .wait(500);
    .get_service("commander").

+target_reached(Pos): state("defending") <-
    -state("defending");
    +state("patrolling");
    !move_around_flag.

+target_reached(Pos): state("patrolling") <-
    !move_around_flag.

+!move_around_flag: flag(Pos)
    <-
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

+packs_in_fov(ID,Type,Angle,Distance,Health,[X,Y,Z]): not Type = 1003 <-
    .register_pack([X,Y,Z], Type, IsNew);
    if (IsNew & my_commander(Comm)) {
        .send(Comm, tell, pack_seen(X,Y,Z,Type));
    }.

+new_pack(X,Y,Z,Type) <-
    .register_pack([X,Y,Z],Type,_).

+enemies_in_fov(ID,Type,Angle,Distance,Health,[X,Y,Z]) <-
    .now(Now);
    ?position(MyPos);
    .print("Enemy detected at position ", [X,Y,Z]);
    if (my_commander(Comm)) {
        .send(Comm, tell, enemy_seen(X,Y,Z,Health,Type));
    }

    .can_shoot(MyPos, [X,Y,Z], CanShoot);
    if (CanShoot) {
        .shoot(10, [X,Y,Z]);
    }.