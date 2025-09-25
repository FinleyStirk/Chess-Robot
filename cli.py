from common.robot_board import RobotBoard
from common.gantry import VirtualGantry
from common.board_state import BoardState
from common.robot import Robot

gantry = VirtualGantry()
robot = Robot(gantry=gantry)

board_state = BoardState()
board = RobotBoard(board_state=board_state, robot=robot)

commands = iter([
    "play e2e4",
    "play d7d5",
    "play e4d5",
])

while True:
    print(board)
    # command = next(commands).split()
    command = input().split()
    match command[0].lower():
        case "play":
            move = command[1]
            board.play_move(move)
        # case "undo":
        #     board.undo_move()
        # case "reset":
        #     board.reset()
        # case "set":
        #     fen = command[1]
        #     board.set_fen(fen)
        case _:
            continue
    