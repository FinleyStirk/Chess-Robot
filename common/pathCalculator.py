# Other Files #
# <---------------------------> #
from common.structs import Coord, Vector2, Node
from chess import Move, Board
# <---------------------------> #

# Functions #
# <---------------------------> #
def DirectPath(start, end):
    stepOne = Coord(start.x, start.y, 0)
    stepTwo = Coord(end.x, end.y, 1)
    return [stepOne, stepTwo]
def KnightPath(start, end):
    path = []

    startCornerX = start.x + 0.5 if start.x <= end.x else start.x - 0.5
    startCornerY = start.y + 0.5 if start.y < end.y else start.y - 0.5
    endCornerX = end.x - 0.5 if start.x < end.x else end.x + 0.5
    endCornerY = end.y - 0.5 if start.y <= end.y else end.y + 0.5

    path.append(Coord(start.x, start.y, 0))
    path.append(Coord(startCornerX, startCornerY, 1))
    if abs(end.x - start.x) >= 2:
        path.append(Coord(endCornerX, startCornerY, 1))
    if abs(end.y - start.y) >= 2:
        path.append(Coord(endCornerX, endCornerY, 1))
    path.append(Coord(end.x, end.y, 1))
            
    return path
def IndirectPath(start, end, piecePositions):
    start, end = Node(start.x, start.y), Node(end.x, end.y)
    traversedNodes = [start]
    solved = False
    for node in traversedNodes:
        for offset in offsets:
            nextNode = node + offset
            nextNode.direction = offset
            if offset == node.direction:
                nextNode.parent = node.parent
            else:
                nextNode.parent = node
            if nextNode == end:
                currentStep = nextNode
                solved = True
                break
            if nextNode.x not in boardSizeX or nextNode.y not in boardSizeY or Vector2(nextNode.x, nextNode.y) in piecePositions or nextNode in traversedNodes:
                continue
            traversedNodes.append(nextNode)
        if solved:
            break
    path = []
    if not solved:
        # When no possible path exists that means a pawn is blocking the way
        if start.x == -3 or end.x == -3 or start.x == 10 or end.x == 10:
            if start.x == -3:
                # Move Pawn out of Way
                path += DirectPath(Vector2(-2, start.y), Vector2(-1, start.y))
                # Update the piece positions to reflect new pawn position
                piecePositions.remove(Vector2(-2, start.y))
                piecePositions.append(Vector2(-1, start.y))
                # Recalculate path now that pawn was moved
                path += IndirectPath(Vector2(start.x, start.y), Vector2(end.x, end.y), piecePositions)
                # Move pawn back to original position
                path += DirectPath(Vector2(-1, start.y), Vector2(-2, start.y))
            elif end.x == -3:
                path += DirectPath(Vector2(-2, end.y), Vector2(-1, end.y))
                piecePositions.remove(Vector2(-2, end.y))
                piecePositions.append(Vector2(-1, end.y))
                path += IndirectPath(Vector2(start.x, start.y), Vector2(end.x, end.y), piecePositions)
                path += DirectPath(Vector2(-1, end.y), Vector2(-2, end.y))
            elif start.x == 10:
                path += DirectPath(Vector2(9, start.y), Vector2(8, start.y))
                piecePositions.remove(Vector2(9, start.y))
                piecePositions.append(Vector2(8, start.y))
                path += IndirectPath(Vector2(start.x, start.y), Vector2(end.x, end.y), piecePositions)
                path += DirectPath(Vector2(8, start.y), Vector2(9, start.y))
            elif end.x == 10:
                path += DirectPath(Vector2(9, end.y), Vector2(8, end.y))
                piecePositions.remove(Vector2(9, end.y))
                piecePositions.append(Vector2(8, end.y))
                path += IndirectPath(Vector2(start.x, start.y), Vector2(end.x, end.y), piecePositions)
                path += DirectPath(Vector2(8, end.y), Vector2(9, end.y))
            return path
        else:
            raise Exception("No possible path")
    while currentStep != start:
        path.insert(0, currentStep.toCoord(1))
        currentStep = currentStep.parent
    path.insert(0, start.toCoord(0))
    return path
def SmoothPath(start, end):
    direction = end - start
    if abs(direction.x) == (direction.y):
        return None

    isHorizontal = abs(direction.x) > abs(direction.y)
    if isHorizontal:
        y = end.y
        if direction.x * direction.y > 0:
            x = start.x + direction.y
        else:
            x = start.x - direction.y
    else:
        x = end.x
        if direction.x * direction.y > 0:
            y = start.y + direction.x
        else:
            y = start.y - direction.x

    middleStep = Vector2(x, y)
    if middleStep == start:
        return None
    elif middleStep == end:
        return None
    else:
        return middleStep
def CastlePath(board : Board, move : Move, reverse : bool = False):
    if board.turn:
        if board.is_kingside_castling(move):
            if reverse:
                return (Coord(6, 0, 0), Coord(6, -1, 1), Coord(4, -1, 1), Coord(4, 0, 1), Coord(5, 0, 0), Coord(7, 0, 1))
            else:
                return (Coord(7, 0, 0), Coord(5, 0, 1), Coord(4, 0, 0), Coord(4, -1, 1), Coord(6, -1, 1), Coord(6, 0, 1))
        if board.is_queenside_castling(move):
            if reverse:
                return (Coord(2, 0, 0), Coord(2, -1, 1), Coord(4, -1, 1), Coord(4, 0, 1), Coord(3, 0, 0), Coord(0, 0, 1))
            else:
                return (Coord(0, 0, 0), Coord(3, 0, 1), Coord(4, 0, 0), Coord(4, -1, 1), Coord(2, -1, 1), Coord(2, 0, 1))
    else:
        if board.is_kingside_castling(move):
            if reverse:
                return (Coord(6, 7, 0), Coord(6, 8, 1), Coord(4, 8, 1), Coord(4, 7, 1), Coord(5, 7, 0), Coord(7, 7, 1))
            else:
                return (Coord(7, 7, 0), Coord(5, 7, 1), Coord(4, 7, 0), Coord(4, 8, 1), Coord(6, 8, 1), Coord(6, 7, 1))
        if board.is_queenside_castling(move):
            if reverse:
                return (Coord(2, 7, 0), Coord(2, 8, 1), Coord(4, 8, 1), Coord(4, 7, 1), Coord(3, 7, 0), Coord(0, 7, 1))
            else:
                return (Coord(0, 7, 0), Coord(3, 7, 1), Coord(4, 7, 0), Coord(4, 8, 1), Coord(2, 8, 1), Coord(2, 7, 1))        
# <---------------------------> #
    
# Internal Variables #
# <---------------------------> #
offsets = (
    Vector2(1, 0),
    Vector2(-1, 0),
    Vector2(0, 1),
    Vector2(0, -1),
    Vector2(1, 1),
    Vector2(1, -1),
    Vector2(-1, 1),
    Vector2(-1, -1),
)
boardSizeX = range(-3, 11)
boardSizeY = range(-1, 9)
# <---------------------------> #