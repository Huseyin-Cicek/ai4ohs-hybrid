"""sitecustomize module that blocks outbound network access.

This module is injected via PYTHONPATH during the offline CI simulation to
prevent any code from opening external network connections. Loopback traffic
(127.0.0.1/::1) is still allowed so that local services may be exercised.
"""

from __future__ import annotations

import os
import socket
from functools import wraps
from typing import Any, Optional

# Hosts explicitly allowed inside the offline sandbox.
DEFAULT_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}

# Allow callers to extend the allow-list via environment variable.
EXTRA_ALLOWED = {
    host.strip() for host in os.environ.get("OFFLINE_CI_ALLOW_HOSTS", "").split(",") if host.strip()
}

ALLOWED_HOSTS = DEFAULT_ALLOWED_HOSTS.union(EXTRA_ALLOWED)

_ORIGINAL_CONNECT = socket.socket.connect
_ORIGINAL_CONNECT_EX = socket.socket.connect_ex
_ORIGINAL_CREATE_CONNECTION = socket.create_connection


def _extract_host(address: Any) -> Optional[str]:
    """Best-effort extraction of hostname/IP from a socket target."""
    if isinstance(address, str):
        return address
    if isinstance(address, (list, tuple)) and address:
        host = address[0]
        if isinstance(host, str):
            return host
    return None


def _assert_allowed(host: Optional[str]) -> None:
    """Raise if the requested host is not inside the allow-list."""
    if host is None:
        # Unable to determine host – assume outbound and block.
        raise RuntimeError(
            "Network target could not be resolved; access blocked by offline CI guard"
        )
    if host in ALLOWED_HOSTS:
        return
    raise RuntimeError(f"Network access to '{host}' blocked by offline CI simulation")


def _guard_socket_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # socket.socket.connect(self, address, ...)
        address = kwargs.get("address")
        if address is None and len(args) >= 2:
            address = args[1]
        _assert_allowed(_extract_host(address))
        return func(*args, **kwargs)

    return wrapper


def _guard_create_connection(func):
    @wraps(func)
    def wrapper(address, *args, **kwargs):
        _assert_allowed(_extract_host(address))
        return func(address, *args, **kwargs)

    return wrapper


socket.socket.connect = _guard_socket_call(_ORIGINAL_CONNECT)  # type: ignore[assignment]
socket.socket.connect_ex = _guard_socket_call(_ORIGINAL_CONNECT_EX)  # type: ignore[assignment]
socket.create_connection = _guard_create_connection(_ORIGINAL_CREATE_CONNECTION)  # type: ignore[assignment]

# Optionally block the use of getaddrinfo for remote hosts by wrapping it.
_ORIGINAL_GETADDRINFO = socket.getaddrinfo


def _guard_getaddrinfo(host: Optional[str], *args, **kwargs):
    if host is not None:
        _assert_allowed(host)
    return _ORIGINAL_GETADDRINFO(host, *args, **kwargs)


socket.getaddrinfo = _guard_getaddrinfo  # type: ignore[assignment]


def __getattr__(name: str) -> Any:  # pragma: no cover - defensive access
    """Expose original socket helpers if someone reaches into sitecustomize."""
    if name == "ALLOWED_HOSTS":
        return ALLOWED_HOSTS
    raise AttributeError(name)
