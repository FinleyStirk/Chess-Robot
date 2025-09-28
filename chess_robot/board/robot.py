import chess

from utils.structs import MoveInfo
from utils.path_calculator import PathCalculator
from gantry.base import Gantry


class Robot:

    def __init__(self, gantry: Gantry):
        self._gantry = gantry

    def play_move(self, move: MoveInfo):
        path = []

        if move.capture_destination is not None:
            path += PathCalculator.indirect_path(
                start_square=move.to_square, 
                end_square=move.capture_destination,
                obstructed_squares=move.current_piece_positions
            )

        if move.is_castling:
            path += PathCalculator.castle_path(move_uci=move.uci)

        elif move.moving_piece is chess.KNIGHT:
            path += PathCalculator.knight_path(
                start_square=move.from_square, 
                end_square=move.to_square
            )

        else:
            path += PathCalculator.direct_path(
                start_square=move.from_square, 
                end_square=move.to_square
            )

        self._gantry.run_path(path)
