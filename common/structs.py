import chess
from dataclasses import dataclass

class GantryCommand:
    def __init__(self, x: float, y: float, magnet_state: int):
        self.x = x
        self.y = y
        self.magnet_state = magnet_state

    def __repr__(self):
        return f"Coord(x={self.x}, y={self.y}, magnet_state={self.magnet_state})"
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
@dataclass(frozen=True)
class Vector2:
    x: int
    y: int
    
    def __add__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __eq__(self, other: "Vector2") -> bool:
        return self.x == other.x and self.y == other.y

class Cell:
    def __init__(self, position: Vector2, parent: "Cell" = None):
        self.position = position
        self.parent = parent

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
        return GantryCommand(self.x, self.y, emState)
    
class PieceStorage:
    def __init__(self):
        self._state = {
            chess.Piece.from_symbol("r"): Storage(empty=[Vector2(-3, 0), Vector2(-3, 7)]),
            chess.Piece.from_symbol("n"): Storage(empty=[Vector2(-3, 1), Vector2(-3, 6)]),
            chess.Piece.from_symbol("b"): Storage(empty=[Vector2(-3, 2), Vector2(-3, 5)]),
            chess.Piece.from_symbol("q"): Storage(empty=[Vector2(-3, 3)], filled=[Vector2(-3, 4)]),
            chess.Piece.from_symbol("p"): Storage(empty=[Vector2(-2, i) for i in range(8)]),

            chess.Piece.from_symbol("R"): Storage(empty=[Vector2(10, 0), Vector2(10, 7)]),
            chess.Piece.from_symbol("N"): Storage(empty=[Vector2(10, 1), Vector2(10, 6)]),
            chess.Piece.from_symbol("B"): Storage(empty=[Vector2(10, 2), Vector2(10, 5)]),
            chess.Piece.from_symbol("Q"): Storage(empty=[Vector2(10, 3)], filled=[Vector2(10, 4)]),
            chess.Piece.from_symbol("P"): Storage(empty=[Vector2(9, i) for i in range(8)]),
        }
    
    def get_filled(self) -> list[Vector2]:
        filled_storage = []
        for storage in self._state.values():
            filled_storage += storage.filled
        return filled_storage

    def piece_at(self, position):
        for piece in self._state:
            if self._state[piece].has_piece_at(position):
                return piece
            
    def get_next_free(self, piece):
        return self._state[piece].get_next_free()

    def add(self, piece):
        return self._state[piece].add()
    
    def remove(self, piece):
        return self._state[piece].remove()
    
class Storage:
    def __init__(self, filled: list[Vector2] = None, empty: list[Vector2] = None):
        self.filled = filled or []
        self.empty = empty or []

    def get_next_free(self):
        return self.empty[0]

    def add(self):
        square = self.empty.pop(0)
        self.filled.insert(0, square)
        return square
    
    def remove(self):
        square = self.filled.pop(0)
        self.empty.insert(0, square)
        return square
    
    def has_piece_at(self, position: Vector2) -> bool:
        return position in self.filled
    
class MoveInfo:
    def __init__(
            self, 
            uci: str,
            from_square: Vector2 = None,
            to_square: Vector2 = None,
            moving_piece: chess.Piece = None,
            captured_piece: chess.Piece = None,
            capture_destination: Vector2 = None,
            is_castling: bool = False,
            is_enpassant: bool = False,
            current_piece_positions: set[Vector2] = set(),
        ):
        self.uci = uci
        self.from_square = from_square
        self.to_square = to_square
        self.moving_piece = moving_piece
        self.capture_destination = capture_destination
        self.is_castling = is_castling
        self.is_enpassant = is_enpassant
        self.captured_piece = captured_piece
        self.current_piece_positions = current_piece_positions


    def __repr__(self):
        return (
            f"MoveInfo(uci='{self.uci}', "
            f"from_square={self.from_square}, to_square={self.to_square}, "
            f"moving_piece='{self.moving_piece}', "
            f"captured_piece='{self.captured_piece}', "
            f"capture_destination={self.capture_destination}, "
            f"is_castling={self.is_castling}, "
            f"is_enpassant={self.is_enpassant}, "
            f"pieces={self.current_piece_positions})"
        )

