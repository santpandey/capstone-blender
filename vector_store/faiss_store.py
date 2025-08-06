"""
FAISS-based vector store implementation
Optimized for local development and cost-effective production deployment
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer
from rapidfuzz import process, fuzz
import asyncio
import time

from .base import VectorStore, SearchResult, IndexStats, VectorBackend

class FAISSStore(VectorStore):
    """FAISS-based vector store following EAG-V17 patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.index_path = config.get('index_path', 'faiss_index')
        self.model_name = config.get('model_name', 'all-MiniLM-L6-v2')
        self.dimension = config.get('dimension', 384)
        
        # Initialize components
        self.embeddings_model = None
        self.faiss_index = None
        self.metadata_store = {}
        self.id_to_index = {}
        self.index_to_id = {}
        
        # Fuzzy matching for exact API names
        self.api_names = []
        self.api_name_to_id = {}
        
        # Ensure index directory exists
        Path(self.index_path).mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize FAISS index and embedding model"""
        try:
            # Load embedding model
            self.embeddings_model = SentenceTransformer(self.model_name)
            
            # Try to load existing index
            if await self._load_existing_index():
                print(f"✅ Loaded existing FAISS index with {self.faiss_index.ntotal} vectors")
            else:
                # Create new index
                self.faiss_index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                print(f"✅ Created new FAISS index (dimension: {self.dimension})")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize FAISS store: {e}")
            return False
    
    async def _load_existing_index(self) -> bool:
        """Load existing FAISS index and metadata"""
        try:
            index_file = Path(self.index_path) / "index.bin"
            metadata_file = Path(self.index_path) / "metadata.json"
            mappings_file = Path(self.index_path) / "mappings.pkl"
            
            if not all(f.exists() for f in [index_file, metadata_file, mappings_file]):
                return False
            
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(index_file))
            
            # Load metadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata_store = json.load(f)
            
            # Load ID mappings
            with open(mappings_file, 'rb') as f:
                mappings = pickle.load(f)
                self.id_to_index = mappings['id_to_index']
                self.index_to_id = mappings['index_to_id']
                self.api_names = mappings['api_names']
                self.api_name_to_id = mappings['api_name_to_id']
            
            return True
            
        except Exception as e:
            print(f"⚠️ Could not load existing index: {e}")
            return False
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to FAISS index"""
        try:
            if not documents:
                return True
            
            # Extract texts for embedding
            texts = []
            doc_ids = []
            
            for doc in documents:
                # Create searchable text from API info
                api_name = doc.get('full_name', '')
                description = doc.get('description', '')
                category = doc.get('category', '')
                tags = ' '.join(doc.get('tags', []))
                
                # Combine for better semantic search
                searchable_text = f"{api_name} {description} {category} {tags}"
                texts.append(searchable_text)
                
                doc_id = doc.get('id', api_name)
                doc_ids.append(doc_id)
                
                # Store metadata
                self.metadata_store[doc_id] = doc
                
                # Update API name mappings for fuzzy search
                if api_name:
                    self.api_names.append(api_name)
                    self.api_name_to_id[api_name] = doc_id
            
            # Generate embeddings
            embeddings = self.embeddings_model.encode(texts, convert_to_tensor=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to FAISS index
            start_idx = self.faiss_index.ntotal
            self.faiss_index.add(embeddings)
            
            # Update ID mappings
            for i, doc_id in enumerate(doc_ids):
                index_pos = start_idx + i
                self.id_to_index[doc_id] = index_pos
                self.index_to_id[index_pos] = doc_id
            
            # Save updated index
            await self._save_index()
            
            print(f"✅ Added {len(documents)} documents to FAISS index")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
            return False
    
    async def search(self, 
                    query: str, 
                    top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Semantic search using FAISS"""
        try:
            if self.faiss_index.ntotal == 0:
                return []
            
            # Generate query embedding
            query_embedding = self.embeddings_model.encode([query], convert_to_tensor=False)
            query_embedding = np.array(query_embedding).astype('float32')
            faiss.normalize_L2(query_embedding)
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(query_embedding, min(top_k * 2, self.faiss_index.ntotal))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                doc_id = self.index_to_id.get(idx)
                if not doc_id or doc_id not in self.metadata_store:
                    continue
                
                metadata = self.metadata_store[doc_id]
                
                # Apply filters if provided
                if filters and not self._apply_filters(metadata, filters):
                    continue
                
                api_name, category, parameters = self._extract_api_info(metadata)
                
                result = SearchResult(
                    id=doc_id,
                    score=self._normalize_score(float(score), VectorBackend.FAISS),
                    metadata=metadata,
                    content=metadata.get('description', ''),
                    api_name=api_name,
                    category=category,
                    parameters=parameters
                )
                results.append(result)
            
            # Sort by score (descending) and limit
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    async def hybrid_search(self,
                           query: str,
                           semantic_weight: float = 0.7,
                           fuzzy_weight: float = 0.3,
                           top_k: int = 5,
                           filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Hybrid search combining semantic and fuzzy matching"""
        try:
            # 1. Semantic search
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
            print(f"❌ Hybrid search failed: {e}")
            return []
    
    async def _fuzzy_search(self, query: str, top_k: int, filters: Optional[Dict[str, Any]]) -> List[SearchResult]:
        """Fuzzy matching for exact API names"""
        if not self.api_names:
            return []
        
        # Use rapidfuzz for fuzzy matching
        matches = process.extract(query, self.api_names, limit=top_k, scorer=fuzz.token_set_ratio)
        
        results = []
        for api_name, score, _ in matches:
            if score < 60:  # Minimum fuzzy score threshold
                continue
            
            doc_id = self.api_name_to_id.get(api_name)
            if not doc_id or doc_id not in self.metadata_store:
                continue
            
            metadata = self.metadata_store[doc_id]
            
            # Apply filters
            if filters and not self._apply_filters(metadata, filters):
                continue
            
            api_name_extracted, category, parameters = self._extract_api_info(metadata)
            
            result = SearchResult(
                id=doc_id,
                score=score / 100.0,  # Normalize to 0-1
                metadata=metadata,
                content=metadata.get('description', ''),
                api_name=api_name_extracted,
                category=category,
                parameters=parameters
            )
            results.append(result)
        
        return results
    
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
    
    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filters to metadata"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True
    
    async def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            index_file = Path(self.index_path) / "index.bin"
            faiss.write_index(self.faiss_index, str(index_file))
            
            # Save metadata
            metadata_file = Path(self.index_path) / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_store, f, indent=2, ensure_ascii=False)
            
            # Save ID mappings
            mappings_file = Path(self.index_path) / "mappings.pkl"
            mappings = {
                'id_to_index': self.id_to_index,
                'index_to_id': self.index_to_id,
                'api_names': self.api_names,
                'api_name_to_id': self.api_name_to_id
            }
            with open(mappings_file, 'wb') as f:
                pickle.dump(mappings, f)
            
        except Exception as e:
            print(f"⚠️ Failed to save index: {e}")
    
    async def get_stats(self) -> IndexStats:
        """Get FAISS index statistics"""
        index_size_mb = 0.0
        if self.faiss_index:
            # Estimate index size
            index_size_mb = (self.faiss_index.ntotal * self.dimension * 4) / (1024 * 1024)  # 4 bytes per float32
        
        return IndexStats(
            total_vectors=self.faiss_index.ntotal if self.faiss_index else 0,
            index_size_mb=index_size_mb,
            last_updated=time.time(),
            backend=VectorBackend.FAISS
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check FAISS store health"""
        try:
            stats = await self.get_stats()
            
            return {
                'status': 'healthy',
                'backend': 'faiss',
                'total_vectors': stats.total_vectors,
                'index_size_mb': stats.index_size_mb,
                'model_loaded': self.embeddings_model is not None,
                'index_loaded': self.faiss_index is not None
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def close(self):
        """Close FAISS store and cleanup"""
        try:
            await self._save_index()
            print("✅ FAISS store closed and saved")
        except Exception as e:
            print(f"⚠️ Error closing FAISS store: {e}")
