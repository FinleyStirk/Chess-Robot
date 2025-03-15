# Other Files #
# <---------------------------> #
from structs import Coord, Vector2, Node
from chess import Move, Board
import asyncio
# <---------------------------> #

# Functions #
# <---------------------------> #
def DirectPath(start, end):
    stepOne = Coord(start.x, start.y, 0)
    stepTwo = Coord(end.x, end.y, 1)
    return [stepOne, stepTwo]
def IndirectPath(start, end):
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
def OffBoardPath(start, end, piecePositions : list):
    hCost = lambda coord: min(abs(end.x - coord.x), abs(end.y - coord.y)) * 14 + abs(abs(end.x - coord.x) - abs(end.y - coord.y)) * 10
    openNodes = [Node(0, hCost(start), None, start)]
    closedNodes = []
    pathFound = False
    while not pathFound:
        if len(openNodes) == 0:
            print("impossible")
        
        currentNode = openNodes[0]
        for node in openNodes:
            if node.f < currentNode.f:
                currentNode = node

        openNodes.remove(currentNode)
        closedNodes.append(currentNode)

        for offset, gCost in offsets:
            nextNodeName = currentNode.name + offset
            if nextNodeName == end:
                pathFound = True
                break
            if nextNodeName in piecePositions:
                continue
            if nextNodeName.x not in boardSizeX or nextNodeName.y not in boardSizeY:
                continue
            if nextNodeName in [node.name for node in closedNodes]:
                continue

            nextNode = Node(currentNode.g + gCost, hCost(nextNodeName), currentNode, nextNodeName)
            if nextNode.name not in [node.name for node in openNodes]:
                openNodes.append(nextNode)
            else:
                for node in openNodes:
                    if node.name == nextNode.name:
                        if node.g > nextNode.g:
                            openNodes.remove(node)
                            openNodes.append(nextNode)
    path = []
    while currentNode.name != start:
        path.append(Coord(currentNode.name.x, currentNode.name.y, 1))
        currentNode = currentNode.parent
    
    path = path[::-1]
    path.append(Coord(end.x, end.y, 1))
    path.insert(0, Coord(start.x, start.y, 0))

    previous_direction = None
    simplifiedPath = [path[0]]
    for i in range(1, len(path)-1):
        direction = path[i+1] - path[i]
        if previous_direction is None or direction != previous_direction:
            simplifiedPath.append(path[i])
        previous_direction = direction
    simplifiedPath.append(path[-1])

    return simplifiedPath
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
def CastlePath(board : Board, move : Move):
    if board.turn:
        if board.is_kingside_castling(move):
            return (Coord(7, 0, 0), Coord(5, 0, 1), Coord(4, 0, 0), Coord(4, -1, 1), Coord(6, -1, 1), Coord(6, 0, 1))
        if board.is_queenside_castling(move):
            return (Coord(0, 0, 0), Coord(3, 0, 1), Coord(4, 0, 0), Coord(4, -1, 1), Coord(2, -1, 1), Coord(2, 0, 1))
    else:
        if board.is_kingside_castling(move):
            return (Coord(7, 7, 0), Coord(5, 7, 1), Coord(4, 7, 0), Coord(4, 8, 1), Coord(6, 8, 1), Coord(6, 7, 1))
        if board.is_queenside_castling(move):
            return (Coord(0, 7, 0), Coord(3, 7, 1), Coord(4, 7, 0), Coord(4, 8, 1), Coord(2, 8, 1), Coord(2, 7, 1))
# <---------------------------> #
    
# Internal Variables #
# <---------------------------> #
offsets = (
    (Vector2(1, 0), 10),
    (Vector2(-1, 0), 10),
    (Vector2(0, 1), 10),
    (Vector2(0, -1), 10),
    (Vector2(1, 1), 14),
    (Vector2(1, -1), 14),
    (Vector2(-1, 1), 14),
    (Vector2(-1, -1), 14),
)
boardSizeX = range(-3, 11)
boardSizeY = range(-1, 9)
# <---------------------------> #