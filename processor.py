"""
Core data processing logic for POI extraction and street attribution.
"""

from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
import config
from utils import (
    geocode_district,
    query_overpass,
    build_retail_query,
    build_highway_query,
    haversine_distance
)


class DistrictProcessor:
    """Processes a single district to extract and rank streets by POI count."""

    def __init__(
        self,
        district: str,
        radius_m: int = config.DEFAULT_RADIUS_M,
        max_assign_m: float = config.DEFAULT_MAX_ASSIGN_M,
        include_all_shops: bool = False,
        shop_types: List[str] = None,
        amenities: List[str] = None,
        property_selectors: List[str] = None
    ):
        self.district = district
        self.radius_m = radius_m
        self.max_assign_m = max_assign_m
        self.include_all_shops = include_all_shops
        self.shop_types = shop_types or []
        self.amenities = amenities or []
        self.property_selectors = property_selectors or []

        self.center_coords: Optional[Tuple[float, float]] = None
        self.pois: List[Dict[str, Any]] = []
        self.streets: List[Dict[str, Any]] = []
        self.street_poi_counts: Dict[str, int] = {}
        self.street_to_pois: Dict[str, List[Dict[str, Any]]] = {}
        self.error: Optional[str] = None

    def process(self) -> Dict[str, Any]:
        """
        Execute the full processing pipeline for this district.

        Returns:
            Dictionary with results or error information
        """
        try:
            # Step 1: Geocode district
            coords = geocode_district(self.district)
            if not coords:
                self.error = f"Could not geocode district: {self.district}"
                return self._build_error_result()

            self.center_coords = coords
            lat, lon = coords

            # Step 2: Fetch POIs
            poi_query = build_retail_query(
                lat=lat,
                lon=lon,
                radius_m=self.radius_m,
                include_all_shops=self.include_all_shops,
                shop_types=self.shop_types,
                amenities=self.amenities,
                property_selectors=self.property_selectors
            )

            poi_data = query_overpass(poi_query)
            self.pois = self._extract_pois(poi_data)

            if not self.pois:
                return self._build_result([])

            # Step 3: Fetch streets (highways)
            highway_query = build_highway_query(lat, lon, self.radius_m)
            highway_data = query_overpass(highway_query)
            self.streets = self._extract_streets(highway_data)

            # Step 4: Attribute POIs to streets
            self.street_poi_counts = self._attribute_pois_to_streets()

            # Step 5: Rank streets
            top_streets = self._rank_streets(self.street_poi_counts)

            return self._build_result(top_streets)

        except Exception as e:
            self.error = str(e)
            return self._build_error_result()

    def _extract_pois(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract POI information from Overpass response.
        Filters POIs to only include those matching the district postcode prefix.

        Args:
            data: Overpass API JSON response

        Returns:
            List of POI dictionaries with relevant fields
        """
        pois = []

        for element in data.get('elements', []):
            tags = element.get('tags', {})

            # Determine coordinates
            if element['type'] == 'node':
                lat = element['lat']
                lon = element['lon']
            elif 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
            else:
                continue  # Skip if no coordinates

            # Filter by postcode if available
            postcode = tags.get('addr:postcode', '')
            if postcode:
                # Normalize postcode: remove spaces and uppercase
                postcode_upper = postcode.upper().replace(' ', '')
                # Skip if postcode doesn't start with our target district
                # This handles sub-districts like SE17 matching SE1
                if not postcode_upper.startswith(self.district):
                    continue

            poi = {
                'id': element['id'],
                'type': element['type'],
                'lat': lat,
                'lon': lon,
                'tags': tags,
                'street': tags.get('addr:street'),
                'postcode': postcode,
                'name': tags.get('name'),
                'shop': tags.get('shop'),
                'amenity': tags.get('amenity'),
                'office': tags.get('office'),
                'building': tags.get('building'),
                'landuse': tags.get('landuse')
            }

            pois.append(poi)

        return pois

    def _extract_streets(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract street information from Overpass highway query.

        Args:
            data: Overpass API JSON response

        Returns:
            List of street dictionaries
        """
        streets = []

        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name')

            if not name:
                continue

            # Use center coordinates for ways
            if 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
            else:
                continue

            street = {
                'id': element['id'],
                'name': name,
                'lat': lat,
                'lon': lon,
                'highway_type': tags.get('highway')
            }

            streets.append(street)

        return streets

    def _attribute_pois_to_streets(self) -> Dict[str, int]:
        """
        Assign each POI to a street name.

        Uses addr:street tag if available, otherwise finds nearest named road
        within max_assign_m distance.

        Also builds street_to_pois mapping for postcode filtering.

        Returns:
            Dictionary mapping street names to POI counts
        """
        street_counts = Counter()
        from collections import defaultdict
        self.street_to_pois = defaultdict(list)

        for poi in self.pois:
            street_name = None

            # Priority 1: Use addr:street if available
            if poi['street']:
                street_name = poi['street']
            else:
                # Priority 2: Find nearest street
                street_name = self._find_nearest_street(poi)

            if street_name:
                street_counts[street_name] += 1
                self.street_to_pois[street_name].append(poi)

        return dict(street_counts)

    def _find_nearest_street(self, poi: Dict[str, Any]) -> Optional[str]:
        """
        Find the nearest named street to a POI within max_assign_m distance.

        Args:
            poi: POI dictionary with lat/lon

        Returns:
            Street name or None if no street within threshold
        """
        if not self.streets:
            return None

        poi_lat = poi['lat']
        poi_lon = poi['lon']

        nearest_street = None
        min_distance = float('inf')

        for street in self.streets:
            distance = haversine_distance(
                poi_lat, poi_lon,
                street['lat'], street['lon']
            )

            if distance < min_distance:
                min_distance = distance
                nearest_street = street['name']

        # Only assign if within threshold
        if min_distance <= self.max_assign_m:
            return nearest_street

        return None

    def _rank_streets(self, street_counts: Dict[str, int]) -> List[Tuple[str, int]]:
        """
        Rank streets by POI count and return top N.

        Args:
            street_counts: Dictionary mapping street names to counts

        Returns:
            List of (street_name, count) tuples, sorted descending
        """
        sorted_streets = sorted(
            street_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_streets[:config.TOP_N_STREETS]

    def _filter_streets_by_postcode(self, street_name: str) -> bool:
        """
        Check if a street should be included based on POI postcodes.

        A street is included if the majority of its POIs (with postcodes) belong
        to the target district.

        Args:
            street_name: Name of the street to check

        Returns:
            True if street should be included, False otherwise
        """
        # Get POIs on this street from precomputed mapping
        pois_on_street = self.street_to_pois.get(street_name, [])

        # Count POIs by postcode district
        district_count = 0
        other_district_count = 0

        for poi in pois_on_street:
            postcode = poi.get('postcode', '')
            if postcode:
                postcode_upper = postcode.upper().replace(' ', '')
                if postcode_upper.startswith(self.district):
                    district_count += 1
                else:
                    other_district_count += 1

        # If no POIs have postcodes, include the street (benefit of doubt)
        if district_count == 0 and other_district_count == 0:
            return True

        # Include if majority of POIs with postcodes match our district
        return district_count >= other_district_count

    def _build_result(self, top_streets: List[Tuple[str, int]]) -> Dict[str, Any]:
        """
        Build result dictionary for successful processing.

        Args:
            top_streets: List of (street_name, count) tuples

        Returns:
            Result dictionary
        """
        # Pad to exactly 3 streets
        while len(top_streets) < config.TOP_N_STREETS:
            top_streets.append(('', 0))

        result = {
            'district': self.district,
            'success': True,
            'error': None,
            'total_pois': len(self.pois),
            'total_streets_found': len(self.streets),
        }

        # Add top 3 streets
        for i, (street, count) in enumerate(top_streets[:3], start=1):
            result[f'street_{i}'] = street
            result[f'count_{i}'] = count

        # Build all_streets list with POI counts (DISTINCT by street name, exclude zero counts)
        streets_map = {}

        for street in self.streets:
            street_name = street['name']

            # Skip if we already have this street name
            if street_name in streets_map:
                continue

            poi_count = self.street_poi_counts.get(street_name, 0)

            # Skip streets with zero POI count
            if poi_count == 0:
                continue

            # Filter streets based on POI postcodes
            if not self._filter_streets_by_postcode(street_name):
                continue

            streets_map[street_name] = {
                'name': street_name,
                'poi_count': poi_count
            }

        # Convert to list and sort by POI count descending
        all_streets_with_counts = list(streets_map.values())
        all_streets_with_counts.sort(key=lambda x: x['poi_count'], reverse=True)

        result['all_streets'] = all_streets_with_counts

        return result

    def _build_error_result(self) -> Dict[str, Any]:
        """
        Build result dictionary for failed processing.

        Returns:
            Error result dictionary
        """
        result = {
            'district': self.district,
            'success': False,
            'error': self.error,
            'total_pois': 0,
            'total_streets_found': 0,
            'street_1': '',
            'count_1': 0,
            'street_2': '',
            'count_2': 0,
            'street_3': '',
            'count_3': 0
        }

        return result
