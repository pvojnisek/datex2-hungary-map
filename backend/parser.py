"""
Parser for Hungarian road network DATEX II DAT files.
Converts data to DuckDB with spatial extension.
"""
import pandas as pd
import duckdb
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoadDataParser:
    """Parse DATEX II DAT files and load into DuckDB."""

    def __init__(self, data_dir: str, db_path: str):
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        self.conn = None

    def _read_dat_file(self, filename: str) -> Optional[pd.DataFrame]:
        """Read a DAT file with proper encoding."""
        file_path = self.data_dir / filename
        if not file_path.exists():
            logger.warning(f"File not found: {filename}")
            return None

        try:
            # Read with UTF-8 BOM encoding, semicolon delimiter
            df = pd.read_csv(
                file_path,
                sep=';',
                encoding='utf-8-sig',
                low_memory=False
            )
            logger.info(f"Loaded {filename}: {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            return None

    def initialize_database(self):
        """Initialize DuckDB with spatial extension."""
        logger.info(f"Initializing database at {self.db_path}")
        self.conn = duckdb.connect(self.db_path)

        # Install and load spatial extension
        self.conn.execute("INSTALL spatial;")
        self.conn.execute("LOAD spatial;")

        logger.info("Spatial extension loaded successfully")

    def parse_coordinates(self, coord_str: str) -> Optional[float]:
        """
        Parse coordinates from DATEX II format like '+01871379'
        These are WGS84 decimal degrees * 100000
        Returns decimal degrees
        """
        if pd.isna(coord_str):
            return None

        # Remove leading '+' and convert to float
        coord_str = str(coord_str).strip()
        if coord_str.startswith('+'):
            coord_str = coord_str[1:]

        try:
            # Coordinates are decimal degrees * 100000
            value = float(coord_str) / 100000.0
            return value
        except (ValueError, AttributeError):
            return None

    def create_tables(self):
        """Create all necessary tables with spatial support."""
        logger.info("Creating database tables...")

        # Countries table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                cid INTEGER,
                ecc VARCHAR,
                ccd VARCHAR,
                cname VARCHAR,
                PRIMARY KEY (cid)
            )
        """)

        # Types and Subtypes
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS types (
                class VARCHAR,
                tcd INTEGER,
                tdesc VARCHAR,
                tnatcd VARCHAR,
                tnatdesc VARCHAR,
                PRIMARY KEY (class, tcd)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS subtypes (
                class VARCHAR,
                tcd INTEGER,
                stcd INTEGER,
                sdesc VARCHAR,
                snatcode VARCHAR,
                snatdesc VARCHAR,
                PRIMARY KEY (class, tcd, stcd)
            )
        """)

        # Administrative areas
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS administrative_areas (
                cid INTEGER,
                tabcd INTEGER,
                lcd INTEGER,
                class VARCHAR,
                tcd INTEGER,
                stcd INTEGER,
                nid INTEGER,
                pol_lcd INTEGER,
                PRIMARY KEY (cid, tabcd, lcd)
            )
        """)

        # Roads (linear features)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS roads (
                cid INTEGER,
                tabcd INTEGER,
                lcd INTEGER,
                class VARCHAR,
                tcd INTEGER,
                stcd INTEGER,
                roadnumber VARCHAR,
                rnid INTEGER,
                n1id INTEGER,
                n2id INTEGER,
                pol_lcd INTEGER,
                pes_lev VARCHAR,
                rdid VARCHAR,
                PRIMARY KEY (cid, tabcd, lcd)
            )
        """)

        # Points (with spatial geometry)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS points (
                cid INTEGER,
                tabcd INTEGER,
                lcd INTEGER,
                class VARCHAR,
                tcd INTEGER,
                stcd INTEGER,
                junctionnumber VARCHAR,
                rnid INTEGER,
                n1id INTEGER,
                n2id INTEGER,
                pol_lcd INTEGER,
                oth_lcd INTEGER,
                seg_lcd INTEGER,
                roa_lcd INTEGER,
                inpos INTEGER,
                inneg INTEGER,
                outpos INTEGER,
                outneg INTEGER,
                presentpos INTEGER,
                presentneg INTEGER,
                diversionpos VARCHAR,
                diversionneg VARCHAR,
                xcoord VARCHAR,
                ycoord VARCHAR,
                interruptsroad VARCHAR,
                urban INTEGER,
                jnid VARCHAR,
                eov_x DOUBLE,
                eov_y DOUBLE,
                lon DOUBLE,
                lat DOUBLE,
                geometry GEOMETRY,
                PRIMARY KEY (cid, tabcd, lcd)
            )
        """)

        # Intersections
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS intersections (
                cid INTEGER,
                tabcd INTEGER,
                lcd INTEGER,
                int_cid INTEGER,
                int_tabcd INTEGER,
                int_lcd INTEGER,
                PRIMARY KEY (cid, tabcd, lcd, int_cid, int_tabcd, int_lcd)
            )
        """)

        # Names
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS names (
                cid INTEGER,
                lid INTEGER,
                nid INTEGER,
                name VARCHAR,
                ncomment VARCHAR,
                officialname VARCHAR,
                PRIMARY KEY (cid, lid, nid)
            )
        """)

        logger.info("Tables created successfully")

    def load_data(self):
        """Load all DAT files into database."""
        logger.info("Loading data from DAT files...")

        # Load simple tables
        files_to_load = {
            'COUNTRIES.DAT': 'countries',
            'TYPES.DAT': 'types',
            'SUBTYPES.DAT': 'subtypes',
            'ADMINISTRATIVEAREA.DAT': 'administrative_areas',
            'ROADS.DAT': 'roads',
            'INTERSECTIONS.DAT': 'intersections',
            'NAMES.DAT': 'names',
        }

        for filename, table_name in files_to_load.items():
            df = self._read_dat_file(filename)
            if df is not None:
                # Clean column names (lowercase)
                df.columns = df.columns.str.lower()

                # Insert into table
                self.conn.execute(f"DELETE FROM {table_name}")
                self.conn.register('temp_df', df)
                self.conn.execute(f"INSERT INTO {table_name} SELECT * FROM temp_df")
                self.conn.unregister('temp_df')

                logger.info(f"Loaded {len(df)} rows into {table_name}")

        # Load points with coordinate processing
        self._load_points()

    def _load_points(self):
        """Load points with coordinate conversion."""
        logger.info("Processing points with coordinates...")

        df = self._read_dat_file('POINTS.DAT')
        if df is None:
            return

        df.columns = df.columns.str.lower()

        # Parse coordinates (already in WGS84 format, just encoded as * 100000)
        df['lon'] = df['xcoord'].apply(self.parse_coordinates)
        df['lat'] = df['ycoord'].apply(self.parse_coordinates)

        # Keep eov_x and eov_y as NULL (we don't have EOV data, coordinates are already WGS84)
        df['eov_x'] = None
        df['eov_y'] = None

        # Remove rows with invalid coordinates
        df_valid = df[df['lon'].notna() & df['lat'].notna()].copy()

        logger.info(f"Valid coordinates: {len(df_valid)}/{len(df)} points")

        # Insert into database (specify columns explicitly to avoid mismatch)
        self.conn.execute("DELETE FROM points")
        self.conn.register('temp_points', df_valid)

        # Get column names from dataframe
        cols = ', '.join(df_valid.columns)

        self.conn.execute(f"INSERT INTO points ({cols}) SELECT {cols} FROM temp_points")
        self.conn.unregister('temp_points')

        # Create geometry from lon/lat (already in WGS84)
        logger.info("Creating geometries from WGS84 coordinates...")
        self.conn.execute("""
            UPDATE points
            SET geometry = ST_Point(lon, lat)
            WHERE lon IS NOT NULL AND lat IS NOT NULL
        """)

        count = self.conn.execute("""
            SELECT COUNT(*) FROM points WHERE geometry IS NOT NULL
        """).fetchone()[0]

        logger.info(f"Successfully converted {count} points to WGS84")

    def create_indexes(self):
        """Create spatial and regular indexes for performance."""
        logger.info("Creating indexes...")

        # Create spatial index on points
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_points_geometry
            ON points USING RTREE (geometry)
        """)

        # Regular indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_roads_roadnumber ON roads(roadnumber)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_roads_class ON roads(class, tcd, stcd)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_points_type ON points(class, tcd, stcd)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_names_nid ON names(nid)")

        logger.info("Indexes created successfully")

    def get_stats(self):
        """Print database statistics."""
        logger.info("Database Statistics:")

        tables = ['countries', 'types', 'subtypes', 'administrative_areas',
                  'roads', 'points', 'intersections', 'names']

        for table in tables:
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            logger.info(f"  {table}: {count:,} rows")

        # Points with valid geometry
        geo_count = self.conn.execute("""
            SELECT COUNT(*) FROM points WHERE geometry IS NOT NULL
        """).fetchone()[0]
        logger.info(f"  Points with geometry: {geo_count:,}")

        # Road types breakdown
        logger.info("\nRoad types:")
        road_types = self.conn.execute("""
            SELECT s.sdesc, COUNT(*) as cnt
            FROM roads r
            JOIN subtypes s ON r.class = s.class AND r.tcd = s.tcd AND r.stcd = s.stcd
            GROUP BY s.sdesc
            ORDER BY cnt DESC
        """).fetchall()

        for desc, cnt in road_types:
            logger.info(f"  {desc}: {cnt:,}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Main entry point for parsing data."""
    import sys

    data_dir = sys.argv[1] if len(sys.argv) > 1 else "./data"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "./road_network.duckdb"

    parser = RoadDataParser(data_dir, db_path)

    try:
        parser.initialize_database()
        parser.create_tables()
        parser.load_data()
        parser.create_indexes()
        parser.get_stats()
    finally:
        parser.close()

    logger.info(f"✅ Database created successfully at {db_path}")


if __name__ == "__main__":
    main()
