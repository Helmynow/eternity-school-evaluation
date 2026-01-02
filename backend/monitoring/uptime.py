"""
Uptime monitoring and health check utilities
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import psutil
from sqlalchemy.orm import Session
from sqlalchemy import text

class UptimeMonitor:
    """Monitor system uptime and health metrics"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0
    
    def get_uptime(self) -> Dict[str, Any]:
        """Get system uptime information"""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "started_at": self.start_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime),
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": disk.percent,
                },
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics"""
        return {
            "requests_total": self.request_count,
            "errors_total": self.error_count,
            "error_rate": round(self.error_count / max(self.request_count, 1) * 100, 2),
        }
    
    def check_database_health(self, db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start = datetime.utcnow()
            db.execute(text("SELECT 1"))
            duration = (datetime.utcnow() - start).total_seconds()
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    def get_full_health_check(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """Get comprehensive health check"""
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": self.get_uptime(),
            "application": self.get_application_metrics(),
        }
        
        # Add system metrics (may fail in some environments)
        try:
            health["system"] = self.get_system_metrics()
        except Exception:
            health["system"] = {"error": "Metrics unavailable"}
        
        # Add database health if session provided
        if db:
            health["database"] = self.check_database_health(db)
        
        # Determine overall status
        if health.get("database", {}).get("status") != "healthy":
            health["status"] = "degraded"
        
        return health

# Global uptime monitor instance
uptime_monitor = UptimeMonitor()
