from .base import GameMode
from chess_robot.board.robot_board import RobotBoard
from chess_robot.input_method import Input


class TwoPlayerLocal(GameMode):

    def __init__(self, board: RobotBoard, player_input: Input, opponent_input: Input):
        super().__init__(board)
        self._player_input = player_input
        self._opponent_input = opponent_input

    def player_move(self) -> None:
        command = self._player_input.get_command()
        self.execute_command(command)
        

    def opponent_move(self) -> None:
        command = self._opponent_input.get_command()
        self.execute_command(command)

    