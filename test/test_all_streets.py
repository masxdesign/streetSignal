"""
Test script to verify all_streets field is returned in /step endpoint response.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_all_streets():
    """Test that all_streets field is included in the response."""

    # Start a job with E1 district
    start_payload = {
        "districts": ["E1"],
        "preset": "shop",
        "radius_m": 900,
        "max_assign_m": 200
    }

    print("Starting job for E1...")
    response = requests.post(f"{BASE_URL}/start", json=start_payload)

    if response.status_code != 200:
        print(f"Error starting job: {response.text}")
        return

    result = response.json()
    job_id = result.get('job_id')
    print(f"Job ID: {job_id}")

    # Poll /step until complete
    print("\nProcessing E1 district...")
    while True:
        step_response = requests.post(f"{BASE_URL}/step", json={"job_id": job_id})

        if step_response.status_code != 200:
            print(f"Error in step: {step_response.text}")
            return

        step_result = step_response.json()

        if step_result.get('completed'):
            print("\nJob completed!")

            # Check the result for all_streets field
            district_result = step_result['result']

            print(f"\nDistrict: {district_result['district']}")
            print(f"Total POIs: {district_result['total_pois']}")
            print(f"Total Streets Found: {district_result['total_streets_found']}")
            print(f"\nTop 3 streets:")
            print(f"  1. {district_result['street_1']} - {district_result['count_1']} POIs")
            print(f"  2. {district_result['street_2']} - {district_result['count_2']} POIs")
            print(f"  3. {district_result['street_3']} - {district_result['count_3']} POIs")

            # Check for all_streets field
            if 'all_streets' in district_result:
                all_streets = district_result['all_streets']
                print(f"\n[OK] all_streets field found!")
                print(f"  Total streets with data: {len(all_streets)}")

                # Show top 10 streets from all_streets
                print(f"\nTop 10 streets from all_streets:")
                for i, street in enumerate(all_streets[:10], 1):
                    print(f"  {i}. {street['name']} - {street['poi_count']} POIs")

                # Check if Brick Lane is in the list
                brick_lane = next((s for s in all_streets if 'Brick Lane' in s['name']), None)
                if brick_lane:
                    brick_lane_rank = all_streets.index(brick_lane) + 1
                    print(f"\n[OK] Brick Lane found at rank #{brick_lane_rank} with {brick_lane['poi_count']} POIs")
                else:
                    print(f"\n[ERROR] Brick Lane not found in all_streets")

                # Show streets with 0 POIs count
                zero_poi_streets = [s for s in all_streets if s['poi_count'] == 0]
                print(f"\nStreets with 0 POIs: {len(zero_poi_streets)}")

            else:
                print(f"\n[ERROR] all_streets field NOT found in response")
                print(f"Available fields: {list(district_result.keys())}")

            break

        print(f"Processing {step_result.get('current_district', '?')}...")
        time.sleep(2)

if __name__ == "__main__":
    test_all_streets()
