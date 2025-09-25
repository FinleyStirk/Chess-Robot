import serial
import time
from common.structs import GantryCommand, Vector2
from abc import ABC, abstractmethod


# Maybe add intermediary steps back in
class Gantry(ABC):

    CM_PER_STEP = 0.02
    SQUARE_LENGTH = 3

    def __init__(self, position: Vector2):
        self.position = position

    def calculate_motor_steps(self, target_x: float, target_y: float):
        # Would rather do this with Vectors
        board_distance_x = target_x - self.position.x
        board_distance_y = target_y - self.position.y

        cm_distance_x = (board_distance_x + board_distance_y) * self.SQUARE_LENGTH
        cm_distance_y = (board_distance_x - board_distance_y) * self.SQUARE_LENGTH

        x_steps = int(cm_distance_x / self.CM_PER_STEP)
        y_steps = int(cm_distance_y / self.CM_PER_STEP)

        self.position = Vector2(target_x, target_y)

        return Vector2(x_steps, y_steps)
    
    @abstractmethod
    def home(self):
        pass
    
    @abstractmethod
    def run_path(self, path: list[GantryCommand]):
        pass
    

class VirtualGantry(Gantry):
    # Create a better visualisation

    def __init__(self, position: Vector2 = Vector2(0,0)):
        super().__init__(position)

    def run_path(self, path: list[GantryCommand]):
        # step feels like the wrong name
        for step in path:
            print(step)

    def home(self):
        self.position = Vector2(0, 0)



class PhysicalGantry(Gantry):

    def __init__(self, port: str, baudrate: int, position: Vector2 = Vector2(0, 0), setup_time: float = 1):
        super().__init__(position)
        self.ser = serial.Serial(port, baudrate)
        time.sleep(setup_time)

    def run_path(self, path: list[GantryCommand]):
        for step in path:
            motor_steps = self.calculate_motor_steps(step.x, step.y)

    def run_motors(self, steps: Vector2, magnet_state: int, blocking: bool = True, max_wait_time: float = float('inf')):
        # Implement some kind of response protocol to robot
        dataStr = f"{steps.x},{steps.y},{magnet_state}\n"

        self.ser.write(dataStr.encode())

        start_time = time.time()
        while blocking:
            if self.ser.in_waiting > 0:
                received_data = self.ser.readline().decode().strip()
                return received_data
            
            if time.time() - start_time > max_wait_time:
                raise Exception(f"Unable to complete movement in time")
    
    def home(self):
        self.run_motors(Vector2(0, 0), magnet_state=-1)
        self.position = Vector2(0, 0)


