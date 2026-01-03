# Quick Reference Card

## Street Signal - Essential Commands & Info

---

## 🚀 Quick Start

```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# Manual
python app.py
```

**URL**: http://127.0.0.1:5001

---

## ⚙️ First-Time Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Update User-Agent** in [config.py](config.py:15):
   ```python
   USER_AGENT = "StreetSignal/1.0 (your-email@example.com)"
   ```

3. **Run**: `python app.py`

---

## 📁 Project Structure

```
StreetSignal/
├── app.py              - Flask app entry point
├── processor.py        - POI extraction & street attribution
├── utils.py            - API wrappers, geocoding, distance calc
├── config.py           - Settings and presets
├── requirements.txt    - Python dependencies
├── routes/             - Flask blueprints
│   ├── jobs.py         - Job processing endpoints
│   └── geocode.py      - Geocoding API endpoints
│
├── README.md           - User documentation
├── DEPLOYMENT.md       - Deployment guide
├── TECHNICAL_SPEC.md   - Developer reference
├── PROJECT_SUMMARY.md  - Project overview
└── QUICK_REFERENCE.md  - This file
```

---

## 🎯 Presets

| Preset | Includes |
|--------|----------|
| **Shop** | `shop=*` + cafes, restaurants, bars, pharmacies |
| **Industrial** | `landuse=industrial`, warehouses |
| **Office** | `office=*` |
| **Custom** | User-selected filters |

---

## 🔧 Default Parameters

```python
RADIUS_M = 500          # Search radius around district center
MAX_ASSIGN_M = 50.0     # Max distance to assign POI to street
TOP_N_STREETS = 3       # Number of streets to return per district
```

Edit in [config.py](config.py)

---

## 🌐 API Endpoints

### Job Processing (Web UI)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Render main page |
| `/start` | POST | Initialize job |
| `/step` | POST | Process 1 district |
| `/download` | GET | Download CSV |
| `/reset` | POST | Clear job |

### Geocoding API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/geocode/street` | GET/POST | Street → area + lat/lon |
| `/api/geocode/district` | GET/POST | District → centroid lat/lon |
| `/api/geocode/bulk` | POST | Bulk street geocoding (max 50) |

#### Street Geocoding

```bash
# GET
curl "http://127.0.0.1:5001/api/geocode/street?postcode=E1&street=Brick%20Lane"

# POST
curl -X POST http://127.0.0.1:5001/api/geocode/street \
  -H "Content-Type: application/json" \
  -d '{"postcode": "E1", "street": "Brick Lane"}'

# Response
{"postcode": "E1", "street": "Brick Lane", "area": "Spitalfields", "lat": 51.52, "lon": -0.07}
```

#### Bulk Geocoding

```bash
curl -X POST http://127.0.0.1:5001/api/geocode/bulk \
  -H "Content-Type: application/json" \
  -d '{"items": [{"postcode": "E1", "street": "Brick Lane"}]}'
```

---

## 📊 CSV Output Columns

```
District, Street 1, Count 1, Street 2, Count 2, Street 3, Count 3,
Total POIs, Total Streets, Status, Notes
```

---

## ⏱️ Rate Limits

- **Nominatim**: 1 request per 2 seconds
- **Overpass**: 1 request per second

**Typical processing time**:
- 1 district: ~3-5 seconds
- 10 districts: ~30-60 seconds

---

## 🐛 Troubleshooting

### "Could not geocode district"
- Check spelling (e.g., "E1", "SW1")
- Verify internet connection
- Check Nominatim service status

### "Module not found"
```bash
pip install -r requirements.txt
```

### Port already in use
```bash
# Change port in app.py or kill existing process
lsof -i :5001  # Find process
kill -9 <PID>  # Kill process
```

### Slow processing
**This is normal!** Rate limits are intentional to respect OSM APIs.

---

## 🧪 Sample Test Districts

**London Postcode Districts**:
```
E1      # Whitechapel, Shoreditch
SW1     # Westminster, Belgravia
W1      # West End, Mayfair
EC1     # Clerkenwell, Farringdon
N1      # Islington
SE1     # Southwark, Borough
```

---

## 📝 Common Edits

### Add a New Preset

