"""Schreibt das OpenAPI-Schema des Backends als Datei, ohne Server und ohne Datenbank.

Aufruf: cd backend && uv run python ../scripts/export-openapi.py ../frontend/openapi.json
Daraus erzeugt das Frontend seine Typen (npm run api:types).
"""

import json
import sys
from pathlib import Path

from pydantic import SecretStr

from tutor.core.config import Settings
from tutor.main import create_app

# Platzhalter: Für das Schema braucht die App keine echten Verbindungen
settings = Settings(
    database_url="sqlite+aiosqlite:///:memory:",
    llm_base_url="http://unused",
    llm_api_key=SecretStr("unused"),
    api_token=SecretStr("x" * 32),
)
schema = create_app(settings).openapi()
Path(sys.argv[1]).write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
print(f"OpenAPI-Schema geschrieben: {sys.argv[1]}")
