import serial

from .base import Input
from chess_robot.utils.structs import RobotCommand, Vector2

class PhysicalBoard(Input):

    def __init__(self, ser: serial.Serial):
        self._ser = ser
    
    def get_command(self) -> RobotCommand:
        pass