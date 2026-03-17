"""
NexusClaw - Interface de Linha de Comando
=========================================

Este módulo fornece uma interface interativa
para usar o NexusClaw via terminal.
"""

import asyncio
import sys
import logging
from typing import Optional

from config.settings import get_settings
from core.agent import NexusAgent
from core.memory import MemorySystem
from skills import get_skills_registry
from skills.builtins import register_all_skills


logger = logging.getLogger(__name__)


class CLIInterface:
    """Interface de linha de comando para NexusClaw"""
    
    def __init__(self):
        self.settings = get_settings()
        self.agent: Optional[NexusAgent] = None
        self.memory_system: Optional[MemorySystem] = None
        self.running = False
    
    async def initialize(self):
        """Inicializa os componentes"""
        print("Inicializando NexusClaw CLI...")
        
        # Registra habilidades
        register_all_skills()
        skills = get_skills_registry()
        print(f"Habilidades carregadas: {len(skills)}")
        
        # Inicializa memória
        self.memory_system = MemorySystem()
        await self.memory_system.initialize()
        print("Memória inicializada")
        
        # Cria agente
        self.agent = NexusAgent(
            skills_registry=skills,
            memory_system=self.memory_system
        )
        print("Agente pronto\n")
    
    async def run(self):
        """Executa o loop principal"""
        self.running = True
        
        print("=" * 50)
        print("  NexusClaw - Interface de Comando")
        print("=" * 50)
        print("Digite suas mensagens ou comandos:")
        print("  :quit ou :exit - Sair")
        print("  :clear - Limpar tela")
        print("  :help - Ver ajuda")
        print()
        
        while self.running:
            try:
                # Lê input
                user_input = input("Você: ").strip()
                
                if not user_input:
                    continue
                
                # Comandos especiais
                if user_input.lower() in [":quit", ":exit", "sair"]:
                    break
                
                if user_input.lower() == ":clear":
                    print("\033[2J\033[H")
                    continue
                
                if user_input.lower() == ":help":
                    self._print_help()
                    continue
                
                if user_input.lower() == ":skills":
                    self._print_skills()
                    continue
                
                # Processa mensagem
                print("\nPensando...", end="\r")
                
                response = await self.agent.handle_message(
                    user_id="cli_user",
                    channel="cli",
                    message=user_input
                )
                
                # Limpa "Pensando..." e mostra resposta
                print(" " * 20 + "\r")
                print(f"NexusClaw: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nEncerrando...")
                break
            except Exception as e:
                print(f"Erro: {e}\n")
        
        print("Tchau!")
    
    def _print_help(self):
        """Mostra ajuda"""
        print("""
Comandos disponíveis:
  :quit, :exit, sair - Encerrar programa
  :clear                 - Limpar tela
  :help                  - Mostrar esta ajuda
  :skills                - Listar habilidades disponíveis

Você pode:
  - Conversar normalmente com o assistente
  - Pedir para buscar informações na web
  - Pedir para executar código Python
  - Pedir para gerenciar arquivos
  - E muito mais!
""")
    
    def _print_skills(self):
        """Lista habilidades"""
        skills = get_skills_registry()
        print("\nHabilidades disponíveis:")
        for name in skills:
            print(f"  - {name}")
        print()


async def main():
    """Ponto de entrada do CLI"""
    cli = CLIInterface()
    await cli.initialize()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
