from .base import Input
from chess_robot.utils.structs import RobotCommand

class CommandLine(Input):
    
    def get_command(self) -> RobotCommand:
        raw_input = input("Enter a move: ")
        formatted_input = raw_input.split()
        match formatted_input[0].lower():
            case "play":
                command = RobotCommand.move(formatted_input[1])
            case "undo":
                command = RobotCommand.undo()
            case _:
                raise Exception("Invalid Command")

        return command