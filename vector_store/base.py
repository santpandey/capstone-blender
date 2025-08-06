"""
Base interface for vector database implementations
Provides unified API for FAISS and Qdrant backends
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import time

class VectorBackend(Enum):
    FAISS = "faiss"
    QDRANT = "qdrant"

@dataclass
class SearchResult:
    """Unified search result format"""
    id: str
    score: float
    metadata: Dict[str, Any]
    content: str
    api_name: str
    category: str
    parameters: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'score': self.score,
            'metadata': self.metadata,
            'content': self.content,
            'api_name': self.api_name,
            'category': self.category,
            'parameters': self.parameters
        }

@dataclass
class IndexStats:
    """Vector index statistics"""
    total_vectors: int
    index_size_mb: float
    last_updated: float
    backend: VectorBackend
    
class VectorStore(ABC):
    """Abstract base class for vector database implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backend = VectorBackend(config.get('backend', 'faiss'))
        self._stats = IndexStats(0, 0.0, time.time(), self.backend)
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the vector store"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store"""
        pass
    
    @abstractmethod
    async def search(self, 
                    query: str, 
                    top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    async def hybrid_search(self,
                           query: str,
                           semantic_weight: float = 0.7,
                           fuzzy_weight: float = 0.3,
                           top_k: int = 5,
                           filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Perform hybrid search (semantic + fuzzy matching)"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> IndexStats:
        """Get index statistics"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check vector store health"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close connections and cleanup"""
        pass
    
    # Common utility methods
    def _normalize_score(self, score: float, backend: VectorBackend) -> float:
        """Normalize scores across different backends"""
        if backend == VectorBackend.FAISS:
            # FAISS uses cosine similarity (higher is better)
            return max(0.0, min(1.0, score))
        elif backend == VectorBackend.QDRANT:
            # Qdrant uses distance (lower is better), convert to similarity
            return max(0.0, min(1.0, 1.0 - score))
        return score
    
    def _extract_api_info(self, metadata: Dict[str, Any]) -> tuple:
        """Extract API information from metadata"""
        api_name = metadata.get('full_name', '')
        category = metadata.get('category', 'unknown')
        parameters = metadata.get('parameters', [])
        return api_name, category, parameters
