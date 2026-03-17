"""
NexusClaw - Ponto de Entrada Principal
======================================

Este módulo inicializa e coordena todos os componentes
do NexusClaw.
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from core.agent import NexusAgent
from core.memory import MemorySystem
from core.orchestrator import TaskOrchestrator
from core.self_improvement import SelfImprovementEngine, EvolutionEngine, register_self_improvement
from core.code_evolution import create_code_evolution_system
from core.deep_thinking import (
    create_deep_thinking_agent,
    ReasoningDepth,
    ChainOfThought,
    SelfReflector,
    AutonomousPlanner,
    DeepThinkingAgent
)
from adapters.base import ADAPTERS
from skills import get_skills_registry
from skills.builtins import register_all_skills


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/app/data/nexus-ai.log")
    ]
)

logger = logging.getLogger(__name__)


class NexusAIApplication:
    """Aplicação principal do NexusClaw"""
    
    def __init__(self):
        self.settings = get_settings()
        self.agent = None
        self.memory_system = None
        self.orchestrator = None
        self.improvement_engine = None
        self.evolution_engine = None
        self.code_evolution = None
        self.deep_thinking_agent = None  # Sistema de pensamento profundo
        self.adapters = {}
        self._running = False
    
    async def initialize(self):
        """Inicializa todos os componentes"""
        logger.info("=" * 60)
        logger.info("Inicializando NexusClaw...")
        logger.info("=" * 60)
        
        # 1. Registra habilidades
        logger.info("📦 Registrando habilidades...")
        register_all_skills()
        skills_registry = get_skills_registry()
        logger.info(f"   {len(skills_registry)} habilidades disponíveis")
        
        # 2. Inicializa sistema de memória
        logger.info("🧠 Inicializando sistema de memória...")
        self.memory_system = MemorySystem()
        await self.memory_system.initialize()
        logger.info("   Sistema de memória pronto")
        
        # 3. Cria agente
        logger.info("🤖 Criando agente...")
        self.agent = NexusAgent(
            skills_registry=skills_registry,
            memory_system=self.memory_system
        )
        logger.info("   Agente pronto")
        
        # 4. Inicializa orquestrador
        logger.info("⚙️ Inicializando orquestrador de tarefas...")
        self.orchestrator = TaskOrchestrator(
            agent=self.agent,
            max_parallel=self.settings.max_parallel_tasks
        )
        await self.orchestrator.start()
        logger.info("   Orquestrador pronto")
        
        # 5. Inicializa motor de auto-aperiçoamento
        logger.info("🔄 Inicializando motor de auto-aperiçoamento...")
        self.improvement_engine = register_self_improvement(
            agent=self.agent,
            memory_system=self.memory_system
        )
        await self.improvement_engine.start()
        self.evolution_engine = EvolutionEngine(
            agent=self.agent,
            improvement_engine=self.improvement_engine
        )
        logger.info("   Sistema de auto-aperiçoamento ativo")
        
        # 6. Inicializa sistema de evolução de código
        logger.info("💻 Inicializando sistema de evolução de código...")
        self.code_evolution = create_code_evolution_system(self.improvement_engine)
        logger.info("   Sistema de análise de código ativo")
        
        # 7. Inicializa sistema de pensamento profundo
        logger.info("🧠 Inicializando sistema de pensamento profundo...")
        self.deep_thinking_agent = create_deep_thinking_agent(self.agent)
        logger.info("   Sistema de pensamento profundo ativo")
        
        # 8. Inicializa adaptadores
        logger.info("📡 Inicializando adaptadores...")
        await self._initialize_adapters()
        
        logger.info("=" * 60)
        logger.info("NexusClaw inicializado com sucesso!")
        logger.info("🔄 Auto-aperiçoamento: ATIVO")
        logger.info("💻 Análise de Código: ATIVO")
        logger.info("🧠 Pensamento Profundo: ATIVO")
        logger.info("=" * 60)
    
    async def _initialize_adapters(self):
        """Inicializa adaptadores de canal"""
        
        # CLI Adapter (sempre disponível)
        if True:  # Sempre inicia CLI
            from adapters.base import CLIAdapter
            self.adapters["cli"] = CLIAdapter(self.agent)
            await self.adapters["cli"].start()
            logger.info("   ✓ CLI Adapter")
        
        # Telegram
        if self.settings.telegram_bot_token:
            adapter = ADAPTERS["telegram"](self.agent)
            try:
                await adapter.start()
                self.adapters["telegram"] = adapter
                logger.info("   ✓ Telegram Adapter")
            except Exception as e:
                logger.error(f"   ✗ Telegram Adapter: {e}")
        
        # Discord
        if self.settings.discord_bot_token:
            adapter = ADAPTERS["discord"](self.agent)
            try:
                await adapter.start()
                self.adapters["discord"] = adapter
                logger.info("   ✓ Discord Adapter")
            except Exception as e:
                logger.error(f"   ✗ Discord Adapter: {e}")
        
        # Web
        adapter = ADAPTERS["web"](self.agent)
        await adapter.start()
        self.adapters["web"] = adapter
        logger.info("   ✓ Web Adapter (porta 8000)")
    
    async def shutdown(self):
        """Encerra todos os componentes"""
        logger.info("Encerrando NexusClaw...")
        
        # Para motor de auto-aperiçoamento
        if self.improvement_engine:
            await self.improvement_engine.stop()
            logger.info("   Motor de auto-aperiçoamento parado")
        
        # Para adaptadores
        for name, adapter in self.adapters.items():
            try:
                await adapter.stop()
                logger.info(f"   Adapter {name} parado")
            except Exception as e:
                logger.error(f"Erro ao parar {name}: {e}")
        
        # Para orquestrador
        if self.orchestrator:
            await self.orchestrator.stop()
        
        logger.info("NexusClaw encerrado")
    
    async def run_cli_interactive(self):
        """Executa modo interativo via CLI"""
        if "cli" in self.adapters:
            await self.adapters["cli"].run_interactive()


# Instância global da aplicação
app_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    global app_instance
    
    app_instance = NexusAIApplication()
    await app_instance.initialize()
    
    yield
    
    await app_instance.shutdown()


# Criação da aplicação FastAPI
def create_app() -> FastAPI:
    """Cria a aplicação FastAPI"""
    
    app = FastAPI(
        title="NexusClaw",
        description="Seu Assistente de IA Pessoal Soberano",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rotas
    @app.get("/")
    async def root():
        return {
            "name": "NexusClaw",
            "version": "1.0.0",
            "status": "running",
            "description": "Seu Assistente de IA Pessoal Soberano"
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "adapters": list(app_instance.adapters.keys()) if app_instance else []
        }
    
    @app.post("/api/chat")
    async def chat(request: dict):
        """Endpoint para enviar mensagens"""
        if not app_instance:
            return {"error": "Aplicação não inicializada"}
        
        message = request.get("message", "")
        user_id = request.get("user_id", "api_user")
        channel = request.get("channel", "api")
        
        response = await app_instance.agent.handle_message(
            user_id=user_id,
            channel=channel,
            message=message
        )
        
        return {
            "response": response,
            "user_id": user_id,
            "channel": channel
        }
    
    @app.get("/api/memories")
    async def get_memories(query: str = "", limit: int = 5):
        """Busca em memórias"""
        if not app_instance or not app_instance.memory_system:
            return {"error": "Sistema de memória não disponível"}
        
        results = await app_instance.memory_system.search_memories(
            query=query,
            limit=limit
        )
        
        return {"results": results}
    
    @app.post("/api/memories/fact")
    async def add_fact(request: dict):
        """Adiciona um fato à memória"""
        if not app_instance or not app_instance.memory_system:
            return {"error": "Sistema de memória não disponível"}
        
        fact = request.get("fact", "")
        await app_instance.memory_system.add_fact(fact=fact)
        
        return {"success": True, "fact": fact}
    
    @app.get("/api/tasks")
    async def get_tasks(user_id: str = None):
        """Lista tarefas"""
        if not app_instance or not app_instance.orchestrator:
            return {"error": "Orquestrador não disponível"}
        
        if user_id:
            tasks = app_instance.orchestrator.task_queue.get_user_tasks(user_id)
        else:
            tasks = list(app_instance.orchestrator.task_queue.tasks.values())
        
        return {
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "created_at": t.created_at.isoformat()
                }
                for t in tasks
            ]
        }
    
    @app.get("/api/improvement/report")
    async def get_improvement_report():
        """Retorna relatório de auto-aperiçoamento"""
        if not app_instance or not app_instance.improvement_engine:
            return {"error": "Motor de auto-aperiçoamento não disponível"}
        
        report = await app_instance.improvement_engine.get_performance_report()
        return report
    
    @app.post("/api/improvement/feedback")
    async def submit_feedback(request: dict):
        """Registra feedback para uma interação"""
        if not app_instance or not app_instance.improvement_engine:
            return {"error": "Motor de auto-aperiçoamento não disponível"}
        
        interaction_id = request.get("interaction_id")
        feedback_type = request.get("feedback_type", "thumb")
        value = request.get("value", "up")
        reason = request.get("reason")
        
        from core.self_improvement import FeedbackType
        fb_type = FeedbackType.EXPLICIT_THUMB
        
        await app_instance.improvement_engine.record_feedback(
            interaction_id=interaction_id,
            feedback_type=fb_type,
            value=value,
            reason=reason
        )
        
        return {"success": True}
    
    @app.get("/api/evolution/skills")
    async def get_skill_suggestions():
        """Sugere novas habilidades baseadas em padrões"""
        if not app_instance or not app_instance.evolution_engine:
            return {"error": "Motor de evolução não disponível"}
        
        gaps = await app_instance.evolution_engine.analyze_skill_gaps()
        return {"gaps": gaps}
    
    @app.get("/api/evolution/suggestions")
    async def get_evolution_suggestions():
        """Retorna sugestões de evolução"""
        if not app_instance or not app_instance.evolution_engine:
            return {"error": "Motor de evolução não disponível"}
        
        suggestions = await app_instance.evolution_engine.suggest_new_skills()
        return {
            "suggestions": [
                {
                    "id": s.id,
                    "type": s.type,
                    "description": s.description,
                    "priority": s.priority,
                    "confidence": s.confidence
                }
                for s in suggestions
            ]
        }
    
    # ==================== Code Evolution Endpoints ====================
    
    @app.get("/api/code/analysis")
    async def analyze_code():
        """Analisa a base de código e retorna issues e sugestões"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de análise de código não disponível"}
        
        analysis = await app_instance.code_evolution["code_analyzer"].analyze_all()
        
        return {
            "modules": {
                name: {
                    "file_path": str(a.file_path),
                    "issues_count": len(a.issues),
                    "suggestions_count": len(a.suggestions),
                    "complexity_score": a.complexity_score,
                    "maintainability_score": a.maintainability_score,
                    "tested": a.tested,
                    "documented": a.documented,
                    "issues": a.issues[:5],  # Top 5 issues
                    "suggestions": a.suggestions[:3]  # Top 3 suggestions
                }
                for name, a in analysis.items()
            },
            "critical_issues": app_instance.code_evolution["code_analyzer"].get_critical_issues(),
            "summary": {
                "total_modules": len(analysis),
                "total_issues": sum(len(a.issues) for a in analysis.values()),
                "avg_complexity": sum(a.complexity_score for a in analysis.values()) / len(analysis) if analysis else 0
            }
        }
    
    @app.get("/api/code/improvements")
    async def get_code_improvements():
        """Retorna plano de melhorias de código"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de análise de código não disponível"}
        
        improvements = app_instance.code_evolution["code_analyzer"].generate_improvement_plan()
        
        return {
            "improvements": [
                {
                    "id": i.id,
                    "type": i.type,
                    "title": i.title,
                    "description": i.description,
                    "priority": i.priority,
                    "effort": i.effort,
                    "impact": i.impact
                }
                for i in improvements
            ]
        }
    
    @app.get("/api/code/recommendations")
    async def get_technical_recommendations():
        """Retorna recomendações técnicas completas"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de evolução de código não disponível"}
        
        recommendations = await app_instance.code_evolution["evolution_advisor"].generate_technical_recommendations()
        
        return recommendations
    
    @app.get("/api/code/priorities")
    async def get_developer_priorities():
        """Retorna trabalho priorizado para desenvolvedores"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de evolução de código não disponível"}
        
        priorities = app_instance.code_evolution["evolution_advisor"].prioritize_developer_work()
        
        return {
            "priorities": priorities,
            "total": len(priorities)
        }
    
    # ==================== Feature Suggestion Endpoints ====================
    
    @app.get("/api/features/suggestions")
    async def get_feature_suggestions():
        """Retorna sugestões de novas funcionalidades"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de sugestão não disponível"}
        
        suggestions = await app_instance.code_evolution["feature_suggester"].analyze_usage_patterns()
        
        return {
            "suggestions": [
                {
                    "id": s.id,
                    "type": s.type,
                    "title": s.title,
                    "description": s.description,
                    "justification": s.justification,
                    "priority": s.priority,
                    "effort": s.effort,
                    "impact": s.impact,
                    "auto_detected": s.auto_detected
                }
                for s in suggestions
            ]
        }
    
    @app.get("/api/features/user/{user_id}")
    async def get_user_suggestions(user_id: str):
        """Retorna sugestões personalizadas para usuário"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de sugestão não disponível"}
        
        suggestions = await app_instance.code_evolution["feature_suggester"].suggest_to_user(user_id)
        
        return {
            "user_id": user_id,
            "suggestions": suggestions
        }
    
    @app.post("/api/features/request")
    async def request_feature(request: dict):
        """Registra solicitação de nova feature pelo usuário"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de sugestão não disponível"}
        
        from core.code_evolution import FeatureRequest
        
        feature_request = FeatureRequest(
            id=f"user_req_{datetime.now().timestamp()}",
            type="new_feature",
            title=request.get("title", "Solicitação de usuário"),
            description=request.get("description", ""),
            justification=request.get("justification", "Solicitado pelo usuário"),
            priority=request.get("priority", 3),
            effort=request.get("effort", "medium"),
            impact=request.get("impact", "medium"),
            user_requested=True
        )
        
        request_id = app_instance.code_evolution["feature_suggester"].add_user_request(feature_request)
        
        return {
            "success": True,
            "request_id": request_id,
            "message": "Sua solicitação foi registrada e será analisada"
        }
    
    @app.get("/api/features/code/{feature_id}")
    async def get_feature_code_template(feature_id: str):
        """Retorna template de código para implementar feature"""
        if not app_instance or not app_instance.code_evolution:
            return {"error": "Sistema de evolução de código não disponível"}
        
        from core.code_evolution import FeatureRequest
        
        # Cria uma feature request temporária para gerar o snippet
        temp_request = FeatureRequest(
            id=feature_id,
            type="new_feature",
            title="Feature",
            description="",
            justification="",
            priority=3,
            effort="medium",
            impact="medium"
        )
        
        code_snippet = app_instance.code_evolution["evolution_advisor"].generate_code_snippet_suggestion(temp_request)
        
        if code_snippet:
            return {
                "feature_id": feature_id,
                "code_template": code_snippet,
                "language": "python"
            }
        else:
            return {
                "error": "Template não disponível para esta feature"
            }
    
    # ==================== Deep Thinking Endpoints ====================
    
    @app.post("/api/deep-think/process")
    async def process_with_deep_thinking(request: dict):
        """Processa uma mensagem com pensamento profundo"""
        if not app_instance or not app_instance.deep_thinking_agent:
            return {"error": "Sistema de pensamento profundo não disponível"}
        
        message = request.get("message", "")
        context = request.get("context", [])
        depth = request.get("depth", "deep")
        
        # Converte profundidade para enum
        depth_map = {
            "surface": ReasoningDepth.SURFACE,
            "medium": ReasoningDepth.MEDIUM,
            "deep": ReasoningDepth.DEEP,
            "comprehensive": ReasoningDepth.COMPREHENSIVE
        }
        reasoning_depth = depth_map.get(depth.lower(), ReasoningDepth.DEEP)
        
        result = await app_instance.deep_thinking_agent.process_with_deep_thinking(
            prompt=message,
            context=context,
            depth=reasoning_depth,
            reflect=True
        )
        
        return {
            "response": result["response"],
            "thoughts_count": result["thoughts_count"],
            "depth_achieved": result["depth_achieved"],
            "reasoning_summary": {
                "total_thoughts": len(result["reasoning_chain"].thoughts),
                "depth_level": result["reasoning_chain"].depth_level.name,
                "reflection_score": result["reflection"].get("overall_score", 0) if result.get("reflection") else None
            }
        }
    
    @app.post("/api/deep-think/autonomous")
    async def autonomous_task_execution(request: dict):
        """Executa uma tarefa completamente autônoma"""
        if not app_instance or not app_instance.deep_thinking_agent:
            return {"error": "Sistema de pensamento profundo não disponível"}
        
        goal = request.get("goal", "")
        context = request.get("context", {})
        
        result = await app_instance.deep_thinking_agent.autonomous_task(
            goal=goal,
            context=context
        )
        
        return result
    
    @app.get("/api/deep-think/reasoning")
    async def get_reasoning_summary():
        """Retorna resumo das capacidades de raciocínio"""
        if not app_instance or not app_instance.deep_thinking_agent:
            return {"error": "Sistema de pensamento profundo não disponível"}
        
        summary = app_instance.deep_thinking_agent.get_reasoning_summary()
        
        return {
            "total_thoughts": summary.get("total_thoughts", 0),
            "reflections": summary.get("reflections", {}),
            "plans_executed": summary.get("plans", 0),
            "current_beliefs": summary.get("current_beliefs", {}),
            "active_goals": summary.get("goals", [])
        }
    
    @app.post("/api/deep-think/reflect")
    async def reflect_on_response(request: dict):
        """Reflete sobre uma resposta específica"""
        if not app_instance or not app_instance.deep_thinking_agent:
            return {"error": "Sistema de pensamento profundo não disponível"}
        
        prompt = request.get("prompt", "")
        response = request.get("response", "")
        context = request.get("context", [])
        
        reflection = await app_instance.deep_thinking_agent.self_reflector.reflect_on_response(
            prompt=prompt,
            response=response,
            context=context
        )
        
        return reflection
    
    @app.get("/api/deep-think/state")
    async def get_agentic_state():
        """Retorna o estado atual do agente autônomo"""
        if not app_instance or not app_instance.deep_thinking_agent:
            return {"error": "Sistema de pensamento profundo não disponível"}
        
        state = app_instance.deep_thinking_agent.state
        
        return {
            "current_task": state.current_task,
            "active_goals": state.goals,
            "beliefs": state.beliefs,
            "observations_count": len(state.observations),
            "confidence_level": state.confidence_level,
            "pending_actions": len(state.pending_actions),
            "completed_actions": len(state.completed_actions)
        }
    
    return app


# Main
if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
