"""Headless render entry point.

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \\
        -P render/render.py -- --shot hero [--draft | --final] [--engine eevee] [--save-blend]

--draft renders with Workbench (flat viewport-style shading, fractions of a
second per frame) for checking framing, timing and motion; the default
Cycles preview and --final are for judging the look.

Add --program render/programs/demo.json to render a video of the gantry
running that program (see gantry.py for the format) instead of a still.
Shots with a "camera_move" render as a video too. Videos are MP4s in
render/out/, or with --frames a numbered WebP frame sequence (for a
scroll-driven website) in render/out/<shot>/.

Rendering on another machine (e.g. a PC with an NVIDIA GPU for the
finals): install the same Blender version (4.4), copy the repo over (it
needs visuals/ and render/, including render/programs/ -- not the robot
code's Python environment), run `python render/fetch_assets.py` there, then

    blender -b --factory-startup -P render/render.py -- --shot office \
        --program render/programs/story_sergey_karjakin_vs_magnus_carlsen.json --frames --final --resume

(On Windows `blender` is "C:\\Program Files\\Blender Foundation\\Blender 4.4\\blender.exe"
unless it's on the PATH; run it from the repo's top folder.)

The GPU is picked automatically (OptiX > CUDA > HIP > Metal, else CPU).
--resume skips frames that already exist, so an interrupted run carries on
(Blender only writes a frame once it's finished). --frame-range START END
renders part of it; --samples N overrides the sample count; --resolution W H
sets the output size (e.g. 1280 720 for web frames); --fps sets frames per
second (everything is timed in seconds, so more fps = more, closer frames).

Blender frame: metres, Z-up. The board's top surface is at z = 0.053 and
white sits on the -X side, with the a-file towards -Y."""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import numpy as np
from mathutils import Matrix, Vector

import arrows
import gantry
import glow
import materials
import office
import scene

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
FLOOR_Z = -0.052  # bottom of the frame
EXPOSURE = -0.5   # Cycles/EEVEE; the user prefers renders a little darker than Blender's default

SHOTS = {
    "hero": {
        "position": None,  # None = starting position, otherwise a FEN
        "environment": "studio",
        "camera": {"location": (-0.50, -0.40, 0.27), "target": (0.0, 0.0, 0.06), "lens_mm": 50},
        "resolution": (1920, 1080),
    },
    "office": {
        "position": None,
        "environment": "office",
        "camera": {"location": (-0.46, -0.70, 0.76), "target": (0.03, -0.01, 0.0), "lens_mm": 35,
                   "focus": (0.0, 0.0, 0.07), "f_stop": 5.6},
        "resolution": (1920, 1080),
    },
    "knight": {
        "position": None,
        "environment": "office",
        # Behind white's g1 knight (y = 0.076), level with the board's
        # files and looking straight down the board towards black.
        "camera": {"location": (-0.29, 0.076, 0.14), "target": (0.12, 0.076, 0.05), "lens_mm": 35,
                   "focus": (-0.103, 0.076, 0.085), "f_stop": 4.0},
        "resolution": (1920, 1080),
    },
    # Scroll-site trial: eases from the office view to behind the g1 knight.
    "office_to_knight": {
        "position": None,
        "environment": "office",
        "camera_move": {"from": "office", "to": "knight", "frames": 120},
        "resolution": (1920, 1080),
    },
    # Roughly white's seat: raised behind white's side, tilted down at the
    # board. Shows the board, both storage areas and
    # the lanes (for the BFS demos). Square-on: centred on the board (y = 0.001).
    "player": {
        "position": None,
        "environment": "office",
        "camera": {"location": (-0.46, 0.001, 0.72), "target": (0.0, 0.001, 0.053), "lens_mm": 38,
                   "focus": (0.0, 0.0, 0.06), "f_stop": 8.0},
        "resolution": (1920, 1080),
    },
    # For demo sections whose program brings its own camera (e.g. move_demo.py's
    # close-up straight down over a move); this camera is only a fallback.
    "closeup": {
        "position": None,
        "environment": "office",
        "camera": {"location": (0.0, 0.0, 0.32), "target": (0.0, 0.0, 0.053), "up": (1, 0, 0), "lens_mm": 35},
        "resolution": (1920, 1080),
    },
    # Top-down like "top" but a normal (perspective) camera, from high above
    # so it looks nearly flat -- this one can be glided to and from.
    "overhead": {
        "position": None,
        "environment": "office",
        "camera": {"location": (0.0, 0.0, 1.3), "target": (0.0, 0.0, 0.053), "up": (1, 0, 0), "lens_mm": 50},
        "resolution": (1920, 1080),
    },
    "top": {
        "position": None,
        "environment": "office",
        # Straight down and orthographic (a true plan view). "up" = +X puts
        # white (-X) at the bottom with the board's long side across the frame.
        "camera": {"location": (0.0, 0.0, 1.2), "target": (0.0, 0.0, 0.0), "up": (1, 0, 0),
                   "ortho_scale": 0.9},  # frame fits (0.47m tall), desk edge just out of shot
        "resolution": (1920, 1080),
    },
}


