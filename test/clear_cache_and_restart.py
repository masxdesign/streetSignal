"""Clear the geocode cache completely and verify"""
import os
import json

# Delete the cache file
cache_file = "geocode_cache.json"
if os.path.exists(cache_file):
    os.remove(cache_file)
    print(f"Deleted {cache_file}")

# Create a fresh empty cache
with open(cache_file, 'w') as f:
    json.dump({}, f)
    print(f"Created fresh empty {cache_file}")

print("\nNow restart the Flask server to pick up the empty cache.")
print("Run: python app.py")
