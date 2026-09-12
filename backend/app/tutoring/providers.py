"""Tutor provider adapters.

Every provider-specific field lives in one adapter. The rest of the
application depends only on ``TutorProvider.complete``.

Modes:
  nvidia   - the real hosted model, used with a configured key
  authored - clearly labelled authored course help, never called a live answer
  fake     - deterministic fixtures for automated tests only
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.config import Settings


class ProviderError(Exception):
    """A provider call failed in a way the caller must handle honestly."""

    def __init__(self, reason_code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.message = message
        self.retryable = retryable


@dataclass(frozen=True)
class ProviderReply:
    raw_text: str
    provider: str
    model: str
    latency_ms: int
    usage: dict[str, Any] | None = None


class TutorProvider(Protocol):
    name: str

    def complete(self, system: str, envelope: str, question: str) -> ProviderReply: ...


class NvidiaAdapter:
    """HTTP adapter for the NVIDIA-hosted chat completions endpoint.

    The system policy, the trusted context envelope, and the learner request
    are sent as distinct messages. Learner text is never presented as a
    developer instruction.
    """

    name = "nvidia"

    def __init__(self, settings: Settings) -> None:
        if not settings.nvidia_api_key:
            raise ProviderError(
                "missing_credentials",
                "No NVIDIA API key is configured, so no live call can be made.",
            )
        self._settings = settings

    def _request_body(self, system: str, envelope: str, question: str) -> dict[str, Any]:
        return {
            "model": self._settings.nvidia_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "system", "content": envelope},
                {"role": "user", "content": question},
            ],
            "temperature": self._settings.tutor_temperature,
            "top_p": self._settings.tutor_top_p,
            "max_tokens": self._settings.tutor_max_output_tokens,
            "stream": False,
        }

    def complete(self, system: str, envelope: str, question: str) -> ProviderReply:
        url = f"{self._settings.nvidia_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._settings.nvidia_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        started = time.monotonic()
        try:
            with httpx.Client(timeout=self._settings.tutor_timeout_seconds) as client:
                response = client.post(
                    url, headers=headers, json=self._request_body(system, envelope, question)
                )
        except httpx.TimeoutException as error:
            raise ProviderError(
                "timeout",
                f"The model did not respond within "
                f"{self._settings.tutor_timeout_seconds:.0f} seconds.",
                retryable=False,
            ) from error
        except httpx.ProxyError as error:
            raise ProviderError(
                "proxy_blocked",
                "An HTTP proxy refused the connection to the provider. Check whether "
                "this network allows outbound requests to "
                f"{self._settings.nvidia_base_url}.",
            ) from error
        except httpx.ConnectError as error:
            raise ProviderError(
                "connect_error",
                "The provider host could not be reached. This is a network or DNS "
                f"failure rather than a credential problem: {error}",
            ) from error
        except httpx.HTTPError as error:
            raise ProviderError(
                "transport_error",
                f"The model could not be reached: {type(error).__name__}.",
            ) from error

        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code == 401:
            raise ProviderError("unauthorized", "The configured NVIDIA credentials were rejected.")
        if response.status_code == 429:
            raise ProviderError(
                "rate_limited",
                "The provider reported a rate or quota limit. "
                f"Retry-After: {response.headers.get('retry-after', 'not supplied')}.",
            )
        if response.status_code >= 500:
            raise ProviderError(
                "provider_unavailable", "The provider reported a server error.", retryable=True
            )
        if response.status_code != 200:
            raise ProviderError(
                "unexpected_status", f"Provider returned HTTP {response.status_code}."
            )

        try:
            payload = response.json()
            choice = payload["choices"][0]["message"]
            text = choice.get("content") or ""
        except (ValueError, KeyError, IndexError) as error:
            raise ProviderError(
                "malformed_response", "The provider response could not be read."
            ) from error

        if payload["choices"][0].get("finish_reason") == "length":
            raise ProviderError("truncated_response", "The model response reached its token limit.")
        if not text.strip():
            raise ProviderError("empty_response", "The provider returned no visible answer.")

        return ProviderReply(
            raw_text=text,
            provider=self.name,
            model=self._settings.nvidia_model,
            latency_ms=latency_ms,
            usage=payload.get("usage"),
        )

    def capability_manifest(self) -> dict[str, Any]:
        """What this adapter actually sends; recorded with smoke-test evidence."""
        return {
            "base_url": self._settings.nvidia_base_url,
            "endpoint": "POST /chat/completions",
            "model": self._settings.nvidia_model,
            "temperature": self._settings.tutor_temperature,
            "top_p": self._settings.tutor_top_p,
            "max_output_tokens": self._settings.tutor_max_output_tokens,
            "timeout_seconds": self._settings.tutor_timeout_seconds,
            "streaming": False,
            "json_schema_response_mode": "not assumed; output is parsed and validated",
            "reasoning_toggle": (
                "not sent; the hosted endpoint's accepted request syntax must be "
                "confirmed before enabling a thinking option"
            ),
        }


class FakeAdapter:
    """Deterministic fixtures for automated tests. Never a live conversation."""

    name = "fake"

    def __init__(self, scripted: dict[str, str] | None = None) -> None:
        self._scripted = scripted or {}

    def complete(self, system: str, envelope: str, question: str) -> ProviderReply:
        for key, value in self._scripted.items():
            if key.lower() in question.lower():
                return ProviderReply(
                    raw_text=value, provider=self.name, model="test-fixture", latency_ms=1
                )
        return ProviderReply(
            raw_text=(
                '{"intent": "answer", "answer_markdown": "Test fixture answer.", '
                '"passage_ids": [], "fact_ids": [], "followup_question": null}'
            ),
            provider=self.name,
            model="test-fixture",
            latency_ms=1,
        )


def build_provider(settings: Settings) -> TutorProvider | None:
    """Return the configured provider, or None for authored-only mode."""
    if settings.tutor_provider == "nvidia":
        return NvidiaAdapter(settings)
    if settings.tutor_provider == "fake":
        if settings.app_env != "test":
            raise ProviderError(
                "fake_provider_outside_tests",
                "The fake provider is only permitted when APP_ENV=test.",
            )
        return FakeAdapter()
    return None


def diagnostics(settings: Settings) -> dict[str, Any]:
    """Non-sensitive configuration diagnostic. Never echoes the key."""
    return {
        "provider": settings.tutor_provider,
        "usage_mode": settings.tutor_usage_mode,
        "model": settings.nvidia_model if settings.tutor_provider == "nvidia" else None,
        "base_url": settings.nvidia_base_url if settings.tutor_provider == "nvidia" else None,
        "key_configured": bool(settings.nvidia_api_key),
        "live_answers_available": settings.tutor_live_configured(),
        "note": (
            "Authored help is always available. A missing key never produces a "
            "simulated live answer."
        ),
    }
