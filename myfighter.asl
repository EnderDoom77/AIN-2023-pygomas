// Initial Beliefs
center([128, 0, 128])
damage_factor(2)
turn_angle(1.25);
/*
ITEM STRUCTURE: ID, Time, Position, Value
Value is Health recovery for HP, Ammo recovery for AP, and remaining Health for Enemies
*/
known_health_pack()
known_ammo_pack()
known_enemy()

+flag(F): team(200)
  <-
  .create_control_points(F,100,3,C);
  +control_points(C);
  //.wait(5000);
  .length(C,L);
  +total_control_points(L);
  +patrolling;
  +patroll_point(0);
  .print("Got control points:", C).


+target_reached(T): patrolling & team(200)
  <-
  ?patroll_point(P);
  -+patroll_point(P+1);
  -target_reached(T).

+patroll_point(P): total_control_points(T) & P<T
  <-
  ?control_points(C);
  .nth(P,C,A);
  .goto(A).

+patroll_point(P): total_control_points(T) & P==T
  <-
  -patroll_point(P);
  +patroll_point(0).
 
/*  
  +enemies_in_fov(ID,Type,Angle,Distance,Health,Position)
    <-
    .shoot(3,Position).
*/
  
+friends_in_fov(ID,Type,Angle,Distance,Health,Position)
  <-
  .shoot(3,Position).
