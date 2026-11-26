# Architektur und Plan

Stand: 2026-11-26. Ergänzt die [Anforderungen](REQUIREMENTS.md). Entscheidungen sind als kurze ADRs (Architecture Decision Records) festgehalten.

## 1. Serviceübersicht

```
Frontend (PWA) ──► backend (FastAPI) ──► litellm (Gateway) ──► AI Hub (Modell "gemini-3.5-flash")
                      │   └──► Sprach-Dienste (später)
                      ├──► mcp-learner (später): Tools für Lerndaten
                      └──► postgres (pgvector)
```

| Service | Port | Aufgabe | Technik | Etappe |
|---|---|---|---|---|
| `backend` | 8000 | Tutor-API: Gespräche, Korrekturen, Lerndaten, Auth | Python 3.13, FastAPI, SQLAlchemy 2 (async), Alembic | 1 |
| `litellm` | 4000 | Modell-Gateway: ein Format für alle Modelle, Limits, Budgets, Kosten | LiteLLM-Proxy | 1 |
| `postgres` | 5432 (nur lokal) | Lerndaten, später Grammatikwissen als Vektoren | PostgreSQL 17 mit pgvector | 1 |
| `migrate` | – | Einmaliger Job: Datenbankmigrationen | Alembic (Image des Backends) | 1 |
| `mcp-learner` | 8001 | Tools für Fehlerlog, Vokabeln, Lernplan, gedacht für den Agenten | Python, FastMCP | 2 |
| `frontend` | 5173 / 80 | PWA, Mikrofon, Anzeige der Hinweise | React, TypeScript | 3 bis 4 |
| `langfuse` | 3000 | Tracing und Kosten der Modellaufrufe | Langfuse | 2 bis 5 |
| Sprach-Dienste | – | Sprache zu Text, Text zu Sprache | offen (O-3) | 4 |

## 2. Entscheidungen

### ADR-1: Modularer Monolith statt Microservices für die Anwendungslogik
**Entscheidung:** Das Backend ist **ein** Dienst mit klar getrennten Modulen. Eigene Prozesse gibt es nur dort, wo ein Grund besteht: fremde Software (Gateway, Datenbank), eine eigene Rechtegrenze (MCP-Server mit Tools für den Agenten) und das Frontend.

**Begründung:**
- Ein Nutzer, ein Team: Microservices lösen Skalierungs- und Teamprobleme, die hier nicht existieren, und kosten Betrieb (Netzwerkfehler, verteilte Transaktionen, mehr Deployments).
- Saubere Modulgrenzen im Code (API, Services, Daten, LLM-Anbindung) erlauben später eine Abspaltung, falls ein Teil einen eigenen Rhythmus oder eine eigene Skalierung braucht (zum Beispiel die Sprachpipeline).
- Das entspricht der gängigen Praxis: erst modularer Monolith, dann gezielt herauslösen.

### ADR-2: Das Backend kennt nur den Modell-Alias `tutor`
Das Backend ruft immer das Modell `tutor` im Gateway auf. Das Gateway ordnet den Alias dem echten Modell zu (derzeit `gemini-3.5-flash` über den AI Hub, vorher `gpt-6-luna`). Ein Modellwechsel ist damit eine Konfigurationsänderung ohne Codeänderung, und das Eval-Set entscheidet, ob der Wechsel sicher ist.

### ADR-3: Strukturierte Ausgaben mit Validierung und einem Wiederholungsversuch
Jede Antwort des Modells besteht aus `reply` und `corrections` und wird gegen ein Schema geprüft (unter anderem: Erklärung höchstens zwei Sätze). Besteht die Ausgabe die Prüfung nicht, gibt es **einen** Wiederholungsversuch mit der Fehlermeldung als Rückmeldung. Danach bricht der Aufruf mit einem klaren Fehler ab. So erfüllt die App die Anforderung FR-6 nicht nur "meistens".

### ADR-4: Schreiben erst nach erfolgreichem Modellaufruf
Der Modellaufruf passiert **ohne** offene Datenbanktransaktion. Nachricht, Antwort und Fehlerlog werden erst danach in einer Transaktion gespeichert. Schlägt der Aufruf fehl, bleibt kein halber Zustand zurück.

### ADR-5: Migrationen als eigener Schritt
Datenbankmigrationen laufen als getrennter Job (`migrate`) und nicht beim Start des Backends. In Kubernetes wird daraus ein Job oder ein Init-Container, damit mehrere Backend-Instanzen nicht gleichzeitig migrieren.

### ADR-6: Konfiguration über Umgebungsvariablen, Geheimnisse nie im Repository
Zwölf-Faktoren-Konfiguration. Lokal liegt alles in der `.env` (ignoriert, Vorlage in `.env.example`), im Cluster kommen Geheimnisse aus Kubernetes-Secrets.

