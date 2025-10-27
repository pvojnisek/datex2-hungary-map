"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class BoundingBox(BaseModel):
    """Bounding box coordinates."""
    west: float = Field(..., description="Western longitude")
    south: float = Field(..., description="Southern latitude")
    east: float = Field(..., description="Eastern longitude")
    north: float = Field(..., description="Northern latitude")


class RoadFeature(BaseModel):
    """Road feature data."""
    lcd: int
    roadnumber: Optional[str] = None
    class_: str = Field(alias='class')
    tcd: int
    stcd: int
    road_type: Optional[str] = None
    start_name: Optional[str] = None
    end_name: Optional[str] = None
    start_lon: Optional[float] = None
    start_lat: Optional[float] = None
    end_lon: Optional[float] = None
    end_lat: Optional[float] = None

    class Config:
        populate_by_name = True


class PointFeature(BaseModel):
    """Point of Interest feature data."""
    lcd: int
    lon: float
    lat: float
    tcd: int
    stcd: int
    point_type: Optional[str] = None
    name: Optional[str] = None
    junction_number: Optional[str] = None
    urban: Optional[int] = None


class SearchResult(BaseModel):
    """Location search result."""
    nid: int
    name: str
    officialname: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    type: Optional[str] = None


class Statistics(BaseModel):
    """Database statistics."""
    total_roads: int
    total_points: int
    total_intersections: int
    road_types: List[Dict[str, Any]]
    point_types: List[Dict[str, Any]]
    bbox: Dict[str, float]
    center: Dict[str, float]


class Motorway(BaseModel):
    """Motorway information."""
    road: str
    segments: int


class RoadsResponse(BaseModel):
    """Response for roads endpoint."""
    count: int
    features: List[RoadFeature]


class PointsResponse(BaseModel):
    """Response for points endpoint."""
    count: int
    features: List[PointFeature]


class SearchResponse(BaseModel):
    """Response for search endpoint."""
    count: int
    results: List[SearchResult]
