// Simple differential equation  der(x) = -a*x
model HDE
  Real x(start = 1, fixed = true);
  parameter Real a = 1;
equation
  der(x) = -a*x;
end HDE;
