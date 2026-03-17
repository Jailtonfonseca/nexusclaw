# Guia de Instalação - NexusClaw no Orange Pi 3B

## Especificações do Hardware

| Componente | Especificação |
|------------|---------------|
| **Processador** | Rockchip RK3566 (4x Cortex-A55 @ 1.8GHz) |
| **GPU** | Mali-G52 MP2 |
| **RAM** | 8GB LPDDR4 |
| **Armazenamento** | Cartão microSD ou eMMC (mínimo 32GB classe A2) |

## Instalação Rápida

### 1. Prepare o Sistema Operacional

Recomenda-se usar Armbian ou Ubuntu Server para Orange Pi:

```bash
# Baixe a imagem do Armbian
# https://www.armbian.com/orange-pi-3b/

# Flashe o cartão SD com BalenaEtcher
# ou use dd:
sudo dd if=armbian.img of=/dev/sdX bs=4M status=progress
```

### 2. Configure o Sistema

```bash
# Conecte via SSH (usuário: root, senha: 1234)
ssh root@192.168.x.x

# Atualize o sistema
apt update && apt upgrade -y

# Instale dependências do sistema
apt install -y docker.io docker-compose git curl wget

# Configure o Docker para iniciar automaticamente
systemctl enable docker
systemctl start docker
```

### 3. Configure Memória Swap

```bash
# Adicione 2GB de swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Adicione ao fstab para persistir
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Verifique
free -h
```

### 4. Instale o NexusClaw

```bash
# Clone o repositório
git clone https://github.com/nexus-ai/local-assistant.git
cd nexus-ai

# Use a configuração otimizada para Orange Pi
cp docker-compose.orange-pi.yml docker-compose.yml

# Copie as configurações
cp .env.example .env
nano .env  # Configure conforme necessário
```

### 5. Inicie os Serviços

```bash
# Inicie apenas os serviços essenciais
docker-compose up -d

# Verifique os logs
docker-compose logs -f
```

---

## Modelos Recomendados

Para o Orange Pi 3B com 8GB RAM, os seguintes modelos são recomendados:

### LLM (Language Model)

| Modelo | Tamanho | Tokens/s | RAM |
|--------|---------|----------|-----|
| **Phi-3.5 Mini** | 3.8GB | ~8-12 | ~4GB |
| **Gemma 3 1B** | 2GB | ~15-20 | ~3GB |
| **TinyLlama** | 1GB | ~20-25 | ~2GB |
| **DeepSeek Coder 1.3B** | 2.6GB | ~10-15 | ~3GB |

### Embedding

| Modelo | Tamanho | Uso |
|--------|---------|-----|
| **all-MiniLM-L6-v2** | ~80MB | Busca semântica |
| **BAAI/bge-small-en-v1.5** | ~130MB | Melhor qualidade |

### Comandos para Baixar Modelos

```bash
# Acesse o container Ollama
docker exec -it nexus-ollama ollama pull phi3:mini
docker exec -it nexus-ollama ollama pull gemma:1b
docker exec -it nexus-ollama ollama pull tinyllama

# Para embeddings (execute no host)
docker exec -it nexus-ai python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

---

## Configuração de Desempenho

### Arquivo .env Otimizado

```bash
# Modelo leve
OLLAMA_MODEL=phi3:mini

# Threads limitadas
OLLAMA_NUM_THREADS=4

# Memória
MAX_WORKERS=2

# Contexto reduzido (menor uso de RAM)
OLLAMA_CONTEXT_WINDOW=2048

# Sem flash attention (não suportado)
OLLAMA_FLASH_ATTENTION=0
```

### Configurações do Sistema

```bash
# Adicione ao /etc/sysctl.conf:
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5

# Aplique
sysctl -p
```

---

## Limitações Conhecidas

Devido ao hardware limitado, algumas funcionalidades estão reduzidas:

| Funcionalidade | Status | Notas |
|----------------|--------|-------|
| Memória vetorial | ⚠️ Limitado | Qdrant com 1GB máx |
| Múltiplos canais | ⚠️ 1 por vez | Telegram ou CLI |
| Execução paralela | ❌ Desabilitada | Lentidão |
| Geração de imagens | ❌ Não disponível | Hardware insuficiente |
| Processamento de vídeo | ❌ Não disponível | GPU limitada |

---

## Solução de Problemas

### Lentidão nas Respostas

1. Use modelos menores:
   ```bash
   docker exec -it nexus-ollama ollama pull tinyllama
   ```

2. Reduza o contexto:
   ```bash
   # Edite .env
   OLLAMA_CONTEXT_WINDOW=1024
   ```

### Memória Esgotada

1. Verifique o uso:
   ```bash
   docker stats
   htop
   ```

2. Reduza serviços:
   ```bash
   # Comente qdrant no docker-compose se não necessário
   ```

3. Aumente swap:
   ```bash
   # Adicione mais 2GB
   sudo fallocate -l 2G /swapfile2
   sudo swapon /swapfile2
   ```

### Container não inicia

1. Verifique logs:
   ```bash
   docker-compose logs nexus-ai
   ```

2. Reinicie:
   ```bash
   docker-compose down
   docker system prune -a
   docker-compose up -d
   ```

---

## Uso Recomendado

### Modo Terminal (Recomendado)

```bash
# Acesse o container
docker exec -it nexus-ai python -m nexusclaw.cli
```

### Via Telegram

Configure apenas um canal para melhor performance.

### Via API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá", "user_id": "user1"}'
```

---

## Próximos Passos

1. **Baixe modelos** antes de usar (execute `docker exec -it nexus-ollama ollama pull phi3:mini`)
2. **Configure um canal** (Telegram recomendado)
3. **Comece com conversas simples** para testar

Boa sorte!
