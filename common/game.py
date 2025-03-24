# Libraries #
# <---------------------------> #
import chess
import chess.engine
from sys import platform
# <---------------------------> #

# Other Files #
# <---------------------------> #
from common.structs import Vector2, Storage
from common.gantry import RunPath
from common.pathCalculator import IndirectPath, DirectPath, CastlePath, KnightPath
# <---------------------------> #

# Functions #
# <---------------------------> #
def GetComponents(index : int):
    return Vector2(index % 8, index // 8)
def GetSquareName(index : int):
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

        position = GetComponents(index)

        return files[position.x] + ranks[position.y]
def PiecePositions():
    piecePositions = []
    for pieceStorage in storage.values():
        for square in pieceStorage.filledStorage:
                piecePositions.append(square)
    for square in range(64):
        nextPiece = str(board.piece_at(square))
        if nextPiece != "None":
            piecePositions.append(GetComponents(square))
    return piecePositions
def EngineMove():
    return engine.play(board, chess.engine.Limit(time=0.5)).move
def PlayLastMove():
    move = board.pop()
    targetSquare = GetComponents(move.to_square)
    originSquare = GetComponents(move.from_square)
    movingPiece = board.piece_at(move.from_square)
    capturedPiece = str(board.piece_at(move.to_square))

    path = []
    if board.is_capture(move):
         offBoardSquare = storage[capturedPiece].AddToStorage()
         path += IndirectPath(targetSquare, offBoardSquare, PiecePositions())
    if movingPiece.piece_type == chess.KNIGHT:
        path += KnightPath(originSquare, targetSquare)
    elif board.is_castling(move):
        path += CastlePath(board, move)
    else:
        path += DirectPath(originSquare, targetSquare)
    board.push(move)
    print(f"\n|<          Move {(board.ply()+1 // 2)} {'Black' if board.turn else 'White'}: {move.uci()}          >|")
    RunPath(path)
    return True
def PlayMove(uci):
    board.push_uci(uci)
    PlayLastMove()
def UndoMove():
    print(f"\n|<          Undoing Move {(board.ply()+1 // 2)}         >|")
    move = board.pop()
    targetSquare = GetComponents(move.to_square)
    originSquare = GetComponents(move.from_square)
    movingPiece = board.piece_at(move.from_square)
    
    path = []
    if movingPiece.piece_type == chess.KNIGHT:
        path += KnightPath(targetSquare, originSquare)
    elif board.is_castling(move):
        path += CastlePath(board, move, reverse=True)
    else:
        path += DirectPath(targetSquare, originSquare)
    if board.is_capture(move):
        capturedPiece = str(board.piece_at(move.to_square))
        offBoardSquare = storage[capturedPiece].RemoveFromStorage()
        path += IndirectPath(offBoardSquare, targetSquare, PiecePositions())

    RunPath(path)
def SetFEN(FENstring : str):
    pieces = FENstring.split()[0]
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
        nextPiece = str(board.piece_at(square))
        if nextPiece != "None":
            currentPositions[nextPiece].append(GetComponents(square))
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
            toSquare = storage[piece].AddToStorage()
            path += IndirectPath(fromSquare, toSquare, PiecePositions())
            board.remove_piece_at(chess.square(fromSquare.x, fromSquare.y))
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
                            path += IndirectPath(fromSquare, square, PiecePositions())
                            targetPositions[piece].remove(square)
                            board.remove_piece_at(chess.square(fromSquare.x, fromSquare.y))
                            board.set_piece_at(chess.square(square.x, square.y), chess.Piece.from_symbol(piece))
                        except Exception:
                            currentPositions[piece].append(fromSquare)
                            print(f"{piece} : {fromSquare} --> {square} Not Possible")
                    else:
                        fromSquare = storage[piece].RemoveFromStorage()
                        try:
                            path += IndirectPath(fromSquare, square, PiecePositions())
                            targetPositions[piece].remove(square)
                            board.set_piece_at(chess.square(square.x, square.y), chess.Piece.from_symbol(piece))
                        except Exception:
                            storage[piece].AddToStorage()
                            print(f"{piece} : {fromSquare} --> {square} Not Possible")
                    finished = False
    print(f"\n|<          Setting Up Board to {pieces}          >|")
    RunPath(path)
    board.set_board_fen(pieces)
def reset():
    SetFEN("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    board.reset()
# <---------------------------> #

# Objects #
# <---------------------------> #
global board
board = chess.Board()
match (platform ):
    case "darwin":
        engine = chess.engine.SimpleEngine.popen_uci('common/stockfish/stockfishMac/stockfish-macos-m1-apple-silicon')
    case "win32":
        engine = chess.engine.SimpleEngine.popen_uci('common/stockfish/stockfishWindows/stockfish-windows-x86-64-avx2.exe')
    case _:
        raise "Incompatable OS"
storage = {
    "r" : Storage([Vector2(-3,0), Vector2(-3, 7)]),
    "n" : Storage([Vector2(-3,1), Vector2(-3, 6)]),
    "b" : Storage([Vector2(-3,2), Vector2(-3, 5)]),
    "q" : Storage([Vector2(-3,3)], [Vector2(-3, 4)]),
    "p" : Storage([Vector2(-2,0), Vector2(-2,1), Vector2(-2,2), Vector2(-2,3), Vector2(-2,4), Vector2(-2,5), Vector2(-2,6), Vector2(-2,7)]),
    "R" : Storage([Vector2(10,0), Vector2(10,7)]),
    "N" : Storage([Vector2(10,1), Vector2(10,6)]),
    "B" : Storage([Vector2(10,2), Vector2(10,5)]),
    "Q" : Storage([Vector2(10,3)], [Vector2(10,4)]),
    "P" : Storage([Vector2(9,0), Vector2(9,1), Vector2(9,2), Vector2(9,3), Vector2(9,4), Vector2(9,5), Vector2(9,6), Vector2(9,7)]),
}
# <---------------------------> #