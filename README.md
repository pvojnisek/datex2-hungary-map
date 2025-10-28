# 🗺️ Hungarian Road Network Interactive Map

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Interactive web-based map of the Hungarian road network using official DATEX II data from Magyar Közút (Hungarian Public Roads).

## Features

- **Interactive Map** with toggleable point layers (motorway junctions, intersections, services)
- **Dynamic Data Loading** - only fetches data for current viewport (high performance)
- **Search Functionality** - search for locations by name
- **Layer Controls** - toggle visibility of 5 different point categories (top-right corner)
- **30 Point Types** - complete icon system for all junction and infrastructure types
- **REST API** - full-featured API for accessing road network data
- **Modern Stack** - DuckDB, FastAPI, Leaflet.js, Docker Compose

## ⚠️ Important: Understanding the Map Display

**What You See on the Map:**

1. **Gray/Colored Roads (Background)**: These come from **OpenStreetMap** (the base layer), providing geographic context
2. **Icons (🔷 ➕ ⭕ 🌉)**: These are **your DATEX II reference points** from Magyar Közút - junctions, bridges, service areas, etc.

**What You DON'T See:**

- **Road lines drawn from your data**: The DATEX II database contains reference points only, not road geometry (the actual paths/lines of roads)

**Why?**

Your data is a **location reference system** designed for traffic management ("accident at M1 Junction 15"), not a complete road map. The OpenStreetMap base layer provides the road visualization, while your Magyar Közút points mark the official reference locations.

## Data Coverage

- **63,488** Location codes
- **14,476** Geographic points with coordinates (junctions, intersections, bridges, tunnels)
- **11,197** Intersections
- **4,199** Road metadata entries
- **3,201** Administrative areas
- **Motorways**: M0-M86 (ring roads and major highways)
- **Road Classifications**: 1st, 2nd, and 3rd class roads

**Data Type**: This DATEX II dataset contains **location reference points** (junctions, intersections, service areas, bridges) but **NOT road geometry** (the actual lines/paths of roads).

**Map Display**:
- **Base Layer (OpenStreetMap)**: Shows actual roads for geographic context
- **Your Data Points**: 14,476 official Magyar Közút reference locations overlaid on top
- **Why No Lines from Your Data**: The database only has point coordinates, not the path geometry between them

Think of it like a **catalog of important landmarks** on the road network rather than a complete street map.

## Technology Stack

- **Database**: DuckDB with spatial extension
- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Leaflet.js
- **Package Manager**: uv (ultra-fast Python package manager)
- **Deployment**: Docker Compose
- **Coordinate System**: EOV (EPSG:23700) → WGS84 (EPSG:4326)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OR Python 3.12+ with uv

### Option 1: Docker (Recommended)

```bash
# 1. Start the application
docker compose up

# 2. Wait for the data parsing (first run only, ~30 seconds)
# You'll see: "📊 Database not found. Parsing DAT files..."
# Then: "✅ Database created successfully!"
# Finally: "🚀 Starting FastAPI server..."

# 3. Open your browser
http://localhost:8000

# Done! The application will automatically parse data on first run.
# Subsequent starts will be instant since the database is already created.
```

**Note**: On first startup, the container will automatically:
- Parse all 27 DAT files
- Create the DuckDB spatial database
- Convert coordinates to WGS84
- Build spatial indexes
- Then start the web server

This takes ~30-60 seconds on first run. After that, startup is instant!

### Option 2: Local Development

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# 3. Parse the DAT files and create DuckDB database
python backend/parser.py data/ road_network.duckdb

# 4. Run the FastAPI server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 5. Open your browser
http://localhost:8000
```

## Project Structure

```
hungarian-road-map/
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Container definition
├── pyproject.toml             # Python dependencies (uv)
├── README.md                  # This file
├── data/                      # Source DAT files
│   ├── ROADS.DAT
│   ├── POINTS.DAT
│   ├── INTERSECTIONS.DAT
│   └── ...
├── backend/
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── database.py           # DuckDB queries
│   ├── parser.py             # DAT file parser
│   └── models.py             # Pydantic models
├── frontend/
│   └── templates/
│       └── map.html          # Interactive map UI
└── road_network.duckdb       # Generated database (after parsing)
```

## API Documentation

Once running, visit:
- **Interactive Map**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### Key Endpoints

#### `GET /api/stats`
Get overall database statistics

```bash
curl http://localhost:8000/api/stats
```

#### `GET /api/roads`
Get roads within bounding box

```bash
curl "http://localhost:8000/api/roads?west=19.0&south=47.0&east=19.5&north=47.5&types=1,2"
```

Parameters:
- `west`, `south`, `east`, `north` - Bounding box (WGS84 coordinates)
- `types` - Optional comma-separated road types (1=motorway, 2=1st class, 3=2nd class, 4=3rd class)

#### `GET /api/points`
Get points of interest within bounding box

```bash
curl "http://localhost:8000/api/points?west=19.0&south=47.0&east=19.5&north=47.5"
```

#### `GET /api/search`
Search for locations by name

```bash
curl "http://localhost:8000/api/search?q=budapest&limit=10"
```

#### `GET /api/motorways`
Get list of all motorways

```bash
curl http://localhost:8000/api/motorways
```

#### `GET /health`
Health check endpoint

```bash
curl http://localhost:8000/health
```

## Map Usage

### Controls

- **Zoom**: Mouse wheel or +/- buttons
- **Pan**: Click and drag
- **Layer Toggle**: ☰ Checkbox panel in **top-right corner** - turn categories on/off
- **Search**: Type location name in the search box (top-left, below info panel)
- **Info**: Click on any icon to see details (name, type, junction number)

### Layer Categories (Toggle On/Off)

Use the layer control in the **top-right corner** to show/hide:

- ☑ **🔷 Motorway Points** (581) - Junctions, exits, entrances on M-roads
- ☑ **➕ Junctions & Intersections** (11,370) - T-junctions, crossroads, roundabouts, link roads
- ☑ **🌉 Infrastructure** - Bridges, tunnels, railroad crossings
- ☑ **⛽ Services & Facilities** - Rest areas, ferry terminals, border crossings
- ☑ **📍 Other Points** - Tourist attractions, airports, churches, traffic cameras

### Complete Icon Guide

**Motorway Features:**
- 🔷 Motorway Junction
- ⚡ Motorway Intersection
- 🔺 Motorway Triangle
- ➡️ Motorway Entrance
- 🔻 Exit

**Junctions (11,370 total):**
- ⊤ T-Junction (7,381)
- ➕ Crossroads (2,684)
- ↗️ Link Road Point (1,877)
- ⭕ Roundabout (499)
- 🔄 Gyratory (793)

**Infrastructure:**
- 🌉 Bridge (8)
- 🚇 Tunnel (1)
- 🚂 Railroad Crossing (5)

**Services:**
- ⛽ Rest Area (110)
- 🍴 Service Area (2)
- ⛴️ Ferry Terminal (99)
- 🚧 Border Crossing (71)

**Note**: The gray/colored roads you see are from **OpenStreetMap** (base layer). Your Magyar Közút data points appear as icons on top.

## Data Processing

The application automatically:

1. **Parses** DAT files (CSV format with `;` delimiter)
2. **Converts** EOV coordinates to WGS84 using DuckDB's ST_Transform
3. **Creates** spatial indexes for fast bounding box queries
4. **Stores** data in optimized DuckDB database

### Manual Database Rebuild

```bash
# Delete existing database
rm road_network.duckdb

