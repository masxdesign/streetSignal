"""
Geocoding routes for Street Signal.
Provides API endpoints for geocoding streets and districts.
"""

from flask import Blueprint, request, jsonify
from utils import get_area_and_coords, geocode_district


geocode_bp = Blueprint('geocode', __name__, url_prefix='/api/geocode')


@geocode_bp.route('/street', methods=['GET', 'POST'])
def street_geocode():
    """
    Get area/suburb and coordinates for a street within a postcode district.

    GET params or POST JSON:
        - postcode: Postcode district (e.g., "E1", "SW1")
        - street: Street name (e.g., "Brick Lane")

    Returns:
        JSON with 'area', 'lat', 'lon' keys
    """
    if request.method == 'POST':
        data = request.json or {}
        postcode = data.get('postcode', '').strip()
        street = data.get('street', '').strip()
    else:
        postcode = request.args.get('postcode', '').strip()
        street = request.args.get('street', '').strip()

    if not postcode:
        return jsonify({'error': 'postcode is required'}), 400
    if not street:
        return jsonify({'error': 'street is required'}), 400

    result = get_area_and_coords(postcode, street)

    return jsonify({
        'postcode': postcode.upper(),
        'street': street,
        'area': result.get('area', ''),
        'lat': result.get('lat'),
        'lon': result.get('lon')
    })


@geocode_bp.route('/district', methods=['GET', 'POST'])
def district_geocode():
    """
    Get coordinates for a postcode district centroid.

    GET params or POST JSON:
        - district: Postcode district (e.g., "E1", "SW1")

    Returns:
        JSON with 'lat', 'lon' keys
    """
    if request.method == 'POST':
        data = request.json or {}
        district = data.get('district', '').strip()
    else:
        district = request.args.get('district', '').strip()

    if not district:
        return jsonify({'error': 'district is required'}), 400

    result = geocode_district(district)

    if result is None:
        return jsonify({
            'district': district.upper(),
            'lat': None,
            'lon': None,
            'error': 'District not found'
        }), 404

    return jsonify({
        'district': district.upper(),
        'lat': result[0],
        'lon': result[1]
    })


@geocode_bp.route('/bulk', methods=['POST'])
def bulk_street_geocode():
    """
    Bulk geocode multiple streets.

    POST JSON:
        - items: Array of {postcode, street} objects

    Returns:
        JSON array of results with 'postcode', 'street', 'area', 'lat', 'lon'
    """
    data = request.json or {}
    items = data.get('items', [])

    if not items:
        return jsonify({'error': 'items array is required'}), 400

    if len(items) > 50:
        return jsonify({'error': 'Maximum 50 items per request'}), 400

    results = []
    for item in items:
        postcode = item.get('postcode', '').strip()
        street = item.get('street', '').strip()

        if not postcode or not street:
            results.append({
                'postcode': postcode,
                'street': street,
                'error': 'postcode and street are required'
            })
            continue

        result = get_area_and_coords(postcode, street)
        results.append({
            'postcode': postcode.upper(),
            'street': street,
            'area': result.get('area', ''),
            'lat': result.get('lat'),
            'lon': result.get('lon')
        })

    return jsonify({'results': results})
