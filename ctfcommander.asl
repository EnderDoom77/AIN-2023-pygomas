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
  .wait(500);
  !update.

+my_status(X,Y,Z,Health)[source(A)]
  <-
  .print("Received status");
  .register_position(A, [X,Y,Z], Health).

+pack_seen(X,Y,Z,Type)
  <-
  .register_pack(Position, Type, IsNew);
  if (IsNew) {
    .print("New pack of type,", Type, "detected at", Position);
    !broadcast(new_pack(X,Y,Z,Type));
  }.

+!broadcast(Msg)
  <-
  .print("Broadcasting", Msg);
  .get_team(Allies);
  for (.member(A, Allies)) {
    .send(A, tell, Msg);
  }.

+packs_in_fov(ID, Type, Angle, Distance, Value, [X,Y,Z]): Type < 1003
  <-
  .print("Pack of type", Type, "in fov at", [X,Y,Z]);
  +pack_seen(X,Y,Z,Type).

+!command_circle
  <-
  +guard_command("circle");
  .get_service("guard").

+guard(Guards): guard_command("circle") <-
  -guard_command("circle");
  ?flag(FlagPos);
  .get_circular_formation(FlagPos, 20, Guards, Stations);
  +temp_var_i(0);
  for (.member(G,Guards)) {
    ?temp_var_i(I);
    .nth(I,Stations,Pos);
    .send(G,tell,defend_position(Pos));
    -temp_var_i(I);
    +temp_var_i(I+1);
  }
  .print("Commanded foot soldiers into defensive formation").
  