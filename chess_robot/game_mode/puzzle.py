import random
import json

def get_puzzle(lowerBound, upperBound):
    possiblePuzzles = []
    with open("puzzles.json", "r") as puzzle_file:
        puzzles = json.load(puzzle_file)
        for puzzle in puzzles:
            fen = puzzle["board"]
            turn = puzzle["active_colour"]
            solution = puzzle["moves"]
            rating = puzzle["rating"]
            if rating in range(lowerBound, upperBound):
                possiblePuzzles.append((fen, turn, solution, rating))
    if possiblePuzzles:
        return random.choice(possiblePuzzles)
    else:
        return None
    