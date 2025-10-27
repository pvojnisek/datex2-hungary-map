#!/bin/bash

# Hungarian Road Network Map - Setup Script

echo "🗺️  Hungarian Road Network Map - Setup"
echo "========================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed"
fi

# Create virtual environment
echo "Creating virtual environment..."
uv venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Check if database exists
if [ ! -f "road_network.duckdb" ]; then
    echo ""
    echo "📊 Database not found. Parsing DAT files..."
    echo "This may take a few minutes..."
    python backend/parser.py data/ road_network.duckdb
    echo "✅ Database created successfully"
else
    echo "✅ Database already exists"
fi

echo ""
echo "🚀 Setup complete!"
echo ""
echo "To start the application:"
echo "  source .venv/bin/activate"
echo "  uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Or use Docker:"
echo "  docker compose up --build"
echo ""
