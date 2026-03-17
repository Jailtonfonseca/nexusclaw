"""
NexusClaw - Sistema de Auto-Aperfeiçoamento
==========================================

Este módulo implementa um sistema de evolução contínua
que permite ao assistente aprender e melhorar automaticamente
ao longo do tempo através de múltiplos mecanismos de feedback.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from config.settings import get_settings


logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Tipos de feedback do sistema"""
    EXPLICIT_THUMB = "thumb"           # 👍/👎
    EXPLICIT_RATING = "rating"        # 1-5 estrelas
    EXPLICIT_TEXT = "text"            # Feedback descritivo transcrito
    IMPLICIT_SUCCESS = "success"       # Ação completada com sucesso
    IMPLICIT_FAILURE = "failure"       # Ação falhou
    CONTEXT_REUSE = "context_reuse"    # Usuário buscou contexto similar
    ABANDONMENT = "abandonment"        # Conversa abandonada
    REPETITION = "repetition"          # Usuário repetiu pergunta


@dataclass
class InteractionRecord:
    """Registro de uma interação para análise"""
    id: str
    timestamp: datetime
    user_id: str
    channel: str
    prompt: str
    response: str
    context: List[Dict[str, str]]
    feedback: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    skills_used: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    tokens_used: int = 0


@dataclass
class PerformanceMetrics:
    """Métricas de desempenho do assistente"""
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    average_response_time: float = 0.0
    average_tokens: float = 0.0
    skill_usage_count: Dict[str, int] = field(default_factory=dict)
    skill_success_rate: Dict[str, float] = field(default_factory=dict)
    prompt_patterns: Dict[str, int] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)
    user_satisfaction_score: float = 0.0


@dataclass
class ImprovementAction:
    """Ação de melhoria identificada"""
    id: str
    type: str  # "prompt_tweak", "skill_update", "new_skill", "parameter_adjust"
    priority: int  # 1-5, 5 sendo mais importante
    description: str
    target: str  # O que será alterado
    suggested_change: str
    confidence: float  # 0-1, confiança na sugestão
    evidence: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    reverted_at: Optional[datetime] = None
    impact_score: float = 0.0  # Score de impacto após aplicação


