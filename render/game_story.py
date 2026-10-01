"""Builds one continuous program telling a game's opening, stitched from the
single-move demos -- everything from running the real chess_robot code:

  1. hold on the office view while the gantry drives under the first
     piece to move; glide down through the board to look at the carriage
     from below, beside it; ride along under the board as the gantry
     carries the piece; glide up to the player view  (--intro-only stops here)
  2. play fast up to the game's first knight move, and drive the gantry
     under that knight
  3. draw the knight move's chess.com-style arrow in the player view, glide
     down to the knight close-up, fade the arrow there, then play the rest
     of the knight demo (move_demo.py) and glide back to the player view
  4. play fast up to the first capture
  5. capture demo (bfs_demo.py): the arrow in the player view, then glide
     to the overhead view for the search, route and carry
  6. glide back to the player view and hold

Marker steps note when each demo section starts and ends, for the
website's captions: piece_movement_* (camera arrives under the board ->
carry finished), knight_movement_* (camera arrives at the close-up, a beat before
the chess.com-style arrow fades -> knight landed), capture_* (camera arrives overhead -> capture finished).

The gantry never moves while the camera does, except while the camera
rides along with it under the board. Run with the project's Python from
the repo root:

    .venv/bin/python render/game_story.py "chess_robot/games/Sergey Karjakin vs Magnus Carlsen.pgn"
    # -> render/programs/story_sergey_karjakin_vs_magnus_carlsen.json
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess  # noqa: E402
import chess.pgn  # noqa: E402

from chess_robot import BoardState, Robot, RobotBoard  # noqa: E402
from bfs_demo import capture_steps, play_instrumented, storage_contents  # noqa: E402
from move_demo import move_steps, notation_arrow_step  # noqa: E402
from record_game import PROGRAMS_DIR, RecordingGantry  # noqa: E402

# The in-between moves, played quickly: 12x the demos' speed. (Speed x4,
# acceleration x16 and the gap /4 make every fast move take exactly a quarter
# of the time it did at 450 mm/s, 3000 mm/s^2, 0.15 s gaps.)
FAST = {"speed_mm_s": 1800, "accel_mm_s2": 48000}
BETWEEN_FAST_MOVES = 0.0375  # seconds
GLIDE = 1.5                 # seconds per camera glide
KNIGHT_CAMERA_BACK = 1.5    # squares behind the knight (see move_demo.py)
UNDERSIDE_HOLD = 1.5        # seconds looking up at the carriage under the first piece
ARROW_HOLD_IN_CLOSEUP = 1.5 # seconds the knight's chess.com-style arrow stays after the close-up arrives


def glide(camera, seconds=GLIDE):
    return {"camera": camera, "seconds": seconds}


def play(board, gantry, uci):
    """Plays a move through the real code; returns its recorded gantry steps."""
    first = len(gantry.steps)
    board.play_move(uci)
    return gantry.steps[first:]


def fast(steps):
    return [{**step, **FAST} for step in steps] + [{"pause": BETWEEN_FAST_MOVES}]


def with_marker_after_last_move(steps, marker):
    """Inserts a marker step right after the last move step."""
    last = max(i for i, step in enumerate(steps) if "move" in step)
    return steps[:last + 1] + [{"marker": marker}] + steps[last + 1:]


def build_story(game, intro_only=False):
    moves = list(game.mainline_moves())
    replay = game.board()
    knight_ply = capture_ply = None
    for ply, move in enumerate(moves):
        if knight_ply is None and replay.piece_type_at(move.from_square) == chess.KNIGHT:
            knight_ply = ply
        if replay.is_capture(move):
            capture_ply = ply
            break
        replay.push(move)
    if knight_ply is None or capture_ply is None or knight_ply > capture_ply:
        raise SystemExit("need a knight move before the game's first capture")
    if moves[knight_ply].from_square // 8 > 3:
        raise SystemExit("the knight close-up assumes white's knight (camera behind it, on white's side)")

    gantry = RecordingGantry()
    board = RobotBoard(BoardState(), Robot(gantry))
    header = {"position": board._board_state.board.fen(), "storage": storage_contents(board),
              "start": [gantry._position.x, gantry._position.y], "camera": "office"}

    # Intro: the first move. The gantry drives under the piece (office view),
    # the camera glides beneath the board beside it, waits, then rides along
    # under the board as the piece is carried, then glides up to the player view.
    first = moves[0]
    recorded = play(board, gantry, first.uci())
    beside = chess.square_name(first.from_square - 1 if chess.square_file(first.from_square) > 0
                               else first.from_square + 1)
    steps = [{"pause": 1.0}]
    steps += fast(recorded[:1])
    steps += [glide({"under": beside, "looking_at": chess.square_name(first.from_square)}, 2.0),
              {"marker": "piece_movement_start"}, {"pause": UNDERSIDE_HOLD}]
    steps += [{**step, "camera_follow": True} for step in recorded[1:]]
    steps += [{"marker": "piece_movement_end"}, {"pause": 0.6}, glide("player", 2.0), {"pause": 0.3}]
    if intro_only:
        return {**header, "steps": steps + [{"pause": 0.7}]}

    for move in moves[1:knight_ply]:
        steps += fast(play(board, gantry, move.uci()))

    # The knight: drive under it fast, glide down, then the knight demo.
    knight = moves[knight_ply]
    knight_steps = play(board, gantry, knight.uci())
    steps += [{**knight_steps[0], **FAST}, {"pause": 0.3}]
    in_front = chess.square_name(knight.from_square + 8)  # the square ahead of it, up its file
    # The chess.com-style arrow is drawn in the player view and stays up
    # through the glide down, fading once the close-up has arrived:
    # draw 0.5 + 0.5 to look at it + the glide + ARROW_HOLD_IN_CLOSEUP.
    steps += [notation_arrow_step(knight.uci(), hold=0.5 + GLIDE + ARROW_HOLD_IN_CLOSEUP), {"pause": 1.0},
              glide({"above": in_front, "view_squares": 5, "back_squares": KNIGHT_CAMERA_BACK}),
              {"marker": "knight_movement_start"},  # caption in on arrival, a beat before the arrow fades
              {"pause": ARROW_HOLD_IN_CLOSEUP + 0.4 + 0.3}]  # the rest of the hold, the fade, then a beat
    steps += with_marker_after_last_move(move_steps(knight_steps, knight.uci(), arrow_id="knight", notation=False),
                                         "knight_movement_end")
    steps += [glide("player"), {"pause": 0.3}]

    for move in moves[knight_ply + 1:capture_ply]:
        steps += fast(play(board, gantry, move.uci()))

    # The capture: arrow in the player view, then overhead for the search.
    capture = moves[capture_ply]
    capture_recorded, explored, route = play_instrumented(board, gantry, capture.uci())
    steps += with_marker_after_last_move(
        capture_steps(capture_recorded, explored, route, arrow_id="capture",
                      after_arrow=[glide("overhead"), {"marker": "capture_start"}, {"pause": 0.3}]),
        "capture_end")
    steps += [glide("player"), {"pause": 1.0}]

    labels = {ply: f"{ply // 2 + 1}{'.' if ply % 2 == 0 else '...'}" for ply in (knight_ply, capture_ply)}
    print(f"knight demo: {labels[knight_ply]} {knight.uci()}, capture demo: {labels[capture_ply]} {capture.uci()}")
    return {**header, "steps": steps}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pgn")
    parser.add_argument("--intro-only", action="store_true", help="just the first move's under-board intro")
    parser.add_argument("--out", help="default: render/programs/story_<pgn name>[_intro].json")
    args = parser.parse_args()

    program = build_story(chess.pgn.read_game(open(args.pgn)), intro_only=args.intro_only)
    name = os.path.splitext(os.path.basename(args.pgn))[0].lower().replace(" ", "_")
    out = args.out or os.path.join(PROGRAMS_DIR, f"story_{name}{'_intro' if args.intro_only else ''}.json")
    with open(out, "w") as f:
        json.dump(program, f, indent=1)
    print(f"wrote {len(program['steps'])} steps -> {out}")


if __name__ == "__main__":
    main()
