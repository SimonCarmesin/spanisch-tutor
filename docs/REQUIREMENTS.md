# Anforderungen: Spanisch-Tutor

Stand: 2026-11-26 · Status: Entwurf (wird mit dem Projekt fortgeschrieben)

## 1. Ziel und Motivation

Eine eigene, agentenbasierte App, mit der ich **Spanisch sprechen lerne**. Duolingo vermittelt vor allem Wörter, hilft mir aber kaum beim Sprechen im Alltag. Die App soll mich in realistischen Situationen sprechen lassen, meine Fehler erkennen und mich gezielt dort trainieren, wo ich schwach bin.

Das Projekt hat ein zweites Ziel: Es ist ein **Praxisprojekt für KI-Entwicklung** (LLM-Anwendungen, RAG, Agenten mit Tools, MCP, Evals, Gateway, Guardrails, Docker, Kubernetes, CI/CD). Ich nutze die App danach selbst weiter.

## 2. Nutzer und Nutzung

- Einziger Nutzer zu Beginn: ich selbst. Mehrere Nutzer sind kein Ziel der ersten Etappen, die Datenstruktur soll es aber nicht verbauen (Nutzer-ID in allen Tabellen).
- Nutzung vor allem **mobil unterwegs** (zum Beispiel in der Bahn), daneben am Rechner.
- Unterrichtssprache der Erklärungen: Deutsch. Gesprochen und geübt wird Spanisch.
- Das Modell läuft über den **AI Hub meines Arbeitgebers** (private Nutzung ist erlaubt). Das Gateway muss so gebaut sein, dass auch andere Modelle oder Anbieter angebunden werden können.

## 3. Funktionale Anforderungen

### 3.1 Gespräch ("Telefonieren")
- **FR-1** Ich führe Sprechgespräche. Standard ist das **freie Gespräch**: Ich spreche über ein Thema meiner Wahl, nenne ich keins, schlägt die Gegenseite eines vor. Zusätzlich gibt es wählbare Alltagsszenarien (zum Beispiel Café, Arzt, Wohnungssuche, Restaurant, Einkauf) mit vorgegebener Rolle und vorgegebenem Ton.
- **FR-2** Das Gespräch läuft zunächst **nur mit Audio** (Stimme, keine Videofigur). Ein Text-Modus ist als Rückfalloption und für die Entwicklung vorhanden.
- **FR-3** Das Sprachniveau der Gegenseite richtet sich nach meinem gespeicherten Niveau (CEFR A1 bis C2) und lässt sich überschreiben.
- **FR-4** Das Gespräch hat Grenzen: Rolle halten, maximale Länge pro Gespräch. In Szenarien bleibt das Gespräch beim Szenario. Im freien Gespräch ist das Thema frei, die Gegenseite bleibt aber Gesprächspartner einer Sprachübung und übernimmt keine anderen Aufgaben (zum Beispiel Programmcode, Hausaufgaben, lange Texte).
- **FR-22** Verstehe ich einen Beitrag der Gegenseite nicht, kann ich ihn mir **ins Deutsche übersetzen** lassen. Die Übersetzung gibt es nur auf Abruf (sie wird nicht automatisch angezeigt, damit ich zuerst selbst verstehe), sie gilt für einen bestimmten Beitrag und wird gespeichert, damit ein erneuter Abruf nichts kostet. Optional nennt sie bis zu drei Schlüsselwörter mit Übersetzung, die in den Wortschatz übernommen werden können (FR-13).
- **FR-5** Am Ende des Gesprächs gibt es eine **Auswertung**: Fehlerliste, bessere Formulierungen, neue Wörter. Alles wird gespeichert (siehe 5).