def add_camera(location, target, lens_mm=50, focus=None, f_stop=None, up=(0, 0, 1), ortho_scale=None):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = lens_mm
    if ortho_scale is not None:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho_scale
    if focus is not None:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = (Vector(focus) - Vector(location)).length
        cam_data.dof.aperture_fstop = f_stop
    cam_data.clip_start = 0.001  # 1 mm: under-board shots sit centimetres from the gantry
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.matrix_world = aim_matrix(location, target, up)
    bpy.context.scene.camera = cam
    return cam


def overhead_camera(above, view_squares=5, lens_mm=35, back_squares=0.0):
    """Camera looking down at a square, white at the bottom of the frame,
    high enough that `view_squares` squares fill the frame's height.
    back_squares moves it back towards white's side (same height, still
    aimed at the square), tilting the view forward up the board."""
    x, y, board_z = glow.square_point(above, 0.0)
    sensor_height = 36.0 * 9 / 16  # Blender's default 36 mm sensor, fitted to a 16:9 frame's width
    height = (view_squares * scene.SQUARE_SIZE_MM / 1000 / 2) * lens_mm / (sensor_height / 2)
    back = back_squares * scene.SQUARE_SIZE_MM / 1000
    return {"location": (x - back, y, board_z + height), "target": (x, y, board_z), "up": (1, 0, 0),
            "lens_mm": lens_mm}


BOARD_UNDERSIDE_Z = 0.050  # bottom face of the acrylic plate (its top is at ~0.053)


def underside_camera(under, looking_at, lens_mm=16, below=0.022, target_below=0.004):
    """Camera beneath the acrylic, under square `under`, looking sideways
    and up at the gantry/underside of the piece on `looking_at`."""
    x, y, _ = glow.square_point(under, 0.0)
    tx, ty, _ = glow.square_point(looking_at, 0.0)
    return {"location": (x, y, BOARD_UNDERSIDE_Z - below), "target": (tx, ty, BOARD_UNDERSIDE_Z - target_below),
            "lens_mm": lens_mm}


def aim_matrix(location, target, up=(0, 0, 1)):
    forward = (Vector(target) - Vector(location)).normalized()
    right = forward.cross(Vector(up)).normalized()
    return Matrix.Translation(location) @ Matrix((right, right.cross(forward), -forward)).transposed().to_4x4()


def resolve_camera(spec):
    """A camera spec -> add_camera() settings. Specs are a shot name
    ("office", "player", "overhead", ...), an overhead spec like
    {"above": "g2", "view_squares": 5, "back_squares": 1.5}, an under-board
    spec like {"under": "d2", "looking_at": "e2"}, or settings."""
    if isinstance(spec, str):
        spec = SHOTS[spec]["camera"]
    if "above" in spec:
        spec = overhead_camera(**spec)
    elif "under" in spec:
        spec = underside_camera(**spec)
    return spec


