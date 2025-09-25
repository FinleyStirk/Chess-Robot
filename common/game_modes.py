from abc import ABC, abstractmethod
from common.robot_board import RobotBoard
from common.lichess_api import LichessAPI



class GameMode(ABC):

    def __init__(self, board: RobotBoard):
        self._board = board

    @abstractmethod
    def play_move(self, move):
        pass



class LichessAIGame(GameMode):

    def __init__(self, board: RobotBoard, lichess_api: LichessAPI, ai_strength: int = None, game_id: str = None):
        super().__init__(board=board)
        self._lichess_api = lichess_api

        if game_id is not None:
            lichess_api.attach_to_game(game_id=game_id)
            moves = lichess_api.get_move_stack()
            self._board.set_move_stack(moves)

        elif ai_strength is not None:
            lichess_api.start_ai_game(ai_strength=ai_strength)

        else:
            raise ValueError("Either an ai_strength or a game_id must be provided")

    def play_move(self, move: str):
        self._board.play_move(move)
        self._lichess_api.make_move(move)
        move = self._lichess_api.wait_for_opponent_move()
        self._board.play_move(move)



class Game:

    def __init__(self, mode: GameMode):
        self._mode = mode

    def play_move(self, move: str):
        return self._mode.play_move(move)


if __name__ == "__main__":
    CODE = "wQezHnM9gp9A"
    board = RobotBoard()
    api = LichessAPI()
    game_mode = LichessAIGame(lichess_api=api, board=board, game_id=CODE)
    game = Game(mode=game_mode)
    while True:
        game.play_move(input())