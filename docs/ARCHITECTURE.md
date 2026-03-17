# Arquitetura do NexusClaw

## Visão Geral

O NexusClaw é um assistente de IA pessoal soberano, 100% local, construído com arquitetura modular e escalável. O sistema é composto por vários componentes que trabalham em conjunto para fornecer uma experiência de assistente de IA completo.

## Componentes Principais

### 1. Core (Núcleo)

#### Agente (`core/agent.py`)
O cérebro do sistema, responsável por:
- Processar mensagens e gerar respostas
- Coordenar o uso de habilidades
- Gerenciar contexto de conversas
- Integrar com modelos de linguagem

#### Memória (`core/memory.py`)
Sistema de memória hierárquico:
- **Memória de Curto Prazo**: Contexto da conversa atual
- **Memória Episódica**: Histórico de conversas passadas (armazenado em vetores)
- **Memória de Fatos**: Entidades e preferências do usuário

#### Orquestrador (`core/orchestrator.py`)
Gerencia tarefas autonomous:
- Fila de tarefas com prioridades
- Execução paralela de operações
- Agendamento de tarefas futuras

### 2. Adaptadores de Canal

O NexusClaw suporta múltiplos canais de comunicação através de adaptadores:

- **TelegramAdapter**: Bot do Telegram com comandos
- **DiscordAdapter**: Bot do Discord
- **CLIAdapter**: Interface de terminal
- **WebAdapter**: API REST e WebSocket

Cada adaptor implementa a interface `BaseAdapter` e converte mensagens do formato específico para o formato interno do sistema.

### 3. Sistema de Habilidades

Habilidades são plugins modulares que extendem as capacidades do agente:

- **WebSearchSkill**: Busca na web via SearXNG
- **FileOperationsSkill**: Ler/escrever arquivos locais
- **CodeExecutionSkill**: Executar código Python/Bash
- **CalculatorSkill**: Cálculos matemáticos

## Fluxo de Dados

```
Usuário → Adaptador → Agente → Habilidades → Resposta
                ↓
           Memória
                ↓
           Orquestrador (se necessário)
```

## Stack Tecnológica

### Backend
- **Python 3.11+**: Linguagem principal
- **FastAPI**: Framework web assíncrono
- **SQLAlchemy**: ORM para banco de dados
- **Redis**: Cache e filas

### IA/ML
- **Ollama**: Inferência de LLM local
- **Qdrant**: Banco de vetores para memória semântica
- **Sentence-Transformers**: Geração de embeddings

### Infraestrutura
- **Docker**: Containerização
- **PostgreSQL**: Banco de dados relacional

## Padrões de Projeto

### Adapter Pattern
Cada canal de comunicação é um adapter separado, permitindo fácil adição de novos canais.

### Plugin System
Habilidades são carregadas dinamicamente, permitindo extensão sem modificar o código core.

### Repository Pattern
Acesso a dados através de repositórios abstratos, permitindo trocar implementações (ex: PostgreSQL por MySQL).

## Segurança

- Execução de código em sandbox
- Validação de parâmetros
- Isolamento de dados por usuário
- Rate limiting configurável

## Escalabilidade

O sistema pode escalar em múltiplas dimensões:

1. **Horizontal**: Múltiplas instâncias atrás de um load balancer
2. **Vertical**: Mais recursos (CPU/RAM) para 处理 de tarefas pesadas
3. **Distribuído**: Componentes podem estar em máquinas separadas

## Desenvolvimento Futuro

- Suporte a mais canais (Slack, Teams, etc.)
- Mais habilidadesbuilt-in
- Interface web administrativa
- Dashboard de analytics
