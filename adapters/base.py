"""
NexusClaw - Adaptadores de Canal
===============================

Este módulo implementa adaptadores para diferentes
canais de comunicação (Telegram, Discord, CLI, etc).
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Callable, Awaitable

from config.settings import get_settings


logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Classe base para adaptadores de canal"""
    
    def __init__(self, agent: Any):
        self.settings = get_settings()
        self.agent = agent
        self._running = False
    
    @abstractmethod
    async def start(self):
        """Inicia o adaptador"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Para o adaptador"""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        user_id: str,
        message: str,
        **kwargs
    ):
        """Envia uma mensagem"""
        pass
    
    async def handle_message(
        self,
        user_id: str,
        channel: str,
        message: str
    ) -> str:
        """Processa uma mensagem recebida"""
        from core.agent import Message, ConversationContext
        
        # Obtém ou cria contexto
        context = self.agent.get_or_create_context(user_id, channel)
        
        # Cria mensagem do usuário
        user_message = Message(
            id=f"msg_{asyncio.get_event_loop().time()}",
            role="user",
            content=message,
            channel=channel,
            user_id=user_id
        )
        
        # Processa através do agente
        response = await self.agent.process_message(user_message, context)
        
        # Salva na memória
        if self.agent.memory_system:
            await self.agent.memory_system.save_conversation_turn(
                user_id=user_id,
                channel=channel,
                user_message=message,
                assistant_message=response
            )
        
        return response


class TelegramAdapter(BaseAdapter):
    """Adaptador para Telegram"""
    
    async def start(self):
        """Inicia o bot do Telegram"""
        if not self.settings.telegram_bot_token:
            logger.warning("Token do Telegram não configurado")
            return
        
        # Inicializa cliente (aiogram)
        from aiogram import Bot, Dispatcher
        from aiogram.filters import Command
        from aiogram.types import Message as TgMessage
        
        self.bot = Bot(token=self.settings.telegram_bot_token)
        self.dp = Dispatcher()
        
        # Registra handlers
        self.dp.message.register(self._handle_start, Command("start"))
        self.dp.message.register(self._handle_help, Command("help"))
        self.dp.message.register(self._handle_memory, Command("remember"))
        self.dp.message.register(self._handle_search, Command("search"))
        self.dp.message.register(self._handle_message)
        
        # Inicia polling
        self.dp.run_polling(self.bot)
        self._running = True
        
        logger.info("Adaptador Telegram iniciado")
    
    async def stop(self):
        """Para o bot do Telegram"""
        if hasattr(self, 'bot'):
            await self.bot.session.close()
        self._running = False
        logger.info("Adaptador Telegram parado")
    
    async def send_message(
        self,
        user_id: str,
        message: str,
        **kwargs
    ):
        """Envia mensagem via Telegram"""
        from aiogram import Bot
        
        bot = Bot(token=self.settings.telegram_bot_token)
        await bot.send_message(chat_id=int(user_id), text=message)
        await bot.session.close()
    
    async def _handle_start(self, event: TgMessage):
        """Handler para comando /start"""
        await event.answer(
            "Olá! Eu sou o NexusClaw, seu assistente de IA pessoal.\n\n"
            "Posso ajudá-lo com:\n"
            "- Conversas inteligentes\n"
            "- Buscar informações\n"
            "- Gerenciar arquivos\n"
            "- Executar tarefas\n\n"
            "Apenas me envie uma mensagem!"
        )
    
    async def _handle_help(self, event: TgMessage):
        """Handler para comando /help"""
        await event.answer(
            "Comandos disponíveis:\n"
            "/start - Iniciar conversa\n"
            "/help - Ver esta ajuda\n"
            "/remember <info> - Salvar uma informação\n"
            "/search <termo> - Buscar na memória\n"
            "/clear - Limpar conversa atual"
        )
    
    async def _handle_memory(self, event: TgMessage):
        """Handler para comando /remember"""
        if not self.agent.memory_system:
            await event.answer("Sistema de memória não disponível")
            return
        
        # Extrai o fato após o comando
        fact = event.text.replace("/remember", "").strip()
        
        if not fact:
            await event.answer("Uso: /remember <informação>")
            return
        
        await self.agent.memory_system.add_fact(
            fact=fact,
            user_id=str(event.from_user.id)
        )
        
        await event.answer(f"Salvo: {fact}")
    
    async def _handle_search(self, event: TgMessage):
        """Handler para comando /search"""
        if not self.agent.memory_system:
            await event.answer("Sistema de memória não disponível")
            return
        
        query = event.text.replace("/search", "").strip()
        
        if not query:
            await event.answer("Uso: /search <termo>")
            return
        
        results = await self.agent.memory_system.search_memories(query)
        
        if results:
            response = "Resultados encontrados:\n\n"
            for r in results[:5]:
                response += f"- {r['content']}\n"
            await event.answer(response)
        else:
            await event.answer("Nenhum resultado encontrado")
    
    async def _handle_message(self, event: TgMessage):
        """Handler para mensagens normais"""
        user_id = str(event.from_user.id)
        message = event.text
        
        response = await self.handle_message(user_id, "telegram", message)
        await event.answer(response)


