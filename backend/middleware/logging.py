"""
Structured logging middleware for FastAPI
Outputs JSON-formatted logs for log aggregation services
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import os

# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)

# Setup structured logger
def setup_structured_logging():
    """Configure structured JSON logging"""
    logger = logging.getLogger()
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Add file handler if LOG_FILE is set
    log_file = os.getenv("LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

# Initialize logger
logger = setup_structured_logging()

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests in structured JSON format"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "extra_fields": {
                    "type": "request",
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", ""),
                }
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            duration = time.time() - start_time
            
            # Log successful response
            logger.info(
                "Request completed",
                extra={
                    "extra_fields": {
                        "type": "response",
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "client_ip": client_ip,
                    }
                }
            )
            
            # Add performance header
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "extra_fields": {
                        "type": "error",
                        "method": method,
                        "path": path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "duration_ms": round(duration * 1000, 2),
                        "client_ip": client_ip,
                    }
                },
                exc_info=True
            )
            
            raise

def get_logger(name: str = None):
    """Get a logger instance with structured logging"""
    return logging.getLogger(name or __name__)
