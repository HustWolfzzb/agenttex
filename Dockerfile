# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime with TeX Live
FROM texlive/texlive:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY backend/app ./backend/app/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./backend/static

RUN mkdir -p /app/data/uploads /app/data/projects /app/data/output

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
