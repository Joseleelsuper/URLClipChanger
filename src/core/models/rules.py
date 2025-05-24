"""
Modelos de dominio para URL Clip Changer.
"""
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class UrlRule:
    """Modelo que representa una regla de transformación de URL."""
    
    patterns: List[str]
    suffix: str
    
    def matches(self, url: str) -> bool:
        """
        Verifica si la URL coincide con alguno de los patrones de esta regla.
        
        Args:
            url: URL a verificar
            
        Returns:
            True si la URL coincide con algún patrón
        """
        return any(pattern in url for pattern in self.patterns)
    
    def __str__(self) -> str:
        return f"UrlRule(patterns={self.patterns}, suffix='{self.suffix}')"


# Alias para compatibilidad con el código existente
Rule = Tuple[List[str], str]


def rule_tuple_to_model(rule_tuple: Rule) -> UrlRule:
    """
    Convierte una tupla de regla al modelo UrlRule.
    
    Args:
        rule_tuple: Tupla (patterns, suffix)
        
    Returns:
        Instancia de UrlRule
    """
    patterns, suffix = rule_tuple
    return UrlRule(patterns=patterns, suffix=suffix)


def rule_model_to_tuple(rule_model: UrlRule) -> Rule:
    """
    Convierte un modelo UrlRule a tupla.
    
    Args:
        rule_model: Instancia de UrlRule
        
    Returns:
        Tupla (patterns, suffix)
    """
    return (rule_model.patterns, rule_model.suffix)
