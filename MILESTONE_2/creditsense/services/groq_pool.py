from __future__ import annotations

import os
import threading
from collections.abc import Iterable


class GroqKeyPool:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._index = 0
        self._keys = self._load_keys()

    @staticmethod
    def _dedupe(keys: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for key in keys:
            token = key.strip()
            if not token or token in seen:
                continue
            seen.add(token)
            out.append(token)
        return out

    def _load_keys(self) -> list[str]:
        env_keys = [os.getenv(f"GROQ_KEY_{idx}", "") for idx in range(1, 6)]
        api_key = os.getenv("GROQ_API_KEY", "")
        return self._dedupe([*env_keys, api_key])

    @property
    def size(self) -> int:
        return len(self._keys)

    def has_keys(self) -> bool:
        return self.size > 0

    def next_key(self) -> str | None:
        if not self._keys:
            return None
        with self._lock:
            key = self._keys[self._index % len(self._keys)]
            self._index += 1
        return key


groq_pool = GroqKeyPool()
