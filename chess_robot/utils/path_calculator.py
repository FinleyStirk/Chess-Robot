from collections import deque

from chess_robot.utils.structs import Cell, Vector2


class PathCalculator:

    @staticmethod
    def castle_path(move_uci: str) -> list[list[Vector2]]:
        # Not a fan of this (maybe add more info to MoveInfo)
        match move_uci:
            case "e1g1":
                path = [
                    [Vector2(7,  0), Vector2(5,  0)], 
                    [Vector2(4,  0), Vector2(4, -1), Vector2(6, -1), Vector2(6,  0)]
                ]
            case "e1c1":
                path = [
                    [Vector2(0,  0), Vector2(3,  0)], 
                    [Vector2(4,  0), Vector2(4, -1), Vector2(2, -1),  Vector2(2,  0)],
                ]
            case "e8g8":
                path = [
                    [Vector2(7,  7), Vector2(5,  7)], 
                    [Vector2(4,  7), Vector2(4,  8), Vector2(6,  8), Vector2(6,  7)]
                ]
            case "e8c8":
                path = [
                    [Vector2(0,  7), Vector2(3,  7)]
                    [Vector2(4,  7), Vector2(4,  8), Vector2(2,  8), Vector2(2,  7)]
                ]
            case _:
                raise Exception("Invalid Castle move")
            
        return path


    @staticmethod
    def indirect_path(start_square: Vector2, end_square: Vector2, obstructed_squares: frozenset[Vector2]) -> list[Vector2]:
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
                        path = [start_square]
                        while next_square.parent:
                            path.insert(1, next_square.position)
                            next_square = next_square.parent
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
    def knight_path(start_square: Vector2, end_square: Vector2) -> list[Vector2]:
        # Can be improved later
        path = []

        start_corner_x = start_square.x + 0.5 if start_square.x <= end_square.x else start_square.x - 0.5
        start_corner_y = start_square.y + 0.5 if start_square.y < end_square.y else start_square.y - 0.5
        end_corner_x = end_square.x - 0.5 if start_square.x < end_square.x else end_square.x + 0.5
        end_corner_y = end_square.y - 0.5 if start_square.y <= end_square.y else end_square.y + 0.5

        path.append(start_square)
        path.append(Vector2(start_corner_x, start_corner_y))
        if abs(end_square.x - start_square.x) >= 2:
            path.append(Vector2(end_corner_x, start_corner_y))
        if abs(end_square.y - start_square.y) >= 2:
            path.append(Vector2(end_corner_x, end_corner_y))
        path.append(end_square)
                
        return path


    @staticmethod
    def direct_path(start_square: Vector2, end_square: Vector2) -> list[Vector2]:
        return [start_square, end_square]
    
