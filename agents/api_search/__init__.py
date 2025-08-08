"""
Optimized API Search System for Coordinator Agent
High-performance search through Blender API registry
"""

from .models import (
    CompressedAPI,
    APISearchResult,
    SearchContext,
    SearchStrategy,
    SearchMetrics,
    APICategory,
    SearchConfig,
    create_search_context
)
from .registry_loader import APIRegistryLoader
from .search_engine import OptimizedAPISearcher
from .indices import (
    ExactMatchIndex,
    CategoryIndex,
    KeywordIndex,
    FuzzyMatchIndex
)

__all__ = [
    'CompressedAPI',
    'APISearchResult', 
    'SearchContext',
    'SearchStrategy',
    'SearchMetrics',
    'APICategory',
    'SearchConfig',
    'create_search_context',
    'APIRegistryLoader',
    'OptimizedAPISearcher',
    'ExactMatchIndex',
    'CategoryIndex',
    'KeywordIndex',
    'FuzzyMatchIndex'
]
