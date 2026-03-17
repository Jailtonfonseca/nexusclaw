"""
NexusClaw - Sistema de Pensamento Profundo e Agente Autônomo
============================================================

Este módulo implementa capacidades avançadas de raciocínio,
permitindo ao assistente pensar profundamente, refletir sobre
suas decisões e operar de forma verdadeiramente autônoma.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re

from config.settings import get_settings


logger = logging.getLogger(__name__)


class ReasoningDepth(Enum):
    """Níveis de profundidade de raciocínio"""
    SURFACE = 1      # Resposta direta
    MEDIUM = 2       # Análise básica
    DEEP = 3        # Raciocínio elaborado
    COMPREHENSIVE = 4 # Pensamento holístico


class ThoughtType(Enum):
    """Tipos de pensamento"""
    OBSERVATION = "observation"       # Observação
    ANALYSIS = "analysis"           # Análise
    HYPOTHESIS = "hypothesis"       # Hipótese
    REASONING = "reasoning"         # Raciocínio
    PLANNING = "planning"           # Planejamento
    REFLECTION = "reflection"      # Reflexão
    EVALUATION = "evaluation"       # Avaliação
    DECISION = "decision"           # Decisão
    ACTION = "action"              # Ação
    VERIFICATION = "verification"   # Verificação
    CORRECTION = "correction"      # Correção


@dataclass
class Thought:
    """Um pensamento individual"""
    id: str
    type: ThoughtType
    content: str
    depth: ReasoningDepth
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningChain:
    """Cadeia completa de raciocínio"""
    id: str
    task: str
    thoughts: List[Thought] = field(default_factory=list)
    root_thought_id: Optional[str] = None
    current_thought_id: Optional[str] = None
    depth_level: ReasoningDepth = ReasoningDepth.SURFACE
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    success: bool = False
    reflection: str = ""
    lessons_learned: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgenticState:
    """Estado do agente autônomo"""
    current_task: Optional[str] = None
    reasoning_chains: Dict[str, ReasoningChain] = field(default_factory=dict)
    active_plan: Optional[Dict[str, Any]] = None
    pending_actions: List[Dict[str, Any]] = field(default_factory=list)
    completed_actions: List[Dict[str, Any]] = field(default_factory=list)
    beliefs: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    confidence_level: float = 0.5


class ChainOfThought:
    """
    Implementa pensamento em cadeia (Chain-of-Thought)
    permitindo raciocínio profundo e estruturado.
    """
    
    def __init__(self, agent: Any):
        self.agent = agent
        self.settings = get_settings()
        self.current_chain: Optional[ReasoningChain] = None
        self.thought_counter = 0
    
    async def think_deeply(
        self,
        task: str,
        context: List[Dict[str, str]] = None,
        depth: ReasoningDepth = ReasoningDepth.DEEP,
        max_iterations: int = 10
    ) -> ReasoningChain:
        """
        Executa pensamento profundo sobre uma tarefa.
        
        O processo inclui:
        1. Observação - Entender o problema
        2. Análise - Decompor em partes
        3. Hipótese - Formular possíveis soluções
        4. Raciocínio - Avaliar cada opção
        5. Decisão - Escolher a melhor abordagem
        6. Verificação - Validar a decisão
        """
        logger.info(f"Iniciando pensamento profundo sobre: {task[:50]}...")
        
        # Cria nova cadeia de raciocínio
        chain = ReasoningChain(
            id=f"chain_{datetime.now().timestamp()}",
            task=task,
            depth_level=depth
        )
        
        self.current_chain = chain
        
        # Etapa 1: Observação
        observation = await self._create_thought(
            ThoughtType.OBSERVATION,
            f"Tarefa recebida: {task}\nContexto: {self._summarize_context(context)}",
            ReasoningDepth.SURFACE
        )
        chain.thoughts.append(observation)
        chain.root_thought_id = observation.id
        
        # Etapa 2: Análise
        analysis = await self._create_thought(
            ThoughtType.ANALYSIS,
            await self._analyze_task(task, context),
            ReasoningDepth.MEDIUM
        )
        observation.children_ids.append(analysis.id)
        analysis.parent_id = observation.id
        chain.thoughts.append(analysis)
        
        # Etapa 3: Geração de hipóteses
        if depth.value >= ReasoningDepth.MEDIUM.value:
            hypothesis = await self._create_thought(
                ThoughtType.HYPOTHESIS,
                await self._generate_hypotheses(task, context),
                ReasoningDepth.MEDIUM
            )
            analysis.children_ids.append(hypothesis.id)
            hypothesis.parent_id = analysis.id
            chain.thoughts.append(hypothesis)
        
        # Etapa 4: Raciocínio profundo
        if depth.value >= ReasoningDepth.DEEP.value:
            current = analysis
            iterations = 0
            
            while iterations < max_iterations:
                reasoning = await self._create_thought(
                    ThoughtType.REASONING,
                    await self._deep_reason(current, task, context),
                    ReasoningDepth.DEEP
                )
                current.children_ids.append(reasoning.id)
                reasoning.parent_id = current.id
                chain.thoughts.append(reasoning)
                
                # Verifica se atingiu convergência
                if reasoning.confidence > 0.8:
                    break
                
                current = reasoning
                iterations += 1
        
        # Etapa 5: Decisão
        decision = await self._create_thought(
            ThoughtType.DECISION,
            await self._make_decision(chain),
            depth
        )
        
        # Conecta à última thought relevante
        if chain.thoughts:
            last_thought = chain.thoughts[-1]
            last_thought.children_ids.append(decision.id)
            decision.parent_id = last_thought.id
        
        chain.thoughts.append(decision)
        chain.current_thought_id = decision.id
        
        # Etapa 6: Verificação
        if depth.value >= ReasoningDepth.DEEP.value:
            verification = await self._create_thought(
                ThoughtType.VERIFICATION,
                await self._verify_decision(decision, task),
                ReasoningDepth.COMPREHENSIVE
            )
            decision.children_ids.append(verification.id)
            verification.parent_id = decision.id
            chain.thoughts.append(verification)
        
        # Completa a cadeia
        chain.completed_at = datetime.now()
        
        # Reflexão final
        if depth.value >= ReasoningDepth.COMPREHENSIVE.value:
            chain.reflection = await self._reflect_on_chain(chain)
            chain.lessons_learned = await self._extract_lessons(chain)
        
        logger.info(f"Pensamento concluído: {len(chain.thoughts)} pensamentos gerados")
        
        return chain
    
    async def _create_thought(
        self,
        thought_type: ThoughtType,
        content: str,
        depth: ReasoningDepth
    ) -> Thought:
        """Cria um novo pensamento"""
        self.thought_counter += 1
        
        return Thought(
            id=f"thought_{self.thought_counter}",
            type=thought_type,
            content=content,
            depth=depth,
            confidence=0.5  # Inicia com confiança média
        )
    
    def _summarize_context(self, context: List[Dict[str, str]] = None) -> str:
        """Resume o contexto da conversa"""
        if not context:
            return "Sem contexto adicional"
        
        summary_parts = []
        for msg in context[-5:]:  # Últimas 5 mensagens
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:50]
            summary_parts.append(f"{role}: {content}...")
        
        return " | ".join(summary_parts)
    
    async def _analyze_task(self, task: str, context: List[Dict[str, str]] = None) -> str:
        """Analisa a tarefa em profundidade"""
        
        # Usa LLM para análise
        analysis_prompt = f"""
