"""
Configuration settings for Street Signal application.
"""

# API Configuration
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
OVERPASS_BASE_URL = "https://overpass-api.de/api/interpreter"

# Rate Limiting (requests per second)
NOMINATIM_RATE_LIMIT = 0.5  # 1 request per 2 seconds
OVERPASS_RATE_LIMIT = 1.0   # 1 request per second

# Request Configuration
NOMINATIM_TIMEOUT = 10  # seconds
OVERPASS_TIMEOUT = 240  # seconds

# User Agent - REQUIRED by Nominatim
USER_AGENT = "StreetSignal/1.0 (salgadom7503@gmail.com)"

# Cache Configuration
GEOCODE_CACHE_FILE = "geocode_cache.json"
HTTP_CACHE_DB = "http_cache.sqlite"

# Default Query Parameters
DEFAULT_RADIUS_M = 900  # Increased from 500 for better coverage
DEFAULT_MAX_ASSIGN_M = 200.0  # Increased from 50 for better street attribution
TOP_N_STREETS = 3

# Presets
PRESETS = {
    "shop": {
        "name": "Shop",
        "include_all_shops": True,
        "shop_types": [],
        "amenities": ["restaurant", "cafe", "fast_food", "pub", "bar", "pharmacy",
                     "post_office", "bank", "atm", "hairdresser", "beauty", "marketplace"],
        "property_selectors": []
    },
    "industrial": {
        "name": "Industrial",
        "include_all_shops": False,
        "shop_types": [],
        "amenities": [],
        "property_selectors": ["landuse=industrial", "building=industrial", "building=warehouse", "industrial=*"]
    },
    "office": {
        "name": "Office",
        "include_all_shops": False,
        "shop_types": [],
        "amenities": [],
        "property_selectors": ["office=*"]
    },
    "custom": {
        "name": "Custom",
        "include_all_shops": True,
        "shop_types": [],
        "amenities": [],
        "property_selectors": []
    }
}

# Available Filter Options
SHOP_TYPES = [
    "supermarket", "convenience", "bakery", "butcher", "greengrocer", "alcohol", "wine", "beverages",
    "clothes", "shoes", "department_store", "mall", "jewelry", "gift", "books", "electronics", "mobile_phone",
    "furniture", "doityourself", "hardware", "florist", "optician", "chemist", "pharmacy",
    "beauty", "hairdresser", "cosmetics", "sports", "bicycle", "car_repair", "car", "motorcycle", "pet",
    "newsagent", "stationery", "toy", "second_hand", "charity", "travel_agency"
]

AMENITY_TYPES = [
    "restaurant", "cafe", "fast_food", "bar", "pub", "bank", "atm", "pharmacy",
    "clinic", "dentist", "doctors", "hairdresser", "beauty", "post_office", "marketplace",
    "place_of_worship"
]

PROPERTY_SELECTORS = [
    # Worship buildings
    "building=church",
    "building=cathedral",
    # Industrial/logistics
    "landuse=industrial",
    "building=industrial",
    "building=warehouse",
    "industrial=*",
    # Office
    "office=*",
    # Commercial
    "building=commercial",
    "building=retail",
    "landuse=commercial",
    "landuse=retail"
]
