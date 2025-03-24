# Libraries #
# <---------------------------> #
import serial
import time
# <---------------------------> #

# Other Files #
# <---------------------------> #
from common.pathCalculator import SmoothPath
from common.structs import Coord, Vector2
# <---------------------------> #

# Functions #
# <---------------------------> #
def CalculateNextInstruction(xCoord, yCoord):
    global positionX
    global positionY

    xDist = xCoord - positionX
    yDist = yCoord - positionY

    xDistCm = (xDist + yDist) * SquareLength
    yDistCm = (xDist - yDist) * SquareLength

    xSteps = int(xDistCm / CmPerStep)
    ySteps = int(yDistCm / CmPerStep)

    positionX = xCoord
    positionY = yCoord

    return xSteps, ySteps
def RunMotors(motorOneSteps, motorTwoSteps, emState=0):
    dataStr = f"{motorOneSteps},{motorTwoSteps},{emState}\n"
    if transmitting:
        ser.write(dataStr.encode())
        WaitForArrival()
def WaitForArrival():
    while True:
        if ser.inWaiting() > 0:
            recvData = ser.readline().decode().strip()
            return recvData
def RunPath(coords : list[Coord]):
    for coord in coords:
        intermediaryStep = SmoothPath(Vector2(positionX, positionY), Vector2(coord.x, coord.y))
        if intermediaryStep:
            stepOne, stepTwo = CalculateNextInstruction(intermediaryStep.x, intermediaryStep.y)

            RunMotors(stepOne, stepTwo, coord.emState)
            print(Coord(intermediaryStep.x, intermediaryStep.y, coord.emState))
        stepOne, stepTwo = CalculateNextInstruction(coord.x, coord.y)
        print(coord)
        RunMotors(stepOne, stepTwo, coord.emState)
def StartTransmitting():
    global transmitting
    global ser
    transmitting = True
    ser = serial.Serial('com5', 9600)
    time.sleep(2)
def EndTransmitting():
    global transmitting
    transmitting = False
    ser.close()
def Home():
    RunMotors(0, 0, -1)
    global positionX, positionY
    positionX = 0
    positionY = 0
# <---------------------------> #

# Gantry Settings #
# <---------------------------> #
transmitting = False
CmPerStep = 0.02
SquareLength = 3
# <---------------------------> #

# Internal Variables #
# <---------------------------> #
positionX, positionY = 0, 0
if transmitting:
    StartTransmitting()
# <---------------------------> #