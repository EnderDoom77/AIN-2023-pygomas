+flag(Pos) <-
    .get_service("commander");
    .register_service("medic");
    !!update.

+commander(CommList): not CommList == [] <-
    .nth(0, CommList, X);
    +my_commander(X).

+commander([]) <-
    .wait(500);
    .get_service("commander").

+!update <-
    if (my_commander(Comm)) {
        ?position(Here);
        .send(Comm, "tell", mypos(Here));
    }
    .wait(500);
    !update.