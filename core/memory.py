"""
NexusClaw - Sistema de Memória
=============================

Este módulo implementa o sistema de memória do assistente,
incluindo memória episódica, memória de fatos e contexto.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


from config.settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Uma entrada de memória"""
    id: str
    content: str
    memory_type: str  # "episodic", "fact", "context"
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    importance: float = 1.0


class VectorStore:
    """Interface com banco de vetores (Qdrant)"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.embedding_model = None
        self._initialized = False
    
    async def initialize(self):
        """Inicializa a conexão com Qdrant e modelo de embedding"""
        if self._initialized:
            return
        
        try:
            from qdrant_client import QdrantClient
            from sentence_transformers import SentenceTransformer
            
            # Conecta ao Qdrant
            self.client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port
            )
            
            # Carrega modelo de embedding
            self.embedding_model = SentenceTransformer(
                self.settings.embedding_model,
                device=self.settings.embedding_device
            )
            
            # Cria coleção se não existir
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.settings.qdrant_collection not in collection_names:
                self.client.create_collection(
                    collection_name=self.settings.qdrant_collection,
                    vectors_config={
                        "size": self.embedding_model.get_sentence_embedding_dimension(),
                        "distance": "Cosine"
                    }
                )
                logger.info(f"Criada coleção: {self.settings.qdrant_collection}")
            
            self._initialized = True
            logger.info("VectorStore inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar VectorStore: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Gera embedding para um texto"""
        if not self._initialized:
            await self.initialize()
        
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    async def add_memory(
        self,
        memory: MemoryEntry,
        vector: List[float] = None
    ):
        """Adiciona uma memória ao banco de vetores"""
        if not self._initialized:
            await self.initialize()
        
        if vector is None:
            vector = await self.embed_text(memory.content)
        
        self.client.upsert(
            collection_name=self.settings.qdrant_collection,
            points=[
                {
                    "id": memory.id,
                    "vector": vector,
                    "payload": {
                        "content": memory.content,
                        "memory_type": memory.memory_type,
                        "metadata": json.dumps(memory.metadata),
                        "created_at": memory.created_at.isoformat(),
                        "importance": memory.importance
                    }
                }
            ]
        )
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        memory_type: str = None
    ) -> List[Dict[str, Any]]:
        """Busca memórias similares a uma query"""
        if not self._initialized:
            await self.initialize()
        
        query_vector = await self.embed_text(query)
        
        filter_condition = None
        if memory_type:
            filter_condition = {
                "must": [
                    {
                        "key": "memory_type",
                        "match": {"value": memory_type}
                    }
                ]
            }
        
        results = self.client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_condition
        )
        
        return [
            {
                "id": r.id,
                "content": r.payload["content"],
                "memory_type": r.payload["memory_type"],
                "metadata": json.loads(r.payload["metadata"]),
                "score": r.score,
                "created_at": r.payload["created_at"]
            }
            for r in results
        ]
    
    async def delete_memory(self, memory_id: str):
        """Deleta uma memória"""
        if not self._initialized:
            await self.initialize()
        
        self.client.delete(
            collection_name=self.settings.qdrant_collection,
            points_selector=[memory_id]
        )


