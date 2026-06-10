import logging
import sys
from config import config

def setup_logger(name: str = "driver_safety") -> logging.Logger:
    """Configures and returns a logger with handlers for console and file output."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger
        
    logger.setLevel(config.log_level)
    
    # Formatter configuration
    formatter = logging.Formatter(
        fmt="%(asctime)s | [%(levelname)s] | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    try:
        log_file = config.log_file_path
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Failed to create file log handler: {e}", file=sys.stderr)
        
    return logger

# Export a default logger instance
logger = setup_logger()
