"""
Test script to investigate Albert Embankment appearing in SE11 vs SE1.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_albert_embankment():
    """Test Albert Embankment in both SE1 and SE11."""

    # Test both districts
    districts = ["SE1", "SE11"]

    for district in districts:
        print(f"\n{'='*60}")
        print(f"Testing district: {district}")
        print(f"{'='*60}")

        start_payload = {
            "districts": [district],
            "preset": "shop",
            "radius_m": 900,
            "max_assign_m": 200
        }

        response = requests.post(f"{BASE_URL}/start", json=start_payload)

        if response.status_code != 200:
            print(f"Error starting job: {response.text}")
            continue

        result = response.json()
        job_id = result.get('job_id')

        # Poll /step until complete
        while True:
            step_response = requests.post(f"{BASE_URL}/step", json={"job_id": job_id})

            if step_response.status_code != 200:
                print(f"Error in step: {step_response.text}")
                break

            step_result = step_response.json()

            if step_result.get('completed'):
                district_result = step_result['result']

                print(f"\nDistrict: {district_result['district']}")
                print(f"Total POIs: {district_result['total_pois']}")
                print(f"Total Streets Found: {district_result['total_streets_found']}")

                # Check if Albert Embankment is in all_streets
                if 'all_streets' in district_result:
                    all_streets = district_result['all_streets']
                    albert_emb = next((s for s in all_streets if 'Albert Embankment' in s['name']), None)

                    if albert_emb:
                        rank = all_streets.index(albert_emb) + 1
                        print(f"\n[FOUND] Albert Embankment at rank #{rank} with {albert_emb['poi_count']} POIs")
                    else:
                        print(f"\n[NOT FOUND] Albert Embankment not in results")

                    # Show top 10 for context
                    print(f"\nTop 10 streets:")
                    for i, street in enumerate(all_streets[:10], 1):
                        marker = " <-- Albert Embankment" if 'Albert Embankment' in street['name'] else ""
                        print(f"  {i}. {street['name']} - {street['poi_count']} POIs{marker}")

                break

            time.sleep(1)

        time.sleep(2)  # Wait between districts

if __name__ == "__main__":
    test_albert_embankment()