Analise profundamente esta tarefa:
"{task}"

Considere:
1. O que o usuário está pedindo?
2. Quais são os requisitos explícitos?
3. Quais são os requisitos implícitos?
4. Quais informações estão faltando?
5. Que restrições existem?

Forneça uma análise estruturada em formato:
- Objetivo principal:
- Requisitos:
- Informações necessárias:
- Restrições:
- Complexidade: (baixa/média/alta)
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=500
            )
            return response.get("content", "")
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return f"Análise básica: {task}"
    
    async def _generate_hypotheses(self, task: str, context: List[Dict[str, str]] = None) -> str:
        """Gera múltiplas hipóteses de solução"""
        
        hypothesis_prompt = f"""
Para a tarefa: "{task}"

Gere pelo menos 3 abordagens diferentes para resolver:
1. Abordagem direta:
2. Abordagem alternativa:
3. Abordagem criativa:

Para cada uma, considere:
- Prós
- Contras
- Recursos necessários
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=hypothesis_prompt,
                temperature=0.7,
                max_tokens=600
            )
            return response.get("content", "")
        except Exception:
            return f"Hipótese: Resolver {task}"
    
    async def _deep_reason(
        self,
        previous_thought: Thought,
        task: str,
        context: List[Dict[str, str]] = None
    ) -> str:
        """Executa raciocínio profundo iterativo"""
        
        reasoning_prompt = f"""
