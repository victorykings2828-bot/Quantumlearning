"""Deterministic OpenAPI export.

Run with: uv run --frozen python export_contracts.py [--check]

The export never touches the database, runs a migration, or contacts a model
provider, so it can run in CI without any credential.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://export:export@localhost:5432/export")
os.environ.setdefault("SESSION_SECRET", "contract-export-not-a-real-secret")

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "openapi.json"


def render() -> str:
    from app.main import openapi_document

    document = openapi_document()
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the backend OpenAPI contract.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the committed contract differs from the current code.",
    )
    arguments = parser.parse_args()

    rendered = render()
    if arguments.check:
        if not CONTRACT_PATH.is_file():
            print(f"Missing contract file: {CONTRACT_PATH}")
            return 1
        if CONTRACT_PATH.read_text(encoding="utf-8") != rendered:
            print(
                "contracts/openapi.json is out of date. "
                "Run: uv run --frozen python export_contracts.py"
            )
            return 1
        print("contracts/openapi.json is up to date.")
        return 0

    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {CONTRACT_PATH} ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
