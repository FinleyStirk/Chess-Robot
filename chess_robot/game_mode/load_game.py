import chess.pgn

from .base import GameMode
from chess_robot.board.robot_board import RobotBoard


class LoadGame(GameMode):

    def __init__(self, board: RobotBoard, pgn_path: str):
        super().__init__(board)

        pgn = open(pgn_path)
        game = chess.pgn.read_game(pgn)
        self.moves = iter(game.mainline_moves())

    def player_move(self) -> None:
        next_move = next(self.moves)
        self._board.play_move(next_move.uci())
        input()

    def opponent_move(self) -> None:
        self.player_move()