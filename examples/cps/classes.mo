// Classes and instances
class Point "Point in a three-dimensional space"
  Real x;
  Real y;
  Real z;
end Point;

class Triangle
  Point point1;
  Point point2;
  Point point3;
end Triangle;

class Triangle2 "with modification of an instance"
  Point point1(x = 1, y = 2, z = 3);
  Point point2;
  Point point3;
end Triangle2;
