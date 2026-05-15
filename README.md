<div align="center">

# ◈ AgentTeX

**Agent-oriented TeX Compiler**

Compile LaTeX projects via Web UI or REST API. Built for humans and AI agents.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18+-61dafb.svg)](https://react.dev)

</div>

---

## Why AgentTeX?

Cloud LaTeX platforms (Overleaf, etc.) impose limits on storage, compile history, and concurrent jobs. With a free account you typically get:
- Limited compile timeout (1-4 min)
- Capped project count and storage
- Compilation history deleted after a few days
- No API access for automation

**AgentTeX runs on your own server — zero limits:**
- **Unlimited compilation history** — every upload, source file, compile log, and PDF is preserved
- **Unlimited storage** — your disk, your rules
- **No timeout pressure** — configurable compile timeout (default 90s, raise it as needed)
- **Full API access** — every feature is a REST endpoint, ready for AI agents and scripts
- **Your data, your control** — nothing leaves your server, no account restrictions

## Features

- **AI-native Web UI** — Glassmorphism dark theme with gradient accents, glow effects, live task monitoring
- **Agent REST API** — Programmatic compilation, file browsing, error diagnosis, stats
- **Unlimited history** — Every compilation preserved: source files, logs, and PDF outputs
- **Smart naming** — Auto-extracts `\title{}` from TeX source, or name manually via API/UI
- **Async compilation** — Celery + Redis task queue, non-blocking
- **XeLaTeX support** — Full TeX Live via `latexmk -xelatex`
- **Security** — Path traversal protection, zip bomb prevention, size/count limits
- **One-command setup** — `bash setup.sh && bash start.sh`

## Quick Start

### Option 1: One-command setup (non-Docker)

```bash
git clone https://github.com/HustWolfzzb/agenttex.git
cd agenttex
bash setup.sh      # Install dependencies & build frontend
bash start.sh      # Start all services
```

Open http://localhost:8000

### Option 2: Docker

```bash
git clone https://github.com/HustWolfzzb/agenttex.git
cd agenttex
docker compose up -d --build
```

### Option 3: Dev mode (hot reload)

```bash
bash setup.sh
bash start.sh --dev    # Frontend on :5173, backend on :8000
```

## API Reference

### Browser Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/compile` | Upload `.zip` (optional `name` field), returns `task_id` |
| `GET` | `/tasks/{id}` | Query compilation status (includes `name`) |
| `GET` | `/tasks/{id}/pdf` | Download compiled PDF |
| `GET` | `/tasks/{id}/view` | View PDF in browser |
| `GET` | `/latest/view` | View latest successful PDF |
| `GET` | `/latest/pdf` | Download latest PDF |

### Agent API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | List tasks (`?status=&limit=`) |
| `GET` | `/api/tasks/{id}/files` | List project files |
| `GET` | `/api/tasks/{id}/files/{path}` | Read source file |
| `GET` | `/api/tasks/{id}/log` | Full compilation log |
| `DELETE` | `/api/tasks/{id}` | Delete task and files |
| `PUT` | `/api/tasks/{id}/rename` | Rename task (`?name=...`) |
| `GET` | `/api/stats` | Service statistics |

Interactive docs at `/docs` (Swagger UI).

### Example: Agent Workflow

```bash
# 1. Compile
curl -F "file=@project.zip" http://localhost:8000/compile
# {"task_id": "abc123...", "status": "pending"}

# 2. Poll
curl http://localhost:8000/tasks/abc123...
# {"task_id": "abc123...", "status": "success", ...}

# 3. Get PDF
curl -O http://localhost:8000/tasks/abc123.../pdf

# 4. Diagnose failure
curl http://localhost:8000/api/tasks/abc123.../log

# 5. Browse project files
curl http://localhost:8000/api/tasks/abc123.../files
```

## Configuration

Environment variables with `AGENTTEX_` prefix (or use `.env`):

```bash
cp .env.example .env
# Edit .env as needed
```

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTTEX_HOST` | `127.0.0.1` | Server host |
| `AGENTTEX_PORT` | `8000` | Server port |
| `AGENTTEX_REDIS_URL` | `redis://localhost:6379/0` | Redis URL |
| `AGENTTEX_MAX_ZIP_SIZE` | `104857600` | Max upload (100MB) |
| `AGENTTEX_MAX_FILE_COUNT` | `1000` | Max files per zip |
| `AGENTTEX_COMPILE_TIMEOUT` | `90` | Timeout (seconds) |
| `AGENTTEX_DATA_DIR` | `./data` | Data storage path |

## Commands

```bash
bash setup.sh           # Install dependencies & build
bash start.sh           # Production mode
bash start.sh --dev     # Dev mode (hot reload)
make build              # Rebuild frontend
make up                 # Docker start
make down               # Docker stop
```

## Tech Stack

- **Backend**: FastAPI + Celery + Redis
- **Frontend**: React + TypeScript + Vite
- **TeX**: TeX Live + latexmk + XeLaTeX
- **Deploy**: Docker multi-stage build or bare metal

## License

[MIT](LICENSE)
