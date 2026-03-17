# NexusClaw - Guia Completo de Instalação e Uso

**Versão 1.0.0**
**Data: Março 2026**

---

## Sumário

1. [Introdução](#1-introdução)
2. [Requisitos do Sistema](#2-requisitos-do-sistema)
3. [Instalação](#3-instalação)
4. [Configuração](#4-configuração)
5. [Funcionalidades Principais](#5-funcionalidades-principais)
6. [Uso da API](#6-uso-da-api)
7. [Canais de Comunicação](#7-canais-de-comunicação)
8. [Sistema de Pensamento Profundo](#8-sistema-de-pensamento-profundo)
9. [Auto-Aperiçoamento](#9-auto-aperiçoamento)
10. [Evolução de Código](#10-evolução-de-código)
11. [Otimização para Orange Pi](#11-otimização-para-orange-pi)
12. [Solução de Problemas](#12-solução-de-problemas)

---

## 1. Introdução

### 1.1 O que é o NexusClaw?

O **NexusClaw** é um assistente de inteligência artificial pessoal soberano e 100% local, projetado para operar de forma completamente offline, garantindo total privacidade e controle sobre seus dados. Diferente de assistentes baseados em nuvem, o NexusClaw processa todas as informações localmente, utilizando modelos de linguagem que rodam diretamente no seu hardware.

O nome "NexusClaw" representa a natureza versátil e robusta do sistema: "Nexus" simboliza a conexão central de todas as funcionalidades, enquanto "Claw" representa a capacidade do sistema de "agarrar" e executar tarefas com precisão e eficiência.

### 1.2 Características Principais

O NexusClaw combina tecnologias avançadas de inteligência artificial com uma arquitetura modular que permite máxima flexibilidade e personalização. Suas características principais incluem processamento completamente offline, garantindo que nenhuma informação saia do seu dispositivo; suporte a múltiplos canais de comunicação, permitindo interação via Telegram, Discord, CLI e API web; um sistema de memória vetorial que mantém contexto de conversas passadas; capacidade de pensamento profundo que permite análise complexa de problemas; auto-aperiçoamento contínuo através de feedback e métricas de desempenho; e evolução de código automática que permite ao sistema melhorar suas próprias capacidades.

### 1.3 Arquitetura do Sistema

A arquitetura do NexusClaw é organizada em camadas distintas que trabalham em harmonia para proporcionar uma experiência fluida e poderosa. A camada de comunicação gerencia todos os adaptadores de entrada e saída, tratando cada canal de forma unificada. A camada de processamento abriga o agente principal, responsável por interpretar mensagens, tomar decisões e coordenar a execução de tarefas. A camada de inteligência artificial engloba os sistemas de pensamento profundo, auto-aperiçoamento e evolução de código. A camada de memória gerencia tanto o contexto de curta duração quanto o armazenamento vetorial de longa duração. Finalmente, a camada de habilidades contém ferramentas especializadas que extendem as capacidades do agente.

---

## 2. Requisitos do Sistema

### 2.1 Requisitos Mínimos para Funcionamento Básico

Para executar o NexusClaw em sua configuração mais básica, você precisará de um processador com pelo menos 2 cores, 4GB de memória RAM, 10GB de espaço em disco, e acesso à internet apenas para download inicial de dependências. Esta configuração permite executar modelos menores como TinyLlama ou Phi-3.5 Mini, oferecendo respostas rápidas mas com capacidade de raciocínio limitada.

### 2.2 Requisitos Recomendados para Performance Ótima

Para uma experiência completa com todas as funcionalidades avançadas, incluindo pensamento profundo e evolução de código, os requisitos recomendados incluem processador com 4+ cores, 8GB de memória RAM ou mais, 20GB de espaço em disco SSD, e preferencialmente uma placa de vídeo com suporte a CUDA para aceleração de inferência. Esta configuração permite executar modelos maiores como Llama 3 ou Mistral, proporcionando raciocínio mais sofisticado e respostas mais contextualizadas.

### 2.3 Requisitos para Orange Pi 3B

O NexusClaw foi especialmente otimizado para funcionar em dispositivos de baixo consumo como a Orange Pi 3B. Para esta plataforma, os requisitos são processador ARM de 4 cores, 8GB de RAM, cartão microSD de 16GB classe 10 ou superior, e acesso à internet para configuração inicial. O sistema utilizará modelos quantizados menores para manter performance aceitável dentro das limitações de hardware.

---

## 3. Instalação

### 3.1 Instalação via Docker (Recomendado)

A forma mais simples e rápida de instalar o NexusClaw é através do Docker. Primeiro, certifique-se de ter o Docker instalado em seu sistema. Em sistemas baseados em Debian/Ubuntu, você pode instalar com o comando:

```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
```

Depois,clone o repositório do NexusClaw e navegue até o diretório do projeto:

```bash
git clone https://github.com/seu-usuario/nexusclaw.git
cd nexusclaw
```

Para iniciar o sistema, simplesmente execute:

```bash
docker-compose up -d
```

O sistemairá inicializar todos os serviços necessários, incluindo o banco de dados PostgreSQL, o banco vetorial Qdrant, o servidor Ollama para modelos de linguagem, e a aplicação principal. Após a inicialização, você pode acessar a interface web em `http://localhost:8000`.

### 3.2 Instalação Manual

Para instalação manual, você precisará configurar cada componente individualmente. Comece instalando as dependências do sistema:

```bash
sudo apt update
sudo apt install python3.11 python3-pip python3-venv postgresql redis-server
```

Agora, crie um ambiente virtual e instale as dependências Python:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure o PostgreSQL criando um banco de dados:

```bash
sudo -u postgres psql
CREATE DATABASE nexusclaw;
CREATE USER nexusclaw_user WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE nexusclaw TO nexusclaw_user;
\q
```

Inicie os serviços necessários:

```bash
sudo systemctl start postgresql
sudo systemctl start redis
```

Finalmente, configure as variáveis de ambiente e inicie a aplicação:

```bash
export DATABASE_URL="postgresql://nexusclaw_user:sua_senha@localhost/nexusclaw"
export REDIS_URL="redis://localhost:6379"
python main.py
```

### 3.3 Instalação para Orange Pi 3B

A instalação para Orange Pi requer passos específicos devido à arquitetura ARM. Primeiro, prepare o sistema operacional Armbian na Orange Pi. Depois, instale as dependências ARM64:

```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo apt install python3-pip python3-venv
```

Clone o repositório e use os arquivos otimizados para ARM:

```bash
git clone https://github.com/seu-usuario/nexusclaw.git
cd nexusclaw
```

Use o docker-compose otimizado para Orange Pi:

```bash
docker-compose -f docker-compose.orange-pi.yml up -d
```

Alternativamente, para instalação sem Docker, execute o script de instalação:

```bash
chmod +x scripts/install-orange-pi.sh
./scripts/install-orange-pi.sh
```

### 3.4 Verificação da Instalação

Após a instalação, verifique se todos os serviços estão funcionando corretamente executando o script de verificação:

```bash
docker-compose ps
# ou para instalação manual:
curl http://localhost:8000/health
```

Você deve ver uma resposta indicando que o sistema está saudável e listando os adaptadores ativos.

---

## 4. Configuração

### 4.1 Arquivo de Configuração Principal

O arquivo `config/settings.py` contém todas as configurações do sistema. As variáveis de ambiente podem ser usadas para sobrescrever estos valores padrão. Crie um arquivo `.env` no diretório raiz do projeto com as seguintes configurações:

```env
# Configurações do Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Configurações do LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3.5-mini
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=2048

# Configurações do Banco de Dados
DATABASE_URL=postgresql://nexusclaw:senha@localhost:5432/nexusclaw
REDIS_URL=redis://localhost:6379

# Configurações de Memória Vetorial
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Configurações de Canais
TELEGRAM_BOT_TOKEN=seu_token_aqui
DISCORD_BOT_TOKEN=seu_token_aqui

# Configurações de Busca Web
SEARXNG_URL=http://localhost:8888

# Configurações de Execução
SANDBOX_EXECUTION_TIMEOUT=30
MAX_PARALLEL_TASKS=5
MEMORY_CONTEXT_WINDOW=10
```

### 4.2 Configuração do Ollama

O NexusClaw utiliza o Ollama para executar modelos de linguagem localmente. Após instalar o Ollama, você precisa baixar os modelos que deseja usar. Para instalar o modelo Phi-3.5 Mini, por exemplo:

```bash
ollama pull phi3.5-mini
```

Para modelos maiores como Llama 3:

```bash
ollama pull llama3
```

Para verificar os modelos disponíveis:

```bash
ollama list
```

### 4.3 Configuração de Canais de Comunicação

#### Telegram

Para ativar o bot do Telegram, você precisa criar um bot através do @BotFather no Telegram. Depois de obter o token, adicione-o às suas variáveis de ambiente:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

O bot estará disponível imediatamente após reiniciar o sistema.

#### Discord

Para ativar o bot do Discord, crie um aplicativo no Discord Developer Portal e adicione um bot. Copie o token e configure:

```env
DISCORD_BOT_TOKEN=SEU_TOKEN_AQUI
```

Depois, instale o bot no seu servidor Discord usando o OAuth2 URL gerado no portal do desenvolvedor.

#### Web Interface

A interface web está sempre ativa na porta 8000. Você pode personalizar a porta modificando a variável `PORT` ou usando um proxy reverso como Nginx.

### 4.4 Configuração de Memória Vetorial

O sistema de memória vetorial utiliza Qdrant para armazenamento de embeddings. Para configuração personalizada:

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=nexusclaw_memories
QDRANT_VECTOR_SIZE=768
```

Para persistência de dados, monte um volume docker ou configure um diretório de dados persistente.

---

## 5. Funcionalidades Principais

### 5.1 Sistema de Memória Inteligente

O NexusClaw possui um sistema de memória em duas camadas que permite manter contexto ao longo de conversas e armazenar conhecimento de longo prazo. A memória de curta duração mantém as últimas mensagens da conversa atual, permitindo respostas coerentes e contextualmente apropriadas. A memória de longa duração utiliza bancos de dados vetoriais para armazenar informações importantes que podem ser recuperadas quando relevante.

O sistema de memória vetorial permite busca semântica, significando que você pode encontrar informações não apenas por palavras-chave exatas, mas também por significado. Por exemplo, se você salvou informações sobre "a reunião com o cliente ontem", pode recuperá-las buscando por "encontros de trabalho" ou "conversas profissionais recentes".

### 5.2 Sistema de Habilidades

O NexusClaw vem com habilidades integradas que extendem suas capacidades além do processamento de texto. A habilidade de busca na web permite pesquisar informações atualizadas na internet. A habilidade de operações de arquivo permite ler, escrever e gerenciar arquivos no sistema. A habilidade de execução de código permite rodar código Python e Bash em ambiente sandbox. A habilidade de calculadora realiza cálculos matemáticos seguros.

Cada habilidade é projetada para ser usada pelo agente de forma autônoma, permitindo que o sistema execute tarefas complexas que requerem múltiplas operações.

### 5.3 Processamento de Linguagem Natural

O agente do NexusClaw utiliza modelos de linguagem avançados para compreender e gerar texto. O sistema 支持ia múltiplos provedores de LLM, permitindo que você escolha entre execução local via Ollama, ou provedores de API como OpenAI e Anthropic. A arquitetura permite fallback automático, então se um provedor falhar, o sistema tentará o próximo automaticamente.

### 5.4 Orquestrador de Tarefas

O orquestrador de tarefas permite executar operações complexas de forma autônoma. O sistema pode receber um objetivo de alto nível, como "agendar uma reunião com minha equipe amanhã às 14h", e automaticamente decompor isso em passos executáveis, coordenar a execução, e reportar o resultado.

---

## 6. Uso da API

### 6.1 Endpoints Principais

O NexusClaw expõe uma API REST completa para interação programática. Os endpoints principais incluem:

**Chat Básico:**
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Olá, como você está?",
  "user_id": "usuario_123",
  "channel": "api"
}
```

**Busca em Memórias:**
```http
GET /api/memories?query=reuniões&limit=5
```

**Gerenciamento de Tarefas:**
```http
GET /api/tasks?user_id=usuario_123
```

### 6.2 Endpoints de Pensamento Profundo

O sistema de pensamento profundo possui endpoints dedicados:

**Processar com Pensamento Profundo:**
```http
POST /api/deep-think/process
Content-Type: application/json

{
  "message": "Como devo planejar minha aposentadoria?",
  "depth": "comprehensive",
  "context": []
}
```

**Execução Autônoma:**
```http
POST /api/deep-think/autonomous
Content-Type: application/json

{
  "goal": "Organizar meus documentos financeiros",
  "context": {"user_id": "usuario_123"}
}
```

**Estado do Agente:**
```http
GET /api/deep-think/state
```

### 6.3 Endpoints de Auto-Aperiçoamento

**Relatório de Desempenho:**
```http
GET /api/improvement/report
```

**Registrar Feedback:**
```http
POST /api/improvement/feedback
Content-Type: application/json

{
  "interaction_id": "int_123",
  "feedback_type": "thumb",
  "value": "up",
  "reason": "Resposta muito útil"
}
```

### 6.4 Endpoints de Evolução de Código

**Análise de Código:**
```http
GET /api/code/analysis
```

**Sugestões de Funcionalidades:**
```http
GET /api/features/suggestions
```

**Solicitar Nova Feature:**
```http
POST /api/features/request
Content-Type: application/json

{
  "title": "Integração com Google Calendar",
  "description": "Permitir que o agente adicione eventos ao calendário",
  "priority": 3,
  "justification": "Facilitaria o gerenciamento de agenda"
}
```

---

## 7. Canais de Comunicação

### 7.1 Interface de Linha de Comando (CLI)

A CLI é a forma mais direta de interagir com o NexusClaw. Após iniciar o sistema, você pode acessar o modo interativo:

```bash
docker exec -it nexusclaw-app python main.py
# ou diretamente
python main.py
```

No modo interativo, você verá um prompt onde pode digitar suas mensagens. O CLI oferece suporte a histórico de comandos e auto-completar para conveniência.

### 7.2 Bot do Telegram

Após configurar o token do Telegram, você pode conversar com o NexusClaw diretamente pelo Telegram. O bot responde a mensagens normais e também suporta comandos especiais. O comando `/start` inicia uma nova conversa. O comando `/help` mostra todos os comandos disponíveis. O comando `/remember` salva uma informação na memória. O comando `/search` busca em suas memórias salvas.

### 7.3 Bot do Discord

O bot do Discord oferece integração similar ao Telegram. Depois de adicionar o bot ao seu servidor, você pode mencioná-lo ou enviar mensagens diretas. O bot também suporta slash commands para funcionalidades específicas.

### 7.4 Interface Web

A interface web está disponível em `http://localhost:8000` e oferece uma experiência visual completa. Você pode enviar mensagens, ver histórico de conversas, acessar configurações, e visualizar métricas do sistema. A interface também suporta WebSocket para comunicação em tempo real.

---

## 8. Sistema de Pensamento Profundo

### 8.1 Arquitetura do Pensamento Profundo

O sistema de pensamento profundo do NexusClaw representa uma das suas capacidades mais avançadas. Diferente de respondores de pergunta tradicionais, o NexusClaw pode realmente "pensar" sobre problemas complexos antes de chegar a uma resposta.

A arquitetura é composta por quatro níveis de profundidade. O nível superficial é usado para perguntas simples que não requerem análise elaborada. O nível médio aplica análise básica e considera múltiplas perspectivas. O nível profundo realiza raciocínio iterativo com múltiplas rodadas de refinamento. O nível compreensivo adiciona metacognição, onde o sistema reflete sobre seu próprio processo de pensamento.

### 8.2 Cadeia de Pensamento (Chain-of-Thought)

Quando você faz uma pergunta complexa, o sistema gera uma cadeia de pensamentos que documenta todo o processo de raciocínio. Cada pensamento é classificado por tipo: observações iniciais, análises de componentes, hipóteses geradas, raciocínios elaborados, decisões tomadas, e verificações realizadas.

Esta cadeia não apenas melhora a qualidade das respostas, mas também fornece transparência sobre como o sistema chegou a uma conclusão, permitindo que você entenda e valide o processo.

### 8.3 Auto-Reflexão

Antes de entregar uma resposta, o sistema pode automaticamente avaliar sua própria resposta em cinco dimensões: precisão, completude, clareza, relevância e tom. Se a avaliação encontrar deficiências significativas, o sistema tentará melhorar a resposta automaticamente.

Este processo de auto-reflexão é análogo ao que humanos fazem naturalmente quando revisam suas próprias comunicações antes de enviá-las.

### 8.4 Execução Autônoma

Para tarefas complexas que requerem múltiplos passos, o sistema pode criar e executar planos automaticamente. Por exemplo, se você pedir para "organizar meus arquivos de trabalho", o sistema pode criar um plano que inclui: identificar tipos de arquivos, criar estrutura de pastas, mover arquivos um a um, e verificar se tudo foi organizado corretamente.

Durante a execução, o sistema monitora o progresso, lida com erros, e ajusta o plano conforme necessário.

---

## 9. Auto-Aperiçoamento

### 9.1 Mecanismos de Feedback

O NexusClaw aprende continuamente através de múltiplos mecanismos de feedback. O feedback explícito inclui avaliações diretas como polegares para cima ou para baixo, estrelas de 1 a 5, ou comentários escritos. O feedback implícito inclui taxa de sucesso de tarefas, tempo de resposta, e padrões de reutilização de informações.

O sistema registra cada interação junto com seu feedback, permitindo análise agregada para identificar padrões de melhoria.

### 9.2 Métricas de Desempenho

O painel de métricas mostra informações detalhadas sobre o desempenho do sistema. Você pode visualizar o número total de interações, taxa de sucesso, tempo médio de resposta, uso de habilidades, e satisfação do usuário ao longo do tempo.

Estas métricas são atualizadas em tempo real e podem ser acessadas através da API ou interface web.

### 9.3 Ações de Melhoria

Baseado no feedback recebido, o sistema pode identificar e aplicar melhorias automaticamente. Estas podem incluir ajustes em prompts do sistema, modificação de parâmetros de geração, atualização de comportamentos de habilidades, ou mesmo sugestão de novas funcionalidades.

Todas as melhorias são documentadas e podem ser revertidas se não funcionarem como esperado.

---

## 10. Evolução de Código

### 10.1 Análise Automatizada de Código

O NexusClaw inclui um sistema de análise de código que pode examinar sua própria base de código para identificar problemas e oportunidades de melhoria. O analisador detecta issues como código duplicado, funções muito complexas, falta de documentação, e vulnerabilidades potenciais.

O sistema gera relatórios detalhados com métricas de complexidade e manutenibilidade, permitindo que desenvolvedores priorizem esforços de refatoração.

### 10.2 Sugestão de Funcionalidades

Através da análise de padrões de uso, o sistema pode identificar lacunas nas funcionalidades atuais e sugerir novas features. Por exemplo, se usuários frequentemente pedem para gerenciar日历, o sistema pode sugerir a adição de uma habilidade de integração com calendário.

As sugestões incluem justificativas detalhadas, estimada de esforço, e impacto potencial para ajudar na priorização.

### 10.3 Geração de Código

Para novas funcionalidades sugeridas, o sistema pode gerar templates de código que servem como ponto de partida para implementação. Estes templates seguem as convenções do projeto e incluem estrutura básica, documentação inicial, e testes placeholder.

---

## 11. Otimização para Orange Pi

### 11.1 Desafios e Soluções

Dispositivos como a Orange Pi 3B apresentam desafios únicos devido à limitação de recursos. O NexusClaw aborda isto através de várias otimizações. Modelos menores e quantizados como Phi-3.5 Mini ou TinyLlama são usados para reduzir uso de memória. A execução sequencial substitui processamento paralelo para economizar energia. Componentes opcionais podem ser desabilitados para reduzir carga. Compressão de contexto mantém apenas informações essenciais.

### 11.2 Modelos Recomendados

Para Orange Pi 3B com 8GB de RAM, os modelos recomendados incluem Phi-3.5 Mini (2.2B parâmetros, ~2GB RAM) para equilíbrio entre qualidade e velocidade, TinyLlama (1.1B parâmetros, ~1GB RAM) para máxima velocidade, e Qwen2-0.5B (0.5B parâmetros, ~500MB RAM) para dispositivos muito limitados.

### 11.3 Scripts de Instalação

O script de instalação otimizado para Orange Pi automatiza todo o processo:

```bash
chmod +x scripts/install-orange-pi.sh
./scripts/install-orange-pi.sh
```

O script instala dependências ARM64, baixa modelos otimizados, configura memória swap se necessário, e otimiza configurações do sistema operacional.

---

## 12. Solução de Problemas

### 12.1 Problemas Comuns e Soluções

**Sistema não inicia:**
Verifique se todas as portas necessárias estão disponíveis com `netstat -tulpn | grep -E '8000|5432|6379|6333'`. Confirme que o Docker tem recursos suficientes com `docker stats`. Verifique logs com `docker-compose logs -f`.

**Memória insuficiente:**
Reduza o tamanho do modelo no arquivo de configuração. Aumente a memória swap com `sudo fallocate -l 2G /swapfile`. Considere usar versões quantizadas de modelos.

**Respostas lentas:**
Verifique se há outros processos consumindo recursos com `htop`. Mude para um modelo menor. Ative aceleração GPU se disponível. Reduza o tamanho do contexto máximo.

**Erro de conexão com banco de dados:**
Verifique se o PostgreSQL está rodando com `sudo systemctl status postgresql`. Confirme as credenciais no arquivo `.env`. Tente reconectar o banco.

### 12.2 Logs e Debugging

Os logs do sistema estão disponíveis em `/app/data/nexus-ai.log` dentro do container Docker, ou podem ser acessados via:

```bash
docker-compose logs -f app
```

Para debugging detalhado, ative o modo debug no arquivo de configuração:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### 12.3 Reinicialização e Manutenção

Para reiniciar o sistema:

```bash
docker-compose restart
# ou
sudo systemctl restart nexusclaw
```

Para fazer backup da memória e configurações:

```bash
docker-compose exec postgres pg_dump -U nexusclaw > backup_$(date +%Y%m%d).sql
docker-compose exec qdrant sh -c "curl localhost:6333/collections > collections_backup.json"
```

---

## Conclusão

O NexusClaw representa uma nova geração de assistentes de IA que priorizam privacidade, soberania de dados e Capabilities avançadas. Com sua arquitetura modular, suporte a múltiplos canais de comunicação, e sistemas de aprendizado contínuo, o NexusClaw oferece uma experiência poderosa enquanto mantém todas as informações sob seu controle.

Para mais informações, documentação adicional, e suporte da comunidade, visite o repositório oficial do projeto. Contributions são bem-vindas!

---

**NexusClaw - Seu Assistente de IA Pessoal Soberano**

*Versão 1.0.0 - Março 2026*
