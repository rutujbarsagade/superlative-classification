import unittest
from unittest.mock import Mock, patch

from tools import (
    MAX_RESPONSE_BYTES,
    _read_limited_response,
    _validate_public_url,
    create_web_search_tool,
    scrape_url,
)


def address_info(address: str, port: int = 443):
    return (2, 1, 6, "", (address, port))


class PublicUrlValidationTests(unittest.TestCase):
    def test_rejects_non_http_schemes(self):
        for url in ("file:///etc/passwd", "ftp://example.com", "not-a-url"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _validate_public_url(url)

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            _validate_public_url("https://user:password@example.com")

    def test_rejects_non_standard_ports(self):
        with self.assertRaises(ValueError):
            _validate_public_url("https://example.com:8443")

    def test_rejects_private_and_loopback_addresses(self):
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1"):
            with self.subTest(address=address), patch(
                "tools.socket.getaddrinfo",
                return_value=[address_info(address)],
            ), self.assertRaises(ValueError):
                _validate_public_url("https://example.com")

    def test_rejects_mapped_loopback_addresses(self):
        with patch(
            "tools.socket.getaddrinfo",
            return_value=[address_info("::ffff:127.0.0.1")],
        ), self.assertRaises(ValueError):
            _validate_public_url("https://example.com")

    def test_accepts_global_address(self):
        with patch(
            "tools.socket.getaddrinfo",
            return_value=[address_info("93.184.216.34")],
        ):
            parsed = _validate_public_url("https://example.com/article")
        self.assertEqual(parsed.hostname, "example.com")

    def test_scraper_rejects_local_address(self):
        with patch(
            "tools.socket.getaddrinfo",
            return_value=[address_info("127.0.0.1", 80)],
        ):
            result = scrape_url.invoke({"url": "http://localhost/admin"})
        self.assertIn("URL rejected", result)


class ResponseLimitTests(unittest.TestCase):
    def test_response_body_is_capped(self):
        response = Mock()
        response.headers = {}
        response.iter_content.return_value = [
            b"a" * MAX_RESPONSE_BYTES,
            b"b",
        ]
        content = _read_limited_response(response)
        self.assertEqual(len(content), MAX_RESPONSE_BYTES)

    def test_oversized_content_length_is_rejected(self):
        response = Mock()
        response.headers = {"Content-Length": str(MAX_RESPONSE_BYTES + 1)}
        with self.assertRaises(ValueError):
            _read_limited_response(response)


class SearchToolTests(unittest.TestCase):
    def test_search_tool_uses_its_scoped_client(self):
        client = Mock()
        client.search.return_value = {
            "results": [
                {
                    "title": "Example result",
                    "url": "https://example.com",
                    "content": "Example snippet",
                }
            ]
        }
        tool = create_web_search_tool("test-session-key")
        with patch("tools.get_tavily_client", return_value=client) as get_client:
            result = tool.invoke({"query": "example"})
        get_client.assert_called_once_with("test-session-key")
        self.assertIn("https://example.com", result)


if __name__ == "__main__":
    unittest.main()
