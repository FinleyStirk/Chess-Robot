from common.game import RobotBoard

board = RobotBoard()
while True:
    print(board)
    move = input()
    board.play_move(move)