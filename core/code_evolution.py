"""
NexusClaw - Sistema de Análise e Evolução de Código
================================================

Este módulo implementa capacidades de auto-análise do código
e sugestão proativa de novas funcionalidades aos usuários.
"""

import asyncio
import json
import logging
import inspect
import ast
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

from config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysis:
    """Resultado da análise de código"""
    module: str
    file_path: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    complexity_score: float = 0.0
    maintainability_score: float = 0.0
    tested: bool = False
    documented: bool = False


@dataclass
class FeatureRequest:
    """Solicitação de nova funcionalidade"""
    id: str
    type: str  # "code_improvement", "new_feature", "integration"
    title: str
    description: str
    justification: str
    priority: int  # 1-5
    effort: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    created_at: datetime = field(default_factory=datetime.now)
    user_requested: bool = False
    auto_detected: bool = False
    status: str = "pending"  # "pending", "approved", "in_progress", "completed", "rejected"
    implementation_notes: str = ""


class CodeAnalyzer:
    """
    Analisador de código do NexusClaw.
    Examina a base de código e identifica áreas de melhoria.
    """
    
    def __init__(self, project_root: str = "/app"):
        self.project_root = Path(project_root)
        self.analysis_cache: Dict[str, CodeAnalysis] = {}
        self.last_analysis: Optional[datetime] = None
    
    async def analyze_all(self) -> Dict[str, CodeAnalysis]:
        """Analisa todos os módulos do projeto"""
        logger.info("Iniciando análise de código...")
        
        analyses = {}
        
        # Analisa módulos core
        core_dir = self.project_root / "core"
        if core_dir.exists():
            analyses["core"] = await self._analyze_module("core", core_dir)
        
        # Analisa módulos adapters
        adapters_dir = self.project_root / "adapters"
        if adapters_dir.exists():
            analyses["adapters"] = await self._analyze_module("adapters", adapters_dir)
        
        # Analisa módulos skills
        skills_dir = self.project_root / "skills"
        if skills_dir.exists():
            analyses["skills"] = await self._analyze_module("skills", skills_dir)
        
        # Analisa config
        config_dir = self.project_root / "config"
        if config_dir.exists():
            analyses["config"] = await self._analyze_module("config", config_dir)
        
        self.last_analysis = datetime.now()
        self.analysis_cache = analyses
        
        logger.info(f"Análise concluída: {len(analyses)} módulos")
        return analyses
    
    async def _analyze_module(self, module_name: str, module_path: Path) -> CodeAnalysis:
        """Analisa um módulo específico"""
        analysis = CodeAnalysis(
            module=module_name,
            file_path=str(module_path)
        )
        
        python_files = list(module_path.rglob("*.py"))
        
        for py_file in python_files:
            if "__pycache__" in str(py_file):
                continue
            
            try:
                file_analysis = await self._analyze_file(py_file)
                analysis.issues.extend(file_analysis["issues"])
                analysis.suggestions.extend(file_analysis["suggestions"])
                analysis.complexity_score += file_analysis["complexity"]
                
                if file_analysis["has_tests"]:
                    analysis.tested = True
                if file_analysis["has_docstrings"]:
                    analysis.documented = True
                    
            except Exception as e:
                logger.warning(f"Erro ao analisar {py_file}: {e}")
        
        # Calcula scores médios
        if python_files:
            analysis.complexity_score /= len(python_files)
            analysis.maintainability_score = max(0, 100 - analysis.complexity_score * 10)
        
        return analysis
    
    async def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analisa um arquivo Python específico"""
        result = {
            "issues": [],
            "suggestions": [],
            "complexity": 0,
            "has_tests": False,
            "has_docstrings": False
        }
        
        content = file_path.read_text()
        
        # Verifica documentação
        if '"""' in content or "'''" in content:
            result["has_docstrings"] = True
        
        # Verifica testes
        if "_test" in file_path.name or "test_" in file_path.name:
            result["has_tests"] = True
        
        # Analisa AST
        try:
            tree = ast.parse(content)
            
            # Conta funções e classes
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            
            # Calcula complexidade ciclomática simplificada
            complexity = len(functions) + len(classes)
            
            # Identifica issues
            for node in ast.walk(tree):
                # Funções sem docstrings
                if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                    if len(inspect.signature(node)) > 5:
                        result["issues"].append({
                            "type": "missing_docstring",
                            "severity": "warning",
                            "location": f"{file_path.name}:{node.lineno}",
                            "message": f"Função '{node.name}' não tem docstring"
                        })
                
                # Exceções amplas
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception"):
                        result["issues"].append({
                            "type": "broad_exception",
                            "severity": "info",
                            "location": f"{file_path.name}:{node.lineno}",
                            "message": "Consider usar exceção mais específica"
                        })
                
                # Loops aninhados (complexidade)
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if isinstance(child, ast.For) and child != node:
                            result["issues"].append({
                                "type": "nested_loop",
                                "severity": "warning",
                                "location": f"{file_path.name}:{node.lineno}",
                                "message": "Loops aninhados detectados - considerar otimização"
                            })
                            break
            
            result["complexity"] = complexity
            
        except SyntaxError as e:
            result["issues"].append({
                "type": "syntax_error",
                "severity": "error",
                "location": f"{file_path.name}:{e.lineno}",
                "message": str(e)
            })
        
        # Gera sugestões
        if len(result["issues"]) > 5:
            result["suggestions"].append({
                "type": "refactor_module",
                "priority": 3,
                "message": f"Módulo {file_path.name} tem muitos issues - considerar refatoração"
            })
        
        return result
    
    def get_critical_issues(self) -> List[Dict[str, Any]]:
        """Retorna issues críticos que precisam de atenção"""
        critical = []
        
        for analysis in self.analysis_cache.values():
            for issue in analysis.issues:
                if issue["severity"] == "error":
                    critical.append(issue)
                elif issue["type"] == "broad_exception":
                    critical.append(issue)
        
        return critical
    
    def generate_improvement_plan(self) -> List[FeatureRequest]:
        """Gera plano de melhorias baseado na análise"""
        requests = []
        
        # Analisa cada módulo
        for module_name, analysis in self.analysis_cache.items():
            # Issues de documentação
            doc_issues = [i for i in analysis.issues if i["type"] == "missing_docstring"]
            if len(doc_issues) > 3:
                requests.append(FeatureRequest(
                    id=f"improve_doc_{module_name}",
                    type="code_improvement",
                    title=f"Melhorar documentação do módulo {module_name}",
                    description=f"Adicionar docstrings a {len(doc_issues)} funções",
                    justification="Código bem documentado é mais fácil de manter e evoluir",
                    priority=3,
                    effort="medium",
                    impact="medium",
                    auto_detected=True
                ))
            
            # Issues de complexidade
            if analysis.complexity_score > 10:
                requests.append(FeatureRequest(
                    id=f"refactor_{module_name}",
                    type="code_improvement",
                    title=f"Refatorar módulo {module_name}",
                    description="Reduzir complexidade ciclomática",
                    justification=f"Score de complexidade: {analysis.complexity_score:.1f}",
                    priority=4,
                    effort="high",
                    impact="high",
                    auto_detected=True
                ))
            
            # Módulo sem testes
            if not analysis.tested and module_name != "config":
                requests.append(FeatureRequest(
                    id=f"add_tests_{module_name}",
                    type="code_improvement",
                    title=f"Adicionar testes ao módulo {module_name}",
                    description="Criar testes unitários e de integração",
                    justification="Testes garantem qualidade e facilitam refatorações",
                    priority=4,
                    effort="medium",
                    impact="high",
                    auto_detected=True
                ))
        
        return requests


