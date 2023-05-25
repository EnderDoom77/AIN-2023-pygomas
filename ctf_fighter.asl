//EJEMPLO LUCHADOR 

+flag(F)
  <-
  ?position(Pos);
  +initial_pos(Pos);
  .goto(F).

+target_reached(T): initial_pos(InitPos)
  <-
  .goto(InitPos).

+enemies_in_fov(ID,Type,Angle,Distance,Health,Position)
  <-
  .shoot(3,Position).
