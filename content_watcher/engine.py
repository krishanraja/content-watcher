"""The content engine's API: the only way this machine reaches the system."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from . import secrets


class EngineError(RuntimeError):
    def __init__(self, status_class: str):
        super().__init__(status_class)
        self.status_class = status_class


class Engine:
    def __init__(self, base_url: str, token: str | None = None, *, timeout: float = 60, opener=None):
        self.base_url = base_url.rstrip("/")
        self.token = token if token is not None else secrets.engine_token()
        self.timeout = timeout
        self.opener = opener or urllib.request.build_opener()

    def _post(self, path: str, body: dict) -> dict:
        if not self.token:
            raise EngineError("no_engine_key")
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"},
            method="POST",
        )
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            exc.close()
            raise EngineError({401: "engine_refused_key", 403: "engine_refused_key", 404: "engine_route_missing",
                               413: "engine_body_too_big"}.get(exc.code, f"engine_http_{exc.code}")) from None
        except (socket.timeout, TimeoutError):
            raise EngineError("engine_timeout") from None
        except urllib.error.URLError:
            raise EngineError("engine_unreachable") from None
        return json.loads(raw) if raw.strip() else {}

    def claim(self, machine: str, limit: int) -> list[dict]:
        return list(self._post("/api/watch/claim", {"machine": machine, "limit": limit}).get("requests") or [])

    def report(self, request_id: str, machine: str, status: str, **fields) -> dict:
        body = {"id": request_id, "machine": machine, "status": status}
        body.update({key: value for key, value in fields.items() if value is not None})
        return self._post("/api/watch/report", body)

    def read(self, machine: str, reads: list[dict]) -> dict:
        return self._post("/api/watch/read", {"machine": machine, "reads": reads})
