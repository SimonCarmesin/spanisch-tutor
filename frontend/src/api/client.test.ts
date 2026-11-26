import { describe, expect, it } from "vitest";
import { ApiError, createApi } from "./client";

function fakeFetch(handler: (url: string, init: RequestInit) => Response | Promise<Response>): typeof fetch {
  return ((url: string, init: RequestInit) => Promise.resolve(handler(url, init))) as typeof fetch;
}

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("API-Client", () => {
  it("sendet das Token und den Text als JSON", async () => {
    let seen: { url: string; init: RequestInit } | null = null;
    const api = createApi({
      token: "geheim",
      fetchImpl: fakeFetch((url, init) => {
        seen = { url, init };
        return json(200, { reply: "¡Bien!", reply_message_id: "m2", corrections: [] });
      }),
    });

    const result = await api.takeTurn("s1", "Hola");

    expect(result.reply).toBe("¡Bien!");
    expect(seen!.url).toBe("/api/v1/sessions/s1/turns");
    expect(new Headers(seen!.init.headers).get("Authorization")).toBe("Bearer geheim");
    expect(JSON.parse(seen!.init.body as string)).toEqual({ text: "Hola" });
  });

  it("übersetzt Fehlercodes des Backends in verständliche Meldungen", async () => {
    const api = createApi({
      token: "falsch",
      fetchImpl: fakeFetch(() => json(401, { code: "http_401", message: "Ungültiges oder fehlendes Token" })),
    });

    const error = await api.listScenarios().catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toContain("Einstellungen");
    expect((error as ApiError).retryable).toBe(false);
  });

  it("meldet einen Netzabbruch als wiederholbaren Fehler", async () => {
    const api = createApi({
      token: "t",
      fetchImpl: fakeFetch(() => Promise.reject(new TypeError("Failed to fetch"))),
    });

    const error = (await api.takeTurn("s1", "Hola").catch((e: unknown) => e)) as ApiError;

    expect(error.code).toBe("network");
    expect(error.retryable).toBe(true);
    expect(error.message).toContain("nicht verloren");
  });

  it("kommt mit Antworten ohne JSON zurecht (zum Beispiel vom Proxy)", async () => {
    const api = createApi({
      token: "t",
      fetchImpl: fakeFetch(() => new Response("Bad Gateway", { status: 502 })),
    });

    const error = (await api.listScenarios().catch((e: unknown) => e)) as ApiError;

    expect(error.status).toBe(502);
    expect(error.code).toBe("http_502");
  });
});
