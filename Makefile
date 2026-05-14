.PHONY: setup dev build up down logs clean

PORT ?= 8000

# Non-Docker setup
setup:
	bash setup.sh

# Start in dev mode (frontend + backend + worker)
dev:
	bash start.sh --dev

# Start in production mode
start:
	bash start.sh

# Build frontend only
build:
	cd frontend && npm install && npm run build
	rm -rf backend/static
	cp -r frontend/dist backend/static

# Docker
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	rm -rf frontend/node_modules frontend/dist backend/static .venv data
