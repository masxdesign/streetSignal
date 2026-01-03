# StreetSignal

London Retail & Property Street Intelligence Tool - A web application to query OpenStreetMap data, aggregate POIs by street, and rank top streets per postcode district.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open browser to http://127.0.0.1:5001
```

## Features

- **District-based POI Search**: Query London postcode districts (E1, SW1, etc.)
- **Street Ranking**: Identify top 3 streets by POI count
- **Multiple Presets**: Shop, Industrial, Office, and Custom filters
- **CSV Export**: Download results for further analysis
- **Accurate Geocoding**: Uses postcodes.io API for precise district centroids
- **Street Geocoding API**: Get suburb/area and coordinates for any street + district

## Project Structure

```
StreetSignal/
├── app.py              # Flask app entry point
├── processor.py        # District processing logic
├── utils.py            # Geocoding & API utilities
├── config.py           # Configuration & presets
├── requirements.txt    # Python dependencies
├── routes/             # Flask blueprints
│   ├── __init__.py
│   ├── jobs.py         # Job processing endpoints (/, /start, /step, etc.)
│   └── geocode.py      # Geocoding API endpoints
├── templates/          # HTML templates
│   └── index.html
├── docs/               # Documentation
│   ├── README.md
│   ├── DEPLOYMENT.md
│   ├── TECHNICAL_SPEC.md
│   ├── PROJECT_SUMMARY.md
│   └── QUICK_REFERENCE.md
└── test/               # Test scripts
    └── test_*.py
```

## API Endpoints

### Job Processing (Web UI)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Render main page |
| `/start` | POST | Initialize processing job |
| `/step` | POST | Process next district |
| `/download` | GET | Download results as CSV |
| `/reset` | POST | Clear current job |

### Geocoding API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/geocode/street` | GET/POST | Get area + lat/lon for street |
| `/api/geocode/district` | GET/POST | Get centroid lat/lon for district |
| `/api/geocode/bulk` | POST | Bulk geocode streets (max 50) |

#### Street Geocoding Example

```bash
# GET request
curl "http://127.0.0.1:5001/api/geocode/street?postcode=E1&street=Brick%20Lane"

# POST request
curl -X POST http://127.0.0.1:5001/api/geocode/street \
  -H "Content-Type: application/json" \
  -d '{"postcode": "E1", "street": "Brick Lane"}'

# Response
{
  "postcode": "E1",
  "street": "Brick Lane",
  "area": "Spitalfields",
  "lat": 51.5215,
  "lon": -0.0716
}
```

#### Bulk Geocoding Example

```bash
curl -X POST http://127.0.0.1:5001/api/geocode/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"postcode": "E1", "street": "Brick Lane"},
      {"postcode": "W1", "street": "Oxford Street"}
    ]
  }'
```

## Documentation

- **[Full README](docs/README.md)** - Complete documentation
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment
- **[Technical Spec](docs/TECHNICAL_SPEC.md)** - Architecture details
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - API reference

## Key Technologies

- **Backend**: Flask (Python 3.8+)
- **APIs**:
  - postcodes.io (geocoding)
  - Nominatim (fallback geocoding + reverse geocoding)
  - Overpass API (OpenStreetMap data)
- **Caching**: SQLite-based geocode cache
- **Rate Limiting**: pyrate-limiter

## License

MIT License
