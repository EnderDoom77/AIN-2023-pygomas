+flag(Pos) <-
    .register_service("commander");
    .print("Moving to", Pos);
    .goto(Pos).

+mypos(Pos)[source(A)]:
    .register_position(A, Pos).