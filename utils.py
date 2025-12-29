"""
Utility functions for geocoding, caching, and distance calculations.
"""

import json
import math
import os
import re
import time
import requests
from typing import Optional, Tuple, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pyrate_limiter import Duration, Rate, Limiter
import config


# Validation regexes for Overpass queries
_token_re = re.compile(r"^[a-z0-9_]+$")
_selector_re = re.compile(r"^[a-z0-9_]+=(\*|[a-z0-9_]+)$")


# Rate limiters
nominatim_limiter = Limiter(Rate(1, Duration.SECOND * 2))  # 1 request per 2 seconds
overpass_limiter = Limiter(Rate(1, Duration.SECOND))       # 1 request per second


class GeocodingCache:
    """Persistent disk-based cache for geocoding results."""

    def __init__(self, cache_file: str = config.GEOCODE_CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save cache: {e}")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached geocoding result."""
        return self.cache.get(key)

    def set(self, key: str, value: Dict[str, Any]):
        """Store geocoding result in cache."""
        self.cache[key] = value
        self._save_cache()


# Global cache instance
geocode_cache = GeocodingCache()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
)
def geocode_district(district: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a London postcode district using postcodes.io API.

    This uses the postcodes.io outcode endpoint which provides pre-calculated
    centroids for each postcode district, ensuring consistent and accurate results.

    Args:
        district: Postcode district (e.g., "E1", "SW1")

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    # Check cache first
    cached = geocode_cache.get(district)
    if cached:
        return (cached['lat'], cached['lon'])

    # Try postcodes.io API first (UK-specific, most accurate)
    try:
        response = requests.get(
            f"https://api.postcodes.io/outcodes/{district.upper()}",
            timeout=10
        )

        if response.ok:
            data = response.json()
            if data.get('status') == 200 and data.get('result'):
                result = data['result']
                lat = result['latitude']
                lon = result['longitude']

                # Cache result
                geocode_cache.set(district, {'lat': lat, 'lon': lon})

                return (lat, lon)
    except Exception as e:
        # Fall through to Nominatim fallback
        print(f"postcodes.io failed for {district}: {e}")

    # Fallback to Nominatim if postcodes.io fails
    nominatim_limiter.try_acquire("nominatim")

    params = {
        'q': f"{district}, London, UK",
        'format': 'jsonv2',
        'limit': 10,
        'addressdetails': 1
    }

    headers = {
        'User-Agent': config.USER_AGENT
    }

    response = requests.get(
        f"{config.NOMINATIM_BASE_URL}/search",
        params=params,
        headers=headers,
        timeout=config.NOMINATIM_TIMEOUT
    )
    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    # Calculate centroid of all exact matches
    district_upper = district.upper()
    exact_matches = []

    for result in results:
        address = result.get('address', {})
        postcode = address.get('postcode', '').upper()

        # Collect exact matches (e.g., "E1 6RH" for district "E1")
        if postcode.startswith(district_upper + ' '):
            exact_matches.append({
                'lat': float(result['lat']),
                'lon': float(result['lon'])
            })

    # If we have exact matches, use their centroid
    if exact_matches:
        lats = [m['lat'] for m in exact_matches]
        lons = [m['lon'] for m in exact_matches]
        lat = sum(lats) / len(lats)
        lon = sum(lons) / len(lons)

        # Cache result
        geocode_cache.set(district, {'lat': lat, 'lon': lon})

        return (lat, lon)

    # Final fallback: use first result
    lat = float(results[0]['lat'])
    lon = float(results[0]['lon'])

    # Cache result
    geocode_cache.set(district, {'lat': lat, 'lon': lon})

    return (lat, lon)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
)
def query_overpass(query: str) -> Dict[str, Any]:
    """
    Execute an Overpass API query.

    Args:
        query: Overpass QL query string

    Returns:
        JSON response from Overpass API
    """
    # Rate limit
    overpass_limiter.try_acquire("overpass")

    headers = {
        'User-Agent': config.USER_AGENT
    }

    response = requests.post(
        config.OVERPASS_BASE_URL,
        data={'data': query},
        headers=headers,
        timeout=config.OVERPASS_TIMEOUT
    )
    response.raise_for_status()

    return response.json()


