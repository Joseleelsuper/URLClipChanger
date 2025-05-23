import logging
import os
from datetime import datetime
from pathlib import Path


class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        """Initialize the logger with file and console handlers"""
        self.logger = logging.getLogger("URLClipChanger")
        self.logger.setLevel(logging.DEBUG)
          # Create formatter with timestamp (HH:MM:SS)
        formatter = logging.Formatter(
            "[%(levelname)s] [%(asctime)s] %(message)s", 
            datefmt="%H:%M:%S"
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # File handler
        log_dir = Path(__file__).parent.parent / "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"log_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, msg):
        """Log debug message"""
        self.logger.debug(msg)
    
    def info(self, msg):
        """Log info message"""
        self.logger.info(msg)
    
    def warning(self, msg):
        """Log warning message"""
        self.logger.warning(msg)
    
    def error(self, msg):
        """Log error message"""
        self.logger.error(msg)
    
    def critical(self, msg):
        """Log critical message"""
        self.logger.critical(msg)


# Create singleton instance
logger = Logger()