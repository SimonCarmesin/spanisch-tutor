import { useEffect, useState } from "react";
import { ApiError, type Api, type Scenario } from "../api/client";
import { ChatIcon } from "../components/Icons";

const SCENARIO_EMOJI: Record<string, string> = {
  frei: "💬",
  cafe: "☕",
  arzt: "🩺",
  wohnung: "🏠",
  restaurant: "🍽️",
  einkaufen: "🛍️",
};

interface Props {
  api: Api;
  hasToken: boolean;
  hasOpenConversation: boolean;
  onResume: () => void;
  onStart: (scenarioId: string) => Promise<void>;
  onOpenSettings: () => void;
}

export function MapScreen({ api, hasToken, hasOpenConversation, onResume, onStart, onOpenSettings }: Props) {
  const [scenarios, setScenarios] = useState<Scenario[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState<string | null>(null);

  useEffect(() => {
    if (!hasToken) return;
    let cancelled = false;
    api
      .listScenarios()
      .then((list) => !cancelled && setScenarios(list))
      .catch((e: unknown) => !cancelled && setError(e instanceof ApiError ? e.message : "Fehler beim Laden"));
    return () => {
      cancelled = true;
    };
  }, [api, hasToken]);

  const start = async (id: string) => {
    setStarting(id);
    setError(null);
    try {
      await onStart(id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Das Gespräch konnte nicht starten.");
    } finally {
      setStarting(null);
    }
  };

  if (!hasToken) {
    return (
      <section className="screen map">
        <h1>¡Hola!</h1>
        <p>Trag zuerst dein Token in den Einstellungen ein, dann kann es losgehen.</p>
        <button type="button" className="primary-button" onClick={onOpenSettings}>
          Zu den Einstellungen
        </button>
      </section>
    );
  }

  const [free, ...others] = scenarios ?? [];
  return (
    <section className="screen map">
      <h1>¡Hola!</h1>
      <p className="muted">Worüber möchtest du heute sprechen?</p>

      {hasOpenConversation && (
        <button type="button" className="resume-card" onClick={onResume}>
          <ChatIcon /> Laufendes Gespräch fortsetzen
        </button>
      )}

      {error && <p className="inline-error">{error}</p>}
      {!scenarios && !error && <p className="muted">Lade …</p>}

      {free && (
        <button
          type="button"
          className="scenario-card featured"
          onClick={() => void start(free.id)}
          disabled={starting !== null}
        >
          <span className="scenario-emoji">{SCENARIO_EMOJI[free.id] ?? "💬"}</span>
          <span>
            <strong>{starting === free.id ? "Starte …" : free.title}</strong>
            <small>{free.description}</small>
          </span>
        </button>
      )}

      {others.length > 0 && <h2>Situationen</h2>}
      <div className="scenario-path">
        {others.map((s) => (
          <button
            key={s.id}
            type="button"
            className="scenario-card"
            onClick={() => void start(s.id)}
            disabled={starting !== null}
          >
            <span className="scenario-emoji">{SCENARIO_EMOJI[s.id] ?? "💬"}</span>
            <span>
              <strong>{starting === s.id ? "Starte …" : s.title}</strong>
              <small>{s.description}</small>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