### 3.2 Fehlerhinweise (zentrale Anforderung)
- **FR-6** Mache ich im Sprechen oder in einer Übung einen Fehler, bekomme ich einen Hinweis in **höchstens zwei Sätzen**, der enthält: (a) was falsch war, (b) warum, (c) wie es richtig wäre.
- **FR-7** Der Zeitpunkt des Hinweises ist konfigurierbar: sofort nach meinem Beitrag oder gesammelt am Ende. Voreinstellung: in Übungen sofort, im Gespräch kurz nach meinem Beitrag, ohne den Redefluss zu stören (siehe offene Entscheidung O-4).
- **FR-8** Hinweise werden als strukturierte Daten erzeugt (nicht als freier Text) und automatisch geprüft (Länge, Vollständigkeit).
- **FR-9** Jeder Fehler wird mit Kategorie (zum Beispiel "pretérito indefinido"), Originalsatz, Korrektur, Begründung und Datum im Fehlerlog gespeichert.

Beispiel für das Datenformat eines Hinweises:
```json
{
  "original": "Ayer yo voy al mercado.",
  "corrected": "Ayer fui al mercado.",
  "category": "pretérito indefinido",
  "explanation": "Für abgeschlossene Handlungen in der Vergangenheit brauchst du das pretérito indefinido, nicht das Präsens. Von 'ir' heißt es 'fui'."
}
```

### 3.3 Zeitformen-Trainer
- **FR-10** Gezielte Übungen zu Zeitformen (Präsens, pretérito indefinido, imperfecto, perfecto, futuro, subjuntivo und weitere nach Bedarf).
- **FR-11** Übungen werden erzeugt und **soweit möglich per Code geprüft** (zum Beispiel Konjugation gegen Regeln und Ausnahmelisten). Freie Antworten bewertet ein Modell.
- **FR-12** Grammatikregeln werden aus einer Wissensbasis per Retrieval (RAG) erklärt.

### 3.4 Alltagssprache und Wortschatz
- **FR-13** Redewendungen und Wortschatz nach Situationen, im Kontext statt als Einzelvokabeln.
- **FR-14** Wiederholungsplan: Wörter und Fehler kommen nach einem Zeitplan wieder (Spaced Repetition), gespeist aus meinen eigenen Fehlern.

### 3.5 Lernplan-Agent
- **FR-15** Ein Agent wertet Fehlerlog, Niveau und Verlauf aus und schlägt die nächste Einheit vor (Szenario, Übungen, Wiederholungen).
- **FR-16** Der Agent nutzt dafür Tools (siehe MCP-Server in 4) und begründet seinen Vorschlag kurz.

### 3.6 Niveau und Gedächtnis
- **FR-17** Mein Niveau ergibt sich aus Ergebnissen und Fehlern und wird nicht vom Modell geraten. Es wird regelmäßig neu berechnet und ist einsehbar.
- **FR-18** Die App kennt meine Schwächen (häufige Fehlerkategorien) und gewichtet damit Übungen und Gesprächsthemen.

### 3.7 Frontend
- **FR-19** Webanwendung als **PWA**: auf dem Handy installierbar, Mikrofonzugriff, für Touch-Bedienung ausgelegt. **Hauptgerät ist das Smartphone**: Das Layout wird zuerst für schmale Bildschirme entworfen, große Bildschirme sind zweitrangig. Für die Nutzung unterwegs muss das Backend aus dem Internet erreichbar sein (Etappe 5); bis dahin im Heimnetz.
- **FR-20** Bildschirme: Start (Empfehlung des Lernplans), Gespräch, Übungen, Fehlerübersicht und Verlauf, Einstellungen.
- **FR-21** Bei schlechtem Netz (zum Beispiel in der Bahn) bricht die App nicht ab: verständliche Meldung, automatischer Wiederaufbau, bereits Gesagtes geht nicht verloren.

### 3.8 Satztrainer und weitere Lerntechniken

Leitidee: Ich lerne ganze Sätze, indem ich sie **selbst bilde**, statt sie wiederzuerkennen. Aktives Abrufen, ein angemessener Schwierigkeitsgrad und Wiederholung im Abstand wirken nachweislich besser als Wiedererkennen (Multiple Choice) und reines Lesen.

