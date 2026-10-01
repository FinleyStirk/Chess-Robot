"""Principled BSDF materials, plus which one each CAD part gets.

PART_RULES is matched in order against the lowercased part name (first hit
wins), so put more specific names above general ones."""

import bpy

# name -> Principled BSDF inputs
PALETTE = {
    # Low roughness so it reads as metal (reflections with real contrast)
    # rather than evenly lit white plastic.
    "aluminium":   {"Base Color": (0.78, 0.79, 0.81, 1), "Metallic": 1.0, "Roughness": 0.2},
    "steel":       {"Base Color": (0.62, 0.63, 0.65, 1), "Metallic": 1.0, "Roughness": 0.18},
    "nickel":      {"Base Color": (0.70, 0.67, 0.62, 1), "Metallic": 1.0, "Roughness": 0.12},
    # The magnets in the pieces' bases: darker and less mirror-like than the
    # nickel above. Seen from below they mostly reflect the white carriage
    # right beneath them, so a brighter metal reads as an empty hole.
    "piece_magnet": {"Base Color": (0.2, 0.2, 0.21, 1), "Metallic": 1.0, "Roughness": 0.42},
    "motor":       {"Base Color": (0.035, 0.035, 0.04, 1), "Metallic": 0.7, "Roughness": 0.35},
    "black_plastic": {"Base Color": (0.02, 0.02, 0.02, 1), "Roughness": 0.45},
    # Colours below matched by eye to reference photos of the real robot/pieces.
    "printed":     {"Base Color": (0.19, 0.20, 0.22, 1), "Roughness": 0.6},  # same grey PLA as the grey pieces
    "acrylic":     {"Base Color": (0.95, 0.97, 1.0, 1), "Roughness": 0.03, "Transmission Weight": 1.0, "IOR": 1.49},
    "board":       {"Base Color": (0.95, 0.97, 1.0, 1), "Roughness": 0.02, "Transmission Weight": 1.0, "IOR": 1.49},  # clear acrylic top plate
    "piece_white": {"Base Color": (0.035, 0.24, 0.52, 1), "Roughness": 0.6},  # matte blue PLA
    "piece_black": {"Base Color": (0.19, 0.20, 0.22, 1), "Roughness": 0.6},   # matte cool-grey PLA
    "floor":       {"Base Color": (0.18, 0.185, 0.19, 1), "Roughness": 0.7},
}

# Glass-like materials that shadow rays pass straight through. Without this
# Cycles treats them as opaque to direct light, leaving everything under the
# clear top plate in shadow.
SHADOW_TRANSPARENT = {"acrylic", "board"}

PART_RULES = [
    ("clear plate", "acrylic"),
    ("extrusion cover", "printed"),
    ("aluminium", "aluminium"),
    ("plate 90 degrees", "aluminium"),
    ("x carriage body", "printed"),
    ("y carriage", "printed"),
    ("bracket", "printed"),
    ("spacer", "printed"),
    ("mount", "printed"),
    ("linear rail", "steel"),
    ("bolt", "steel"),
    ("shaft", "steel"),
    ("pulley", "aluminium"),
    ("idler gear", "aluminium"),
    ("magnet", "nickel"),
    ("stepper motor", "motor"),
    ("limit switch", "black_plastic"),
]


def get(name):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        for socket, value in PALETTE[name].items():
            bsdf.inputs[socket].default_value = value
        if name in SHADOW_TRANSPARENT:
            _pass_shadow_rays(material, bsdf)
    return material


def _pass_shadow_rays(material, bsdf):
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes["Material Output"]
    light_path = nodes.new("ShaderNodeLightPath")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(light_path.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    links.new(transparent.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])


def frost_dark_squares(material, a1_corner, square_size, file_ranges=((0, 7),), frosted_roughness=0.35):
    """Frosts the dark squares of a grid on a clear material by driving its
    roughness from world position. a1_corner is the (x, y) world corner of
    a1; ranks (0-7) run along +X, files along +Y, and a1 is dark. Only files
    within file_ranges (inclusive (first, last) pairs, e.g. the board plus
    storage columns) are frosted; the checkerboard pattern carries on
    across all of them."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    clear_roughness = bsdf.inputs["Roughness"].default_value

    def math(operation, *operands):
        node = nodes.new("ShaderNodeMath")
        node.operation = operation
        for socket, value in zip(node.inputs, operands):
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs[0]

    position = nodes.new("ShaderNodeSeparateXYZ")
    links.new(nodes.new("ShaderNodeNewGeometry").outputs["Position"], position.inputs[0])
    rank = math("FLOOR", math("DIVIDE", math("SUBTRACT", position.outputs["X"], a1_corner[0]), square_size))
    file = math("FLOOR", math("DIVIDE", math("SUBTRACT", position.outputs["Y"], a1_corner[1]), square_size))

    def within(index, first, last):
        return math("MULTIPLY", math("GREATER_THAN", index, first - 0.5), math("LESS_THAN", index, last + 0.5))

    file_inside = None
    for first, last in file_ranges:  # ranges don't overlap, so adding them is an OR
        part = within(file, first, last)
        file_inside = part if file_inside is None else math("ADD", file_inside, part)
    inside = math("MULTIPLY", within(rank, 0, 7), file_inside)
    dark = math("SUBTRACT", 1.0, math("FLOORED_MODULO", math("ADD", rank, file), 2.0))
    mask = math("MULTIPLY", inside, dark)

    links.new(math("MULTIPLY_ADD", mask, frosted_roughness - clear_roughness, clear_roughness),
              bsdf.inputs["Roughness"])


def for_part(part_name):
    lowered = part_name.lower()
    for keyword, material in PART_RULES:
        if keyword in lowered:
            return get(material)
    print(f"[materials] no rule for {part_name!r}, using 'printed'")
    return get("printed")
