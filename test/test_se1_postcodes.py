"""
Check what postcodes SE1 POIs have.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import geocode_district, query_overpass, build_retail_query
from collections import Counter

district = "SE1"
coords = geocode_district(district)
lat, lon = coords

print(f"Testing postcode formats for {district}")
print(f"Centroid: ({lat:.6f}, {lon:.6f})")
print("="*60)

# Fetch POIs
poi_query = build_retail_query(
    lat=lat,
    lon=lon,
    radius_m=900,
    include_all_shops=True,
    amenities=["restaurant", "cafe", "fast_food", "pub", "bar", "pharmacy",
               "post_office", "bank", "atm", "hairdresser", "beauty", "marketplace"]
)

poi_data = query_overpass(poi_query)

postcode_prefixes = Counter()
sample_postcodes = []

for element in poi_data.get('elements', []):
    tags = element.get('tags', {})
    postcode = tags.get('addr:postcode', '')

    if postcode:
        # Extract prefix
        if ' ' in postcode:
            prefix = postcode.split()[0].upper()
        else:
            # Try to extract district from postcode without space
            # E.g., "SE17SP" -> "SE1"
            import re
            match = re.match(r'([A-Z]+\d+[A-Z]?)', postcode.upper())
            prefix = match.group(1) if match else postcode[:4].upper()

        postcode_prefixes[prefix] += 1

        if len(sample_postcodes) < 20:
            sample_postcodes.append(postcode)

print(f"\nTotal POIs: {len(poi_data.get('elements', []))}")
print(f"\nPostcode prefix distribution:")
for prefix, count in postcode_prefixes.most_common(15):
    print(f"  {prefix}: {count}")

print(f"\nSample postcodes (first 20):")
for pc in sample_postcodes:
    print(f"  {pc}")
