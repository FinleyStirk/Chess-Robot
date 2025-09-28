from .base import Gantry
from utils.structs import Vector2, GantryCommand

class VirtualGantry(Gantry):

    def __init__(self, position: Vector2 = Vector2(0,0)):
        super().__init__(position)

    def run_path(self, path: list[GantryCommand]):
        for step in path:
            self._position = step.position
            print(step)

    def home(self):
        self._position = Vector2(0, 0)