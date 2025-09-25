import chess
import chess.engine
from common.structs import Vector2, PieceStorage, MoveInfo
from common.robot import Robot
from common.board_state import BoardState

# Functions #
# <---------------------------> #
#     def set_fen(self, FENstring : str):
#         fen_components = FENstring.split()
#         pieces = fen_components[0]
#         y, x = 7, 0
#         targetPositions = {
#             "r": [],
#             "n": [],
#             "b": [],
#             "k": [],
#             "q": [],
#             "p": [],
#             "R": [],
#             "N": [],
#             "B": [],
#             "K": [],
#             "Q": [],
#             "P": [],
#         }
#         currentPositions = {
#             "r": [],
#             "n": [],
#             "b": [],
#             "k": [],
#             "q": [],
#             "p": [],
#             "R": [],
#             "N": [],
#             "B": [],
#             "K": [],
#             "Q": [],
#             "P": [],
#         }
#         for piece in pieces:
#             if piece == "/":
#                 y -= 1
#                 x = 0
#             elif piece.isdigit():
#                 x += int(piece)
#             else:
#                 targetPositions[piece].append(Vector2(x, y))
#                 x += 1
#         for square in range(64):
#             nextPiece = str(self._board.piece_at(square))
#             if nextPiece != "None":
#                 currentPositions[nextPiece].append(RobotBoard._get_components(square))
#         # Check what pieces are already in the correct Locations
#         for piece in targetPositions:
#             for square in targetPositions[piece]:
#                 if square in currentPositions[piece]:
#                     targetPositions[piece].remove(square)
#                     currentPositions[piece].remove(square)
#         # Remove Excess Pieces
#         path  = []
#         for piece in targetPositions:
#             while len(targetPositions[piece]) < len(currentPositions[piece]):
#                 fromSquare = currentPositions[piece].pop()
#                 toSquare = self._storage.add(piece)
#                 path += IndirectPath(fromSquare, toSquare, self._piece_positions())
#                 self._board.remove_piece_at(chess.square(fromSquare.x, fromSquare.y))
#         finished = False
#         # Repeat until All pieces moved to target
#         while not finished:
#             finished = True
#             for piece in targetPositions:
#                 for square in targetPositions[piece]:
#                     squareEmpty = True
#                     for positions in currentPositions.values():
#                         if square in positions:
#                             squareEmpty = False
#                             break
#                     if squareEmpty:
#                         if len(currentPositions[piece]) > 0:
#                             fromSquare = currentPositions[piece].pop()
#                             # Check if move is possible
#                             try:
#                                 path += IndirectPath(fromSquare, square, self._piece_positions())
#                                 targetPositions[piece].remove(square)
#                                 self._board.remove_piece_at(chess.square(fromSquare.x, fromSquare.y))
#                                 self._board.set_piece_at(chess.square(square.x, square.y), chess.Piece.from_symbol(piece))
#                             except Exception:
#                                 currentPositions[piece].append(fromSquare)
#                                 print(f"{piece} : {fromSquare} --> {square} Not Possible")
#                         else:
#                             fromSquare = self._storage.remove(piece)
#                             try:
#                                 path += IndirectPath(fromSquare, square, self._piece_positions())
#                                 targetPositions[piece].remove(square)
#                                 self._board.set_piece_at(chess.square(square.x, square.y), chess.Piece.from_symbol(piece))
#                             except Exception:
#                                 self._storage.add(piece)
#                                 print(f"{piece} : {fromSquare} --> {square} Not Possible")
#                         finished = False
#         print(f"|<          Setting Up Board to {pieces}          >|")
#         RunPath(path)
#         self._board.set_board_fen(pieces)

# <---------------------------> #


class RobotBoard:
    def __init__(self, board_state: BoardState, robot: Robot):
        self._board_state = board_state
        self._robot = robot

    def play_move(self, move_uci: str):
        move = self._board_state.parse_move(move_uci=move_uci)
        self._board_state.play_move(move)
        self._robot.play_move(move)

    def reset(self):
        self.set_fen_string("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def set_fen_string(self, fen_string: str):
        pass

    def undo_move(self):
        pass

    def engine_move(self):
        pass
    
    def __repr__(self):
        return repr(self._board_state)

