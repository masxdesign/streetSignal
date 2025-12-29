"""Test better geocoding strategies for E1"""
import requests
import config

headers = {'User-Agent': config.USER_AGENT}

queries = [
    "E1, London, UK",
    "E1 postcode district, London",
    "E1 postcode area, London, UK",
    "Tower Hamlets E1, London",
]

for query in queries:
    print(f"\nQuery: '{query}'")
    print("=" * 60)

    params = {
        'q': query,
        'format': 'jsonv2',
        'limit': 3,
        'addressdetails': 1
    }

    response = requests.get(
        f"{config.NOMINATIM_BASE_URL}/search",
        params=params,
        headers=headers,
        timeout=10
    )

    if response.ok:
        results = response.json()
        for i, r in enumerate(results, 1):
            addr = r.get('address', {})
            postcode = addr.get('postcode', 'N/A')
            print(f"  {i}. {r.get('lat')}, {r.get('lon')} - {postcode}")
            print(f"     {r.get('display_name')[:100]}")
