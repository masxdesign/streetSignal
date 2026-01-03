"""
Job processing routes for Street Signal.
Handles the form endpoints from templates/index.html.
"""

import csv
import io
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Blueprint, render_template, request, jsonify, Response
import config
from processor import DistrictProcessor


# Blueprint for job-related routes
jobs_bp = Blueprint('jobs', __name__)

# In-memory job storage (single-process only)
current_job: Optional[Dict[str, Any]] = None


def create_job(
    districts: list,
    preset: str,
    radius_m: int,
    max_assign_m: float,
    include_all_shops: bool,
    shop_types: list,
    amenities: list,
    property_selectors: list
) -> Dict[str, Any]:
    """Create a new job instance."""
    return {
        'job_id': str(uuid.uuid4()),
        'districts': districts,
        'preset': preset,
        'radius_m': radius_m,
        'max_assign_m': max_assign_m,
        'include_all_shops': include_all_shops,
        'shop_types': shop_types,
        'amenities': amenities,
        'property_selectors': property_selectors,
        'current_index': 0,
        'results': [],
        'created_at': datetime.now().isoformat(),
        'completed': False
    }


def apply_preset(preset_name: str) -> Dict[str, Any]:
    """
    Apply preset configuration.

    Args:
        preset_name: Name of the preset to apply

    Returns:
        Dictionary with preset settings
    """
    preset = config.PRESETS.get(preset_name, config.PRESETS['custom'])

    if preset_name == 'custom':
        return {}

    return {
        'include_all_shops': preset.get('include_all_shops', False),
        'shop_types': preset.get('shop_types', []),
        'amenities': preset.get('amenities', []),
        'property_selectors': preset.get('property_selectors', [])
    }


def generate_csv(results: list) -> str:
    """
    Generate CSV content from results.

    Args:
        results: List of result dictionaries

    Returns:
        CSV content as string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'District',
        'Street 1',
        'Count 1',
        'Street 2',
        'Count 2',
        'Street 3',
        'Count 3',
        'Total POIs',
        'Total Streets',
        'Status',
        'Notes'
    ])

    # Data rows
    for result in results:
        writer.writerow([
            result.get('district', ''),
            result.get('street_1', ''),
            result.get('count_1', 0),
            result.get('street_2', ''),
            result.get('count_2', 0),
            result.get('street_3', ''),
            result.get('count_3', 0),
            result.get('total_pois', 0),
            result.get('total_streets_found', 0),
            'Success' if result.get('success') else 'Error',
            result.get('error', '')
        ])

    return output.getvalue()


@jobs_bp.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html',
                          presets=config.PRESETS,
                          shop_types=config.SHOP_TYPES,
                          amenities=config.AMENITY_TYPES,
                          property_selectors=config.PROPERTY_SELECTORS,
                          job=current_job)


@jobs_bp.route('/start', methods=['POST'])
def start_job():
    """
    Initialize a new processing job.

    Expects JSON payload with:
    - districts: list of district codes
    - preset: preset name
    - radius_m: search radius
    - max_assign_m: max assignment distance
    - (optional filters if preset is 'custom')
    """
    global current_job

    data = request.json

    # Parse districts (accept both string and list)
    districts_input = data.get('districts', '')

    if isinstance(districts_input, list):
        districts = [d.strip().upper() for d in districts_input if d.strip()]
    elif isinstance(districts_input, str):
        districts_input = districts_input.strip()
        if not districts_input:
            return jsonify({'error': 'No districts provided'}), 400
        districts = [d.strip().upper() for d in districts_input.replace(',', '\n').split('\n') if d.strip()]
    else:
        return jsonify({'error': 'Invalid districts format'}), 400

    if not districts:
        return jsonify({'error': 'No valid districts provided'}), 400

    # Get parameters
    preset = data.get('preset', 'custom')
    radius_m = int(data.get('radius_m', config.DEFAULT_RADIUS_M))
    max_assign_m = float(data.get('max_assign_m', config.DEFAULT_MAX_ASSIGN_M))

    # Apply preset or use custom selections
    if preset != 'custom':
        preset_config = apply_preset(preset)
        include_all_shops = preset_config.get('include_all_shops', False)
        shop_types = preset_config.get('shop_types', [])
        amenities = preset_config.get('amenities', [])
        property_selectors = preset_config.get('property_selectors', [])
    else:
        include_all_shops = data.get('include_all_shops', False)
        shop_types = data.get('shop_types', [])
        amenities = data.get('amenities', [])
        property_selectors = data.get('property_selectors', [])

    # Create job
    current_job = create_job(
        districts=districts,
        preset=preset,
        radius_m=radius_m,
        max_assign_m=max_assign_m,
        include_all_shops=include_all_shops,
        shop_types=shop_types,
        amenities=amenities,
        property_selectors=property_selectors
    )

    return jsonify({
        'job_id': current_job['job_id'],
        'total_districts': len(districts),
        'message': 'Job created successfully'
    })


@jobs_bp.route('/step', methods=['POST'])
def process_step():
    """
    Process the next district in the current job.

    Returns:
        JSON with step result and progress information
    """
    global current_job

    if not current_job:
        return jsonify({'error': 'No active job'}), 400

    if current_job['completed']:
        return jsonify({'error': 'Job already completed'}), 400

    idx = current_job['current_index']
    districts = current_job['districts']

    if idx >= len(districts):
        current_job['completed'] = True
        return jsonify({
            'completed': True,
            'total': len(districts),
            'processed': idx
        })

    # Process this district
    district = districts[idx]

    processor = DistrictProcessor(
        district=district,
        radius_m=current_job['radius_m'],
        max_assign_m=current_job['max_assign_m'],
        include_all_shops=current_job['include_all_shops'],
        shop_types=current_job['shop_types'],
        amenities=current_job['amenities'],
        property_selectors=current_job['property_selectors']
    )

    result = processor.process()
    current_job['results'].append(result)
    current_job['current_index'] += 1

    # Check if completed
    completed = current_job['current_index'] >= len(districts)
    if completed:
        current_job['completed'] = True

    return jsonify({
        'completed': completed,
        'total': len(districts),
        'processed': current_job['current_index'],
        'result': result
    })


@jobs_bp.route('/download')
def download_csv():
    """Download results as CSV file."""
    if not current_job or not current_job['results']:
        return "No results to download", 400

    csv_content = generate_csv(current_job['results'])

    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=street_signal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )


@jobs_bp.route('/reset', methods=['POST'])
def reset_job():
    """Clear the current job."""
    global current_job
    current_job = None
    return jsonify({'message': 'Job reset successfully'})
