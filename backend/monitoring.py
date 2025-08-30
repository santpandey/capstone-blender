"""
Monitoring and health check utilities for 3D Asset Generator
"""

import asyncio
import time
import psutil
import os
from typing import Dict, Any, List
from pathlib import Path

class SystemMonitor:
    """Monitor system resources and application health"""
    
    def __init__(self):
        self.start_time = time.time()
        self.generation_count = 0
        self.error_count = 0
        self.last_generation_time = None
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "uptime_seconds": time.time() - self.start_time
        }
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        return {
            "generations_total": self.generation_count,
            "errors_total": self.error_count,
            "last_generation": self.last_generation_time,
            "error_rate": self.error_count / max(self.generation_count, 1),
            "models_directory_size": self._get_directory_size("generated_models"),
            "scripts_directory_size": self._get_directory_size("generated_scripts")
        }
    
    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes"""
        try:
            path = Path(directory)
            if not path.exists():
                return 0
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        except Exception:
            return 0
    
    def record_generation(self, success: bool = True):
        """Record a generation attempt"""
        self.generation_count += 1
        self.last_generation_time = time.time()
        if not success:
            self.error_count += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_application_metrics()
        
        # Health checks
        health_checks = {
            "memory_ok": system_metrics["memory"]["percent"] < 85,
            "disk_ok": system_metrics["disk"]["percent"] < 90,
            "cpu_ok": system_metrics["cpu_percent"] < 80,
            "error_rate_ok": app_metrics["error_rate"] < 0.1,
            "blender_available": self._check_blender_available()
        }
        
        overall_healthy = all(health_checks.values())
        
        return {
            "healthy": overall_healthy,
            "checks": health_checks,
            "system": system_metrics,
            "application": app_metrics,
            "timestamp": time.time()
        }
    
    def _check_blender_available(self) -> bool:
        """Check if Blender is available"""
        try:
            import subprocess
            result = subprocess.run(
                ['blender', '--version'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

# Global monitor instance
monitor = SystemMonitor()
