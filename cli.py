from chess_robot import Robot, VirtualGantry, RobotBoard, BoardState, LoadGame

gantry = VirtualGantry()
robot = Robot(gantry=gantry)

board_state = BoardState()
board = RobotBoard(board_state=board_state, robot=robot)

# game_mode = TwoPlayerCommandLine(board)
game_mode = LoadGame(board, "games/Bobby Fischer vs Boris Spassky.pgn")

while True:
    print(game_mode)
    game_mode.player_move()
    print(game_mode)
    game_mode.opponent_move()
    