.ONESHELL:

.PHONY: verify lint typecheck test dev up down seed generate-contracts

up:
	docker compose -f docker-compose.yml up -d

down:
	docker compose -f docker-compose.yml down

dev:
	docker compose -f docker-compose.yml up --build

seed:
	docker compose -f docker-compose.yml exec api python seed/seed.py

test:
	set -e
	pytest ../services/api/tests

lint:
	set -e
	ruff check ../services/api

typecheck:
	set -e
	mypy ../services/api/app

verify:
	set -e
	make lint
	make typecheck
	make test

generate-contracts:
	set -e
	@echo "Starting API server for schema extraction..."
	cd ../services/api && uvicorn app.main:app --host 127.0.0.1 --port 8001 &
	API_PID=$$!
	for i in $$(seq 1 30); do \
		python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/api/v1/health')" 2>/dev/null && break; \
		sleep 0.5; \
	done
	npx openapi-typescript http://127.0.0.1:8001/openapi.json --output ../packages/contracts/src/generated/index.ts
	kill $$API_PID
	wait $$API_PID 2>/dev/null || true
	@echo "Contracts generated successfully."
