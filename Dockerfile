# Production Dockerfile — single container serving FastAPI + React frontend
# Used by Render, Railway, or any Docker-based cloud platform.

# --- Stage 1: Build frontend ---
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# --- Stage 2: Python backend + static frontend ---
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source
COPY backend/ /app/

# Copy built frontend into the static directory FastAPI will serve
COPY --from=frontend-build /build/dist /app/app/static

# Copy data files for seeding
COPY data/ /app/data/

# Default port (Render uses PORT env var)
ENV PORT=10000

CMD ["sh", "-c", "python -m scripts.setup_cloud_db && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
