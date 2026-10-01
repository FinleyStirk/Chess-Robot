"""Records a gantry program by running the real chess_robot code with a
virtual gantry, so renders show exactly what the robot does -- every
in-between step the path planner produces, not hand-written moves.

Runs the normal CLI (load mode, no pauses) with its gantry swapped for one
that logs every home()/run_path() call, then writes those as a gantry.py
program. Run it with the project's own Python (it needs chess_robot's
dependencies), from the repo root:

    .venv/bin/python render/record_game.py "chess_robot/games/Fools Mate.pgn"
    # -> render/programs/fools_mate.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chess_robot import BoardState, Robot, RobotBoard, VirtualGantry  # noqa: E402
from chess_robot import cli  # noqa: E402

PROGRAMS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programs")


class RecordingGantry(VirtualGantry):
    """Logs moves in gantry.py's program format. Magnet rule is WebGantry's:
    the first step of each segment is travel (magnet off), the rest carry."""

    def __init__(self):
        super().__init__()
        self.steps = []

    def run_path(self, path):
        for segment in path:
            for index, step in enumerate(segment):
                self.steps.append({"move": [step.x, step.y], "magnet": bool(index)})
        super().run_path(path)

    def home(self):
        self.steps.append({"move": [0, 0], "magnet": False})
        super().home()


def record(pgn_path):
    gantry = RecordingGantry()
    start = gantry._position
    args = cli.parse_args(["load", "--pgn", pgn_path, "--no-pause"])
    board = RobotBoard(BoardState(), Robot(gantry))
    cli.run(cli.build_game(args, board, gantry, link=None))
    return {"source": os.path.basename(pgn_path), "start": [start.x, start.y], "steps": gantry.steps}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pgn")
    parser.add_argument("--out", help="output path (default: render/programs/<pgn name>.json)")
    args = parser.parse_args()

    program = record(args.pgn)
    name = os.path.splitext(os.path.basename(args.pgn))[0].lower().replace(" ", "_")
    out = args.out or os.path.join(PROGRAMS_DIR, f"{name}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(program, f, indent=2)
    print(f"recorded {len(program['steps'])} steps -> {out}")


if __name__ == "__main__":
    main()
