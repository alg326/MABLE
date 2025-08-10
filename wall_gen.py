import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# === Load existing GeoJSON ===
with open('hstf1.geojson', 'r') as f:
    geojson_data = json.load(f)

features = geojson_data['features']

# === Extract room polygons ===
room_polys = [
    shape(f['geometry'])
    for f in features
    if f['geometry']['type'] == 'Polygon' and f['properties'].get('class') == 'room'
]

# === Wall generation (per room) ===
room_buffer_distance = 0.0001  # adjust for thickness of interior walls
wall_features = []

for room in room_polys:
    try:
        outer = room.buffer(room_buffer_distance)
        wall_ring = outer.difference(room)
        if not wall_ring.is_empty:
            wall_features.append({
                "type": "Feature",
                "geometry": mapping(wall_ring),
                "properties": {"class": "wall"}
            })
    except Exception as e:
        print(f"⚠️ Skipped invalid room geometry: {e}")

print(f"Added {len(wall_features)} wall rings around individual rooms")

# === Building outline and exterior wall ===
try:
    # Union all rooms into one shape
    building_union = unary_union(room_polys)

    # Optional: add the building outline shape as its own feature
    outline_feature = {
        "type": "Feature",
        "geometry": mapping(building_union),
        "properties": {"class": "outline"}
    }
    features.append(outline_feature)
    print("Added building outline feature")

    # Create exterior wall by buffering outward from the building shape
    exterior_buffer_distance = 0.0002
    exterior = building_union.buffer(exterior_buffer_distance)
    exterior_wall = exterior.difference(building_union)

    if not exterior_wall.is_empty:
        wall_features.append({
            "type": "Feature",
            "geometry": mapping(exterior_wall),
            "properties": {"class": "wall"}
        })
        print("Added exterior wall ring around entire building")

except Exception as e:
    print(f"Failed to generate building exterior: {e}")

# === Save updated GeoJSON ===
features.extend(wall_features)
geojson_data['features'] = features

with open('edited.geojson', 'w') as f:
    json.dump(geojson_data, f, indent=2)

print("GeoJSON updated with interior walls, exterior wall ring, and building outline")