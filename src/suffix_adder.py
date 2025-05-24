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

class DefaultStrategy(SuffixStrategy):
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        return original_url


def get_strategy(suffix: str) -> SuffixStrategy:
    """Get the appropriate strategy based on the suffix.

    Args:
        suffix (str): The suffix to determine the strategy for.

    Returns:
        SuffixStrategy: The strategy to use for modifying the URL.
    """
    strategy: SuffixStrategy = DefaultStrategy()
    match suffix:
        case s if s.startswith(("http://", "https://")):
            strategy = AbsoluteUrlStrategy()
        case s if s.startswith("/"):
            strategy = PathStrategy()
        case s if s.startswith("?"):
            strategy = QueryStrategy()
        case _:
            strategy = SimpleSuffixStrategy()
        
    return strategy


def add_suffix(url: str, rules: List[Rule]) -> str:
    """Add suffix to the URL based on the rules.

    Args:
        url (str): URL to modify
        rules (List[Rule]): List of rules, where each rule is a tuple containing:
            - List[str]: List of domains to match (e.g., ["example.com", "sub.example.com"])
            - str: Suffix to add (e.g., "https://example.com/some/path")

    Returns:
        str: Modified URL with the suffix added, or the original URL if no rules match.
    """

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    for domains, suffix_str in rules:
        if any(d in host for d in domains):
            strategy = get_strategy(suffix_str)
            return strategy.apply(parsed, suffix_str, url)
    return url
