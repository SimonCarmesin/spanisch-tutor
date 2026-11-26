import { describe, expect, it } from "vitest";
import type { StartSessionResponse } from "../api/client";
import { initialState, isBusy, reducer, sentTurns, type UserMessage } from "./state";

const started: StartSessionResponse = {
  session_id: "s1",
  scenario: { id: "frei", title: "Freies Gespräch", description: "…" },
  cefr_level: "A2",
  opening: "¡Hola! ¿Qué tal?",
  opening_message_id: "m0",
  max_turns: 60,
};

const correction = {
  original: "Ayer yo voy",
  corrected: "Ayer fui",
  category: "preterito_indefinido" as const,
  explanation: "Abgeschlossene Handlung. Deshalb „fui“.",
};

describe("Gesprächszustand", () => {
  it("beginnt mit der Eröffnung der Gegenseite", () => {
    const state = initialState(started);
    expect(state.messages).toEqual([
      { kind: "partner", id: "m0", text: "¡Hola! ¿Qué tal?", translation: { status: "idle" } },
    ]);
    expect(state.session.maxTurns).toBe(60);
  });

  it("zeigt den eigenen Beitrag sofort und hängt Antwort und Korrekturen an", () => {
    let state = reducer(initialState(started), { type: "userSent", localId: "u1", text: "Ayer yo voy" });
    expect(isBusy(state)).toBe(true);

    state = reducer(state, {
      type: "turnSucceeded",
      localId: "u1",
      reply: "¿Y qué compraste?",
      replyId: "m2",
      corrections: [correction],
    });

    expect(isBusy(state)).toBe(false);
    expect(sentTurns(state)).toBe(1);
    const [, user, reply] = state.messages;
    expect(user).toMatchObject({ kind: "user", status: "sent", corrections: [correction] });
    expect(reply).toMatchObject({ kind: "partner", id: "m2", text: "¿Y qué compraste?" });
  });

  it("behält den Text bei einem Fehler und sendet ihn erneut, ohne ihn zu verdoppeln", () => {
    let state = reducer(initialState(started), { type: "userSent", localId: "u1", text: "Hola" });
    state = reducer(state, { type: "turnFailed", localId: "u1", message: "Keine Verbindung" });
    expect(state.messages[1]).toMatchObject({ status: "failed", text: "Hola", error: "Keine Verbindung" });
    expect(sentTurns(state)).toBe(0);

    state = reducer(state, { type: "userSent", localId: "u1", text: "Hola" });

    expect(state.messages).toHaveLength(2); // derselbe Beitrag, kein Duplikat
    expect((state.messages[1] as UserMessage).status).toBe("sending");
    expect((state.messages[1] as UserMessage).error).toBeUndefined();
  });

  it("lädt eine Übersetzung einmal und blendet sie danach nur noch um", () => {
    let state = reducer(initialState(started), { type: "translationRequested", messageId: "m0" });
    expect(state.messages[0]).toMatchObject({ translation: { status: "loading" } });

    state = reducer(state, {
      type: "translationLoaded",
      messageId: "m0",
      result: { translation: "Hallo! Wie geht's?", keywords: [], cached: false },
    });
    expect(state.messages[0]).toMatchObject({ translation: { status: "done", visible: true } });

    state = reducer(state, { type: "translationToggled", messageId: "m0" });
    expect(state.messages[0]).toMatchObject({ translation: { status: "done", visible: false } });
  });

  it("sperrt neue Beiträge, solange das Gespräch beendet wird", () => {
    const state = reducer(initialState(started), { type: "endRequested" });
    expect(isBusy(state)).toBe(true);
    const failed = reducer(state, { type: "endFailed", message: "Fehler" });
    expect(isBusy(failed)).toBe(false);
    expect(failed.error).toBe("Fehler");
  });
});
