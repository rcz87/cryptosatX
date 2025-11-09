# ADDED FOR CRYPTOSATX ENHANCEMENT
"""
Structured JSON Logging System
For debugging, monitoring, and audit trails
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing and analysis"""
    
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
        
        # Add custom fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_json_logger(name: str = "cryptosatx", level: int = logging.INFO) -> logging.Logger:
    """
    Setup structured JSON logger
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Optional: File handler for persistent logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / f"{name}.log")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger


def log_api_call(logger: logging.Logger, endpoint: str, symbol: Optional[str] = None, 
                 duration: Optional[float] = None, status: str = "success", 
                 extra_data: Optional[Dict[str, Any]] = None):
    """
    Log API calls with structured data
    
    Example:
        log_api_call(logger, "/signals/BTC", symbol="BTC", duration=1.23, 
                     extra_data={"score": 65, "signal": "LONG"})
    """
    data = {
        "endpoint": endpoint,
        "symbol": symbol,
        "duration_ms": round(duration * 1000, 2) if duration else None,
        "status": status,
    }
    
    if extra_data:
        data.update(extra_data)
    
    # Create log record with extra data
    log_record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, 
        f"API Call: {endpoint}", (), None
    )
    setattr(log_record, 'extra_data', data)  # Use setattr to avoid type checking issues
    logger.handle(log_record)


def log_signal_generation(logger: logging.Logger, symbol: str, signal: str, 
                          score: float, factors: Dict[str, Any]):
    """
    Log signal generation events
    
    Example:
        log_signal_generation(logger, "BTC", "LONG", 72.5, 
                            {"funding_rate": 0.01, "sentiment": 75})
    """
    data = {
        "event": "signal_generated",
        "symbol": symbol,
        "signal": signal,
        "score": score,
        "factors": factors,
    }
    
    log_record = logger.makeRecord(
        logger.name, logging.INFO, "", 0,
        f"Signal Generated: {symbol} -> {signal}", (), None
    )
    setattr(log_record, 'extra_data', data)  # Use setattr to avoid type checking issues
    logger.handle(log_record)


def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log errors with context
    
    Example:
        try:
            ...
        except Exception as e:
            log_error(logger, e, {"symbol": "BTC", "endpoint": "/signals/BTC"})
    """
    data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
    }
    
    log_record = logger.makeRecord(
        logger.name, logging.ERROR, "", 0,
        f"Error: {str(error)}", (), None
    )
    setattr(log_record, 'extra_data', data)  # Use setattr to avoid type checking issues
    logger.handle(log_record)


# Create default logger instance
default_logger = setup_json_logger()
