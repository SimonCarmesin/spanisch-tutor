/** Einstellungen im Gerät. Das Token liegt im lokalen Speicher: für den Einzelnutzerbetrieb
 * vertretbar, bei Mehrbenutzerbetrieb wird daraus eine richtige Anmeldung (Backlog). */
import { useCallback, useState } from "react";

const TOKEN_KEY = "tutor.apiToken";

function read(key: string): string {
  try {
    return localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

export function useToken(): [string, (value: string) => void] {
  const [token, setTokenState] = useState(() => read(TOKEN_KEY));
  const setToken = useCallback((value: string) => {
    const trimmed = value.trim();
    try {
      localStorage.setItem(TOKEN_KEY, trimmed);
    } catch {
      // ohne Speicher gilt das Token nur bis zum Neuladen
    }
    setTokenState(trimmed);
  }, []);
  return [token, setToken];
}
