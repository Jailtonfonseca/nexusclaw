"""
NexusClaw - Agente Principal (Brain)
===================================

Este módulo implementa o cérebro do assistente,
responsável por processar mensagens, tomar decisões
e coordenar habilidades.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

import httpx
from config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Representa uma mensagem no sistema"""
    id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    channel: str = "unknown"
    user_id: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Contexto de uma conversa"""
    user_id: str
    channel: str
    messages: List[Message] = field(default_factory=list)
    system_prompt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMWrapper:
    """Wrapper para interagir com modelos de linguagem"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def generate(
        self,
        prompt: str,
        messages: List[Dict[str, str]] = None,
        temperature: float = None,
        max_tokens: int = None,
        tools: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Gera uma resposta usando o LLM configurado.
        Tenta Ollama primeiro, depois OpenAI, depois Anthropic.
        """
        temperature = temperature or self.settings.ollama_temperature
        max_tokens = max_tokens or self.settings.ollama_max_tokens
        
        # Tenta Ollama primeiro (local)
        try:
            return await self._generate_ollama(
                prompt, messages, temperature, max_tokens, tools
            )
        except Exception as e:
            logger.warning(f"Ollama falhou: {e}")
        
        # Tenta OpenAI como fallback
        if self.settings.openai_api_key:
            try:
                return await self._generate_openai(
                    prompt, messages, temperature, max_tokens, tools
                )
            except Exception as e:
                logger.warning(f"OpenAI falhou: {e}")
        
        # Tenta Anthropic como último recurso
        if self.settings.anthropic_api_key:
            try:
                return await self._generate_anthropic(
                    prompt, messages, temperature, max_tokens, tools
                )
            except Exception as e:
                logger.warning(f"Anthropic falhou: {e}")
        
        raise Exception("Todos os provedores de LLM falharam")
    
    async def _generate_ollama(
        self,
        prompt: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        tools: List[Dict]
    ) -> Dict[str, Any]:
        """Gera resposta usando Ollama local"""
        url = f"{self.settings.ollama_base_url}/api/chat"
        
        # Constrói mensagens no formato Ollama
        ollama_messages = []
        
        if messages:
            ollama_messages.extend(messages)
        
        if prompt:
            ollama_messages.append({
                "role": "user",
                "content": prompt
            })
        
        payload = {
            "model": self.settings.ollama_model,
            "messages": ollama_messages,
            "temperature": temperature,
            "options": {
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        if tools:
            payload["tools"] = tools
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "content": data.get("message", {}).get("content", ""),
            "tool_calls": data.get("message", {}).get("tool_calls", []),
            "model": data.get("model", self.settings.ollama_model),
            "done": True
        }
    
    async def _generate_openai(
        self,
        prompt: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        tools: List[Dict]
    ) -> Dict[str, Any]:
        """Gera resposta usando OpenAI"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url
        )
        
        openai_messages = messages or []
        if prompt:
            openai_messages.append({
                "role": "user",
                "content": prompt
            })
        
        params = {
            "model": self.settings.openai_model,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            params["tools"] = tools
        
        response = await client.chat.completions.create(**params)
        
        return {
            "content": response.choices[0].message.content or "",
            "tool_calls": [
                {"function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in response.choices[0].message.tool_calls or []
            ],
            "model": response.model
        }
    
    async def _generate_anthropic(
        self,
        prompt: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        tools: List[Dict]
    ) -> Dict[str, Any]:
        """Gera resposta usando Anthropic"""
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        
        anthropic_messages = messages or []
        if prompt:
            anthropic_messages.append({
                "role": "user",
                "content": prompt
            })
        
        params = {
            "model": "claude-3-opus-20240229",
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = await client.messages.create(**params)
        
        return {
            "content": response.content[0].text if response.content else "",
            "tool_calls": [],
            "model": response.model
        }


class NexusAgent:
    """
    Agente principal do NexusClaw.
    Responsável por processar mensagens e coordenar habilidades.
    """
    
    def __init__(
        self,
        skills_registry: Dict[str, Callable],
        memory_system: Any = None
    ):
        self.settings = get_settings()
        self.llm = LLMWrapper()
        self.skills_registry = skills_registry
        self.memory_system = memory_system
        self.conversations: Dict[str, ConversationContext] = {}
        
        # Prompts do sistema
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema base"""
        return """Você é o NexusClaw, um assistente de IA pessoal soberano e 100% local.

Sua missão é ajudar o usuário em qualquer tarefa que ele precisar, usando suas habilidades disponíveis.

Suas características:
- Você tem acesso a ferramentas para buscar informações, gerenciar arquivos, executar código, e muito mais.
- Você lembra de conversas passadas e pode buscar informações na sua memória.
- Você pode executar tarefas autonomous quando necessário.
- Você prioriza a privacidade e soberania de dados do usuário.

Quando precisar usar uma ferramenta, use o formato de tool_call.
Quando não souber algo, seja honesto e peça esclarecimentos.
Sempre seja útil, claro e conciso.

Habilidades disponíveis:
{skills_description}

Comece a conversa"""
    
    async def process_message(
        self,
        message: Message,
        context: ConversationContext
    ) -> str:
        """
        Processa uma mensagem e retorna a resposta.
        
        Args:
            message: A mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            A resposta gerada
        """
        try:
            # Adiciona mensagem ao contexto
            context.messages.append(message)
            
            # Limita tamanho do contexto
            if len(context.messages) > self.settings.memory_context_window:
                context.messages = context.messages[-self.settings.memory_context_window:]
            
            # Converte mensagens para formato LLM
            llm_messages = self._build_llm_messages(context)
            
            # Prepara tool definitions
            tools = self._build_tools_definitions()
            
            # Gera resposta
            response = await self.llm.generate(
                prompt="",
                messages=llm_messages,
                tools=tools if tools else None
            )
            
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            
            # Processa tool calls se houver
            if tool_calls:
                content = await self._process_tool_calls(
                    tool_calls, llm_messages, content
                )
            
            # Adiciona resposta ao contexto
            assistant_message = Message(
                id=f"assistant_{datetime.now().timestamp()}",
                role="assistant",
                content=content,
                channel=message.channel,
                user_id=message.user_id
            )
            context.messages.append(assistant_message)
            
            return content
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
            return f"Desculpe, encontrei um erro ao processar sua mensagem: {str(e)}"
    
    def _build_llm_messages(self, context: ConversationContext) -> List[Dict[str, str]]:
        """Constrói lista de mensagens no formato do LLM"""
        messages = []
        
        # Adiciona system prompt
        skills_desc = "\n".join([
            f"- {name}: {skill.__doc__ or 'Descrição não disponível'}"
            for name, skill in self.skills_registry.items()
        ])
        
        system_msg = self.system_prompt.format(skills_description=skills_desc)
        messages.append({
            "role": "system",
            "content": system_msg
        })
        
        # Adiciona mensagens do histórico
        for msg in context.messages[-10:]:  # Últimas 10 mensagens
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    def _build_tools_definitions(self) -> List[Dict]:
        """Constrói definições de ferramentas para o LLM"""
        tools = []
        
        for name, skill_func in self.skills_registry.items():
            # Obtém informações da skill do docstring
            doc = skill_func.__doc__ or "Função disponível"
            
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": doc,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "object",
                                "description": "Parâmetros para a função"
                            }
                        },
                        "required": ["params"]
                    }
                }
            })
        
        return tools
    
    async def _process_tool_calls(
        self,
        tool_calls: List[Dict],
        llm_messages: List[Dict],
        current_content: str
    ) -> str:
        """Processa chamadas de ferramentas"""
        results = []
        
        for tool_call in tool_calls:
            try:
                func_name = tool_call.get("function", {}).get("name")
                func_args = tool_call.get("function", {}).get("arguments", "{}")
                
                if isinstance(func_args, str):
                    func_args = json.loads(func_args)
                
                params = func_args.get("params", func_args)
                
                # Executa a skill
                if func_name in self.skills_registry:
                    skill_func = self.skills_registry[func_name]
                    
                    if asyncio.iscoroutinefunction(skill_func):
                        result = await skill_func(**params)
                    else:
                        result = skill_func(**params)
                    
                    results.append({
                        "tool": func_name,
                        "result": result
                    })
                    
                    # Adiciona resultado às mensagens
                    llm_messages.append({
                        "role": "tool",
                        "content": json.dumps(result),
                        "name": func_name
                    })
                    
            except Exception as e:
                logger.error(f"Erro ao executar skill {func_name}: {e}")
                results.append({
                    "tool": func_name,
                    "error": str(e)
                })
        
        # Gera resposta final com resultados das tools
        if results:
            final_response = await self.llm.generate(
                prompt="Com base nos resultados das ferramentas executadas, forneça uma resposta completa ao usuário.",
                messages=llm_messages
            )
            return final_response.get("content", current_content)
        
        return current_content
    
    async def handle_message(
        self,
        user_id: str,
        channel: str,
        message: str
    ) -> str:
        """
        Método de conveniência para processar mensagens.
        
        Args:
            user_id: ID do usuário
            channel: Canal de comunicação
            message: Conteúdo da mensagem
            
        Returns:
            Resposta gerada
        """
        # Obtém ou cria contexto
        context = self.get_or_create_context(user_id, channel)
        
        # Cria objeto de mensagem
        msg = Message(
            id=f"user_{datetime.now().timestamp()}",
            role="user",
            content=message,
            channel=channel,
            user_id=user_id
        )
        
        # Processa a mensagem
        return await self.process_message(msg, context)
    
    def get_or_create_context(
        self,
        user_id: str,
        channel: str
    ) -> ConversationContext:
        """Obtém ou cria contexto de conversa"""
        key = f"{user_id}:{channel}"
        
        if key not in self.conversations:
            self.conversations[key] = ConversationContext(
                user_id=user_id,
                channel=channel,
                system_prompt=self.system_prompt
            )
        
        return self.conversations[key]
