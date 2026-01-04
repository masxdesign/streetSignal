"""
Utility functions for geocoding, caching, and distance calculations.
"""

import json
import math
import re
import sqlite3
import time
import requests
from typing import Optional, Tuple, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pyrate_limiter import Duration, Rate, Limiter, BucketFullException
import config


# Validation regexes for Overpass queries
_token_re = re.compile(r"^[a-z0-9_]+$")
_selector_re = re.compile(r"^[a-z0-9_]+=(\*|[a-z0-9_]+)$")


# Rate limiters
nominatim_limiter = Limiter(Rate(1, Duration.SECOND * 2))  # 1 request per 2 seconds
overpass_limiter = Limiter(Rate(1, Duration.SECOND))       # 1 request per second


def acquire_with_wait(limiter: Limiter, item: str, max_wait: float = 10.0) -> None:
    """
    Acquire rate limit slot, waiting if bucket is full instead of throwing.

    Args:
        limiter: The rate limiter instance
        item: The item identifier for the bucket
        max_wait: Maximum seconds to wait before giving up
    """
    wait_time = 0.5
    total_waited = 0.0

    while total_waited < max_wait:
        try:
            limiter.try_acquire(item)
            return
        except BucketFullException:
            time.sleep(wait_time)
            total_waited += wait_time

    # Final attempt after max wait
    limiter.try_acquire(item)


class GeocodeCache:
    """SQLite-based cache for all geocoding results (districts and streets)."""

    def __init__(self, db_file: str = "geocode_cache.sqlite"):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with both tables."""
        conn = sqlite3.connect(self.db_file)
        # District cache (simple key -> lat/lon)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS district_cache (
                district TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                updated_at INTEGER
            )
        """)
        # Street cache (postcode+street -> lat/lon/area)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS street_cache (
                key TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                area TEXT,
                raw_json TEXT,
                updated_at INTEGER
            )
        """)
        conn.commit()
        conn.close()

    # --- District cache methods ---
    def get_district(self, district: str) -> Optional[Dict[str, float]]:
        """Retrieve cached district geocoding result."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT lat, lon FROM district_cache WHERE district = ?",
            (district.upper().strip(),)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'lat': row['lat'], 'lon': row['lon']}
        return None

    def set_district(self, district: str, lat: float, lon: float):
        """Store district geocoding result in cache."""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            INSERT INTO district_cache (district, lat, lon, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(district) DO UPDATE SET
                lat = excluded.lat,
                lon = excluded.lon,
                updated_at = excluded.updated_at
        """, (district.upper().strip(), lat, lon, int(time.time() * 1000)))
        conn.commit()
        conn.close()

    # --- Street cache methods ---
    def _street_key(self, postcode: str, street: str) -> str:
        """Generate cache key from postcode district and street."""
        return f"{postcode.upper().strip()}|{street.lower().strip()}"

    def get_street(self, postcode: str, street: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached street geocoding result."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT lat, lon, area, raw_json FROM street_cache WHERE key = ?",
            (self._street_key(postcode, street),)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def set_street(self, postcode: str, street: str, lat: Optional[float],
                   lon: Optional[float], area: str, raw: Dict[str, Any]):
        """Store street geocoding result in cache."""
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            INSERT INTO street_cache (key, lat, lon, area, raw_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                lat = excluded.lat,
                lon = excluded.lon,
                area = excluded.area,
                raw_json = excluded.raw_json,
                updated_at = excluded.updated_at
        """, (
            self._street_key(postcode, street),
            lat,
            lon,
            area,
            json.dumps(raw),
            int(time.time() * 1000)
        ))
        conn.commit()
        conn.close()


