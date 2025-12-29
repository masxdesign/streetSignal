"""Test the new postcodes.io geocoding"""
from utils import geocode_district, haversine_distance

print("Testing postcodes.io geocoding for E1...")
print("=" * 60)

result = geocode_district('E1')
print(f"\nGeocoded E1 to: {result}")

if result:
    lat, lon = result
    print(f"Latitude: {lat}")
    print(f"Longitude: {lon}")

    # Check distance to Brick Lane
    brick_lat, brick_lon = 51.5189, -0.0716
    distance = haversine_distance(lat, lon, brick_lat, brick_lon)
    print(f"\nDistance to Brick Lane: {distance:.0f}m")
    print(f"Within 900m radius? {distance <= 900}")

    if distance <= 900:
        print("\n✓ SUCCESS: Brick Lane should appear in results!")
    else:
        print(f"\n✗ PROBLEM: Brick Lane is {distance - 900:.0f}m outside the 900m radius")
else:
    print("ERROR: Geocoding failed!")

print("\n" + "=" * 60)
print("Testing a few more districts...")
print("=" * 60)

for district in ['SE1', 'W1D', 'SW1']:
    coords = geocode_district(district)
    if coords:
        print(f"{district}: {coords}")
    else:
        print(f"{district}: FAILED")
