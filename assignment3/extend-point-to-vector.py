from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Point):
            return False

        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        return f"Point({self.x}, {self.y})"

    def distance_to(self, other: "Point") -> float:
        if not isinstance(other, Point):
            raise TypeError("distance_to expects another Point")

        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Vector(Point):
    def __str__(self) -> str:
        return f"Vector<{self.x}, {self.y}>"

    def __add__(self, other: "Vector") -> "Vector":
        if not isinstance(other, Vector):
            return NotImplemented

        return Vector(self.x + other.x, self.y + other.y)


def main():
    point_a = Point(0, 0)
    point_b = Point(3, 4)
    point_c = Point(3, 4)

    vector_a = Vector(2, 5)
    vector_b = Vector(4, -1)
    vector_c = vector_a + vector_b

    print(point_a)
    print(point_b)
    print(point_b == point_c)
    print(point_a.distance_to(point_b))
    print(vector_a)
    print(vector_b)
    print(vector_c)


if __name__ == "__main__":
    main()
