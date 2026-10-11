# Define all phony targets to prevent conflicts with local filenames
.PHONY: help up down logs restart validate clean install shell qdrant-reset rabbitmq-ui redis-cli run-api run-worker env scan-images prune-docker force-up check-port-in-use api-restart api-logs api-health ui-up ui-down ui-logs

# --- CONFIGURATION & PATHS ---
# Load .env variables into Makefile environment (ignore if missing)
-include .env

# Define paths with fallbacks (if not in .env, use defaults)
API_GATEWAY_DIR ?= api_gateway
INFRA_SCRIPTS_DIR ?= infrastructure/scripts
CONFIG_DIR ?= app_config
DATA_DIR ?= .local_data
DOCKER_COMPOSE_FILE ?= docker-compose.yml

# Use virtual environment Python if it exists, otherwise fallback to python3
ifeq ($(wildcard .venv/bin/python),)
	PYTHON_CMD := python3
else
	PYTHON_CMD := .venv/bin/python
endif

# --- DEFAULT HELP MENU ---
help:
	@echo "========================================================================"
	@echo "                       ORTHO RAG PLATFORM WORKFLOW SYSTEM               "
	@echo "========================================================================"
	@echo "Project Root: $(shell pwd)"
	@echo "Scripts Dir : $(INFRA_SCRIPTS_DIR)"
	@echo "Source Dir  : $(INFRA_SCRIPTS_DIR)"
	@echo ""
	@echo "Available Commands:"
	@echo "  make up          - Start all services (Smart check for existing ports)"
	@echo "  make force-up    - Stop existing containers first, then start fresh"
	@echo "  make down        - Stop and remove containers (Preserves $(DATA_DIR))"
	@echo "  make restart     - Restart all running services"
	@echo "  make logs        - View live logs for all services"
	@echo "  make clean       - Remove containers AND wipe local data ($(DATA_DIR))"
	@echo ""
	@echo "FastAPI Container Management:"
	@echo "  make api-restart   - Restart only the FastAPI container"
	@echo "  make api-logs      - View FastAPI container logs"
	@echo "  make api-health    - Check FastAPI health endpoint"
	@echo ""
	@echo "Validation & Setup:"
	@echo "  make validate    - Run infrastructure sanity check (Redis, RMQ, Qdrant, FastAPI)"
	@echo "  make install     - Install Python dependencies"
	@echo "  make env         - Create default .env file if missing"
	@echo ""
	@echo "Application:"
	@echo "  make run-api     - Start FastAPI server (Development mode)"
	@echo "  make run-worker  - Start Celery Worker (Background tasks)"
	@echo "  make shell       - Open Python shell with project path configured"
	@echo ""
	@echo "Security & Optimization:"
	@echo "  make scan-images - Scan Docker images for vulnerabilities (Trivy)"
	@echo "  make prune-docker- Clean up unused Docker resources to save space"
	@echo ""
	@echo "Utilities:"
	@echo "  make qdrant-reset - Delete all Qdrant collections (Use with caution!)"
	@echo "  make rabbitmq-ui  - Open RabbitMQ Management UI in browser"
	@echo "  make redis-cli    - Connect to Redis CLI inside container"
	@echo "========================================================================"

# --- DOCKER MANAGEMENT CORE (SMART) ---

check-port-in-use:
	@if docker ps --filter "name=ortho_redis" --format "{{.Status}}" | grep -q "Up"; then \
		echo "✅ Redis is already running."; \
	else \
		echo "⚠️  Redis not found or stopped."; \
	fi
	@if docker ps --filter "name=ortho_rabbitmq" --format "{{.Status}}" | grep -q "Up"; then \
		echo "✅ RabbitMQ is already running."; \
	else \
		echo "⚠️  RabbitMQ not found or stopped."; \
	fi
	@if docker ps --filter "name=ortho_qdrant" --format "{{.Status}}" | grep -q "Up"; then \
		echo "✅ Qdrant is already running."; \
	else \
		echo "⚠️  Qdrant not found or stopped."; \
	fi
	@if docker ps --filter "name=ortho_api" --format "{{.Status}}" | grep -q "Up"; then \
		echo "✅ FastAPI Container is already running."; \
	else \
		echo "⚠️  FastAPI Container not found or stopped."; \
	fi

