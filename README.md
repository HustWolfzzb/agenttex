# AgentTeX

Agent-oriented TeX Compiler — a human-and-agent-friendly LaTeX compilation service with web UI.

Upload an Overleaf project (`.zip`), get a compiled PDF. Designed for both humans and AI agents.

## Features

- **Web UI** — Dark developer-themed interface with drag-and-drop upload, live task monitoring, and PDF preview
- **Agent API** — RESTful endpoints for programmatic compilation, task management, and error diagnosis
- **Async compilation** — Celery + Redis queue, non-blocking
- **XeLaTeX support** — Full TeX Live with `latexmk -xelatex`
- **Security** — Path traversal protection, zip bomb prevention, file size/count limits
- **One-click deploy** — `docker compose up` starts everything

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/HustWolfzzb/agenttex.git
cd agenttex
docker compose up -d --build
```

Open http://localhost:8000

### Local Development

```bash
# Start Redis
redis-server

# Terminal 1: Backend
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --port 8000 --reload &

# Terminal 2: Celery worker
celery -A backend.app.tasks.celery_app worker --loglevel=info --concurrency=1 &

# Terminal 3: Frontend dev server
cd frontend && npm install && npm run dev
```

Frontend dev server runs on http://localhost:5173 with API proxy to port 8000.

## API Reference

### Human / Browser Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/compile` | Upload `.zip`, returns `task_id` |
| `GET` | `/tasks/{id}` | Query compilation status |
| `GET` | `/tasks/{id}/pdf` | Download compiled PDF |
| `GET` | `/tasks/{id}/view` | View PDF in browser |
| `GET` | `/latest/view` | View latest successful PDF |
| `GET` | `/latest/pdf` | Download latest PDF |

### Agent API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | List tasks, supports `?status=&limit=` filtering |
| `GET` | `/api/tasks/{id}/files` | List project files |
| `GET` | `/api/tasks/{id}/files/{path}` | Read source file content |
| `GET` | `/api/tasks/{id}/log` | Full compilation log for error diagnosis |
| `GET` | `/api/stats` | Service statistics |

Full interactive docs available at `/docs` (Swagger UI).

### Example: Agent Workflow

```bash
# 1. Upload and compile
curl -F "file=@project.zip" http://localhost:8000/compile
# {"task_id": "abc123...", "status": "pending"}

# 2. Poll until done
curl http://localhost:8000/tasks/abc123...
# {"task_id": "abc123...", "status": "success", ...}

# 3. Download PDF
curl -O http://localhost:8000/tasks/abc123.../pdf

# 4. On failure, diagnose
curl http://localhost:8000/api/tasks/abc123.../log
```

## Configuration

All settings via environment variables (prefix `AGENTTEX_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTTEX_HOST` | `127.0.0.1` | Server host |
| `AGENTTEX_PORT` | `8000` | Server port |
| `AGENTTEX_REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `AGENTTEX_MAX_ZIP_SIZE` | `104857600` | Max upload size (100MB) |
| `AGENTTEX_MAX_FILE_COUNT` | `1000` | Max files per zip |
| `AGENTTEX_COMPILE_TIMEOUT_SOFT` | `90` | Soft timeout (seconds) |
| `AGENTTEX_COMPILE_TIMEOUT_HARD` | `120` | Hard timeout (seconds) |
| `AGENTTEX_DATA_DIR` | `./data` | Data storage path |

## Tech Stack

- **Backend**: FastAPI + Celery + Redis
- **Frontend**: React + TypeScript + Vite
- **TeX**: TeX Live with latexmk + XeLaTeX
- **Deploy**: Docker multi-stage build

## License

MIT
