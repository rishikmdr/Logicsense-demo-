.PHONY: start stop reset logs logs-backend logs-dashboard status check demo-url

start:
	@cp -n .env.example .env 2>/dev/null || true
	@echo "Starting LogiSense 360 Demo..."
	docker compose up -d --build
	@echo ""
	@echo "Waiting for services to be ready (this takes ~60s on first run)..."
	@sleep 20
	@docker compose ps
	@echo ""
	@echo "Dashboard: http://localhost"
	@echo "API Docs:  http://localhost/api/docs"
	@echo ""
	@echo "Demo credentials:"
	@echo "  admin@fasttrack.in     / Admin@123"
	@echo "  ops@fasttrack.in       / Ops@123"
	@echo "  finance@fasttrack.in   / Finance@123"
	@echo "  driver1@fasttrack.in   / Driver@123"

stop:
	docker compose down

reset:
	docker compose down -v
	docker compose up -d --build

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-dashboard:
	docker compose logs -f dashboard

status:
	docker compose ps

check:
	python3 health_check.py

demo-url:
	@echo "http://localhost"
