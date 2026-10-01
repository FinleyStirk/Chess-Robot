"""Glowing squares on the board: soft-edged emissive tiles just above the
acrylic, one per square, that can be switched on/off over time (they grow
in and shrink out). Used by gantry programs ("glow"/"unglow" steps), shot
definitions ("glows") and render.py's --glow flag.

Squares use the same coordinates as gantry programs: "e4" or [file, rank],
so off-board storage slots like [10, 3] work too. Colours are "#rrggbb" or
[r, g, b] in 0-1, both sRGB (as a colour picker shows them)."""

import bpy
import bmesh

import gantry
import scene

BOARD_TOP_Z = 0.0532       # acrylic top surface (m), tiles sit just above it
TILE_SIZE = 0.029          # a touch under the 30 mm square so neighbours read as separate
EMISSION_STRENGTH = 10.0  # much higher and AgX burns colours (esp. blues) out to white
FADE_SECONDS = 0.15
DEFAULT_COLOR = "#2fd3ff"


def parse_color(color):
    """sRGB hex or [r, g, b] -> linear RGBA for Blender."""
    if isinstance(color, str):
        color = color.lstrip("#")
        color = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in color[:3]]
    return (*linear, 1.0)


def _material(color):
    """One material per colour: emission fading out towards the tile's edges
    (via its generated coordinates) over a transparent base."""
    rgba = parse_color(color)
    name = "glow " + ",".join(f"{c:.3f}" for c in rgba[:3])
    material = bpy.data.materials.get(name)
    if material:
        return material
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*rgba[:3], 1.0)  # what Workbench (--draft) shows
    material.use_nodes = True
    material.blend_method = "BLEND"
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()

    coords = nodes.new("ShaderNodeTexCoord")
    xyz = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Generated"], xyz.inputs[0])

    def centred(axis):  # |coord - 0.5|, 0 at the tile centre, 0.5 at its edge
        sub = nodes.new("ShaderNodeMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = 0.5
        links.new(xyz.outputs[axis], sub.inputs[0])
        absolute = nodes.new("ShaderNodeMath")
        absolute.operation = "ABSOLUTE"
        links.new(sub.outputs[0], absolute.inputs[0])
        return absolute.outputs[0]

    edge = nodes.new("ShaderNodeMath")
    edge.operation = "MAXIMUM"
    links.new(centred("X"), edge.inputs[0])
    links.new(centred("Y"), edge.inputs[1])
    falloff = nodes.new("ShaderNodeMapRange")  # solid in the middle, soft towards the edges
    falloff.interpolation_type = "SMOOTHSTEP"
    falloff.inputs["From Min"].default_value = 0.28
    falloff.inputs["From Max"].default_value = 0.5
    falloff.inputs["To Min"].default_value = 1.0
    falloff.inputs["To Max"].default_value = 0.0
    links.new(edge.outputs[0], falloff.inputs["Value"])

    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = rgba
    emission.inputs["Strength"].default_value = EMISSION_STRENGTH
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(falloff.outputs["Result"], mix.inputs["Fac"])
    links.new(transparent.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs["Shader"], output.inputs["Surface"])
    return material


def _tile_mesh():
    mesh = bpy.data.meshes.get("glow tile")
    if mesh is None:
        mesh = bpy.data.meshes.new("glow tile")
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=TILE_SIZE / 2)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(None)  # one slot, filled per object (colour varies)
    return mesh


def square_point(square, lift=0.0004):
    """Centre of a square ("e4" or [file, rank]) in Blender coordinates,
    `lift` metres above the acrylic."""
    file, rank = gantry.parse_square(square)
    x, z = scene.square_viewer_xz(file, rank)
    return x / 1000, -z / 1000, BOARD_TOP_Z + lift


def _key(square):
    """Same square, same key, whether given as "e2", [4, 1] or [4.0, 1.0]."""
    return tuple(float(v) for v in gantry.parse_square(square))


class Glows:
    """Creates and animates glowing squares. Frames are Blender frames; a
    tile with no keyframes is simply always on (for stills)."""

    def __init__(self, fps=24):
        self.fps = fps
        self.collection = bpy.data.collections.new("Glows")
        bpy.context.scene.collection.children.link(self.collection)
        self.active = {}  # square key -> tile object currently lit
        self._bloom_added = False

    def _add_bloom(self):
        """Soft halo around bright things (the tiles) via the compositor's
        Fog Glow, added once the first tile exists. High threshold so the
        rest of the image is left alone."""
        if self._bloom_added:
            return
        self._bloom_added = True
        sc = bpy.context.scene
        sc.use_nodes = True
        nodes, links = sc.node_tree.nodes, sc.node_tree.links
        layers = nodes.get("Render Layers") or nodes.new("CompositorNodeRLayers")
        composite = nodes.get("Composite") or nodes.new("CompositorNodeComposite")
        glare = nodes.new("CompositorNodeGlare")
        glare.glare_type = "FOG_GLOW"
        glare.quality = "HIGH"
        glare.threshold = 2.5
        glare.size = 7
        glare.mix = -0.6  # mostly the original image, a little glow
        links.new(layers.outputs["Image"], glare.inputs["Image"])
        links.new(glare.outputs["Image"], composite.inputs["Image"])

    def _tile(self, square, color):
        ob = bpy.data.objects.new(f"glow {square}", _tile_mesh())
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = _material(color)
        ob.location = square_point(square)
        ob.visible_shadow = False
        self.collection.objects.link(ob)
        self._add_bloom()
        return ob

    def add_static(self, squares, color=DEFAULT_COLOR):
        return [self._tile(square, color) for square in squares]

    def _key_scale(self, ob, frame, on):
        ob.scale = (1, 1, 1) if on else (1e-4, 1e-4, 1)
        ob.keyframe_insert("scale", frame=frame)

    def glow(self, squares, frame, color=DEFAULT_COLOR, hold=None):
        """Light squares from `frame`; with `hold` (seconds) they go out again
        after that, otherwise they stay lit until unglow()."""
        fade = FADE_SECONDS * self.fps
        for square in squares:
            key = _key(square)
            self.unglow([square], frame)  # re-lighting a square replaces its old tile
            ob = self._tile(square, color)
            self._key_scale(ob, frame, False)
            self._key_scale(ob, frame + fade, True)
            if hold is not None:
                self._key_scale(ob, frame + fade + hold * self.fps, True)
                self._key_scale(ob, frame + 2 * fade + hold * self.fps, False)
            else:
                self.active[key] = ob

    def unglow(self, squares, frame):
        """Put squares out from `frame`; squares="all" clears every lit one."""
        keys = list(self.active) if squares == "all" else [_key(s) for s in squares]
        for key in keys:
            ob = self.active.pop(key, None)
            if ob is not None:
                self._key_scale(ob, frame, True)
                self._key_scale(ob, frame + FADE_SECONDS * self.fps, False)


def parse_cli(spec):
    """--glow "e4 e5 10,3:#ff7a1a" -> (squares, color). Squares are space
    separated, each "e4" or "file,rank"; the colour is optional."""
    squares_part, _, color = spec.partition(":")
    squares = [[float(v) for v in token.split(",")] if "," in token else token
               for token in squares_part.split()]
    return squares, (color or DEFAULT_COLOR)
