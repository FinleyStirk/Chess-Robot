from common.structs import GantryCommand, Cell, Vector2
from collections import deque
import chess

class PathCalculator:

    @staticmethod
    def castle_path(move_uci: str):
        # Not a fan of this (maybe add more info to MoveInfo)
        match move_uci:
            case "e1g1":
                path = [
                    GantryCommand(7,  0,  0), GantryCommand(5,  0,  1), 
                    GantryCommand(4,  0,  0), GantryCommand(4, -1,  1), 
                    GantryCommand(6, -1,  1), GantryCommand(6,  0,  1),
                ]
            case "e1c1":
                path = [
                    GantryCommand(0,  0,  0), GantryCommand(3,  0,  1), 
                    GantryCommand(4,  0,  0), GantryCommand(4, -1,  1), 
                    GantryCommand(2, -1,  1), GantryCommand(2,  0,  1),
                ]
            case "e8g8":
                path = [
                    GantryCommand(7,  7,  0), GantryCommand(5,  7,  1), 
                    GantryCommand(4,  7,  0), GantryCommand(4,  8,  1), 
                    GantryCommand(6,  8,  1), GantryCommand(6,  7,  1),
                ]
            case "e8c8":
                path = [
                    GantryCommand(0,  7,  0), GantryCommand(3,  7,  1), 
                    GantryCommand(4,  7,  0), GantryCommand(4,  8,  1), 
                    GantryCommand(2,  8,  1), GantryCommand(2,  7,  1),
                ]
            case _:
                raise Exception("Invalid Castle move")
            
        return path

    @staticmethod
    def indirect_path(start_square: Vector2, end_square: Vector2, obstructed_squares: set[Vector2]):
        visited_squares = set()
        unvisited_squares = deque([Cell(start_square)])
        while unvisited_squares:
            square = unvisited_squares.popleft()
            visited_squares.add(square.position)
            
            for x in (-1, 0, 1):
                for y in (-1, 0, 1):
                    next_square_position = square.position + Vector2(x, y)
                    next_square = Cell(next_square_position, square)

                    if next_square.position == end_square:
                        path = []
                        while next_square.parent:
                            path.append(GantryCommand(square.position.x, square.position.y, 1))
                            next_square = next_square.parent
                        path.append(GantryCommand(start_square.x, start_square.y, 0))
                        path.reverse()
                        return path
                    
                    if next_square.position in visited_squares:
                        continue
                    if next_square.position.x not in range(-3, 11) or next_square.position.y not in range(-1, 9): 
                        continue
                    if next_square.position in obstructed_squares:
                        continue

                    unvisited_squares.append(next_square)

            

        raise Exception(f"No available path from {start_square} to {end_square} with blocked squares {obstructed_squares}")

    @staticmethod
    def knight_path(start_square: Vector2, end_square: Vector2):
        # Can be improved later
        path = []

        startCornerX = start_square.x + 0.5 if start_square.x <= end_square.x else start_square.x - 0.5
        startCornerY = start_square.y + 0.5 if start_square.y < end_square.y else start_square.y - 0.5
        endCornerX = end_square.x - 0.5 if start_square.x < end_square.x else end_square.x + 0.5
        endCornerY = end_square.y - 0.5 if start_square.y <= end_square.y else end_square.y + 0.5

        path.append(GantryCommand(start_square.x, start_square.y, 0))
        path.append(GantryCommand(startCornerX, startCornerY, 1))
        if abs(end_square.x - start_square.x) >= 2:
            path.append(GantryCommand(endCornerX, startCornerY, 1))
        if abs(end_square.y - start_square.y) >= 2:
            path.append(GantryCommand(endCornerX, endCornerY, 1))
        path.append(GantryCommand(end_square.x, end_square.y, 1))
                
        return path

    @staticmethod
    def direct_path(start_square: Vector2, end_square: Vector2):
        stepOne = GantryCommand(start_square.x, start_square.y, 0)
        stepTwo = GantryCommand(end_square.x, end_square.y, 1)
        return [stepOne, stepTwo]