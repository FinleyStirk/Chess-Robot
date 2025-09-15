# Libraries #
# <---------------------------> #
import chess
import chess.engine
# <---------------------------> #

# Other Files #
# <---------------------------> #
from common.structs import Vector2, PieceStorage
from common.gantry import RunPath
from common.pathCalculator import IndirectPath, DirectPath, CastlePath, KnightPath
# <---------------------------> #

# Functions #
# <---------------------------> #

class RobotBoard:
    def __init__(self, engine_path: str = None):
        self._board = chess.Board()

        self._storage = PieceStorage()

        if engine_path is not None:
            self._engine = chess.engine.SimpleEngine.popen_uci(engine_path)

    @staticmethod
    def _get_components(index : int):
        return Vector2(index % 8, index // 8)

    @staticmethod
    def _get_square_name(index : int):
            files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

            position = RobotBoard._get_components(index)

            return files[position.x] + ranks[position.y]

    def _piece_positions(self):
        piecePositions = self._storage.get_filled_storage()
        for square in range(64):
            nextPiece = str(self._board.piece_at(square))
            if nextPiece != "None":
                piecePositions.append(RobotBoard._get_components(square))
        return piecePositions

    def EngineMove(self):
        return self._engine.play(self._board, chess.engine.Limit(time=0.5)).move

    def play_move(self, uci):
        move = self._board.parse_uci(uci)

        targetSquare = RobotBoard._get_components(move.to_square)
        originSquare = RobotBoard._get_components(move.from_square)
        movingPiece = self._board.piece_at(move.from_square)
        capturedPiece = str(self._board.piece_at(move.to_square))

        path = []
        if self._board.is_capture(move):
            offBoardSquare = self._storage.add_to_storage(capturedPiece)
            path += IndirectPath(targetSquare, offBoardSquare, self._piece_positions())
        if movingPiece.piece_type == chess.KNIGHT:
            path += KnightPath(originSquare, targetSquare)
        elif self._board.is_castling(move):
            path += CastlePath(self._board, move)
        else:
            path += DirectPath(originSquare, targetSquare)
        self._board.push(move)
        print(f"|<          Move {(self._board.ply()+1 // 2)} {'Black' if self._board.turn else 'White'}: {move.uci()}          >|")
        RunPath(path)

    def undo_move(self):
        if not self._board.move_stack:
            raise Exception('No moves to undo')
        print(f"|<          Undoing Move {(self._board.ply()+1 // 2)}         >|")
        move = self._board.pop()
        targetSquare = RobotBoard._get_components(move.to_square)
        originSquare = RobotBoard._get_components(move.from_square)
        movingPiece = self._board.piece_at(move.from_square)
        
        path = []
        if movingPiece.piece_type == chess.KNIGHT:
            path += KnightPath(targetSquare, originSquare)
        elif self._board.is_castling(move):
            path += CastlePath(self._board, move, reverse=True)
        else:
            path += DirectPath(targetSquare, originSquare)
        if self._board.is_capture(move):
            capturedPiece = str(self._board.piece_at(move.to_square))
            offBoardSquare = self._storage.remove_from_storage(capturedPiece)
            path += IndirectPath(offBoardSquare, targetSquare, self._piece_positions())

        RunPath(path)

    def set_fen(self, FENstring : str):
        fen_components = FENstring.split()
        pieces = fen_components[0]
        y, x = 7, 0
        targetPositions = {
            "r": [],
            "n": [],
            "b": [],
            "k": [],
            "q": [],
            "p": [],
            "R": [],
            "N": [],
            "B": [],
            "K": [],
            "Q": [],
            "P": [],
        }
        currentPositions = {
            "r": [],
            "n": [],
            "b": [],
            "k": [],
            "q": [],
            "p": [],
            "R": [],
            "N": [],
            "B": [],
            "K": [],
            "Q": [],
            "P": [],
        }
        for piece in pieces:
            if piece == "/":
                y -= 1
                x = 0
            elif piece.isdigit():
                x += int(piece)
            else:
                targetPositions[piece].append(Vector2(x, y))
                x += 1
        for square in range(64):
            nextPiece = str(self._board.piece_at(square))
            if nextPiece != "None":
                currentPositions[nextPiece].append(RobotBoard._get_components(square))
        # Check what pieces are already in the correct Locations
        for piece in targetPositions:
            for square in targetPositions[piece]:
                if square in currentPositions[piece]:
                    targetPositions[piece].remove(square)
                    currentPositions[piece].remove(square)
        # Remove Excess Pieces
        path  = []
        for piece in targetPositions:
            while len(targetPositions[piece]) < len(currentPositions[piece]):
                fromSquare = currentPositions[piece].pop()
                toSquare = self._storage.add_to_storage(piece)
                path += IndirectPath(fromSquare, toSquare, self._piece_positions())
                self._board.remove_piece_at(chess.square(fromSquare.x, fromSquare.y))
        finished = False
        # Repeat until All pieces moved to target
        while not finished:
            finished = True
            for piece in targetPositions:
                for square in targetPositions[piece]:
                    squareEmpty = True
                    for positions in currentPositions.values():
                        if square in positions:
                            squareEmpty = False
                            break
                    if squareEmpty:
                        if len(currentPositions[piece]) > 0:
                            fromSquare = currentPositions[piece].pop()
                            # Check if move is possible
                            try:
                                path += IndirectPath(fromSquare, square, self._piece_positions())
                                targetPositions[piece].remove(square)
                                self._board.remove_piece_at(chess.square(fromSquare.x, fromSquare.y))
                                self._board.set_piece_at(chess.square(square.x, square.y), chess.Piece.from_symbol(piece))
                            except Exception:
                                currentPositions[piece].append(fromSquare)
                                print(f"{piece} : {fromSquare} --> {square} Not Possible")
                        else:
                            fromSquare = self._storage.remove_from_storage(piece)
                            try:
                                path += IndirectPath(fromSquare, square, self._piece_positions())
                                targetPositions[piece].remove(square)
                                self._board.set_piece_at(chess.square(square.x, square.y), chess.Piece.from_symbol(piece))
                            except Exception:
                                self._storage.add_to_storage(piece)
                                print(f"{piece} : {fromSquare} --> {square} Not Possible")
                        finished = False
        print(f"|<          Setting Up Board to {pieces}          >|")
        RunPath(path)
        self._board.set_board_fen(pieces)

    def reset(self):
        self.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self._board.reset()

    def skip_turn(self):
        self._board.push(chess.Move.null())

    def _piece_at(self, position: Vector2):
        index = position.x + position.y * 8
        if position.x in range(8) and position.y in range(8):
            piece = self._board.piece_at(index)
            if type(piece) is chess.Piece:
                return piece.symbol()
        else:
            return self._storage.piece_at(position)
        
    def __repr__(self):
        rows = []
        for y in range(7, -1, -1):
            row = []
            for x in range(-3, 11):
                row.append(self._piece_at(Vector2(x, y)) or ".")
            rows.append(" ".join(row))
        return "\n".join(rows)
# <---------------------------> #
