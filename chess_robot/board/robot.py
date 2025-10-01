import chess

from chess_robot.utils.structs import MoveInfo, Vector2
from chess_robot.utils.path_calculator import PathCalculator
from .gantry.base import Gantry


class Robot:

    def __init__(self, gantry: Gantry):
        self._gantry = gantry
        self._path_history: list[list[list[Vector2]]] = []

    def play_move(self, move: MoveInfo) -> None:
        path = []

        if move.capture_destination is not None:
            path.append(PathCalculator.indirect_path(
                start_square=move.to_square, 
                end_square=move.capture_destination,
                obstructed_squares=move.current_piece_positions
            ))

        if move.is_castling:
            path += PathCalculator.castle_path(move_uci=move.uci)

        elif move.moving_piece.piece_type == chess.KNIGHT:
            path.append(PathCalculator.knight_path(
                start_square=move.from_square, 
                end_square=move.to_square
            ))

        else:
            path.append(PathCalculator.direct_path(
                start_square=move.from_square, 
                end_square=move.to_square
            ))

        self._path_history.append(path)
        self._gantry.run_path(path)

    def undo_move(self) -> None:
        last_path = self._path_history.pop()
        reversed_path = [segment[::-1] for segment in last_path[::-1]]
        self._gantry.run_path(reversed_path)