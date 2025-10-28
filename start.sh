#!/bin/bash
set -e

echo "🗺️  Hungarian Road Network Map - Starting..."

# Create db directory if it doesn't exist
mkdir -p /app/db

# Check if database exists
if [ ! -f "/app/db/road_network.duckdb" ]; then
    echo "📊 Database not found. Parsing DAT files..."
    echo "This will take a few minutes on first startup..."
    python /app/backend/parser.py /app/data /app/db/road_network.duckdb
    echo "✅ Database created successfully!"
else
    echo "✅ Database found, skipping parsing"
fi

echo "🚀 Starting FastAPI server..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
