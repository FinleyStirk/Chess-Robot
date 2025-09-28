from collections import deque

from utils.structs import GantryCommand, Cell, Vector2


class PathCalculator:

    @staticmethod
    def castle_path(move_uci: str):
        # Not a fan of this (maybe add more info to MoveInfo)
        match move_uci:
            case "e1g1":
                path = [
                    GantryCommand(Vector2(7,  0),  0), GantryCommand(Vector2(5,  0),  1), 
                    GantryCommand(Vector2(4,  0),  0), GantryCommand(Vector2(4, -1),  1), 
                    GantryCommand(Vector2(6, -1),  1), GantryCommand(Vector2(6,  0),  1),
                ]
            case "e1c1":
                path = [
                    GantryCommand(Vector2(0,  0),  0), GantryCommand(Vector2(3,  0),  1), 
                    GantryCommand(Vector2(4,  0),  0), GantryCommand(Vector2(4, -1),  1), 
                    GantryCommand(Vector2(2, -1),  1), GantryCommand(Vector2(2,  0),  1),
                ]
            case "e8g8":
                path = [
                    GantryCommand(Vector2(7,  7),  0), GantryCommand(Vector2(5,  7),  1), 
                    GantryCommand(Vector2(4,  7),  0), GantryCommand(Vector2(4,  8),  1), 
                    GantryCommand(Vector2(6,  8),  1), GantryCommand(Vector2(6,  7),  1),
                ]
            case "e8c8":
                path = [
                    GantryCommand(Vector2(0,  7),  0), GantryCommand(Vector2(3,  7),  1), 
                    GantryCommand(Vector2(4,  7),  0), GantryCommand(Vector2(4,  8),  1), 
                    GantryCommand(Vector2(2,  8),  1), GantryCommand(Vector2(2,  7),  1),
                ]
            case _:
                raise Exception("Invalid Castle move")
            
        return path


    @staticmethod
    def indirect_path(start_square: Vector2, end_square: Vector2, obstructed_squares: frozenset[Vector2]):
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
                            path.append(GantryCommand(Vector2(next_square.position.x, next_square.position.y), 1))
                            next_square = next_square.parent
                        path.append(GantryCommand(Vector2(start_square.x, start_square.y), 0))
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

        start_corner_x = start_square.x + 0.5 if start_square.x <= end_square.x else start_square.x - 0.5
        start_corner_y = start_square.y + 0.5 if start_square.y < end_square.y else start_square.y - 0.5
        end_corner_x = end_square.x - 0.5 if start_square.x < end_square.x else end_square.x + 0.5
        end_corner_y = end_square.y - 0.5 if start_square.y <= end_square.y else end_square.y + 0.5

        path.append(GantryCommand(Vector2(start_square.x, start_square.y), 0))
        path.append(GantryCommand(Vector2(start_corner_x, start_corner_y), 1))
        if abs(end_square.x - start_square.x) >= 2:
            path.append(GantryCommand(Vector2(end_corner_x, start_corner_y), 1))
        if abs(end_square.y - start_square.y) >= 2:
            path.append(GantryCommand(Vector2(end_corner_x, end_corner_y), 1))
        path.append(GantryCommand(Vector2(end_square.x, end_square.y), 1))
                
        return path


    @staticmethod
    def direct_path(start_square: Vector2, end_square: Vector2):
        stepOne = GantryCommand(Vector2(start_square.x, start_square.y), 0)
        stepTwo = GantryCommand(Vector2(end_square.x, end_square.y), 1)
        return [stepOne, stepTwo]
    

if __name__ == "__main__":
    from_square=Vector2(x=4, y=3)
    to_square=Vector2(x=3, y=4)
    capture_destination=Vector2(x=-2, y=0)
    current_piece_positions=frozenset({Vector2(x=4, y=0), Vector2(x=3, y=4), Vector2(x=4, y=3), Vector2(x=3, y=1), Vector2(x=3, y=7), Vector2(x=4, y=6), Vector2(x=5, y=1), Vector2(x=5, y=7), Vector2(x=1, y=0), Vector2(x=1, y=6), Vector2(x=7, y=1), Vector2(x=7, y=7), Vector2(x=3, y=0), Vector2(x=5, y=0), Vector2(x=5, y=6), Vector2(x=0, y=1), Vector2(x=0, y=7), Vector2(x=2, y=1), Vector2(x=2, y=7), Vector2(x=6, y=1), Vector2(x=7, y=0), Vector2(x=6, y=7), Vector2(x=7, y=6), Vector2(x=4, y=7), Vector2(x=-3, y=4), Vector2(x=0, y=0), Vector2(x=10, y=4), Vector2(x=1, y=1), Vector2(x=2, y=0), Vector2(x=0, y=6), Vector2(x=1, y=7), Vector2(x=2, y=6), Vector2(x=6, y=0), Vector2(x=6, y=6)})
    print(PathCalculator.indirect_path(to_square, capture_destination, current_piece_positions))