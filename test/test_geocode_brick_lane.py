"""Check geocoding for E1 and Brick Lane location"""
import requests
import config

# Test E1 geocoding
district = "E1"
params = {
    'q': f"{district}, London, UK",
    'format': 'jsonv2',
    'limit': 5,
    'addressdetails': 1
}

headers = {
    'User-Agent': config.USER_AGENT
}

print(f"Querying: {params['q']}")
print("=" * 60)

response = requests.get(
    f"{config.NOMINATIM_BASE_URL}/search",
    params=params,
    headers=headers,
    timeout=10
)

if response.ok:
    results = response.json()
    print(f"\nFound {len(results)} results for 'E1, London, UK':\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.get('display_name')}")
        print(f"   Lat/Lon: {r.get('lat')}, {r.get('lon')}")
        print(f"   Type: {r.get('type')}")
        addr = r.get('address', {})
        print(f"   Postcode: {addr.get('postcode', 'N/A')}")
        print()

# Check where Brick Lane actually is
print("\n" + "=" * 60)
print("Checking Brick Lane location:")
print("=" * 60)

params2 = {
    'q': "Brick Lane, London, E1",
    'format': 'jsonv2',
    'limit': 1
}

response2 = requests.get(
    f"{config.NOMINATIM_BASE_URL}/search",
    params=params2,
    headers=headers,
    timeout=10
)

if response2.ok:
    results2 = response2.json()
    if results2:
        r = results2[0]
        print(f"\nBrick Lane location:")
        print(f"   {r.get('display_name')}")
        print(f"   Lat/Lon: {r.get('lat')}, {r.get('lon')}")

        # Calculate if it's within 900m of the E1 geocoded point
        from utils import haversine_distance
        e1_lat, e1_lon = 51.5554478, -0.0238945
        brick_lat, brick_lon = float(r.get('lat')), float(r.get('lon'))

        distance = haversine_distance(e1_lat, e1_lon, brick_lat, brick_lon)
        print(f"\n   Distance from geocoded E1 center: {distance:.0f}m")
        print(f"   Within 900m radius? {distance <= 900}")
