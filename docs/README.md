# Street Signal

**London Retail & Property Street Intelligence Tool**

A web-based tool for analyzing London street-level commercial density using OpenStreetMap data. Query multiple postcode districts, aggregate Points of Interest (POIs) by street, and export ranked results.

---

## Features

- **Multi-district batch processing** - Process multiple London postcode districts in one run
- **Flexible presets** - Shop, Industrial, Office, or Custom configurations
- **Smart street attribution** - Uses OSM address tags or nearest-street fallback with Haversine distance
- **Live progress tracking** - Step-by-step processing with real-time UI updates
- **CSV export** - Download results with top 3 streets per district
- **API-safe design** - Respects Nominatim and Overpass rate limits with automatic retry/backoff

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure User Agent

**IMPORTANT**: Before running, edit [config.py](config.py) and update the `USER_AGENT` line with your actual contact information:

```python
USER_AGENT = "StreetSignal/1.0 (your-email@example.com)"
```

This is **required** by Nominatim's usage policy.

### 3. Run the Application

```bash
python app.py
```

Open your browser to: **http://127.0.0.1:5000**

---

## Usage

### Step 1: Select Configuration

1. **Choose a preset**:
   - **Shop** - Retail stores + consumer amenities (cafes, restaurants, etc.)
   - **Industrial** - Warehouses, industrial landuse
   - **Office** - Office buildings
   - **Custom** - Manually select filters

2. **Set parameters**:
   - **Radius (m)** - Search radius around district center (default: 500m)
   - **Max Assign (m)** - Maximum distance to assign POI to nearest street (default: 50m)

### Step 2: Enter Districts

Enter London postcode districts in the text area, one per line or comma-separated:

```
E1
SW1
W1
EC1
```

### Step 3: Run

Click **Run** and watch live progress. Results appear incrementally in the table.

### Step 4: Download

When processing completes, click **Download CSV** to export results.

---

## Architecture

### Tech Stack

- **Backend**: Python 3.10+, Flask
- **Frontend**: Vanilla JavaScript, no build step
- **Storage**: In-memory job state + JSON disk cache for geocoding
- **APIs**: Nominatim (geocoding), Overpass (POI/highway queries)

### Key Files

| File | Purpose |
|------|---------|
| [app.py](app.py) | Flask application with all endpoints and HTML template |
| [processor.py](processor.py) | Core processing logic (POI fetching, street attribution, ranking) |
| [utils.py](utils.py) | Geocoding, caching, Overpass query builders, Haversine distance |
| [config.py](config.py) | Configuration, presets, filter options |
| [requirements.txt](requirements.txt) | Python dependencies |

### Data Flow

1. **Geocode district** → Nominatim API (cached permanently)
2. **Fetch POIs** → Overpass API (shop, amenity, office, building, landuse)
3. **Fetch streets** → Overpass API (highways with names)
4. **Attribute POIs to streets**:
   - Use `addr:street` tag if present
   - Else find nearest named street within `max_assign_m`
5. **Rank streets** → Count POIs per street, return top 3
6. **Export** → Generate CSV from in-memory results

---

## API Usage & Rate Limiting

### Nominatim

- **Purpose**: Geocode district names to coordinates
- **Rate limit**: 1 request per 2 seconds
- **Caching**: Permanent disk cache (`geocode_cache.json`)
- **User-Agent**: **REQUIRED** - must include contact info

### Overpass API

- **Purpose**: Query POIs and highways (streets)
- **Rate limit**: 1 request per second
- **Method**: POST only
- **Timeout**: 240 seconds

All API calls include:
- Exponential backoff retry (up to 3 attempts)
- Jitter to avoid thundering herd
- Automatic rate limiting via `pyrate-limiter`

---

## Deployment Notes

### Safe Environments

✅ Local development
✅ Single-process server (Flask dev server)
✅ Docker container (single worker)

### Unsafe Without Changes

❌ Gunicorn with multiple workers (job state is in-memory)
❌ Serverless (no shared state between invocations)
❌ Read-only filesystem (cache can't be written)

**To scale horizontally**: Replace in-memory job storage with Redis/database.

---

## CSV Output Format

| Column | Description |
|--------|-------------|
| District | Postcode district (e.g., "E1") |
| Street 1 | Top-ranked street name |
| Count 1 | POI count for Street 1 |
| Street 2 | Second-ranked street |
| Count 2 | POI count for Street 2 |
| Street 3 | Third-ranked street |
| Count 3 | POI count for Street 3 |
| Total POIs | Total POIs found in district |
| Total Streets | Total named streets found |
| Status | Success or Error |
| Notes | Error message (if any) |

---

## Customization

### Adding a New Preset

Edit [config.py](config.py):

```python
PRESETS = {
    "retail_parks": {
        "name": "Retail Parks",
        "include_all_shops": True,
        "amenities": ["parking", "fuel"],
        "property_selectors": ["landuse=retail"]
    }
}
```

### Changing Top N Streets

Edit [config.py](config.py):

```python
TOP_N_STREETS = 5  # Default is 3
```

### Adjusting Rate Limits

Edit [config.py](config.py):

```python
NOMINATIM_RATE_LIMIT = 0.5  # requests per second
OVERPASS_RATE_LIMIT = 1.0
```

---

## Troubleshooting

### "Could not geocode district"

- Check spelling of district name
- Ensure district exists in London
- Verify internet connection
- Check Nominatim service status

### Slow Processing

**This is intentional**. Rate limits ensure we respect OSM API policies:
- Nominatim: 1 request per 2 seconds
- Overpass: 1 request per second

Processing 10 districts takes approximately 30-60 seconds.

### No POIs Found

- Try increasing search radius
- Check if preset matches expected POI types
- Verify district is in a commercial area
- Use Custom preset to broaden filters

### Request Timeouts

- Overpass may be under heavy load
- Try again later
- Consider reducing search radius
- The tool automatically retries 3 times with backoff

---

## Development

### Running Tests (Future)

```bash
pytest tests/
```

### Code Structure

```
StreetSignal/
├── app.py              # Flask app + endpoints + HTML
├── processor.py        # District processing logic
├── utils.py            # API wrappers, geocoding, distance calc
├── config.py           # Settings and presets
├── requirements.txt    # Dependencies
└── README.md          # This file
```

### Extension Points

Easy to add:
- Additional presets
- Confidence scoring per street
- Street-level breakdown view
- Borough-level aggregation
- Saved runs (requires database)

---

## License

This project uses OpenStreetMap data, which is © OpenStreetMap contributors and available under the Open Database License (ODbL).

---

## Credits

- **OSM Data**: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors
- **Nominatim**: [Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)
- **Overpass API**: [https://overpass-api.de/](https://overpass-api.de/)

---

## Support

For issues or questions:
1. Check this README first
2. Review [config.py](config.py) for settings
3. Check browser console for JavaScript errors
4. Verify API rate limits aren't being exceeded

---

**Built with transparency and respect for OSM infrastructure.**
