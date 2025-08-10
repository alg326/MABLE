import os
import json
from pathlib import Path
from shapely.geometry import Polygon, Point, box
from shapely.errors import TopologicalError
from PIL import Image

# === CONFIGURATION ===
class_id_map = {
    0: "room",
    1: "door",
    2: "window"
}

# === Coordinate Conversion ===
def pixel_to_latlon(x, y, image_size, bounding_box):
    img_w, img_h = image_size
    left, top, width, height = bounding_box
    lon = left + (x / img_w) * width
    lat = top - (y / img_h) * height
    return [lon, lat]

# === Polygon Orthogonalization ===
def orthogonalize_polygon(poly):
    minx, miny, maxx, maxy = poly.bounds
    return box(minx, miny, maxx, maxy)

# === Segmentation Label Parser ===
def parse_segmentation_label(label_path, image_size, bounding_box, class_map):
    img_w, img_h = image_size
    features = []
    if not os.path.exists(label_path):
        return features
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            class_id = int(parts[0])
            coords = list(map(float, parts[1:]))
            polygon = [(coords[i] * img_w, coords[i + 1] * img_h) for i in range(0, len(coords), 2)]
            poly = Polygon(polygon)
            ortho_poly = orthogonalize_polygon(poly)
            if not ortho_poly or not ortho_poly.is_valid or ortho_poly.area == 0:
                continue
            latlon_coords = [pixel_to_latlon(x, y, image_size, bounding_box) for x, y in ortho_poly.exterior.coords]
            features.append({
                "type": "Feature",
                "properties": {"class": class_map[class_id]},
                "geometry": {"type": "Polygon", "coordinates": [latlon_coords]}
            })
    return features

# === Bounding Box Label Parser ===
def parse_bbox_label(label_path, image_size, bounding_box, class_map):
    img_w, img_h = image_size
    features = []
    if not os.path.exists(label_path):
        return features
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            class_id = int(parts[0])
            if class_id not in class_map:
                continue
            x_c, y_c, w, h = map(float, parts[1:])
            x_center = x_c * img_w
            y_center = y_c * img_h
            lon, lat = pixel_to_latlon(x_center, y_center, image_size, bounding_box)
            features.append({
                "type": "Feature",
                "properties": {"class": class_map[class_id]},
                "geometry": {"type": "Point", "coordinates": [lon, lat]}
            })
    return features

# === Main Conversion Function ===
def convert_labels_to_geojson(seg_file, box_file, output_path, image_path, class_map):
    with Image.open(image_path) as img:
        img_w, img_h = img.size
        image_size = (img_w, img_h)

        # Compute bounding box based on real aspect ratio
        left = -0.01
        top = 0.01
        height = 0.02
        width = height * (img_w / img_h)
        bounding_box = (left, top, width, height)

    features = []
    features.extend(parse_segmentation_label(seg_file, image_size, bounding_box, class_map))
    features.extend(parse_bbox_label(box_file, image_size, bounding_box, class_map))

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(output_path, 'w') as out:
        json.dump(geojson, out, indent=2)

# === Example Usage ===
image_name = ""
image_path = f""
seg_label_file = f""
box_label_file = f""
output_geojson_path = ""

convert_labels_to_geojson(seg_label_file, box_label_file, output_geojson_path, image_path, class_id_map)