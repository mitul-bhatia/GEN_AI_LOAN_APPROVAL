from __future__ import annotations

import os
from typing import Any

import httpx


DEFAULT_BACKEND_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8010")


def _full_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def health(base_url: str = DEFAULT_BACKEND_URL) -> dict[str, Any]:
    url = _full_url(base_url, "/api/v1/health")
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def fetch_initial_state(base_url: str = DEFAULT_BACKEND_URL) -> dict[str, Any]:
    url = _full_url(base_url, "/api/v1/agent/state/initial")
    with httpx.Client(timeout=20.0) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    state = payload.get("state")
    if not isinstance(state, dict):
        raise RuntimeError("Backend did not return a valid initial state")
    return state


def run_turn(
    *,
    user_message: str,
    state: dict[str, Any],
    base_url: str = DEFAULT_BACKEND_URL,
) -> dict[str, Any]:
    url = _full_url(base_url, "/api/v1/agent/turn")
    payload = {"user_message": user_message, "state": state}

    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def seed_parameters(
    *,
    parameters: dict[str, Any],
    state: dict[str, Any],
    base_url: str = DEFAULT_BACKEND_URL,
) -> dict[str, Any]:
    url = _full_url(base_url, "/api/v1/agent/seed-parameters")
    payload = {"parameters": parameters, "state": state}

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