Edit [config.py](config.py):
```python
PRESETS["healthcare"] = {
    "name": "Healthcare",
    "include_all_shops": False,
    "shop_types": ["pharmacy"],
    "amenities": ["hospital", "clinic", "doctors"],
    "property_selectors": []
}
```

### Change Top N Streets

Edit [config.py](config.py):
```python
TOP_N_STREETS = 5  # Default is 3
```

### Adjust Rate Limits

Edit [config.py](config.py):
```python
NOMINATIM_RATE_LIMIT = 0.5  # requests per second
OVERPASS_RATE_LIMIT = 1.0
```

---

## 🔍 Debug Mode

Enable detailed logging in [app.py](app.py):

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View Overpass queries at: https://overpass-turbo.eu/

---

## 📦 Dependencies

```
Flask==3.0.0         # Web framework
requests==2.31.0     # HTTP library
requests-cache==1.1.1  # HTTP caching
tenacity==8.2.3      # Retry logic
pyrate-limiter==3.1.1  # Rate limiting
```

---

## 🔐 Security Checklist

Before public deployment:
- [ ] Disable debug mode (`debug=False`)
- [ ] Add authentication
- [ ] Enable HTTPS
- [ ] Add rate limiting per IP
- [ ] Set up error monitoring
- [ ] Update User-Agent

---

## 🚢 Deployment

### Single-Process (Safe)
```bash
gunicorn -w 1 -b 0.0.0.0:5001 app:app
```

### Docker
```bash
docker build -t streetsignal .
docker run -p 5001:5001 streetsignal
```

**See [DEPLOYMENT.md](DEPLOYMENT.md) for full checklist.**

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | User guide, features, usage |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment, monitoring, security |
| [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) | Architecture, algorithms, API reference |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview, status |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | This cheat sheet |

---

## 🔗 External Resources

- **Nominatim Policy**: https://operations.osmfoundation.org/policies/nominatim/
- **Overpass API**: https://overpass-api.de/
- **Overpass Turbo**: https://overpass-turbo.eu/
- **OSM Wiki**: https://wiki.openstreetmap.org/
- **Flask Docs**: https://flask.palletsprojects.com/

---

## 🏷️ OSM Tag Reference

### Shop Tags
```
shop=supermarket, convenience, clothes, bakery, butcher,
     florist, jewelry, books, electronics
```

### Amenity Tags
```
amenity=cafe, restaurant, fast_food, bar, pub, bank,
        pharmacy, post_office, library, school
```

### Property Tags
```
office=*
building=commercial, retail, warehouse, industrial
landuse=industrial, commercial, retail
```

---

## 💡 Tips

1. **Start small** - Test with 2-3 districts first
2. **Use cache** - Geocodes are cached permanently
3. **Check results** - Verify top streets make sense for the area
4. **Custom filters** - Use Custom preset for specific needs
5. **Download early** - Get CSV before resetting

---

## ✅ Pre-Flight Checklist

Before running:
- [x] Dependencies installed
- [x] User-Agent updated
- [x] Python 3.10+ available
- [x] Internet connection active
- [x] Port 5001 available

---

## 🎯 Key Files to Know

| File | What |
|------|------|
| `config.py:18` | User-Agent (MUST UPDATE) |
| `config.py:10-11` | Rate limits |
| `config.py:25-26` | Default parameters |
| `config.py:29` | Presets definition |
| `routes/jobs.py` | Job processing endpoints |
| `routes/geocode.py` | Geocoding API endpoints |
| `utils.py` | GeocodeCache class + geocoding functions |

---

## 🆘 Quick Help

**Question**: How do I...?

1. **...add a new preset?** → Edit [config.py](config.py), add to `PRESETS` dict
2. **...change search radius?** → Edit [config.py](config.py), change `DEFAULT_RADIUS_M`
3. **...test Overpass queries?** → Copy query from logs, paste at overpass-turbo.eu
4. **...deploy to production?** → See [DEPLOYMENT.md](DEPLOYMENT.md)
5. **...understand the algorithm?** → See [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)
6. **...report a bug?** → Check logs, review error in CSV Notes column

---

**Built with ❤️ and respect for OSM infrastructure**

*Last updated: 2026-01-03*
