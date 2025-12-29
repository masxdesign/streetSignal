"""
Quick test script to diagnose E1 processing issue.
"""

from processor import DistrictProcessor
import config

# Test E1 with Shop preset
print("=" * 60)
print("Testing E1 District with Shop Preset")
print("=" * 60)

preset = config.PRESETS['shop']

processor = DistrictProcessor(
    district='E1',
    radius_m=500,
    max_assign_m=50.0,
    include_all_shops=preset['include_all_shops'],
    shop_types=preset.get('shop_types', []),
    amenities=preset.get('amenities', []),
    property_selectors=preset.get('property_selectors', [])
)

print("\nConfiguration:")
print(f"  District: E1")
print(f"  Radius: 500m")
print(f"  Max Assign: 50m")
print(f"  Include All Shops: {preset['include_all_shops']}")
print(f"  Amenities: {preset.get('amenities', [])}")
print(f"  Property Selectors: {preset.get('property_selectors', [])}")

print("\nProcessing...")
result = processor.process()

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Success: {result['success']}")
print(f"Total POIs: {result['total_pois']}")
print(f"Total Streets: {result['total_streets_found']}")
print(f"\nTop 3 Streets:")
print(f"  1. {result['street_1']} ({result['count_1']} POIs)")
print(f"  2. {result['street_2']} ({result['count_2']} POIs)")
print(f"  3. {result['street_3']} ({result['count_3']} POIs)")

if result.get('error'):
    print(f"\nError: {result['error']}")

print("\n" + "=" * 60)
