from . import *

gantry = VirtualGantry()
robot = Robot(gantry=gantry)

board_state = BoardState()
robot_board = RobotBoard(board_state=board_state, robot=robot)

player = input_method.CommandLine()
opponent = input_method.CommandLine()
game = TwoPlayerLocal(
    board=robot_board, 
    player_input=player, 
    opponent_input=opponent
)
# game = LoadGame(robot_board, "chess_robot/games/Bobby Fischer vs Boris Spassky.pgn")

while True:
    print(game)
    game.player_move()
    print(game)
    game.opponent_move()
    