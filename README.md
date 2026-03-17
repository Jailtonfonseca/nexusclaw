# NexusClaw 🎯
**Seu Assistente de IA Pessoal Soberano - 100% Local**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-green?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-Local-blue?style=for-the-badge&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

> Um orquestrador de IA pessoal, 100% auto-hospedado, que centraliza sua vida digital. Atua como um "segundo cérebro" com memória infinita, acessível via qualquer plataforma de chat, capaz de executar tarefas autônomas.

## ✨ Funcionalidades

### 🎧 Multi-Canais
- **Telegram** - Bot com suporte a comandos, voz e arquivos
- **Discord** - Bot com threads e moderação
- **Terminal/CLI** - Interface direta via SSH
- **WhatsApp** - Via integração local
- **Web API** - Endpoints REST/WebSocket

### 🧠 Memória Inteligente
- **Memória Episódica** - Lembra de conversas passadas via busca semântica
- **Memória de Fatos** - Extrai e armazena entidades importantes
- **Contexto Deslizante** - Mantém relevância em longas conversas

### 🔧 Sistema de Habilidades
- **Busca na Web** - Via SearXNG local (privado)
- **Gerenciamento de Arquivos** - Ler/escrever no sistema local
- **Execução de Código** - Scripts Python/Bash em sandbox
- **Agendamento** - Lembretes e tarefas futuras
- **Extensível** - Adicione seus próprios plugins!

### 🤖 Modo Autônomo
- Receba objetivos complexos e veja o agente quebrar em tarefas
- Exemplo: "Pesquise preços de SSDs, crie planilha e mande no Telegram"

## 🚀 Quick Start

### Pré-requisitos
- Docker e Docker Compose
- 8GB RAM mínimo (16GB recomendado)
- Python 3.11+ (para desenvolvimento local)

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/nexus-ai/local-assistant.git
cd nexus-ai

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# 3. Inicie os serviços
docker-compose up -d

# 4. Verifique os logs
docker-compose logs -f nexus-ai
```

### Configuração do Telegram
1. Busque @BotFather no Telegram
2. Crie um novo bot com /newbot
3. Copie o token para a variável TELEGRAM_BOT_TOKEN no .env

### Configuração do Discord
1. Vá para Discord Developer Portal
2. Crie uma aplicação e adicione um bot
3. Copie o token para DISCORD_BOT_TOKEN
4. Adicione intents de Message Content e Guilds

## 📖 Documentação

- [Arquitetura do Sistema](docs/ARCHITECTURE.md)
- [Guia de Habilidades](docs/SKILLS.md)
- [API Reference](docs/API.md)
- [Deploy Local com Ollama](docs/OLLAMA.md)

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     NEXUS-AI CORE                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │   AGENTE    │  │   MEMÓRIA   │  │  ORQUESTRADOR   │   │
│  │  (Brain)    │  │  (Vectors)  │  │   (Tasks)       │   │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │
│         │                │                   │             │
│  ┌──────┴────────────────┴───────────────────┴────────┐  │
│  │              SISTEMA DE HABILIDADES (Skills)         │  │
│  │  🔍 Search  📁 Files  ⏰ Schedule  💻 Code  📡 ...   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ▲                ▲                ▲
         │                │                │
┌────────┴───┐   ┌────────┴───┐   ┌────────┴───┐
│  TELEGRAM │   │  DISCORD   │   │   CLI      │
│   BOT     │   │    BOT     │   │  INTERFACE │
└───────────┘   └────────────┘   └────────────┘
```

## 🎯 Uso

### Via Terminal
```bash
python -m nexusclaw.cli
# ou
docker exec -it nexus-ai python -m nexusclaw.cli
```

### Via Telegram
```
/start - Iniciar conversa
/remember <fato> - Salvar informação
/search <termo> - Buscar na memória
/help - Ver todos os comandos
```

### Via API
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá!", "channel": "api"}'
```

## 🔧 Configuração Avançada

### Modelos de LLM
Por padrão, o sistema usa Ollama local. Configure no arquivo `config/models.yaml`:

```yaml
models:
  default: "llama3"
  fallback: "mistral"
  vision: "llava"
```

### Habilidades Personalizadas
Crie um arquivo em `skills/custom/`:

```python
from skills.base import Skill

class MyCustomSkill(Skill):
    name = "minha_habilidade"
    description = "O que minha habilidade faz"
    
    async def execute(self, **params):
        # Sua lógica aqui
        return {"result": "sucesso"}
```

## 📊 Monitoramento

Acesse o dashboard de monitoramento em: `http://localhost:8000`

- Status dos serviços
- Uso de memória e CPU
- Logs em tempo real
- Gerenciamento de conversas

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-habilidade`)
3. Commit suas mudanças (`git commit -am 'Add nova habilidade'`)
4. Push para a branch (`git push origin feature/nova-habilidade`)
5. Crie um Pull Request

## 📝 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

**NOTA**: Este projeto está em desenvolvimento ativo. Contribuições são bem-vindas!
