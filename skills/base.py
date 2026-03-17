"""
NexusClaw - Sistema de Habilidades
=================================

Este módulo implementa o sistema de habilidades (skills)
que o agente pode utilizar para executar tarefas.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List
from dataclasses import dataclass
from pathlib import Path

from config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """Metadados de uma habilidade"""
    name: str
    description: str
    parameters: Dict[str, Any]
    examples: List[str] = None
    category: str = "general"
    requires_auth: bool = False


class BaseSkill(ABC):
    """Classe base para habilidades"""
    
    metadata: SkillMetadata
    
    @abstractmethod
    async def execute(self, **params) -> Dict[str, Any]:
        """Executa a habilidade com os parâmetros fornecidos"""
        pass
    
    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida os parâmetros recebidos"""
        required = self.metadata.parameters.get("required", [])
        
        for param in required:
            if param not in params:
                logger.warning(f"Parâmetro obrigatório faltando: {param}")
                return False
        
        return True


class WebSearchSkill(BaseSkill):
    """Habilidade de busca na web"""
    
    metadata = SkillMetadata(
        name="web_search",
        description="Busca informações na web. Útil para encontrar informações atuais, notícias, resultados de pesquisa, etc.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termo de busca"
                },
                "num_results": {
                    "type": "number",
                    "description": "Número de resultados (padrão: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        },
        category="information",
        examples=[
            "web_search(query='python async教程')",
            "web_search(query='latest AI news', num_results=10)"
        ]
    )
    
    def __init__(self):
        self.settings = get_settings()
    
    async def execute(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Executa busca na web via SearXNG"""
        try:
            import httpx
            
            # Busca no SearXNG local
            url = f"{self.settings.searxng_url}/search"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params={
                        "q": query,
                        "format": "json",
                        "engines": "google,duckduckgo,bing",
                        "num_results": num_results
                    }
                )
                
                data = response.json()
                
                results = []
                for item in data.get("results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", "")[:200],
                        "engine": item.get("engine", "")
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "num_results": len(results),
                    "results": results
                }
                
        except Exception as e:
            logger.error(f"Erro na busca web: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }


class FileOperationsSkill(BaseSkill):
    """Habilidade de operações de arquivo"""
    
    metadata = SkillMetadata(
        name="file_operations",
        description="Lê, escreve, lista ou manipula arquivos no sistema local.",
        parameters={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "list", "delete", "exists"],
                    "description": "Ação a ser executada"
                },
                "path": {
                    "type": "string",
                    "description": "Caminho do arquivo ou diretório"
                },
                "content": {
                    "type": "string",
                    "description": "Conteúdo para escrever (仅 para ação 'write')"
                }
            },
            "required": ["action", "path"]
        },
        category="filesystem",
        examples=[
            "file_operations(action='read', path='/home/user/document.txt')",
            "file_operations(action='write', path='/tmp/notes.txt', content='Olá mundo!')"
        ]
    )
    
    def __init__(self, base_path: str = "/app/data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def execute(
        self,
        action: str,
        path: str,
        content: str = None
    ) -> Dict[str, Any]:
        """Executa operação de arquivo"""
        try:
            file_path = self.base_path / path.lstrip("/")
            
            if action == "exists":
                return {
                    "success": True,
                    "exists": file_path.exists(),
                    "path": str(file_path)
                }
            
            elif action == "list":
                if not file_path.is_dir():
                    return {
                        "success": False,
                        "error": "Caminho não é um diretório"
                    }
                
                items = []
                for item in file_path.iterdir():
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None
                    })
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "items": items,
                    "count": len(items)
                }
            
            elif action == "read":
                if not file_path.exists():
                    return {
                        "success": False,
                        "error": "Arquivo não encontrado"
                    }
                
                content = file_path.read_text(encoding="utf-8")
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "content": content,
                    "size": len(content)
                }
            
            elif action == "write":
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content or "", encoding="utf-8")
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "bytes_written": len(content or "")
                }
            
            elif action == "delete":
                if not file_path.exists():
                    return {
                        "success": False,
                        "error": "Arquivo não encontrado"
                    }
                
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    import shutil
                    shutil.rmtree(file_path)
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "deleted": True
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Ação desconhecida: {action}"
                }
                
        except Exception as e:
            logger.error(f"Erro na operação de arquivo: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class CodeExecutionSkill(BaseSkill):
    """Habilidade de execução de código"""
    
    metadata = SkillMetadata(
        name="code_executor",
        description="Executa código Python ou Bash em ambiente sandbox. Útil para cálculos, automação, processamento de dados.",
        parameters={
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["python", "bash"],
                    "description": "Linguagem do código"
                },
                "code": {
                    "type": "string",
                    "description": "Código a ser executado"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout em segundos (padrão: 30)",
                    "default": 30
                }
            },
            "required": ["language", "code"]
        },
        category="execution",
        examples=[
            "code_executor(language='python', code='print(2+2)')",
            "code_executor(language='bash', code='ls -la')"
        ]
    )
    
    def __init__(self):
        self.settings = get_settings()
    
    async def execute(
        self,
        language: str,
        code: str,
        timeout: int = None
    ) -> Dict[str, Any]:
        """Executa código em sandbox"""
        timeout = timeout or self.settings.sandbox_execution_timeout
        
        try:
            if language == "python":
                return await self._execute_python(code, timeout)
            elif language == "bash":
                return await self._execute_bash(code, timeout)
            else:
                return {
                    "success": False,
                    "error": f"Linguagem não suportada: {language}"
                }
                
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Execução atingiu timeout de {timeout}s"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_python(self, code: str, timeout: int) -> Dict[str, Any]:
        """Executa código Python"""
        import io
        import sys
        import contextlib
        
        stdout = io.StringIO()
        stderr = io.StringIO()
        
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                # Executa o código
                exec_globals = {}
                exec(code, exec_globals)
                
                return {
                    "success": True,
                    "language": "python",
                    "stdout": stdout.getvalue(),
                    "stderr": stderr.getvalue(),
                    "output": exec_globals.get("_", stdout.getvalue())
                }
            except Exception as e:
                return {
                    "success": False,
                    "language": "python",
                    "error": str(e),
                    "stderr": stderr.getvalue()
                }
    
    async def _execute_bash(self, code: str, timeout: int) -> Dict[str, Any]:
        """Executa comando Bash"""
        process = await asyncio.create_subprocess_shell(
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "language": "bash",
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8")
            }
        except asyncio.TimeoutError:
            process.kill()
            raise


class CalculatorSkill(BaseSkill):
    """Habilidade de calculadora"""
    
    metadata = SkillMetadata(
        name="calculator",
        description="Realiza cálculos matemáticos. Suporta operações básicas, científicas e expressões.",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Expressão matemática a ser calculada"
                }
            },
            "required": ["expression"]
        },
        category="utilities",
        examples=[
            "calculator(expression='2+2*3')",
            "calculator(expression='sqrt(16) + log(10)')"
        ]
    )
    
    async def execute(self, expression: str) -> Dict[str, Any]:
        """Executa cálculo matemático"""
        try:
            # Avalia expressão de forma segura
            import ast
            import math
            
            # Mapeia funções disponíveis
            allowed_names = {
                "abs": abs,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
                "sum": sum,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
            }
            
            # Parse e avaliação segura
            tree = ast.parse(expression, mode="eval")
            
            def safe_eval(node):
                if isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.Name):
                    if node.id in allowed_names:
                        return allowed_names[node.id]
                    raise NameError(f"Nome não permitido: {node.id}")
                elif isinstance(node, ast.BinOp):
                    left = safe_eval(node.left)
                    right = safe_eval(node.right)
                    if isinstance(node.op, ast.Add):
                        return left + right
                    elif isinstance(node.op, ast.Sub):
                        return left - right
                    elif isinstance(node.op, ast.Mult):
                        return left * right
                    elif isinstance(node.op, ast.Div):
                        return left / right
                    elif isinstance(node.op, ast.Pow):
                        return left ** right
                    elif isinstance(node.op, ast.Mod):
                        return left % right
                elif isinstance(node, ast.UnaryOp):
                    if isinstance(node.op, ast.USub):
                        return -safe_eval(node.operand)
                    elif isinstance(node.op, ast.UAdd):
                        return +safe_eval(node.operand)
                elif isinstance(node, ast.Call):
                    func = safe_eval(node.func)
                    args = [safe_eval(arg) for arg in node.args]
                    return func(*args)
                
                raise ValueError(f"Expressão inválida: {expression}")
            
            result = safe_eval(tree.body)
            
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }


# Registro centralizado de habilidades
SKILLS_REGISTRY: Dict[str, Callable] = {}


def register_skill(skill_class: type):
    """Decorator para registrar uma habilidade"""
    skill_instance = skill_class()
    SKILLS_REGISTRY[skill_instance.metadata.name] = skill_instance.execute
    logger.info(f"Habilidade registrada: {skill_instance.metadata.name}")
    return skill_class


def get_skills_registry() -> Dict[str, Callable]:
    """Retorna o registro de habilidades"""
    return SKILLS_REGISTRY


def load_skills_from_directory(directory: str = "/app/skills"):
    """Carrega habilidades de um diretório"""
    skills_path = Path(directory)
    
    if not skills_path.exists():
        logger.warning(f"Diretório de habilidades não existe: {directory}")
        return
    
    # Carrega habilidadesbuilt-in
    from skills import builtins
    builtins.register_all_skills()
    
    logger.info(f"Habilidades carregadas de {directory}")
