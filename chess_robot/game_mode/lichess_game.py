from .base import GameMode
from integrations.lichess_api import LichessAPI
from board.robot_board import RobotBoard

# Fix this
class LichessAIGame(GameMode):

    def __init__(self, board: RobotBoard, lichess_api: LichessAPI, ai_strength: int = None, game_id: str = None):
        super().__init__(board=board)
        self._lichess_api = lichess_api

        if game_id is not None:
            pass

        elif ai_strength is not None:
            lichess_api.start_ai_game(ai_strength=ai_strength)

        else:
            raise ValueError("Either an ai_strength or a game_id must be provided")

    def player_move(self):
        move = input()
        self._board.play_move(move)
        self._lichess_api.make_move(move)

    def opponent_move(self):
        move = self._lichess_api.wait_for_opponent_move()
        self._board.play_move(move)
