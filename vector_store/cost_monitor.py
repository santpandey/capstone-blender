"""
Cost monitoring system for vector database operations
Tracks usage and triggers fallback to FAISS when Qdrant costs exceed thresholds
"""

import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

class CostEvent(Enum):
    SEARCH = "search"
    INSERT = "insert"
    UPDATE = "update"
    STORAGE = "storage"

@dataclass
class CostMetrics:
    """Cost tracking metrics"""
    total_searches: int = 0
    total_inserts: int = 0
    total_updates: int = 0
    storage_mb: float = 0.0
    estimated_monthly_cost: float = 0.0
    last_updated: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CostThresholds:
    """Cost threshold configuration"""
    max_monthly_cost: float = 50.0  # Maximum monthly cost in USD
    warning_threshold: float = 0.8  # Warn at 80% of max cost
    fallback_threshold: float = 0.9  # Fallback at 90% of max cost
    search_cost_per_1k: float = 0.0004  # Qdrant pricing per 1k searches
    storage_cost_per_gb: float = 0.25  # Qdrant pricing per GB/month
    insert_cost_per_1k: float = 0.002  # Qdrant pricing per 1k inserts

class CostMonitor:
    """Monitor and track vector database costs with automatic fallback"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_file = Path(config.get('metrics_file', 'cost_metrics.json'))
        
        # Load thresholds
        threshold_config = config.get('thresholds', {})
        self.thresholds = CostThresholds(
            max_monthly_cost=threshold_config.get('max_monthly_cost', 50.0),
            warning_threshold=threshold_config.get('warning_threshold', 0.8),
            fallback_threshold=threshold_config.get('fallback_threshold', 0.9),
            search_cost_per_1k=threshold_config.get('search_cost_per_1k', 0.0004),
            storage_cost_per_gb=threshold_config.get('storage_cost_per_gb', 0.25),
            insert_cost_per_1k=threshold_config.get('insert_cost_per_1k', 0.002)
        )
        
        # Load existing metrics
        self.metrics = self._load_metrics()
        
        # Callbacks for cost events
        self.warning_callbacks = []
        self.fallback_callbacks = []
    
    def _load_metrics(self) -> CostMetrics:
        """Load cost metrics from file"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    return CostMetrics(**data)
        except Exception as e:
            print(f"⚠️ Could not load cost metrics: {e}")
        
        return CostMetrics(last_updated=time.time())
    
    def _save_metrics(self):
        """Save cost metrics to file"""
        try:
            self.metrics.last_updated = time.time()
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics.to_dict(), f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save cost metrics: {e}")
    
    def track_event(self, event: CostEvent, count: int = 1, size_mb: float = 0.0):
        """Track a cost event and update metrics"""
        if event == CostEvent.SEARCH:
            self.metrics.total_searches += count
        elif event == CostEvent.INSERT:
            self.metrics.total_inserts += count
        elif event == CostEvent.UPDATE:
            self.metrics.total_updates += count
        elif event == CostEvent.STORAGE:
            self.metrics.storage_mb = size_mb
        
        # Recalculate estimated monthly cost
        self._update_estimated_cost()
        
        # Check thresholds
        self._check_thresholds()
        
        # Save updated metrics
        self._save_metrics()
    
    def _update_estimated_cost(self):
        """Update estimated monthly cost based on current usage"""
        # Calculate costs based on current month's usage
        current_time = time.time()
        days_in_month = 30
        seconds_in_month = days_in_month * 24 * 3600
        
        # Estimate monthly usage based on current usage
        time_since_start = current_time - self.metrics.last_updated
        if time_since_start > 0:
            usage_multiplier = seconds_in_month / max(time_since_start, 3600)  # At least 1 hour
        else:
            usage_multiplier = 1
        
        # Calculate estimated monthly costs
        monthly_searches = self.metrics.total_searches * usage_multiplier
        monthly_inserts = self.metrics.total_inserts * usage_multiplier
        
        search_cost = (monthly_searches / 1000) * self.thresholds.search_cost_per_1k
        insert_cost = (monthly_inserts / 1000) * self.thresholds.insert_cost_per_1k
        storage_cost = (self.metrics.storage_mb / 1024) * self.thresholds.storage_cost_per_gb
        
        self.metrics.estimated_monthly_cost = search_cost + insert_cost + storage_cost
    
    def _check_thresholds(self):
        """Check if cost thresholds are exceeded"""
        cost_ratio = self.metrics.estimated_monthly_cost / self.thresholds.max_monthly_cost
        
        if cost_ratio >= self.thresholds.fallback_threshold:
            self._trigger_fallback()
        elif cost_ratio >= self.thresholds.warning_threshold:
            self._trigger_warning()
    
    def _trigger_warning(self):
        """Trigger cost warning"""
        warning_msg = (
            f"⚠️ Cost Warning: Estimated monthly cost ${self.metrics.estimated_monthly_cost:.2f} "
            f"is {(self.metrics.estimated_monthly_cost/self.thresholds.max_monthly_cost)*100:.1f}% "
            f"of maximum ${self.thresholds.max_monthly_cost:.2f}"
        )
        print(warning_msg)
        
        # Call warning callbacks
        for callback in self.warning_callbacks:
            try:
                callback(self.metrics, warning_msg)
            except Exception as e:
                print(f"⚠️ Warning callback failed: {e}")
    
    def _trigger_fallback(self):
        """Trigger fallback to FAISS"""
        fallback_msg = (
            f"🚨 Cost Threshold Exceeded: Estimated monthly cost ${self.metrics.estimated_monthly_cost:.2f} "
            f"exceeds {self.thresholds.fallback_threshold*100:.0f}% of maximum ${self.thresholds.max_monthly_cost:.2f}. "
            f"Triggering fallback to FAISS."
        )
        print(fallback_msg)
        
        # Call fallback callbacks
        for callback in self.fallback_callbacks:
            try:
                callback(self.metrics, fallback_msg)
            except Exception as e:
                print(f"⚠️ Fallback callback failed: {e}")
    
    def add_warning_callback(self, callback):
        """Add callback for cost warnings"""
        self.warning_callbacks.append(callback)
    
    def add_fallback_callback(self, callback):
        """Add callback for cost fallback"""
        self.fallback_callbacks.append(callback)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary"""
        cost_ratio = self.metrics.estimated_monthly_cost / self.thresholds.max_monthly_cost
        
        return {
            'current_metrics': self.metrics.to_dict(),
            'thresholds': asdict(self.thresholds),
            'cost_ratio': cost_ratio,
            'status': self._get_cost_status(cost_ratio),
            'recommendations': self._get_recommendations(cost_ratio)
        }
    
    def _get_cost_status(self, cost_ratio: float) -> str:
        """Get current cost status"""
        if cost_ratio >= self.thresholds.fallback_threshold:
            return "CRITICAL - Fallback triggered"
        elif cost_ratio >= self.thresholds.warning_threshold:
            return "WARNING - Approaching limits"
        elif cost_ratio >= 0.5:
            return "MODERATE - Monitor usage"
        else:
            return "HEALTHY - Within limits"
    
    def _get_recommendations(self, cost_ratio: float) -> List[str]:
        """Get cost optimization recommendations"""
        recommendations = []
        
        if cost_ratio >= self.thresholds.fallback_threshold:
            recommendations.extend([
                "Switch to FAISS backend immediately",
                "Review query patterns for optimization",
                "Consider increasing cost thresholds if budget allows"
            ])
        elif cost_ratio >= self.thresholds.warning_threshold:
            recommendations.extend([
                "Monitor usage closely",
                "Optimize query frequency",
                "Consider caching frequent queries",
                "Review storage requirements"
            ])
        elif cost_ratio >= 0.5:
            recommendations.extend([
                "Usage is moderate - continue monitoring",
                "Consider query optimization for better performance"
            ])
        else:
            recommendations.append("Usage is healthy - no action needed")
        
        return recommendations
    
    def reset_metrics(self):
        """Reset cost metrics (use carefully!)"""
        self.metrics = CostMetrics(last_updated=time.time())
        self._save_metrics()
        print("✅ Cost metrics reset")
    
    def simulate_monthly_cost(self, 
                            searches_per_day: int = 0,
                            inserts_per_day: int = 0,
                            storage_gb: float = 0.0) -> float:
        """Simulate monthly cost for given usage patterns"""
        monthly_searches = searches_per_day * 30
        monthly_inserts = inserts_per_day * 30
        
        search_cost = (monthly_searches / 1000) * self.thresholds.search_cost_per_1k
        insert_cost = (monthly_inserts / 1000) * self.thresholds.insert_cost_per_1k
        storage_cost = storage_gb * self.thresholds.storage_cost_per_gb
        
        return search_cost + insert_cost + storage_cost