class MemorySystem:
    """
    Sistema completo de memória do NexusClaw.
    Gerencia memória episódica, de fatos e contexto.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_store = VectorStore()
        self.short_term_cache = {}  # Redis-like em memória
        self._initialized = False
    
    async def initialize(self):
        """Inicializa o sistema de memória"""
        if self._initialized:
            return
        
        await self.vector_store.initialize()
        self._initialized = True
        logger.info("Sistema de memória inicializado")
    
    async def add_episodic_memory(
        self,
        content: str,
        user_id: str,
        channel: str,
        importance: float = 1.0
    ):
        """Adiciona uma memória episódica (conversa/evento)"""
        memory = MemoryEntry(
            id=f"episodic_{datetime.now().timestamp()}",
            content=content,
            memory_type="episodic",
            metadata={
                "user_id": user_id,
                "channel": channel
            },
            importance=importance
        )
        
        await self.vector_store.add_memory(memory)
        logger.info(f"Memória episódica adicionada: {memory.id}")
    
    async def add_fact(
        self,
        fact: str,
        entity_type: str = "general",
        user_id: str = "global"
    ):
        """Adiciona um fato conhecido"""
        memory = MemoryEntry(
            id=f"fact_{datetime.now().timestamp()}",
            content=fact,
            memory_type="fact",
            metadata={
                "entity_type": entity_type,
                "user_id": user_id
            },
            importance=1.0
        )
        
        await self.vector_store.add_memory(memory)
        logger.info(f"Fato adicionado: {memory.id}")
    
    async def search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca em todas as memórias"""
        if memory_types is None:
            memory_types = ["episodic", "fact"]
        
        results = []
        for mem_type in memory_types:
            type_results = await self.vector_store.search(
                query=query,
                limit=limit,
                memory_type=mem_type
            )
            results.extend(type_results)
        
        # Ordena por relevância
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:limit]
    
    async def get_context_for_conversation(
        self,
        user_id: str,
        channel: str,
        current_message: str
    ) -> str:
        """
        Obtém contexto relevante para a conversa atual.
        Busca memórias relacionadas e constrói um contexto.
        """
        # Busca memórias episódicas relacionadas
        episodic_results = await self.vector_store.search(
            query=current_message,
            limit=3,
            memory_type="episodic"
        )
        
        # Busca fatos relevantes
        fact_results = await self.vector_store.search(
            query=current_message,
            limit=3,
            memory_type="fact"
        )
        
        context_parts = []
        
        if episodic_results:
            context_parts.append("=== Memórias de conversas passadas ===")
            for r in episodic_results:
                if r["score"] > 0.7:  # Só inclui se muito relevante
                    context_parts.append(f"- {r['content']}")
        
        if fact_results:
            context_parts.append("\n=== Informações que você sabe ===")
            for r in fact_results:
                if r["score"] > 0.8:
                    context_parts.append(f"- {r['content']}")
        
        if context_parts:
            return "\n".join(context_parts)
        
        return ""
    
    async def extract_and_save_facts(
        self,
        conversation: List[Dict[str, str]],
        user_id: str
    ):
        """
        Analisa uma conversa e extrai fatos importantes para salvar.
        """
        # Constrói texto da conversa
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation
        ])
        
        # Prompt para extrair fatos
        extraction_prompt = f"""
Analise a seguinte conversa e extraia fatos importantes que devem ser lembrados.
Retorne apenas os fatos em formato JSON array, sem outras explicações.

Exemplo de formato:
[{{"fact": "O usuário gosta de café sem açúcar", "type": "preference"}}, ...]

Conversa:
{conversation_text}
"""
        
        # Usa o LLM para extrair fatos
        from core.agent import LLMWrapper
        
        llm = LLMWrapper()
        try:
            response = await llm.generate(
                prompt=extraction_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse dos fatos
            facts_text = response.get("content", "[]")
            
            # Limpa markdown se presente
            if "```json" in facts_text:
                facts_text = facts_text.split("```json")[1].split("```")[0]
            elif "```" in facts_text:
                facts_text = facts_text.split("```")[1].split("```")[0]
            
            facts = json.loads(facts_text)
            
            # Salva cada fato
            for fact_data in facts:
                await self.add_fact(
                    fact=fact_data.get("fact", ""),
                    entity_type=fact_data.get("type", "general"),
                    user_id=user_id
                )
            
            logger.info(f"Extraídos {len(facts)} fatos da conversa")
            
        except Exception as e:
            logger.error(f"Erro ao extrair fatos: {e}")
    
    async def save_conversation_turn(
        self,
        user_id: str,
        channel: str,
        user_message: str,
        assistant_message: str
    ):
        """Salva um turno de conversa como memória episódica"""
        content = f"Usuário: {user_message}\nAssistente: {assistant_message}"
        
        await self.add_episodic_memory(
            content=content,
            user_id=user_id,
            channel=channel,
            importance=0.8
        )
    
    async def clear_user_memories(self, user_id: str):
        """Limpa todas as memórias de um usuário (GDPR)"""
        # Implementação simplificada - em produção seria mais sofisticado
        logger.info(f"Limpeza de memórias solicitada para usuário: {user_id}")