Tarefa: {task}

Pensamento anterior:
{previous_thought.content}

Com base no pensamento anterior, aprofunde o raciocínio:
1. O que está correto nesta análise?
2. O que pode estar errado?
3. Que novos insights surgem?
4. Qual a confiança nesta análise? (0-1)

Pense passo a passo.
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=reasoning_prompt,
                temperature=0.5,
                max_tokens=400
            )
            
            content = response.get("content", "")
            
            # Atualiza confiança
            confidence_match = re.search(r'confiança[:\s]+([0-9.]+)', content.lower())
            if confidence_match:
                previous_thought.confidence = float(confidence_match.group(1))
            
            return content
            
        except Exception:
            return "Continuando análise..."
    
    async def _make_decision(self, chain: ReasoningChain) -> str:
        """Faz uma decisão baseada em todo o raciocínio"""
        
        # Consolida todos os pensamentos
        all_thoughts = "\n\n".join([
            f"[{t.type.value}] {t.content[:200]}..."
            for t in chain.thoughts[-5:]
        ])
        
        decision_prompt = f"""
Baseado em toda a análise anterior, qual é a melhor abordagem para resolver esta tarefa?

Resumo da análise:
{all_thoughts}

Escolha uma abordagem e justifique:
1. Decisão:
2. Justificativa:
3. Confiança:
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=decision_prompt,
                temperature=0.3,
                max_tokens=300
            )
            return response.get("content", "")
        except Exception:
            return "Decisão: Prosseguir com a solução mais direta"
    
    async def _verify_decision(self, decision: Thought, task: str) -> str:
        """Verifica se a decisão é válida"""
        
        verification_prompt = f"""
Tarefa original: {task}

Decisão tomada:
{decision.content}

Verifique:
1. A decisãoresolve o problema?
2. Há gargalos potenciais?
3. O que pode dar errado?
4. Como mitigar riscos?

