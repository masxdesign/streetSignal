"""Test the filtering logic"""
import requests
import config

district = "E1"
params = {
    'q': f"{district}, London, UK",
    'format': 'jsonv2',
    'limit': 10,
    'addressdetails': 1
}

headers = {'User-Agent': config.USER_AGENT}

response = requests.get(
    f"{config.NOMINATIM_BASE_URL}/search",
    params=params,
    headers=headers,
    timeout=10
)

results = response.json()

print(f"Testing postcode filtering for '{district}':")
print("=" * 60)

district_upper = district.upper()
found_match = False

for i, result in enumerate(results, 1):
    address = result.get('address', {})
    postcode = address.get('postcode', 'N/A')

    # Check if postcode starts with the district
    matches = postcode.upper().startswith(district_upper + ' ') or (postcode.upper().startswith(district_upper) and len(postcode) > len(district_upper))

    marker = " <-- MATCH!" if matches else ""

    print(f"\n{i}. Postcode: {postcode}{marker}")
    print(f"   Lat/Lon: {result.get('lat')}, {result.get('lon')}")
    print(f"   Display: {result.get('display_name')[:80]}")

    if matches and not found_match:
        found_match = True
        print(f"\n   ** Would select this result **")

if not found_match:
    print(f"\n\nNo results with postcode starting with '{district}'")
    print("Will fall back to first result (which may be wrong!)")
