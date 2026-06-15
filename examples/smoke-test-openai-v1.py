#!/usr/bin/env python3
"""Minimal Azure OpenAI / OpenAI-compatible v1 smoke test.

Reads configuration from environment variables or a local .env file.
This script uses only the Python standard library.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    base_url = os.getenv("AZURE_OPENAI_BASE_URL", "").strip().rstrip("/")
    model = os.getenv("AZURE_OPENAI_MODEL", "").strip()
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    max_completion_tokens_raw = os.getenv("AZURE_OPENAI_MAX_COMPLETION_TOKENS", "1024").strip()

    if not base_url:
        print("ERROR: missing AZURE_OPENAI_BASE_URL")
        return 2
    if not model:
        print("ERROR: missing AZURE_OPENAI_MODEL")
        return 2
    if not api_key:
        print("ERROR: missing AZURE_OPENAI_API_KEY")
        return 2

    try:
        max_completion_tokens = int(max_completion_tokens_raw)
    except ValueError:
        print("ERROR: AZURE_OPENAI_MAX_COMPLETION_TOKENS must be an integer")
        return 2

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with one short sentence."},
            {"role": "user", "content": "Say exactly: endpoint operational"},
        ],
        "max_completion_tokens": max_completion_tokens,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP ERROR {exc.code}: {raw}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1

    choice = (data.get("choices") or [{}])[0]
    message = (choice.get("message") or {}).get("content", "").strip()

    print("OK: request completed")
    print(f"model: {data.get('model', model)}")
    print(f"finish_reason: {choice.get('finish_reason')}")
    print(f"reply: {message or '<no visible content>'}")
    if usage := data.get("usage"):
        print(f"usage: {usage}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
