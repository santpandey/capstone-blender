"""
High-performance search indices for API lookup
Provides O(1) hash lookups and O(log n) fuzzy matching
"""

import time
import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict
from functools import lru_cache

from rapidfuzz import fuzz, process
from .models import CompressedAPI, APICategory, IndexStats, SearchError

class BaseIndex:
    """Base class for all search indices"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.stats = IndexStats(index_name=name)
        self._built = False
    
    def build(self, apis: List[CompressedAPI]) -> None:
        """Build the index from API list"""
        start_time = time.time()
        try:
            self._build_index(apis)
            self._built = True
            self.stats.total_entries = len(apis)
            build_time = (time.time() - start_time) * 1000
            self.logger.info(f"Built {self.name} index with {len(apis)} APIs in {build_time:.2f}ms")
        except Exception as e:
            self.logger.error(f"Failed to build {self.name} index: {e}")
            raise SearchError(f"Failed to build {self.name} index: {str(e)}")
    
    def _build_index(self, apis: List[CompressedAPI]) -> None:
        """Override in subclasses"""
        raise NotImplementedError
    
    def is_built(self) -> bool:
        """Check if index is built"""
        return self._built
    
    def get_stats(self) -> IndexStats:
        """Get index statistics"""
        return self.stats

class ExactMatchIndex(BaseIndex):
    """
    O(1) exact match index using hash maps
    Provides instant lookups for exact API names
    """
    
    def __init__(self):
        super().__init__("exact_match")
        self.name_to_api: Dict[str, CompressedAPI] = {}
        self.normalized_name_to_api: Dict[str, CompressedAPI] = {}
    
    def _build_index(self, apis: List[CompressedAPI]) -> None:
        """Build hash maps for exact matching"""
        self.name_to_api.clear()
        self.normalized_name_to_api.clear()
        
        for api in apis:
            # Index by exact name
            self.name_to_api[api.name] = api
            
            # Index by normalized name (lowercase, no spaces)
            normalized = api.name.lower().replace(" ", "").replace("_", "")
            self.normalized_name_to_api[normalized] = api
        
        # Update memory usage estimate
        self.stats.memory_usage_mb = (
            len(self.name_to_api) * 100 +  # Rough estimate: 100 bytes per entry
            len(self.normalized_name_to_api) * 100
        ) / (1024 * 1024)
    
    def search(self, query: str) -> Optional[CompressedAPI]:
        """
        Search for exact match
        
        Args:
            query: Search query
            
        Returns:
            Matching API or None
        """
        start_time = time.time()
        self.stats.total_lookups += 1
        
        try:
            # Try exact match first
            if query in self.name_to_api:
                self.stats.cache_hits += 1
                return self.name_to_api[query]
            
            # Try normalized match
            normalized_query = query.lower().replace(" ", "").replace("_", "")
            if normalized_query in self.normalized_name_to_api:
                return self.normalized_name_to_api[normalized_query]
            
            return None
            
        finally:
            lookup_time = (time.time() - start_time) * 1000
            self.stats.avg_lookup_time_ms = (
                (self.stats.avg_lookup_time_ms * (self.stats.total_lookups - 1) + lookup_time) /
                self.stats.total_lookups
            )

class CategoryIndex(BaseIndex):
    """
    O(1) category-based filtering index
    Pre-groups APIs by category for fast filtering
    """
    
    def __init__(self):
        super().__init__("category")
        self.category_to_apis: Dict[APICategory, List[CompressedAPI]] = defaultdict(list)
        self.category_counts: Dict[APICategory, int] = {}
    
    def _build_index(self, apis: List[CompressedAPI]) -> None:
        """Build category groupings"""
        self.category_to_apis.clear()
        self.category_counts.clear()
        
        for api in apis:
            self.category_to_apis[api.category].append(api)
        
        # Update counts and sort by popularity
        for category, api_list in self.category_to_apis.items():
            # Sort by popularity score (descending)
            api_list.sort(key=lambda x: x.popularity_score, reverse=True)
            self.category_counts[category] = len(api_list)
        
        # Update memory usage estimate
        total_apis = sum(len(api_list) for api_list in self.category_to_apis.values())
        self.stats.memory_usage_mb = (total_apis * 8) / (1024 * 1024)  # 8 bytes per reference
    
    def get_apis_by_category(self, category: APICategory, limit: Optional[int] = None) -> List[CompressedAPI]:
        """
        Get APIs by category
        
        Args:
            category: API category
            limit: Maximum number of APIs to return
            
        Returns:
            List of APIs in the category
        """
        start_time = time.time()
        self.stats.total_lookups += 1
        
        try:
            apis = self.category_to_apis.get(category, [])
            if limit:
                apis = apis[:limit]
            return apis
            
        finally:
            lookup_time = (time.time() - start_time) * 1000
            self.stats.avg_lookup_time_ms = (
                (self.stats.avg_lookup_time_ms * (self.stats.total_lookups - 1) + lookup_time) /
                self.stats.total_lookups
            )
    
    def get_category_stats(self) -> Dict[APICategory, int]:
        """Get API count by category"""
        return self.category_counts.copy()

class KeywordIndex(BaseIndex):
    """
    Inverted index for keyword-based search
    Maps keywords to APIs that contain them
    """
    
    def __init__(self):
        super().__init__("keyword")
        self.keyword_to_apis: Dict[str, Set[str]] = defaultdict(set)  # keyword -> set of API IDs
        self.api_id_to_api: Dict[str, CompressedAPI] = {}
    
    def _build_index(self, apis: List[CompressedAPI]) -> None:
        """Build inverted keyword index"""
        self.keyword_to_apis.clear()
        self.api_id_to_api.clear()
        
        for api in apis:
            self.api_id_to_api[api.id] = api
            
            # Index all search keywords
            for keyword in api.search_keywords:
                self.keyword_to_apis[keyword.lower()].add(api.id)
            
            # Index tags
            for tag in api.tags:
                self.keyword_to_apis[tag.lower()].add(api.id)
            
            # Index common use cases
            for use_case in api.common_use_cases:
                # Split use case into words
                words = use_case.lower().split()
                for word in words:
                    if len(word) > 2:  # Skip very short words
                        self.keyword_to_apis[word].add(api.id)
        
        # Update memory usage estimate
        total_keywords = len(self.keyword_to_apis)
        avg_apis_per_keyword = sum(len(apis) for apis in self.keyword_to_apis.values()) / max(total_keywords, 1)
        self.stats.memory_usage_mb = (total_keywords * avg_apis_per_keyword * 8) / (1024 * 1024)
    
    def search_by_keywords(self, keywords: List[str], max_results: int = 50) -> List[Tuple[CompressedAPI, float]]:
        """
        Search APIs by keywords with scoring
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of results
            
        Returns:
            List of (API, score) tuples sorted by relevance
        """
        start_time = time.time()
        self.stats.total_lookups += 1
        
        try:
            if not keywords:
                return []
            
            # Find APIs that match keywords
            api_scores: Dict[str, float] = defaultdict(float)
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                matching_api_ids = self.keyword_to_apis.get(keyword_lower, set())
                
                # Score based on keyword rarity (inverse document frequency)
                idf_score = 1.0 / max(len(matching_api_ids), 1)
                
                for api_id in matching_api_ids:
                    api_scores[api_id] += idf_score
            
            # Convert to API objects and sort by score
            results = []
            for api_id, score in api_scores.items():
                if api_id in self.api_id_to_api:
                    api = self.api_id_to_api[api_id]
                    # Boost score with popularity
                    final_score = score * (1 + api.popularity_score)
                    results.append((api, final_score))
            
            # Sort by score (descending) and limit results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:max_results]
            
        finally:
            lookup_time = (time.time() - start_time) * 1000
            self.stats.avg_lookup_time_ms = (
                (self.stats.avg_lookup_time_ms * (self.stats.total_lookups - 1) + lookup_time) /
                self.stats.total_lookups
            )

class FuzzyMatchIndex(BaseIndex):
    """
    Fuzzy string matching index using RapidFuzz
    Provides approximate string matching for typos and variations
    """
    
    def __init__(self, score_threshold: float = 70.0):
        super().__init__("fuzzy_match")
        self.score_threshold = score_threshold
        self.api_names: List[str] = []
        self.name_to_api: Dict[str, CompressedAPI] = {}
        
        # Cache for frequent fuzzy searches
        self._fuzzy_cache: Dict[str, List[Tuple[str, float]]] = {}
        self._cache_max_size = 500
    
    def _build_index(self, apis: List[CompressedAPI]) -> None:
        """Build fuzzy matching structures"""
        self.api_names.clear()
        self.name_to_api.clear()
        self._fuzzy_cache.clear()
        
        for api in apis:
            self.api_names.append(api.name)
            self.name_to_api[api.name] = api
            
            # Also add search keywords for fuzzy matching
            for keyword in api.search_keywords:
                if keyword not in self.name_to_api:  # Avoid duplicates
                    self.api_names.append(keyword)
                    self.name_to_api[keyword] = api
        
        # Update memory usage estimate
        self.stats.memory_usage_mb = (
            len(self.api_names) * 50 +  # Rough estimate for string storage
            len(self.name_to_api) * 8    # Reference storage
        ) / (1024 * 1024)
    
    @lru_cache(maxsize=200)
    def search_fuzzy(self, query: str, limit: int = 10) -> List[Tuple[CompressedAPI, float]]:
        """
        Fuzzy search with caching
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of (API, score) tuples
        """
        start_time = time.time()
        self.stats.total_lookups += 1
        
        try:
            # Use RapidFuzz for fuzzy matching
            matches = process.extract(
                query,
                self.api_names,
                scorer=fuzz.WRatio,
                limit=limit * 2,  # Get more candidates for filtering
                score_cutoff=self.score_threshold
            )
            
            # Convert to API objects and normalize scores
            results = []
            seen_apis = set()
            
            for match_result in matches:
                # Handle different RapidFuzz return formats
                if len(match_result) == 2:
                    match_text, score = match_result
                elif len(match_result) == 3:
                    match_text, score, _ = match_result  # Third element might be index
                else:
                    continue  # Skip malformed results
                
                if match_text in self.name_to_api:
                    api = self.name_to_api[match_text]
                    
                    # Avoid duplicate APIs (same API might match multiple keywords)
                    if api.id not in seen_apis:
                        seen_apis.add(api.id)
                        # Normalize score to 0-1 range
                        normalized_score = score / 100.0
                        results.append((api, normalized_score))
                
                if len(results) >= limit:
                    break
            
            return results
            
        finally:
            lookup_time = (time.time() - start_time) * 1000
            self.stats.avg_lookup_time_ms = (
                (self.stats.avg_lookup_time_ms * (self.stats.total_lookups - 1) + lookup_time) /
                self.stats.total_lookups
            )
    
    def clear_cache(self) -> None:
        """Clear fuzzy search cache"""
        self.search_fuzzy.cache_clear()
        self._fuzzy_cache.clear()

class CompositeIndex:
    """
    Composite index that combines all individual indices
    Provides unified interface for all search operations
    """
    
    def __init__(self):
        self.exact_index = ExactMatchIndex()
        self.category_index = CategoryIndex()
        self.keyword_index = KeywordIndex()
        self.fuzzy_index = FuzzyMatchIndex()
        
        self.logger = logging.getLogger(__name__)
        self._built = False
    
    def build_all_indices(self, apis: List[CompressedAPI]) -> None:
        """Build all indices from API list"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Building composite index for {len(apis)} APIs...")
            
            # Build all indices
            self.exact_index.build(apis)
            self.category_index.build(apis)
            self.keyword_index.build(apis)
            self.fuzzy_index.build(apis)
            
            self._built = True
            
            build_time = (time.time() - start_time) * 1000
            total_memory = sum(
                index.get_stats().memory_usage_mb 
                for index in [self.exact_index, self.category_index, self.keyword_index, self.fuzzy_index]
            )
            
            self.logger.info(
                f"Built all indices in {build_time:.2f}ms, "
                f"total memory usage: {total_memory:.2f}MB"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to build composite index: {e}")
            raise SearchError(f"Failed to build composite index: {str(e)}")
    
    def is_ready(self) -> bool:
        """Check if all indices are built and ready"""
        return (
            self._built and
            self.exact_index.is_built() and
            self.category_index.is_built() and
            self.keyword_index.is_built() and
            self.fuzzy_index.is_built()
        )
    
    def get_memory_usage(self) -> float:
        """Get total memory usage in MB"""
        return sum(
            index.get_stats().memory_usage_mb 
            for index in [self.exact_index, self.category_index, self.keyword_index, self.fuzzy_index]
        )
    
    def get_all_stats(self) -> Dict[str, IndexStats]:
        """Get statistics for all indices"""
        return {
            "exact_match": self.exact_index.get_stats(),
            "category": self.category_index.get_stats(),
            "keyword": self.keyword_index.get_stats(),
            "fuzzy_match": self.fuzzy_index.get_stats()
        }
    
    def clear_all_caches(self) -> None:
        """Clear all caches"""
        self.fuzzy_index.clear_cache()
        self.logger.info("Cleared all index caches")
