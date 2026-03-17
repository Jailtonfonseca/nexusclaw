#!/bin/bash
# NexusClaw - Script de Instalação Direta no Orange Pi
# Sem Docker, execução nativa para melhor performance

set -e

echo "========================================"
echo "  NexusClaw - Instalação Direta"
echo "  Otimizado para Orange Pi 3B"
echo "========================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verifica se é root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Execute como root: sudo $0${NC}"
    exit 1
fi

echo -e "${GREEN}1. Atualizando sistema...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}2. Instalando dependências...${NC}"
apt install -y \
    python3 python3-pip python3-venv \
    git curl wget \
    libpq-dev build-essential \
    libssl-dev libffi-dev \
    libsqlite3-dev \
    redis-server \
    htop

echo -e "${GREEN}3. Configurando memória swap...${NC}"
if ! grep -q "/swapfile" /etc/fstab; then
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap configurado!"
fi

echo -e "${GREEN}4. Instalando Ollama...${NC}"
# Instala Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configura Ollama para iniciar automaticamente
systemctl enable ollama
systemctl start ollama

echo -e "${GREEN}5. Baixando modelos recomendados...${NC}"
# Modelos leves para 8GB RAM
ollama pull phi3:mini
ollama pull tinyllama

echo -e "${GREEN}6. Configurando Redis...${NC}"
systemctl enable redis-server
systemctl start redis-server

echo -e "${GREEN}7. Instalando NexusClaw...${NC}"
# Cria usuário para NexusClaw
useradd -m -s /bin/bash nexus || true

# Clona ou copia o código
cd /opt
git clone https://github.com/nexus-ai/local-assistant.git nexus-ai || cd nexus-ai

# Cria ambiente virtual
python3 -m venv /opt/nexus-ai/venv
source /opt/nexus-ai/venv/bin/activate

# Instala dependências
pip install --upgrade pip
pip install -r /opt/nexus-ai/requirements.orange-pi.txt

# Permissões
chown -R nexus:nexus /opt/nexus-ai

echo -e "${GREEN}8. Configurando variáveis de ambiente...${NC}"
cat > /opt/nexus-ai/.env << 'EOF'
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# SQLite para banco leve
DATABASE_URL=sqlite:////opt/nexus-ai/data/nexus.db

# Redis local
REDIS_URL=redis://localhost:6379

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
OLLAMA_NUM_THREADS=4
OLLAMA_CONTEXT_WINDOW=2048

# Memória
MAX_WORKERS=2

# Embedding leve
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
EOF

mkdir -p /opt/nexus-ai/data /opt/nexus-ai/logs

echo -e "${GREEN}9. Criando serviço systemd...${NC}"
cat > /etc/systemd/system/nexus-ai.service << 'EOF'
[Unit]
Description=NexusClaw Personal Assistant
After=network.target ollama.service redis-server.service

[Service]
Type=simple
User=nexus
WorkingDirectory=/opt/nexus-ai
Environment="PATH=/opt/nexus-ai/venv/bin:$PATH"
Environment="OLLAMA_HOST=0.0.0.0"
ExecStart=/opt/nexus-ai/venv/bin/python main.py
Restart=always
RestartSec=10
MemoryMax=1.5G

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nexus-ai

echo -e "${GREEN}10. Iniciando serviços...${NC}"
systemctl start nexus-ai
systemctl status nexus-ai --no-pager

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Instalação concluída!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Acesse:"
echo "  - API:        http://localhost:8000"
echo "  - Ollama:    http://localhost:11434"
echo ""
echo "Comandos:"
echo "  sudo systemctl status nexus-ai    # Ver status"
echo "  sudo systemctl restart nexus-ai    # Reiniciar"
echo "  sudo journalctl -u nexus-ai -f    # Ver logs"
echo ""
echo "Modelo instalado: phi3:mini"
echo "Para mudar: sudo systemctl edit nexus-ai"
echo "  (adicione Environment=OLLAMA_MODEL=tinyllama)"
echo ""
