"""Find the best center point for E1 that includes Brick Lane"""
from utils import haversine_distance

# Brick Lane location
brick_lane = (51.5189, -0.0716)

# Candidate E1 centers from Nominatim results
candidates = [
    ("E1W 2BB - Wapping", 51.508859, -0.0612435),
    ("E1 4UF - Cephas Street", 51.5228748, -0.0530633),
    ("E1 6UW - Folgate Street", 51.5207451, -0.0750553),
    ("E1 6HU - Shoreditch High St", 51.5244153, -0.0771173),
    ("E1 1AA - Whitechapel Rd", 51.5189063, -0.0580314),
    ("E1 4NP - Mile End", 51.5251118, -0.0391318),
]

print("Testing which E1 center point is closest to Brick Lane:")
print("=" * 70)

best_distance = float('inf')
best_candidate = None

for name, lat, lon in candidates:
    distance = haversine_distance(lat, lon, brick_lane[0], brick_lane[1])
    marker = " <-- BEST!" if distance < best_distance else ""
    if distance < best_distance:
        best_distance = distance
        best_candidate = (name, lat, lon)

    print(f"\n{name}")
    print(f"  Coords: ({lat}, {lon})")
    print(f"  Distance to Brick Lane: {distance:.0f}m")
    print(f"  Within 900m? {distance <= 900}{marker}")

print("\n" + "=" * 70)
print(f"\nBest center: {best_candidate[0]}")
print(f"Distance to Brick Lane: {best_distance:.0f}m")

if best_distance > 900:
    print(f"\nNOTE: Even the best center is {best_distance:.0f}m from Brick Lane")
    print(f"To include Brick Lane, need radius of at least {best_distance + 200:.0f}m")
