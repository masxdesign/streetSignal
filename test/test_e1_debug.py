"""Debug E1 to see why Brick Lane isn't included"""
from processor import DistrictProcessor
import config

print("=" * 60)
print("Debugging E1 District - Looking for Brick Lane")
print("=" * 60)

preset = config.PRESETS['shop']

processor = DistrictProcessor(
    district='E1',
    radius_m=900,
    max_assign_m=200.0,
    include_all_shops=preset['include_all_shops'],
    shop_types=preset.get('shop_types', []),
    amenities=preset.get('amenities', []),
    property_selectors=preset.get('property_selectors', [])
)

# Process
from utils import geocode_district, query_overpass, build_retail_query, build_highway_query

coords = geocode_district('E1')
print(f"\nGeocoded E1 to: {coords}")

if coords:
    lat, lon = coords

    # Fetch POIs
    poi_query = build_retail_query(
        lat=lat,
        lon=lon,
        radius_m=900,
        include_all_shops=preset['include_all_shops'],
        shop_types=preset.get('shop_types', []),
        amenities=preset.get('amenities', []),
        property_selectors=preset.get('property_selectors', [])
    )

    poi_data = query_overpass(poi_query)
    pois = processor._extract_pois(poi_data)

    print(f"\nTotal POIs found: {len(pois)}")

    # Check for Brick Lane in POI addresses
    brick_lane_pois = [p for p in pois if p.get('street') and 'brick lane' in p['street'].lower()]
    print(f"\nPOIs with addr:street='Brick Lane': {len(brick_lane_pois)}")

    if brick_lane_pois:
        print("\nBrick Lane POIs:")
        for poi in brick_lane_pois:
            print(f"  - {poi.get('name', 'Unnamed')} ({poi.get('shop') or poi.get('amenity')})")

    # Fetch streets
    highway_query = build_highway_query(lat, lon, 900)
    highway_data = query_overpass(highway_query)
    streets = processor._extract_streets(highway_data)

    print(f"\nTotal streets found: {len(streets)}")

    # Check if Brick Lane is in the streets list
    brick_lane_streets = [s for s in streets if 'brick lane' in s['name'].lower()]
    print(f"\nStreets with 'Brick Lane' in name: {len(brick_lane_streets)}")

    if brick_lane_streets:
        print("\nBrick Lane streets found:")
        for s in brick_lane_streets:
            print(f"  - {s['name']} (lat: {s['lat']}, lon: {s['lon']})")

    # Now run full attribution
    processor.pois = pois
    processor.streets = streets
    street_assignments = processor._attribute_pois_to_streets()

    print(f"\n\nStreet Attribution Results:")
    print(f"Total streets with POIs: {len(street_assignments)}")

    # Sort and show all streets with counts
    sorted_streets = sorted(street_assignments.items(), key=lambda x: x[1], reverse=True)

    print(f"\nTop 10 Streets by POI count:")
    for i, (street, count) in enumerate(sorted_streets[:10], 1):
        print(f"  {i}. {street}: {count} POIs")

    # Check specifically for Brick Lane
    brick_lane_count = street_assignments.get('Brick Lane', 0)
    print(f"\n\nBrick Lane POI count: {brick_lane_count}")

    if brick_lane_count == 0:
        print("\n⚠️  Brick Lane has 0 POIs assigned!")
        print("This could mean:")
        print("  1. No POIs have addr:street='Brick Lane'")
        print("  2. No POIs are within 200m of Brick Lane street geometry")
        print("  3. Brick Lane street is not in the 900m radius from geocoded E1 center")
