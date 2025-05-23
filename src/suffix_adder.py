from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import List, Tuple, Dict

Rule = Tuple[List[str], str]


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
    for domains, suffix in rules:
        if any(d in host for d in domains):
            if suffix.startswith(("http://", "https://")):
                return suffix
            if suffix.startswith("/"):
                new_path = parsed.path.rstrip("/") + suffix
                return urlunparse(parsed._replace(path=new_path))
            if suffix.startswith("?"):
                qs: Dict[str, List[str]] = parse_qs(parsed.query)
                for param in suffix.lstrip("?").split("&"):
                    k, v = param.split("=", 1)
                    qs[k] = [v]
                new_q = urlencode(qs, doseq=True)
                return urlunparse(parsed._replace(query=new_q))
            return url.rstrip("/") + suffix
    return url
