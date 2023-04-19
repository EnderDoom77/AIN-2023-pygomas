// Initial Beliefs
center([128, 0, 128])
damage_factor(2)
turn_angle(1.25);
/*
ITEM STRUCTURE: ID, Time, Position, Value
Value is Health recovery for HP, Ammo recovery for AP, and remaining Health for Enemies
*/

+flag(F): team(200)
  <-
  ?center(C);
  .goto(C);
  .print("Moving towards the center: ", C);
  +rotating;
  +state(centralizing).

+rotating:
  <-
  -rotating;
  .wait(1000);
  ?turn_angle(A);
  .turn(A);
  +rotating.

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
  +enemies_in_fov(ID, Type, Angle, Distance, Health, Position)
    <-
    .shoot(3,Position).
*/
  
+friends_in_fov(ID, Type, Angle, Distance, Health, Position)
  <-
  .seen_enemy(ID, Type, Health, Position);
  -friends_in_fov(ID, Type, Angle, Distance, Health, Position);
  

+packs_in_fov(ID, Type, Angle, Distance, Value, Position)
  <-
  .seen_pack(ID, Type, Value, Position).

+threshold_health(HP)
  <-
  +fleeing
