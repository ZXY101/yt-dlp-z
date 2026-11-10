import { type Route, json, noContent } from "@/test/fake-http";

export const FAKE_TOKEN = "ytz_fake-token-for-tests";

export const tokenRoutes: Route[] = [
  {
    method: "GET",
    path: /^\/api\/tokens$/,
    handle: (server) => json(server.apiTokens),
  },
  {
    method: "POST",
    path: /^\/api\/tokens$/,
    handle: (server, { body }) => {
      const token = {
        id: server.apiTokens.length + 1,
        name: String(body.name),
        scope: body.scope === "send" ? ("send" as const) : ("full" as const),
        created_at: "2026-11-04T10:00:00Z",
        last_used_at: null,
      };
      server.apiTokens.push(token);
      return json({ ...token, token: FAKE_TOKEN }, 201);
    },
  },
  {
    method: "DELETE",
    path: /^\/api\/tokens\/(\d+)$/,
    handle: (server, { params }) => {
      server.apiTokens = server.apiTokens.filter((token) => token.id !== Number(params[0]));
      return noContent();
    },
  },
];
