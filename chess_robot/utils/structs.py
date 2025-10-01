import math
from typing import Optional
from enum import Enum
from dataclasses import dataclass

import chess

class CommandType(Enum):
    MOVE = 0
    UNDO = 1
    SET_FEN = 2
    RESET = 3

@dataclass(frozen=True)
class RobotCommand:
    command: CommandType
    data: Optional[str] = None

    @classmethod
    def move(cls, move_str: str) -> "RobotCommand":
        return cls(CommandType.MOVE, move_str)

    @classmethod
    def undo(cls) -> "RobotCommand":
        return cls(CommandType.UNDO)
    
    @classmethod
    def reset(cls) -> "RobotCommand":
        return cls(CommandType.RESET)
    
    def set_fen(cls, fen: str) -> "RobotCommand":
        return cls(CommandType.SET_FEN, fen)


@dataclass(frozen=True)
class Vector2:
    x: int | float
    y: int | float

    @staticmethod
    def distance(v1: "Vector2", v2: "Vector2") -> float:
        x_distance_squared = (v1.x - v2.x) ** 2
        y_distance_squared = (v1.y - v2.y) ** 2
        return math.sqrt(x_distance_squared + y_distance_squared)
    
    @staticmethod
    def lerp(v1: "Vector2", v2: "Vector2", t: float) -> "Vector2":
        return v1 + t * (v2 - v1)

    def __add__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other: int | float) -> "Vector2":
        return Vector2(self.x * other, self.y * other)
    
    def __rmul__(self, other: int | float) -> "Vector2":
        return self.__mul__(other)
    
    def __eq__(self, other: "Vector2") -> bool:
        return self.x == other.x and self.y == other.y


@dataclass(frozen=True)
class Cell:
    position: Vector2
    parent: Optional["Cell"] = None


@dataclass(frozen=True)
class MoveInfo:
    uci: str
    from_square: Optional[Vector2] = None
    to_square: Optional[Vector2] = None
    moving_piece: Optional[chess.Piece] = None
    captured_piece: Optional[chess.Piece] = None
    capture_destination: Optional[Vector2] = None
    is_castling: bool = False
    is_enpassant: bool = False
    current_piece_positions: frozenset[Vector2] = frozenset()
    

class PieceStorage:
    
    def __init__(self):
        self._state = {
            chess.Piece(chess.ROOK,   chess.BLACK): Storage(empty=[Vector2(-3, 0), Vector2(-3, 7)]),
            chess.Piece(chess.KNIGHT, chess.BLACK): Storage(empty=[Vector2(-3, 1), Vector2(-3, 6)]),
            chess.Piece(chess.BISHOP, chess.BLACK): Storage(empty=[Vector2(-3, 2), Vector2(-3, 5)]),
            chess.Piece(chess.QUEEN,  chess.BLACK): Storage(empty=[Vector2(-3, 3)], filled=[Vector2(-3, 4)]),
            chess.Piece(chess.PAWN,   chess.BLACK): Storage(empty=[Vector2(-2, i) for i in range(8)]),

            chess.Piece(chess.ROOK,   chess.WHITE): Storage(empty=[Vector2(10, 0), Vector2(10, 7)]),
            chess.Piece(chess.KNIGHT, chess.WHITE): Storage(empty=[Vector2(10, 1), Vector2(10, 6)]),
            chess.Piece(chess.BISHOP, chess.WHITE): Storage(empty=[Vector2(10, 2), Vector2(10, 5)]),
            chess.Piece(chess.QUEEN,  chess.WHITE): Storage(empty=[Vector2(10, 3)], filled=[Vector2(10, 4)]),
            chess.Piece(chess.PAWN,   chess.WHITE): Storage(empty=[Vector2(9, i) for i in range(8)]),
        }
    
    def get_filled(self) -> list[Vector2]:
        filled_storage = []
        for storage in self._state.values():
            filled_storage += storage.filled
        return filled_storage

    def piece_at(self, position: Vector2) -> chess.Piece:
        for piece in self._state:
            if self._state[piece].has_piece_at(position):
                return piece
            
    def get_next_free(self, piece: chess.Piece) -> Vector2:
        return self._state[piece].get_next_free()

    def add(self, piece: chess.Piece) -> Vector2:
        return self._state[piece].add()
    
    def remove(self, piece: chess.Piece) -> Vector2:
        return self._state[piece].remove()
    

class Storage:

    def __init__(self, filled: Optional[list[Vector2]] = None, empty: Optional[list[Vector2]] = None):
        self.filled = filled or []
        self.empty = empty or []

    def get_next_free(self) -> Vector2:
        return self.empty[0]

    def add(self) -> Vector2:
        square = self.empty.pop(0)
        self.filled.insert(0, square)
        return square
    
    def remove(self) -> Vector2:
        square = self.filled.pop(0)
        self.empty.insert(0, square)
        return square
    
    def has_piece_at(self, position: Vector2) -> bool:
        return position in self.filled
    


