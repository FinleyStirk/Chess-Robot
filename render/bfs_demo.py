"""Builds a gantry program that shows off the capture path-finding (the BFS in
chess_robot/utils/path_calculator.py) for one capturing move, from the real
code's own search -- nothing about the search is re-implemented here:

  1. an arrow shows the intended move; it stays up throughout, and is eaten
     up by the piece as the gantry finally carries it along the arrow
  2. the captured piece's square and its storage slot light up
  3. the BFS spreads out from the captured piece, layer by layer (turquoise),
     in the order the real search explores squares
  4. the storage slot turns green, then the route backtracks to the start,
     each square turning green in turn
  5. every other searched square goes out
  6. the gantry carries the captured piece off along the route (the real,
     simplified waypoints); each square's green goes out as the piece leaves
     it; then the move itself is made
  7. nothing is left lit

The real search is observed by swapping path_calculator's deque for one that
logs what it pops, and wrapping _drop_collinear_waypoints to capture the
full square-by-square route before it's simplified. Run with the project's
Python from the repo root:

    .venv/bin/python render/bfs_demo.py --setup e2e4 d7d5 --move e4d5
    # -> render/programs/bfs_e4d5.json
"""

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chess_robot import BoardState, Robot, RobotBoard  # noqa: E402
from chess_robot.utils import path_calculator  # noqa: E402
from chess_robot.utils.path_calculator import PathCalculator  # noqa: E402
from record_game import PROGRAMS_DIR, RecordingGantry  # noqa: E402

ARROW = "#ff2a2a"
ENDPOINTS = "#ffd21a"   # start square + storage slot, before the search
SEARCHED = "#1ad6c8"    # turquoise
ROUTE = "#2ee65a"       # green

# Pacing (seconds)
LAYER_SECONDS = 0.25     # between BFS layers
BACKTRACK_SECONDS = 0.18  # between route squares turning green


class _LoggingDeque(collections.deque):
    popped = []  # Cells, in the order the BFS explores them

    def popleft(self):
        cell = super().popleft()
        _LoggingDeque.popped.append(cell)
        return cell


def _depth(cell):
    depth = 0
    while cell.parent is not None:
        depth, cell = depth + 1, cell.parent
    return depth


def play_instrumented(board, gantry, move):
    """Plays capturing `move` on a RobotBoard whose Robot drives a
    RecordingGantry, observing the real BFS. Returns (gantry steps for this
    move, explored cells in search order, full square-by-square route)."""
    first_step = len(gantry.steps)
    routes = []
    original_drop = PathCalculator._drop_collinear_waypoints
    original_deque = path_calculator.deque

    def capture_route(path):
        routes.append(list(path))
        return original_drop(path)

    _LoggingDeque.popped = []
    path_calculator.deque = _LoggingDeque
    PathCalculator._drop_collinear_waypoints = staticmethod(capture_route)
    try:
        info = board.play_move(move)
    finally:
        path_calculator.deque = original_deque
        PathCalculator._drop_collinear_waypoints = staticmethod(original_drop)

    if info.capture_destination is None or not routes:
        raise SystemExit(f"{move} isn't a capture that goes through the BFS")
    return gantry.steps[first_step:], list(_LoggingDeque.popped), routes[0]


def storage_contents(board):
    """What PieceStorage holds right now: every piece captured so far, plus
    the spare queens it starts with."""
    return [{"square": [square.x, square.y], "piece": piece.symbol()}
            for piece, slots in board._board_state._storage._state.items() for square in slots.filled]


def record_capture(setup_moves, move):
    """Plays setup_moves, then `move` with the search instrumented. Returns
    (FEN before `move`, pieces in storage before `move`, gantry start,
    gantry steps for `move`, explored cells, full route)."""
    gantry = RecordingGantry()
    board = RobotBoard(BoardState(), Robot(gantry))
    for uci in setup_moves:
        board.play_move(uci)
    fen = board._board_state.board.fen()
    storage = storage_contents(board)
    start = [gantry._position.x, gantry._position.y]
    gantry.steps = []
    steps, explored, route = play_instrumented(board, gantry, move)
    return fen, storage, start, steps, explored, route


def xy(v):
    return [v.x, v.y]


def build_program(fen, storage, start, steps, explored, route):
    return {"position": fen, "storage": storage, "start": start, "steps": capture_steps(steps, explored, route)}


def capture_steps(steps, explored, route, after_arrow=(), arrow_id="move"):
    """The demo's program steps for one recorded capture. `after_arrow` steps
    (e.g. a camera move) are slotted in once the arrow has been drawn."""
    route_squares = [xy(v) for v in route]
    capture_from, slot = route_squares[0], route_squares[-1]  # slot: where the captured piece goes
    program_steps = [{"pause": 0.5}]

    # 1. intended move: the capturing piece's own leg is the last recorded segment
    move_from, move_to = steps[-2]["move"], steps[-1]["move"]
    program_steps += [{"arrow": [move_from, move_to], "color": ARROW, "id": arrow_id, "hold": None}, {"pause": 1.2}]
    program_steps += list(after_arrow)

    # 2. endpoints
    program_steps += [{"glow": [capture_from, slot], "color": ENDPOINTS}, {"pause": 0.8}]

    # 3. BFS, layer by layer, in the real search's order (first visit only)
    seen, layers = {tuple(capture_from)}, collections.defaultdict(list)
    for cell in explored:
        key = (cell.position.x, cell.position.y)
        if key in seen:
            continue
        seen.add(key)
        layers[_depth(cell)].append(list(key))
    searched = []
    for depth in sorted(layers):
        program_steps += [{"glow": layers[depth], "color": SEARCHED}, {"pause": LAYER_SECONDS}]
        searched += layers[depth]
    program_steps.append({"pause": 0.5})

    # 4. storage turns green, then backtrack to the start
    for square in reversed(route_squares):
        program_steps += [{"glow": [square], "color": ROUTE}, {"pause": BACKTRACK_SECONDS}]
    program_steps.append({"pause": 0.6})

    # 5. everything searched but not on the route goes out
    off_route = [s for s in searched if s not in route_squares]
    program_steps += [{"unglow": off_route}, {"pause": 0.6}]

    # 6. carry the captured piece along the real (simplified) waypoints, as
    #    recorded; each square goes dark the moment the effector leaves it.
    capture_segment_end = next(i for i, s in enumerate(steps) if s["move"] == slot) + 1
    for step in steps[:capture_segment_end]:
        program_steps.append({**step, "clear_glows_passed": True} if step["magnet"] else step)
    program_steps += [{"pause": 0.3}, {"unglow": [slot]}]

    # ...then the move itself, exactly as recorded, eating the arrow as it goes
    program_steps += [{**step, "consume_arrow": arrow_id} if step["magnet"] else step
                      for step in steps[capture_segment_end:]]
    program_steps.append({"pause": 1.0})
    return program_steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", nargs="*", default=[], help="UCI moves played first to reach the position")
    parser.add_argument("--move", required=True, help="the capturing move to show, in UCI")
    parser.add_argument("--out", help="default: render/programs/bfs_<move>.json")
    args = parser.parse_args()

    fen, storage, start, steps, explored, route = record_capture(args.setup, args.move)
    program = build_program(fen, storage, start, steps, explored, route)
    out = args.out or os.path.join(PROGRAMS_DIR, f"bfs_{args.move}.json")
    with open(out, "w") as f:
        json.dump(program, f, indent=1)
    print(f"route {[xy(v) for v in route]}")
    print(f"explored {len(explored)} cells; wrote {len(program['steps'])} steps -> {out}")


if __name__ == "__main__":
    main()
