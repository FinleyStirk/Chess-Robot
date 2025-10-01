from .base import Gantry
from chess_robot.utils.structs import Vector2

class VirtualGantry(Gantry):

    def __init__(self, position: Vector2 = Vector2(0,0)):
        super().__init__(position)

    def run_path(self, path: list[list[Vector2]]) -> None:
        for segment in path:
            print(segment)
            for step in segment:
                self._position = step
            

    def home(self) -> None:
        self._position = Vector2(0, 0)