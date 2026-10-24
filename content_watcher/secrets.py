"""Reading keys from the environment or Windows Credential Manager. Never printed, never logged."""

from __future__ import annotations

import os
import sys

ENGINE_TARGET = "Mindmake/engine-operator-token"
APIFY_TARGET = "Mindmake/apify-token"


def _windows_credential(target: str) -> str | None:
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
        ]

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    pointer = ctypes.POINTER(CREDENTIAL)()
    if not advapi32.CredReadW(target, 1, 0, ctypes.byref(pointer)):
        return None
    try:
        blob = ctypes.string_at(pointer.contents.CredentialBlob, pointer.contents.CredentialBlobSize)
    finally:
        advapi32.CredFree(pointer)
    for encoding in ("utf-16-le", "utf-8"):
        try:
            value = blob.decode(encoding).strip("\x00").strip()
        except UnicodeDecodeError:
            continue
        if value and value.isprintable():
            return value
    return None


def engine_token() -> str | None:
    return os.environ.get("MINDMAKE_ENGINE_TOKEN") or _windows_credential(ENGINE_TARGET)


def apify_token() -> str | None:
    return os.environ.get("APIFY_TOKEN") or _windows_credential(APIFY_TARGET)
