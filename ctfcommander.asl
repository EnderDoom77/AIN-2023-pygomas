guard_radius(15).

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
  .print("I'm alive");
  .wait(500);
  if (target_reached(_) & position(Pos)) {
    .random_point_around(Pos, 10, 10, RandPos);
    .look_at(RandPos);
  }
  !update.

+teamdata(X,Y,Z,Health)[source(A)]
  <-
  .print("Received status");
  // .register_position(A, [X,Y,Z], Health);
  -teamdata(_,_,_,_).

+pack_seen(X,Y,Z,Type)
  <-
  .register_pack(Position, Type, IsNew);
  if (IsNew) {
    .print("New pack of type,", Type, "detected at", Position);
    !broadcast(new_pack(X,Y,Z,Type));
  }.

+enemy_seen(X,Y,Z,Health) <-
  .register_enemy([X,Y,Z], Health).

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
  