"""Animates the gantry from a program of board moves, using the same
kinematics as the web demo (visuals/viewer.html): the whole gantry slides
along the viewer's Z axis, the carriage additionally along X. Moves go in
straight lines between their points. Consecutive moves with the same
magnet state form one movement (e.g. carrying a captured piece round
several corners): the gantry accelerates once at its start, keeps its speed
through the corners, and decelerates once at its end. Unlike
the web demo there are no travel limits: the gantry goes wherever the
program says (e.g. far storage slots).
Switching the magnet on picks up the piece on the carriage's current square
(exact grid match); switching it off drops the piece wherever it is.

Program format (JSON) -- squares are "e2" or [file, rank] with 0-based,
possibly fractional, coordinates ([4.5, 1.5] is the corner between e2/f2/e3/f3):

    {
      "speed_mm_s": 150,        # top speed
      "accel_mm_s2": 600,       # acceleration / deceleration at each movement's ends
      "steps": [
        {"move": "e2"},                  # travel, magnet off
        {"move": "e4", "magnet": true},  # carry whatever is on e2
        {"move": "e6", "magnet": true, "clear_glows_passed": true},  # lit squares go out as it leaves them
        {"pause": 0.5},                  # seconds
        {"glow": ["e5", "e4"], "color": "#ff7a1a", "hold": 1.5},  # light squares (takes no time)
        {"unglow": "all"},               # or a list of squares
        {"camera": "player", "seconds": 1.5},  # camera glides there; the gantry holds still meanwhile
        {"move": "e5", "speed_mm_s": 450, "accel_mm_s2": 3000},  # per-movement speed override
        {"move": "e6", "magnet": true, "camera_follow": true},     # the camera rides along with the gantry
        {"marker": "capture_start"},     # records the current frame (e.g. for website captions)
        {"arrow": ["e1", "f2"], "color": "#ff2a2a", "hold": 1.0},  # draws in, holds, fades (takes no time)
        {"arrow": ["g1", "g3", "f3"], "width": 0.35},              # 3+ points bend; width scales thickness
        {"arrow": ["e2", "e4"], "id": "next", "hold": null},       # stays until consumed...
        {"move": "e4", "magnet": true, "consume_arrow": "next"},   # ...by the piece travelling along it
        {"move": [0, 0]}
      ]
    }

For glows "hold" is optional: without it squares stay lit until an
"unglow". Arrows always fade out after their hold (default 1 s). See
glow.py / arrows.py.

The gantry starts at its CAD rest position unless the program gives
"start": <square>."""

import json
import math

import bpy
from mathutils import Vector

import scene

# --- from viewer.html ---
# (part name, which numbered copy, 1-based) -- the whole moving gantry.
GANTRY_PARTS = [
    ("MGN12H linear rail block", 1), ("Final X carriage body", 1), ("Final X carriage body", 2),
    ("MGN12H linear rail block", 2), ("3D printed Y carriage limit switch and linear rail mount", 1),
    ("GT2 Timing belt idler gear", 4), ("3D printed Y carriage limit switch and linear rail mount", 2),
    ("MGN12H linear rail 400mm", 1), ("MGN12H linear rail block", 3), ("Y carriage U block adaptor", 1),
    ("Y carriage block belt gripper shortened", 1), ("Limit switches modified", 1),
    ("GT2 Timing belt idler pulley", 1), ("Limit switches modified", 2), ("GT2 Timing belt idler pulley", 2),
    ("GT2 Timing belt idler gear", 6), ("M5x40 bolt for X carriage", 1),
    ("Y carriage clear plate final version", 1), ("M5x40 bolt for X carriage", 2),
    ("M5x40 bolt for X carriage", 3), ("Y carriage block belt gripper", 1), ("M5x40 bolt for X carriage", 4),
    ("Servo motor mount", 1),
]
# The central carriage (subset of the above), which also moves along X.
CARRIAGE_PARTS = [
    ("MGN12H linear rail block", 3), ("Y carriage U block adaptor", 1),
    ("Y carriage block belt gripper shortened", 1), ("Y carriage clear plate final version", 1),
    ("Y carriage block belt gripper", 1), ("Servo motor mount", 1),
]
EFFECTOR_PART = ("Servo motor mount", 1)
DEFAULT_SPEED_MM_S = 150
DEFAULT_ACCEL_MM_S2 = 600   # reaches 150 mm/s in 0.25 s


