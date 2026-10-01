"""A small modelled home office around the robot: real walls/floor/ceiling
with a window, a desk and furniture from Poly Haven (fetch_assets.py), lit
by a sun coming through the window plus a ceiling fill. Everything is
geometry -- no photo backdrop -- so the camera can move freely for video.

Layout (metres, Blender Z-up): the robot stays where scene.py puts it, the
desk top meets the robot's frame bottom, the desk's back edge is against
the back wall (+Y), and the window is in the right-hand wall (+X)."""

import math

import bmesh
import bpy
from mathutils import Vector

import fetch_assets

DESK_TOP_HEIGHT = 0.788  # metal_office_desk, measured from the model
WOOD_TOP_THICKNESS = 0.025  # how far down from the top the wood goes (the top panel)

ROOM_X = (-2.3, 1.9)
ROOM_Y = (-3.2, 0.52)      # back wall face sits just behind the desk
ROOM_HEIGHT = 2.6
WALL_THICKNESS = 0.12
WINDOW_Y = (-1.7, -0.3)    # in the right-hand wall
WINDOW_Z = (0.85, 2.25)    # above the floor
SUN_DIRECTION = Vector((-0.9, 0.35, -0.36))  # travel direction; lands a sun patch across the board

# asset id -> placement. "on": "desk" is relative to the desk top (desk
# centre at x = y = 0), "floor" relative to the floor.
PROPS = {
    "classic_laptop":   {"on": "desk", "location": (-0.62, 0.12), "rotation_deg": 28, "scale": 0.55},
    "potted_plant_04":  {"on": "desk", "location": (0.52, 0.28), "rotation_deg": 0},
    "desk_lamp_arm_01": {"on": "desk", "location": (0.80, 0.15), "rotation_deg": -140},
    # The file lays several items out around its origin; keep two and place
    # the origin so they land front-right of the robot.
    "office_notepads":  {"on": "desk", "location": (0.28, -0.43), "rotation_deg": 8,
                         "keep": ["office_notepads_yellow_pad", "office_notepads_note_stack"]},
    "dining_chair_02":  {"on": "floor", "location": (0.55, -0.95), "rotation_deg": 200},
    "potted_plant_01":  {"on": "floor", "location": (1.55, 0.15), "rotation_deg": 40},
    "steel_frame_shelves_02": {"on": "floor", "location": (-1.55, 0.25), "rotation_deg": 0},
}


# --- helpers -----------------------------------------------------------------

def import_model(asset_id, keep=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=fetch_assets.model_path(asset_id))
    imported = [ob for ob in bpy.data.objects if ob not in before]
    if keep is not None:
        for ob in [ob for ob in imported if ob.type == "MESH" and ob.name not in keep]:
            imported.remove(ob)
            bpy.data.objects.remove(ob)
    root = bpy.data.objects.new(asset_id, None)
    bpy.context.scene.collection.objects.link(root)
    for ob in imported:
        if ob.parent is None:
            ob.parent = root
    return root


def box(name, lo, hi, material):
    """Axis-aligned box in world coordinates (object at the origin, so the
    materials' object-space texture mapping is world-space too)."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector([lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)])
    bm.to_mesh(mesh)
    bm.free()
    ob = bpy.data.objects.new(name, mesh)
    ob.data.materials.append(material)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def textured_material(name, texture_id, tint=(1, 1, 1, 1), saturation=1.0, value=1.0, bump=1.0):
    """Poly Haven texture, box-projected in world space at its real size."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    texture_into(material, material.node_tree.nodes["Principled BSDF"], texture_id, tint, saturation, value, bump)
    return material