up: check-port-in-use
	@echo ""
	@if docker ps --filter "name=ortho_redis" --format "{{.Status}}" | grep -q "Up"; then \
		echo "🔄 Services detected as running. Attempting graceful restart..."; \
		docker compose -f $(DOCKER_COMPOSE_FILE) restart; \
	else \
		echo "🚀 Starting fresh infrastructure..."; \
		docker compose -f $(DOCKER_COMPOSE_FILE) up -d --build; \
	fi
	@echo "⏳ Waiting for services to be healthy (approx 15s)..."
	@sleep 15
	@make validate

force-up:
	@echo "💥 Forcing a clean start (Stopping any existing containers first)..."
	docker compose -f $(DOCKER_COMPOSE_FILE) down --remove-orphans
	docker compose -f $(DOCKER_COMPOSE_FILE) up -d --build
	@sleep 15
	@make validate

down:
	@echo "🛑 Stopping Infrastructure (Preserving $(DATA_DIR))..."
	docker compose -f $(DOCKER_COMPOSE_FILE) down --remove-orphans

restart:
	@echo "🔄 Restarting Infrastructure..."
	docker compose -f $(DOCKER_COMPOSE_FILE) restart
	@sleep 10
	@make validate

logs:
	@echo "📝 Viewing Live Logs..."
	docker compose -f $(DOCKER_COMPOSE_FILE) logs -f --tail=50

clean:
	@echo "⚠️  WARNING: This will delete containers AND wipe local data ($(DATA_DIR))!"
	@read -p "Are you sure? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose -f $(DOCKER_COMPOSE_FILE) down --remove-orphans -v
	rm -rf $(DATA_DIR)/
	@echo "✅ Local data and containers wiped. Next 'make up' will start fresh."

# --- VALIDATION & SETUP (Dynamic Paths) ---

validate:
	@echo "🔍 Running Infrastructure Sanity Check..."
	@if [ ! -f "$(INFRA_SCRIPTS_DIR)/validate_infra.py" ]; then \
		echo "❌ Error: $(INFRA_SCRIPTS_DIR)/validate_infra.py not found."; \
		exit 1; \
	fi
	PYTHONPATH=$(CURDIR) $(PYTHON_CMD) $(INFRA_SCRIPTS_DIR)/validate_infra.py

install:
	@echo "📦 Installing Python Dependencies..."
	@if [ ! -f requirements.txt ]; then \
		echo "❌ Error: requirements.txt not found. Creating a basic one..."; \
		printf "redis\npika\nqdrant-client\ncelery\nfastapi\nuvicorn\npyyaml\n" > requirements.txt; \
	fi
	pip install -r requirements.txt

env:
	@echo "📝 Checking .env file..."
	@if [ ! -f ".env" ]; then \
		echo "✅ Creating default .env..."; \
		printf "# Ortho RAG Platform Configuration\n" > .env; \
		printf "APP_ENV=development\n" >> .env; \
		printf "\n# Project Structure (Editable)\n" >> .env; \
		printf "SCRIPTS_DIR=scripts\n" >> .env; \
		printf "INFRA_SCRIPTS_DIR=src\n" >> .env; \
		printf "CONFIG_DIR=config\n" >> .env; \
		printf "DATA_DIR=.local_data\n" >> .env; \
		printf "DOCKER_COMPOSE_FILE=docker-compose.yml\n" >> .env; \
		printf "\n# YouTube API (Required for Production, Optional for Local Mock Mode)\n" >> .env; \
		printf "YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY_HERE\n" >> .env; \
		printf "\n# Redis\n" >> .env; \
		printf "REDIS_HOST=localhost\n" >> .env; \
		printf "REDIS_PORT=6379\n" >> .env; \
		printf "\n# RabbitMQ\n" >> .env; \
		printf "RABBITMQ_HOST=localhost\n" >> .env; \
		printf "RABBITMQ_PORT=5672\n" >> .env; \
		printf "RABBITMQ_USER=guest\n" >> .env; \
		printf "RABBITMQ_PASSWORD=guest\n" >> .env; \
		printf "\n# Qdrant\n" >> .env; \
		printf "QDRANT_HOST=localhost\n" >> .env; \
		printf "QDRANT_PORT=6333\n" >> .env; \
		printf "QDRANT_COLLECTION_NAME=ortho_rag_corpus\n" >> .env; \
		echo "✅ .env created. Please update YOUTUBE_API_KEY."; \
	else \
		echo "ℹ️  .env already exists."; \
	fi

