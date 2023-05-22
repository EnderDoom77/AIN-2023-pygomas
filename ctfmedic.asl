state("defending").

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
        .print("Medic Reporting to", Comm);
        ?position([X,Y,Z]);
        ?health(HP);
        .send(Comm, tell, my_status(X, Y, Z, HP));
    }
    if (state("patrolling")) {
        .cure;
    }
    .wait(500);
    !update.