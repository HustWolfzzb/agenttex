.PHONY: dev-frontend dev-backend build up down logs init

AGENTTEX_PORT ?= 8000

init:
	cd frontend && npm install

dev-frontend:
	cd frontend && npm run dev

dev-backend:
	uvicorn backend.app.main:app --host 127.0.0.1 --port $(AGENTTEX_PORT) --reload &
	celery -A backend.app.tasks.celery_app worker --loglevel=info --concurrency=1

build:
	cd frontend && npm run build
	rm -rf backend/static
	cp -r frontend/dist backend/static

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f
