"""
NexusClaw - Orquestrador de Tarefas
===================================

Este módulo gerencia a execução autônoma de tarefas
e o调度 de operações do assistente.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from config.settings import get_settings


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status de uma tarefa"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Prioridade de tarefas"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """Representa uma tarefa a ser executada"""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    result: Any = None
    error: Optional[str] = None
    user_id: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """Fila de tarefas com suporte a prioridades"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running_tasks: Dict[str, Task] = {}
    
    async def add_task(
        self,
        task: Task
    ) -> str:
        """Adiciona uma tarefa à fila"""
        self.tasks[task.id] = task
        
        # Adiciona à fila de prioridade (menor número = maior prioridade)
        priority = -task.priority.value  # Negativo para inverter ordem
        await self.pending_queue.put((priority, task.id))
        
        logger.info(f"Tarefa adicionada: {task.name} (ID: {task.id})")
        return task.id
    
    async def get_next_task(self) -> Optional[Task]:
        """Obtém próxima tarefa da fila"""
        try:
            priority, task_id = await asyncio.wait_for(
                self.pending_queue.get(),
                timeout=1.0
            )
            
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                return task
            
            return None
            
        except asyncio.TimeoutError:
            return None
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: Optional[str] = None
    ):
        """Atualiza status de uma tarefa"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = status
        
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
            self._running_tasks[task_id] = task
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.result = result
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
        elif status == TaskStatus.FAILED:
            task.completed_at = datetime.now()
            task.error = error
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Obtém uma tarefa pelo ID"""
        return self.tasks.get(task_id)
    
    def get_user_tasks(self, user_id: str) -> List[Task]:
        """Obtém todas as tarefas de um usuário"""
        return [
            task for task in self.tasks.values()
            if task.user_id == user_id
        ]


class TaskOrchestrator:
    """
    Orquestrador de tarefas autonomous.
    Gerencia execução de tarefas complexas em múltiplos passos.
    """
    
    def __init__(self, agent: Any, max_parallel: int = 5):
        self.settings = get_settings()
        self.agent = agent
        self.task_queue = TaskQueue()
        self.max_parallel = max_parallel
        self._workers: List[asyncio.Task] = []
        self._running = False
    
    async def start(self):
        """Inicia o orquestrador"""
        self._running = True
        
        # Inicia workers
        for i in range(self.max_parallel):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        
        logger.info(f"Orquestrador iniciado com {self.max_parallel} workers")
    
    async def stop(self):
        """Para o orquestrador"""
        self._running = False
        
        # Cancela workers
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        logger.info("Orquestrador parado")
    
    async def _worker(self, worker_id: int):
        """Worker que processa tarefas da fila"""
        logger.info(f"Worker {worker_id} iniciado")
        
        while self._running:
            task = await self.task_queue.get_next_task()
            
            if task:
                await self._execute_task(task)
            else:
                await asyncio.sleep(0.5)
        
        logger.info(f"Worker {worker_id} parado")
    
    async def _execute_task(self, task: Task):
        """Executa uma tarefa"""
        logger.info(f"Executando tarefa: {task.name}")
        
        await self.task_queue.update_task_status(
            task.id,
            TaskStatus.RUNNING
        )
        
        try:
            # Executa cada passo da tarefa
            for step in task.steps:
                task.current_step += 1
                
                step_type = step.get("type")
                step_params = step.get("params", {})
                
                if step_type == "tool":
                    result = await self._execute_tool(
                        step_params.get("tool"),
                        step_params.get("arguments", {})
                    )
                    step["result"] = result
                    
                elif step_type == "message":
                    # Envia mensagem ao usuário
                    await self._send_message(
                        step_params.get("content"),
                        task.user_id,
                        step_params.get("channel", "default")
                    )
                
                elif step_type == "wait":
                    wait_time = step_params.get("seconds", 1)
                    await asyncio.sleep(wait_time)
                
                # Verifica se tarefa foi cancelada
                current_task = self.task_queue.get_task(task.id)
                if current_task and current_task.status == TaskStatus.CANCELLED:
                    return
            
            # Tarefa concluída
            await self.task_queue.update_task_status(
                task.id,
                TaskStatus.COMPLETED,
                result={"steps_completed": task.current_step}
            )
            
        except Exception as e:
            logger.error(f"Erro ao executar tarefa {task.id}: {e}")
            await self.task_queue.update_task_status(
                task.id,
                TaskStatus.FAILED,
                error=str(e)
            )
    
    async def _execute_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Executa uma ferramenta"""
        if hasattr(self.agent.skills_registry, tool_name):
            skill_func = getattr(self.agent.skills_registry, tool_name)
            
            if asyncio.iscoroutinefunction(skill_func):
                return await skill_func(**arguments)
            else:
                return skill_func(**arguments)
        
        raise ValueError(f"Tool não encontrada: {tool_name}")
    
    async def _send_message(
        self,
        content: str,
        user_id: str,
        channel: str
    ):
        """Envia mensagem ao usuário (placeholder)"""
        logger.info(f"Mensagem para {user_id} via {channel}: {content}")
    
    async def create_autonomous_task(
        self,
        goal: str,
        user_id: str,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Cria uma tarefa autonomous a partir de um objetivo.
        O agente planeja os passos necessários.
        """
        from core.agent import LLMWrapper
        
        llm = LLMWrapper()
        
        # Prompt para planejar tarefa
        planning_prompt = f"""
O usuário quer que você execute o seguinte objetivo:
"{goal}"

Planeje os passos necessários para completar esta tarefa.
Retorne apenas um JSON array com os passos.

Cada passo deve ter:
- type: "tool", "message", ou "wait"
- params: parâmetros do passo

Ferramentas disponíveis:
{json.dumps(list(self.agent.skills_registry.keys()), indent=2)}

Exemplo de formato:
[
  {{"type": "tool", "params": {{"tool": "web_search", "arguments": {{"query": "..."}}}}}},
  {{"type": "message", "params": {{"content": "Encontrei informações..."}}}},
  {{"type": "tool", "params": {{"tool": "file_operations", "arguments": {{"action": "write", ...}}}}}}
]
"""
        
        try:
            response = await llm.generate(
                prompt=planning_prompt,
                temperature=0.5,
                max_tokens=1000
            )
            
            steps_text = response.get("content", "[]")
            
            # Limpa markdown se presente
            if "```json" in steps_text:
                steps_text = steps_text.split("```json")[1].split("```")[0]
            elif "```" in steps_text:
                steps_text = steps_text.split("```")[1].split("```")[0]
            
            steps = json.loads(steps_text)
            
            # Cria tarefa
            task = Task(
                id=f"task_{datetime.now().timestamp()}",
                name=goal[:50],
                description=goal,
                priority=priority,
                steps=steps,
                user_id=user_id
            )
            
            task_id = await self.task_queue.add_task(task)
            logger.info(f"Tarefa autonomous criada: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Erro ao criar tarefa autonomous: {e}")
            raise
    
    async def schedule_task(
        self,
        task: Task,
        scheduled_at: datetime
    ):
        """Agenda uma tarefa para executar no futuro"""
        task.scheduled_at = scheduled_at
        
        # Implementação simplificada - em produção usaria um scheduler
        delay = (scheduled_at - datetime.now()).total_seconds()
        
        if delay > 0:
            await asyncio.sleep(delay)
        
        await self.task_queue.add_task(task)
