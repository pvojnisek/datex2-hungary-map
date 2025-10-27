"""
Database module for querying Hungarian road network data from DuckDB.
"""
import duckdb
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RoadDatabase:
    """Database connection and query manager."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to DuckDB and load spatial extension."""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}. Please run the parser first: python backend/parser.py data/ road_network.duckdb")

        self.conn = duckdb.connect(self.db_path, read_only=True)

        # Install and load spatial extension
        try:
            self.conn.execute("INSTALL spatial;")
        except Exception:
            pass  # Already installed

        self.conn.execute("LOAD spatial;")
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def get_roads_in_bbox(
        self,
        west: float,
        south: float,
        east: float,
        north: float,
        road_types: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get roads within bounding box.

        Args:
            west, south, east, north: Bounding box coordinates (WGS84)
            road_types: Optional list of road type codes (1=motorway, 2=1st class, etc.)
        """
        # Get roads that have points in the bbox - use proper column order for RoadFeature model
        query = """
            SELECT DISTINCT
                r.lcd,
                r.roadnumber,
                r.class,
                r.tcd,
                r.stcd,
                s.sdesc as road_type,
                n.name as start_name,
                '' as end_name,
                MIN(p.lon) as start_lon,
                MIN(p.lat) as start_lat,
                MAX(p.lon) as end_lon,
                MAX(p.lat) as end_lat
            FROM roads r
            LEFT JOIN subtypes s ON r.class = s.class AND r.tcd = s.tcd AND r.stcd = s.stcd
            LEFT JOIN points p ON r.lcd = p.roa_lcd
            LEFT JOIN names n ON r.n1id = n.nid AND n.lid = 1
            WHERE p.lon BETWEEN ? AND ?
                AND p.lat BETWEEN ? AND ?
            GROUP BY r.lcd, r.roadnumber, r.class, r.tcd, r.stcd, s.sdesc, n.name
        """

        params = [west, east, south, north]

        if road_types:
            placeholders = ','.join(['?'] * len(road_types))
            query += f" AND r.stcd IN ({placeholders})"
            params.extend(road_types)

        query += " LIMIT 5000"

        result = self.conn.execute(query, params).fetchall()

        # Convert to list of dicts
        columns = [
            'lcd', 'roadnumber', 'class', 'tcd', 'stcd', 'road_type',
            'start_name', 'end_name', 'start_lon', 'start_lat', 'end_lon', 'end_lat'
        ]

        return [dict(zip(columns, row)) for row in result]

    def get_points_in_bbox(
        self,
        west: float,
        south: float,
        east: float,
        north: float,
        categories: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get POIs (points) within bounding box.

        Args:
            west, south, east, north: Bounding box coordinates (WGS84)
            categories: Optional list of subtype codes to filter
        """
        query = """
            SELECT
                p.lcd,
                p.lon,
                p.lat,
                p.tcd,
                p.stcd,
                s.sdesc as point_type,
                n.name,
                p.junctionnumber as junction_number,
                p.urban
            FROM points p
            LEFT JOIN subtypes s ON p.class = s.class AND p.tcd = s.tcd AND p.stcd = s.stcd
            LEFT JOIN names n ON p.n1id = n.nid AND n.lid = 1
            WHERE p.lon BETWEEN ? AND ?
                AND p.lat BETWEEN ? AND ?
                AND p.geometry IS NOT NULL
        """

        params = [west, east, south, north]

        if categories:
            placeholders = ','.join(['?'] * len(categories))
            query += f" AND p.stcd IN ({placeholders})"
            params.extend(categories)

        query += " LIMIT 10000"

        result = self.conn.execute(query, params).fetchall()

        columns = [
            'lcd', 'lon', 'lat', 'tcd', 'stcd', 'point_type',
            'name', 'junction_number', 'urban'
        ]

        return [dict(zip(columns, row)) for row in result]

    def search_locations(self, query_text: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for locations by name.

        Args:
            query_text: Search string
            limit: Maximum number of results
        """
        query = """
            SELECT DISTINCT
                n.nid,
                n.name,
                n.officialname,
                p.lon,
                p.lat,
                s.sdesc as type
            FROM names n
            LEFT JOIN points p ON n.nid = p.n1id
            LEFT JOIN subtypes s ON p.class = s.class AND p.tcd = s.tcd AND p.stcd = s.stcd
            WHERE LOWER(n.name) LIKE LOWER(?)
                AND p.geometry IS NOT NULL
            LIMIT ?
        """

        result = self.conn.execute(query, [f"%{query_text}%", limit]).fetchall()

        columns = ['nid', 'name', 'officialname', 'lon', 'lat', 'type']

        return [dict(zip(columns, row)) for row in result]

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        stats = {}

        # Total counts
        stats['total_roads'] = self.conn.execute("SELECT COUNT(*) FROM roads").fetchone()[0]
        stats['total_points'] = self.conn.execute(
            "SELECT COUNT(*) FROM points WHERE geometry IS NOT NULL"
        ).fetchone()[0]
        stats['total_intersections'] = self.conn.execute(
            "SELECT COUNT(*) FROM intersections"
        ).fetchone()[0]

        # Road type breakdown
        road_types = self.conn.execute("""
            SELECT s.sdesc, COUNT(*) as cnt
            FROM roads r
            JOIN subtypes s ON r.class = s.class AND r.tcd = s.tcd AND r.stcd = s.stcd
            GROUP BY s.sdesc
            ORDER BY cnt DESC
        """).fetchall()

        stats['road_types'] = [{'type': row[0], 'count': row[1]} for row in road_types]

        # Point type breakdown
        point_types = self.conn.execute("""
            SELECT s.sdesc, COUNT(*) as cnt
            FROM points p
            JOIN subtypes s ON p.class = s.class AND p.tcd = s.tcd AND p.stcd = s.stcd
            WHERE p.geometry IS NOT NULL
            GROUP BY s.sdesc
            ORDER BY cnt DESC
            LIMIT 20
        """).fetchall()

        stats['point_types'] = [{'type': row[0], 'count': row[1]} for row in point_types]

        # Bounding box
        bbox = self.conn.execute("""
            SELECT
                MIN(lon) as min_lon,
                MIN(lat) as min_lat,
                MAX(lon) as max_lon,
                MAX(lat) as max_lat
            FROM points
            WHERE geometry IS NOT NULL
        """).fetchone()

        stats['bbox'] = {
            'west': bbox[0],
            'south': bbox[1],
            'east': bbox[2],
            'north': bbox[3]
        }

        # Center point
        stats['center'] = {
            'lon': (bbox[0] + bbox[2]) / 2,
            'lat': (bbox[1] + bbox[3]) / 2
        }

        return stats

    def get_motorways(self) -> List[Dict[str, Any]]:
        """Get all motorways (M roads)."""
        query = """
            SELECT DISTINCT
                r.roadnumber,
                COUNT(*) as segment_count
            FROM roads r
            WHERE r.roadnumber LIKE 'M%'
            GROUP BY r.roadnumber
            ORDER BY r.roadnumber
        """

        result = self.conn.execute(query).fetchall()
        return [{'road': row[0], 'segments': row[1]} for row in result]

    def get_road_details(self, road_lcd: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific road."""
        query = """
            SELECT
                r.*,
                s.sdesc as road_type,
                n1.name as start_name,
                n2.name as end_name
            FROM roads r
            LEFT JOIN subtypes s ON r.class = s.class AND r.tcd = s.tcd AND r.stcd = s.stcd
            LEFT JOIN names n1 ON r.n1id = n1.nid AND n1.lid = 1
            LEFT JOIN names n2 ON r.n2id = n2.nid AND n2.lid = 1
            WHERE r.lcd = ?
        """

        result = self.conn.execute(query, [road_lcd]).fetchone()

        if not result:
            return None

        columns = [desc[0] for desc in self.conn.description]
        return dict(zip(columns, result))


# Global database instance
_db: Optional[RoadDatabase] = None


def get_database() -> RoadDatabase:
    """Get database instance (singleton pattern)."""
    global _db
    if _db is None:
        import os
        db_path = os.getenv('DUCKDB_PATH', './road_network.duckdb')
        _db = RoadDatabase(db_path)
        _db.connect()
    return _db
