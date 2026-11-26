/**
 * Einzige Stelle, die mit dem Backend spricht. Die Typen kommen aus dem OpenAPI-Schema
 * des Backends (npm run api:types), damit Frontend und Backend nicht auseinanderlaufen.
 */
import type { components } from "./schema";

type Schemas = components["schemas"];
export type Scenario = Schemas["ScenarioOut"];
export type CefrLevel = Schemas["CefrLevel"];
export type StartSessionResponse = Schemas["StartSessionResponse"];
export type TurnResponse = Schemas["TurnResponse"];
export type Correction = Schemas["CorrectionOut"];
export type Summary = Schemas["SummaryResponse"];
export type TranslationResponse = Schemas["TranslationResponse"];
export type Profile = Schemas["ProfileOut"];

/** Ein Fehler mit stabilem Code (vom Backend oder "network"/"timeout") und deutscher Meldung. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }

  /** Lohnt sich ein erneuter Versuch? Bei Netz- und Modellproblemen ja, bei Eingabefehlern nicht. */
  get retryable(): boolean {
    return ["network", "timeout", "llm_unavailable", "llm_rate_limited", "llm_invalid_output"].includes(
      this.code,
    );
  }
}

const MESSAGES: Record<string, string> = {
  network: "Keine Verbindung. Dein Text ist nicht verloren, versuch es gleich noch einmal.",
  timeout: "Die Antwort dauert zu lange. Versuch es noch einmal.",
  http_401: "Das Token fehlt oder ist falsch. Trag es in den Einstellungen ein.",
  llm_unavailable: "Der Tutor ist gerade nicht erreichbar. Versuch es gleich noch einmal.",
  llm_rate_limited: "Der Tutor ist gerade ausgelastet. Warte kurz und versuch es noch einmal.",
  llm_invalid_output: "Der Tutor hat sich verhaspelt. Versuch es noch einmal.",
  turn_limit_reached: "Das Gespräch hat die maximale Länge erreicht. Beende es, um die Auswertung zu sehen.",
  session_closed: "Dieses Gespräch ist schon beendet.",
};

// Modellaufrufe brauchen einige Sekunden, inklusive Wiederholungsversuch auch mal länger
const TIMEOUT_MS = 45_000;

export interface ApiOptions {
  token: string;
  /** Für Tests ersetzbar */
  fetchImpl?: typeof fetch;
}

async function request<T>(
  options: ApiOptions,
  method: "GET" | "POST" | "PATCH",
  path: string,
  body?: unknown,
): Promise<T> {
  const doFetch = options.fetchImpl ?? fetch;
  let response: Response;
  try {
    response = await doFetch(path, {
      method,
      headers: {
        Authorization: `Bearer ${options.token}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    const code = timedOut ? "timeout" : "network";
    throw new ApiError(0, code, MESSAGES[code] ?? "Fehler");
  }

  if (!response.ok) {
    let code = `http_${response.status}`;
    let message = `Fehler ${response.status}`;
    try {
      const data = (await response.json()) as { code?: string; message?: string };
      code = data.code ?? code;
      message = data.message ?? message;
    } catch {
      // Antwort ohne JSON (zum Beispiel vom Proxy): Statuscode reicht
    }
    throw new ApiError(response.status, code, MESSAGES[code] ?? message);
  }
  return (await response.json()) as T;
}

export function createApi(options: ApiOptions) {
  return {
    listScenarios: () => request<Scenario[]>(options, "GET", "/api/v1/scenarios"),
    startSession: (scenario: string, cefrLevel?: CefrLevel) =>
      request<StartSessionResponse>(options, "POST", "/api/v1/sessions", {
        scenario,
        ...(cefrLevel ? { cefr_level: cefrLevel } : {}),
      }),
    takeTurn: (sessionId: string, text: string) =>
      request<TurnResponse>(options, "POST", `/api/v1/sessions/${sessionId}/turns`, { text }),
    endSession: (sessionId: string) =>
      request<Summary>(options, "POST", `/api/v1/sessions/${sessionId}/end`),
    translate: (sessionId: string, messageId: string) =>
      request<TranslationResponse>(
        options,
        "POST",
        `/api/v1/sessions/${sessionId}/messages/${messageId}/translation`,
      ),
    getProfile: () => request<Profile>(options, "GET", "/api/v1/profile"),
    updateProfile: (cefrLevel: CefrLevel) =>
      request<Profile>(options, "PATCH", "/api/v1/profile", { cefr_level: cefrLevel }),
  };
}

export type Api = ReturnType<typeof createApi>;
