"""Arrows on the board, e.g. to flag an important move before the gantry
makes it: flat shafts + one head lying just above the acrylic, through a
list of points -- two for a straight arrow, more for one that bends (like
a knight's L, or the gantry's actual path). Points are square centres
("e4" or [file, rank], fractional allowed for corners between squares).

Animated arrows draw in (head leading, from the first point) and fade out
after a hold -- or, with hold=None, stay until a gantry move "consumes"
them: the tail follows the piece being carried along the arrow, so it's
eaten up as the piece travels it. Used by gantry programs ("arrow" steps,
"consume_arrow" on moves) and render.py's --arrow flag. Colours as in
glow.py."""

import math

import bmesh
import bpy
from mathutils import Vector

import glow

DEFAULT_COLOR = "#ff2a2a"
LIFT = 0.0015           # above the acrylic (and above glow tiles)
SHAFT_WIDTH = 0.006
HEAD_WIDTH = 0.016
HEAD_LENGTH = 0.014
DRAW_SECONDS = 0.5
FADE_SECONDS = 0.4
HIDDEN = 1e-4           # scale used for "not visible right now"
LAYER = 0.00005         # height step between an arrow's pieces, so overlaps can't z-fight


def _flat_mesh(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in verts]
    for face in faces:
        bm.faces.new([bm_verts[i] for i in face])
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(None)  # one slot, filled per object (each arrow has its own material)
    return mesh


def _meshes():
    """Unit shaft (x 0..1, scaled to length), a head with its base at x=0,
    and a round joint that fills the gap where two shafts meet at a bend
    (round, so it fits a bend of any angle)."""
    if "arrow shaft" not in bpy.data.meshes:
        w, h = SHAFT_WIDTH / 2, HEAD_WIDTH / 2
        _flat_mesh("arrow shaft", [(0, -w, 0), (1, -w, 0), (1, w, 0), (0, w, 0)], [(0, 1, 2, 3)])
        _flat_mesh("arrow head", [(0, -h, 0), (HEAD_LENGTH, 0, 0), (0, h, 0)], [(0, 1, 2)])
        circle = [(w * math.cos(2 * math.pi * i / 24), w * math.sin(2 * math.pi * i / 24), 0) for i in range(24)]
        _flat_mesh("arrow joint", circle, [tuple(range(24))])
    return bpy.data.meshes["arrow shaft"], bpy.data.meshes["arrow head"], bpy.data.meshes["arrow joint"]


def _material(color, name):
    """Per-arrow material (so each can fade on its own): bright flat colour
    with a little emission so it reads in sunlight, mixed with transparency
    by an 'opacity' value that gets keyframed. Its viewport colour's alpha
    is keyframed too, for Workbench (--draft)."""
    rgba = glow.parse_color(color)
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*rgba[:3], 1.0)
    material.use_nodes = True
    material.blend_method = "BLEND"
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Emission Color"].default_value = rgba
    bsdf.inputs["Emission Strength"].default_value = 1.5
    bsdf.inputs["Roughness"].default_value = 0.4
    opacity = nodes.new("ShaderNodeValue")
    opacity.name = "opacity"
    opacity.outputs[0].default_value = 1.0
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(opacity.outputs[0], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], nodes["Material Output"].inputs["Surface"])
    return material


def _key_opacity(material, frame, value):
    material.node_tree.nodes["opacity"].outputs[0].default_value = value
    material.node_tree.nodes["opacity"].outputs[0].keyframe_insert("default_value", frame=frame)
    material.diffuse_color[3] = value
    material.keyframe_insert("diffuse_color", index=3, frame=frame)


