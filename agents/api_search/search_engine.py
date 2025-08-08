"""
Main search engine that orchestrates all indices for optimal API search
Implements the hybrid search pipeline with intelligent fallbacks
"""

import time
import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from .models import (
    CompressedAPI, 
    APISearchResult, 
    SearchContext, 
    SearchStrategy, 
    SearchMetrics,
    SearchConfig,
    SearchError,
    APICategory
)
from .registry_loader import APIRegistryLoader
from .indices import CompositeIndex

class OptimizedAPISearcher:
    """
    High-performance API search engine with hybrid search strategies
    """
    
    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.registry_loader = APIRegistryLoader()
        self.indices = CompositeIndex()
        
        # Performance tracking
        self.search_metrics: List[SearchMetrics] = []
        self.total_searches = 0
        self.cache_hits = 0
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_searches)
        
        # Initialization state
        self._initialized = False
        self._initialization_error: Optional[str] = None
    
    async def initialize(self, force_reload: bool = False) -> bool:
        """
        Initialize the search engine
        
        Args:
            force_reload: Force reload of registry data
            
        Returns:
            True if initialization successful
        """
        if self._initialized and not force_reload:
            return True
        
        start_time = time.time()
        
        try:
            self.logger.info("Initializing API search engine...")
            
            # Load API registry
            apis = await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self.registry_loader.load_registry,
                force_reload
            )
            
            # Validate loaded data
            if not self.registry_loader.validate_loaded_data():
                raise SearchError("Registry data validation failed")
            
            # Build all indices
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.indices.build_all_indices,
                apis
            )
            
            # Verify indices are ready
            if not self.indices.is_ready():
                raise SearchError("Failed to build search indices")
            
            self._initialized = True
            self._initialization_error = None
            
            init_time = (time.time() - start_time) * 1000
            memory_usage = self.indices.get_memory_usage()
            
            self.logger.info(
                f"Search engine initialized successfully in {init_time:.2f}ms, "
                f"memory usage: {memory_usage:.2f}MB"
            )
            
            return True
            
        except Exception as e:
            self._initialization_error = str(e)
            self.logger.error(f"Failed to initialize search engine: {e}")
            return False
    
    async def search(
        self, 
        query: str, 
        context: Optional[SearchContext] = None
    ) -> List[APISearchResult]:
        """
        Main search method with hybrid strategy
        
        Args:
            query: Search query
            context: Search context for filtering and preferences
            
        Returns:
            List of search results sorted by relevance
        """
        if not self._initialized:
            if not await self.initialize():
                raise SearchError(f"Search engine not initialized: {self._initialization_error}")
        
        # Use default context if none provided
        if context is None:
            context = SearchContext(task_type="general")
        
        start_time = time.time()
        self.total_searches += 1
        
        try:
            # Determine optimal search strategy
            strategy = self._determine_search_strategy(query, context)
            
            # Execute search with chosen strategy
            results = await self._execute_search_strategy(query, context, strategy)
            
            # Post-process and rank results
            final_results = self._post_process_results(results, query, context)
            
            # Record metrics
            search_time = (time.time() - start_time) * 1000
            metrics = self._create_search_metrics(query, strategy, search_time, final_results)
            self.search_metrics.append(metrics)
            
            # Limit metrics history
            if len(self.search_metrics) > 1000:
                self.search_metrics = self.search_metrics[-500:]
            
            self.logger.debug(f"Search completed: {metrics}")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            raise SearchError(f"Search failed: {str(e)}")
    
    def _determine_search_strategy(self, query: str, context: SearchContext) -> SearchStrategy:
        """
        Intelligently determine the best search strategy
        
        Args:
            query: Search query
            context: Search context
            
        Returns:
            Optimal search strategy
        """
        query_lower = query.lower().strip()
        
        # Fast path for exact API names
        if query_lower.startswith("bpy.ops.") and "." in query_lower[8:]:
            return SearchStrategy.EXACT_MATCH
        
        # Category-filtered search if category preferences specified
        if context.preferred_categories and len(context.preferred_categories) <= 2:
            return SearchStrategy.CATEGORY_FILTERED
        
        # Prefer fast search if requested
        if context.prefer_fast_search:
            return SearchStrategy.FUZZY_MATCH
        
        # Short queries often benefit from fuzzy matching
        if len(query.split()) <= 2:
            return SearchStrategy.FUZZY_MATCH
        
        # Default to hybrid for complex queries
        return SearchStrategy.HYBRID
    
    async def _execute_search_strategy(
        self, 
        query: str, 
        context: SearchContext, 
        strategy: SearchStrategy
    ) -> List[Tuple[CompressedAPI, float, str]]:
        """
        Execute search with the specified strategy
        
        Returns:
            List of (API, score, match_type) tuples
        """
        if strategy == SearchStrategy.EXACT_MATCH:
            return await self._search_exact(query)
        elif strategy == SearchStrategy.CATEGORY_FILTERED:
            return await self._search_category_filtered(query, context)
        elif strategy == SearchStrategy.FUZZY_MATCH:
            return await self._search_fuzzy(query, context)
        elif strategy == SearchStrategy.SEMANTIC_SEARCH:
            return await self._search_semantic(query, context)
        elif strategy == SearchStrategy.HYBRID:
            return await self._search_hybrid(query, context)
        else:
            return await self._search_fallback(query, context)
    
    async def _search_exact(self, query: str) -> List[Tuple[CompressedAPI, float, str]]:
        """Exact match search"""
        result = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.indices.exact_index.search,
            query
        )
        
        if result:
            return [(result, 1.0, "exact")]
        return []
    
    async def _search_category_filtered(
        self, 
        query: str, 
        context: SearchContext
    ) -> List[Tuple[CompressedAPI, float, str]]:
        """Category-filtered search"""
        results = []
        
        # Get APIs from preferred categories
        for category in context.preferred_categories:
            category_apis = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.indices.category_index.get_apis_by_category,
                category,
                context.max_results
            )
            
            # Score each API against the query
            for api in category_apis:
                score = self._calculate_relevance_score(query, api)
                if score >= context.min_relevance:
                    results.append((api, score, "category_filtered"))
        
        return results
    
    async def _search_fuzzy(
        self, 
        query: str, 
        context: SearchContext
    ) -> List[Tuple[CompressedAPI, float, str]]:
        """Fuzzy string matching search"""
        fuzzy_results = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.indices.fuzzy_index.search_fuzzy,
            query,
            context.max_results * 2
        )
        
        results = []
        for api, score in fuzzy_results:
            if score >= context.min_relevance:
                results.append((api, score, "fuzzy"))
        
        return results
    
    async def _search_semantic(
        self, 
        query: str, 
        context: SearchContext
    ) -> List[Tuple[CompressedAPI, float, str]]:
        """Semantic search using keywords"""
        # Extract keywords from query
        keywords = query.lower().split()
        
        keyword_results = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.indices.keyword_index.search_by_keywords,
            keywords,
            context.max_results * 2
        )
        
        results = []
        for api, score in keyword_results:
            # Normalize score to 0-1 range
            normalized_score = min(score / len(keywords), 1.0)
            if normalized_score >= context.min_relevance:
                results.append((api, normalized_score, "semantic"))
        
        return results
    
    async def _search_hybrid(
        self, 
        query: str, 
        context: SearchContext
    ) -> List[Tuple[CompressedAPI, float, str]]:
        """Hybrid search combining multiple strategies"""
        # Run multiple search strategies concurrently
        tasks = [
            self._search_exact(query),
            self._search_fuzzy(query, context),
            self._search_semantic(query, context)
        ]
        
        # Add category search if preferences specified
        if context.preferred_categories:
            tasks.append(self._search_category_filtered(query, context))
        
        # Execute all searches concurrently
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results from all strategies
        combined_results = []
        strategy_weights = {
            "exact": 1.0,
            "fuzzy": 0.8,
            "semantic": 0.7,
            "category_filtered": 0.9
        }
        
        for result_set in all_results:
            if isinstance(result_set, Exception):
                self.logger.warning(f"Search strategy failed: {result_set}")
                continue
            
            for api, score, match_type in result_set:
                # Apply strategy weight
                weighted_score = score * strategy_weights.get(match_type, 0.5)
                combined_results.append((api, weighted_score, match_type))
        
        return combined_results
    
    async def _search_fallback(
        self, 
        query: str, 
        context: SearchContext
    ) -> List[Tuple[CompressedAPI, float, str]]:
        """Fallback search when other strategies fail"""
        # Simple keyword-based fallback
        keywords = [word for word in query.lower().split() if len(word) > 2]
        
        if not keywords:
            # Return popular APIs if no meaningful keywords
            popular_apis = []
            for category in APICategory:
                if category != APICategory.UNKNOWN:
                    category_apis = self.indices.category_index.get_apis_by_category(category, 5)
                    popular_apis.extend(category_apis)
            
            # Sort by popularity and return top results
            popular_apis.sort(key=lambda x: x.popularity_score, reverse=True)
            return [(api, 0.3, "fallback") for api in popular_apis[:context.max_results]]
        
        # Try keyword search as fallback
        return await self._search_semantic(query, context)
    
    def _calculate_relevance_score(self, query: str, api: CompressedAPI) -> float:
        """
        Calculate relevance score between query and API
        
        Args:
            query: Search query
            api: API to score
            
        Returns:
            Relevance score (0-1)
        """
        query_lower = query.lower()
        score = 0.0
        
        # Exact name match gets highest score
        if query_lower == api.name.lower():
            return 1.0
        
        # Partial name match
        if query_lower in api.name.lower():
            score += 0.8
        
        # Description match
        if query_lower in api.description.lower():
            score += 0.6
        
        # Keyword matches
        query_words = set(query_lower.split())
        api_keywords = set(keyword.lower() for keyword in api.search_keywords)
        
        if query_words & api_keywords:  # Intersection
            overlap_ratio = len(query_words & api_keywords) / len(query_words)
            score += 0.7 * overlap_ratio
        
        # Use case matches
        for use_case in api.common_use_cases:
            if query_lower in use_case.lower():
                score += 0.5
                break
        
        # Boost with popularity
        score *= (1 + api.popularity_score * 0.2)
        
        return min(score, 1.0)
    
    def _post_process_results(
        self, 
        results: List[Tuple[CompressedAPI, float, str]], 
        query: str, 
        context: SearchContext
    ) -> List[APISearchResult]:
        """
        Post-process and rank search results
        
        Args:
            results: Raw search results
            query: Original query
            context: Search context
            
        Returns:
            Processed and ranked results
        """
        # Remove duplicates (same API from different strategies)
        seen_apis = {}
        for api, score, match_type in results:
            if api.id not in seen_apis or seen_apis[api.id][1] < score:
                seen_apis[api.id] = (api, score, match_type)
        
        # Convert to APISearchResult objects
        search_results = []
        for api, score, match_type in seen_apis.values():
            # Calculate confidence based on score and match type
            confidence = self._calculate_confidence(score, match_type)
            
            # Create match details
            match_details = {
                "match_type": match_type,
                "original_score": score,
                "query_length": len(query.split()),
                "api_popularity": api.popularity_score
            }
            
            # Generate suggested parameters (placeholder for now)
            suggested_parameters = self._suggest_parameters(api, query, context)
            
            result = APISearchResult(
                api=api,
                relevance_score=score,
                match_type=match_type,
                match_details=match_details,
                confidence=confidence,
                matched_terms=self._extract_matched_terms(query, api),
                suggested_parameters=suggested_parameters
            )
            
            search_results.append(result)
        
        # Sort by relevance score (descending)
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Apply context filters
        filtered_results = self._apply_context_filters(search_results, context)
        
        # Limit to max results
        return filtered_results[:context.max_results]
    
    def _calculate_confidence(self, score: float, match_type: str) -> float:
        """Calculate confidence score based on relevance and match type"""
        base_confidence = score
        
        # Adjust based on match type
        type_multipliers = {
            "exact": 1.0,
            "category_filtered": 0.9,
            "fuzzy": 0.8,
            "semantic": 0.7,
            "fallback": 0.5
        }
        
        multiplier = type_multipliers.get(match_type, 0.6)
        return min(base_confidence * multiplier, 1.0)
    
    def _suggest_parameters(
        self, 
        api: CompressedAPI, 
        query: str, 
        context: SearchContext
    ) -> Dict[str, Any]:
        """Generate suggested parameter values for the API"""
        # This is a placeholder - could be enhanced with ML or heuristics
        suggestions = {}
        
        # Basic parameter suggestions based on common patterns
        if "scale" in api.name.lower() and "size" in query.lower():
            suggestions["factor"] = 1.0
        elif "rotate" in api.name.lower() and any(word in query.lower() for word in ["angle", "degree"]):
            suggestions["angle"] = 90.0
        elif "extrude" in api.name.lower():
            suggestions["value"] = 1.0
        
        return suggestions
    
    def _extract_matched_terms(self, query: str, api: CompressedAPI) -> List[str]:
        """Extract terms that matched between query and API"""
        query_words = set(query.lower().split())
        matched_terms = []
        
        # Check against API keywords
        for keyword in api.search_keywords:
            if keyword.lower() in query_words:
                matched_terms.append(keyword)
        
        # Check against use cases
        for use_case in api.common_use_cases:
            use_case_words = set(use_case.lower().split())
            if query_words & use_case_words:
                matched_terms.append(use_case)
        
        return matched_terms
    
    def _apply_context_filters(
        self, 
        results: List[APISearchResult], 
        context: SearchContext
    ) -> List[APISearchResult]:
        """Apply context-based filtering to results"""
        filtered = []
        
        for result in results:
            # Filter by minimum relevance
            if result.relevance_score < context.min_relevance:
                continue
            
            # Filter by excluded categories
            if result.api.category in context.excluded_categories:
                continue
            
            # Boost preferred categories
            if result.api.category in context.preferred_categories:
                result.relevance_score *= 1.2
                result.relevance_score = min(result.relevance_score, 1.0)
            
            filtered.append(result)
        
        return filtered
    
    def _create_search_metrics(
        self, 
        query: str, 
        strategy: SearchStrategy, 
        total_time: float, 
        results: List[APISearchResult]
    ) -> SearchMetrics:
        """Create search metrics for performance tracking"""
        avg_relevance = (
            sum(r.relevance_score for r in results) / len(results) 
            if results else 0.0
        )
        
        avg_confidence = (
            sum(r.confidence for r in results) / len(results) 
            if results else 0.0
        )
        
        return SearchMetrics(
            query=query,
            strategy_used=strategy,
            total_time_ms=total_time,
            final_results=len(results),
            avg_relevance_score=avg_relevance,
            confidence_score=avg_confidence
        )
    
    # Performance and monitoring methods
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        base_stats = {
            "total_searches": self.total_searches,
            "cache_hit_rate": self.cache_hits / max(self.total_searches, 1),
            "memory_usage_mb": self.indices.get_memory_usage() if self._initialized else 0.0,
            "indices_ready": self.indices.is_ready() if self._initialized else False
        }
        
        if not self.search_metrics:
            return base_stats
        
        avg_time = sum(m.total_time_ms for m in self.search_metrics) / len(self.search_metrics)
        avg_results = sum(m.final_results for m in self.search_metrics) / len(self.search_metrics)
        avg_relevance = sum(m.avg_relevance_score for m in self.search_metrics) / len(self.search_metrics)
        
        base_stats.update({
            "avg_search_time_ms": avg_time,
            "avg_results_per_search": avg_results,
            "avg_relevance_score": avg_relevance
        })
        
        return base_stats
    
    def clear_caches(self) -> None:
        """Clear all caches"""
        self.indices.clear_all_caches()
        self.search_metrics.clear()
        self.cache_hits = 0
        self.logger.info("Cleared all search caches")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the search engine"""
        health = {
            "initialized": self._initialized,
            "indices_ready": self.indices.is_ready() if self._initialized else False,
            "memory_usage_mb": self.indices.get_memory_usage() if self._initialized else 0,
            "total_searches": self.total_searches,
            "initialization_error": self._initialization_error
        }
        
        # Test search if initialized
        if self._initialized:
            try:
                test_results = await self.search("test", SearchContext(task_type="test", max_results=1))
                health["search_functional"] = True
                health["test_search_results"] = len(test_results)
            except Exception as e:
                health["search_functional"] = False
                health["search_error"] = str(e)
        
        return health
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