# Global cache instance (single SQLite file for all geocoding)
geocode_cache = GeocodeCache()


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
    cached = geocode_cache.get_district(district)
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
                geocode_cache.set_district(district, lat, lon)

                return (lat, lon)
    except Exception as e:
        # Fall through to Nominatim fallback
        print(f"postcodes.io failed for {district}: {e}")

    # Fallback to Nominatim if postcodes.io fails
    acquire_with_wait(nominatim_limiter, "nominatim")

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
        geocode_cache.set_district(district, lat, lon)

        return (lat, lon)

    # Final fallback: use first result
    lat = float(results[0]['lat'])
    lon = float(results[0]['lon'])

    # Cache result
    geocode_cache.set_district(district, lat, lon)

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


# ============================================================================
# Street Geocoding with Area/Suburb Lookup
# ============================================================================

def _pick_area(address: Optional[Dict[str, Any]]) -> str:
    """Extract the most relevant area/suburb from Nominatim address response."""
    if not address:
        return ""
    return (
        address.get("neighbourhood") or
        address.get("suburb") or
        address.get("city_district") or
        address.get("borough") or
        address.get("town") or
        address.get("city") or
        ""
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
)
def geocode_street(postcode_district: str, street: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a street within a postcode district using Nominatim.

    Args:
        postcode_district: Postcode district (e.g., "E1", "SW1")
        street: Street name

    Returns:
        Dict with 'lat', 'lon', 'raw' or None if not found
    """
    acquire_with_wait(nominatim_limiter, "nominatim")

    query = f"{street}, {postcode_district}, London, UK"
    params = {
        'q': query,
        'format': 'jsonv2',
        'limit': 1
    }
    headers = {'User-Agent': config.USER_AGENT}

    response = requests.get(
        f"{config.NOMINATIM_BASE_URL}/search",
        params=params,
        headers=headers,
        timeout=config.NOMINATIM_TIMEOUT
    )
    response.raise_for_status()

    data = response.json()
    if not data or len(data) == 0:
        return None

    return {
        'lat': float(data[0]['lat']),
        'lon': float(data[0]['lon']),
        'raw': data[0]
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
)
def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """
    Reverse geocode coordinates to get address details including area/suburb.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Dict with 'area' and 'raw' response
    """
    acquire_with_wait(nominatim_limiter, "nominatim")

    params = {
        'format': 'jsonv2',
        'zoom': 16,
        'addressdetails': 1,
        'lat': lat,
        'lon': lon
    }
    headers = {'User-Agent': config.USER_AGENT}

    response = requests.get(
        f"{config.NOMINATIM_BASE_URL}/reverse",
        params=params,
        headers=headers,
        timeout=config.NOMINATIM_TIMEOUT
    )
    response.raise_for_status()

    data = response.json()
    return {
        'area': _pick_area(data.get('address')),
        'raw': data
    }


def get_area_and_coords(postcode: str, street: str) -> Dict[str, Any]:
    """
    Get the area/suburb and coordinates for a street within a postcode district.

    This is the main function to call - it handles caching automatically.

    Args:
        postcode: Postcode district (e.g., "E1", "SW1")
        street: Street name

    Returns:
        Dict with 'area', 'lat', 'lon' keys
    """
    # Check cache first
    cached = geocode_cache.get_street(postcode, street)
    if cached and cached.get('lat') is not None and cached.get('lon') is not None:
        return {
            'area': cached.get('area') or '',
            'lat': cached['lat'],
            'lon': cached['lon']
        }

    # Geocode the street
    geocode_result = geocode_street(postcode, street)
    if not geocode_result:
        geocode_cache.set_street(postcode, street, None, None, '', {'error': 'geocode_not_found'})
        return {'area': '', 'lat': None, 'lon': None}

    lat, lon = geocode_result['lat'], geocode_result['lon']

    # Reverse geocode to get area/suburb
    reverse_result = reverse_geocode(lat, lon)
    area = reverse_result.get('area') or ''

    # Cache the result
    geocode_cache.set_street(postcode, street, lat, lon, area, {
        'geocode': geocode_result['raw'],
        'reverse': reverse_result['raw']
    })

    return {'area': area, 'lat': lat, 'lon': lon}
