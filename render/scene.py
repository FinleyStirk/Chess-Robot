"""Builds the chess robot scene in Blender from the 3MF files in visuals/.

Placement is ported from visuals/viewer.html (board offset/rotation, piece
heights and pivot fixes, square grid) and done in that viewer's frame --
millimetres, Y-up -- then converted once by VIEWER_TO_BLENDER into
Blender's metres, Z-up. So every constant below can be compared 1:1 with
viewer.html."""

import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

import threemf
import materials

VISUALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visuals")
ASSEMBLY_FILE = "Chess Robot Assembly.3MF"
PIECES_FILE = "Cyan and aluminium full set.3MF"
BOARD_FILE = "temp full board top plate.3MF"

# viewer (x, y, z) mm, Y-up  ->  Blender (x, -z, y) m, Z-up
VIEWER_TO_BLENDER = np.array([
    [0.001, 0, 0, 0],
    [0, 0, -0.001, 0],
    [0, 0.001, 0, 0],
    [0, 0, 0, 1],
])

# --- from viewer.html ---
BOARD_POSITION = (-40, 50, -90)
BOARD_ROTATION_Y_DEG = 90
PIECE_SET_POSITION = (0, 55, 0)
SQUARE_SIZE_MM = 30
BOARD_ORIGIN = {"x": -106, "z": 104}
# Captured-piece storage columns, from PieceStorage in chess_robot/utils/structs.py:
# black's pieces/pawns in files -3/-2, white's pawns/pieces in 9/10 (ranks 0-7).
STORAGE_FILE_RANGES = ((-3, -2), (9, 10))
STANDARD_BACK_ROW = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
PIECE_INITIAL_Y = {"rook": 58.30, "knight": 57.20, "bishop": 60.20, "king": 61.00, "queen": 56.50, "pawn": 59.10}
PIECE_LOCAL_OFFSET_X = {"rook": -5.8828, "knight": -2.5684, "bishop": 0.7883, "king": -0.7573, "queen": -1.2440, "pawn": -3.3079}


def translate(x, y, z):
    matrix = np.identity(4)
    matrix[:3, 3] = (x, y, z)
    return matrix


def rotate_y(degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    matrix = np.identity(4)
    matrix[0, 0], matrix[0, 2], matrix[2, 0], matrix[2, 2] = c, s, -s, c
    return matrix


def clean_name(name):
    return name.replace("(Default)Display State 1", "").replace(" - Cyan and aluminium", "").strip()


def square_viewer_xz(file, rank):
    return BOARD_ORIGIN["x"] + rank * SQUARE_SIZE_MM, BOARD_ORIGIN["z"] - file * SQUARE_SIZE_MM


class SceneBuilder:
    def __init__(self):
        self._mesh_cache = {}  # (file, object id) -> bpy mesh, so repeated parts share data
        self._models = {}

    def model(self, filename):
        if filename not in self._models:
            self._models[filename] = threemf.load(os.path.join(VISUALS_DIR, filename))
        return self._models[filename]

    def _mesh(self, filename, obj):
        key = (filename, obj.id)
        if key not in self._mesh_cache:
            mesh = bpy.data.meshes.new(obj.name or f"mesh{obj.id}")
            mesh.from_pydata(obj.vertices.tolist(), [], obj.triangles.tolist())
            mesh.validate()
            mesh.shade_smooth()
            mesh.set_sharp_from_angle(angle=math.radians(35))
            mesh.materials.append(None)  # one slot, filled per object (shared meshes differ in colour)
            self._mesh_cache[key] = mesh
        return self._mesh_cache[key]

    def add(self, filename, object_id, viewer_matrix, name, collection, material):
        """Instance every mesh under object_id, placed at viewer_matrix (viewer frame)."""
        created = []
        for leaf, leaf_matrix in threemf.leaves(self.model(filename), object_id, viewer_matrix):
            ob = bpy.data.objects.new(name, self._mesh(filename, leaf))
            ob.matrix_world = Matrix((VIEWER_TO_BLENDER @ leaf_matrix).tolist())
            ob["part"] = name
            ob.material_slots[0].link = "OBJECT"
            ob.material_slots[0].material = material
            collection.objects.link(ob)
            created.append(ob)
        return created


def _collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _viewer_aabb_center(model, object_id):
    """Replicates THREE.Box3.setFromObject (non-precise): union of each mesh's
    local AABB corners after transforming them to world."""
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for leaf, matrix in threemf.leaves(model, object_id, np.identity(4)):
        a, b = leaf.vertices.min(0), leaf.vertices.max(0)
        corners = np.array([[x, y, z, 1] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])])
        world = (matrix @ corners.T).T[:, :3]
        lo, hi = np.minimum(lo, world.min(0)), np.maximum(hi, world.max(0))
    return (lo + hi) / 2


