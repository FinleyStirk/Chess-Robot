"""Minimal 3MF reader: meshes plus the object/component tree, no Blender
dependency. Everything stays in the file's own frame (millimetres, Y-up
for these SolidWorks exports) -- scene.py does the conversion to Blender."""

import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import numpy as np

CORE_NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"


@dataclass
class Object3MF:
    id: int
    name: str
    vertices: np.ndarray | None = None   # (N, 3) float
    triangles: np.ndarray | None = None  # (M, 3) int
    components: list[tuple[int, np.ndarray]] = field(default_factory=list)  # (object id, 4x4)


@dataclass
class Model3MF:
    objects: dict[int, Object3MF]
    build: list[tuple[int, np.ndarray]]


def parse_transform(text: str | None) -> np.ndarray:
    """3MF stores a 3x4 row-vector matrix (p' = p . M); return the
    equivalent column-vector 4x4."""
    matrix = np.identity(4)
    if text:
        values = [float(v) for v in text.split()]
        matrix[:3, :3] = np.array(values[:9]).reshape(3, 3).T
        matrix[:3, 3] = values[9:12]
    return matrix


def load(path: str) -> Model3MF:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("3D/3dmodel.model"))

    objects = {}
    for element in root.iter(f"{CORE_NS}object"):
        obj = Object3MF(id=int(element.get("id")), name=element.get("name", ""))
        mesh = element.find(f"{CORE_NS}mesh")
        if mesh is not None:
            obj.vertices = np.array(
                [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
                 for v in mesh.iter(f"{CORE_NS}vertex")])
            obj.triangles = np.array(
                [(int(t.get("v1")), int(t.get("v2")), int(t.get("v3")))
                 for t in mesh.iter(f"{CORE_NS}triangle")], dtype=np.int32)
        components = element.find(f"{CORE_NS}components")
        if components is not None:
            obj.components = [(int(c.get("objectid")), parse_transform(c.get("transform")))
                              for c in components.iter(f"{CORE_NS}component")]
        objects[obj.id] = obj

    build = [(int(item.get("objectid")), parse_transform(item.get("transform")))
             for item in root.iter(f"{CORE_NS}item")]
    return Model3MF(objects, build)


def leaves(model: Model3MF, object_id: int, matrix: np.ndarray):
    """Yield (mesh object, accumulated 4x4) for every mesh under object_id."""
    obj = model.objects[object_id]
    if obj.vertices is not None and len(obj.triangles):
        yield obj, matrix
    for child_id, child_matrix in obj.components:
        yield from leaves(model, child_id, matrix @ child_matrix)
