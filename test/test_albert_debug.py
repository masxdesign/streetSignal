"""
Debug Albert Embankment POI postcodes in SE11.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import geocode_district, query_overpass, build_retail_query

district = "SE11"
coords = geocode_district(district)
lat, lon = coords

print(f"Debugging Albert Embankment POIs in {district}")
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

albert_emb_pois = []

for element in poi_data.get('elements', []):
    tags = element.get('tags', {})
    street = tags.get('addr:street', '')
    postcode = tags.get('addr:postcode', '')

    if street and 'Albert Embankment' in street:
        # Check if it passes the postcode filter
        passes_filter = True
        if postcode:
            postcode_upper = postcode.upper().replace(' ', '')
            if not postcode_upper.startswith("SE11"):
                passes_filter = False

        albert_emb_pois.append({
            'name': tags.get('name', 'Unnamed'),
            'postcode': postcode or 'NONE',
            'shop': tags.get('shop', ''),
            'amenity': tags.get('amenity', ''),
            'passes_filter': passes_filter
        })

print(f"\nTotal Albert Embankment POIs found: {len(albert_emb_pois)}")
print(f"\nPOI details:")
for i, poi in enumerate(albert_emb_pois, 1):
    status = "[KEPT]" if poi['passes_filter'] else "[FILTERED]"
    print(f"{i}. {status} {poi['name']}")
    print(f"   Postcode: {poi['postcode']}")
    print(f"   Type: {poi['shop'] or poi['amenity'] or 'unknown'}")

kept_count = sum(1 for p in albert_emb_pois if p['passes_filter'])
filtered_count = sum(1 for p in albert_emb_pois if not p['passes_filter'])

print(f"\nSummary:")
print(f"  Kept (no postcode or SE11 postcode): {kept_count}")
print(f"  Filtered (SE1 postcode): {filtered_count}")
print(f"  Total: {len(albert_emb_pois)}")