class DiscordAdapter(BaseAdapter):
    """Adaptador para Discord"""
    
    async def start(self):
        """Inicia o bot do Discord"""
        if not self.settings.discord_bot_token:
            logger.warning("Token do Discord não configurado")
            return
        
        import discord
        from discord import app_commands
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)
        
        @self.client.event
        async def on_ready():
            logger.log(f"Bot Discord conectado como {self.client.user}")
            await self.tree.sync()
        
        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            
            # Ignora mensagens de outros bots
            if message.author.bot:
                return
            
            user_id = str(message.author.id)
            response = await self.handle_message(
                user_id, 
                "discord", 
                message.content
            )
            await message.reply(response)
        
        await self.client.start(self.settings.discord_bot_token)
        self._running = True
    
    async def stop(self):
        """Para o bot do Discord"""
        if hasattr(self, 'client'):
            await self.client.close()
        self._running = False
    
    async def send_message(
        self,
        user_id: str,
        message: str,
        channel_id: str = None,
        **kwargs
    ):
        """Envia mensagem via Discord"""
        import discord
        
        if not hasattr(self, 'client'):
            return
        
        # Envia no canal especificado ou via DM
        if channel_id:
            channel = self.client.get_channel(int(channel_id))
            if channel:
                await channel.send(message)
        else:
            # Tenta enviar DM
            user = self.client.get_user(int(user_id))
            if user:
                await user.send(message)


class CLIAdapter(BaseAdapter):
    """Adaptador para Interface de Linha de Comando"""
    
    def __init__(self, agent: Any):
        super().__init__(agent)
        self.input_queue = asyncio.Queue()
    
    async def start(self):
        """Inicia a interface CLI"""
        self._running = True
        
        # Inicia tarefa de leitura de input
        asyncio.create_task(self._read_input())
        
        logger.info("Adaptador CLI iniciado")
    
    async def stop(self):
        """Para a interface CLI"""
        self._running = False
    
    async def _read_input(self):
        """Lê input do usuário continuamente"""
        loop = asyncio.get_event_loop()
        
        while self._running:
            try:
                # Lê linha do terminal
                line = await loop.run_in_executor(None, input, "Você: ")
                
                if line.strip():
                    await self.input_queue.put(line)
                    
            except Exception as e:
                logger.error(f"Erro ao ler input: {e}")
                break
    
    async def run_interactive(self):
        """Executa modo interativo"""
        print("=" * 50)
        print("  NexusClaw - Interface de Linha de Comando")
        print("=" * 50)
        print("Digite suas mensagens (ou 'sair' para terminar)")
        print()
        
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self.input_queue.get(),
                    timeout=1.0
                )
                
                if message.lower() in ["sair", "exit", "quit"]:
                    break
                
                print("\nProcessando...")
                response = await self.handle_message(
                    user_id="cli_user",
                    channel="cli",
                    message=message
                )
                
                print(f"\nNexusClaw: {response}\n")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erro: {e}")
        
        print("\nEncerrando...")
    
    async def send_message(
        self,
        user_id: str,
        message: str,
        **kwargs
    ):
        """Envia mensagem para stdout (CLI)"""
        print(f"NexusClaw: {message}")


class WebAdapter(BaseAdapter):
    """Adaptador para API Web (REST/WebSocket)"""
    
    def __init__(self, agent: Any, app: Any = None):
        super().__init__(agent)
        self.app = app
        self.websocket_connections: Dict[str, Any] = {}
    
    async def start(self):
        """Inicia o servidor web"""
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        import uvicorn
        
        if self.app is None:
            self.app = FastAPI(title="NexusClaw API")
        
        @self.app.get("/")
        async def root():
            return {"message": "NexusClaw API", "status": "running"}
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        @self.app.post("/api/chat")
        async def chat(request: Dict):
            """Endpoint para chatting"""
            message = request.get("message", "")
            user_id = request.get("user_id", "api_user")
            channel = request.get("channel", "api")
            
            response = await self.handle_message(user_id, channel, message)
            
            return {
                "response": response,
                "user_id": user_id,
                "channel": channel
            }
        
        @self.app.websocket("/ws/{user_id}")
        async def websocket_endpoint(websocket: WebSocket, user_id: str):
            """Endpoint WebSocket para chat em tempo real"""
            await websocket.accept()
            self.websocket_connections[user_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_text()
                    data_json = json.loads(data)
                    
                    message = data_json.get("message", "")
                    response = await self.handle_message(
                        user_id, "websocket", message
                    )
                    
                    await websocket.send_json({
                        "response": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                if user_id in self.websocket_connections:
                    del self.websocket_connections[user_id]
        
        # Servidor em background
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        
        asyncio.create_task(self.server.serve())
        self._running = True
        
        logger.info("Adaptador Web iniciado na porta 8000")
    
    async def stop(self):
        """Para o servidor web"""
        if hasattr(self, 'server'):
            self.server.should_exit = True
        self._running = False
    
    async def send_message(
        self,
        user_id: str,
        message: str,
        **kwargs
    ):
        """Envia mensagem via WebSocket"""
        if user_id in self.websocket_connections:
            await self.websocket_connections[user_id].send_json({
                "message": message,
                "timestamp": datetime.now().isoformat()
            })


# Registro de adaptadores
ADAPTERS = {
    "telegram": TelegramAdapter,
    "discord": DiscordAdapter,
    "cli": CLIAdapter,
    "web": WebAdapter
}