def movement_seconds(distance, speed, accel):
    """Duration of a movement: accelerate, cruise, decelerate, stop (a
    triangle profile if it's too short to reach full speed)."""
    if distance <= 0:
        return 0.0
    if distance >= speed * speed / accel:
        return speed / accel + distance / speed
    return 2 * math.sqrt(distance / accel)


def movement_progress(t, distance, speed, accel):
    """Distance covered t seconds into a movement_seconds() movement."""
    peak = min(speed, math.sqrt(accel * distance))
    t_accel = peak / accel
    d_accel = 0.5 * accel * t_accel ** 2
    t_cruise = (distance - 2 * d_accel) / peak
    total = 2 * t_accel + t_cruise
    if t <= t_accel:
        return 0.5 * accel * t * t
    if t <= t_accel + t_cruise:
        return d_accel + peak * (t - t_accel)
    remaining = max(0.0, total - t)
    return distance - 0.5 * accel * remaining * remaining


def movements(steps):
    """Splits program steps into items: non-move steps on their own, and
    runs of consecutive move steps sharing a magnet state (and speed
    settings) as one list."""
    def kind(step):
        return step.get("magnet", False), step.get("speed_mm_s"), step.get("accel_mm_s2")

    items = []
    for step in steps:
        if "move" in step and items and isinstance(items[-1], list) and kind(items[-1][-1]) == kind(step):
            items[-1].append(step)
        else:
            items.append([step] if "move" in step else step)
    return items


def parse_square(square):
    if isinstance(square, str):
        return ord(square[0].lower()) - ord("a"), int(square[1:]) - 1
    file, rank = square
    return float(file), float(rank)


def load_program(path):
    with open(path) as f:
        return json.load(f)


