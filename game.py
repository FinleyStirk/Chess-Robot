# Libraries #
# <---------------------------> #
import chess
import chess.engine
import asyncio
from sys import platform
# <---------------------------> #

# Other Files #
# <---------------------------> #
from structs import Coord, Vector2, Storage, Stack
from gantry import RunPath
from pathCalculator import OffBoardPath, IndirectPath, DirectPath, CastlePath
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
def UpdatePiecePositions():
        global piecePositions
        piecePositions = []
        for pieceStorage in storage.values():
            for square in pieceStorage.filledStorage:
                 piecePositions.append(square)
        for square in range(64):
            nextPiece = str(board.piece_at(square))
            if nextPiece != "None":
                piecePositions.append(GetComponents(square))
async def EngineMove():
    await PlayMove(engine.play(board, chess.engine.Limit(time=0.5)).move)
def UndoMove():
    print(f"\n|<          Undoing Move {(board.ply()+1 // 2)}         >|")
    move = board.pop()
    if board.is_capture(move):
        piece = str(board.piece_at(move.from_square))
        storage[piece].EmptyStorage()

    UpdatePiecePositions()
async def PlayMove(move: chess.Move):
    targetSquare = GetComponents(move.to_square)
    originSquare = GetComponents(move.from_square)
    movingPiece = board.piece_at(move.from_square)
    capturedPiece = str(board.piece_at(move.to_square))

    path = []
    if board.is_capture(move):
         offBoardSquare = storage[capturedPiece].FillStorage()
         path += OffBoardPath(targetSquare, offBoardSquare, piecePositions)
    if movingPiece.piece_type == chess.KNIGHT:
        path += IndirectPath(originSquare, targetSquare)
    elif board.is_castling(move):
        path += CastlePath(board, move)
    else:
        path += DirectPath(originSquare, targetSquare)
    board.push(move)
    UpdatePiecePositions()
    print(f"\n|<          Move {(board.ply()+1 // 2)} {'Black' if board.turn else 'White'}: {move.uci()}          >|")
    await RunPath(path)
    return True
# <---------------------------> #

# Objects #
# <---------------------------> #
global board
board = chess.Board()
match (platform ):
    case "darwin":
        engine = chess.engine.SimpleEngine.popen_uci("stockfish 2/stockfish-macos-m1-apple-silicon")
    case "win32":
        raise "I forgot about the windows Stockfish :("
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