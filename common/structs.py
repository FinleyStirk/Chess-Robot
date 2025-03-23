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
class MoveBuffer:
    def __init__(self, moves=[]):
        self.moves = []
        self.Add(moves)

    def IsEmpty(self):
        return len(self.moves) == 0

    def Next(self):
        return self.moves.pop(0)

    def Add(self, moves):
        if type(moves) == list:
            self.moves += list(moves)
        else:
            self.moves.append(moves)
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
class Node:
    def __init__(self, g, h, parent, name):
        self.parent = parent
        self.name = name
        self.g = g
        self.h = h
        self.f = h + g

    def __repr__(self):
        return f"({self.name} : {self.f})"    
class Storage:
    def __init__(self, emptyStorage, filledStorage = []):
        self.emptyStorage = emptyStorage
        self.filledStorage = filledStorage
    
    def FillStorage(self):
        space = self.emptyStorage.pop(0)
        self.filledStorage.append(space)
        return space
    
    def EmptyStorage(self):
        space = self.filledStorage.pop(0)
        self.emptyStorage.append(space)
        return space
class Stack:
    def __init__(self):
        self.__stack = []
        self.__endPointer = -1
    
    def Add(self, element):
        self.__stack.append(element)
        self.__endPointer += 1
    
    def Pop(self):
        element = self.__stack.pop(self.__endPointer)
        self.__endPointer -= 1
        return element
# <---------------------------> #