"""
Qdrant-based vector store implementation
Optimized for cloud production deployment with built-in clustering and HA
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from rapidfuzz import process, fuzz
import time

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct, Filter, 
        FieldCondition, MatchValue, SearchRequest
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️ Qdrant client not installed. Install with: uv add qdrant-client")

from .base import VectorStore, SearchResult, IndexStats, VectorBackend

class QdrantStore(VectorStore):
    """Qdrant-based vector store for cloud production deployment"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client not available. Install with: uv add qdrant-client")
        
        # Qdrant configuration
        self.collection_name = config.get('collection_name', 'blender_apis')
        self.model_name = config.get('model_name', 'all-MiniLM-L6-v2')
        self.dimension = config.get('dimension', 384)
        
        # Connection settings
        self.url = config.get('url', ':memory:')  # In-memory for local development
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        
        # Initialize components
        self.client = None
        self.embeddings_model = None
        
        # Fuzzy matching cache
        self.api_names_cache = []
        self.cache_updated = 0
    
    async def initialize(self) -> bool:
        """Initialize Qdrant client and collection"""
        try:
            # Initialize embedding model
            self.embeddings_model = SentenceTransformer(self.model_name)
            
            # Initialize Qdrant client
            if self.url == ':memory:':
                self.client = QdrantClient(":memory:")
                print("✅ Using in-memory Qdrant for development")
            else:
                self.client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key,
                    timeout=self.timeout
                )
                print(f"✅ Connected to Qdrant at {self.url}")
            
            # Create collection if it doesn't exist
            await self._ensure_collection_exists()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Qdrant store: {e}")
            return False
    
    async def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created Qdrant collection: {self.collection_name}")
            else:
                print(f"✅ Using existing Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            print(f"❌ Failed to ensure collection exists: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to Qdrant collection"""
        try:
            if not documents:
                return True
            
            points = []
            
            for doc in documents:
                # Create searchable text
                api_name = doc.get('full_name', '')
                description = doc.get('description', '')
                category = doc.get('category', '')
                tags = ' '.join(doc.get('tags', []))
                
                searchable_text = f"{api_name} {description} {category} {tags}"
                
                # Generate embedding
                embedding = self.embeddings_model.encode([searchable_text])[0].tolist()
                
                # Create point
                point_id = doc.get('id', api_name)
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        'full_name': api_name,
                        'description': description,
                        'category': category,
                        'tags': doc.get('tags', []),
                        'parameters': doc.get('parameters', []),
                        'module': doc.get('module', ''),
                        'signature': doc.get('signature', ''),
                        'examples': doc.get('examples', []),
                        'searchable_text': searchable_text
                    }
                )
                points.append(point)
            
            # Batch upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            # Update API names cache for fuzzy search
            await self._update_api_names_cache()
            
            print(f"✅ Added {len(documents)} documents to Qdrant")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add documents to Qdrant: {e}")
            return False
    
    async def search(self, 
                    query: str, 
                    top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Semantic search using Qdrant"""
        try:
            # Generate query embedding
            query_embedding = self.embeddings_model.encode([query])[0].tolist()
            
            # Build filter if provided
            qdrant_filter = None
            if filters:
                qdrant_filter = self._build_qdrant_filter(filters)
            
            # Search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter
            )
            
            results = []
            for hit in search_result:
                payload = hit.payload
                
                result = SearchResult(
                    id=str(hit.id),
                    score=self._normalize_score(hit.score, VectorBackend.QDRANT),
                    metadata=payload,
                    content=payload.get('description', ''),
                    api_name=payload.get('full_name', ''),
                    category=payload.get('category', ''),
                    parameters=payload.get('parameters', [])
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"❌ Qdrant search failed: {e}")
            return []
    
    async def hybrid_search(self,
                           query: str,
                           semantic_weight: float = 0.7,
                           fuzzy_weight: float = 0.3,
                           top_k: int = 5,
                           filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Hybrid search combining Qdrant semantic search and fuzzy matching"""
        try:
            # 1. Semantic search with Qdrant
            semantic_results = await self.search(query, top_k * 2, filters)
            
            # 2. Fuzzy search for exact API names
            fuzzy_results = await self._fuzzy_search(query, top_k, filters)
            
            # 3. Combine and re-rank results
            combined_results = self._combine_results(
                semantic_results, fuzzy_results,
                semantic_weight, fuzzy_weight
            )
            
            return combined_results[:top_k]
            
        except Exception as e:
            print(f"❌ Qdrant hybrid search failed: {e}")
            return []
    
    async def _fuzzy_search(self, query: str, top_k: int, filters: Optional[Dict[str, Any]]) -> List[SearchResult]:
        """Fuzzy matching using cached API names"""
        if not self.api_names_cache:
            await self._update_api_names_cache()
        
        if not self.api_names_cache:
            return []
        
        # Fuzzy matching
        matches = process.extract(query, self.api_names_cache, limit=top_k, scorer=fuzz.token_set_ratio)
        
        results = []
        for api_name, score, _ in matches:
            if score < 60:  # Minimum threshold
                continue
            
            # Get full document from Qdrant
            try:
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_filter=Filter(
                        must=[FieldCondition(key="full_name", match=MatchValue(value=api_name))]
                    ),
                    limit=1
                )
                
                if search_result:
                    hit = search_result[0]
                    payload = hit.payload
                    
                    # Apply additional filters
                    if filters and not self._apply_payload_filters(payload, filters):
                        continue
                    
                    result = SearchResult(
                        id=str(hit.id),
                        score=score / 100.0,  # Normalize to 0-1
                        metadata=payload,
                        content=payload.get('description', ''),
                        api_name=payload.get('full_name', ''),
                        category=payload.get('category', ''),
                        parameters=payload.get('parameters', [])
                    )
                    results.append(result)
                    
            except Exception as e:
                print(f"⚠️ Error in fuzzy search for {api_name}: {e}")
                continue
        
        return results
    
    async def _update_api_names_cache(self):
        """Update cached API names for fuzzy search"""
        try:
            # Get all API names from Qdrant
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Adjust based on your dataset size
                with_payload=["full_name"]
            )
            
            self.api_names_cache = [
                point.payload.get('full_name', '') 
                for point in scroll_result[0] 
                if point.payload.get('full_name')
            ]
            
            self.cache_updated = time.time()
            print(f"✅ Updated API names cache with {len(self.api_names_cache)} entries")
            
        except Exception as e:
            print(f"⚠️ Failed to update API names cache: {e}")
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from dictionary"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, list):
                # OR condition for list values
                or_conditions = [
                    FieldCondition(key=key, match=MatchValue(value=v))
                    for v in value
                ]
                conditions.extend(or_conditions)
            else:
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        return Filter(must=conditions) if conditions else None
    
    def _apply_payload_filters(self, payload: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filters to Qdrant payload"""
        for key, value in filters.items():
            if key not in payload:
                return False
            
            if isinstance(value, list):
                if payload[key] not in value:
                    return False
            else:
                if payload[key] != value:
                    return False
        
        return True
    
    def _combine_results(self, semantic_results: List[SearchResult], 
                        fuzzy_results: List[SearchResult],
                        semantic_weight: float, fuzzy_weight: float) -> List[SearchResult]:
        """Combine and re-rank semantic and fuzzy results"""
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            result.score = result.score * semantic_weight
            result_map[result.id] = result
        
        # Add/update with fuzzy results
        for result in fuzzy_results:
            if result.id in result_map:
                # Combine scores
                result_map[result.id].score += result.score * fuzzy_weight
            else:
                result.score = result.score * fuzzy_weight
                result_map[result.id] = result
        
        # Sort by combined score
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results
    
    async def get_stats(self) -> IndexStats:
        """Get Qdrant collection statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return IndexStats(
                total_vectors=collection_info.points_count,
                index_size_mb=collection_info.vectors_count * self.dimension * 4 / (1024 * 1024),
                last_updated=time.time(),
                backend=VectorBackend.QDRANT
            )
            
        except Exception as e:
            print(f"❌ Failed to get Qdrant stats: {e}")
            return IndexStats(0, 0.0, time.time(), VectorBackend.QDRANT)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant store health"""
        try:
            # Test connection
            collections = self.client.get_collections()
            stats = await self.get_stats()
            
            return {
                'status': 'healthy',
                'backend': 'qdrant',
                'url': self.url,
                'collection_name': self.collection_name,
                'total_vectors': stats.total_vectors,
                'collections_count': len(collections.collections),
                'api_names_cached': len(self.api_names_cache)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'backend': 'qdrant',
                'error': str(e)
            }
    
    async def close(self):
        """Close Qdrant client"""
        try:
            if self.client:
                self.client.close()
            print("✅ Qdrant store closed")
        except Exception as e:
            print(f"⚠️ Error closing Qdrant store: {e}")
