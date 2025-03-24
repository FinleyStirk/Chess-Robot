import random

def get_puzzle(lowerBound, upperBound):
    possiblePuzzles = []
    with open("puzzles.txt", "r") as puzzleFile:
        for line in puzzleFile:
            fen = line.split()[0]
            turn = line.split()[1]
            solution = line.split()[2:-1]
            rating = int(line.split()[-1])
            if rating in range(lowerBound, upperBound):
                possiblePuzzles.append((fen, turn, solution, rating))
    if possiblePuzzles:
        return random.choice(possiblePuzzles)
    else:
        return None