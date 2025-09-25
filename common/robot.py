from common.structs import MoveInfo, Vector2
from common.gantry import Gantry, VirtualGantry
from common.path_calculator import PathCalculator
import numpy as np
import chess


class Robot:

    def __init__(self, gantry: Gantry):
        self._gantry = gantry

    def play_move(self, move: MoveInfo):
        path = []

        if move.capture_destination is not None:
            path += PathCalculator.indirect_path(
                start_square=move.from_square, 
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


    
if __name__ == "__main__":
    gantry = VirtualGantry()
    robot = Robot(gantry)
    move = MoveInfo(uci='e4d5', from_square=Vector2(x=4, y=3), to_square=Vector2(x=3, y=4), moving_piece="P", captured_piece="p", capture_destination=Vector2(x=-2, y=0), is_castling=False, is_enpassant=False, current_piece_positions={Vector2(x=4, y=0), Vector2(x=3, y=4), Vector2(x=4, y=3), Vector2(x=3, y=1), Vector2(x=3, y=7), Vector2(x=4, y=6), Vector2(x=5, y=1), Vector2(x=5, y=7), Vector2(x=1, y=0), Vector2(x=1, y=6), Vector2(x=7, y=1), Vector2(x=7, y=7), Vector2(x=3, y=0), Vector2(x=5, y=0), Vector2(x=5, y=6), Vector2(x=0, y=1), Vector2(x=0, y=7), Vector2(x=2, y=1), Vector2(x=2, y=7), Vector2(x=6, y=1), Vector2(x=7, y=0), Vector2(x=6, y=7), Vector2(x=7, y=6), Vector2(x=4, y=7), Vector2(x=-3, y=4), Vector2(x=0, y=0), Vector2(x=10, y=4), Vector2(x=1, y=1), Vector2(x=2, y=0), Vector2(x=0, y=6), Vector2(x=1, y=7), Vector2(x=2, y=6), Vector2(x=6, y=0), Vector2(x=6, y=6)})
    robot.play_move(move)