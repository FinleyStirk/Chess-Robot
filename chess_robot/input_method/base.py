from abc import ABC, abstractmethod

from chess_robot.utils.structs import RobotCommand

class Input(ABC):

    @abstractmethod
    def get_command(self) -> RobotCommand:
        pass