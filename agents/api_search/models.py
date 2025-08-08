"""
Data models for the optimized API search system
Defines compressed API structures and search result formats
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import time

# ================= Core API Models =================

class APICategory(str, Enum):
    """Blender API categories"""
    MESH_OPERATORS = "mesh_operators"
    OBJECT_OPERATORS = "object_operators"
    GEOMETRY_NODES = "geometry_nodes"
    SHADER_NODES = "shader_nodes"
    MATERIAL_OPERATORS = "material_operators"
    ANIMATION_OPERATORS = "animation_operators"
    SCENE_OPERATORS = "scene_operators"
    UNKNOWN = "unknown"

class CompressedAPI(BaseModel):
    """
    Memory-efficient API representation
    Reduced from full JSON to essential fields only
    """
    id: str = Field(..., description="Unique API identifier")
    name: str = Field(..., description="Full API name (e.g., bpy.ops.mesh.bevel)")
    category: APICategory = Field(..., description="API category")
    description: str = Field("", description="Brief description (max 200 chars)")
    
    # Essential metadata
    parameters: List[str] = Field(default_factory=list, description="Parameter names only")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    complexity: str = Field("moderate", description="API complexity level")
    
    # Search optimization fields
    search_keywords: List[str] = Field(default_factory=list, description="Extracted search keywords")
    common_use_cases: List[str] = Field(default_factory=list, description="Common usage scenarios")
    
    # Performance metadata
    embedding_id: Optional[int] = Field(None, description="Reference to embedding vector")
    popularity_score: float = Field(0.0, description="Usage popularity (0-1)")

class APISearchResult(BaseModel):
    """
    Search result with relevance scoring
    """
    api: CompressedAPI = Field(..., description="The matched API")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    match_type: str = Field(..., description="Type of match (exact, fuzzy, semantic)")
    match_details: Dict[str, Any] = Field(default_factory=dict, description="Details about the match")
    confidence: float = Field(0.0, description="Confidence in the match (0-1)")
    
    # Context information
    matched_terms: List[str] = Field(default_factory=list, description="Terms that matched")
    suggested_parameters: Dict[str, Any] = Field(default_factory=dict, description="Suggested parameter values")

# ================= Search Context Models =================

class SearchContext(BaseModel):
    """
    Context information for API search
    """
    # Subtask context
    task_type: str = Field(..., description="Type of task being performed")
    task_description: str = Field("", description="Description of the task")
    
    # Filtering preferences
    preferred_categories: List[APICategory] = Field(default_factory=list, description="Preferred API categories")
    excluded_categories: List[APICategory] = Field(default_factory=list, description="Categories to exclude")
    
    # Search parameters
    max_results: int = Field(10, description="Maximum number of results to return")
    min_relevance: float = Field(0.3, description="Minimum relevance score threshold")
    include_alternatives: bool = Field(True, description="Include alternative suggestions")
    
    # Performance hints
    prefer_fast_search: bool = Field(False, description="Prefer speed over accuracy")
    enable_semantic_search: bool = Field(True, description="Enable semantic similarity search")

class SearchStrategy(str, Enum):
    """
    Search strategy types
    """
    EXACT_MATCH = "exact_match"           # O(1) hash lookup
    CATEGORY_FILTERED = "category_filtered" # Pre-filtered by category
    FUZZY_MATCH = "fuzzy_match"           # String similarity
    SEMANTIC_SEARCH = "semantic_search"   # Vector similarity
    HYBRID = "hybrid"                     # Combined approach
    FALLBACK = "fallback"                 # Last resort

# ================= Performance Models =================

class SearchMetrics(BaseModel):
    """
    Performance metrics for search operations
    """
    query: str = Field(..., description="Original search query")
    strategy_used: SearchStrategy = Field(..., description="Search strategy employed")
    
    # Timing metrics
    total_time_ms: float = Field(0.0, description="Total search time in milliseconds")
    index_lookup_time_ms: float = Field(0.0, description="Time for index lookups")
    scoring_time_ms: float = Field(0.0, description="Time for relevance scoring")
    
    # Result metrics
    total_candidates: int = Field(0, description="Total candidates considered")
    filtered_candidates: int = Field(0, description="Candidates after filtering")
    final_results: int = Field(0, description="Final results returned")
    
    # Cache metrics
    cache_hit: bool = Field(False, description="Whether result was cached")
    cache_key: Optional[str] = Field(None, description="Cache key used")
    
    # Quality metrics
    avg_relevance_score: float = Field(0.0, description="Average relevance of results")
    confidence_score: float = Field(0.0, description="Overall confidence in results")
    
    def __str__(self) -> str:
        return f"SearchMetrics(query='{self.query}', time={self.total_time_ms:.2f}ms, results={self.final_results})"

# ================= Index Models =================

class IndexStats(BaseModel):
    """
    Statistics for search indices
    """
    index_name: str = Field(..., description="Name of the index")
    total_entries: int = Field(0, description="Total entries in index")
    memory_usage_mb: float = Field(0.0, description="Memory usage in MB")
    last_updated: float = Field(default_factory=time.time, description="Last update timestamp")
    
    # Performance stats
    total_lookups: int = Field(0, description="Total lookups performed")
    cache_hits: int = Field(0, description="Number of cache hits")
    avg_lookup_time_ms: float = Field(0.0, description="Average lookup time")
    
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_lookups == 0:
            return 0.0
        return self.cache_hits / self.total_lookups

# ================= Configuration Models =================

class SearchConfig(BaseModel):
    """
    Configuration for the search system
    """
    # Performance settings
    enable_caching: bool = Field(True, description="Enable LRU caching")
    cache_size: int = Field(1000, description="Maximum cache entries")
    max_concurrent_searches: int = Field(10, description="Maximum concurrent searches")
    
    # Search thresholds
    exact_match_threshold: float = Field(1.0, description="Threshold for exact matches")
    fuzzy_match_threshold: float = Field(0.7, description="Threshold for fuzzy matches")
    semantic_match_threshold: float = Field(0.6, description="Threshold for semantic matches")
    
    # Index settings
    preload_indices: bool = Field(True, description="Preload all indices at startup")
    lazy_load_embeddings: bool = Field(True, description="Load embeddings on demand")
    compress_embeddings: bool = Field(True, description="Use compressed embeddings")
    
    # Memory management
    max_memory_usage_mb: int = Field(100, description="Maximum memory usage in MB")
    enable_memory_monitoring: bool = Field(True, description="Monitor memory usage")
    
    # Fallback settings
    enable_fallback_search: bool = Field(True, description="Enable fallback strategies")
    fallback_timeout_ms: int = Field(5000, description="Timeout for fallback searches")

# ================= Error Models =================

class SearchError(Exception):
    """
    Base exception for search errors
    """
    def __init__(self, message: str, error_code: str = "SEARCH_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class IndexNotFoundError(SearchError):
    """
    Raised when a required index is not found
    """
    def __init__(self, index_name: str):
        super().__init__(
            f"Index '{index_name}' not found",
            error_code="INDEX_NOT_FOUND",
            details={"index_name": index_name}
        )

class SearchTimeoutError(SearchError):
    """
    Raised when search operation times out
    """
    def __init__(self, timeout_ms: int):
        super().__init__(
            f"Search operation timed out after {timeout_ms}ms",
            error_code="SEARCH_TIMEOUT",
            details={"timeout_ms": timeout_ms}
        )

# ================= Utility Functions =================

def create_search_context(
    task_type: str,
    task_description: str = "",
    max_results: int = 10,
    preferred_categories: Optional[List[str]] = None
) -> SearchContext:
    """
    Convenience function to create search context
    """
    categories = []
    if preferred_categories:
        for cat in preferred_categories:
            try:
                categories.append(APICategory(cat))
            except ValueError:
                # Skip invalid categories
                continue
    
    return SearchContext(
        task_type=task_type,
        task_description=task_description,
        max_results=max_results,
        preferred_categories=categories
    )

def normalize_api_name(api_name: str) -> str:
    """
    Normalize API name for consistent indexing
    """
    return api_name.lower().strip()

def extract_keywords_from_description(description: str) -> List[str]:
    """
    Extract searchable keywords from API description
    """
    import re
    
    # Remove common stop words and extract meaningful terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    # Extract words (alphanumeric sequences)
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', description.lower())
    
    # Filter out stop words and short words
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords[:10]  # Limit to top 10 keywords
