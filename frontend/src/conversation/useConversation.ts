/**
 * Verbindet den Reducer mit der API und speichert das laufende Gespräch im Gerät.
 * Auf dem Handy beendet das System Apps im Hintergrund; nach dem Neustart geht es weiter.
 */
import { useCallback, useEffect, useReducer } from "react";
import { ApiError, type Api, type StartSessionResponse } from "../api/client";
import { type ConversationState, initialState, reducer } from "./state";

const STORAGE_KEY = "tutor.conversation.v1"; // Version im Schlüssel: altes Format wird ignoriert

export function loadSavedConversation(): ConversationState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const state = JSON.parse(raw) as ConversationState;
    // Unterbrochene Vorgänge sind nach einem Neustart nicht mehr unterwegs
    return {
      ...state,
      ending: false,
      messages: state.messages.map((m) =>
        m.kind === "user" && m.status === "sending"
          ? { ...m, status: "failed", error: "Unterbrochen. Bitte erneut senden." }
          : m.kind === "partner" && m.translation.status === "loading"
            ? { ...m, translation: { status: "idle" } }
            : m,
      ),
    };
  } catch {
    return null; // Speicher nicht verfügbar oder beschädigt: einfach neu beginnen
  }
}

export function clearSavedConversation(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignorieren
  }
}

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unerwarteter Fehler. Versuch es noch einmal.";
}

export function useConversation(api: Api, start: StartSessionResponse | ConversationState) {
  const [state, dispatch] = useReducer(
    reducer,
    start,
    (s) => ("session_id" in s ? initialState(s) : s),
  );

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Speicher voll oder gesperrt (privater Modus): Gespräch läuft trotzdem weiter
    }
  }, [state]);

  const sessionId = state.session.id;

  const send = useCallback(
    async (text: string, localId: string = crypto.randomUUID()) => {
      dispatch({ type: "userSent", localId, text });
      try {
        const result = await api.takeTurn(sessionId, text);
        dispatch({
          type: "turnSucceeded",
          localId,
          reply: result.reply,
          replyId: result.reply_message_id,
          corrections: result.corrections,
        });
      } catch (error) {
        dispatch({ type: "turnFailed", localId, message: errorMessage(error) });
      }
    },
    [api, sessionId],
  );

  const translate = useCallback(
    async (messageId: string) => {
      dispatch({ type: "translationRequested", messageId });
      try {
        const result = await api.translate(sessionId, messageId);
        dispatch({ type: "translationLoaded", messageId, result });
      } catch (error) {
        dispatch({ type: "translationFailed", messageId, message: errorMessage(error) });
      }
    },
    [api, sessionId],
  );

  const toggleTranslation = useCallback(
    (messageId: string) => dispatch({ type: "translationToggled", messageId }),
    [],
  );

  const end = useCallback(async () => {
    dispatch({ type: "endRequested" });
    try {
      dispatch({ type: "endSucceeded", summary: await api.endSession(sessionId) });
    } catch (error) {
      dispatch({ type: "endFailed", message: errorMessage(error) });
    }
  }, [api, sessionId]);

  return { state, send, translate, toggleTranslation, end };
}
