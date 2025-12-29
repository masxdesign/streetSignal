# Technical Design Specification

## Street Signal - Developer Documentation

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Data Models](#data-models)
3. [API Endpoints](#api-endpoints)
4. [Processing Pipeline](#processing-pipeline)
5. [Algorithm Details](#algorithm-details)
6. [Error Handling](#error-handling)
7. [Performance Considerations](#performance-considerations)
8. [Extension Guidelines](#extension-guidelines)

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (Client)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  HTML Form   │  │   Progress   │  │ Results Table│  │
│  │  Controls    │  │     Bar      │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────▲───────┘  │
│         │                 │                  │           │
│         └─────────────────┼──────────────────┘           │
│                           │ Fetch API                    │
└───────────────────────────┼──────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────┐
│                Flask App (app.py)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │   GET /  │  │ POST     │  │ POST     │  │   GET    ││
│  │          │  │ /start   │  │ /step    │  │/download ││
│  └──────────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘│
│                     │              │             │       │
│  ┌──────────────────▼──────────────▼─────────────▼────┐ │
│  │         In-Memory Job Storage (dict)               │ │
│  │    { job_id, districts, results, current_index }   │ │
│  └────────────────────────────────────────────────────┘ │
└───────────────────────────┼──────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────┐
│              DistrictProcessor (processor.py)            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  1. Geocode district                             │   │
│  │  2. Fetch POIs (Overpass)                        │   │
│  │  3. Fetch highways (Overpass)                    │   │
│  │  4. Attribute POIs → Streets                     │   │
│  │  5. Rank streets                                 │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────┼──────────────────────────────┘
                            │
┌───────────────────────────┼──────────────────────────────┐
│                    Utilities (utils.py)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Geocoding   │  │   Overpass   │  │  Haversine   │  │
│  │  + Cache     │  │Query Builder │  │   Distance   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │
│         │                 │                             │
└─────────┼─────────────────┼─────────────────────────────┘
          │                 │
┌─────────▼─────────────────▼─────────────────────────────┐
│              External APIs + Cache                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Nominatim   │  │  Overpass    │  │geocode_cache │  │
│  │ (Geocoding)  │  │ (OSM POIs)   │  │    .json     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Data Models

### Job Structure

Stored in-memory as Python dict:

```python
{
    'job_id': str,              # UUID
    'districts': List[str],      # e.g., ['E1', 'SW1', 'W1']
    'preset': str,              # 'shop', 'industrial', 'office', 'custom'
    'radius_m': int,            # Search radius (default: 500)
    'max_assign_m': float,      # Max street assignment distance (default: 50.0)
    'include_all_shops': bool,  # Include shop=* wildcard
    'shop_types': List[str],    # Specific shop types
    'amenities': List[str],     # Amenity types (cafe, restaurant, etc.)
    'property_selectors': List[str],  # office=*, building=warehouse, etc.
    'current_index': int,       # Processing progress
    'results': List[Dict],      # Result objects
    'created_at': str,          # ISO timestamp
    'completed': bool           # Job status
}
```

### Result Structure

Per-district result:

```python
{
    'district': str,            # e.g., 'E1'
    'success': bool,            # True if processed successfully
    'error': Optional[str],     # Error message if failed
    'total_pois': int,          # Total POIs found
    'total_streets_found': int, # Total named streets found
    'street_1': str,            # Top-ranked street name
    'count_1': int,             # POI count for street_1
    'street_2': str,            # Second-ranked street
    'count_2': int,             # POI count for street_2
    'street_3': str,            # Third-ranked street
    'count_3': int              # POI count for street_3
}
```

### POI Internal Structure

```python
{
    'id': int,                  # OSM element ID
    'type': str,                # 'node' or 'way'
    'lat': float,               # Latitude
    'lon': float,               # Longitude
    'tags': Dict[str, str],     # All OSM tags
    'street': Optional[str],    # addr:street tag if present
    'name': Optional[str],      # POI name
    'shop': Optional[str],      # shop tag value
    'amenity': Optional[str],   # amenity tag value
    'office': Optional[str],    # office tag value
    'building': Optional[str],  # building tag value
    'landuse': Optional[str]    # landuse tag value
}
```

### Street Internal Structure

```python
{
    'id': int,                  # OSM way ID
    'name': str,                # Street name
    'lat': float,               # Center latitude
    'lon': float,               # Center longitude
    'highway_type': str         # road, residential, primary, etc.
}
```

---

## API Endpoints

### `GET /`

**Purpose**: Render main application page

**Response**: HTML page with embedded JavaScript

**Template Variables**:
- `presets`: Available presets from config
- `shop_types`: Available shop type filters
- `amenities`: Available amenity filters
- `property_selectors`: Available property filters
- `job`: Current job state (if any)

---

### `POST /start`

**Purpose**: Initialize new processing job

**Request Body** (JSON):
```json
{
  "districts": "E1, SW1, W1",
  "preset": "shop",
  "radius_m": 500,
  "max_assign_m": 50,
  "include_all_shops": false,    // Only if preset='custom'
  "amenities": ["cafe", "bar"],  // Only if preset='custom'
  "property_selectors": []       // Only if preset='custom'
}
```

**Success Response** (200):
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_districts": 3,
  "message": "Job created successfully"
}
```

**Error Response** (400):
```json
{
  "error": "No districts provided"
}
```

**Side Effects**:
- Creates global `current_job` instance
- Resets any previous job
- Parses district input (comma or newline separated)
- Applies preset configuration

---

### `POST /step`

**Purpose**: Process next district in current job

**Request Body**: None (uses global job state)

**Success Response** (200):
```json
{
  "completed": false,
  "total": 3,
  "processed": 1,
  "result": {
    "district": "E1",
    "success": true,
    "total_pois": 47,
    "street_1": "Brick Lane",
    "count_1": 12,
    // ... (full result object)
  }
}
```

**Completion Response** (200):
```json
{
  "completed": true,
  "total": 3,
  "processed": 3
}
```

**Error Response** (400):
```json
{
  "error": "No active job"
}
```

**Processing**:
1. Check job exists and not completed
2. Get current district from `current_index`
3. Instantiate `DistrictProcessor`
4. Execute `processor.process()`
5. Append result to `job['results']`
6. Increment `job['current_index']`
7. Mark completed if all districts processed

---

### `GET /download`

**Purpose**: Download results as CSV

**Response**: CSV file attachment

**Headers**:
```
Content-Type: text/csv
Content-Disposition: attachment; filename=street_signal_20250128_143022.csv
```

**CSV Format**:
```csv
District,Street 1,Count 1,Street 2,Count 2,Street 3,Count 3,Total POIs,Total Streets,Status,Notes
E1,Brick Lane,12,Commercial Street,8,Whitechapel Road,6,47,23,Success,
```

**Error Response** (400):
```
"No results to download"
```

---

### `POST /reset`

**Purpose**: Clear current job and reset UI

**Response** (200):
```json
{
  "message": "Job reset successfully"
}
```

**Side Effects**:
- Sets `current_job = None`
- Client must clear UI state

---

## Processing Pipeline

### Step-by-Step Flow

#### 1. Geocoding

```python
coords = geocode_district("E1")
# → Checks geocode_cache.json
# → If miss: queries Nominatim
# → Returns (lat, lon) tuple
```

**Cache Structure** (`geocode_cache.json`):
```json
{
  "E1": {"lat": 51.5154, "lon": -0.0648},
  "SW1": {"lat": 51.4975, "lon": -0.1357}
}
```

#### 2. POI Query

```python
query = build_overpass_query(
    lat=51.5154,
    lon=-0.0648,
    radius_m=500,
    include_all_shops=True,
    amenities=["cafe", "restaurant"]
)
# → Constructs Overpass QL
# → Posts to Overpass API
# → Returns JSON with elements
```

**Example Overpass QL**:
```
[out:json][timeout:180];
(
node["shop"](around:500,51.5154,-0.0648);
way["shop"](around:500,51.5154,-0.0648);
node["amenity"="cafe"](around:500,51.5154,-0.0648);
way["amenity"="cafe"](around:500,51.5154,-0.0648);
);
out center;
```

#### 3. Highway Query

```python
query = build_highway_query(lat=51.5154, lon=-0.0648, radius_m=500)
# → Fetches all named highways
```

**Overpass QL**:
```
[out:json][timeout:180];
way["highway"]["name"](around:500,51.5154,-0.0648);
out center;
```

#### 4. Street Attribution

For each POI:

```python
if poi['street']:  # Has addr:street tag
    street_name = poi['street']
else:
    # Find nearest street
    nearest = find_nearest_street(poi, streets)
    if distance <= max_assign_m:
        street_name = nearest['name']
```

#### 5. Ranking

```python
street_counts = Counter()
for poi in pois:
    if poi.street_name:
        street_counts[poi.street_name] += 1

top_3 = sorted(street_counts.items(), key=lambda x: x[1], reverse=True)[:3]
```

---

## Algorithm Details

### Haversine Distance Formula

**Purpose**: Calculate great-circle distance between two points on Earth

**Implementation** ([utils.py:84](utils.py#L84)):

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters

    φ1 = radians(lat1)
    φ2 = radians(lat2)
    Δφ = radians(lat2 - lat1)
    Δλ = radians(lon2 - lon1)

    a = sin²(Δφ/2) + cos(φ1) × cos(φ2) × sin²(Δλ/2)
    c = 2 × atan2(√a, √(1-a))

    return R × c
```

**Complexity**: O(1)

**Accuracy**: ~0.5% error for distances < 1km

---

### Nearest Street Search

**Algorithm**: Brute-force linear search

**Complexity**: O(P × S) where P = POIs, S = Streets

**Implementation** ([processor.py:155](processor.py#L155)):

```python
def _find_nearest_street(poi):
    min_distance = inf
    nearest_street = None

    for street in streets:
        d = haversine_distance(poi.lat, poi.lon, street.lat, street.lon)
        if d < min_distance:
            min_distance = d
            nearest_street = street.name

    return nearest_street if min_distance <= max_assign_m else None
```

**Optimization Potential**:
- Could use spatial index (R-tree) for O(log S)
- Not implemented due to low S (typically < 100 streets per district)

---

## Error Handling

### Retry Strategy

All external API calls use `tenacity` retry decorator:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type((RequestException, Timeout))
)
```

**Behavior**:
- Attempt 1: Immediate
- Attempt 2: Wait 4-8 seconds (jittered)
- Attempt 3: Wait 8-16 seconds (jittered)
- After 3 failures: Raise exception

### Error Propagation

```
DistrictProcessor.process()
  ├─ Try:
  │   ├─ geocode_district()  → RetryError → Return error result
  │   ├─ query_overpass()    → RetryError → Return error result
  │   └─ Any exception       → Catch → Return error result
  └─ Except Exception as e:
      └─ Return _build_error_result()
```

**Error Result Structure**:
```python
{
    'district': 'E1',
    'success': False,
    'error': 'Overpass timeout after 3 retries',
    'total_pois': 0,
    'street_1': '', 'count_1': 0,
    'street_2': '', 'count_2': 0,
    'street_3': '', 'count_3': 0
}
```

**Job Continuation**: Job continues to next district even if one fails

---

## Performance Considerations

### Rate Limiting Bottleneck

**Nominatim**: 1 request per 2 seconds = 30 requests/minute
**Overpass**: 1 request per second = 60 requests/minute

**Per District**:
- 1 Nominatim call (if not cached)
- 2 Overpass calls (POIs + highways)
- Minimum time: ~3 seconds

**10 Districts**:
- Best case (all geocodes cached): ~30 seconds
- Worst case (no cache): ~50 seconds

### Memory Usage

**Per District**:
- POIs: ~100-500 elements × 500 bytes ≈ 50-250 KB
- Streets: ~20-100 elements × 200 bytes ≈ 4-20 KB
- Results: ~500 bytes

**For 100 Districts**:
- Total memory: ~5-30 MB (negligible)

### Disk Cache

**Geocode Cache**:
- ~100 bytes per district
- 1000 districts ≈ 100 KB
- Never expires

**HTTP Cache**:
- SQLite managed by `requests-cache`
- Default expiration: Session-based
- Can grow large if many unique queries

---

## Extension Guidelines

### Adding a New Preset

**File**: [config.py](config.py)

```python
PRESETS["healthcare"] = {
    "name": "Healthcare",
    "include_all_shops": False,
    "shop_types": ["pharmacy"],
    "amenities": ["hospital", "clinic", "doctors", "dentist"],
    "property_selectors": []
}
```

**No code changes required** - preset automatically appears in UI.

---

### Adding Database Persistence

**Required Changes**:

1. **Replace in-memory job storage**:

```python
# Before (app.py)
current_job = None

# After
from sqlalchemy import create_engine
from models import Job, Result

engine = create_engine('sqlite:///jobs.db')
```

2. **Update endpoints**:

```python
@app.route('/start', methods=['POST'])
def start_job():
    job = Job(districts=districts, ...)
    db.session.add(job)
    db.session.commit()
    return jsonify({'job_id': job.id})

@app.route('/step', methods=['POST'])
def process_step():
    job = Job.query.filter_by(completed=False).first()
    # ... process
    db.session.commit()
```

3. **Add session management** for multi-user support

---

### Adding Confidence Scoring

**Strategy**: Weight streets by attribution method

```python
# In processor.py
class POIAssignment:
    street_name: str
    confidence: float  # 1.0 = addr:street, 0.5-0.9 = nearest

def _attribute_pois_to_streets(self):
    assignments = []

    for poi in self.pois:
        if poi['street']:
            assignments.append(POIAssignment(poi['street'], confidence=1.0))
        else:
            street, distance = self._find_nearest_street_with_distance(poi)
            if street:
                confidence = 1.0 - (distance / self.max_assign_m) * 0.5
                assignments.append(POIAssignment(street, confidence))

    # Aggregate with confidence weighting
    street_scores = defaultdict(float)
    for a in assignments:
        street_scores[a.street_name] += a.confidence

    return street_scores
```

---

### Adding Map Visualization

**Option 1: Leaflet.js** (Client-side)

```html
<!-- In HTML template -->
<div id="map" style="height: 400px;"></div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
const map = L.map('map').setView([51.5074, -0.1278], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Add markers for top streets
topStreets.forEach(street => {
    L.marker([street.lat, street.lon])
        .addTo(map)
        .bindPopup(`${street.name}: ${street.count} POIs`);
});
</script>
```

**Option 2: Static Maps API**

Use Mapbox Static API or Google Static Maps to generate images.

---

### Adding Background Job Processing

**Using Celery**:

```python
# tasks.py
from celery import Celery

app = Celery('streetsignal', broker='redis://localhost:6379')

@app.task
def process_district(district, **kwargs):
    processor = DistrictProcessor(district, **kwargs)
    return processor.process()

# app.py
@app.route('/start', methods=['POST'])
def start_job():
    job_id = str(uuid.uuid4())

    for district in districts:
        process_district.delay(district, radius_m=500, ...)

    return jsonify({'job_id': job_id})
```

**Benefits**:
- Non-blocking requests
- Horizontal scaling
- Job retry on worker failure

---

## Testing Strategy

### Unit Tests

```python
# tests/test_utils.py
def test_haversine_distance():
    # London Eye to Big Ben (~1.2 km)
    d = haversine_distance(51.5033, -0.1195, 51.5007, -0.1246)
    assert 1100 < d < 1300

def test_geocode_cache_hit():
    cache = GeocodingCache()
    cache.set('E1', {'lat': 51.5, 'lon': -0.06})
    result = cache.get('E1')
    assert result == {'lat': 51.5, 'lon': -0.06}
```

### Integration Tests

```python
# tests/test_processor.py
@patch('utils.query_overpass')
@patch('utils.geocode_district')
def test_district_processor(mock_geocode, mock_overpass):
    mock_geocode.return_value = (51.5, -0.06)
    mock_overpass.return_value = load_fixture('overpass_response.json')

    processor = DistrictProcessor('E1')
    result = processor.process()

    assert result['success'] is True
    assert result['total_pois'] > 0
```

### End-to-End Tests

```python
# tests/test_api.py
def test_full_job_flow(client):
    # Start job
    response = client.post('/start', json={
        'districts': 'E1',
        'preset': 'shop',
        'radius_m': 500,
        'max_assign_m': 50
    })
    assert response.status_code == 200

    # Process steps
    response = client.post('/step')
    data = response.get_json()
    assert data['completed'] is True

    # Download CSV
    response = client.get('/download')
    assert response.status_code == 200
    assert 'text/csv' in response.content_type
```

---

## Code Organization Principles

### Separation of Concerns

- **app.py**: HTTP layer, routing, HTML rendering
- **processor.py**: Business logic, data processing
- **utils.py**: External API wrappers, pure functions
- **config.py**: Configuration, no logic

### Single Responsibility

Each function does one thing:
- `geocode_district()`: Only geocoding
- `build_overpass_query()`: Only query construction
- `haversine_distance()`: Only distance calculation

### Dependency Direction

```
app.py → processor.py → utils.py → config.py
                     ↓
              External APIs
```

**Never**: utils.py imports from processor.py

---

## Security Considerations

### Input Validation

**Currently Implemented**:
- District name sanitization (strip, uppercase)
- Numeric bounds on radius_m, max_assign_m

**Recommended Additions**:
- Regex validation for district codes: `^[A-Z]{1,2}[0-9]{1,2}$`
- Limit number of districts per request (e.g., max 50)
- Sanitize CSV output to prevent formula injection

### Rate Limiting (User-facing)

**Recommended**:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/start', methods=['POST'])
@limiter.limit("10 per hour")
def start_job():
    ...
```

### API Key Management

**Currently**: No authentication required for OSM APIs

**If adding paid APIs**:
- Store keys in environment variables
- Never commit to Git
- Use separate keys for dev/prod

---

## Debugging Tips

### Enable Detailed Logging

```python
# app.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Inspect Overpass Queries

Add before `query_overpass()` call:

```python
print("=" * 50)
print(query)
print("=" * 50)
```

Copy query to [Overpass Turbo](https://overpass-turbo.eu/) for visualization.

### Mock External APIs

```python
# tests/conftest.py
@pytest.fixture
def mock_apis():
    with patch('utils.geocode_district') as geocode, \
         patch('utils.query_overpass') as overpass:
        geocode.return_value = (51.5, -0.06)
        overpass.return_value = {'elements': [...]}
        yield geocode, overpass
```

---

## Appendix: OSM Tag Reference

### Common Shop Tags

```
shop=supermarket, convenience, clothes, bakery, butcher,
     florist, jewelry, books, electronics, furniture
```

### Common Amenity Tags

```
amenity=cafe, restaurant, fast_food, bar, pub, bank,
        pharmacy, post_office, library, school, hospital
```

### Highway Types

```
highway=motorway, trunk, primary, secondary, tertiary,
        residential, service, footway, cycleway
```

### Building Tags

```
building=commercial, retail, warehouse, industrial,
         office, apartments, house
```

### Landuse Tags

```
landuse=commercial, retail, industrial, residential,
        farmland, forest
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-28
**Maintainer**: Street Signal Development Team
