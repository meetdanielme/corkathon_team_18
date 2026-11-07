"""Bounded, public-only page fetching. Every hop (including redirects) must resolve to a public IP."""
from __future__ import annotations

import html
import ipaddress
import re
import socket
import urllib.request
from urllib.parse import urlparse

MAX_BYTES = 1_000_000
TIMEOUT_S = 10
USER_AGENT = "FootfallHackathonBot/0.1 (+student project; contact via repo)"


class FetchError(Exception):
    pass


def check_public(url: str) -> None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise FetchError(f"blocked scheme or host: {url}")
    try:
        infos = socket.getaddrinfo(p.hostname, None)
    except socket.gaierror as e:
        raise FetchError(f"DNS failed for {p.hostname}: {e}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise FetchError(f"blocked non-public address {ip} for {p.hostname}")


class _GuardedRedirect(urllib.request.HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_public(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def fetch_text(url: str) -> tuple[str, str]:
    """Returns (final_url, plain_text). Raises FetchError on any failure."""
    check_public(url)
    opener = urllib.request.build_opener(_GuardedRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(req, timeout=TIMEOUT_S) as r:
            body = r.read(MAX_BYTES + 1)[:MAX_BYTES]
            charset = r.headers.get_content_charset() or "utf-8"
            return r.geturl(), html_to_text(body.decode(charset, errors="replace"))
    except FetchError:
        raise
    except Exception as e:
        raise FetchError(f"{type(e).__name__}: {e}") from e
