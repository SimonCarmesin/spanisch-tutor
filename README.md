# spanisch-tutor

Agentenbasierte Spanisch-Lern-App mit Fokus auf **Sprechen im Alltag**. Die App führt Sprechgespräche zu Alltagsszenarien, weist bei Fehlern in höchstens zwei Sätzen auf Fehler, Grund und richtige Form hin und trainiert gezielt die Schwächen des Lernenden. Zugleich ist sie ein Praxisprojekt für LLM-Anwendungen, MCP, Evals, Gateway, Docker und Kubernetes.

## Funktionen

- **Gespräch** frei oder zu Alltagsszenarien, mit Übersetzung auf Abruf (Text, später Audio)
- **Satztrainer**: ganze Sätze Deutsch ↔ Spanisch, Hilfestufen, eigene Fehler als Übungsmaterial
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

- [Anforderungen](docs/REQUIREMENTS.md)
- [Architektur und Plan](docs/ARCHITECTURE.md)

## Schnellstart

```bash
make env            # fehlende Werte in .env ergänzen (AI_HUB_* selbst eintragen)
make up             # Postgres, Gateway, Migrationen und Backend starten
make frontend       # App unter http://localhost:5173 öffnen
```

In der App unter **Einstellungen** das `TUTOR_API_TOKEN` aus der `.env` eintragen.

**Aufs Handy (im selben WLAN):** `make frontend-phone` starten, dann auf dem Handy `http://<IP-des-Macs>:5173` öffnen. Die IP zeigt `ipconfig getifaddr en0`. Die Installation als App („Zum Home-Bildschirm“) mit Offline-Hülle braucht HTTPS; das kommt mit dem Deployment in Etappe 5.

## Status

Etappe 1 (Text-Tutor) läuft mit dem AI Hub. Frontend mit Gesprächsbildschirm ist vorgezogen. Als Nächstes: Satztrainer (FR-23 ff.) und Eval-Set. Details im [Plan](docs/ARCHITECTURE.md#6-plan).
