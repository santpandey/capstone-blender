"""
Hybrid Vector Database Manager
Intelligently switches between FAISS and Qdrant based on cost, performance, and availability
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pathlib import Path

from .base import VectorStore, SearchResult, IndexStats, VectorBackend
from .faiss_store import FAISSStore
from .qdrant_store import QdrantStore
from .cost_monitor import CostMonitor, CostEvent

class FallbackReason(Enum):
    COST_THRESHOLD = "cost_threshold_exceeded"
    QDRANT_UNAVAILABLE = "qdrant_unavailable"
    PERFORMANCE_ISSUES = "performance_issues"
    MANUAL_OVERRIDE = "manual_override"

class HybridVectorManager:
    """
    Hybrid manager that automatically switches between FAISS and Qdrant
    based on cost thresholds, availability, and performance metrics
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize cost monitor
        cost_config = config.get('cost_monitor', {})
        self.cost_monitor = CostMonitor(cost_config)
        
        # Vector store configurations
        faiss_config = config.get('faiss', {
            'backend': 'faiss',
            'index_path': 'faiss_index',
            'model_name': 'all-MiniLM-L6-v2',
            'dimension': 384
        })
        
        qdrant_config = config.get('qdrant', {
            'backend': 'qdrant',
            'collection_name': 'blender_apis',
            'model_name': 'all-MiniLM-L6-v2',
            'dimension': 384,
            'url': ':memory:',  # Default to in-memory for development
            'api_key': None
        })
        
        # Initialize vector stores
        self.faiss_store = FAISSStore(faiss_config)
        self.qdrant_store = None
        
        # Try to initialize Qdrant (may fail if not available)
        try:
            self.qdrant_store = QdrantStore(qdrant_config)
        except ImportError:
            print("⚠️ Qdrant not available - will use FAISS only")
        
        # Current active backend
        self.active_backend = VectorBackend.FAISS
        self.fallback_reason = None
        
        # Performance tracking
        self.performance_metrics = {
            'faiss': {'avg_search_time': 0.0, 'search_count': 0},
            'qdrant': {'avg_search_time': 0.0, 'search_count': 0}
        }
        
        # Setup cost monitor callbacks
        self.cost_monitor.add_warning_callback(self._on_cost_warning)
        self.cost_monitor.add_fallback_callback(self._on_cost_fallback)
        
        # Sync settings
        self.auto_sync = config.get('auto_sync', True)
        self.sync_interval = config.get('sync_interval', 3600)  # 1 hour
        self.last_sync = 0
    
    async def initialize(self) -> bool:
        """Initialize the hybrid vector manager"""
        try:
            # Always initialize FAISS (fallback)
            faiss_success = await self.faiss_store.initialize()
            if not faiss_success:
                print("❌ Failed to initialize FAISS store")
                return False
            
            # Try to initialize Qdrant if available
            qdrant_success = False
            if self.qdrant_store:
                try:
                    qdrant_success = await self.qdrant_store.initialize()
                    if qdrant_success:
                        print("✅ Qdrant store initialized successfully")
                        # Start with Qdrant if available and cost-effective
                        if self._should_use_qdrant():
                            self.active_backend = VectorBackend.QDRANT
                        else:
                            self.active_backend = VectorBackend.FAISS
                    else:
                        print("⚠️ Qdrant initialization failed - using FAISS")
                        self.active_backend = VectorBackend.FAISS
                        self.fallback_reason = FallbackReason.QDRANT_UNAVAILABLE
                except Exception as e:
                    print(f"⚠️ Qdrant initialization error: {e} - using FAISS")
                    self.active_backend = VectorBackend.FAISS
                    self.fallback_reason = FallbackReason.QDRANT_UNAVAILABLE
            else:
                self.active_backend = VectorBackend.FAISS
                self.fallback_reason = FallbackReason.QDRANT_UNAVAILABLE
            
            print(f"✅ Hybrid manager initialized with active backend: {self.active_backend.value}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize hybrid manager: {e}")
            return False
    
    def _should_use_qdrant(self) -> bool:
        """Determine if Qdrant should be used based on cost and availability"""
        if not self.qdrant_store:
            return False
        
        cost_summary = self.cost_monitor.get_cost_summary()
        cost_ratio = cost_summary['cost_ratio']
        
        # Don't use Qdrant if cost threshold is exceeded
        if cost_ratio >= self.cost_monitor.thresholds.fallback_threshold:
            return False
        
        return True
    
    def _get_active_store(self) -> VectorStore:
        """Get the currently active vector store"""
        if self.active_backend == VectorBackend.QDRANT and self.qdrant_store:
            return self.qdrant_store
        return self.faiss_store
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the active vector store"""
        try:
            active_store = self._get_active_store()
            
            # Track cost for inserts
            if self.active_backend == VectorBackend.QDRANT:
                self.cost_monitor.track_event(CostEvent.INSERT, len(documents))
            
            success = await active_store.add_documents(documents)
            
            # Sync to other store if auto-sync is enabled
            if success and self.auto_sync:
                await self._sync_documents(documents)
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
            return False
    
    async def search(self, 
                    query: str, 
                    top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search using the active vector store with performance tracking"""
        start_time = time.time()
        
        try:
            active_store = self._get_active_store()
            
            # Track cost for searches
            if self.active_backend == VectorBackend.QDRANT:
                self.cost_monitor.track_event(CostEvent.SEARCH, 1)
            
            results = await active_store.search(query, top_k, filters)
            
            # Update performance metrics
            search_time = time.time() - start_time
            self._update_performance_metrics(self.active_backend, search_time)
            
            return results
            
        except Exception as e:
            print(f"❌ Search failed on {self.active_backend.value}: {e}")
            
            # Try fallback if primary fails
            if self.active_backend == VectorBackend.QDRANT:
                print("🔄 Attempting fallback to FAISS...")
                try:
                    results = await self.faiss_store.search(query, top_k, filters)
                    search_time = time.time() - start_time
                    self._update_performance_metrics(VectorBackend.FAISS, search_time)
                    return results
                except Exception as fallback_error:
                    print(f"❌ Fallback search also failed: {fallback_error}")
            
            return []
    
    async def hybrid_search(self,
                           query: str,
                           semantic_weight: float = 0.7,
                           fuzzy_weight: float = 0.3,
                           top_k: int = 5,
                           filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Hybrid search using the active vector store"""
        start_time = time.time()
        
        try:
            active_store = self._get_active_store()
            
            # Track cost for searches
            if self.active_backend == VectorBackend.QDRANT:
                self.cost_monitor.track_event(CostEvent.SEARCH, 1)
            
            results = await active_store.hybrid_search(
                query, semantic_weight, fuzzy_weight, top_k, filters
            )
            
            # Update performance metrics
            search_time = time.time() - start_time
            self._update_performance_metrics(self.active_backend, search_time)
            
            return results
            
        except Exception as e:
            print(f"❌ Hybrid search failed on {self.active_backend.value}: {e}")
            
            # Try fallback if primary fails
            if self.active_backend == VectorBackend.QDRANT:
                print("🔄 Attempting hybrid search fallback to FAISS...")
                try:
                    results = await self.faiss_store.hybrid_search(
                        query, semantic_weight, fuzzy_weight, top_k, filters
                    )
                    search_time = time.time() - start_time
                    self._update_performance_metrics(VectorBackend.FAISS, search_time)
                    return results
                except Exception as fallback_error:
                    print(f"❌ Fallback hybrid search also failed: {fallback_error}")
            
            return []
    
    async def _sync_documents(self, documents: List[Dict[str, Any]]):
        """Sync documents to the inactive store"""
        try:
            if self.active_backend == VectorBackend.QDRANT and self.faiss_store:
                await self.faiss_store.add_documents(documents)
                print(f"✅ Synced {len(documents)} documents to FAISS")
            elif self.active_backend == VectorBackend.FAISS and self.qdrant_store:
                await self.qdrant_store.add_documents(documents)
                print(f"✅ Synced {len(documents)} documents to Qdrant")
        except Exception as e:
            print(f"⚠️ Document sync failed: {e}")
    
    def _update_performance_metrics(self, backend: VectorBackend, search_time: float):
        """Update performance metrics for a backend"""
        backend_key = backend.value
        metrics = self.performance_metrics[backend_key]
        
        # Update running average
        count = metrics['search_count']
        avg_time = metrics['avg_search_time']
        
        new_avg = (avg_time * count + search_time) / (count + 1)
        
        metrics['avg_search_time'] = new_avg
        metrics['search_count'] = count + 1
    
    def _on_cost_warning(self, metrics, message: str):
        """Handle cost warning callback"""
        print(f"💰 {message}")
        # Could implement additional warning logic here
    
    def _on_cost_fallback(self, metrics, message: str):
        """Handle cost fallback callback"""
        print(f"🚨 {message}")
        
        # Switch to FAISS
        if self.active_backend == VectorBackend.QDRANT:
            self.active_backend = VectorBackend.FAISS
            self.fallback_reason = FallbackReason.COST_THRESHOLD
            print("✅ Switched to FAISS backend due to cost threshold")
    
    async def force_backend(self, backend: VectorBackend, reason: str = "manual_override"):
        """Manually force a specific backend"""
        if backend == VectorBackend.QDRANT and not self.qdrant_store:
            print("❌ Cannot switch to Qdrant - not available")
            return False
        
        self.active_backend = backend
        self.fallback_reason = FallbackReason.MANUAL_OVERRIDE if reason == "manual_override" else None
        print(f"✅ Manually switched to {backend.value} backend")
        return True
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from both stores"""
        stats = {
            'active_backend': self.active_backend.value,
            'fallback_reason': self.fallback_reason.value if self.fallback_reason else None,
            'performance_metrics': self.performance_metrics,
            'cost_summary': self.cost_monitor.get_cost_summary()
        }
        
        # Get stats from active store
        try:
            active_store = self._get_active_store()
            active_stats = await active_store.get_stats()
            stats['active_store_stats'] = {
                'total_vectors': active_stats.total_vectors,
                'index_size_mb': active_stats.index_size_mb,
                'backend': active_stats.backend.value
            }
        except Exception as e:
            stats['active_store_stats'] = {'error': str(e)}
        
        # Get health checks
        try:
            faiss_health = await self.faiss_store.health_check()
            stats['faiss_health'] = faiss_health
            
            if self.qdrant_store:
                qdrant_health = await self.qdrant_store.health_check()
                stats['qdrant_health'] = qdrant_health
            else:
                stats['qdrant_health'] = {'status': 'unavailable', 'reason': 'not_installed'}
        except Exception as e:
            stats['health_check_error'] = str(e)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            stats = await self.get_comprehensive_stats()
            
            # Determine overall health
            faiss_healthy = stats.get('faiss_health', {}).get('status') == 'healthy'
            qdrant_healthy = stats.get('qdrant_health', {}).get('status') == 'healthy'
            
            if self.active_backend == VectorBackend.FAISS:
                overall_status = 'healthy' if faiss_healthy else 'unhealthy'
            else:
                overall_status = 'healthy' if qdrant_healthy else ('degraded' if faiss_healthy else 'unhealthy')
            
            return {
                'status': overall_status,
                'active_backend': self.active_backend.value,
                'fallback_available': faiss_healthy if self.active_backend == VectorBackend.QDRANT else qdrant_healthy,
                'details': stats
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def close(self):
        """Close all vector stores"""
        try:
            await self.faiss_store.close()
            if self.qdrant_store:
                await self.qdrant_store.close()
            print("✅ Hybrid vector manager closed")
        except Exception as e:
            print(f"⚠️ Error closing hybrid manager: {e}")

# Convenience factory function
def create_hybrid_manager(config: Dict[str, Any]) -> HybridVectorManager:
    """Factory function to create a configured hybrid manager"""
    return HybridVectorManager(config)
