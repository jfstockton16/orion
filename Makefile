.PHONY: help install test lint format clean docker-build docker-run dashboard

help:
	@echo "Orion Arbitrage Engine - Available Commands:"
	@echo ""
	@echo "  make install        - Install dependencies"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code with black"
	@echo "  make clean          - Clean temporary files"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run with Docker Compose"
	@echo "  make dashboard      - Launch Streamlit dashboard"
	@echo "  make init-db        - Initialize database"
	@echo "  make dry-run        - Run in dry-run mode"
	@echo "  make logs           - Tail log files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/ *.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build:
	docker build -t orion-arbitrage:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

dashboard:
	streamlit run dashboard.py

init-db:
	python main.py --init-db

dry-run:
	python main.py --dry-run --log-level DEBUG

logs:
	tail -f logs/arbitrage.log

.DEFAULT_GOAL := help
