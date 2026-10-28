"""The content engine's API: the only way this machine reaches the system."""

from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request

from . import secrets


def _opener():
    """An opener that checks the engine's certificate against the operating system's own store (truststore) when
    it is installed, so a Windows machine trusts what its browser and PowerShell trust; else Python's default."""
    try:
        import truststore

        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:  # noqa: BLE001 - not installed yet, or an old Python: the default opener still works
        return urllib.request.build_opener()
    return urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))


def unreachable_class(reason: object) -> str:
    """Why the engine could not be reached, as a class the log and the engine's health report can carry. Krish,
    2026-10-28, after pasting this machine's log: "engine_unreachable" alone told nobody what to fix."""
    if isinstance(reason, ssl.SSLCertVerificationError):
        return "engine_tls_untrusted"
    if isinstance(reason, ssl.SSLError):
        return "engine_tls_error"
    if isinstance(reason, socket.gaierror):
        return "engine_dns_failed"
    if isinstance(reason, (socket.timeout, TimeoutError)) or getattr(reason, "winerror", None) == 10060:
        return "engine_timeout"
    if isinstance(reason, PermissionError) or getattr(reason, "winerror", None) == 10013:
        return "engine_blocked"
    if isinstance(reason, ConnectionRefusedError):
        return "engine_connection_refused"
    if isinstance(reason, (ConnectionResetError, ConnectionAbortedError)):
        return "engine_connection_reset"
    if isinstance(reason, str) and "proxy" in reason.lower():
        return "engine_proxy"
    return "engine_unreachable"


class EngineError(RuntimeError):
    def __init__(self, status_class: str):
        super().__init__(status_class)
        self.status_class = status_class


class Engine:
    def __init__(self, base_url: str, token: str | None = None, *, timeout: float = 60, opener=None):
        self.base_url = base_url.rstrip("/")
        self.token = token if token is not None else secrets.engine_token()
        self.timeout = timeout
        self.opener = opener or _opener()

    def _post(self, path: str, body: dict, *, timeout: float | None = None) -> dict:
        if not self.token:
            raise EngineError("no_engine_key")
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"},
            method="POST",
        )
        try:
            with self.opener.open(request, timeout=timeout or self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            exc.close()
            raise EngineError({401: "engine_refused_key", 403: "engine_refused_key", 404: "engine_route_missing",
                               413: "engine_body_too_big"}.get(exc.code, f"engine_http_{exc.code}")) from None
        except (socket.timeout, TimeoutError):
            raise EngineError("engine_timeout") from None
        except urllib.error.URLError as exc:
            raise EngineError(unreachable_class(exc.reason)) from None
        except (ssl.SSLError, ConnectionError) as exc:
            raise EngineError(unreachable_class(exc)) from None
        return json.loads(raw) if raw.strip() else {}

    def claim(self, machine: str, limit: int) -> list[dict]:
        return list(self._post("/api/watch/claim", {"machine": machine, "limit": limit}).get("requests") or [])

    def report(self, request_id: str, machine: str, status: str, **fields) -> dict:
        body = {"id": request_id, "machine": machine, "status": status}
        body.update({key: value for key, value in fields.items() if value is not None})
        return self._post("/api/watch/report", body)

    def read(self, machine: str, reads: list[dict]) -> dict:
        return self._post("/api/watch/read", {"machine": machine, "reads": reads})

    def held(self, machine: str, shas: list[str]) -> dict[str, str]:
        """Which of these media the engine already holds a reading of, with that reading's engine_rev."""
        held = self._post("/api/watch/read", {"machine": machine, "check": shas}).get("held")
        return {str(sha): str(rev) for sha, rev in held.items()} if isinstance(held, dict) else {}

    def apify(self, request_id: str, machine: str, actor: str, payload: dict) -> list[dict]:
        """The cloud backup's paid step: the engine runs the actor with its own key, for this machine's claimed
        request only (content-engine api/watch/apify.ts), and answers the dataset's first items."""
        answer = self._post("/api/watch/apify", {"id": request_id, "machine": machine, "actor": actor,
                                                 "input": payload}, timeout=300)
        items = answer.get("items")
        return items if isinstance(items, list) else []

    def upload(self, request_id: str, machine: str, *, folder: str, name: str, sha256: str, size: int, mime: str) -> dict:
        """The cloud backup's filing: the engine opens a Drive upload session in the lane's folder, as Krish, or says
        the same bytes are already there (content-engine api/watch/upload.ts)."""
        return self._post("/api/watch/upload", {"id": request_id, "machine": machine, "folder": folder, "name": name,
                                                "sha256": sha256, "bytes": size, "mime": mime})


def put_upload(url: str, path, mime: str, *, timeout: float = 600, opener=None) -> dict:
    """Send a file's bytes to the Drive upload session the engine opened. Google answers the new file's name, size
    and sha256. The session URL is the only authority; no key travels with it."""
    opener = opener or urllib.request.build_opener()
    with open(path, "rb") as handle:
        request = urllib.request.Request(url, data=handle, method="PUT", headers={
            "Content-Type": mime, "Content-Length": str(path.stat().st_size)})
        try:
            with opener.open(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            exc.close()
            raise EngineError(f"drive_upload_http_{exc.code}") from None
        except (socket.timeout, TimeoutError):
            raise EngineError("drive_upload_timeout") from None
        except (urllib.error.URLError, ssl.SSLError, ConnectionError):
            raise EngineError("drive_upload_unreachable") from None
    return json.loads(raw) if raw.strip() else {}