def build_assembly(builder):
    """Returns one dict per part instance: name, type_index (its order among
    same-named parts, as viewer.html counts them), its Blender objects, and
    its origin in the viewer frame (what three.js calls the part's position)."""
    col = _collection("Assembly")
    model = builder.model(ASSEMBLY_FILE)
    root_id, root_matrix = model.build[0]
    # The viewer recentres the assembly on its bounding box; board and pieces
    # are positioned relative to that recentred frame.
    center = _viewer_aabb_center(model, root_id)
    base = translate(*-center) @ root_matrix
    parts, seen = [], {}
    for part_id, part_matrix in model.objects[root_id].components:
        name = clean_name(model.objects[part_id].name)
        matrix = base @ part_matrix
        objects = builder.add(ASSEMBLY_FILE, part_id, matrix, name, col, materials.for_part(name))
        parts.append({"name": name, "type_index": seen.get(name, 0), "objects": objects,
                      "viewer_origin": matrix[:3, 3].copy()})
        seen[name] = seen.get(name, 0) + 1
    return parts


def build_board(builder):
    col = _collection("Board")
    model = builder.model(BOARD_FILE)
    root_id, root_matrix = model.build[0]
    placement = translate(*BOARD_POSITION) @ rotate_y(BOARD_ROTATION_Y_DEG) @ root_matrix
    material = materials.get("board")
    # Same grid the pieces are placed on (square_viewer_xz), converted to
    # Blender: viewer x -> x, viewer z -> -y, mm -> m. Offset by half a
    # square from a1's centre to its corner.
    a1_x, a1_z = square_viewer_xz(0, 0)
    half = SQUARE_SIZE_MM / 2
    materials.frost_dark_squares(material, ((a1_x - half) / 1000, (-a1_z - half) / 1000), SQUARE_SIZE_MM / 1000,
                                 file_ranges=((0, 7), *STORAGE_FILE_RANGES))
    builder.add(BOARD_FILE, root_id, placement, "Board", col, material)
    return col


def piece_templates(builder):
    """piece type -> (object id, 3x3 rotation baked into the set file)."""
    model = builder.model(PIECES_FILE)
    root_id, _ = model.build[0]
    templates = {}
    for piece_id, piece_matrix in model.objects[root_id].components:
        rotation = np.identity(4)
        rotation[:3, :3] = piece_matrix[:3, :3]
        templates[clean_name(model.objects[piece_id].name).lower()] = (piece_id, rotation)
    return templates


MAGNET_RADIUS_MM = 2.65  # covers the ~2.57 mm magnet pocket in every piece's base
MAGNET_INSET_MM = 0.1    # just inside the base, so it reads as sitting in the pocket


