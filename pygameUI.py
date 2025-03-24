# Libraries #
# <---------------------------> #
import pygame
import os
import chess
import random
import tkinter as tk
from chess.pgn import read_game
# <---------------------------> #

# Other Files #
# <---------------------------> #
import common.gantry as gantry
from common.game import *
# <---------------------------> #

# UI Functions #
# <---------------------------> #
def UISelection():
    # Window Setup
    global window
    window = tk.Tk()
    window.title("Chess Robot")
    window.iconbitmap('static/PieceImages/blackKnight.ico')
    window.resizable(False, False)
    # Game Modes
    tk.Label(text="Game Modes").grid()
    tk.Button(window, text="Two Player Digital", command=lambda: SetGameMode("TwoPlayerDigital"), width=20).grid(row=1, padx=5)
    tk.Button(window, text="One Player Digital", command=lambda: SetGameMode("OnePlayerDigital"), width=20).grid(row=1, column=1, padx=5)
    tk.Button(window, text="Two Computer Players", command=lambda: SetGameMode("TwoComputerPlayers"), width=20).grid(row=1, column=2, padx=5)
    tk.Label(text="Engine Strength").grid(row=2)
    global engineStrength
    engineStrength = tk.IntVar()
    engineStrength.set(1500)
    tk.Scale(window, variable=engineStrength, from_=1350, to=2850, length=410, orient=tk.HORIZONTAL).grid(row=2, column=1, columnspan=2)
    # Puzzles
    tk.Button(window, text="Puzzle", command=lambda: SetGameMode("Puzzle"), width=20).grid(row=3, padx=5)
    global easiest, hardest
    minRange = 50
    easiest, hardest = tk.IntVar(), tk.IntVar()
    easiest.set(1500)
    hardest.set(1600)
    limitLowerBound = lambda low: easiest.set(hardest.get() - minRange) if int(low) > hardest.get() - minRange else None
    limitUpperBound = lambda high: hardest.set(easiest.get() + minRange) if int(high) < easiest.get() + minRange else None
    tk.Scale(window, variable=easiest, from_=400, to=3000, length=190, orient=tk.HORIZONTAL, command=limitLowerBound).grid(row=3, column=1, padx=5)
    tk.Scale(window, variable=hardest, from_=400, to=3000, length=190, orient=tk.HORIZONTAL, command=limitUpperBound).grid(row=3, column=2, padx=5)
    # Pro Games
    tk.Label(text="Pro Games").grid(row=4)
    for index, gameName in enumerate(os.listdir("Games")):
        tk.Button(window, text=gameName[:-4], width=30, command=lambda: SetGameMode("WatchFamousGame", index)).grid(row=(index % 3)+5, column=index//3)
    # Testing Options
    tk.Label(text="Testing Options").grid(row=8)
    global transmitting
    transmitting = tk.BooleanVar(value=False)
    tk.Checkbutton(window, text="Transmitting", variable=transmitting, onvalue=True, offvalue=False).grid(row=9)
    window.mainloop()
def SetGameMode(gameMode, arguements=None):
    # TKinter Variables
    gantry.transmitting = transmitting.get()
    if transmitting.get():
        gantry.StartTransmitting()
    engine.configure({"UCI_Elo": engineStrength.get()})
    window.destroy()
    # Pygame setup
    global screen
    pygame.init()
    screen = pygame.display.set_mode((squareSize*14, squareSize*8))
    # Start Mainloop
    global squareOne
    squareOne = None
    if gameMode == "TwoPlayerDigital":
        mainLoop(
            mouseControl=True,
            undos=True,
        )
    elif gameMode == "OnePlayerDigital":
        mainLoop(
            mouseControl=True,
            computerPlayerBlack=True,
            undos=True,
        )
    elif gameMode == "TwoComputerPlayers":
        mainLoop(
            computerPlayerBlack=True,
            computerPlayerWhite=True,
        )
    elif gameMode == "WatchFamousGame":
        global moves
        moves = list(move for move in (read_game(open(f"Games\{os.listdir('Games')[arguements]}")).mainline_moves()))
        mainLoop(
            setMoveList=True,
            undos=True,
        )
    elif gameMode == "Puzzle":
        StartPuzzle()
        mainLoop(
            mouseControl=True,
            puzzle=True,
        )
def SelectForMove():
    global squareOne
    x, y = pygame.mouse.get_pos()
    squareFile = (x // squareSize) - 3
    squareRank = 7 - (y // squareSize)
    if squareOne != None:
        moveUCI = GetSquareName(squareOne) + GetSquareName(squareFile + squareRank * 8)
        squareOne = None
        try:
            PlayMove(moveUCI)
            return True
        except chess.InvalidMoveError:
            print("Invalid Move")
        except chess.IllegalMoveError:
            print("Ilegal Move")
        return False
    else:
        square = squareFile + squareRank * 8
        if board.piece_at(square) != None:
            if board.piece_at(square).color == board.turn:
                squareOne = square
        return False
def DrawPieces():
    for y in range(8):
        for x in range(8):
            piece = str(board.piece_at(x + y * 8))
            if piece == "None":
                continue
            elif squareOne == x + y * 8:
                pass
            else:
                screen.blit(imgs[piece], ((x + 3) * squareSize, (7-y) * squareSize))
    for piece in storage:
        for position in storage[piece].filledStorage:
            screen.blit(imgs[piece], ((position.x + 3) * squareSize, (7-position.y) * squareSize))
    #Drag and Drop
    if squareOne != None:
        piece = str(board.piece_at(squareOne))
        mousePosition = pygame.mouse.get_pos()
        #Adjust piece position so mouse doesn't hold top right of model
        x, y = mousePosition[0]-squareSize/2, mousePosition[1]-squareSize/2
        screen.blit(imgs[piece], (x, y))
    pygame.display.update()

def draw_board():
    LIGHT_SQUARE_COLOUR = (212, 187, 133)
    DARK_SQUARE_COLOUR = (130, 84, 47)

    X_SIZE = 14
    Y_SIZE = 8

    BLANK_FILES = (2, 11)
    screen.fill((0, 0, 0))
    for y in range(Y_SIZE):
        for x in range(X_SIZE):
            if x in BLANK_FILES:
                continue
            colour = LIGHT_SQUARE_COLOUR if (x + y) % 2 == 0 else DARK_SQUARE_COLOUR
            pygame.draw.rect(screen, colour, (x*squareSize, y*squareSize, squareSize, squareSize))

def LerpColour(self, colourOne, colourTwo, percentage):
        red = colourOne[0] + ((colourTwo[0]-colourOne[0]) * percentage)
        green = colourOne[1] + ((colourTwo[1]-colourOne[1]) * percentage)
        blue = colourOne[2] + ((colourTwo[2]-colourOne[2]) * percentage)
        return (red, green, blue)

def GetPuzzle(lowerBound, upperBound):
    possiblePuzzles = []
    with open("puzzles.txt", "r") as puzzleFile:
        for line in puzzleFile:
            fen = line.split()[0]
            turn = line.split()[1]
            solution = line.split()[2:-1]
            rating = int(line.split()[-1])
            if rating in range(lowerBound, upperBound):
                possiblePuzzles.append((fen, turn, solution, rating))
    return random.choice(possiblePuzzles)
def StartPuzzle():
    global solution
    fen, turn, solution, rating = GetPuzzle(easiest.get(), hardest.get())
    SetFEN(fen)
    if turn == "b" and board.turn or turn == "w" and not board.turn:
        SkipTurn()
    firstMove = solution.pop(0)
    PlayMove(firstMove)
# <---------------------------> #

# GameModes #
# <---------------------------> #
def mainLoop(mouseControl : bool = False, setMoveList : bool = False, computerPlayerBlack : bool = False, computerPlayerWhite : bool = False, undos : bool = False, puzzle : bool = False):
    moveCounter = 0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONUP and mouseControl:
                if SelectForMove() and puzzle:
                    move = board.peek()
                    if solution[moveCounter] == move.uci():
                        moveCounter += 2
                        if moveCounter < len(solution):
                            PlayMove(solution[moveCounter-1])
                        else:
                            print("Solved")
                            StartPuzzle()
                            moveCounter = 0
                    else:
                        UndoMove()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and undos:
                    moveCounter -= 1
                    UndoMove()
                if event.key == pygame.K_RIGHT and setMoveList:
                    PlayMove(moves[moveCounter])
                    moveCounter += 1
                if event.key == pygame.K_r:
                    reset()
                if event.key == pygame.K_s and puzzle:
                    print(solution[moveCounter])
        draw_board()
        DrawPieces()
        if computerPlayerBlack and not board.turn:
            EngineMove()
        elif computerPlayerWhite and board.turn:
            EngineMove()
    pygame.quit()
# <---------------------------> #

# Visual Settings #
# <---------------------------> #
squareSize = 70
imgs = {
    "P" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/whitePawn.png'), (squareSize, squareSize)),
    "R" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/whiteRook.png'), (squareSize, squareSize)),
    "N" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/whiteKnight.png'), (squareSize, squareSize)),
    "B" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/whiteBishop.png'), (squareSize, squareSize)),
    "Q" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/whiteQueen.png'), (squareSize, squareSize)),
    "K" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/whiteKing.png'), (squareSize, squareSize)),
    "p" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/blackPawn.png'), (squareSize, squareSize)),
    "r" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/blackRook.png'), (squareSize, squareSize)),
    "n" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/blackKnight.png'), (squareSize, squareSize)),
    "b" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/blackBishop.png'), (squareSize, squareSize)),
    "q" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/blackQueen.png'), (squareSize, squareSize)),
    "k" : pygame.transform.scale(pygame.image.load(f'static/PieceImages/blackKing.png'), (squareSize, squareSize)),
}
# <---------------------------> #

# Running Code #
# <---------------------------> #
if __name__ == "__main__":
    UISelection()  
# <---------------------------> #