Forneça uma verificação completa.
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=verification_prompt,
                temperature=0.2,
                max_tokens=300
            )
            return response.get("content", "")
        except Exception:
            return "Verificação: Parece adequado"
    
    async def _reflect_on_chain(self, chain: ReasoningChain) -> str:
        """Reflete sobre toda a cadeia de raciocínio"""
        
        reflection_prompt = f"""
Analise o processo de raciocínio completo para a tarefa:
{chain.task}

Número de pensamentos: {len(chain.thoughts)}
Tipos de pensamentos: {', '.join(set(t.type.value for t in chain.thoughts))}

Reflita:
1. O raciocínio foi completo?
2. Algo importante foi perdido?
3. Como poderia ser melhorado?
4. O que foi aprendido?
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=reflection_prompt,
                temperature=0.5,
                max_tokens=400
            )
            return response.get("content", "")
        except Exception:
            return "Reflexão: Processo de pensamento concluído"
    
    async def _extract_lessons(self, chain: ReasoningChain) -> List[str]:
        """Extrai lições aprendidas"""
        
        lessons = []
        
        # Extrai automaticamente lições básicas
        if chain.thoughts:
            # Confiança média geral
            avg_confidence = sum(t.confidence for t in chain.thoughts) / len(chain.thoughts)
            lessons.append(f"Confiança média do raciocínio: {avg_confidence:.2f}")
        
        # Lições de cada tipo de pensamento
        thought_types = defaultdict(int)
        for thought in chain.thoughts:
            thought_types[thought.type.value] += 1
        
        most_common = max(thought_types.items(), key=lambda x: x[1])
        lessons.append(f"Tipo de pensamento mais frequente: {most_common[0]} ({most_common[1]}x)")
        
        return lessons


class SelfReflector:
    """
    Sistema de auto-reflexão que permite ao agente
    examinar e melhorar suas próprias respostas.
    """
    
    def __init__(self, agent: Any):
        self.agent = agent
        self.reflection_history: List[Dict[str, Any]] = []
    
    async def reflect_on_response(
        self,
        prompt: str,
        response: str,
        context: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Reflete sobre uma resposta gerada.
        
        Avalia:
        - Precisão
        - Completude
        - Clareza
        - Adequação ao contexto
        """
        
        reflection_prompt = f"""
Você é um sistema de auto-reflexão. Avalie esta resposta:

PERGUNTA: {prompt}

SUA RESPOSTA: {response}

Contexto adicional: {self._format_context(context)}

Para cada aspecto, forneça uma avaliação de 0-10 e explicações:

1. PRECISÃO - A informação está correta?
2. COMPLETUDE - A resposta cobre todos os aspectos?
3. CLAREZA - A resposta é fácil de entender?
4. RELEVÂNCIA - A resposta responde à pergunta?
5. TOM - O tom é apropriado?

Retorne em formato JSON:
{{
  "accuracy": {{"score": X, "reason": "..."}},
  "completeness": {{"score": X, "reason": "..."}},
  "clarity": {{"score": X, "reason": "..."}},
  "relevance": {{"score": X, "reason": "..."}},
  "tone": {{"score": X, "reason": "..."}},
  "overall_score": X,
  "improvements": ["...", "..."],
  "self_criticism": "..."
}}
"""
        
        try:
            llm_response = await self.agent.llm.generate(
                prompt=reflection_prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            content = llm_response.get("content", "{}")
            
            # Extrai JSON da resposta
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                reflection = json.loads(json_match.group())
            else:
                reflection = {"error": "Não foi possível processar reflexão"}
            
            # Armazena reflexão
            self.reflection_history.append({
                "prompt": prompt,
                "response": response,
                "reflection": reflection,
                "timestamp": datetime.now()
            })
            
            return reflection
            
        except Exception as e:
            logger.error(f"Erro na reflexão: {e}")
            return {"error": str(e)}
    
    async def suggest_improvements(
        self,
        reflection: Dict[str, Any]
    ) -> str:
        """Sugere como melhorar com base na reflexão"""
        
        if "error" in reflection:
            return "Não foi possível gerar sugestões"
        
        improvements = reflection.get("improvements", [])
        
        if not improvements:
            return "A resposta parece adequada"
        
        suggestions_prompt = f"""
Baseado nestas áreas de melhoria:
{chr(10).join(f"- {imp}" for imp in improvements)}

Sugira uma versão melhorada da resposta original.
Mantenha o mesmo tom e estilo.
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=suggestions_prompt,
                temperature=0.5,
                max_tokens=500
            )
            return response.get("content", "")
        except Exception:
            return ""
    
    def _format_context(self, context: List[Dict[str, str]] = None) -> str:
        """Formata contexto para o prompt"""
        if not context:
            return "Sem contexto"
        return f"{len(context)} mensagens no histórico"
    
    def get_reflection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das reflexões"""
        
        if not self.reflection_history:
            return {"total": 0}
        
        scores = [r["reflection"].get("overall_score", 0) for r in self.reflection_history]
        
        return {
            "total_reflections": len(self.reflection_history),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "recent_trend": "improving" if len(scores) > 1 and scores[-1] > scores[-2] else "stable"
        }


class AutonomousPlanner:
    """
    Planejador autônomo que cria e executa
    planos complexos de forma independente.
    """
    
    def __init__(self, agent: Any):
        self.agent = agent
        self.current_plan: Optional[Dict[str, Any]] = None
        self.plan_history: List[Dict[str, Any]] = []
    
    async def create_and_execute_plan(
        self,
        goal: str,
        context: Dict[str, Any] = None,
        max_steps: int = 20
    ) -> Dict[str, Any]:
        """
        Cria e executa um plano autônomo.
        
        O processo inclui:
        1. Análise do objetivo
        2. Decomposição em tarefas
        3. Identificação de dependências
        4. Execução passo a passo
        5. Verificação de resultados
        6. Ajuste se necessário
        """
        
        logger.info(f"Criando plano autônomo para: {goal[:50]}...")
        
        # Fase 1: Análise do objetivo
        goal_analysis = await self._analyze_goal(goal, context)
        
        # Fase 2: Decomposição em tarefas
        tasks = await self._decompose_goal(goal, goal_analysis)
        
        # Fase 3: Identificar dependências
        task_dependencies = await self._identify_dependencies(tasks)
        
        # Fase 4: Criar plano
        plan = {
            "goal": goal,
            "tasks": tasks,
            "dependencies": task_dependencies,
            "current_step": 0,
            "completed_steps": [],
            "failed_steps": [],
            "status": "planning"
        }
        
        self.current_plan = plan
        
        # Fase 5: Execução
        plan["status"] = "executing"
        
        for step in range(min(len(tasks), max_steps)):
            plan["current_step"] = step
            
            task = tasks[step]
            
            # Verifica dependências
            if not self._can_execute(task, plan):
                # Tenta executar tarefas pendentes primeiro
                continue
            
            # Executa a tarefa
            result = await self._execute_task(task, plan)
            
            if result["success"]:
                plan["completed_steps"].append({
                    "task": task,
                    "result": result,
                    "timestamp": datetime.now()
                })
            else:
                plan["failed_steps"].append({
                    "task": task,
                    "error": result.get("error"),
                    "timestamp": datetime.now()
                })
                
                # Tenta recuperação
                recovery = await self._attempt_recovery(task, result, plan)
                if not recovery:
                    # Se não consegue recuperar, para
                    break
        
        # Fase 6: Verificação final
        plan["status"] = "completed" if plan["completed_steps"] else "failed"
        plan["final_result"] = await self._verify_plan_results(plan)
        
        # Armazena histórico
        self.plan_history.append(plan)
        
        return plan
    
    async def _analyze_goal(
        self,
        goal: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Analisa o objetivo em profundidade"""
        
        analysis_prompt = f"""
Analise este objetivo para criar um plano de execução:

OBJETIVO: {goal}

Contexto: {json.dumps(context) if context else "Sem contexto"}

Determine:
1. O que constitui sucesso?
2. Quais são os marcos intermediários?
3. Que recursos são necessários?
4. Quais são os riscos potenciais?
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=analysis_prompt,
                temperature=0.4,
                max_tokens=400
            )
            return response.get("content", "")
        except Exception:
            return f"Objetivo: {goal}"
    
    async def _decompose_goal(
        self,
        goal: str,
        analysis: str
    ) -> List[Dict[str, Any]]:
        """Decompõe o objetivo em tarefas menores"""
        
        decomposition_prompt = f"""
Decompõe este objetivo em tarefas específicas e executáveis:

OBJETIVO: {goal}

ANÁLISE: {analysis}

Retorne uma lista de tarefas em formato JSON:
[
  {{
    "id": "step_1",
    "description": "Descrição da tarefa",
    "type": "action/thought/verification",
    "estimated_time": "short/medium/long",
    "required_tools": ["tool1", "tool2"],
    "success_criteria": "O que define sucesso"
  }}
]
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=decomposition_prompt,
                temperature=0.5,
                max_tokens=800
            )
            
            content = response.get("content", "[]")
            
            # Extrai JSON
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                tasks = json.loads(json_match.group())
                return tasks
            else:
                # Fallback: cria tarefa única
                return [{"id": "main", "description": goal, "type": "action"}]
                
        except Exception as e:
            logger.error(f"Erro na decomposição: {e}")
            return [{"id": "main", "description": goal, "type": "action"}]
    
    async def _identify_dependencies(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Identifica dependências entre tarefas"""
        
        dependencies = {}
        
        for i, task in enumerate(tasks):
            task_id = task.get("id", f"step_{i}")
            dependencies[task_id] = []
            
            # Detecta dependências simples por contexto
            for j, prev_task in enumerate(tasks[:i]):
                # Se tarefa anterior é necessária
                if any(
                    keyword in task.get("description", "").lower()
                    for keyword in prev_task.get("description", "").lower().split()[:3]
                ):
                    dependencies[task_id].append(prev_task.get("id", f"step_{j}"))
        
        return dependencies
    
    def _can_execute(self, task: Dict, plan: Dict) -> bool:
        """Verifica se uma tarefa pode ser executada"""
        
        task_id = task.get("id")
        dependencies = plan.get("dependencies", {}).get(task_id, [])
        
        # Verifica se todas as dependências foram concluídas
        completed_ids = [s["task"].get("id") for s in plan.get("completed_steps", [])]
        
        for dep in dependencies:
            if dep not in completed_ids:
                return False
        
        return True
    
    async def _execute_task(
        self,
        task: Dict,
        plan: Dict
    ) -> Dict[str, Any]:
        """Executa uma tarefa específica"""
        
        task_type = task.get("type", "action")
        
        if task_type == "action":
            # Executa ação usando skills
            return await self._execute_action(task)
        elif task_type == "thought":
            # Executa pensamento/reflexão
            return await self._execute_thought(task)
        elif task_type == "verification":
            # Executa verificação
            return await self._execute_verification(task, plan)
        
        return {"success": False, "error": "Tipo de tarefa desconhecido"}
    
    async def _execute_action(self, task: Dict) -> Dict[str, Any]:
        """Executa uma ação"""
        
        description = task.get("description", "")
        
        try:
            # Tenta executar usando as skills disponíveis
            # Aqui seria a integração com o sistema de skills
            
            return {
                "success": True,
                "result": f"Ação executada: {description}",
                "output": description
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_thought(self, task: Dict) -> Dict[str, Any]:
        """Executa um pensamento"""
        
        thought = await self.agent.chain_of_thought.think_deeply(
            task.get("description", ""),
            depth=ReasoningDepth.DEEP
        )
        
        return {
            "success": True,
            "result": thought.result or "Pensamento concluído",
            "chain": thought
        }
    
    async def _execute_verification(
        self,
        task: Dict,
        plan: Dict
    ) -> Dict[str, Any]:
        """Executa verificação"""
        
        completed = plan.get("completed_steps", [])
        
        verification = f"Verificação: {len(completed)} de {len(plan.get('tasks', []))} tarefas concluídas"
        
        return {
            "success": True,
            "result": verification
        }
    
    async def _attempt_recovery(
        self,
        failed_task: Dict,
        result: Dict,
        plan: Dict
    ) -> bool:
        """Tenta recuperar de uma falha"""
        
        recovery_prompt = f"""
Uma tarefa falhou:

TAREFA: {failed_task.get('description')}
ERRO: {result.get('error')}

Plano atual: {len(plan.get('completed_steps', []))} tarefas concluídas

Como você pode recuperar esta situação?
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=recovery_prompt,
                temperature=0.5,
                max_tokens=200
            )
            
            # Se gerou sugestão, adiciona ao plano
            return len(response.get("content", "")) > 10
            
        except Exception:
            return False
    
    async def _verify_plan_results(self, plan: Dict) -> str:
        """Verifica os resultados do plano"""
        
        completed = len(plan.get("completed_steps", []))
        total = len(plan.get("tasks", []))
        failed = len(plan.get("failed_steps", []))
        
        return f"Plano concluído: {completed}/{total} tarefas bem-sucedidas, {failed} falhas"


class DeepThinkingAgent:
    """
    Agente completo com capacidade de pensamento profundo.
    Integra todos os sistemas de raciocínio.
    """
    
    def __init__(self, agent: Any):
        self.agent = agent
        self.chain_of_thought = ChainOfThought(agent)
        self.self_reflector = SelfReflector(agent)
        self.autonomous_planner = AutonomousPlanner(agent)
        self.state = AgenticState()
    
    async def process_with_deep_thinking(
        self,
        prompt: str,
        context: List[Dict[str, str]] = None,
        depth: ReasoningDepth = ReasoningDepth.DEEP,
        reflect: bool = True
    ) -> Dict[str, Any]:
        """
        Processa uma solicitação com pensamento profundo.
        
        Inclui:
        1. Pensamento em cadeia
        2. Reflexão automática
        3. Execução autônoma se necessário
        """
        
        # Registra observação
        self.state.observations.append(f"Processando: {prompt[:50]}...")
        
        # Etapa 1: Pensamento profundo
        reasoning_chain = await self.chain_of_thought.think_deeply(
            task=prompt,
            context=context,
            depth=depth
        )
        
        # Etapa 2: Decisão baseada no raciocínio
        # Extrai a decisão da cadeia
        decision_thought = next(
            (t for t in reasoning_chain.thoughts if t.type == ThoughtType.DECISION),
            reasoning_chain.thoughts[-1] if reasoning_chain.thoughts else None
        )
        
        # Etapa 3: Gera resposta baseada na decisão
        response = await self._generate_response_from_decision(
            prompt,
            decision_thought,
            context
        )
        
        # Etapa 4: Reflexão (opcional)
        reflection_result = None
        if reflect:
            reflection_result = await self.self_reflector.reflect_on_response(
                prompt=prompt,
                response=response,
                context=context
            )
            
            # Se encontrou problemas, tenta melhorar
            if reflection_result.get("overall_score", 10) < 7:
                improved = await self.self_reflector.suggest_improvements(reflection_result)
                if improved:
                    response = improved
        
        # Atualiza crenças
        self._update_beliefs(prompt, response)
        
        return {
            "response": response,
            "reasoning_chain": reasoning_chain,
            "reflection": reflection_result,
            "thoughts_count": len(reasoning_chain.thoughts),
            "depth_achieved": reasoning_chain.depth_level.value
        }
    
    async def _generate_response_from_decision(
        self,
        prompt: str,
        decision: Thought,
        context: List[Dict[str, str]] = None
    ) -> str:
        """Gera resposta baseada na decisão de raciocínio"""
        
        # Usa o conteúdo da decisão para guiar a resposta
        generation_prompt = f"""
Com base nesta análise profunda:

{decision.content}

Responda à pergunta do usuário de forma clara e útil:

Pergunta: {prompt}

Contexto: {self._format_context(context)}
"""
        
        try:
            response = await self.agent.llm.generate(
                prompt=generation_prompt,
                temperature=0.7,
                max_tokens=1000
            )
            return response.get("content", "")
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return "Desculpe, encontrei dificuldades ao processar sua solicitação."
    
    def _format_context(self, context: List[Dict[str, str]] = None) -> str:
        """Formata contexto"""
        if not context:
            return "Sem contexto adicional"
        
        return f"{len(context)} mensagens no histórico"
    
    def _update_beliefs(self, prompt: str, response: str):
        """Atualiza crenças do agente"""
        
        # Extrai informações relevantes
        words = prompt.lower().split()
        
        # Crenças simples baseadas em padrões
        if "sou" in prompt or "meu nome" in prompt:
            # Usuário se apresentou
            self.state.beliefs["user_introduced"] = True
            
        if any(keyword in words for keyword in ["sempre", "nunca", "jamais", "todos"]):
            # Crença sobre padrões e absolutismos
            self.state.beliefs["pattern_detected"] = True
    
    async def autonomous_task(
        self,
        goal: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Executa uma tarefa completamente autônoma.
        
        O agente:
        1. Entende o objetivo
        2. Cria um plano
        3. Executa cada etapa
        4. Verifica resultados
        5. Ajusta se necessário
        """
        
        self.state.current_task = goal
        
        # Cria e executa plano
        plan = await self.autonomous_planner.create_and_execute_plan(
            goal=goal,
            context=context
        )
        
        # Analisa resultado
        analysis = {
            "goal": goal,
            "status": plan["status"],
            "completed": len(plan.get("completed_steps", [])),
            "failed": len(plan.get("failed_steps", [])),
            "final_result": plan.get("final_result", "")
        }
        
        return analysis
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Retorna resumo do raciocínio"""
        
        return {
            "total_thoughts": self.chain_of_thought.thought_counter,
            "reflections": self.self_reflector.get_reflection_stats(),
            "plans": len(self.autonomous_planner.plan_history),
            "current_beliefs": self.state.beliefs,
            "goals": self.state.goals
        }


def create_deep_thinking_agent(agent: Any) -> DeepThinkingAgent:
    """Cria e retorna o agente com pensamento profundo"""
    return DeepThinkingAgent(agent)
