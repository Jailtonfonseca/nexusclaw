"""
NexusClaw - Habilidades Built-in
================================

Este módulo registra todas as habilidades padrão
do NexusClaw.
"""

import logging

from skills.base import (
    register_skill,
    WebSearchSkill,
    FileOperationsSkill,
    CodeExecutionSkill,
    CalculatorSkill
)


logger = logging.getLogger(__name__)


def register_all_skills():
    """Registra todas as habilidades built-in"""
    
    # Registra cada habilidade
    register_skill(WebSearchSkill)
    logger.info("Habilidade WebSearch registrada")
    
    register_skill(FileOperationsSkill)
    logger.info("Habilidade FileOperations registrada")
    
    register_skill(CodeExecutionSkill)
    logger.info("Habilidade CodeExecution registrada")
    
    register_skill(CalculatorSkill)
    logger.info("Habilidade Calculator registrada")
    
    logger.info("Todas as habilidades built-in registradas com sucesso")