- **FR-23 Satz-Übersetzungstrainer:** Die App gibt mir vollständige, natürliche Alltagssätze in meinem Niveau. Ich übersetze sie frei in Richtung **Spanisch → Deutsch** oder **Deutsch → Spanisch** (wählbar, Standard: Deutsch → Spanisch, weil das Sprechen trainiert). Da mehrere Übersetzungen richtig sein können, bewertet ein Modell die Antwort (richtig, fast richtig, falsch) und liefert eine Musterlösung. Fehler bekomme ich im Format aus FR-6, und sie landen im Fehlerlog (FR-9).
- **FR-24 Rückübersetzung:** Einen Satz, den ich von Spanisch nach Deutsch übersetzt habe, bekomme ich später auf Deutsch zurück und baue daraus wieder den spanischen Satz. Verglichen wird mit dem Original.
- **FR-25 Hilfestufen statt Lösung (Glühbirne):** Wenn ich nicht weiterkomme, gibt es Hilfe in Stufen: (1) ein Hinweis, etwa die benötigte Zeitform oder ein Schlüsselwort, (2) der Satzanfang, (3) die Lösung. Das gilt im Satztrainer und im Gespräch („Was könnte ich jetzt sagen?“). Genutzte Hilfe fließt in Bewertung und Wiederholungsplan ein.
- **FR-26 Satzbausteine:** Häufige Satzrahmen (zum Beispiel „Me gustaría …“, „¿Podrías …?“, „Lo que pasa es que …“) werden gezielt geübt, indem ich sie in eigenen Sätzen verwende. Sie gehören zum Wortschatz (FR-13).
- **FR-27 Eigene Fehler als Übungsmaterial:** Sätze aus meinem Fehlerlog kommen im Satztrainer wieder, nach dem Wiederholungsplan (FR-14). Im Design: „Fehler-Training starten“.
- **FR-28 Umformen:** Ein Satz soll in eine andere Zeitform oder Person umgeformt werden (zum Beispiel Präsens → pretérito indefinido). Verbindet den Satztrainer mit dem Zeitformen-Trainer (FR-10).
- **FR-29 Nachsprechen (Shadowing, ab Etappe 4):** Einen Satz anhören und sofort nachsprechen. Das Transkript wird mit dem Original verglichen.

## 4. Services und Architektur

```
Frontend (PWA) ──► Tutor-Service ──► LiteLLM-Gateway ──► AI Hub (später auch andere Modelle)
                       │   └──► Sprach-Dienste (Sprache-zu-Text, Text-zu-Sprache)
                       ├──► Learner-MCP-Server (Vokabeln, Fehlerlog, Lernplan)
                       └──► PostgreSQL + pgvector
Querschnitt: Langfuse (Tracing), GitHub Actions (CI/CD), Kubernetes (Betrieb)
```

| Service | Aufgabe | Technik |
|---|---|---|
| **Frontend** | PWA, Mikrofon, Anzeige der Hinweise | React (TypeScript), Vite oder Next.js |
| **Tutor-Service** | Gesprächs- und Übungslogik, Agent, Guardrails, Korrekturformat | Stack offen (O-1): Python oder Java mit Spring AI |
| **Learner-MCP-Server** | Tools für Lerndaten (Fehlerlog lesen und schreiben, Vokabeln, Lernplan) | Python, FastMCP, Streamable HTTP |
| **LiteLLM-Gateway** | Einheitliche Modellschnittstelle, Rate Limits, Budgets, Fallbacks, Kosten | LiteLLM-Proxy |
| **Datenbank** | Profil, Fehlerlog, Vokabeln, Protokolle, Grammatikwissen als Vektoren | PostgreSQL mit pgvector |
| **Sprach-Dienste** | Sprache zu Text und Text zu Sprache | Anbieter offen (O-3) |
| **Observability** | Nachvollziehbarkeit jedes Aufrufs, Kosten, Latenz | Langfuse, optional OpenTelemetry |

