# ========================================
# AI Ops Engineer - Makefile
# ========================================
# Easy commands for development and deployment

.PHONY: help install run test clean docker-up docker-down

# Default target
help:
	@echo "=========================================="
	@echo "  AI Ops Engineer - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "  make install     - Install all dependencies"
	@echo "  make run         - Run backend and frontend"
	@echo "  make run-backend - Run only backend"
	@echo "  make run-frontend- Run only frontend"
	@echo "  make test        - Run all tests"
	@echo "  make clean       - Clean generated files"
	@echo "  make docker-up   - Start with Docker"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make seed        - Populate sample data"
	@echo ""

# ========================================
# Installation
# ========================================
install: install-backend install-frontend
	@echo "✅ All dependencies installed!"

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && python -m venv venv && \
	. venv/Scripts/activate && \
	pip install -r requirements.txt
	@echo "✅ Backend dependencies installed!"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed!"

# ========================================
# Development
# ========================================
run-backend:
	@echo "🚀 Starting backend server..."
	cd backend && . venv/Scripts/activate && uvicorn main:app --reload

run-frontend:
	@echo "🚀 Starting frontend server..."
	cd frontend && npm run dev

run:
	@echo "🚀 Starting both servers..."
	@make -j2 run-backend run-frontend

# ========================================
# Testing
# ========================================
test: test-backend test-frontend
	@echo "✅ All tests passed!"

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && . venv/Scripts/activate && pytest -v

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test

# ========================================
# Docker
# ========================================
docker-up:
	@echo "🐳 Starting Docker containers..."
	docker-compose up --build -d
	@echo "✅ Containers running!"
	@echo "   Frontend: http://localhost:5173"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped!"

docker-logs:
	docker-compose logs -f

# ========================================
# Utilities
# ========================================
seed:
	@echo "🌱 Seeding sample data..."
	cd backend && . venv/Scripts/activate && python scripts/seed_data.py
	@echo "✅ Sample data loaded!"

clean:
	@echo "🧹 Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/venv 2>/dev/null || true
	@echo "✅ Cleaned!"

# ========================================
# Production
# ========================================
build:
	@echo "📦 Building for production..."
	cd frontend && npm run build
	@echo "✅ Production build ready!"

deploy:
	@echo "🚀 Deploying..."
	./scripts/deploy.sh
	@echo "✅ Deployed!"
