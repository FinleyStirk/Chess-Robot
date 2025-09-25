import pygame
import common.gantry as gantry
from common.structs import GantryCommand



def drawSquares():
    screen.fill((0, 0, 0))
    for y in range(Y_SIZE):
        for x in range(X_SIZE):
            if x in BLANK_FILES or y in BLANK_ROWS:
                continue
            colour = LIGHT_SQUARE_COLOUR if (x + y) % 2 == 0 else DARK_SQUARE_COLOUR
            pygame.draw.rect(screen, colour, (x*squareSize, y*squareSize, squareSize, squareSize))



pygame.init()

# Control Variables #
# <---------------------------> #
squareSize = 50
X_SIZE, Y_SIZE = 14, 10
decayFactor = 0.01
LIGHT_SQUARE_COLOUR = (212, 187, 133)
DARK_SQUARE_COLOUR = (130, 84, 47)

BLANK_FILES = (2, 11)
BLANK_ROWS = (0, 9)
# <---------------------------> #

screen = pygame.display.set_mode((squareSize*X_SIZE, squareSize*Y_SIZE))
running = True
emState = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONUP:
            x, y = pygame.mouse.get_pos()
            squareFile = (x // squareSize) - 3
            squareRank = 8 - (y // squareSize)
            gantry.RunPath([GantryCommand(squareFile, squareRank, emState)])
        if event.type == pygame.KEYUP:
            emState = int(not emState)
            print(f"CHANGING EM STATE TO {emState}")
    # gantry.start_transmitting()
    drawSquares()
    pygame.display.update()
    