# Reparse data
python backend/parser.py data/ road_network.duckdb
```

## Performance Optimization

- **Spatial Indexing**: R-tree indexes on geometry columns
- **Viewport-based Loading**: Only fetches visible data
- **Result Limits**: Maximum 5,000 roads and 10,000 points per query
- **Debounced Loading**: 500ms delay after map movement
- **Read-only Database**: Concurrent queries without locking

## Use Cases

### What This Data Is Perfect For:

1. **Traffic Management Systems**
   - Reference exact locations for traffic events ("Accident at M1 Junction 15")
   - Map real-time incidents to specific junctions
   - Integration with DATEX II traffic feeds

2. **Logistics & Transportation**
   - Identify motorway access points for route planning
   - Locate rest areas for driver breaks (110 locations)
   - Find border crossings for international routes (71 crossings)
   - Ferry terminal locations (99 terminals)

3. **Emergency Services**
   - Reference exact junction locations for dispatch
   - Identify bridge and tunnel locations
   - Border crossing coordination

4. **Data Integration**
   - Combine with OpenStreetMap for complete visualization
   - Link traffic sensor data to specific junctions
   - Connect weather data to road segments
   - GIS analysis in QGIS/ArcGIS (export to GeoJSON)

### What This Data Is NOT For:

- ❌ Turn-by-turn navigation (use OpenStreetMap/Google Maps instead)
- ❌ Complete street maps (only major reference points)
- ❌ Drawing road geometry (points only, no path data)
- ❌ Address geocoding (no address database)

## Development

### Adding New Features

1. **Backend**: Add endpoints in `backend/main.py`
2. **Database**: Add queries in `backend/database.py`
3. **Frontend**: Modify `frontend/templates/map.html`

### Running Tests

```bash
uv pip install pytest
pytest tests/
```

### Code Formatting

```bash
uv pip install black ruff
black backend/
ruff check backend/
```

## Troubleshooting

### Database not found error

Make sure to run the parser first:
```bash
python backend/parser.py data/ road_network.duckdb
```

### No data visible on map

Zoom in to level 9 or higher. Data loading is disabled at low zoom levels for performance. You should see icons (🔷 ➕ ⭕) appear on the map.

### I only see gray roads, no data points

Make sure:
1. You've zoomed in enough (level 9+)
2. The layer control (top-right) has categories checked ☑
3. The gray roads are from OpenStreetMap (base layer) - your data points appear as icons on top

### Where are the road lines from my data?

Your DATEX II data contains **points only** (junctions, bridges, etc.), not road geometry. The roads you see on the map are from the OpenStreetMap base layer, which provides geographic context. See the [DATA_NOTES.md](DATA_NOTES.md) file for a detailed explanation.

### Port 8000 already in use

Change the port in `docker-compose.yml` or use a different port:
```bash
uvicorn backend.main:app --port 8080
```

## Data Source

- **Provider**: Magyar Közút Nonprofit Zrt. (Hungarian Public Roads)
- **Format**: DATEX II
- **Valid**: September 15, 2024 - September 15, 2025
- **Coordinate System**: EOV (EPSG:23700) converted to WGS84 (EPSG:4326)

## License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).

You are free to use, modify, and distribute this software under the terms of the GPL-3.0 license. Any derivative work must also be open source under GPL-3.0 or a compatible license.

See the [LICENSE](LICENSE) file for the full license text.

**Data License**: Road network data is provided by Magyar Közút Nonprofit Zrt. and is subject to their terms of use. The data is included for educational and research purposes.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section above
- Open an issue on GitHub

---

**Built with ❤️ using DuckDB, FastAPI, and Leaflet.js**