class FeatureSuggester:
    """
    Sugestor proativo de funcionalidades.
    Analisa padrões de uso e sugere novas features.
    """
    
    def __init__(self, improvement_engine: Any):
        self.improvement_engine = improvement_engine
        self.usage_patterns: Dict[str, int] = defaultdict(int)
        self.feature_requests: List[FeatureRequest] = []
        self.user_preferences: Dict[str, Any] = {}
    
    async def analyze_usage_patterns(self) -> List[FeatureRequest]:
        """Analisa padrões de uso e gera sugestões"""
        suggestions = []
        
        # Analisa histórico de interações
        if hasattr(self.improvement_engine, 'interaction_history'):
            patterns = self._extract_usage_patterns()
            
            for pattern, count in patterns.items():
                if count >= 10:  # Mínimo de 10 ocorrências
                    suggestion = self._create_suggestion_from_pattern(pattern, count)
                    if suggestion:
                        suggestions.append(suggestion)
        
        # Analisa skills mais usadas
        if hasattr(self.improvement_engine, 'metrics'):
            top_skills = self._get_top_skills()
            
            for skill, usage in top_skills[:5]:
                # Sugere melhorias na skill mais usada
                if usage > 50:
                    suggestions.append(FeatureRequest(
                        id=f"enhance_{skill}",
                        type="code_improvement",
                        title=f"Melhorar skill '{skill}'",
                        description=f"Otimizar e expandir capabilities da skill",
                        justification=f"Usada {usage} vezes - é uma skill core",
                        priority=4,
                        effort="medium",
                        impact="high",
                        auto_detected=True
                    ))
        
        # Analisa gaps de funcionalidades
        gap_suggestions = await self._analyze_feature_gaps()
        suggestions.extend(gap_suggestions)
        
        self.feature_requests = suggestions
        return suggestions
    
    def _extract_usage_patterns(self) -> Dict[str, int]:
        """Extrai padrões de uso das interações"""
        patterns = defaultdict(int)
        
        for record in getattr(self.improvement_engine, 'interaction_history', []):
            prompt = record.prompt.lower()
            
            # Padrões de comando
            if prompt.startswith("/"):
                command = prompt.split()[0] if prompt.split() else prompt
                patterns[f"command:{command}"] += 1
            
            # Padrões de pergunta
            question_words = ["como", "o que", "onde", "quando", "por que", "qual"]
            for word in question_words:
                if word in prompt:
                    patterns[f"question:{word}"] += 1
            
            # Padrões de tarefa
            task_words = ["fazer", "criar", "buscar", "analisar", "gerar"]
            for word in task_words:
                if word in prompt:
                    patterns[f"task:{word}"] += 1
        
        return patterns
    
    def _get_top_skills(self) -> List[tuple]:
        """Retorna skills mais usadas"""
        if hasattr(self.improvement_engine, 'metrics'):
            skill_counts = getattr(self.improvement_engine.metrics, 'skill_usage_count', {})
            return sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        return []
    
    async def _analyze_feature_gaps(self) -> List[FeatureRequest]:
        """Analisa gaps de funcionalidades"""
        gaps = []
        
        # Analisa tipos de solicitação não atendidas
        recent_prompts = []
        if hasattr(self.improvement_engine, 'interaction_history'):
            recent_prompts = [
                r.prompt.lower() 
                for r in self.improvement_engine.interaction_history[-100:]
            ]
        
        # Padrões que indicam necessidades
        feature_patterns = {
            "tradução": {
                "keywords": ["traduz", "tradução", "english", "espanhol"],
                "suggestion": "Habilidade de tradução multilingue"
            },
            "resumo": {
                "keywords": ["resumo", "sumarizar", "breve", "curto"],
                "suggestion": "Habilidade de resumo inteligente"
            },
            "agendamento": {
                "keywords": ["agendar", "lembrete", "calendário", "reunião"],
                "suggestion": "Integração com calendário e lembretes"
            },
            "análise de código": {
                "keywords": ["debug", "erro", "bug", "código", "review"],
                "suggestion": "Análise avançada de código e debugging"
            },
            "geração de código": {
                "keywords": ["criar código", "gerar função", "implementar"],
                "suggestion": "Geração de código com templates"
            },
            "pesquisa": {
                "keywords": ["pesquisar", "buscar", "encontrar info"],
                "suggestion": "Busca avançada com múltiplas fontes"
            },
            "criação de conteúdo": {
                "keywords": ["escrever", "criar documento", "redigir"],
                "suggestion": "Criação de documentos e conteúdo"
            },
            "análise de dados": {
                "keywords": ["analisar dados", "gráfico", "estatística"],
                "suggestion": "Análise e visualização de dados"
            }
        }
        
        for feature, config in feature_patterns.items():
            matches = sum(
                1 for prompt in recent_prompts 
                if any(kw in prompt for kw in config["keywords"])
            )
            
            if matches >= 5:
                gaps.append(FeatureRequest(
                    id=f"gap_{feature}",
                    type="new_feature",
                    title=f"Adicionar: {config['suggestion']}",
                    description=f"Detected {matches} solicitações relacionadas a {feature}",
                    justification=f"Padrão recorrente detectado em {matches} interações",
                    priority=min(5, 2 + matches // 10),
                    effort="medium",
                    impact="high",
                    auto_detected=True
                ))
        
        return gaps
    
    def _create_suggestion_from_pattern(self, pattern: str, count: int) -> Optional[FeatureRequest]:
        """Cria sugestão baseada em padrão detectado"""
        pattern_type, value = pattern.split(":", 1)
        
        suggestions_map = {
            "command:/traduz": FeatureRequest(
                id="suggest_translation",
                type="new_feature",
                title="Habilidade de Tradução",
                description="Traduzir texto entre múltiplos idiomas",
                justification=f"Comando /traduz usado {count} vezes",
                priority=3,
                effort="low",
                impact="medium",
                auto_detected=True
            ),
            "question:como": FeatureRequest(
                id="suggest_tutorials",
                type="new_feature",
                title="Tutorial Interativo",
                description="Guias passo a passo para tarefas comuns",
                justification=f"Perguntas 'como' representam {count} interações",
                priority=2,
                effort="medium",
                impact="low",
                auto_detected=True
            ),
            "task:fazer": FeatureRequest(
                id="suggest_automation",
                type="new_feature",
                title="Automação de Tarefas",
                description="Executar múltiplas ações em sequência",
                justification=f"Solicitações de 'fazer' aparecem {count} vezes",
                priority=4,
                effort="high",
                impact="high",
                auto_detected=True
            )
        }
        
        return suggestions_map.get(pattern)
    
    async def suggest_to_user(self, user_id: str) -> List[str]:
        """Gera sugestões personalizadas para o usuário"""
        suggestions = []
        
        # Analisa histórico do usuário específico
        user_interactions = []
        if hasattr(self.improvement_engine, 'interaction_history'):
            user_interactions = [
                r for r in self.improvement_engine.interaction_history
                if r.user_id == user_id
            ]
        
        if not user_interactions:
            return ["Comece a usar o assistente para receber sugestões personalizadas!"]
        
        # Conta padrões do usuário
        user_patterns = defaultdict(int)
        for interaction in user_interactions[-50:]:
            words = interaction.prompt.lower().split()
            for word in words[:3]:
                if len(word) > 4:
                    user_patterns[word] += 1
        
        # Gera sugestões baseadas nos padrões
        top_patterns = sorted(user_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if any("traduz" in p[0] for p in top_patterns):
            suggestions.append(" Posso traduzir textos entre vários idiomas. Quer testar?")
        
        if any("código" in p[0] or "programa" in p[0] for p in top_patterns):
            suggestions.append(" Posso ajudar a escrever e depurar código. Precisa de ajuda?")
        
        if any("buscar" in p[0] or "pesquisar" in p[0] for p in top_patterns):
            suggestions.append(" Posso fazer pesquisas na web para você. Quer que eu busque algo?")
        
        if any("criar" in p[0] or "gerar" in p[0] for p in top_patterns):
            suggestions.append(" Posso criar arquivos, documentos e muito mais. Quer que eu gere algo?")
        
        if not suggestions:
            suggestions.append(" Estou aqui para ajudar! Me pergunte qualquer coisa.")
        
        return suggestions
    
    def add_user_request(self, request: FeatureRequest) -> str:
        """Adiciona solicitação de feature vinda do usuário"""
        request.user_requested = True
        request.status = "pending"
        self.feature_requests.append(request)
        return request.id


class CodeEvolutionAdvisor:
    """
    Advisor que ajuda na evolução do código do NexusClaw.
    Fornece recomendações técnicas e estratégicas.
    """
    
    def __init__(
        self,
        code_analyzer: CodeAnalyzer,
        feature_suggester: FeatureSuggester
    ):
        self.code_analyzer = code_analyzer
        self.feature_suggester = feature_suggester
        self.technical_debt: List[Dict[str, Any]] = []
    
    async def generate_technical_recommendations(self) -> Dict[str, Any]:
        """Gera recomendações técnicas para evolução do código"""
        
        # Análise de código
        await self.code_analyzer.analyze_all()
        critical_issues = self.code_analyzer.get_critical_issues()
        improvement_plan = self.code_analyzer.generate_improvement_plan()
        
        # Análise de features
        feature_suggestions = await self.feature_suggester.analyze_usage_patterns()
        
        # Consolida recomendações
        recommendations = {
            "critical_issues": critical_issues,
            "code_improvements": improvement_plan,
            "new_features": feature_suggestions,
            "technical_debt": self.technical_debt,
            "summary": {
                "total_issues": len(critical_issues),
                "improvements_needed": len(improvement_plan),
                "features_suggested": len(feature_suggestions),
                "debt_items": len(self.technical_debt)
            }
        }
        
        return recommendations
    
    def prioritize_developer_work(self) -> List[Dict[str, Any]]:
        """Prioriza trabalho do desenvolvedor baseado em impacto"""
        recommendations = []
        
        # Issues críticos primeiro
        for issue in self.code_analyzer.get_critical_issues():
            recommendations.append({
                "type": "critical_fix",
                "title": f"Fix: {issue['message']}",
                "location": issue.get("location", "Unknown"),
                "priority": 5,
                "effort": "low"
            })
        
        # Features de alto impacto
        all_features = (
            self.code_analyzer.generate_improvement_plan() +
            self.feature_suggester.feature_requests
        )
        
        # Ordena por prioridade e impacto
        all_features.sort(key=lambda x: (x.priority, x.impact == "high"), reverse=True)
        
        for feature in all_features[:10]:
            recommendations.append({
                "type": feature.type,
                "title": feature.title,
                "description": feature.description,
                "priority": feature.priority,
                "effort": feature.effort,
                "impact": feature.impact
            })
        
        return recommendations
    
    def generate_code_snippet_suggestion(
        self,
        feature_request: FeatureRequest
    ) -> Optional[str]:
        """Gera snippet de código para implementar uma feature"""
        
        snippets = {
            "new_feature:translation": '''
class TranslationSkill(BaseSkill):
    """Habilidade de tradução implementada automaticamente"""
    
    metadata = SkillMetadata(
        name="translate",
        description="Traduz texto entre idiomas",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "target_lang": {"type": "string"},
                "source_lang": {"type": "string", "default": "auto"}
            },
            "required": ["text", "target_lang"]
        }
    )
    
    async def execute(self, text: str, target_lang: str, source_lang: str = "auto") -> dict:
        # Implementação usando API de tradução
        translated = await self._translate_text(text, target_lang, source_lang)
        return {"success": True, "translated": translated, "lang": target_lang}
''',
            "new_feature:summarization": '''
class SummarizationSkill(BaseSkill):
    """Habilidade de resumo implementada automaticamente"""
    
    metadata = SkillMetadata(
        name="summarize",
        description="Resume textos longos",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "max_length": {"type": "number", "default": 100},
                "style": {"type": "string", "enum": ["brief", "detailed"]}
            },
            "required": ["text"]
        }
    )
    
    async def execute(self, text: str, max_length: int = 100, style: str = "brief") -> dict:
        summary = await self._summarize_text(text, max_length, style)
        return {"success": True, "summary": summary, "original_length": len(text)}
''',
            "new_feature:calendar": '''
class CalendarSkill(BaseSkill):
    """Habilidade de calendário implementada automaticamente"""
    
    metadata = SkillMetadata(
        name="calendar",
        description="Gerencia eventos e lembretes",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "list", "remind"]},
                "event": {"type": "string"},
                "datetime": {"type": "string"}
            },
            "required": ["action"]
        }
    )
    
    async def execute(self, action: str, event: str = None, datetime: str = None) -> dict:
        if action == "create":
            return await self._create_event(event, datetime)
        elif action == "list":
            return await self._list_events()
        elif action == "remind":
            return await self._set_reminder(event, datetime)
        return {"success": False, "error": "Invalid action"}
'''
        }
        
        key = f"new_feature:{feature_request.id.replace('gap_', '')}"
        return snippets.get(key)


def create_code_evolution_system(improvement_engine: Any) -> Dict[str, Any]:
    """Cria e retorna o sistema completo de evolução de código"""
    
    code_analyzer = CodeAnalyzer()
    feature_suggester = FeatureSuggester(improvement_engine)
    evolution_advisor = CodeEvolutionAdvisor(code_analyzer, feature_suggester)
    
    return {
        "code_analyzer": code_analyzer,
        "feature_suggester": feature_suggester,
        "evolution_advisor": evolution_advisor
    }
