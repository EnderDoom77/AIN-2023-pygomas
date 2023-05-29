guard_radius(15).
last_attack(0).

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

+teamdata([X,Y,Z,Health,Class])[source(A)]
  <-
  //.print("Received status");
  .register_position(A, [X,Y,Z], Health, Class);
  -teamdata(_,_,_,_,_).

+pack_seen(X,Y,Z,Type)
  <-
  .register_pack([X,Y,Z], Type, IsNew);
  if (IsNew) {
    .print("New pack of ", Type, "detected at", [X,Y,Z]);
    !broadcast(new_pack(X,Y,Z,Type));
  }.

+enemy_seen(X,Y,Z,Health,Type) <-
  .register_enemy([X,Y,Z], Health, Type);
  .now(Now);
  ?last_attack(LastAtt);
  if (Now - LastAtt > 3) {
    !schedule_attack([X,Y,Z]);
  }.

+!schedule_attack([X,Y,Z]) <-
  .get_team(Allies);
  .print("Commanding attack on position", [X,Y,Z], "for allies", Allies);
  for (.member(A, Allies)) {
    .send(M, tell, attack_target(X,Y,Z));
  }
  .now(Now);
  -last_attack(_);
  +last_attack(Now).

+!broadcast(Msg) <-
  .print("Broadcasting", Msg);
  .get_team(Allies);
  for (.member(A, Allies)) {
    .send(A, tell, Msg);
  }.

+packs_in_fov(ID, Type, Angle, Distance, Value, [X,Y,Z]): Type < 1003
  <-
  //.print("Pack of type", Type, "in fov at", [X,Y,Z]);
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
  