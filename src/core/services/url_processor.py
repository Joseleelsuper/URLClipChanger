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


class AmazonAffiliateStrategy(SuffixStrategy):
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        """Apply Amazon affiliate tag to URL.
        
        Handles both short (amzn.eu/d/...) and long Amazon URLs by adding the tag parameter.
        """
        # Extract the tag value from suffix (format: "?tag=affiliate-id")
        tag_value = suffix.lstrip("?").replace("tag=", "")
        
        # Parse existing query parameters
        qs: Dict[str, List[str]] = parse_qs(parsed_url.query)
        
        # Add or update the tag parameter
        qs['tag'] = [tag_value]
        
        # Rebuild the query string
        new_q = urlencode(qs, doseq=True)
        
        return urlunparse(parsed_url._replace(query=new_q))


class SimpleSuffixStrategy(SuffixStrategy):
    def apply(self, parsed_url: ParseResult, suffix: str, original_url: str) -> str:
        return original_url.rstrip("/") + suffix


def _is_amazon_url(url: str) -> bool:
    """Check if the URL is an Amazon domain."""
    amazon_domains = [
        'amazon.com', 'amazon.es', 'amazon.co.uk', 'amazon.de', 'amazon.fr',
        'amazon.it', 'amazon.ca', 'amazon.com.au', 'amazon.co.jp', 'amazon.in',
        'amzn.to', 'amzn.eu', 'a.co'
    ]
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain.startswith('www.'):
        domain = domain[4:]
    
    return any(domain == amazon_domain or domain.endswith('.' + amazon_domain) 
              for amazon_domain in amazon_domains)


def _get_strategy(suffix: str, url: str = "") -> SuffixStrategy:
    """Determine the appropriate strategy based on the suffix format and URL.

    Args:
        suffix (str): The suffix to analyze.
        url (str): The original URL to check for special handling.

    Returns:
        SuffixStrategy: The appropriate strategy instance.
    """
    # Check for Amazon affiliate links
    if _is_amazon_url(url):
        return AmazonAffiliateStrategy()
    
    if suffix.startswith(("http://", "https://")):
        return AbsoluteUrlStrategy()
    elif suffix.startswith("/"):
        return PathStrategy()
    elif suffix.startswith("?"):
        return QueryStrategy()
    
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
            strategy = _get_strategy(suffix, url)
            return strategy.apply(parsed_url, suffix, url)

    return url
