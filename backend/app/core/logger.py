"""Logger configuration."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
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
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
            
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name configured for structured logging."""
    logger = logging.getLogger(name)
    
    # Only add handlers if they haven't been added yet
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)
        
        # File handler for persistent logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger 