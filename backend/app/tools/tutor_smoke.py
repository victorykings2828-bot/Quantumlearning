"""Opt-in live provider smoke test.

Run with: uv run --frozen python -m app.tools.tutor_smoke

It reads local environment configuration, makes one real call to the configured
model, and prints only the model name, status, latency, and a non-sensitive
excerpt. It never prints credentials or private test keys, and ordinary CI does
not run it.
"""

from __future__ import annotations

import sys

from app.config import get_settings
from app.tutoring import knowledge, providers, schema
from app.tutoring.service import build_envelope, load_system_policy

QUESTION = "Why do the Z-basis probabilities stay the same after a Z gate?"


def main() -> int:
    settings = get_settings()
    report = providers.diagnostics(settings)
    print(f"provider            : {report['provider']}")
    print(f"usage mode          : {report['usage_mode']}")
    print(f"model               : {report['model']}")
    print(f"base url            : {report['base_url']}")
    print(f"credential present  : {report['key_configured']}")

    if settings.tutor_provider != "nvidia":
        print()
        print("TUTOR_PROVIDER is not 'nvidia', so no live call was attempted.")
        print("Set TUTOR_PROVIDER=nvidia and NVIDIA_API_KEY in backend/.env to test live.")
        return 2
    if not settings.nvidia_api_key:
        print()
        print("No NVIDIA_API_KEY is configured, so no live call was attempted.")
        return 2

    try:
        adapter = providers.NvidiaAdapter(settings)
    except providers.ProviderError as error:
        print(f"\nstatus              : configuration error ({error.reason_code})")
        return 1

    print()
    print("capability manifest (what this adapter actually sends):")
    for key, value in adapter.capability_manifest().items():
        print(f"  {key}: {value}")

    passages = knowledge.retrieve(QUESTION, topic_ids=None, limit=3)
    envelope = build_envelope(
        question=QUESTION,
        topic=None,
        passages=passages,
        run_facts=[],
        history=[],
        mode="practice",
        max_hint_level=1,
    )

    print()
    print(f"question            : {QUESTION}")
    try:
        reply = adapter.complete(load_system_policy(), envelope, QUESTION)
    except providers.ProviderError as error:
        print(f"status              : FAILED ({error.reason_code})")
        print(f"detail              : {error.message}")
        return 1

    outcome = schema.validate(
        reply.raw_text,
        allowed_passage_ids={passage.id for passage in passages},
        allowed_fact_ids=set(),
    )
    print("status              : HTTP 200")
    print(f"latency             : {reply.latency_ms} ms")
    print(f"served model        : {reply.model}")
    print(f"schema validation   : {'passed' if outcome.ok else 'FAILED'}")
    if not outcome.ok:
        print(f"rejection reason    : {outcome.reason_code} {outcome.detail}")
        print("The application would show authored help for this answer.")
        return 1

    answer = outcome.response.answer_markdown
    excerpt = answer if len(answer) <= 400 else answer[:400] + "..."
    print(f"intent              : {outcome.response.intent}")
    print(f"cited passages      : {', '.join(outcome.response.passage_ids) or 'none'}")
    print("answer excerpt      :")
    for line in excerpt.splitlines():
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
