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
class Storage:
    def __init__(self, emptyStorage, filledStorage = None):
        self.emptyStorage = emptyStorage
        if filledStorage == None:
            self.filledStorage = []
        else:
            self.filledStorage = filledStorage
    
    def AddToStorage(self):
        square = self.emptyStorage.pop(0)
        self.filledStorage.insert(0, square)
        return square
    
    def RemoveFromStorage(self):
        square = self.filledStorage.pop(0)
        self.emptyStorage.insert(0, square)
        return square
# <---------------------------> #