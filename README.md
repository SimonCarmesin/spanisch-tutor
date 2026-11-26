# spanisch-tutor

Agentenbasierte Spanisch-Lern-App mit Fokus auf **Sprechen im Alltag**. Die App führt Sprechgespräche zu Alltagsszenarien, weist bei Fehlern in höchstens zwei Sätzen auf Fehler, Grund und richtige Form hin und trainiert gezielt die Schwächen des Lernenden. Zugleich ist sie ein Praxisprojekt für LLM-Anwendungen, MCP, Evals, Gateway, Docker und Kubernetes.

## Funktionen (geplant)

- **Gespräch ("Telefonieren")** zu Alltagsszenarien, zunächst nur mit Audio
- **Fehlerhinweise** in höchstens zwei Sätzen: was falsch war, warum, wie richtig
- **Zeitformen-Trainer** mit automatisch geprüften Übungen
- **Alltagssprache und Wortschatz** im Kontext, mit Wiederholungsplan aus den eigenen Fehlern
- **Lernplan-Agent**, der Niveau und Schwächen auswertet und die nächste Einheit vorschlägt
- **PWA** für die Nutzung auf dem Handy

## Services

| Service | Aufgabe |
|---|---|
| Frontend (PWA) | Bedienung, Mikrofon, Anzeige der Hinweise |
| Tutor-Service | Gesprächs- und Übungslogik, Agent, Guardrails |
| Learner-MCP-Server | Tools für Fehlerlog, Vokabeln und Lernplan |
| LiteLLM-Gateway | Einheitliche Modellschnittstelle, Rate Limits, Budgets |
| PostgreSQL mit pgvector | Lerndaten und Grammatikwissen |
| Sprach-Dienste | Sprache zu Text, Text zu Sprache |
| Langfuse | Tracing und Kosten |

## Dokumentation

- [Anforderungen und Architektur](docs/REQUIREMENTS.md)

## Status

Planung. Etappe 1 (Text-Tutor mit Gateway, Datenbank und Docker Compose) steht als Nächstes an. Offene Entscheidungen stehen in Abschnitt 10 der Anforderungen.
