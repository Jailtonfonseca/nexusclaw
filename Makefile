.PHONY: help build up down restart logs clean install dev test

help:
	@echo "Nexus-AI - Comandos Disponíveis"
	@echo "================================"
	@echo "make build     - Constrói os containers Docker"
	@echo "make up       - Inicia todos os serviços"
	@echo "make down     - Para todos os serviços"
	@echo "make restart  - Reinicia todos os serviços"
	@echo "make logs     - Mostra logs em tempo real"
	@echo "make clean    - Remove containers e volumes"
	@echo "make install  - Instala dependências Python"
	@echo "make dev      - Inicia em modo desenvolvimento"
	@echo "make test     - Executa testes"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	rm -rf data/*

install:
	pip install -r requirements.txt

dev:
	python -m nexus_ai.cli

test:
	pytest -v

# Services
ps:
	docker-compose ps

logs-nexus:
	docker-compose logs -f nexus-ai

logs-ollama:
	docker-compose logs -f ollama

logs-db:
	docker-compose logs -f postgres

# Database
db-reset:
	docker-compose down -v
	docker-compose up -d postgres

# Pull latest images
pull:
	docker-compose pull
