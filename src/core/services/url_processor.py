"""
Procesador de URLs y aplicación de reglas de transformación.
"""
from urllib.parse import ParseResult, urlparse, urlunparse, parse_qs, urlencode
from typing import List, Tuple, Dict
from abc import ABC, abstractmethod

Rule = Tuple[List[str], str]


class SuffixStrategy(ABC):
    @abstractmethod
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        """Apply the suffix strategy to the parsed URL.

        Args:
            parsed_url (ParseResult): Parsed URL object.
            suffix (str): Suffix to add.
            original_url (str): Original URL.

        Returns:
            str: Modified URL with the suffix applied.
        """
        ...


class AbsoluteUrlStrategy(SuffixStrategy):
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        return suffix


class PathStrategy(SuffixStrategy):
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        new_path = parsed_url.path.rstrip("/") + suffix
        return urlunparse(parsed_url._replace(path=new_path))


class QueryStrategy(SuffixStrategy):
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        qs: Dict[str, List[str]] = parse_qs(parsed_url.query)
        for param in suffix.lstrip("?").split("&"):
            if "=" in param:
                k, v = param.split("=", 1)
                qs[k] = [v]
            else:
                # Handle parameters without values, e.g., "?flag"
                qs[param] = [""]
        new_q = urlencode(qs, doseq=True)
        return urlunparse(parsed_url._replace(query=new_q))


class SimpleSuffixStrategy(SuffixStrategy):
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        return original_url.rstrip("/") + suffix


def _get_strategy(suffix: str) -> SuffixStrategy:
    """Determine the appropriate strategy based on the suffix format.

    Args:
        suffix (str): The suffix to analyze.

    Returns:
        SuffixStrategy: The appropriate strategy instance.
    """
    if suffix.startswith(("http://", "https://")):
        return AbsoluteUrlStrategy()
    elif suffix.startswith("/"):
        return PathStrategy()
    elif suffix.startswith("?"):
        return QueryStrategy()
    else:
        return SimpleSuffixStrategy()


def add_suffix(url: str, rules: List[Rule]) -> str:
    """Add suffix to URL based on matching rules.

    Args:
        url (str): The original URL.
        rules (List[Rule]): List of rules to apply.

    Returns:
        str: The modified URL with suffix applied, or original URL if no rules match.
    """
    if not url or not rules:
        return url

    for patterns, suffix in rules:
        if any(pattern in url for pattern in patterns):
            parsed_url = urlparse(url)
            strategy = _get_strategy(suffix)
            return strategy.apply(parsed_url, suffix, url)

    return url