def build_retail_query(
    lat: float,
    lon: float,
    radius_m: int,
    include_all_shops: bool = False,
    shop_types: List[str] = None,
    amenities: List[str] = None,
    property_selectors: List[str] = None
) -> str:
    """
    Build an Overpass QL query for retail/commercial POIs around a location.

    Args:
        lat, lon: Center coordinates
        radius_m: Search radius in meters
        include_all_shops: Include all shop=* tags
        shop_types: Specific shop types to include (e.g., ['supermarket', 'convenience'])
        amenities: Amenity types to include (e.g., ['restaurant', 'cafe'])
        property_selectors: Property selectors (e.g., ['office=*', 'landuse=industrial'])

    Returns:
        Overpass QL query string
    """
    shop_types = shop_types or []
    amenities = amenities or []
    property_selectors = property_selectors or []

    shop_types = [s for s in shop_types if _token_re.match(s)]
    amenities = [a for a in amenities if _token_re.match(a)]
    property_selectors = [p for p in property_selectors if _selector_re.match(p)]

    parts: List[str] = []

    # shops
    if include_all_shops:
        parts += [
            f'node(around:{radius_m},{lat},{lon})["shop"];',
            f'way(around:{radius_m},{lat},{lon})["shop"];',
            f'relation(around:{radius_m},{lat},{lon})["shop"];',
        ]
    elif shop_types:
        re_pat = "|".join(re.escape(s) for s in shop_types)
        parts += [
            f'node(around:{radius_m},{lat},{lon})["shop"~"^({re_pat})$"];',
            f'way(around:{radius_m},{lat},{lon})["shop"~"^({re_pat})$"];',
            f'relation(around:{radius_m},{lat},{lon})["shop"~"^({re_pat})$"];',
        ]

    # amenities
    if amenities:
        re_pat = "|".join(re.escape(a) for a in amenities)
        parts += [
            f'node(around:{radius_m},{lat},{lon})["amenity"~"^({re_pat})$"];',
            f'way(around:{radius_m},{lat},{lon})["amenity"~"^({re_pat})$"];',
            f'relation(around:{radius_m},{lat},{lon})["amenity"~"^({re_pat})$"];',
        ]

    # property selectors like landuse=industrial or office=*
    for sel in property_selectors:
        k, v = sel.split("=", 1)
        if v == "*":
            parts += [
                f'node(around:{radius_m},{lat},{lon})["{k}"];',
                f'way(around:{radius_m},{lat},{lon})["{k}"];',
                f'relation(around:{radius_m},{lat},{lon})["{k}"];',
            ]
        else:
            parts += [
                f'node(around:{radius_m},{lat},{lon})["{k}"="{v}"];',
                f'way(around:{radius_m},{lat},{lon})["{k}"="{v}"];',
                f'relation(around:{radius_m},{lat},{lon})["{k}"="{v}"];',
            ]

    # default if none selected
    if not parts:
        parts += [
            f'node(around:{radius_m},{lat},{lon})["shop"];',
            f'way(around:{radius_m},{lat},{lon})["shop"];',
            f'relation(around:{radius_m},{lat},{lon})["shop"];',
        ]

    inner = "\n  ".join(parts)
    return f"""[out:json][timeout:180];
(
  {inner}
);
out tags center;"""


def build_highway_query(lat: float, lon: float, radius_m: int) -> str:
    """
    Build an Overpass QL query for highways (streets) around a location.

    Args:
        lat, lon: Center coordinates
        radius_m: Search radius in meters

    Returns:
        Overpass QL query string
    """
    query = f"""[out:json][timeout:180];
way["highway"]["name"](around:{radius_m},{lat},{lon});
out tags center;
"""
    return query
