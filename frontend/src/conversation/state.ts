/**
 * Zustand eines Gesprächs als reine Funktion (Reducer): ohne React, ohne Netz, leicht testbar.
 * Jede Nachricht trägt ihren Zustand ausdrücklich. Ein fehlgeschlagener Beitrag bleibt mit
 * seinem Text stehen und kann erneut gesendet werden (FR-21: Gesagtes geht nicht verloren).
 */
import type { CefrLevel, Correction, StartSessionResponse, Summary, TranslationResponse } from "../api/client";

export type TranslationState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; text: string; keywords: TranslationResponse["keywords"]; visible: boolean }
  | { status: "error"; message: string };

export interface PartnerMessage {
  kind: "partner";
  id: string; // ID aus dem Backend, nötig für die Übersetzung
  text: string;
  translation: TranslationState;
}

export interface UserMessage {
  kind: "user";
  localId: string; // eigene ID, denn das Backend vergibt erst nach Erfolg eine
  text: string;
  status: "sending" | "sent" | "failed";
  error?: string;
  corrections: Correction[];
}

export type ChatMessage = PartnerMessage | UserMessage;

export interface SessionInfo {
  id: string;
  scenarioId: string;
  scenarioTitle: string;
  level: CefrLevel;
  maxTurns: number;
}

export interface ConversationState {
  session: SessionInfo;
  messages: ChatMessage[];
  ending: boolean;
  summary: Summary | null;
  error: string | null; // Fehler, der keine einzelne Nachricht betrifft (zum Beispiel beim Beenden)
}

export type Action =
  | { type: "userSent"; localId: string; text: string }
  | { type: "turnSucceeded"; localId: string; reply: string; replyId: string; corrections: Correction[] }
  | { type: "turnFailed"; localId: string; message: string }
  | { type: "translationRequested"; messageId: string }
  | { type: "translationLoaded"; messageId: string; result: TranslationResponse }
  | { type: "translationFailed"; messageId: string; message: string }
  | { type: "translationToggled"; messageId: string }
  | { type: "endRequested" }
  | { type: "endSucceeded"; summary: Summary }
  | { type: "endFailed"; message: string };

export function initialState(started: StartSessionResponse): ConversationState {
  return {
    session: {
      id: started.session_id,
      scenarioId: started.scenario.id,
      scenarioTitle: started.scenario.title,
      level: started.cefr_level,
      maxTurns: started.max_turns,
    },
    messages: [
      { kind: "partner", id: started.opening_message_id, text: started.opening, translation: { status: "idle" } },
    ],
    ending: false,
    summary: null,
    error: null,
  };
}

function updatePartner(
  state: ConversationState,
  messageId: string,
  update: (m: PartnerMessage) => PartnerMessage,
): ConversationState {
  return {
    ...state,
    messages: state.messages.map((m) => (m.kind === "partner" && m.id === messageId ? update(m) : m)),
  };
}

function updateUser(
  state: ConversationState,
  localId: string,
  update: (m: UserMessage) => UserMessage,
): ConversationState {
  return {
    ...state,
    messages: state.messages.map((m) => (m.kind === "user" && m.localId === localId ? update(m) : m)),
  };
}

export function reducer(state: ConversationState, action: Action): ConversationState {
  switch (action.type) {
    case "userSent": {
      const exists = state.messages.some((m) => m.kind === "user" && m.localId === action.localId);
      if (exists) {
        // Erneuter Versuch: derselbe Beitrag geht wieder auf "senden"
        return updateUser(state, action.localId, (m) => ({ ...m, status: "sending", error: undefined }));
      }
      const message: UserMessage = {
        kind: "user",
        localId: action.localId,
        text: action.text,
        status: "sending",
        corrections: [],
      };
      return { ...state, error: null, messages: [...state.messages, message] };
    }
    case "turnSucceeded": {
      const updated = updateUser(state, action.localId, (m) => ({
        ...m,
        status: "sent",
        error: undefined,
        corrections: action.corrections,
      }));
      const reply: PartnerMessage = {
        kind: "partner",
        id: action.replyId,
        text: action.reply,
        translation: { status: "idle" },
      };
      return { ...updated, messages: [...updated.messages, reply] };
    }
    case "turnFailed":
      return updateUser(state, action.localId, (m) => ({ ...m, status: "failed", error: action.message }));
    case "translationRequested":
      return updatePartner(state, action.messageId, (m) => ({ ...m, translation: { status: "loading" } }));
    case "translationLoaded":
      return updatePartner(state, action.messageId, (m) => ({
        ...m,
        translation: {
          status: "done",
          text: action.result.translation,
          keywords: action.result.keywords,
          visible: true,
        },
      }));
    case "translationFailed":
      return updatePartner(state, action.messageId, (m) => ({
        ...m,
        translation: { status: "error", message: action.message },
      }));
    case "translationToggled":
      // Bereits geladen: nur ein- und ausblenden, kein neuer Aufruf
      return updatePartner(state, action.messageId, (m) =>
        m.translation.status === "done"
          ? { ...m, translation: { ...m.translation, visible: !m.translation.visible } }
          : m,
      );
    case "endRequested":
      return { ...state, ending: true, error: null };
    case "endSucceeded":
      return { ...state, ending: false, summary: action.summary };
    case "endFailed":
      return { ...state, ending: false, error: action.message };
  }
}

/** Zahl der erfolgreich gesendeten eigenen Beiträge (für die Fortschrittsanzeige). */
export function sentTurns(state: ConversationState): number {
  return state.messages.filter((m) => m.kind === "user" && m.status === "sent").length;
}

/** Solange ein Beitrag unterwegs ist, wird kein weiterer gesendet (das Backend lehnt das ab). */
export function isBusy(state: ConversationState): boolean {
  return state.ending || state.messages.some((m) => m.kind === "user" && m.status === "sending");
}
