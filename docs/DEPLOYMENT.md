# Deployment Checklist

## Pre-Deployment

### 1. Configuration

- [ ] Update `USER_AGENT` in [config.py](config.py) with real contact email
- [ ] Review rate limits in [config.py](config.py) (default: safe for OSM APIs)
- [ ] Set `DEBUG = False` in production (modify [app.py](app.py))

### 2. Dependencies

- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify versions: `pip list`

### 3. Testing

- [ ] Test geocoding: Try "E1", "SW1" districts
- [ ] Test each preset: Shop, Industrial, Office, Custom
- [ ] Test CSV export
- [ ] Test error handling: Invalid district name
- [ ] Test reset functionality

---

## Local Deployment (Development)

### Run Server

```bash
python app.py
```

Access at: http://127.0.0.1:5000

**Safe for**: Single user, development, testing

---

## Production Deployment Options

### Option 1: Single-Process Server (Recommended for MVP)

**Safe**: Yes (with current in-memory job storage)

```bash
# Install Gunicorn
pip install gunicorn

# Run with 1 worker only
gunicorn -w 1 -b 0.0.0.0:5000 app:app
```

**Important**: Do NOT use multiple workers without migrating job storage to Redis/database.

### Option 2: Docker Container

**Safe**: Yes

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# IMPORTANT: Update config.py USER_AGENT before building
EXPOSE 5000

CMD ["python", "app.py"]
```

Build and run:

```bash
docker build -t streetsignal .
docker run -p 5000:5000 streetsignal
```

### Option 3: Multi-Worker (Requires Changes)

**Safe**: No (not without code changes)

Required changes:
1. Replace in-memory `current_job` with Redis
2. Use session IDs to track jobs per user
3. Add cleanup for abandoned jobs

---

## Security Checklist

### Before Public Deployment

- [ ] Disable Flask debug mode (`app.run(debug=False)`)
- [ ] Add authentication if not intended for public use
- [ ] Set up HTTPS/TLS
- [ ] Add CORS headers if needed
- [ ] Implement request logging
- [ ] Add input validation for all parameters
- [ ] Set up error monitoring (e.g., Sentry)

### Rate Limiting

- [ ] Consider adding per-IP rate limiting (Flask-Limiter)
- [ ] Monitor API usage to avoid OSM bans
- [ ] Add user-facing rate limit warnings

---

## Environment-Specific Settings

### Development

```python
# app.py
app.run(debug=True, host='127.0.0.1', port=5000)
```

### Production

```python
# app.py
app.run(debug=False, host='0.0.0.0', port=5000)
```

Or use Gunicorn (preferred):

```bash
gunicorn -w 1 -b 0.0.0.0:5000 --timeout 300 app:app
```

---

## Monitoring

### Key Metrics

- Request success/failure rates
- API response times (Nominatim, Overpass)
- Cache hit rates
- Job completion rates

### Logs to Monitor

- Geocoding failures
- Overpass timeouts
- Retry exhaustion
- District processing errors

### Health Check Endpoint (Add to app.py)

```python
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})
```

---

## Backup & Recovery

### What to Backup

✅ `geocode_cache.json` - Saves API calls
✅ `config.py` - Custom settings
❌ Job state - Ephemeral by design

### Cache Recovery

If `geocode_cache.json` is lost:
- Will regenerate on next run
- Expect slower initial processing
- No data loss, just re-queries Nominatim

---

## Scaling Considerations

### When Current Architecture Works

- < 100 requests per day
- Single user or small team
- Non-concurrent usage

### When to Upgrade

If you need:
- **Multiple concurrent users** → Add Redis for job storage
- **Background processing** → Add Celery task queue
- **Historical data** → Add PostgreSQL/SQLite database
- **High availability** → Load balancer + shared storage

---

## Troubleshooting Deployment

### "Address already in use"

Another process is using port 5000:

```bash
# Find process
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Change port in app.py or use different port
python app.py --port 5001
```

### Import Errors

```bash
# Verify virtual environment is activated
which python  # Should point to venv

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Cache Permission Errors

Ensure write permissions for:
- `geocode_cache.json`
- `http_cache.sqlite`

```bash
chmod 644 geocode_cache.json  # If exists
```

### Overpass Timeouts

Increase timeout in [config.py](config.py):

```python
OVERPASS_TIMEOUT = 300  # 5 minutes
```

And in Gunicorn:

```bash
gunicorn -w 1 --timeout 600 app:app
```

---

## Post-Deployment Verification

### Smoke Tests

1. [ ] Access homepage - loads correctly
2. [ ] Select preset - UI updates
3. [ ] Enter district - no validation errors
4. [ ] Run job - progress bar appears
5. [ ] Check results - table populates
6. [ ] Download CSV - file downloads
7. [ ] Reset - UI clears

### API Tests

```bash
# Test geocoding (requires running server)
curl http://localhost:5000/

# Start job
curl -X POST http://localhost:5000/start \
  -H "Content-Type: application/json" \
  -d '{"districts": "E1", "preset": "shop", "radius_m": 500, "max_assign_m": 50}'

# Process step
curl -X POST http://localhost:5000/step

# Reset
curl -X POST http://localhost:5000/reset
```

---

## Rollback Plan

If deployment fails:

1. Stop server: `Ctrl+C` or `docker stop <container>`
2. Check logs for errors
3. Restore previous [config.py](config.py) if changed
4. Clear corrupted cache: `rm geocode_cache.json http_cache.sqlite`
5. Restart with known-good version

---

## Support Contacts

- **OSM Nominatim**: [Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)
- **Overpass API**: [https://overpass-api.de/](https://overpass-api.de/)
- **Flask Docs**: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)

---

**Remember**: This tool is designed to be **transparent and respectful** of external APIs. Rate limiting is non-negotiable.