Entwurfsentscheidungen:
- **Sprache als Pipeline** (Sprache zu Text, Sprachmodell, Text zu Sprache) statt Speech-zu-Speech, damit Transkripte für Korrektur, Evals und Guardrails vorliegen.
- **Tools nur dort über MCP**, wo mehrere Systeme sie nutzen können (Lerndaten). Reine Interna des Tutor-Service bleiben normale Funktionen.
- **Zugriffsrechte am Server**: Der MCP-Server liefert pro Client nur die erlaubten Tools. Der Client filtert zusätzlich, um Kontext zu sparen.
- **Gesprächsprotokolle nur als Text**, kein Audio dauerhaft speichern.

## 5. Datenmodell (Entwurf)

| Tabelle | Inhalt |
|---|---|
| `learner_profile` | Nutzer-ID, Niveau, Ziele, Präferenzen (Hinweis-Zeitpunkt, Tempo), Zeitplan |
| `error_log` | Kategorie, Originalsatz, Korrektur, Begründung, Datum, Häufigkeit, Beherrschungsgrad |
| `vocabulary` | Wort oder Wendung, Beispiel, Situation, Wiederholungsplan (nächster Termin, Intervall) |
| `session` / `message` | Gespräche und Übungen als Text-Protokoll, Szenario, Niveau, Ergebnis |
| `grammar_chunk` | Grammatikregeln mit Vektor-Embedding (RAG) |
| `lesson_plan` | Vorschläge des Lernplan-Agenten und deren Ergebnis |

## 6. Nicht-funktionale Anforderungen

### 6.1 Sicherheit, Guardrails, Rate Limits
- **NFR-1** Rate Limits und Budgets pro Nutzer und Schlüssel im Gateway, zusätzlich Grenzen in der Anwendung (Anfragen pro Minute, maximale Gesprächslänge, Tageslimit).
- **NFR-2** Guardrails: Rolle und Niveau halten, Themengrenzen, Schutz vor Prompt Injection (Transkripte und Dokumente gelten als nicht vertrauenswürdig), keine Weitergabe von Geheimnissen oder Systemanweisungen.
- **NFR-3** Minimale Rechte: Werkzeuge schreiben nur in die Lerndaten, keine weiteren Aktionen.
- **NFR-4** Geheimnisse (API-Schlüssel, Datenbankpasswörter) nie im Repository, sondern per Umgebungsvariablen und im Cluster per Secrets.

### 6.2 Datenschutz
- **NFR-5** Persönliche Lerndaten bleiben in meiner eigenen Datenbank. Kein Audio dauerhaft speichern.
- **NFR-6** Nutzung des AI Hubs gemäß der erlaubten privaten Nutzung. Keine Firmendaten im Projekt.

### 6.3 Qualität und Evals
- **NFR-7** Ein **Eval-Set** (zunächst 30 bis 50 Fälle) prüft automatisch:
  - Format und Länge der Fehlerhinweise (höchstens zwei Sätze, alle Teile vorhanden)
  - Korrektheit der Konjugation und Korrekturen (soweit per Code prüfbar)
  - Treue zum Niveau (zum Beispiel per Modell als Richter, kalibriert an eigenen Beispielen)
  - Verhalten bei Angriffsversuchen (Prompt Injection) und bei Fragen außerhalb des Themas
- **NFR-8** Die Evals laufen in der CI-Pipeline. Fallen Kennzahlen unter eine Schwelle, schlägt der Build fehl.
- **NFR-9** Eigene Gesprächsdaten und echte Fehler fließen laufend als neue Testfälle in das Eval-Set ein.

### 6.4 Leistung und Kosten
- **NFR-10** Gesprächsfluss: Zielwert für die Zeit vom Ende meiner Äußerung bis zum Beginn der Antwort wird nach den ersten Messungen festgelegt (Richtwert unter drei Sekunden).
- **NFR-11** Kosten pro Gespräch und pro Tag werden erfasst und begrenzt.

