state("initial").
my_station([0,0,0]).

+flag(Pos) <-
    .get_service("commander");
    .register_service("guard");
    !!update.

+!update <-
    if (my_commander(Comm)) {
        //.print("Fieldop Reporting to", Comm);
        ?position([X,Y,Z]);
        ?health(HP);
        ?class(Class);
        .send(Comm, tell, teamdata([X, Y, Z, HP, Class]));
    }
    .now(Now);
    if (last_shot(LastShot) & Now - LastShot > 5 & state("attacking") & not enemies_in_fov(_,_,_,_,_,_)) {
        !retreat;
    }
    if (target_reached(_)) {
        .reload;
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
