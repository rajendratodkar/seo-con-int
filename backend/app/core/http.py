"""Shared outbound HTTP: proxy-aware client factory + connectivity probe.

Every integration gets its client from `http_client()` so custom proxies
(SCI_HTTP_PROXY / SCI_HTTPS_PROXY) apply app-wide (desktop requirement).
"""
import socket

import httpx

from app.core.config import settings

DEFAULT_TIMEOUT = 30.0


def proxy_url() -> str | None:
    """HTTPS proxy wins; http proxy is the fallback."""
    return settings.https_proxy or settings.http_proxy or None


def http_client(timeout: float = DEFAULT_TIMEOUT, **kwargs) -> httpx.AsyncClient:
    """httpx.AsyncClient that honors the configured proxy."""
    proxy = proxy_url()
    if proxy:
        kwargs["proxy"] = proxy
    return httpx.AsyncClient(timeout=timeout, **kwargs)


def check_internet(timeout: float = 2.0) -> bool:
    """Cheap connectivity probe (TCP to a public DNS port). Never raises."""
    for host in ("1.1.1.1", "8.8.8.8"):
        try:
            with socket.create_connection((host, 53), timeout=timeout):
                return True
        except OSError:
            continue
    return False
