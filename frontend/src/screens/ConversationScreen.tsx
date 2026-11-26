import { type FormEvent, useEffect, useRef, useState } from "react";
import type { Api, StartSessionResponse } from "../api/client";
import { Avatar } from "../components/Avatar";
import { CATEGORY_LABELS, CorrectionCard } from "../components/CorrectionCard";
import { BackIcon, SendIcon } from "../components/Icons";
import { type ConversationState, isBusy, type PartnerMessage, sentTurns } from "../conversation/state";
import { useConversation } from "../conversation/useConversation";

const PARTNER_NAMES: Record<string, string> = { frei: "Lucía" };

interface Props {
  api: Api;
  start: StartSessionResponse | ConversationState;
  onLeave: () => void; // zurück zur Karte, Gespräch bleibt gespeichert
  onFinished: () => void; // nach der Auswertung: Gespräch verwerfen
}

export function ConversationScreen({ api, start, onLeave, onFinished }: Props) {
  const { state, send, translate, toggleTranslation, end } = useConversation(api, start);
  const [draft, setDraft] = useState("");
  const listEnd = useRef<HTMLDivElement>(null);
  const busy = isBusy(state);
  const turns = sentTurns(state);
  const { session } = state;
  const partnerName = PARTNER_NAMES[session.scenarioId] ?? session.scenarioTitle;
  const limitReached = turns >= session.maxTurns;
  const waitingForReply = state.messages.some((m) => m.kind === "user" && m.status === "sending");

  useEffect(() => {
    listEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [state.messages]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy || limitReached) return;
    setDraft("");
    void send(text);
  };

  const onTranslateClick = (message: PartnerMessage) => {
    if (message.translation.status === "done") toggleTranslation(message.id);
    else if (message.translation.status !== "loading") void translate(message.id);
  };

  if (state.summary) {
    const { summary } = state;
    return (
      <section className="screen summary">
        <h1>¡Muy bien!</h1>
        <p className="muted">
          {summary.turns} {summary.turns === 1 ? "Beitrag" : "Beiträge"} ·{" "}
          {summary.corrections.length} {summary.corrections.length === 1 ? "Korrektur" : "Korrekturen"}
        </p>
        {summary.by_category.length > 0 && (
          <div className="chip-row">
            {summary.by_category.map((c) => (
              <span key={c.category} className="chip">
                {CATEGORY_LABELS[c.category]} · {c.count}
              </span>
            ))}
          </div>
        )}
        {summary.corrections.length === 0 ? (
          <p>Keine Fehler in diesem Gespräch.</p>
        ) : (
          summary.corrections.map((c, i) => <CorrectionCard key={i} correction={c} />)
        )}
        <button type="button" className="primary-button" onClick={onFinished}>
          Zur Karte
        </button>
      </section>
    );
  }

  return (
    <section className="screen conversation">
      <header className="conversation-header">
        <button type="button" className="icon-button" onClick={onLeave} aria-label="Zur Karte">
          <BackIcon />
        </button>
        <div className="conversation-title">
          <span>
            {session.scenarioTitle} · Nivel {session.level}
          </span>
          <div
            className="progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={session.maxTurns}
            aria-valuenow={turns}
          >
            <div style={{ width: `${Math.min(100, (turns / session.maxTurns) * 100)}%` }} />
          </div>
        </div>
        <button type="button" className="text-button" onClick={() => void end()} disabled={busy}>
          {state.ending ? "…" : "Beenden"}
        </button>
      </header>

      <Avatar name={partnerName} speaking={waitingForReply} />

      <div className="messages" aria-live="polite">
        {state.messages.map((m) =>
          m.kind === "partner" ? (
            <div key={m.id} className="message partner">
              <p className="bubble">{m.text}</p>
              <button
                type="button"
                className="translate-button"
                onClick={() => onTranslateClick(m)}
                disabled={m.translation.status === "loading"}
              >
                {m.translation.status === "loading"
                  ? "übersetze …"
                  : m.translation.status === "done" && m.translation.visible
                    ? "Übersetzung ausblenden"
                    : "Auf Deutsch"}
              </button>
              {m.translation.status === "done" && m.translation.visible && (
                <div className="translation">
                  <p>{m.translation.text}</p>
                  {m.translation.keywords.length > 0 && (
                    <ul className="keywords">
                      {m.translation.keywords.map((k) => (
                        <li key={k.spanish}>
                          <strong>{k.spanish}</strong> {k.german}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              {m.translation.status === "error" && <p className="inline-error">{m.translation.message}</p>}
            </div>
          ) : (
            <div key={m.localId} className={`message user ${m.status}`}>
              <p className="bubble">{m.text}</p>
              {m.status === "sending" && <p className="status">wird gesendet …</p>}
              {m.status === "failed" && (
                <p className="inline-error">
                  {m.error}{" "}
                  <button type="button" className="link-button" onClick={() => void send(m.text, m.localId)} disabled={busy}>
                    Erneut senden
                  </button>
                </p>
              )}
              {m.corrections.map((c, i) => (
                <CorrectionCard key={i} correction={c} />
              ))}
            </div>
          ),
        )}
        {state.error && <p className="inline-error center">{state.error}</p>}
        <div ref={listEnd} />
      </div>

      <form className="composer" onSubmit={submit}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            // Am Rechner: Enter sendet, Umschalt+Enter macht eine neue Zeile
            if (e.key === "Enter" && !e.shiftKey) submit(e);
          }}
          placeholder={limitReached ? "Maximale Länge erreicht – bitte beenden" : "Escribe en español …"}
          rows={1}
          maxLength={1000}
          disabled={limitReached}
          enterKeyHint="send"
          lang="es"
          autoCapitalize="sentences"
          aria-label="Dein Beitrag"
        />
        <button
          type="submit"
          className="send-button"
          disabled={!draft.trim() || busy || limitReached}
          aria-label="Senden"
        >
          <SendIcon />
        </button>
      </form>
    </section>
  );
}
