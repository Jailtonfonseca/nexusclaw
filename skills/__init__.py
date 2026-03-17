"""NexusClaw - Módulo de Habilidades"""

from skills.base import (
    BaseSkill,
    SkillMetadata,
    register_skill,
    get_skills_registry,
    load_skills_from_directory,
    WebSearchSkill,
    FileOperationsSkill,
    CodeExecutionSkill,
    CalculatorSkill
)

__all__ = [
    "BaseSkill",
    "SkillMetadata",
    "register_skill",
    "get_skills_registry",
    "load_skills_from_directory",
    "WebSearchSkill",
    "FileOperationsSkill", 
    "CodeExecutionSkill",
    "CalculatorSkill"
]
