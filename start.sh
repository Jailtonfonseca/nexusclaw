#!/bin/bash
# NexusClaw - Script de Inicialização

set -e

echo "=================================="
echo "  NexusClaw - Assistente de IA"
echo "=================================="
echo ""

# Verifica se .env existe
if [ ! -f .env ]; then
    echo "Criando arquivo .env a partir do exemplo..."
    cp .env.example .env
    echo "Por favor, configure o arquivo .env com suas credenciais!"
    exit 1
fi

# Verifica Docker
if ! command -v docker &> /dev/null; then
    echo "Docker não encontrado. Por favor, instale o Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose não encontrado. Por favor, instale."
    exit 1
fi

# Parse argumentos
MODE=${1:-start}

case $MODE in
    start)
        echo "Iniciando NexusClaw..."
        docker-compose up -d
        echo ""
        echo "Serviços iniciados!"
        echo "  - API:        http://localhost:8000"
        echo "  - Qdrant:     http://localhost:6333"
        echo "  - Ollama:     http://localhost:11434"
        echo "  - SearXNG:    http://localhost:8080"
        echo ""
        echo "Para ver logs: docker-compose logs -f"
        ;;
    
    stop)
        echo "Parando NexusClaw..."
        docker-compose down
        ;;
    
    restart)
        echo "Reiniciando NexusClaw..."
        docker-compose restart
        ;;
    
    logs)
        docker-compose logs -f
        ;;
    
    build)
        echo "Construindo NexusClaw..."
        docker-compose build
        ;;
    
    clean)
        echo "Limpando NexusClaw..."
        docker-compose down -v
        echo "Volumes removidos!"
        ;;
    
    *)
        echo "Uso: $0 [start|stop|restart|logs|build|clean]"
        exit 1
        ;;
esac
