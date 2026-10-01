// Planar pendulum as a DAE: 4 differential and 1 algebraic equation.
// The rod force F is an unknown that is computed from the constraint.
model Pendulum "Planar pendulum"
  parameter Real m = 1, g = 9.81, L = 0.5;
  Real F;
  Real x(start = 0.5, fixed = true), y(start = 0);
  Real vx, vy;
equation
  m*der(vx) = -(x/L)*F;
  m*der(vy) = -(y/L)*F - m*g;
  der(x) = vx;
  der(y) = vy;
  x^2 + y^2 = L^2;   // algebraic equation (constraint of the rod)
end Pendulum;
