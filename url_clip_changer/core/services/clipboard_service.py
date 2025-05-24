"""
Servicio de clipboard que implementa la lógica de negocio para el procesamiento de URLs.
"""
from typing import List
from src.core.services.url_processor import Rule, add_suffix
from src.infrastructure.logging.logger import logger


class ClipboardService:
    """Servicio que maneja la lógica de procesamiento de URLs del clipboard."""
    
    def __init__(self, rules: List[Rule]):
        """
        Inicializa el servicio con las reglas de transformación.
        
        Args:
            rules: Lista de reglas para transformar URLs
        """
        self.rules = rules
        logger.debug(f"ClipboardService initialized with {len(rules)} rules")
    
    def process_url(self, url: str) -> str:
        """
        Procesa una URL aplicando las reglas configuradas.
        
        Args:
            url: URL original del clipboard
            
        Returns:
            URL procesada con sufijos aplicados según las reglas
        """
        if not url or not url.strip():
            return url
            
        original_url = url.strip()
        processed_url = add_suffix(original_url, self.rules)
        
        if processed_url != original_url:
            logger.info(f"URL transformed: {original_url} -> {processed_url}")
        else:
            logger.debug(f"No transformation applied to: {original_url}")
            
        return processed_url
    
    def should_process_content(self, content: str) -> bool:
        """
        Determina si el contenido del clipboard debe ser procesado.
        
        Args:
            content: Contenido del clipboard
            
        Returns:
            True si el contenido parece ser una URL que debe procesarse
        """
        if not content or not content.strip():
            return False
            
        content = content.strip()
        
        # Verificar si parece una URL
        if content.startswith(('http://', 'https://', 'ftp://', 'www.')):
            return True
            
        # Verificar si contiene un dominio típico
        if '.' in content and ' ' not in content and '\n' not in content:
            # Simple heuristic para detectar URLs sin protocolo
            return True
            
        return False
