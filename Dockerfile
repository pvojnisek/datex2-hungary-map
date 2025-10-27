# Use Python 3.12 slim image
FROM python:3.12-slim

# Install system dependencies for spatial libraries
RUN apt-get update && apt-get install -y \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY backend ./backend
COPY frontend ./frontend
COPY start.sh ./

# Fix line endings and make startup script executable
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Expose port
EXPOSE 8000

# Health check (give more time for initial startup/parsing)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["/app/start.sh"]