class CameraRig:
    """Keys camera glides for program "camera" steps. Everything blends --
    position, aim point, lens, focus, f-stop and the up direction (straight-
    down views are oriented with white at the bottom, others upright) --
    eased in and out, baked one key per frame."""

    def __init__(self, cam, spec, fps):
        self.cam, self.fps = cam, fps
        self.cam.data.dof.use_dof = True
        self.current = self._full(spec)
        self._pose(self.current)
        self._key(1)

    @staticmethod
    def _full(spec):
        spec = dict(resolve_camera(spec))
        if spec.get("ortho_scale") is not None:
            raise ValueError("can't glide to/from an orthographic camera -- use \"overhead\" instead of \"top\"")
        spec.setdefault("up", (0, 0, 1))
        spec.setdefault("focus", spec["target"])
        spec.setdefault("f_stop", 22.0)  # no focus given: keep (almost) everything sharp
        return spec

    def _pose(self, settings, previous=None):
        self.cam.matrix_world = aim_matrix(settings["location"], settings["target"], settings["up"])
        if previous is not None:
            self.cam.rotation_euler = self.cam.matrix_world.to_euler("XYZ", previous)  # no flips between frames
        self.cam.data.lens = settings["lens_mm"]
        self.cam.data.dof.focus_distance = (Vector(settings["focus"]) - Vector(settings["location"])).length
        self.cam.data.dof.aperture_fstop = settings["f_stop"]

    def _key(self, frame):
        self.cam.keyframe_insert("location", frame=frame)
        self.cam.keyframe_insert("rotation_euler", frame=frame)
        self.cam.data.keyframe_insert("lens", frame=frame)
        self.cam.data.dof.keyframe_insert("focus_distance", frame=frame)
        self.cam.data.dof.keyframe_insert("aperture_fstop", frame=frame)

    def glide(self, spec, start_frame, seconds):
        start, end = self.current, self._full(spec)
        end_frame = start_frame + max(seconds, 1e-3) * self.fps
        frames = [start_frame] + list(range(math.floor(start_frame) + 1, math.ceil(end_frame))) + [end_frame]
        for frame in frames:
            t = (frame - start_frame) / (end_frame - start_frame)
            t = t * t * (3 - 2 * t)
            blend = {key: Vector(start[key]).lerp(Vector(end[key]), t)
                     for key in ("location", "target", "focus", "up")}
            blend["up"] = blend["up"].normalized()
            blend["lens_mm"] = start["lens_mm"] + (end["lens_mm"] - start["lens_mm"]) * t
            blend["f_stop"] = start["f_stop"] + (end["f_stop"] - start["f_stop"]) * t
            self._pose(blend, self.cam.rotation_euler.copy())
            self._key(frame)
        self.current = end

    def follow(self, offset, frame):
        """Key the camera shifted by `offset` (x, y metres) from where it was
        when the follow began -- for riding along with the gantry."""
        if not hasattr(self, "_follow_base"):
            self._follow_base = self.current
            self._key(frame - 1e-3)  # hold the starting pose right up to the move
        shift = Vector((*offset, 0))
        moved = dict(self._follow_base)
        for key in ("location", "target", "focus"):
            moved[key] = tuple(Vector(self._follow_base[key]) + shift)
        self._pose(moved, self.cam.rotation_euler.copy())
        self._key(frame)
        self.current = moved

    def end_follow(self):
        self.__dict__.pop("_follow_base", None)

    def finish(self):
        """Join the baked keys with straight lines, not Blender's easing."""
        for datablock in (self.cam, self.cam.data):
            if datablock.animation_data and datablock.animation_data.action:
                for fcurve in datablock.animation_data.action.fcurves:
                    for key in fcurve.keyframe_points:
                        key.interpolation = "LINEAR"


