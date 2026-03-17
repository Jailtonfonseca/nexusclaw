"""NexusClaw - Módulo Core"""

from core.agent import NexusAgent, Message, ConversationContext, LLMWrapper
from core.memory import MemorySystem, MemoryEntry, VectorStore
from core.self_improvement import SelfImprovementEngine, EvolutionEngine
from core.code_evolution import CodeEvolutionSystem, CodeAnalyzer, FeatureSuggester
from core.deep_thinking import (
    DeepThinkingAgent,
    ChainOfThought,
    SelfReflector,
    AutonomousPlanner,
    ReasoningDepth,
    ThoughtType
)

__all__ = [
    "NexusAgent",
    "Message",
    "ConversationContext",
    "LLMWrapper",
    "MemorySystem",
    "MemoryEntry",
    "VectorStore",
    "SelfImprovementEngine",
    "EvolutionEngine",
    "CodeEvolutionSystem",
    "CodeAnalyzer",
    "FeatureSuggester",
    "DeepThinkingAgent",
    "ChainOfThought",
    "SelfReflector",
    "AutonomousPlanner",
    "ReasoningDepth",
    "ThoughtType"
]
