"""Builds a gantry program showing one (non-capturing) move up close, from
the real code's own path for it:

  1. a chess.com-style arrow for the move (an L for knights: the long leg
     first, then the turn into the target square) draws in, holds, fades
  2. an arrow along the path the robot will actually drive (from
     PathCalculator -- e.g. a knight goes via the corners between squares)
     draws in and stays
  3. the gantry, already sitting under the piece, carries it along that
     path, eating the arrow up as it goes

The camera looks straight down over one square (--camera-square), close
enough to see about --view-squares squares top to bottom. The gantry
starts under the moving piece so sections can be stitched end to end.
Run with the project's Python from the repo root:

    .venv/bin/python render/move_demo.py --setup e2e4 e7e5 --move g1f3 --camera-square g2 --camera-back 1.5
    # -> render/programs/move_g1f3.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess  # noqa: E402

from chess_robot import BoardState, Robot, RobotBoard  # noqa: E402
from record_game import PROGRAMS_DIR, RecordingGantry  # noqa: E402

NOTATION_ARROW = "#ff2a2a"
PATH_ARROW = "#ff2a2a"
ARROW_WIDTH = 0.75        # both arrows, relative to arrows.py's default size


def notation_arrow(move):
    """The arrow a chess site draws: straight, or for a knight an L with the
    long leg first."""
    board_squares = [chess.square_file(move.from_square), chess.square_rank(move.from_square),
                     chess.square_file(move.to_square), chess.square_rank(move.to_square)]
    fx, fy, tx, ty = board_squares
    start, end = [fx, fy], [tx, ty]
    if {abs(tx - fx), abs(ty - fy)} == {1, 2}:  # knight-shaped
        corner = [fx, ty] if abs(ty - fy) > abs(tx - fx) else [tx, fy]
        return [start, corner, end]
    return [start, end]


def record_move(setup_moves, move_uci):
    gantry = RecordingGantry()
    board = RobotBoard(BoardState(), Robot(gantry))
    for uci in setup_moves:
        board.play_move(uci)
    fen = board._board_state.board.fen()
    storage = [{"square": [square.x, square.y], "piece": piece.symbol()}
               for piece, slots in board._board_state._storage._state.items() for square in slots.filled]
    gantry.steps = []
    info = board.play_move(move_uci)
    if info.capture_destination is not None:
        raise SystemExit(f"{move_uci} is a capture -- use bfs_demo.py for those")
    return fen, storage, gantry.steps


def build_program(fen, storage, steps, move_uci, camera_square, view_squares, camera_back):
    return {
        "position": fen,
        "storage": storage,
        "start": steps[0]["move"],        # the piece's square: the gantry starts right under it
        "camera": {"above": camera_square, "view_squares": view_squares, "back_squares": camera_back},
        "steps": move_steps(steps, move_uci),
    }


def notation_arrow_step(move_uci, hold=1.0):
    """The chess.com-style arrow: draws in (0.5 s), holds `hold` s, fades (0.4 s)."""
    return {"arrow": notation_arrow(chess.Move.from_uci(move_uci)), "color": NOTATION_ARROW,
            "width": ARROW_WIDTH, "hold": hold}


def move_steps(steps, move_uci, arrow_id="move", notation=True):
    """The demo's program steps for one recorded move (the gantry should
    already be under the piece). notation=False leaves out the chess.com-
    style arrow, for when the caller shows it separately."""
    path = [steps[0]["move"]] + [s["move"] for s in steps if s["magnet"]]
    program_steps = [{"pause": 0.5}]
    if notation:
        program_steps += [notation_arrow_step(move_uci), {"pause": 2.0}]  # draw + hold + fade, then a beat
    program_steps += [
        {"arrow": path, "color": PATH_ARROW, "width": ARROW_WIDTH, "id": arrow_id, "hold": None},
        {"pause": 1.3},
    ]
    program_steps += [{**s, "consume_arrow": arrow_id} if s["magnet"] else s for s in steps]
    program_steps.append({"pause": 1.0})
    return program_steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", nargs="*", default=[], help="UCI moves played first to reach the position")
    parser.add_argument("--move", required=True, help="the (non-capturing) move to show, in UCI")
    parser.add_argument("--camera-square", required=True, help='square the camera looks straight down on, e.g. "f2"')
    parser.add_argument("--view-squares", type=float, default=5, help="squares visible top to bottom (default 5)")
    parser.add_argument("--camera-back", type=float, default=0.0,
                        help="move the camera this many squares back towards white, tilting it forward (default 0)")
    parser.add_argument("--out", help="default: render/programs/move_<move>.json")
    args = parser.parse_args()

    fen, storage, steps = record_move(args.setup, args.move)
    program = build_program(fen, storage, steps, args.move, args.camera_square, args.view_squares, args.camera_back)
    out = args.out or os.path.join(PROGRAMS_DIR, f"move_{args.move}.json")
    with open(out, "w") as f:
        json.dump(program, f, indent=1)
    print(f"path {[s['move'] for s in steps]}")
    print(f"wrote {len(program['steps'])} steps -> {out}")


if __name__ == "__main__":
    main()
