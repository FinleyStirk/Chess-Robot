from abc import ABC, abstractmethod
from board import RobotBoard



class GameMode(ABC):

    def __init__(self, board: RobotBoard):
        self._board = board

    def __repr__(self):
        return self._board.__repr__()

    @abstractmethod
    def player_move(self):
        pass

    @abstractmethod
    def opponent_move(self):
        pass