class GantryAnimator:
    def __init__(self, parts, pieces, fps, glows=None, arrows=None, camera=None, markers=None):
        self.fps = fps
        self.markers = markers if markers is not None else {}  # marker name -> frame
        self.glows = glows
        self.arrows = arrows
        self.camera = camera  # something with glide(spec, start_frame, seconds), for "camera" steps
        by_key = {(p["name"], p["type_index"] + 1): p for p in parts}
        missing = [key for key in GANTRY_PARTS if key not in by_key]
        if missing:
            raise ValueError(f"gantry parts not found in the assembly: {missing}")
        self.gantry_objects = [ob for key in GANTRY_PARTS for ob in by_key[key]["objects"]]
        self.carriage_objects = [ob for key in CARRIAGE_PARTS for ob in by_key[key]["objects"]]
        self.effector_rest = by_key[EFFECTOR_PART]["viewer_origin"]  # viewer frame, mm
        self.pieces = dict(pieces)  # (file, rank) -> objects; updated as pieces get carried
        self.base_locations = {ob: ob.location.copy() for ob in self.gantry_objects}
        for objects in self.pieces.values():
            for ob in objects:
                self.base_locations[ob] = ob.location.copy()
        self.piece_offsets = {id(objs): Vector() for objs in self.pieces.values()}

        self.gantry_offset = 0.0    # mm along viewer Z
        self.carriage_offset = 0.0  # mm along viewer X
        self.square = None          # carriage's current grid square, if known
        self.held = None
        self.frame = 1.0

    # --- geometry ------------------------------------------------------------

    def _offsets_for(self, square):
        x, z = scene.square_viewer_xz(*square)
        return z - self.effector_rest[2], x - self.effector_rest[0]

    def _key_rig(self):
        """Keyframe gantry, carriage and held piece at the current state."""
        gantry_delta = Vector((0, -self.gantry_offset / 1000, 0))       # viewer +Z -> Blender -Y
        carriage_delta = Vector((self.carriage_offset / 1000, 0, 0))    # viewer +X -> Blender +X
        carriage = set(self.carriage_objects)
        for ob in self.gantry_objects:
            ob.location = self.base_locations[ob] + gantry_delta + (carriage_delta if ob in carriage else Vector())
            ob.keyframe_insert("location", frame=self.frame)
        if self.held is not None:
            for ob in self.held:
                ob.location = self.base_locations[ob] + self.piece_offsets[id(self.held)]
                ob.keyframe_insert("location", frame=self.frame)

    # --- program -------------------------------------------------------------

    def run(self, program, duration=None):
        """duration: if given, seconds the whole program should take --
        overrides the top speed so the movements (plus any pauses) fill exactly
        that, keeping the acceleration."""
        self.speed = program.get("speed_mm_s", DEFAULT_SPEED_MM_S)
        self.accel = program.get("accel_mm_s2", DEFAULT_ACCEL_MM_S2)
        if "start" in program:
            self.square = parse_square(program["start"])
            self.gantry_offset, self.carriage_offset = self._offsets_for(self.square)
        if duration is not None:
            self.speed = self._fit_speed(program, duration)
        self._key_rig()

        for step in movements(program["steps"]):
            if isinstance(step, list):
                self._set_magnet(step[0].get("magnet", False))
                self._movement(step)
                continue
            if "pause" in step:
                self.frame += step["pause"] * self.fps
                self._key_rig()
                continue
            if "marker" in step:
                self.markers[step["marker"]] = round(self.frame)
                continue
            if "camera" in step:
                if self.camera is None:
                    raise ValueError("program has camera steps but no camera rig was given to animate()")
                seconds = step.get("seconds", 0.0)
                self.camera.glide(step["camera"], self.frame, seconds)
                self.frame += seconds * self.fps  # the gantry holds still while the camera moves
                self._key_rig()
                continue
            if "glow" in step or "unglow" in step:
                if self.glows is None:
                    raise ValueError("program has glow steps but no Glows was given to animate()")
                if "glow" in step:
                    kwargs = {k: step[k] for k in ("color", "hold") if k in step}
                    self.glows.glow(step["glow"], self.frame, **kwargs)
                else:
                    self.glows.unglow(step["unglow"], self.frame)
                continue
            if "arrow" in step:
                if self.arrows is None:
                    raise ValueError("program has arrow steps but no Arrows was given to animate()")
                kwargs = {k: step[k] for k in ("color", "hold", "width") if k in step}
                self.arrows.draw(step["arrow"], self.frame, arrow_id=step.get("id"), **kwargs)
                continue
        self._linearize()
        return int(self.frame + 0.999)

    def _movement_lengths(self, program):
        """Path length (mm) of every movement in the program, in order."""
        position = self._offsets_for(parse_square(program["start"])) if "start" in program else (0.0, 0.0)
        lengths = []
        for item in movements(program["steps"]):
            if isinstance(item, list):
                length = 0.0
                for step in item:
                    target = self._offsets_for(parse_square(step["move"]))
                    length += math.dist(target, position)
                    position = target
                lengths.append(length)
        return lengths

    def _fit_speed(self, program, duration):
        """Top speed at which the movements plus pauses take `duration` seconds."""
        pauses = sum(step["pause"] for step in program["steps"] if "pause" in step)
        lengths = self._movement_lengths(program)
        total = lambda speed: sum(movement_seconds(d, speed, self.accel) for d in lengths)
        low, high = 1.0, 20000.0
        if total(high) > duration - pauses:
            print(f"[gantry] can't fit into {duration} s at {self.accel} mm/s^2; using the fastest possible")
            return high
        for _ in range(60):
            mid = (low + high) / 2
            low, high = (mid, high) if total(mid) > duration - pauses else (low, mid)
        return high

    def _set_magnet(self, on):
        if on and self.held is None and self.square is not None:
            key = (round(self.square[0], 3), round(self.square[1], 3))
            self.held = self._take_piece(key)
            if self.held is not None:
                self._key_rig()  # anchor the piece before it starts moving
        elif not on and self.held is not None:
            self.pieces[(round(self.square[0], 3), round(self.square[1], 3))] = self.held
            self.held = None

    def _take_piece(self, key):
        for square in list(self.pieces):
            if (float(square[0]), float(square[1])) == (float(key[0]), float(key[1])):
                return self.pieces.pop(square)
        return None

    def _effector_square(self):
        """Board square (file, rank) the effector is currently over."""
        z = self.effector_rest[2] + self.gantry_offset
        x = self.effector_rest[0] + self.carriage_offset
        return (round((scene.BOARD_ORIGIN["z"] - z) / scene.SQUARE_SIZE_MM),
                round((x - scene.BOARD_ORIGIN["x"]) / scene.SQUARE_SIZE_MM))

    def _effector_xy(self):
        """Effector position in Blender coordinates (x, y), metres."""
        return ((self.effector_rest[0] + self.carriage_offset) / 1000,
                -(self.effector_rest[2] + self.gantry_offset) / 1000)

    def _movement(self, steps):
        """One movement through the move steps' points: straight lines between
        them, one acceleration at the start and one deceleration at the end,
        full speed through the corners. Baked one key per frame (so Blender
        adds no easing, and glows/arrows can follow it). Per step,
        clear_glows_passed puts lit squares out as the effector leaves them,
        and consume_arrow makes that arrow's tail follow the effector."""
        if any(step.get("consume_arrow") for step in steps) and self.arrows is None:
            raise ValueError("program consumes an arrow but no Arrows was given to animate()")
        follow = any(step.get("camera_follow") for step in steps)
        if follow and self.camera is None:
            raise ValueError("program has camera_follow but no camera rig was given to animate()")
        follow_from = self._effector_xy()
        points = [(self.gantry_offset, self.carriage_offset)] + [self._offsets_for(parse_square(s["move"])) for s in steps]
        legs = [math.dist(a, b) for a, b in zip(points, points[1:])]
        distance = sum(legs)
        speed = steps[0].get("speed_mm_s", self.speed)
        accel = steps[0].get("accel_mm_s2", self.accel)
        seconds = movement_seconds(distance, speed, accel)
        piece_start = self.piece_offsets[id(self.held)].copy() if self.held is not None else None
        start_frame = self.frame
        end_frame = start_frame + seconds * self.fps
        previous_square = self._effector_square()

        def leg_at(covered):
            """(leg index, fraction along it) for a distance covered."""
            for index, length in enumerate(legs):
                if covered <= length or index == len(legs) - 1:
                    return index, (covered / length if length else 1.0)
                covered -= length

        self._key_rig()
        if steps[0].get("consume_arrow"):
            self.arrows.consume(steps[0]["consume_arrow"], (*self._effector_xy(), 0), start_frame)
        frames = [f for f in range(math.floor(start_frame) + 1, math.ceil(end_frame))] + [end_frame]
        for frame in frames if seconds > 0 else []:
            covered = movement_progress((frame - start_frame) / self.fps, distance, speed, accel)
            index, fraction = leg_at(min(covered, distance))
            (a_gantry, a_carriage), (b_gantry, b_carriage) = points[index], points[index + 1]
            self.gantry_offset = a_gantry + (b_gantry - a_gantry) * fraction
            self.carriage_offset = a_carriage + (b_carriage - a_carriage) * fraction
            if self.held is not None:  # the held piece rides with the effector
                self.piece_offsets[id(self.held)] = piece_start + Vector((
                    (self.carriage_offset - points[0][1]) / 1000, -(self.gantry_offset - points[0][0]) / 1000, 0))
            self.frame = frame
            self._key_rig()
            if follow:  # keep the camera in the same place relative to the effector
                x, y = self._effector_xy()
                self.camera.follow((x - follow_from[0], y - follow_from[1]), frame)
            step = steps[index]
            if step.get("consume_arrow"):
                self.arrows.consume(step["consume_arrow"], (*self._effector_xy(), 0), frame)
            square = self._effector_square()
            if step.get("clear_glows_passed") and self.glows is not None and square != previous_square:
                self.glows.unglow([list(previous_square)], frame)
            previous_square = square
        self.gantry_offset, self.carriage_offset = points[-1]
        self.frame = end_frame
        if follow:
            self.camera.end_follow()
        self.square = parse_square(steps[-1]["move"])

    def _linearize(self):
        """Blender eases between keys by default (Bezier), which smooths the
        motion out; the baked keys must be joined by straight lines instead."""
        objects = list(self.gantry_objects) + [ob for objs in self.pieces.values() for ob in objs]
        if self.held is not None:
            objects += self.held
        if self.arrows is not None:
            self.arrows.finish()
        for ob in objects:
            if ob.animation_data and ob.animation_data.action:
                for fcurve in ob.animation_data.action.fcurves:
                    for key in fcurve.keyframe_points:
                        key.interpolation = "LINEAR"


def animate(parts, pieces, program, fps, duration=None, glows=None, arrows=None, camera=None, markers=None):
    """Keyframes the program; returns the last frame used. Frames reached by
    "marker" steps are filled into `markers` (name -> frame)."""
    return GantryAnimator(parts, pieces, fps, glows, arrows, camera, markers).run(program, duration)
