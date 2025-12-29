"""Debug geocoding"""
import requests
import config

district = "E1"
params = {
    'q': f"{district} postcode district London",
    'format': 'json',
    'limit': 5,
    'countrycodes': 'gb',
    'addressdetails': 1
}

headers = {
    'User-Agent': config.USER_AGENT
}

print(f"User-Agent: {config.USER_AGENT}")
print(f"Query: {params['q']}")
print("\nSending request...")

response = requests.get(
    f"{config.NOMINATIM_BASE_URL}/search",
    params=params,
    headers=headers,
    timeout=10
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.ok:
    results = response.json()
    print(f"\nFound {len(results)} results:")
    for i, r in enumerate(results):
        print(f"\n  {i+1}. {r.get('display_name')}")
        print(f"      Lat/Lon: {r.get('lat')}, {r.get('lon')}")
        print(f"      Type: {r.get('type')}")