### 6.5 Betrieb
- **NFR-12** Alle Services laufen in Containern. Lokale Entwicklung mit Docker Compose.
- **NFR-13** Tracing jedes Modellaufrufs (Eingabe, Abruf, Tool-Aufrufe, Antwort, Tokens, Kosten, Latenz).
- **NFR-14** Konfiguration (Modelle, Prompts, Schwellen) liegt versioniert im Repository.

## 7. Bereitstellung

1. **Lokal:** Docker Compose mit allen Services.
2. **Lokaler Cluster:** Kubernetes (zum Beispiel kind) mit Manifesten oder Helm/Kustomize.
3. **Produktiv:** Deployment per **GitHub Actions** auf einen echten Kubernetes-Cluster (Ziel offen, O-2). Pipeline: Build, Tests, Evals, Container-Images, Deployment.
4. Ziel dabei: Kubernetes einmal wirklich produktiv aufsetzen und betreiben, nicht nur lokal ausprobieren.

## 8. Etappen

1. **Text-Tutor:** Tutor-Service, Gateway, Datenbank, Compose, erste Szenarien, Fehlerhinweise im Datenformat, erstes Eval-Set.
2. **Gedächtnis und Qualität:** Fehlerlog, Learner-MCP-Server, Grammatik-RAG, Niveau-Berechnung, Evals in der CI.
3. **Frontend (PWA), Satztrainer (FR-23 bis FR-28), Zeitformen-Trainer und Lernplan-Agent.** Das Frontend wird vorgezogen, damit ich die App früh selbst benutze und echte Fälle für das Eval-Set entstehen.
4. **Sprache:** Sprachpipeline, Telefon-Modus, mobile Bedienung, Netz-Robustheit.
5. **Kubernetes, CI/CD, Observability, Guardrails härten.**

Die Etappen 1 und 2 sowie ein Teil von 5 (Docker, CI, Gateway, Evals) liefern das, was für die Vorbereitung auf die KI-Entwickler-Stellen am meisten zählt.

## 9. Backlog

- Visueller **Avatar** mit Lippenbewegung
- **Speech-zu-Speech** (Echtzeit-Sprachmodell) als Alternative zur Pipeline
- **Decision API** testen (Bedeutung noch zu klären)
- Mehrbenutzerbetrieb mit Anmeldung

## 10. Offene Entscheidungen

| Nr. | Frage | Stand |
|---|---|---|
| O-1 | Stack des Tutor-Service: Python (schneller für MVP und Sprache) oder Java mit Spring AI (passt zu den Stellenanforderungen) oder aufgeteilt | offen |
| O-2 | Ziel-Cluster für Produktiv: AKS, GKE oder k3s auf einem kleinen Server | offen |
| O-3 | Anbieter für Sprache zu Text und Text zu Sprache, und ob der AI Hub Audio-Endpunkte anbietet | offen |
| O-4 | Zeitpunkt der Fehlerhinweise im Gespräch (sofort oder gesammelt) | Voreinstellung siehe FR-7 |
| O-5 | Welche Modelle stellt der AI Hub bereit, und wie sehen Endpunkt und Authentifizierung aus | entschieden 2026-11-26: OpenAI-kompatibler Endpunkt mit `/v1`, Authentifizierung per Bearer-Schlüssel, Modellliste über `GET /v1/models`. Gewähltes Modell: `gemini-3.5-flash`. Embedding-Modelle für RAG vorhanden (zum Beispiel `text-embedding-3-large`). Erste Messung mit `gpt-6-luna`: rund 3,8 s bis zum ersten Token |

## 11. Technische Lernziele des Projekts

- RAG mit Hybrid Search und Reranking, Rechtefilter, Chunking
- Agenten mit Tool Calling und MCP (Server und Client), Abwägung Workflow gegen Agent
- Evals und LLMOps: Eval-Set, Richter-Modelle, Regressionstests in der CI, Tracing, Kostenkontrolle
- Gateway-Betrieb: Rate Limits, Budgets, Fallbacks
- Guardrails und Schutz vor Prompt Injection
- Sprachpipeline mit Streaming und Latenzmessung
- Docker, Kubernetes, GitHub Actions
