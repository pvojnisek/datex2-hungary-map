# 🐳 Docker Quick Start Guide

## One Command Setup

```bash
docker compose up --build
```

That's it! Wait 30-60 seconds for first-time setup, then visit **http://localhost:8000**

## What Happens On First Run

The container automatically:

1. ✅ **Checks for database** - looks for `road_network.duckdb`
2. 📊 **Parses DAT files** (first run only)
   - Reads 27 DAT files from `/app/data`
   - Converts coordinates to WGS84
   - Creates spatial indexes
   - Takes ~30-60 seconds
3. 🚀 **Starts web server** - FastAPI on port 8000
4. 🗺️ **Opens for business** - Interactive map ready!

## Expected Output

```
🗺️  Hungarian Road Network Map - Starting...
📊 Database not found. Parsing DAT files...
This will take a few minutes on first startup...
INFO:__main__:Initializing database at /app/road_network.duckdb
INFO:__main__:Spatial extension loaded successfully
INFO:__main__:Creating database tables...
INFO:__main__:Loading data from DAT files...
...
INFO:__main__:Successfully converted 14475 points to WGS84
✅ Database created successfully!
🚀 Starting FastAPI server...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Second Run (Fast!)

On subsequent runs, you'll see:
```
🗺️  Hungarian Road Network Map - Starting...
✅ Database found, skipping parsing
🚀 Starting FastAPI server...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Startup time: **~2 seconds!**

## Stopping the Application

```bash
# Stop containers
docker compose down

# Stop and remove volumes (database will be recreated on next start)
docker compose down -v
```

## Checking Status

```bash
# View logs
docker compose logs -f

# Check if running
docker ps

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/api/stats
```

## Troubleshooting

### Container exits immediately
**Solution**: Check logs with `docker compose logs`

### Port 8000 already in use
**Solution**: Either:
- Stop other services on port 8000
- Or edit `docker-compose.yml` to use different port:
  ```yaml
  ports:
    - "8080:8000"  # Use port 8080 instead
  ```

### "Database not found" error keeps appearing
**Solution**:
1. Check data files exist: `ls data/*.DAT`
2. Rebuild: `docker compose down -v && docker compose up --build`

### Slow parsing
**Solution**: This is normal on first run! Creating 14,475 spatial points takes time.

### Out of memory
**Solution**: Increase Docker memory limit (needs ~2GB)

## Accessing the Application

Once running, access:

- **Interactive Map**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Statistics**: http://localhost:8000/api/stats

## Development Mode

To develop with live reload:

```bash
# Run locally instead of Docker
./setup.sh
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

---

**Need help?** Check the main README.md for more details!