def texture_into(material, bsdf, texture_id, tint=(1, 1, 1, 1), saturation=1.0, value=1.0, bump=1.0):
    """Wires a Poly Haven texture (colour, roughness, normal) into `bsdf`,
    box-projected in the object's own space at the texture's real size."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    coords = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / fetch_assets.TEXTURES[texture_id][1],) * 3
    links.new(coords.outputs["Object"], mapping.inputs["Vector"])

    def image(map_name, non_color):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(fetch_assets.texture_path(texture_id, map_name), check_existing=True)
        if non_color:
            node.image.colorspace_settings.name = "Non-Color"
        node.projection = "BOX"
        node.projection_blend = 0.2
        links.new(mapping.outputs["Vector"], node.inputs["Vector"])
        return node

    hsv = nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = saturation
    hsv.inputs["Value"].default_value = value
    links.new(image("diff", False).outputs["Color"], hsv.inputs["Color"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs["B"].default_value = tint
    links.new(hsv.outputs["Color"], mix.inputs["A"])
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])

    links.new(image("rough", True).outputs["Color"], bsdf.inputs["Roughness"])
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = bump
    links.new(image("nor_gl", True).outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])


def wooden_desktop(desk_root):
    """Gives the metal desk a varnished wooden top: everything in the desk's
    top few cm (the top panel) uses wood; the frame and drawers stay metal.
    Done in the desk's own material so the desk height doesn't change."""
    desk = next(ob for ob in desk_root.children if ob.type == "MESH" and ob.name.startswith("metal_office_desk")
                and "drawer" not in ob.name and "tray" not in ob.name)
    material = desk.active_material.copy()
    desk.active_material = material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    metal = output.inputs["Surface"].links[0].from_socket

    wood = nodes.new("ShaderNodeBsdfPrincipled")
    texture_into(material, wood, "wood_table_001")
    wood.inputs["Coat Weight"].default_value = 0.35  # varnish

    coords = nodes.new("ShaderNodeTexCoord")
    xyz = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Object"], xyz.inputs[0])
    is_top = nodes.new("ShaderNodeMath")
    is_top.operation = "GREATER_THAN"
    is_top.inputs[1].default_value = DESK_TOP_HEIGHT - WOOD_TOP_THICKNESS
    links.new(xyz.outputs["Z"], is_top.inputs[0])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(is_top.outputs[0], mix.inputs["Fac"])
    links.new(metal, mix.inputs[1])
    links.new(wood.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Surface"])


def plain_material(name, color, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def look_rotation(direction):
    return direction.to_track_quat("-Z", "Y").to_euler()


def shelf_tops(shelves, max_height):
    """World z of each shelf board, found by casting rays straight down
    through the unit's centre (saves hard-coding the model's shelf heights)."""
    mesh_obs = [ob for ob in shelves.children_recursive if ob.type == "MESH"]
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    x, y, z = shelves.location.x, shelves.location.y, shelves.location.z + max_height + 0.1
    tops = []
    while True:
        hit, location, _, _, ob, _ = bpy.context.scene.ray_cast(depsgraph, Vector((x, y, z)), Vector((0, 0, -1)))
        if not hit or ob not in mesh_obs:
            break
        tops.append(location.z)
        z = location.z - 0.03  # step through the board
    return tops


# --- room --------------------------------------------------------------------

def build_room(floor_z):
    (x0, x1), (y0, y1), t = ROOM_X, ROOM_Y, WALL_THICKNESS
    top = floor_z + ROOM_HEIGHT
    wall = textured_material("wall", "plastered_wall_04", tint=(0.95, 0.93, 0.89, 1), saturation=0.2, value=1.5, bump=0.3)
    floor = textured_material("floor", "herringbone_parquet")
    trim = plain_material("trim", (0.85, 0.85, 0.83, 1), 0.35)

    box("Floor", (x0 - t, y0 - t, floor_z - t), (x1 + t, y1 + t, floor_z), floor)
    box("Ceiling", (x0 - t, y0 - t, top), (x1 + t, y1 + t, top + t), wall)
    box("Wall back", (x0 - t, y1, floor_z), (x1 + t, y1 + t, top), wall)
    box("Wall front", (x0 - t, y0 - t, floor_z), (x1 + t, y0, top), wall)
    box("Wall left", (x0 - t, y0, floor_z), (x0, y1, top), wall)

    # Right wall, built around the window opening.
    wy0, wy1 = WINDOW_Y
    wz0, wz1 = floor_z + WINDOW_Z[0], floor_z + WINDOW_Z[1]
    box("Wall right a", (x1, y0, floor_z), (x1 + t, wy0, top), wall)
    box("Wall right b", (x1, wy1, floor_z), (x1 + t, y1, top), wall)
    box("Wall right sill", (x1, wy0, floor_z), (x1 + t, wy1, wz0), wall)
    box("Wall right head", (x1, wy0, wz1), (x1 + t, wy1, top), wall)

    # Window frame + one mullion and transom; no glass so the sun comes straight in.
    f, ym = 0.045, (wy0 + wy1) / 2
    box("Window sill", (x1 - 0.04, wy0 - f, wz0 - 0.03), (x1 + t, wy1 + f, wz0), trim)
    for name, lo, hi in [
        ("Frame bottom", (x1, wy0, wz0), (x1 + t, wy1, wz0 + f)),
        ("Frame top", (x1, wy0, wz1 - f), (x1 + t, wy1, wz1)),
        ("Frame left", (x1, wy0, wz0), (x1 + t, wy0 + f, wz1)),
        ("Frame right", (x1, wy1 - f, wz0), (x1 + t, wy1, wz1)),
        ("Mullion", (x1 + 0.03, ym - f / 2, wz0), (x1 + 0.08, ym + f / 2, wz1)),
        ("Transom", (x1 + 0.03, wy0, wz1 - 0.42), (x1 + 0.08, wy1, wz1 - 0.42 + f)),
    ]:
        box(name, lo, hi, trim)

    # Skirting boards.
    s, h = 0.015, 0.08
    box("Skirting back", (x0, y1 - s, floor_z), (x1, y1, floor_z + h), trim)
    box("Skirting front", (x0, y0, floor_z), (x1, y0 + s, floor_z + h), trim)
    box("Skirting left", (x0, y0, floor_z), (x0 + s, y1, floor_z + h), trim)
    box("Skirting right a", (x1 - s, y0, floor_z), (x1, wy0, floor_z + h), trim)
    box("Skirting right b", (x1 - s, wy0, floor_z), (x1, y1, floor_z + h), trim)

    # Garden outside the window: ground so the view out isn't a void.
    box("Garden", (x1 + t, -40, floor_z - 0.4), (x1 + 60, 40, floor_z - 0.3),
        plain_material("garden", (0.09, 0.14, 0.05, 1), 0.9))


def build_lighting(floor_z):
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.55, 0.72, 1.0, 1)
    background.inputs["Strength"].default_value = 1.5
    bpy.context.scene.world = world

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 12
    sun_data.angle = math.radians(1.5)
    sun_data.color = (1.0, 0.93, 0.84)
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = look_rotation(SUN_DIRECTION)
    bpy.context.scene.collection.objects.link(sun)

    # Portal over the window: tells Cycles where sky light enters (less noise).
    x1 = ROOM_X[1]
    portal_data = bpy.data.lights.new("Window portal", "AREA")
    portal_data.shape = "RECTANGLE"
    portal_data.size = WINDOW_Y[1] - WINDOW_Y[0]
    portal_data.size_y = WINDOW_Z[1] - WINDOW_Z[0]
    portal_data.cycles.is_portal = True
    portal = bpy.data.objects.new("Window portal", portal_data)
    portal.location = (x1 + WALL_THICKNESS / 2, sum(WINDOW_Y) / 2, floor_z + sum(WINDOW_Z) / 2)
    portal.rotation_euler = look_rotation(Vector((-1, 0, 0)))
    bpy.context.scene.collection.objects.link(portal)

    # Soft ceiling fill so the far side of the room isn't black.
    fill_data = bpy.data.lights.new("Ceiling fill", "AREA")
    fill_data.shape = "RECTANGLE"
    fill_data.size, fill_data.size_y = 1.4, 1.0
    fill_data.energy = 60
    fill_data.color = (1.0, 0.95, 0.88)
    fill = bpy.data.objects.new("Ceiling fill", fill_data)
    fill.location = (sum(ROOM_X) / 2, -1.0, floor_z + ROOM_HEIGHT - 0.02)
    bpy.context.scene.collection.objects.link(fill)


def build_furniture(desk_top_z, floor_z):
    desk = import_model("metal_office_desk")
    desk.location = (0, 0, floor_z)
    wooden_desktop(desk)

    placed = {}
    for asset_id, prop in PROPS.items():
        root = import_model(asset_id, prop.get("keep"))
        root.location = (*prop["location"], desk_top_z if prop["on"] == "desk" else floor_z)
        root.rotation_euler = (0, 0, math.radians(prop["rotation_deg"]))
        root.scale = (prop.get("scale", 1.0),) * 3
        placed[asset_id] = root

    # Books on the second shelf down; picture above the desk.
    tops = shelf_tops(placed["steel_frame_shelves_02"], 2.2)
    if len(tops) >= 2:
        books = import_model("book_encyclopedia_set_01")
        books.location = (ROOM_X[0] + 0.5, 0.25, tops[1])
    picture = import_model("hanging_picture_frame_02")
    picture.location = (-0.15, ROOM_Y[1] - 0.001, floor_z + 1.75)


def build_office(desk_top_z):
    floor_z = desk_top_z - DESK_TOP_HEIGHT
    build_room(floor_z)
    build_lighting(floor_z)
    build_furniture(desk_top_z, floor_z)
