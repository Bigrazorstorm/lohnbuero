# Multi-stage build für AOM (Addison Operations Manager)

# Stage 1: Backend
FROM python:3.11-slim as backend-builder

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Stage 2: Frontend
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json .
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 3: Runtime
FROM python:3.11-slim

# Install Node runtime für Frontend
RUN apt-get update && apt-get install -y --no-cache \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Backend
COPY --from=backend-builder /app/backend /app/backend

# Copy Frontend built assets
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy docker-compose für Referenz
COPY docker-compose.yml .

EXPOSE 5173 8000

# Start Backend (Frontend wird vom Backend serviert)
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
