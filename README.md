# StreetSignal

London Retail & Property Street Intelligence Tool - A web application to query OpenStreetMap data, aggregate POIs by street, and rank top streets per postcode district.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open browser to http://127.0.0.1:5000
```

## Features

- **District-based POI Search**: Query London postcode districts (E1, SW1, etc.)
- **Street Ranking**: Identify top 3 streets by POI count
- **Multiple Presets**: Shop, Industrial, Office, and Custom filters
- **CSV Export**: Download results for further analysis
- **Accurate Geocoding**: Uses postcodes.io API for precise district centroids

## Project Structure

```
StreetSignal/
├── app.py              # Flask web application
├── processor.py        # District processing logic
├── utils.py            # Geocoding & API utilities
├── config.py           # Configuration & presets
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   └── index.html
├── docs/              # Documentation
│   ├── README.md
│   ├── DEPLOYMENT.md
│   ├── TECHNICAL_SPEC.md
│   ├── PROJECT_SUMMARY.md
│   └── QUICK_REFERENCE.md
└── test/              # Test scripts
    └── test_*.py
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
  - Nominatim (fallback geocoding)
  - Overpass API (OpenStreetMap data)
- **Caching**: Disk-based JSON + requests-cache SQLite
- **Rate Limiting**: pyrate-limiter

## License

MIT License