### ADR-7: Übersetzung auf Abruf statt in jedem Beitrag
**Entscheidung:** Die Übersetzung (FR-22) ist ein eigener Endpunkt mit eigenem Modellaufruf über den Alias `tutor-translate`. Das Ergebnis wird am Beitrag gespeichert (`message.translation`, `message.translation_keywords`).

**Begründung:** Eine Übersetzung in jeder Antwort würde jeden Beitrag teurer und langsamer machen (Latenz ist bereits knapp, siehe O-5) und sie würde sofort sichtbar das eigene Verstehen vorwegnehmen. Auf Abruf zahlt man nur, wenn man sie braucht. Gespeichert wird sie, damit ein zweiter Abruf ohne Modellaufruf auskommt. Der eigene Alias erlaubt später ein kleineres, schnelleres Modell nur für Übersetzungen, ohne Codeänderung. Zwei gleichzeitige erste Abrufe lösen zwei Modellaufrufe aus; das wird bewusst hingenommen (seltener Fall, Ergebnis bleibt korrekt).

## 3. Aufbau des Backends

```
backend/
  src/tutor/
    main.py            App-Fabrik, Lebenszyklus, Middleware
    domain.py          Grundbegriffe: CefrLevel, ErrorCategory, Role
    scenarios.py       Katalog der Gesprächsszenarien
    core/              Konfiguration, Logging, Sicherheit
    db/                Basisklasse, Modelle, Engine und Sessions
    llm/               Schemas (Ausgabeformat), Client, Prompts
    services/          Fachlogik: Gespräch, Profil
    api/               Router, Abhängigkeiten, Fehlerbehandlung, Health
  migrations/          Alembic
  tests/               Unit- und API-Tests
```
Abhängigkeitsrichtung: `api` → `services` → (`db`, `llm`). Services hängen vom Schnittstellentyp `LLMClient` ab, nicht von der konkreten Implementierung, und lassen sich so ohne Netz testen.

## 4. API (Etappe 1)

| Methode und Pfad | Zweck |
|---|---|
| `GET /health/live`, `GET /health/ready` | Lebendigkeits- und Bereitschaftsprüfung (Datenbank) |
| `GET /api/v1/scenarios` | Verfügbare Szenarien, an erster Stelle das freie Gespräch (`frei`) |
| `POST /api/v1/sessions` | Gespräch starten (ohne Angabe: freies Gespräch), liefert die Eröffnung des Gesprächspartners |
| `POST /api/v1/sessions/{id}/turns` | Eigenen Beitrag senden, liefert Antwort und Korrekturen |
| `POST /api/v1/sessions/{id}/end` | Gespräch beenden, liefert die Auswertung |
| `GET /api/v1/profile`, `PATCH /api/v1/profile` | Niveau und Einstellungen |
| `POST /api/v1/sessions/{id}/messages/{message_id}/translation` | Übersetzung eines Beitrags der Gegenseite ins Deutsche (FR-22). Die IDs liefern `opening_message_id` und `reply_message_id` |

Authentifizierung: statisches Bearer-Token aus der Umgebung (Einzelnutzer). Ein richtiges Anmeldeverfahren ist bei Mehrbenutzerbetrieb vorgesehen.

## 5. Qualitätsstandards

- **Typisierung:** `mypy --strict`
- **Lint und Format:** `ruff`
- **Tests:** `pytest`, Modellaufrufe in Tests gegen einen simulierten HTTP-Server, keine echten Aufrufe
- **Migrationen:** `alembic upgrade head` und `alembic check` in der CI (erkennt Abweichungen zwischen Modellen und Migration)
- **Container:** Multi-Stage-Build, Nutzer ohne Root-Rechte, feste Abhängigkeiten über `uv.lock`
- **CI:** GitHub Actions, Abhängigkeitsupdates über Dependabot
- **Datenschutz im Log:** Texte der Lernenden werden nicht geloggt, nur IDs, Dauer und Tokenzahlen

## 6. Plan

| Etappe | Inhalt | Status |
|---|---|---|
| **1** | Text-Tutor: Backend, Gateway, Datenbank, Compose, Korrekturformat, Tests, CI | fertig: 64 Tests, Compose und Gateway mit dem AI Hub getestet (2026-11-26), freies Gespräch, Übersetzung (FR-22); CI läuft beim ersten Pull Request |
| 1b | Eval-Set für das Korrekturformat und erste Qualitätsmetriken | offen |
| **2** | Lerngedächtnis: Fehlerlog auswerten, Learner-MCP-Server, Grammatik-RAG, Niveauberechnung, Langfuse | offen |
| **3** | Zeitformen-Trainer, Lernplan-Agent, Frontend (PWA) | offen |
| **4** | Sprache: Pipeline, Telefon-Modus, Netzrobustheit | offen |
| **5** | Kubernetes, Deployment per GitHub Actions, Observability, Guardrails härten | offen |

Das Gateway-Limit (Anfragen pro Minute, Budget) wird in Etappe 2 mit virtuellen Schlüsseln pro Dienst eingerichtet. Bis dahin nutzt das Backend lokal den Hauptschlüssel des Gateways.
