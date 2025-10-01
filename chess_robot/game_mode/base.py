from abc import ABC, abstractmethod

from chess_robot.board import RobotBoard
from chess_robot.utils.structs import RobotCommand, CommandType



class GameMode(ABC):

    def __init__(self, board: RobotBoard):
        self._board = board

    def __repr__(self) -> str:
        return repr(self._board)
    
    def execute_command(self, command: RobotCommand):
        match command.command:
            case CommandType.MOVE:
                move = command.data
                self._board.play_move(move)
            case CommandType.UNDO:
                self._board.undo_move()
            case _:
                Exception("Unrecognised Command")

    @abstractmethod
    def player_move(self) -> None:
        pass

    @abstractmethod
    def opponent_move(self) -> None:
        pass







