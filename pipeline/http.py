"""HTTP fetching with retry, exponential backoff and an attempt log.

Failure scenario (Part 1): a rate limit (HTTP 429), a server error or a timeout is retried
with growing waits. If every attempt fails, the caller keeps the last good load instead of
guessing, and the attempts are written to the run log.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass

import requests

USER_AGENT = "Mozilla/5.0 (compatible; BUSA3022-student-pipeline/1.0)"
RETRYABLE = {403, 429, 500, 502, 503, 504}   # 403: bot protection on cloud runners is often transient


class FetchError(Exception):
    def __init__(self, message: str, attempts: list[dict]):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class FetchResult:
    content: bytes
    url: str
    attempts: list[dict]


def _retry_after_seconds(response) -> float | None:
    value = response.headers.get("Retry-After") if response is not None else None
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def fetch(url: str, params: dict | None = None, *, timeout: float = 20, retries: int = 3,
          backoff: tuple[float, ...] = (2, 8, 30), session=None, sleep=time.sleep) -> FetchResult:
    """GET a URL; retry retryable failures; raise FetchError with the attempt log if all fail."""
    s = session or requests.Session()
    headers = {"User-Agent": USER_AGENT, "Accept": "text/csv,application/json,text/plain,*/*",
               "Accept-Language": "en-AU,en;q=0.9"}
    attempts: list[dict] = []
    for i in range(retries + 1):
        started = time.monotonic()
        wait = None
        try:
            r = s.get(url, params=params, headers=headers, timeout=timeout)
            attempts.append({"attempt": i + 1, "http_status": r.status_code,
                             "latency_ms": int((time.monotonic() - started) * 1000)})
            if r.status_code == 200 and r.content:
                return FetchResult(r.content, getattr(r, "url", url), attempts)
            if r.status_code not in RETRYABLE and r.content:
                raise FetchError(f"HTTP {r.status_code} is not retryable", attempts)
            wait = _retry_after_seconds(r)
        except requests.Timeout:
            attempts.append({"attempt": i + 1, "http_status": "timeout",
                             "latency_ms": int((time.monotonic() - started) * 1000)})
        except requests.ConnectionError:
            attempts.append({"attempt": i + 1, "http_status": "connection_error",
                             "latency_ms": int((time.monotonic() - started) * 1000)})
        if i < retries:
            base = backoff[min(i, len(backoff) - 1)]
            sleep(wait if wait is not None else base + random.uniform(0, base * 0.25))
    raise FetchError(f"gave up after {len(attempts)} attempts", attempts)
