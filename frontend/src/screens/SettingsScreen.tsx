import { useEffect, useState } from "react";
import { ApiError, type Api, type CefrLevel } from "../api/client";

const LEVELS: CefrLevel[] = ["A1", "A2", "B1", "B2", "C1", "C2"];

interface Props {
  api: Api;
  token: string;
  onTokenChange: (token: string) => void;
}

export function SettingsScreen({ api, token, onTokenChange }: Props) {
  const [draft, setDraft] = useState(token);
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [level, setLevel] = useState<CefrLevel | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .getProfile()
      .then((p) => setLevel(p.cefr_level))
      .catch(() => setLevel(null));
  }, [api, token]);

  const save = async () => {
    onTokenChange(draft);
    setStatus(null);
  };

  const check = async () => {
    try {
      await api.listScenarios();
      setStatus({ ok: true, text: "Verbindung steht, das Token passt." });
    } catch (e) {
      setStatus({ ok: false, text: e instanceof ApiError ? e.message : "Unbekannter Fehler" });
    }
  };

  const changeLevel = async (value: CefrLevel) => {
    setLevel(value);
    try {
      await api.updateProfile(value);
    } catch (e) {
      setStatus({ ok: false, text: e instanceof ApiError ? e.message : "Niveau nicht gespeichert" });
    }
  };

  return (
    <section className="screen settings">
      <h1>Einstellungen</h1>

      <label className="field">
        <span>API-Token</span>
        <input
          type="password"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          autoComplete="off"
          placeholder="TUTOR_API_TOKEN aus der .env"
        />
      </label>
      <div className="button-row">
        <button type="button" className="primary-button" onClick={() => void save()} disabled={draft === token}>
          Speichern
        </button>
        <button type="button" className="secondary-button" onClick={() => void check()} disabled={!token}>
          Verbindung prüfen
        </button>
      </div>
      {status && <p className={status.ok ? "inline-ok" : "inline-error"}>{status.text}</p>}

      {token && (
        <label className="field">
          <span>Mein Niveau (gilt für neue Gespräche)</span>
          <select value={level ?? ""} onChange={(e) => void changeLevel(e.target.value as CefrLevel)} disabled={!level}>
            {!level && <option value="">…</option>}
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
      )}

      <h2>Aufs Handy</h2>
      <p className="muted">
        Öffne die App im Browser deines Handys und wähle „Zum Home-Bildschirm“. Dann startet sie wie
        eine normale App.
      </p>
    </section>
  );
}