def animate_camera(cam, start, end, frames):
    """Keys every frame of an eased (smoothstep) move between two camera
    settings: location, aim point, lens, focus point and f-stop all blend."""
    def lerp(a, b, t):
        return Vector(a).lerp(Vector(b), t)

    for i in range(frames):
        t = i / (frames - 1)
        t = t * t * (3 - 2 * t)
        location = lerp(start["location"], end["location"], t)
        target = lerp(start["target"], end["target"], t)
        focus = lerp(start["focus"], end["focus"], t)
        previous = cam.rotation_euler.copy()
        cam.matrix_world = aim_matrix(location, target)
        cam.rotation_euler = cam.matrix_world.to_euler("XYZ", previous)  # no flips between frames
        cam.data.lens = start["lens_mm"] + (end["lens_mm"] - start["lens_mm"]) * t
        cam.data.dof.focus_distance = (focus - location).length
        cam.data.dof.aperture_fstop = start["f_stop"] + (end["f_stop"] - start["f_stop"]) * t
        frame = i + 1
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)
        cam.data.keyframe_insert("lens", frame=frame)
        cam.data.dof.keyframe_insert("focus_distance", frame=frame)
        cam.data.dof.keyframe_insert("aperture_fstop", frame=frame)
    return frames


def write_markers(markers, name, frames):
    """Marker frames for the website, next to the video/frames."""
    if not markers:
        return
    path = os.path.join(OUT_DIR, name, "markers.json") if frames else os.path.join(OUT_DIR, f"{name}.markers.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(markers, f, indent=1)
    print(f"[render] wrote {path}")


def render_video(name, final, fps, frames=False, save_blend=False, resume=False):
    sc = bpy.context.scene
    sc.render.fps = fps
    if resume and not frames:
        raise SystemExit("--resume needs --frames (an MP4 can't be continued)")
    if frames:
        # With resume, frames already on disk are skipped. No placeholders:
        # a frame only appears once it's fully rendered, so an interrupted
        # frame is simply rendered again.
        sc.render.use_overwrite = not resume
        sc.render.use_placeholder = False
        sc.render.image_settings.file_format = "WEBP"
        sc.render.image_settings.quality = 85
        frames_dir = os.path.join(OUT_DIR, name)
        os.makedirs(frames_dir, exist_ok=True)
        sc.render.filepath = os.path.join(frames_dir, f"{name}_")  # Blender appends 0001, 0002, ...
    else:
        sc.render.image_settings.file_format = "FFMPEG"
        sc.render.ffmpeg.format = "MPEG4"
        sc.render.ffmpeg.codec = "H264"
        sc.render.ffmpeg.constant_rate_factor = "HIGH" if final else "MEDIUM"
        sc.render.filepath = os.path.join(OUT_DIR, f"{name}.mp4")
    if save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, f"{name}.blend"))
    print(f"[render] {sc.frame_end - sc.frame_start + 1} frames")
    bpy.ops.render.render(animation=True)
    print(f"[render] wrote {sc.render.filepath}")


