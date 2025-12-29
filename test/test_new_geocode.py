"""Test new geocoding without importing utils first"""
import os
import json

# Delete cache FIRST before any imports
cache_file = "geocode_cache.json"
if os.path.exists(cache_file):
    os.remove(cache_file)
    print(f"Deleted {cache_file}")

# Now import
from utils import geocode_district

print("\nTesting geocoding for E1 with fresh cache...")
result = geocode_district('E1')
print(f"Result: {result}")

if result:
    lat, lon = result
    print(f"Latitude: {lat}")
    print(f"Longitude: {lon}")
    print("\nThis should be around Whitechapel/Spitalfields area (Brick Lane)")
    print("Expected: lat ~51.52, lon ~-0.06 to -0.07")

    # Check distance to Brick Lane
    from utils import haversine_distance
    brick_lane_lat, brick_lane_lon = 51.5189, -0.0716
    distance = haversine_distance(lat, lon, brick_lane_lat, brick_lane_lon)
    print(f"\nDistance to Brick Lane: {distance:.0f}m")
    print(f"Within 900m radius? {distance <= 900}")
else:
    print("ERROR: Geocoding failed!")

# Show what was cached
if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
        print(f"\nCached data: {json.dumps(cache_data, indent=2)}")
