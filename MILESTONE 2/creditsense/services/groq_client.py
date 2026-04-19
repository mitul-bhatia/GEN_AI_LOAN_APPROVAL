from __future__ import annotations

import json
from typing import Any

import httpx

from .groq_pool import groq_pool


GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


def parse_json_response(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def chat_completion(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 800,
    expect_json: bool = False,
    timeout_seconds: float = 45.0,
) -> str:
    if not groq_pool.has_keys():
        raise RuntimeError("No Groq API keys configured.")

    last_error: Exception | None = None

    for _ in range(max(1, groq_pool.size)):
        key = groq_pool.next_key()
        if not key:
            break

        payload: dict[str, Any] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if expect_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    GROQ_BASE_URL,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

            if response.status_code == 429:
                last_error = RuntimeError("Groq rate limit reached on one key.")
                continue

            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            return content.strip()
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error:
        raise RuntimeError(f"Groq completion failed: {last_error}") from last_error
    raise RuntimeError("Groq completion failed: no API keys available.")
