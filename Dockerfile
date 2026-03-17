FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Labels
LABEL maintainer="Nexus-AI Team"
LABEL description="Seu Assistente de IA Pessoal Soberano"

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia dependências primeiro (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código fonte
COPY . .

# Cria diretórios necessários
RUN mkdir -p /app/data /app/skills /app/config

# Porta
EXPOSE 8000

# Comando inicial
CMD ["python", "main.py"]
