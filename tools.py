import ipaddress
import os
import socket
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2_000_000
ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml", "text/plain")


def get_tavily_client(api_key: str | None = None):
    key = api_key or os.getenv("TAVILY_API_KEY")
    if not key:
        return None
    return TavilyClient(api_key=key)


def create_web_search_tool(api_key: str | None = None):
    """Create a Tavily search tool that keeps credentials local to one caller."""

    @tool("web_search")
    def configured_web_search(query: str) -> str:
        """Search the web for recent, reliable information and return titles, URLs, and snippets."""
        tavily = get_tavily_client(api_key)
        if not tavily:
            return "Error: TAVILY_API_KEY is not configured. Please set your Tavily API key."

        try:
            results = tavily.search(query=query, max_results=5)
        except Exception:
            return "Web search is temporarily unavailable. Please try again later."

        output = []
        for result in results.get("results", []):
            output.append(
                f"Title: {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Snippet: {result.get('content', '')[:300]}\n"
            )
        return "\n----\n".join(output)

    return configured_web_search


def _validate_public_url(url: str):
    """Validate a web URL before making an outbound request."""
    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public HTTP(S) URLs are allowed.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials in URLs are not allowed.")

    try:
        port = parsed.port or (443 if scheme == "https" else 80)
    except ValueError as exc:
        raise ValueError("Invalid URL port.") from exc
    if port not in {80, 443}:
        raise ValueError("Only standard web ports are allowed.")

    try:
        address_info = socket.getaddrinfo(
            parsed.hostname,
            port,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValueError("The URL hostname could not be resolved.") from exc

    addresses = {info[4][0].split("%", 1)[0] for info in address_info}
    if not addresses:
        raise ValueError("The URL hostname could not be resolved.")

    for address in addresses:
        ip_address = ipaddress.ip_address(address)
        if isinstance(ip_address, ipaddress.IPv6Address) and ip_address.ipv4_mapped:
            ip_address = ip_address.ipv4_mapped
        if not ip_address.is_global:
            raise ValueError("Private, loopback, link-local, and reserved addresses are not allowed.")

    return parsed


def _read_limited_response(response) -> bytes:
    """Read at most MAX_RESPONSE_BYTES from a streamed response."""
    content_length = response.headers.get("Content-Length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_RESPONSE_BYTES:
        raise ValueError("The remote page is too large to scrape.")

    chunks = []
    bytes_read = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        remaining = MAX_RESPONSE_BYTES - bytes_read
        chunks.append(chunk[:remaining])
        bytes_read += min(len(chunk), remaining)
        if bytes_read >= MAX_RESPONSE_BYTES:
            break
    return b"".join(chunks)


@tool
def scrape_url(url: str) -> str:
    """Safely scrape clean text from a public HTTP(S) web page."""
    current_url = url
    try:
        for redirect_count in range(MAX_REDIRECTS + 1):
            _validate_public_url(current_url)
            with requests.get(
                current_url,
                timeout=(3.05, 8),
                headers={"User-Agent": "ResearchMind/1.0"},
                allow_redirects=False,
                stream=True,
            ) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("Location")
                    if not location or redirect_count >= MAX_REDIRECTS:
                        raise ValueError("Too many redirects while scraping the URL.")
                    current_url = urljoin(current_url, location)
                    continue

                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
                if content_type and not content_type.startswith(ALLOWED_CONTENT_TYPES):
                    return "Could not scrape URL: only HTML and plain-text pages are supported."

                content = _read_limited_response(response)
                encoding = response.encoding or "utf-8"
                try:
                    text = content.decode(encoding, errors="replace")
                except LookupError:
                    text = content.decode("utf-8", errors="replace")

                soup = BeautifulSoup(text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                return soup.get_text(separator=" ", strip=True)[:3000]

        return "Could not scrape URL safely."
    except ValueError:
        return "URL rejected: only public HTTP(S) pages on ports 80 or 443 can be scraped."
    except requests.RequestException:
        return "Could not scrape URL safely."


# Backwards-compatible default tool for callers that do not supply credentials.
web_search = create_web_search_tool()
