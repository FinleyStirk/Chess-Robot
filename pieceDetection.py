import serial
import time
import pygame

class Squares:
    lightSquareColour = (212, 187, 133)
    darkSquareColour = (130, 84, 47)
    active = (38, 235, 38)

    def __init__(self, xSize, ySize):
        self.xSize = xSize
        self.ySize = ySize

        self.defaultColours = [[] for _ in range(ySize)]
        self.colours = [[] for _ in range(ySize)]
        self.strengths = [[] for _ in range(ySize)]
        for y in range(ySize):
            for x in range(xSize):
                self.defaultColours[y].append(Squares.lightSquareColour if (x + y) % 2 == 0 else Squares.darkSquareColour)
                self.strengths[y].append(0)
                self.colours[y].append(0)
    
    def UpdateSquares(self, states):
        for y in range(ySize):
            for x in range(xSize):
                if states[(y*8)+ x] == "1":
                    self.strengths[y][x] = 1
                else:
                    if self.strengths[y][x] > 0:
                        self.strengths[y][x] -= decayFactor
                self.colours[y][x] = self.LerpColour(self.defaultColours[y][x], self.active, self.strengths[y][x])

    def LerpColour(self, colourOne, colourTwo, percentage):
        red = colourOne[0] + ((colourTwo[0]-colourOne[0]) * percentage)
        green = colourOne[1] + ((colourTwo[1]-colourOne[1]) * percentage)
        blue = colourOne[2] + ((colourTwo[2]-colourOne[2]) * percentage)
        return (red, green, blue)

def drawSquares():
    for y in range(ySize):
        for x in range(xSize):
            pygame.draw.rect(screen, squares.colours[y][x], (x*squareSize, y*squareSize, squareSize, squareSize))



ser = serial.Serial('com3', 9600)
time.sleep(2)
pygame.init()

# Control Variables #
# <---------------------------> #
squareSize = 500
xSize, ySize = 5, 1
decayFactor = 0.01
# <---------------------------> #
squares = Squares(xSize, ySize)
screen = pygame.display.set_mode((squareSize*xSize, squareSize*ySize))
running = True
while running:
    if ser.inWaiting() > 0:
        states = ser.readline().decode().strip()
        squares.UpdateSquares(states)
        drawSquares()
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False