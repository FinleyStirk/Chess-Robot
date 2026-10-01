"""Downloads the Poly Haven (CC0) assets used by the office room into
render/assets/. Safe to re-run: files already on disk are skipped. Kept to
1k/2k resolutions to save disk space.

    python3 render/fetch_assets.py"""

import json
import os
import urllib.request

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
API = "https://api.polyhaven.com/files/"

MODELS = {
    "metal_office_desk": "2k",
    "classic_laptop": "1k",
    "office_notepads": "1k",
    "potted_plant_04": "1k",
    "desk_lamp_arm_01": "1k",
    "dining_chair_02": "1k",
    "potted_plant_01": "1k",
    "hanging_picture_frame_02": "1k",
    "steel_frame_shelves_02": "1k",
    "book_encyclopedia_set_01": "1k",
}

# texture id -> (resolution, real-world width in metres, from Poly Haven's info)
TEXTURES = {
    "herringbone_parquet": ("1k", 3.4),
    "plastered_wall_04": ("1k", 3.2),
    "wood_table_001": ("1k", 1.5),
}
TEXTURE_MAPS = {"diff": "Diffuse", "nor_gl": "nor_gl", "rough": "Rough"}


def _get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "chess-robot-render"})
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def _download(url, path):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"  {os.path.relpath(path, ASSETS_DIR)}")
    request = urllib.request.Request(url, headers={"User-Agent": "chess-robot-render"})
    with urllib.request.urlopen(request) as response, open(path + ".part", "wb") as out:
        out.write(response.read())
    os.replace(path + ".part", path)


def model_path(asset_id):
    # glTF rather than .blend: Poly Haven's .blend files are saved by a newer
    # Blender than 4.4 can open.
    return os.path.join(ASSETS_DIR, asset_id, f"{asset_id}_{MODELS[asset_id]}.gltf")


def texture_path(texture_id, map_name):
    return os.path.join(ASSETS_DIR, "textures", f"{texture_id}_{map_name}_{TEXTURES[texture_id][0]}.jpg")


def main():
    for asset_id, resolution in MODELS.items():
        print(asset_id)
        gltf = _get_json(API + asset_id)["gltf"][resolution]["gltf"]
        _download(gltf["url"], model_path(asset_id))
        for relative, info in gltf.get("include", {}).items():
            _download(info["url"], os.path.join(ASSETS_DIR, asset_id, relative))
    for texture_id, (resolution, _) in TEXTURES.items():
        print(texture_id)
        files = _get_json(API + texture_id)
        for map_name, api_key in TEXTURE_MAPS.items():
            _download(files[api_key][resolution]["jpg"]["url"], texture_path(texture_id, map_name))


if __name__ == "__main__":
    main()
