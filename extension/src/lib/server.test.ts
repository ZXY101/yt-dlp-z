import { afterEach, describe, expect, it, vi } from "vitest";
import { getHealth, getPresets, sendLink } from "./server.ts";
import type { Connection } from "./settings.ts";

const connection: Connection = {
  address: "http://nas.local:9742",
  token: "fake-token",
  headers: [{ name: "X-Proxy-Key", value: "fake-key" }],
};

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function answer(response: Response | Error) {
  const fetchMock = vi.fn<() => Promise<Response>>(() =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("requests", () => {
  it("send the token, custom headers and JSON body", async () => {
    const fetchMock = answer(json(201, { job: { id: 1, title: "A", kind: "download" } }));
    await sendLink(connection, { url: "https://example.org/v", presetId: 3, wholePlaylist: false });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const headers = init.headers as Headers;
    expect(url).toBe("http://nas.local:9742/api/jobs/send");
    expect(headers.get("Authorization")).toBe("Bearer fake-token");
    expect(headers.get("X-Proxy-Key")).toBe("fake-key");
    expect(JSON.parse(init.body as string)).toEqual({
      url: "https://example.org/v",
      preset_id: 3,
      whole_playlist: false,
    });
  });

  it("leave Authorization out without a token", async () => {
    const fetchMock = answer(json(200, []));
    await getPresets({ ...connection, token: "" });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect((init.headers as Headers).has("Authorization")).toBe(false);
  });
});

describe("problems", () => {
  it.each([
    [json(401, { detail: "Not authenticated" }), "bad-token"],
    [json(403, { detail: "This token can only send links" }), "send-only"],
    [json(404, { detail: "Not Found" }), "too-old"],
    [json(500, { detail: "boom" }), "server-error"],
    [
      new Response("<html>login</html>", { headers: { "Content-Type": "text/html" } }),
      "login-page",
    ],
  ])("are named from the answer (%#)", async (response, problem) => {
    answer(response);
    await expect(getPresets(connection)).rejects.toMatchObject({ problem });
  });

  it("ask for a token when there is none", async () => {
    answer(json(401, { detail: "Not authenticated" }));
    await expect(getPresets({ ...connection, token: "" })).rejects.toMatchObject({
      problem: "needs-token",
    });
  });

  it("pass the server's reason for a refused link", async () => {
    answer(json(422, { detail: "This is a playlist with 12 videos." }));
    await expect(
      sendLink(connection, { url: "https://example.org/p", presetId: null, wholePlaylist: false }),
    ).rejects.toMatchObject({ problem: "rejected", message: "This is a playlist with 12 videos." });
  });

  it("join validation errors", async () => {
    answer(json(422, { detail: [{ msg: "bad url" }, { msg: "bad preset" }] }));
    await expect(getPresets(connection)).rejects.toMatchObject({ message: "bad url; bad preset" });
  });

  it("call a network error unreachable", async () => {
    answer(new TypeError("Failed to fetch"));
    await expect(getPresets(connection)).rejects.toMatchObject({ problem: "unreachable" });
  });

  it("call a timeout a timeout", async () => {
    answer(new DOMException("timed out", "TimeoutError"));
    await expect(getPresets(connection)).rejects.toMatchObject({ problem: "timeout" });
  });
});

describe("getHealth", () => {
  it("accepts a new enough server", async () => {
    answer(json(200, { status: "ok", version: "0.1.6" }));
    await expect(getHealth(connection)).resolves.toMatchObject({ version: "0.1.6" });
  });

  it("names the version to update to", async () => {
    answer(json(200, { status: "ok", version: "0.1.5" }));
    await expect(getHealth(connection)).rejects.toMatchObject({
      problem: "too-old",
      message: expect.stringContaining("0.1.6"),
    });
  });
});
