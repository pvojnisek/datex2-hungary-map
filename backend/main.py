"""
FastAPI backend for Hungarian Road Network Map.
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import logging
import os

from backend.database import get_database
from backend.models import (
    RoadsResponse,
    PointsResponse,
    SearchResponse,
    Statistics,
    RoadFeature,
    PointFeature,
    SearchResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hungarian Road Network API",
    description="REST API for Hungarian road network DATEX II data",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="frontend/templates")


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    try:
        db = get_database()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the interactive map."""
    try:
        db = get_database()
        stats = db.get_statistics()
        return templates.TemplateResponse(
            "map.html",
            {
                "request": request,
                "center_lat": stats['center']['lat'],
                "center_lon": stats['center']['lon'],
            }
        )
    except Exception as e:
        logger.error(f"Error serving map: {e}")
        return HTMLResponse(content=f"<h1>Error loading map</h1><p>{str(e)}</p>", status_code=500)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db = get_database()
        # Simple query to verify database is working
        stats = db.get_statistics()
        return {
            "status": "healthy",
            "database": "connected",
            "total_points": stats['total_points']
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/stats", response_model=Statistics)
async def get_statistics():
    """Get overall database statistics."""
    try:
        db = get_database()
        stats = db.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/roads", response_model=RoadsResponse)
async def get_roads(
    west: float = Query(..., description="Western longitude"),
    south: float = Query(..., description="Southern latitude"),
    east: float = Query(..., description="Eastern longitude"),
    north: float = Query(..., description="Northern latitude"),
    types: Optional[str] = Query(None, description="Comma-separated road type codes (1,2,3,4)")
):
    """
    Get roads within bounding box.

    Road types:
    - 1: Motorway
    - 2: 1st class road
    - 3: 2nd class road
    - 4: 3rd class road
    """
    try:
        db = get_database()

        # Parse road types
        road_types = None
        if types:
            road_types = [int(t.strip()) for t in types.split(',')]

        roads = db.get_roads_in_bbox(west, south, east, north, road_types)

        return RoadsResponse(
            count=len(roads),
            features=[RoadFeature(**road) for road in roads]
        )
    except Exception as e:
        logger.error(f"Error getting roads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/points", response_model=PointsResponse)
async def get_points(
    west: float = Query(..., description="Western longitude"),
    south: float = Query(..., description="Southern latitude"),
    east: float = Query(..., description="Eastern longitude"),
    north: float = Query(..., description="Northern latitude"),
    categories: Optional[str] = Query(None, description="Comma-separated point type codes")
):
    """
    Get points of interest within bounding box.

    Common point types:
    - 1: Motorway intersection
    - 2: Motorway triangle
    - 3: Motorway junction
    - 12: Cross-roads
    - 17: T-junction
    """
    try:
        db = get_database()

        # Parse categories
        category_list = None
        if categories:
            category_list = [int(c.strip()) for c in categories.split(',')]

        points = db.get_points_in_bbox(west, south, east, north, category_list)

        return PointsResponse(
            count=len(points),
            features=[PointFeature(**point) for point in points]
        )
    except Exception as e:
        logger.error(f"Error getting points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search", response_model=SearchResponse)
async def search_locations(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results")
):
    """Search for locations by name."""
    try:
        db = get_database()
        results = db.search_locations(q, limit)

        return SearchResponse(
            count=len(results),
            results=[SearchResult(**result) for result in results]
        )
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/motorways")
async def get_motorways():
    """Get list of all motorways."""
    try:
        db = get_database()
        motorways = db.get_motorways()
        return {"count": len(motorways), "motorways": motorways}
    except Exception as e:
        logger.error(f"Error getting motorways: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/road/{lcd}")
async def get_road_details(lcd: int):
    """Get detailed information about a specific road."""
    try:
        db = get_database()
        road = db.get_road_details(lcd)

        if not road:
            raise HTTPException(status_code=404, detail="Road not found")

        return road
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting road details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
