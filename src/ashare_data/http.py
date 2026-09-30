from __future__ import annotations

import random
import threading
import time
from typing import Any

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
)


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    return session


class RateLimitedSession:
    """Thread-safe serial HTTP client for rate-sensitive public endpoints."""

    def __init__(self, min_interval: float = 2.0, max_attempts: int = 3) -> None:
        self.min_interval = float(min_interval)
        self.max_attempts = max(int(max_attempts), 1)
        self.session = make_session()
        self._lock = threading.Lock()
        self._last_call = 0.0

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_call
        wait = self.min_interval - elapsed
        if wait > 0:
            time.sleep(wait + random.uniform(0.05, 0.15))

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        with self._lock:
            last_error: Exception | None = None
            for attempt in range(self.max_attempts):
                self._wait()
                try:
                    response = self.session.request(method, url, **kwargs)
                    self._last_call = time.monotonic()
                except (requests.ConnectionError, requests.Timeout) as exc:
                    last_error = exc
                    if attempt + 1 >= self.max_attempts:
                        raise
                    time.sleep((1.5 * (2**attempt)) + random.uniform(0.2, 0.6))
                    continue

                # 403 commonly means WAF/IP throttling. Retrying immediately makes it worse.
                if response.status_code == 403:
                    response.raise_for_status()
                if response.status_code in {429, 500, 502, 503, 504} and attempt + 1 < self.max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait = float(retry_after) if retry_after else 1.5 * (2**attempt)
                    except ValueError:
                        wait = 1.5 * (2**attempt)
                    time.sleep(wait + random.uniform(0.2, 0.6))
                    continue
                response.raise_for_status()
                return response

            if last_error:
                raise last_error
            raise RuntimeError("request failed without a response")

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)
