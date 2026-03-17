#!/bin/bash
# NexusClaw - Script de Inicialização Otimizado para Orange Pi

set -e

echo "========================================"
echo "  NexusClaw - Orange Pi 3B Edition"
echo "========================================"
echo ""

# Configurações de memória swap
echo "Configurando memória virtual..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
fi
swapon /swapfile 2>/dev/null || true

# Configurações de kernel para melhor performance
echo "Otimizando kernel..."
echo "never" > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
echo "never" > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true

# Limita Python garbage collection para usar menos CPU
export PYTHONGC=1

# Configurações de threading
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2

# Limita memória do Qdrant
export QDRANT__MEMORY__MAX=512m

echo "Iniciando NexusClaw..."
echo ""

# Executa o aplicativo
exec "$@"
