"""
Check how many POIs have postcode tags in the data.
"""

import requests
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import geocode_district, query_overpass, build_retail_query

BASE_URL = "http://127.0.0.1:5000"

district = "SE11"
coords = geocode_district(district)
lat, lon = coords

print(f"Testing postcode coverage for {district}")
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

total_pois = 0
pois_with_postcode = 0
pois_with_se11 = 0
pois_with_se1 = 0
pois_with_other = 0
albert_emb_pois = []

for element in poi_data.get('elements', []):
    tags = element.get('tags', {})
    total_pois += 1

    postcode = tags.get('addr:postcode', '')
    street = tags.get('addr:street', '')

    if postcode:
        pois_with_postcode += 1
        district_prefix = postcode.split()[0].upper() if ' ' in postcode else postcode[:len(district)]

        if district_prefix == 'SE11':
            pois_with_se11 += 1
        elif district_prefix == 'SE1':
            pois_with_se1 += 1
        else:
            pois_with_other += 1

    # Track Albert Embankment POIs
    if street and 'Albert Embankment' in street:
        albert_emb_pois.append({
            'name': tags.get('name', 'Unnamed'),
            'postcode': postcode,
            'street': street,
            'shop': tags.get('shop', ''),
            'amenity': tags.get('amenity', '')
        })

print(f"\nTotal POIs fetched: {total_pois}")
print(f"POIs with postcode tag: {pois_with_postcode} ({100*pois_with_postcode/total_pois:.1f}%)")
print(f"POIs without postcode: {total_pois - pois_with_postcode} ({100*(total_pois-pois_with_postcode)/total_pois:.1f}%)")
print(f"\nPostcode breakdown:")
print(f"  SE11: {pois_with_se11}")
print(f"  SE1: {pois_with_se1}")
print(f"  Other: {pois_with_other}")

print(f"\n\nAlbert Embankment POIs found: {len(albert_emb_pois)}")
for poi in albert_emb_pois:
    print(f"  - {poi['name']}")
    print(f"    Postcode: {poi['postcode'] or 'NONE'}")
    print(f"    Type: {poi['shop'] or poi['amenity'] or 'unknown'}")
