import pygame

from .base import Gantry
from utils.structs import Vector2, GantryCommand


class GraphicalGantry(Gantry):

    SQUARE_SIZE = 50
    X_SIZE, Y_SIZE = 14, 10
    LIGHT_SQUARE_COLOUR = (212, 187, 133)
    DARK_SQUARE_COLOUR = (130, 84, 47)

    GANTRY_PADDING = 5
    SPEED = 3
    ACTIVE_COLOUR = (0, 153, 51)
    INACTIVE_COLOUR = (0, 102, 255)

    BLANK_FILES = (2, 11)
    BLANK_ROWS = (0, 9)

    def __init__(self, position: Vector2 = Vector2(0,0)):
        super().__init__(position)
        pygame.init()

        self.screen = pygame.display.set_mode((
            self.SQUARE_SIZE*self.X_SIZE, 
            self.SQUARE_SIZE*self.Y_SIZE
        ))

    def run_path(self, path: list[GantryCommand]):
        num_steps = 50
        for step in path:
            distance = Vector2.distance(step.position, self._position)
            time = distance / self.SPEED
            for i in range(num_steps):
                t = i / num_steps
                pygame.event.get()
                self.draw_squares()
                self.draw_gantry(
                    Vector2.lerp(self._position, step.position, t),
                    self.ACTIVE_COLOUR if step.magnet_state == 1 else self.INACTIVE_COLOUR
                )
                pygame.display.update()
                pygame.time.wait(int(1000*time/num_steps))

            self._position = step.position
        pygame.time.wait(500)

    def draw_squares(self):
        self.screen.fill((0, 0, 0))
        for y in range(self.Y_SIZE):
            for x in range(self.X_SIZE):
                if x in self.BLANK_FILES or y in self.BLANK_ROWS:
                    continue

                colour = self.LIGHT_SQUARE_COLOUR if (x + y) % 2 == 0 else self.DARK_SQUARE_COLOUR

                pygame.draw.rect(
                    surface=self.screen, 
                    color=colour,
                    rect=(
                        x*self.SQUARE_SIZE, 
                        y*self.SQUARE_SIZE, 
                        self.SQUARE_SIZE, 
                        self.SQUARE_SIZE
                    )
                )

    def draw_gantry(self, draw_position: Vector2, colour: tuple[int, int, int]):
        x = draw_position.x + 3
        y = self.Y_SIZE - draw_position.y - 2
        pygame.draw.rect(
            surface=self.screen, 
            color=colour,
            rect=(
                x*self.SQUARE_SIZE + self.GANTRY_PADDING, 
                y*self.SQUARE_SIZE + self.GANTRY_PADDING, 
                self.SQUARE_SIZE - 2 * self.GANTRY_PADDING, 
                self.SQUARE_SIZE - 2 * self.GANTRY_PADDING
            )
        )

    def home(self):
        self.run_path([GantryCommand(0, 0, -1)])