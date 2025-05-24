"""
Sistema de logging para la aplicación URL Clip Changer.
"""
import logging
import os
import sys
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

        # Prevent adding handlers if they already exist for this logger
        if self.logger.hasHandlers():
            return
        
        # Create formatter
        formatter = logging.Formatter(
            "[%(levelname)s] [%(asctime)s] %(message)s", datefmt="%H:%M:%S"
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Determinar la ruta del log basada en si estamos en un ejecutable o en desarrollo
        if getattr(sys, 'frozen', False):
            # Si estamos en un ejecutable, guardar logs junto al ejecutable
            base_dir = Path(sys.executable).parent
        else:
            # En desarrollo, navegar hasta la raíz del proyecto desde infrastructure/logging
            base_dir = Path(__file__).parent.parent.parent.parent
            
        log_dir = base_dir / "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"log_{timestamp}.log"
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def debug(self, message):
        self.logger.debug(message)
        
    def info(self, message):
        self.logger.info(message)
        
    def warning(self, message):
        self.logger.warning(message)
        
    def error(self, message):
        self.logger.error(message)
        
    def critical(self, message):
        self.logger.critical(message)


# Singleton instance
logger = Logger()
