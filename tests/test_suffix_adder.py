import unittest
from src.suffix_adder import add_suffix

# Conjunto de reglas para tests
RULES = [
    (["example.com"], "?ref=123"),
    (["path.test"], "/promo/456"),
    (["full.url"], "https://override.test/xyz"),
    (["fallback.test"], "-suffix"),
]


class TestAddSuffix(unittest.TestCase):
    # Query suffix: sin parámetros previos
    def test_query_suffix_no_existing(self):
        url = "https://example.com/page"
        expected = "https://example.com/page?ref=123"
        self.assertEqual(add_suffix(url, RULES), expected)

    # Query suffix: con parámetros previos
    def test_query_suffix_with_existing(self):
        url = "https://example.com/page?foo=bar"
        expected = "https://example.com/page?foo=bar&ref=123"
        self.assertEqual(add_suffix(url, RULES), expected)

    # Path suffix: URL sin barra final
    def test_path_suffix_without_trailing_slash(self):
        url = "http://path.test/dir"
        expected = "http://path.test/dir/promo/456"
        self.assertEqual(add_suffix(url, RULES), expected)

    # Path suffix: URL con barra final
    def test_path_suffix_with_trailing_slash(self):
        url = "http://path.test/dir/"
        expected = "http://path.test/dir/promo/456"
        self.assertEqual(add_suffix(url, RULES), expected)

    # Full URL override: siempre devuelve la URL completa
    def test_full_url_override(self):
        url = "https://full.url/anything?param=1"
        expected = "https://override.test/xyz"
        self.assertEqual(add_suffix(url, RULES), expected)

    # Fallback suffix: concatenación simple
    def test_fallback_suffix(self):
        url = "https://fallback.test/page"
        expected = "https://fallback.test/page-suffix"
        self.assertEqual(add_suffix(url, RULES), expected)

    # Dominio no reconocido: sin cambios
    def test_unknown_domain(self):
        url = "https://unknown.com/path"
        self.assertEqual(add_suffix(url, RULES), url)

    # URL no http/https
    def test_non_http_url(self):
        url = "ftp://example.com/file"
        expected = "ftp://example.com/file?ref=123"
        self.assertEqual(add_suffix(url, RULES), expected)

    # Query suffix: con parámetro vacío
    def test_query_suffix_empty_query(self):
        url = "https://example.com/page?"
        expected = "https://example.com/page?ref=123"
        self.assertEqual(add_suffix(url, RULES), expected)


if __name__ == "__main__":
    unittest.main()