# --- APPLICATION EXECUTION (Dynamic Paths) ---

run-api:
	@echo "🌐 Starting FastAPI Server..."
	@if [ ! -f "$(API_GATEWAY_DIR)/main.py" ]; then echo "❌ Error: $(API_GATEWAY_DIR)/main.py not found"; exit 1; fi
	uvicorn api_gateway.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	@echo "🐇 Starting Celery Worker..."
	@if [ ! -f "$(INFRA_SCRIPTS_DIR)/tasks.py" ]; then echo "❌ Error: $(INFRA_SCRIPTS_DIR)/tasks.py not found"; exit 1; fi
	cd $(INFRA_SCRIPTS_DIR) && celery -A tasks.celery_app worker --loglevel=info

# --- FASTAPI CONTAINER MANAGEMENT ---

api-restart:
	@echo "🔄 Restarting FastAPI Container..."
	docker compose -f $(DOCKER_COMPOSE_FILE) restart ortho_api
	@sleep 5
	@echo "⏳ Waiting for API to initialize..."
	@sleep 3
	@make api-health

api-logs:
	@echo "📝 Viewing FastAPI Container Logs..."
	docker logs ortho_api -f --tail=50

api-health:
	@echo "🩺 Checking FastAPI Health Endpoint..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Health check failed. Container may not be ready yet."

shell:
	@echo "🐍 Opening Python Shell..."
	$(PYTHON_CMD) -c "import sys, os; sys.path.insert(0, '$(INFRA_SCRIPTS_DIR)'); print('Project loaded. Import Config via src.config.Config')"

# --- SECURITY & OPTIMIZATION ---

scan-images:
	@echo "🛡️  Scanning Docker images for vulnerabilities (Trivy)..."
	@if command -v trivy > /dev/null; then \
		echo "Scanning redis:7-alpine..."; \
		trivy image --severity HIGH,CRITICAL redis:7-alpine || true; \
		echo "Scanning rabbitmq:3-management-alpine..."; \
		trivy image --severity HIGH,CRITICAL rabbitmq:3-management-alpine || true; \
		echo "Scanning qdrant/qdrant:latest..."; \
		trivy image --severity HIGH,CRITICAL qdrant/qdrant:latest || true; \
		echo "✅ Scan complete."; \
	else \
		echo "❌ Trivy not installed. Install with: brew install aquasecurity/trivy/trivy (Mac) or apt install trivy (Linux)."; \
	fi

prune-docker:
	@echo "🧹 Cleaning up unused Docker resources..."
	docker system prune -f --volumes
	@echo "✅ Unused images, containers, and volumes removed."

# --- UTILITIES ---

qdrant-reset:
	@echo "⚠️  WARNING: This will delete ALL collections in Qdrant!"
	@read -p "Are you sure? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	curl -X DELETE http://localhost:6333/collections/ortho_rag_corpus
	curl -X DELETE http://localhost:6333/collections/ortho_rag_test
	@echo "✅ Collections deleted."

rabbitmq-ui:
	@echo "🌐 Opening RabbitMQ Management UI..."
	@if command -v open > /dev/null; then \
		open http://localhost:15672; \
	elif command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:15672; \
	else \
		echo "Please open http://localhost:15672 in your browser manually."; \
	fi

# --- STREAMLIT UI MANAGEMENT ---

ui-up:
	@echo "🎨 Starting Streamlit UI Container..."
	docker compose -f $(DOCKER_COMPOSE_FILE) up -d app_ui
	@sleep 3
	@echo "✅ UI container started!"
	@echo "🌐 Access the UI at: http://localhost:8501"

ui-down:
	@echo "🛑 Stopping Streamlit UI Container..."
	docker compose -f $(DOCKER_COMPOSE_FILE) stop app_ui
	@echo "✅ UI container stopped."

ui-logs:
	@echo "📝 Viewing Streamlit UI Logs..."
	docker logs ortho_app_ui -f --tail=50

# Open UI in browser
ui-open:
	@echo "🌐 Opening Streamlit UI in browser..."
	@if command -v open > /dev/null; then \
		open http://localhost:8501; \
	elif command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:8501; \
	else \
		echo "Please open http://localhost:8501 in your browser manually."; \
	fi

redis-cli:
	@echo "🔴 Connecting to Redis CLI..."
	docker exec -it ortho_redis redis-cli