def add_area_light(name, location, target, power, size, color=(1, 1, 1)):
    light_data = bpy.data.lights.new(name, "AREA")
    light_data.energy = power
    light_data.size = size
    light_data.color = color
    light = bpy.data.objects.new(name, light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()


def add_studio():
    # Big floor so it reads as an infinite surface at this focal length.
    mesh = bpy.data.meshes.new("Floor")
    s = 20
    mesh.from_pydata([(-s, -s, FLOOR_Z), (s, -s, FLOOR_Z), (s, s, FLOOR_Z), (-s, s, FLOOR_Z)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new("Floor", mesh)
    floor.data.materials.append(materials.get("floor"))
    bpy.context.scene.collection.objects.link(floor)

    target = (0, 0, 0.03)
    add_area_light("Key", (-0.9, -1.1, 1.3), target, power=55, size=1.2, color=(1.0, 0.96, 0.92))
    add_area_light("Fill", (-1.2, 0.9, 0.6), target, power=12, size=1.5, color=(0.9, 0.95, 1.0))
    add_area_light("Rim", (1.1, 0.4, 0.9), target, power=45, size=0.8)

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.022, 0.025, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = world


def _image_average(image):
    pixels = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    return pixels.reshape(-1, 4)[:, :3].mean(0)


def _upstream_image(socket):
    """First image texture feeding a socket, looking back through the node graph."""
    for link in socket.links:
        node = link.from_node
        if node.type == "TEX_IMAGE" and node.image:
            return node.image
        for upstream in node.inputs:
            image = _upstream_image(upstream)
            if image:
                return image
    return None


def sync_viewport_colors():
    """Workbench only sees each material's viewport colour, so copy the real
    base colour across (a texture's average colour if it's image-driven);
    see-through materials get a low alpha."""
    for material in bpy.data.materials:
        if not material.node_tree:
            continue
        bsdf = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        base = bsdf.inputs["Base Color"]
        image = _upstream_image(base)
        rgb = _image_average(image) if image else base.default_value[:3]
        clear = not bsdf.inputs["Transmission Weight"].is_linked and bsdf.inputs["Transmission Weight"].default_value > 0.5
        material.diffuse_color = (*rgb, 0.2 if clear else 1.0)
        material.metallic = bsdf.inputs["Metallic"].default_value if not bsdf.inputs["Metallic"].is_linked else 0.0
        material.roughness = bsdf.inputs["Roughness"].default_value if not bsdf.inputs["Roughness"].is_linked else 0.5


def configure_render(resolution, final, engine, video=False, samples=None):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = resolution
    sc.render.resolution_percentage = 100 if final else 50
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = EXPOSURE
    sc.render.image_settings.file_format = "PNG"

    if engine == "workbench":
        sc.render.engine = "BLENDER_WORKBENCH"
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        sc.view_settings.exposure = 1.3  # studio light alone is dim inside the closed room
        shading = sc.display.shading
        shading.light = "STUDIO"
        shading.color_type = "MATERIAL"
        shading.show_shadows = True
        shading.shadow_intensity = 0.35
        shading.show_cavity = True
        shading.use_dof = True
        sc.display.light_direction = (-0.55, 0.3, 0.78)  # roughly the window's side
        sc.display.render_aa = "8"
        sync_viewport_colors()
        return

    if engine == "eevee":
        # Much faster per frame than Cycles -- meant for video.
        sc.render.engine = "BLENDER_EEVEE_NEXT"
        sc.eevee.taa_render_samples = 64 if final else 16
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
        return

    sc.render.engine = "CYCLES"
    backend = use_best_gpu()
    sc.cycles.device = "GPU" if backend else "CPU"
    sc.cycles.samples = samples or ((256 if video else 512) if final else (12 if video else 64))
    sc.render.use_persistent_data = True  # keep the scene on the GPU between video frames
    sc.cycles.use_denoising = True
    if backend == "OPTIX":
        sc.cycles.denoiser = "OPTIX"  # NVIDIA's own, GPU-accelerated
    print(f"[render] Cycles on {backend or 'CPU'}, {sc.cycles.samples} samples")


GPU_BACKENDS = ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL")  # most preferred first


def use_best_gpu():
    """Turns on every GPU of the best backend this machine has; returns the
    backend's name, or None if there's no usable GPU (render on CPU)."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in GPU_BACKENDS:
        try:
            prefs.compute_device_type = backend
        except TypeError:  # backend not available in this Blender build/OS
            continue
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == backend]
        if gpus:
            for device in prefs.devices:
                device.use = device.type == backend
            return backend
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--shot", default="hero", choices=SHOTS)
    parser.add_argument("--final", action="store_true", help="full resolution, 512 samples")
    parser.add_argument("--draft", action="store_true", help="fast Workbench render for checking framing/motion")
    parser.add_argument("--save-blend", action="store_true", help="also save the scene as a .blend to open in the GUI")
    parser.add_argument("--engine", default="cycles", choices=["cycles", "eevee", "workbench"])
    parser.add_argument("--program", help="JSON gantry program; renders an MP4 of it")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--glow", action="append", default=[], metavar='"SQUARES[:COLOR]"',
                        help='light squares for the whole render, e.g. --glow "e4 e5 10,3:#ff7a1a" (repeatable)')
    parser.add_argument("--arrow", action="append", default=[], metavar='"FROM TO[:COLOR]"',
                        help='static arrow for the whole render, e.g. --arrow "e1 f2" (repeatable)')
    parser.add_argument("--markers-only", action="store_true",
                        help="with --program: just work out and write the marker frames, don't render")
    parser.add_argument("--duration", type=float,
                        help="with --program: total video length in seconds; the gantry speed is set so the "
                             "program fills it, ending on a 0.5 s hold")
    parser.add_argument("--frames", action="store_true", help="write videos as a WebP frame sequence in render/out/<shot>/ instead of an MP4")
    parser.add_argument("--suffix", default="", help="appended to the output filename")
    parser.add_argument("--resume", action="store_true",
                        help="with --frames: skip frames already rendered (carry on an interrupted render)")
    parser.add_argument("--frame-range", type=int, nargs=2, metavar=("START", "END"),
                        help="render only these frames of a video (inclusive)")
    parser.add_argument("--samples", type=int, help="override the Cycles sample count")
    parser.add_argument("--resolution", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"),
                        help="output size (default: the shot's 1920x1080; previews/drafts render at half)")
    args = parser.parse_args(argv)
    if args.draft:
        args.engine = "workbench"

    shot = SHOTS[args.shot]
    program = gantry.load_program(args.program) if args.program else None
    fen = (program or {}).get("position") or shot["position"]  # a program can set its own start position
    placement = scene.fen_position(fen) if fen else scene.starting_position()
    for item in (program or {}).get("storage", []):  # pieces already sitting in storage slots
        placement[tuple(item["square"])] = scene.piece_from_symbol(item["piece"])
    parts, pieces = scene.build(placement)
    if shot["environment"] == "office":
        office.build_office(desk_top_z=FLOOR_Z)
    else:
        add_studio()
    glows = glow.Glows(args.fps)
    for spec in shot.get("glows", []):
        glows.add_static(spec["squares"], spec.get("color", glow.DEFAULT_COLOR))
    for spec in args.glow:
        glows.add_static(*glow.parse_cli(spec))
    board_arrows = arrows.Arrows(args.fps)
    for spec in args.arrow:
        board_arrows.add_static(*arrows.parse_cli(spec))

    move = shot.get("camera_move")
    camera_spec = SHOTS[move["from"]]["camera"] if move else (program or {}).get("camera") or shot["camera"]
    cam = add_camera(**resolve_camera(camera_spec))  # a program's own "camera" overrides the shot's
    has_camera_steps = any("camera" in step for step in (program or {}).get("steps", []))
    rig = CameraRig(cam, camera_spec, args.fps) if has_camera_steps else None
    configure_render(tuple(args.resolution) if args.resolution else shot["resolution"], args.final, args.engine,
                     video=bool(args.program or move), samples=args.samples)

    os.makedirs(OUT_DIR, exist_ok=True)
    suffix = ("_draft" if args.draft else "" if args.final else "_preview") \
        + ("_eevee" if args.engine == "eevee" else "") + args.suffix

    if args.program or move:
        sc = bpy.context.scene
        last_frame = 1
        name = args.shot
        if move:
            last_frame = animate_camera(cam, SHOTS[move["from"]]["camera"], SHOTS[move["to"]]["camera"], move["frames"])
        markers = {}
        if args.program:
            if args.duration:
                gantry.animate(parts, pieces, program, args.fps, duration=args.duration - 0.5, glows=glows,
                               arrows=board_arrows, camera=rig, markers=markers)
                last_frame = max(last_frame, round(args.duration * args.fps))
            else:
                last_frame = max(last_frame, gantry.animate(parts, pieces, program, args.fps, glows=glows,
                                                            arrows=board_arrows, camera=rig,
                                                            markers=markers) + args.fps)  # 1 s hold
            if rig is not None:
                rig.finish()
            name += "_" + os.path.splitext(os.path.basename(args.program))[0]
        sc.frame_start, sc.frame_end = 1, last_frame
        write_markers(markers, name + suffix, args.frames)
        if args.frame_range:
            sc.frame_start, sc.frame_end = max(1, args.frame_range[0]), min(last_frame, args.frame_range[1])
        if not args.markers_only:
            render_video(name + suffix, args.final, args.fps, args.frames, args.save_blend, args.resume)
        return
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, f"{args.shot}.blend"))
    bpy.context.scene.render.filepath = os.path.join(OUT_DIR, f"{args.shot}{suffix}.png")
    bpy.ops.render.render(write_still=True)
    print(f"[render] wrote {bpy.context.scene.render.filepath}")


main()
