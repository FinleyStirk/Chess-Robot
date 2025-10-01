import serial
import time

from .base import Gantry
from chess_robot.utils.structs import Vector2


class PhysicalGantry(Gantry):

    def __init__(self, ser: serial.Serial, position: Vector2 = Vector2(0, 0)):
        super().__init__(position)
        self._ser = ser

    def run_path(self, path: list[list[Vector2]]) -> None:
        for segment in path:
            for index, step in segment:
                motor_steps = self.calculate_motor_steps(step)
                self.run_motors(steps=motor_steps, magnet_state=bool(index))
                self._position = step

    def run_motors(self, steps: Vector2, magnet_state: int, blocking: bool = True, max_wait_time: float = float('inf')) -> None:
        dataStr = f"{steps.x},{steps.y},{magnet_state}\n"

        self._ser.write(dataStr.encode())
        if blocking:
            self.await_arrival(max_wait_time)

        
    # Implement some kind of response protocol to robot
    def await_arrival(self, max_wait_time: float = float('inf')) -> str:
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            if self._ser.in_waiting > 0:
                received_data = self._ser.readline().decode().strip()
                return received_data
        raise Exception(f"Unable to complete movement in time")
    
    def home(self) -> None:
        self.run_motors(Vector2(0, 0), magnet_state=-1)
        self._position = Vector2(0, 0)


