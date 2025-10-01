from abc import ABC, abstractmethod

from chess_robot.utils.structs import Vector2



# Maybe add intermediary steps back in
class Gantry(ABC):

    STEP_PER_CM = 50
    SQUARE_LENGTH = 3

    def __init__(self, position: Vector2):
        self._position = position

    def calculate_motor_steps(self, target_position: Vector2) -> Vector2:
        # Would rather do this with Vectors
        board_distance = target_position - self._position

        cm_distance = Vector2(
            (board_distance.x + board_distance.y) * self.SQUARE_LENGTH,
            (board_distance.x - board_distance.y) * self.SQUARE_LENGTH
        )

        steps = cm_distance * self.STEP_PER_CM

        return steps
    
    @abstractmethod
    def home(self) -> None:
        pass
    
    @abstractmethod
    def run_path(self, path: list[list[Vector2]]) -> None:
        pass
    