class SelfImprovementEngine:
    """
    Motor de auto-aperiçoamento do NexusClaw.
    Analisa interações, identifica padrões e aplica melhorias.
    """
    
    def __init__(self, agent: Any, memory_system: Any = None):
        self.settings = get_settings()
        self.agent = agent
        self.memory_system = memory_system
        
        # Armazenamento de métricas
        self.metrics = PerformanceMetrics()
        self.interaction_history: List[InteractionRecord] = []
        self.improvement_queue: List[ImprovementAction] = []
        self.applied_improvements: List[ImprovementAction] = []
        
        # Configurações de auto-aperiçoamento
        self.enabled = True
        self.min_interactions_for_analysis = 10
        self.improvement_interval = 300  # 5 minutos
        self.max_history_size = 10000
        
        # Lock para operações assíncronas
        self._lock = asyncio.Lock()
        
        # Inicializa o loop de melhoria
        self._improvement_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Inicia o motor de auto-aperiçoamento"""
        logger.info("Iniciando motor de auto-aperiçoamento...")
        self._improvement_task = asyncio.create_task(self._improvement_loop())
        logger.info("Motor de auto-aperiçoamento ativo")
    
    async def stop(self):
        """Para o motor de auto-aperiçoamento"""
        if self._improvement_task:
            self._improvement_task.cancel()
            try:
                await self._improvement_task
            except asyncio.CancelledError:
                pass
        logger.info("Motor de auto-aperiçoamento parado")
    
    async def record_interaction(
        self,
        prompt: str,
        response: str,
        context: List[Dict[str, str]],
        user_id: str,
        channel: str,
        skills_used: List[str] = None,
        execution_time: float = 0.0,
        tokens_used: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """Registra uma interação para análise"""
        async with self._lock:
            record = InteractionRecord(
                id=f"interaction_{len(self.interaction_history)}_{time.time()}",
                timestamp=datetime.now(),
                user_id=user_id,
                channel=channel,
                prompt=prompt,
                response=response,
                context=context,
                skills_used=skills_used or [],
                execution_time=execution_time,
                tokens_used=tokens_used,
                metadata=metadata or {}
            )
            
            self.interaction_history.append(record)
            
            # Limita tamanho do histórico
            if len(self.interaction_history) > self.max_history_size:
                self.interaction_history = self.interaction_history[-self.max_history_size:]
            
            # Atualiza métricas
            self._update_metrics(record)
            
            logger.debug(f"Interação registrada: {record.id}")
    
    async def record_feedback(
        self,
        interaction_id: str,
        feedback_type: FeedbackType,
        value: Any = None,
        reason: str = None
    ):
        """Registra feedback para uma interação"""
        async with self._lock:
            # Encontra a interação
            for record in reversed(self.interaction_history):
                if record.id == interaction_id:
                    record.feedback[feedback_type.value] = {
                        "value": value,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Atualiza métricas de satisfação
                    if feedback_type == FeedbackType.EXPLICIT_THUMB:
                        if value == "up":
                            self.metrics.successful_interactions += 1
                        else:
                            self.metrics.failed_interactions += 1
                    
                    elif feedback_type == FeedbackType.EXPLICIT_RATING:
                        self.metrics.user_satisfaction_score = (
                            self.metrics.user_satisfaction_score * 0.9 + float(value) * 0.1
                        )
                    
                    break
    
    def _update_metrics(self, record: InteractionRecord):
        """Atualiza métricas com base em uma nova interação"""
        self.metrics.total_interactions += 1
        
        # Média de tempo de resposta
        total_time = self.metrics.average_response_time * (self.metrics.total_interactions - 1)
        self.metrics.average_response_time = (total_time + record.execution_time) / self.metrics.total_interactions
        
        # Média de tokens
        total_tokens = self.metrics.average_tokens * (self.metrics.total_interactions - 1)
        self.metrics.average_tokens = (total_tokens + record.tokens_used) / self.metrics.total_interactions
        
        # Contagem de uso de skills
        for skill in record.skills_used:
            self.metrics.skill_usage_count[skill] = self.metrics.skill_usage_count.get(skill, 0) + 1
        
        # Padrões de prompt (extrai palavras-chave)
        words = record.prompt.lower().split()
        for word in words[:5]:  # Primeiras 5 palavras
            if len(word) > 3:
                self.metrics.prompt_patterns[word] = self.metrics.prompt_patterns.get(word, 0) + 1
    
    async def _improvement_loop(self):
        """Loop principal de auto-aperiçoamento"""
        while True:
            try:
                await asyncio.sleep(self.improvement_interval)
                
                if not self.enabled:
                    continue
                
                # Verifica se há interações suficientes para analisar
                if len(self.interaction_history) < self.min_interactions_for_analysis:
                    continue
                
                logger.info("Iniciando ciclo de auto-aperiçoamento...")
                
                # Executa análises
                await self._analyze_patterns()
                await self._identify_failures()
                await self._optimize_prompts()
                await self._evaluate_skills()
                await self._apply_improvements()
                
                logger.info("Ciclo de auto-aperiçoamento concluído")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erro no loop de auto-aperiçoamento: {e}", exc_info=True)
    
    async def _analyze_patterns(self):
        """Analisa padrões nas interações"""
        logger.debug("Analisando padrões...")
        
        # Analisa padrões de sucesso
        successful_prompts = [
            r for r in self.interaction_history[-100:]
            if r.feedback.get("thumb", {}).get("value") == "up"
        ]
        
        if successful_prompts:
            # Extrai elementos comuns em prompts bem-sucedidos
            success_patterns = self._extract_patterns(successful_prompts)
            
            # Cria ação de melhoria se encontrar padrões
            if success_patterns:
                action = ImprovementAction(
                    id=f"pattern_{len(self.improvement_queue)}",
                    type="prompt_tweak",
                    priority=3,
                    description=f"Padrões identificados em {len(successful_prompts)} interações bem-sucedidas",
                    target="system_prompt",
                    suggested_change=json.dumps(success_patterns),
                    confidence=0.7,
                    evidence=[f"{len(successful_prompts)} interações analisadas"]
                )
                self.improvement_queue.append(action)
    
    async def _identify_failures(self):
        """Identifica falhas e gera ações corretivas"""
        logger.debug("Identificando falhas...")
        
        # Interações com feedback negativo
        failed_interactions = [
            r for r in self.interaction_history[-100:]
            if r.feedback.get("thumb", {}).get("value") == "down"
            or r.feedback.get("rating", {}).get("value", 5) <= 2
        ]
        
        for interaction in failed_interactions:
            reason = interaction.feedback.get("thumb", {}).get("reason") or "Feedback negativo"
            
            # Identifica tipo de erro
            error_type = self._classify_error(interaction, reason)
            
            if error_type:
                self.metrics.error_types[error_type] = self.metrics.error_types.get(error_type, 0) + 1
                
                # Cria ação corretiva
                action = self._generate_corrective_action(interaction, error_type, reason)
                if action:
                    self.improvement_queue.append(action)
    
    def _classify_error(self, interaction: InteractionRecord, reason: str) -> Optional[str]:
        """Classifica o tipo de erro"""
        reason_lower = reason.lower()
        prompt_lower = interaction.prompt.lower()
        
        if any(word in reason_lower for word in ["vago", "genérico", "curto"]):
            return "insufficient_detail"
        elif any(word in reason_lower for word in ["errado", "incorreto", "mal"]):
            return "incorrect_information"
        elif any(word in reason_lower for word in ["lento", "demoro"]):
            return "slow_response"
        elif any(word in reason_lower for word in ["não funciona", "falhou"]):
            return "execution_failure"
        elif any(word in prompt_lower for word in ["código", "programa", "função"]):
            return "coding_error"
        else:
            return "general_error"
    
    def _generate_corrective_action(
        self,
        interaction: InteractionRecord,
        error_type: str,
        reason: str
    ) -> Optional[ImprovementAction]:
        """Gera ação corretiva para um erro"""
        
        corrective_prompts = {
            "insufficient_detail": "Forneça respostas mais detalhadas e específicas quando solicitado.",
            "incorrect_information": "Verifique informações antes de responder. Se não tiver certeza, indique isso.",
            "slow_response": "Priorize respostas diretas quando a pergunta for simples.",
            "execution_failure": "Teste mais cuidadosamente código e comandos antes de sugerir.",
            "coding_error": "Revise a sintaxe e lógica do código gerado.",
            "general_error": "Melhore a compreensão do contexto da conversa."
        }
        
        if error_type in corrective_prompts:
            return ImprovementAction(
                id=f"corrective_{len(self.improvement_queue)}",
                type="prompt_tweak",
                priority=4,
                description=f"Correção de erro: {error_type}",
                target="system_prompt",
                suggested_change=corrective_prompts[error_type],
                confidence=0.6,
                evidence=[f"Interação: {interaction.id}", f"Razão: {reason}"]
            )
        
        return None
    
    async def _optimize_prompts(self):
        """Otimiza prompts do sistema com base em resultados"""
        logger.debug("Otimizando prompts...")
        
        # Calcula score de satisfação geral
        recent = self.interaction_history[-50:]
        positive = sum(1 for r in recent if r.feedback.get("thumb", {}).get("value") == "up")
        satisfaction = positive / len(recent) if recent else 0.5
        
        # Se satisfação abaixo de 60%, sugere ajustes
        if satisfaction < 0.6:
            action = ImprovementAction(
                id=f"prompt_opt_{len(self.improvement_queue)}",
                type="parameter_adjust",
                priority=5,
                description="Satisfação abaixo do esperado",
                target="temperature",
                suggested_change="0.8" if satisfaction < 0.4 else "0.7",
                confidence=0.5,
                evidence=[f"Satisfação: {satisfaction:.1%}"]
            )
            self.improvement_queue.append(action)
    
    async def _evaluate_skills(self):
        """Avalia desempenho das habilidades"""
        logger.debug("Avaliando habilidades...")
        
        for skill_name, usage_count in self.metrics.skill_usage_count.items():
            if usage_count < 3:
                continue
            
            # Calcula taxa de sucesso da skill
            skill_records = [
                r for r in self.interaction_history
                if skill_name in r.skills_used
            ]
            
            successful = sum(
                1 for r in skill_records
                if r.feedback.get("thumb", {}).get("value") == "up"
            )
            
            success_rate = successful / len(skill_records) if skill_records else 0
            
            # Se skill tem baixa taxa de sucesso, marca para revisão
            if success_rate < 0.5 and len(skill_records) >= 5:
                action = ImprovementAction(
                    id=f"skill_review_{len(self.improvement_queue)}",
                    type="skill_update",
                    priority=4,
                    description=f"Skill '{skill_name}' com baixa taxa de sucesso",
                    target=f"skills.{skill_name}",
                    suggested_change="Revisar implementação e documentação",
                    confidence=0.7,
                    evidence=[f"Taxa de sucesso: {success_rate:.1%}"]
                )
                self.improvement_queue.append(action)
    
    async def _apply_improvements(self):
        """Aplica melhorias da fila"""
        if not self.improvement_queue:
            return
        
        # Ordena por prioridade
        self.improvement_queue.sort(key=lambda x: x.priority, reverse=True)
        
        # Aplica as top 3 melhorias
        applied = 0
        for action in self.improvement_queue[:3]:
            if action.priority >= 4 and action.confidence >= 0.6:
                success = await self._apply_action(action)
                
                if success:
                    action.applied_at = datetime.now()
                    self.applied_improvements.append(action)
                    applied += 1
        
        # Remove ações aplicadas da fila
        self.improvement_queue = self.improvement_queue[applied:]
    
    async def _apply_action(self, action: ImprovementAction) -> bool:
        """Aplica uma ação de melhoria"""
        try:
            if action.type == "prompt_tweak":
                # Adiciona ao system prompt
                current_prompt = getattr(self.agent, 'system_prompt', '')
                new_prompt = f"{current_prompt}\n\nNota de melhoria: {action.suggested_change}"
                self.agent.system_prompt = new_prompt
                logger.info(f"Aplicada melhoria de prompt: {action.id}")
                
            elif action.type == "parameter_adjust":
                # Ajusta parâmetros
                if action.target == "temperature":
                    try:
                        temp = float(action.suggested_change)
                        if hasattr(self.agent.llm, 'settings'):
                            self.agent.llm.settings.ollama_temperature = temp
                        logger.info(f"Temperatura ajustada para: {temp}")
                    except ValueError:
                        pass
                
            elif action.type == "skill_update":
                # Marca skill para revisão
                logger.info(f"Skill marcada para revisão: {action.target}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar ação {action.id}: {e}")
            return False
    
    def _extract_patterns(self, records: List[InteractionRecord]) -> Dict[str, Any]:
        """Extrai padrões de registros bem-sucedidos"""
        patterns = {
            "common_structures": [],
            "successful_lengths": [],
            "style_elements": []
        }
        
        # Extrai comprimentos de respostas bem-sucedidas
        for record in records:
            word_count = len(record.response.split())
            patterns["successful_lengths"].append(word_count)
        
        # Calcula estatísticas
        if patterns["successful_lengths"]:
            avg_length = sum(patterns["successful_lengths"]) / len(patterns["successful_lengths"])
            patterns["avg_response_length"] = int(avg_length)
        
        return patterns
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório de desempenho"""
        return {
            "metrics": {
                "total_interactions": self.metrics.total_interactions,
                "success_rate": self.metrics.successful_interactions / max(1, self.metrics.total_interactions),
                "average_response_time": self.metrics.average_response_time,
                "average_tokens": self.metrics.average_tokens,
                "user_satisfaction": self.metrics.user_satisfaction_score,
                "top_skills": sorted(
                    self.metrics.skill_usage_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "common_errors": self.metrics.error_types
            },
            "improvements": {
                "pending": len(self.improvement_queue),
                "applied": len(self.applied_improvements),
                "last_applied": self.applied_improvements[-1].id if self.applied_improvements else None
            },
            "recommendations": [
                {
                    "priority": a.priority,
                    "description": a.description,
                    "confidence": a.confidence
                }
                for a in self.improvement_queue[:5]
            ]
        }


class EvolutionEngine:
    """
    Motor de evolução que permite ao assistente
    criar e refinar suas próprias habilidades.
    """
    
    def __init__(self, agent: Any, improvement_engine: SelfImprovementEngine):
        self.agent = agent
        self.improvement_engine = improvement_engine
        self.skill_templates: Dict[str, Dict[str, Any]] = {}
        self.generated_skills: List[Dict[str, Any]] = []
    
    async def analyze_skill_gaps(self) -> List[Dict[str, Any]]:
        """Analisa gaps de habilidades baseado em interações"""
        gaps = []
        
        # Analisa tipos de solicitações não atendidas
        recent_prompts = [
            r.prompt.lower() for r in self.improvement_engine.interaction_history[-100:]
        ]
        
        # Keywords que indicam necessidades
        need_patterns = {
            "traduz": "translation",
            "resum": "summarization",
            "analis": "analysis",
            "compar": "comparison",
            "gerar": "generation",
            "calcul": "calculation",
            "busc": "search"
        }
        
        for pattern, skill_type in need_patterns.items():
            matches = sum(1 for p in recent_prompts if pattern in p)
            
            if matches >= 3:
                # Verifica se a skill já existe
                existing_skills = list(self.agent.skills_registry.keys())
                skill_exists = any(skill_type in s for s in existing_skills)
                
                if not skill_exists:
                    gaps.append({
                        "type": skill_type,
                        "frequency": matches,
                        "suggestion": f"Criar habilidade de {skill_type}"
                    })
        
        return gaps
    
    async def suggest_new_skills(self) -> List[ImprovementAction]:
        """Sugere novas habilidades baseadas em padrões"""
        gaps = await self.analyze_skill_gaps()
        suggestions = []
        
        for gap in gaps:
            action = ImprovementAction(
                id=f"new_skill_{len(suggestions)}",
                type="new_skill",
                priority=gap["frequency"],
                description=f"Nova skill: {gap['type']}",
                target="skills",
                suggested_change=self._generate_skill_template(gap["type"]),
                confidence=0.5,
                evidence=[f"{gap['frequency']} solicitações detectadas"]
            )
            suggestions.append(action)
        
        return suggestions
    
    def _generate_skill_template(self, skill_type: str) -> str:
        """Gera template de código para nova skill"""
        
        templates = {
            "translation": '''
class TranslationSkill(BaseSkill):
    metadata = SkillMetadata(
        name="translate",
        description="Traduz texto entre idiomas",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "source_lang": {"type": "string"},
                "target_lang": {"type": "string"}
            },
            "required": ["text", "target_lang"]
        }
    )
    
    async def execute(self, text: str, target_lang: str, source_lang: str = "auto") -> dict:
        # Implementar tradução
        return {"success": True, "translated": text}
''',
            "summarization": '''
class SummarizationSkill(BaseSkill):
    metadata = SkillMetadata(
        name="summarize",
        description="Resume textos longos",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "max_length": {"type": "number", "default": 100}
            },
            "required": ["text"]
        }
    )
    
    async def execute(self, text: str, max_length: int = 100) -> dict:
        # Implementar resumo
        return {"success": True, "summary": text[:max_length]}
'''
        }
        
        return templates.get(skill_type, "# Skill template não disponível")
    
    async def evolve_skill(self, skill_name: str, feedback: Dict[str, Any]) -> bool:
        """Evolui uma skill existente com base em feedback"""
        logger.info(f"Evoluindo skill: {skill_name}")
        
        # Registra evolução
        evolution_record = {
            "skill_name": skill_name,
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback,
            "version": len([s for s in self.generated_skills if s.get("name") == skill_name]) + 1
        }
        
        self.generated_skills.append(evolution_record)
        
        # Adiciona à fila de melhorias
        action = ImprovementAction(
            id=f"evolve_{skill_name}",
            type="skill_update",
            priority=4,
            description=f"Evolução de {skill_name}",
            target=f"skills.{skill_name}",
            suggested_change=json.dumps(feedback),
            confidence=0.7
        )
        
        self.improvement_engine.improvement_queue.append(action)
        
        return True


# Função de registro do módulo
def register_self_improvement(agent: Any, memory_system: Any = None) -> SelfImprovementEngine:
    """Registra e retorna o motor de auto-aperiçoamento"""
    engine = SelfImprovementEngine(agent, memory_system)
    return engine
