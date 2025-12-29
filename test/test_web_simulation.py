"""Simulate what the web app does when processing E1"""
import sys
import json

# Check what's in the cache
print("Current geocode cache:")
with open('geocode_cache.json', 'r') as f:
    cache = json.load(f)
    print(json.dumps(cache, indent=2))

# Now import and process like the web app does
from processor import DistrictProcessor
import config

print("\n" + "=" * 60)
print("Simulating Web App Request for E1")
print("=" * 60)

preset = config.PRESETS['shop']

processor = DistrictProcessor(
    district='E1',
    radius_m=900,
    max_assign_m=200.0,
    include_all_shops=preset['include_all_shops'],
    shop_types=preset.get('shop_types', []),
    amenities=preset.get('amenities', []),
    property_selectors=preset.get('property_selectors', [])
)

result = processor.process()

print("\nResult:")
print(f"  Success: {result['success']}")
print(f"  Total POIs: {result['total_pois']}")
print(f"  Total Streets: {result['total_streets_found']}")
print(f"\nTop 3 Streets:")
print(f"  1. {result['street_1']} ({result['count_1']} POIs)")
print(f"  2. {result['street_2']} ({result['count_2']} POIs)")
print(f"  3. {result['street_3']} ({result['count_3']} POIs)")

# Check if Brick Lane is there
if 'brick lane' in result['street_1'].lower():
    print("\n✓ Brick Lane found as #1 street!")
elif 'brick lane' in result['street_2'].lower():
    print("\n✓ Brick Lane found as #2 street!")
elif 'brick lane' in result['street_3'].lower():
    print("\n✓ Brick Lane found as #3 street!")
else:
    print("\n✗ Brick Lane NOT in top 3 streets!")
    print(f"\nGeocoded center used: {processor.center_coords}")

    # Check distance to Brick Lane
    from utils import haversine_distance
    if processor.center_coords:
        lat, lon = processor.center_coords
        brick_lat, brick_lon = 51.5189, -0.0716
        distance = haversine_distance(lat, lon, brick_lat, brick_lon)
        print(f"Distance from center to Brick Lane: {distance:.0f}m")
        print(f"Within 900m radius? {distance <= 900}")
