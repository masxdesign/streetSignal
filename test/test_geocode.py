"""Test geocoding for E1"""
from utils import geocode_district

print("Testing geocoding for E1...")
result = geocode_district('E1')
print(f"Result: {result}")

if result:
    lat, lon = result
    print(f"Latitude: {lat}")
    print(f"Longitude: {lon}")
    print("\nThis should be around Whitechapel/Shoreditch area")
    print("Expected: lat ~51.51, lon ~-0.06")
else:
    print("ERROR: Geocoding failed!")
