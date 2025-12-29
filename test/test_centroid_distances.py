"""
Check distance from district centroids to Albert Embankment.
"""

import json
import math

# Load geocode cache
with open('geocode_cache.json', 'r') as f:
    geocode_cache = json.load(f)

# Albert Embankment approximate coordinates (near Lambeth Bridge)
albert_embankment_lat = 51.4925
albert_embankment_lon = -0.1235

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two points using Haversine formula."""
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

print("Distance from district centroids to Albert Embankment:")
print("="*60)

for district in ['SE1', 'SE11']:
    if district in geocode_cache:
        coords = geocode_cache[district]
        lat = coords['lat']
        lon = coords['lon']

        distance = haversine_distance(lat, lon, albert_embankment_lat, albert_embankment_lon)

        print(f"\n{district}:")
        print(f"  Centroid: ({lat:.6f}, {lon:.6f})")
        print(f"  Distance to Albert Embankment: {distance:.0f}m")
        print(f"  Within 900m radius: {'YES' if distance <= 900 else 'NO'}")
