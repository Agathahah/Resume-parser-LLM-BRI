"""LLM clients used by the parser and a factory that picks one from environment variables.

Every client exposes ``create_response(messages, functions=None, sampling_params=None)`` and
returns a dict with the same shape as the internal BRI service:
``{"function_call": None | list, "llm_answer": str}``. ``parser.parse_file`` only depends on that.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

from parser.bri_llm import BRILargeLanguageModel


class OpenAICompatibleLLM:
    """Client for any OpenAI-compatible ``/chat/completions`` endpoint (OpenAI, Groq, Ollama, vLLM ...)."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 120.0) -> None:
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def create_response(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        sampling_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        params = sampling_params or {}
        body: Dict[str, Any] = {"model": self.model, "messages": messages}
        for key in ("temperature", "top_p", "max_tokens"):
            if key in params:
                body[key] = params[key]
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.post(self.url, json=body, headers=headers, timeout=self.timeout)
        if response.status_code != 200:
            raise RuntimeError(f"LLM API returned {response.status_code}: {response.text[:300]}")
        content = response.json()["choices"][0]["message"]["content"]
        return {"function_call": None, "llm_answer": content}


FAKE_CV = {
    "name": "Contoh Kandidat (data fiktif)",
    "email": "kandidat@example.com",
    "phone": "+62 000-0000-0000",
    "experience": [],
    "education": [],
    "skill": ["Python", "SQL"],
    "language": ["Indonesian", "English"],
}


class FakeLLM:
    """Offline stand-in that returns a fixed, fictional CV. Used for demos without an API key and in tests."""

    def __init__(self, answer: Optional[str] = None) -> None:
        self.answer = answer if answer is not None else "```json\n[" + json.dumps(FAKE_CV) + "]\n```"
        self.calls: List[List[Dict[str, str]]] = []

    def create_response(self, messages, functions=None, sampling_params=None) -> Dict[str, Any]:
        self.calls.append(messages)
        return {"function_call": None, "llm_answer": self.answer}


def build_client_from_env():
    """Pick the client from ``LLM_PROVIDER``: ``openai`` (default), ``bri`` or ``fake``."""
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider == "fake":
        return FakeLLM()
    if provider == "bri":
        return BRILargeLanguageModel(
            api_endpoint=os.environ["LLAMA_ENDPOINT"], api_key=os.environ["LLAMA_KEY"]
        )
    if provider == "openai":
        model = os.getenv("LLM_MODEL", "").strip()
        if not model:
            raise ValueError("Set LLM_MODEL to a model id your endpoint serves (see .env.example)")
        return OpenAICompatibleLLM(
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=model,
        )
    raise ValueError(f"Unknown LLM_PROVIDER={provider!r}; use openai, bri or fake")