def _magnet_mesh(builder, piece_id):
    """Disc filling the magnet pocket in a piece's base, in the piece mesh's
    own coordinates: centred on the pocket, just above the base's bottom."""
    key = ("magnet", piece_id)
    if key not in builder._mesh_cache:
        model = builder.model(PIECES_FILE)
        leaf, _ = next(threemf.leaves(model, piece_id, np.identity(4)))
        v = leaf.vertices
        bottom = v[:, 1].min()
        base = v[np.abs(v[:, 1] - bottom) < 0.05]  # the flat bottom face (an annulus round the pocket)
        cx = (base[:, 0].min() + base[:, 0].max()) / 2
        cz = (base[:, 2].min() + base[:, 2].max()) / 2
        y = bottom + MAGNET_INSET_MM
        circle = [(cx + MAGNET_RADIUS_MM * math.cos(a), y, cz + MAGNET_RADIUS_MM * math.sin(a))
                  for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
        mesh = bpy.data.meshes.new(f"magnet {piece_id}")
        mesh.from_pydata(circle, [], [tuple(range(32))])
        mesh.materials.append(materials.get("piece_magnet"))
        builder._mesh_cache[key] = mesh
    return builder._mesh_cache[key]


def build_pieces(builder, placement):
    """placement: {(file, rank): (piece type, is_white)} -- file/rank 0-7.
    Returns {(file, rank): [Blender objects]}."""
    col = _collection("Pieces")
    templates = piece_templates(builder)
    pieces = {}
    for (file, rank), (kind, is_white) in placement.items():
        piece_id, rotation = templates[kind]
        x, z = square_viewer_xz(file, rank)
        if kind == "knight" and is_white:
            rotation = rotate_y(180) @ rotation  # white's knights face the other way (see viewer.html)
        matrix = translate(x, PIECE_INITIAL_Y[kind], z) @ rotation @ translate(-PIECE_LOCAL_OFFSET_X[kind], 0, 0)
        where = f"{'abcdefgh'[file]}{rank + 1}" if 0 <= file <= 7 else f"storage {file},{rank}"
        name = f"{'white' if is_white else 'black'} {kind} {where}"
        objects = builder.add(PIECES_FILE, piece_id, matrix, name, col,
                              materials.get("piece_white" if is_white else "piece_black"))
        # The magnet in the base's pocket -- part of the piece, so it moves with it.
        magnet = bpy.data.objects.new(f"{name} magnet", _magnet_mesh(builder, piece_id))
        magnet.matrix_world = Matrix((VIEWER_TO_BLENDER @ matrix).tolist())
        col.objects.link(magnet)
        pieces[(file, rank)] = objects + [magnet]
    return pieces


def starting_position():
    placement = {}
    for file in range(8):
        placement[(file, 0)] = (STANDARD_BACK_ROW[file], True)
        placement[(file, 1)] = ("pawn", True)
        placement[(file, 6)] = ("pawn", False)
        placement[(file, 7)] = (STANDARD_BACK_ROW[file], False)
    return placement


PIECE_NAMES = {"p": "pawn", "n": "knight", "b": "bishop", "r": "rook", "q": "queen", "k": "king"}


def piece_from_symbol(symbol):
    """FEN letter -> (piece type, is_white), e.g. "q" -> ("queen", False)."""
    return PIECE_NAMES[symbol.lower()], symbol.isupper()


def fen_position(fen):
    placement = {}
    for row_index, row in enumerate(fen.split()[0].split("/")):
        file = 0
        for char in row:
            if char.isdigit():
                file += int(char)
            else:
                placement[(file, 7 - row_index)] = piece_from_symbol(char)
                file += 1
    return placement


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build(placement=None):
    """Returns (assembly parts, pieces) -- see build_assembly/build_pieces."""
    reset_scene()
    builder = SceneBuilder()
    parts = build_assembly(builder)
    build_board(builder)
    pieces = build_pieces(builder, placement or starting_position())
    return parts, pieces


def world_bounds(objects=None):
    objects = objects or [o for o in bpy.context.scene.objects if o.type == "MESH"]
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for ob in objects:
        corners = np.array([tuple(ob.matrix_world @ Vector(c)) for c in ob.bound_box])
        lo, hi = np.minimum(lo, corners.min(0)), np.maximum(hi, corners.max(0))
    return lo, hi