class _Arrow:
    """One arrow's geometry: a shaft per leg, a joint per bend, one head.
    pose(tail, tip) shows the part of the path between those two distances
    along it (metres), with the head ending at `tip`."""

    def __init__(self, name, points, material, collection, width=1.0):
        self.width = width                      # multiplier on shaft/joint/head size
        self.head_length = HEAD_LENGTH * width
        self.points = [Vector(p) for p in points]
        self.legs = [(a, b) for a, b in zip(self.points, self.points[1:]) if (b - a).length > 1e-9]
        self.starts, total = [], 0.0
        for a, b in self.legs:
            self.starts.append(total)
            total += (b - a).length
        self.length = total
        shaft_mesh, head_mesh, joint_mesh = _meshes()

        def make(label, mesh, angle=0.0):
            ob = bpy.data.objects.new(f"{name} {label}", mesh)
            ob.material_slots[0].link = "OBJECT"
            ob.material_slots[0].material = material
            ob.rotation_euler = (0, 0, angle)
            ob.visible_shadow = False
            collection.objects.link(ob)
            return ob

        self.shafts = [make(f"shaft {i}", shaft_mesh, self._angle(i)) for i in range(len(self.legs))]
        self.joints = [make(f"joint {i}", joint_mesh) for i in range(1, len(self.legs))]
        self.head = make("head", head_mesh)
        self.objects = self.shafts + self.joints + [self.head]
        # Each piece a hair above the last: where they overlap at bends one
        # cleanly covers the other instead of flickering through it.
        self.layer = {ob: LAYER * i for i, ob in enumerate(self.objects)}

    def _angle(self, leg):
        a, b = self.legs[leg]
        return math.atan2(b.y - a.y, b.x - a.x)

    def _leg_at(self, distance):
        for index in range(len(self.legs) - 1, -1, -1):
            if distance >= self.starts[index] - 1e-9:
                return index
        return 0

    def point_at(self, distance):
        index = self._leg_at(distance)
        a, b = self.legs[index]
        return a + (b - a).normalized() * (distance - self.starts[index])

    def project(self, point):
        """Distance along the path of the path point closest to `point`."""
        best, best_distance = None, 0.0
        for index, (a, b) in enumerate(self.legs):
            direction = b - a
            t = max(0.0, min(1.0, (Vector(point) - a).xy.dot(direction.xy) / direction.xy.length_squared))
            gap = (a + direction * t - Vector(point)).xy.length
            if best is None or gap < best:
                best, best_distance = gap, self.starts[index] + direction.length * t
        return best_distance

    def pose(self, tail, tip):
        head_scale = max(HIDDEN, min(1.0, (tip - tail) / self.head_length))
        head_leg = self._leg_at(tip - 1e-9)
        a, b = self.legs[head_leg]
        direction = (b - a).normalized()
        self.head.location = self.point_at(tip) - direction * self.head_length * head_scale
        self.head.rotation_euler = (0, 0, self._angle(head_leg))
        self.head.scale = (head_scale * self.width, head_scale * self.width, 1)

        shaft_end = tip - self.head_length * head_scale
        for index, shaft in enumerate(self.shafts):
            leg_start = self.starts[index]
            leg_end = leg_start + (self.legs[index][1] - self.legs[index][0]).length
            start, end = max(tail, leg_start), min(shaft_end, leg_end)
            shaft.location = self.point_at(start) if end > start else self.legs[index][0]
            shaft.scale = (max(end - start, HIDDEN), self.width, 1)
        for index, joint in enumerate(self.joints):
            corner = self.starts[index + 1]
            joint.location = self.legs[index + 1][0]
            visible = tail < corner < shaft_end
            joint.scale = (self.width, self.width, 1) if visible else (HIDDEN, HIDDEN, 1)
        for ob in self.objects:
            ob.location.z += self.layer[ob]

    def key(self, frame):
        for ob in self.objects:
            for path in ("location", "rotation_euler", "scale"):
                ob.keyframe_insert(path, frame=frame)

    def linearize(self):
        """Keys are baked per frame; join them with straight lines, not
        Blender's default easing."""
        for ob in self.objects:
            if ob.animation_data and ob.animation_data.action:
                for fcurve in ob.animation_data.action.fcurves:
                    for key in fcurve.keyframe_points:
                        key.interpolation = "LINEAR"


class Arrows:
    def __init__(self, fps=24):
        self.fps = fps
        self.collection = bpy.data.collections.new("Arrows")
        bpy.context.scene.collection.children.link(self.collection)
        self.count = 0
        self.persistent = {}  # arrow id -> (_Arrow, tail so far), for arrows drawn with hold=None

    def _build(self, squares, color, width=1.0):
        self.count += 1
        material = _material(color, f"arrow {self.count}")
        points = [glow.square_point(square, LIFT) for square in squares]
        return _Arrow(f"arrow {self.count}", points, material, self.collection, width), material

    def add_static(self, squares, color=DEFAULT_COLOR, width=1.0):
        arrow, _ = self._build(squares, color, width)
        arrow.pose(0.0, arrow.length)

    def draw(self, squares, frame, color=DEFAULT_COLOR, hold=1.0, arrow_id=None, width=1.0):
        """Draws in along `squares` from `frame` (head leading), holds `hold`
        seconds, fades out. With hold=None it stays until consume() eats
        it; `arrow_id` names it. `width` scales its thickness (and head)."""
        arrow, material = self._build(squares, color, width)
        drawn = frame + DRAW_SECONDS * self.fps
        steps = max(2, math.ceil(DRAW_SECONDS * self.fps))
        for i in range(steps + 1):
            t = i / steps
            arrow.pose(0.0, arrow.length * t)
            arrow.key(frame + (drawn - frame) * t)
        arrow.linearize()

        if hold is None:
            self.persistent[arrow_id if arrow_id is not None else self.count] = [arrow, 0.0]
            return drawn
        faded_from = drawn + hold * self.fps
        _key_opacity(material, frame, 1.0)
        _key_opacity(material, faded_from, 1.0)
        _key_opacity(material, faded_from + FADE_SECONDS * self.fps, 0.0)
        return faded_from + FADE_SECONDS * self.fps

    def consume(self, arrow_id, point, frame):
        """Moves the arrow's tail to `point` (the carried piece's position,
        projected onto the arrow's path) at `frame`. Near the end the head
        shrinks towards its tip, so the arrow is gone as the piece arrives.
        The tail never moves backwards."""
        entry = self.persistent[arrow_id]
        arrow = entry[0]
        entry[1] = max(entry[1], arrow.project(point))
        arrow.pose(entry[1], arrow.length)
        arrow.key(frame)

    def finish(self):
        """Call once after the last consume(): joins the consumed arrows'
        per-frame keys with straight lines."""
        for arrow, _ in self.persistent.values():
            arrow.linearize()


def parse_cli(spec):
    """--arrow "e1 e3 f3:#ff2a2a" -> (squares, color); two or more squares,
    written like glow.parse_cli."""
    squares, color = glow.parse_cli(spec)
    if len(squares) < 2:
        raise ValueError(f"--arrow needs at least two squares, got {spec!r}")
    return squares, (color if spec.partition(":")[2] else DEFAULT_COLOR)
