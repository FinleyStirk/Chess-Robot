# Objects #
# <---------------------------> #
class Coord:
    def __init__(self, x, y, emState):
        self.x = x
        self.y = y
        self.emState = emState

    def __repr__(self):
        return f"(x={self.x}, y={self.y}, emState={self.emState})"
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.index = y * 8 + x

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y

        return Vector2(x, y)
    
    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y

        return Vector2(x, y)

    def __eq__(self, other):
        if type(self) == type(other):
            return self.x == other.x and self.y == other.y
        else:
            return False

    def __repr__(self):
        return f"({self.x}, {self.y})"
    
class Node(Vector2):
    def __init__(self, x : int, y : int):
        super().__init__(x, y)
        self.parent = None
        self.direction = None

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y

        return Node(x, y)
    
    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y

        return Node(x, y)
    
    def toCoord(self, emState):
        return Coord(self.x, self.y, emState)
    
class PieceStorage:
    def __init__(self):
        self._state = {
            "r": Storage(empty=[Vector2(-3, 0), Vector2(-3, 7)]),
            "n": Storage(empty=[Vector2(-3, 1), Vector2(-3, 6)]),
            "b": Storage(empty=[Vector2(-3, 2), Vector2(-3, 5)]),
            "q": Storage(empty=[Vector2(-3, 3)], filled=[Vector2(-3, 4)]),
            "p": Storage(empty=[Vector2(-2, i) for i in range(8)]),
            "R": Storage(empty=[Vector2(10, 0), Vector2(10, 7)]),
            "N": Storage(empty=[Vector2(10, 1), Vector2(10, 6)]),
            "B": Storage(empty=[Vector2(10, 2), Vector2(10, 5)]),
            "Q": Storage(empty=[Vector2(10, 3)], filled=[Vector2(10, 4)]),
            "P": Storage(empty=[Vector2(9, i) for i in range(8)]),
        }
    
    def get_filled_storage(self) -> list[Vector2]:
        filled_storage = []
        for storage in self._state.values():
            filled_storage += storage.filled_storage
        return filled_storage

    def piece_at(self, position):
        for piece in self._state:
            if self._state[piece].has_piece_at(position):
                return piece

    def add_to_storage(self, piece):
        return self._state[piece].add_to_storage()
    
    def remove_from_storage(self, piece):
        return self._state[piece].remove_from_storage()
    
class Storage:
    def __init__(self, filled: list[Vector2] = None, empty: list[Vector2] = None):
        self.filled_storage = filled or []
        self.empty_storage = empty or []

    def add_to_storage(self):
        square = self.empty_storage.pop(0)
        self.filled_storage.insert(0, square)
        return square
    
    def remove_from_storage(self):
        square = self.filled_storage.pop(0)
        self.empty_storage.insert(0, square)
        return square
    
    def has_piece_at(self, position: Vector2) -> bool:
        return position in self.filled_storage

# <---------------------------> #