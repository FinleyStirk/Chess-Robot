from .base import GameMode

class TwoPlayerCommandLine(GameMode):

    def player_move(self):
        move = input()
        self._board.play_move(move)

    def opponent_move(self):
        self.player_move()