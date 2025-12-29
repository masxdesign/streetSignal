"""Test current E1 geocoding"""
from utils import haversine_distance

# Current cached E1 location
e1_lat, e1_lon = 51.5228748, -0.0530633
print(f"Current E1 geocoded location: ({e1_lat}, {e1_lon})")
print("E1 4UF - Cephas Street, Bethnal Green")

# Brick Lane location
brick_lat, brick_lon = 51.5189, -0.0716

distance = haversine_distance(e1_lat, e1_lon, brick_lat, brick_lon)
print(f"\nDistance to Brick Lane: {distance:.0f}m")
print(f"Within 900m radius? {distance <= 900}")

if distance > 900:
    print(f"\nPROBLEM: Brick Lane is {distance - 900:.0f}m OUTSIDE the 900m search radius!")
    print("This is why Brick Lane doesn't appear in results.")

# Test with correct location
correct_lat, correct_lon = 51.5207451, -0.0750553
distance2 = haversine_distance(correct_lat, correct_lon, brick_lat, brick_lon)
print(f"\nWith E1 6UW (Folgate Street): {distance2:.0f}m from Brick Lane")
print(f"Within 900m? {distance2 <= 900}")
