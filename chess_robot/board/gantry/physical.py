import serial
import time

from .base import Gantry
from utils.structs import Vector2, GantryCommand


class PhysicalGantry(Gantry):

    def __init__(self, port: str, baudrate: int, position: Vector2 = Vector2(0, 0), setup_time: float = 1):
        super().__init__(position)
        self._ser = serial.Serial(port, baudrate)
        time.sleep(setup_time)

    def run_path(self, path: list[GantryCommand]):
        for step in path:
            motor_steps = self.calculate_motor_steps(step.x, step.y)
            self.run_motors(motor_steps, step.magnet_state)
            self._position = step.position

    def run_motors(self, steps: Vector2, magnet_state: int, blocking: bool = True, max_wait_time: float = float('inf')):
        # Implement some kind of response protocol to robot
        dataStr = f"{steps.x},{steps.y},{magnet_state}\n"

        self._ser.write(dataStr.encode())

        start_time = time.time()
        while blocking:
            if self._ser.in_waiting > 0:
                received_data = self._ser.readline().decode().strip()
                return received_data
            
            if time.time() - start_time > max_wait_time:
                raise Exception(f"Unable to complete movement in time")
    
    def home(self):
        self.run_motors(Vector2(0, 0), magnet_state=-1)
        self._position = Vector2(0, 0)


