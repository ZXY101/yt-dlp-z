# Connect Claude Code to yt-dlp-z

The user runs these steps themselves. Ask them not to paste the token into the chat, because
conversations are stored.

## Steps

1. **Check the version.** yt-dlp-z must be a version with **Settings → API tokens**. If that
   section is missing, update the server first.
2. **Create a token.** In the web app, go to **Settings → API tokens**, enter a name such as
   "Claude Code" and select **Create token**. It's shown once.
3. **Add the server.** The page shows this command with the details filled in. Run it in a
   terminal on the machine where Claude Code runs:

   ```bash
   claude mcp add --transport http yt-dlp-z https://your-server/mcp \
     --header "Authorization: Bearer YOUR_TOKEN"
   ```

   If Claude Code runs on the same machine as yt-dlp-z, use `http://localhost:PORT/mcp`, so the
   token doesn't cross the network. Otherwise use HTTPS or a private network such as Tailscale.

4. **Start a new session.** Tools load when a session starts.
5. **Test it.** Ask "what's downloading?". The answer should come from `list_downloads`.

Other MCP clients need the same URL, the streamable HTTP transport and the same header.

## When it doesn't connect

Have the user run `claude mcp list` to see the server's status. Don't run `claude mcp get`, or
read Claude's config file, in a way that prints the header, because that exposes the token.

| Symptom                                                  | Cause and fix                                                                                                                      |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Tools are missing, and the server isn't listed           | Not added. Do step 3.                                                                                                              |
| Tools are missing, and the server is listed as connected | Added during this session. Start a new one.                                                                                        |
| 401                                                      | Wrong or revoked token, or a proxy dropped the header. Create a new token, then run `claude mcp remove yt-dlp-z` and add it again. |
| 404, or the web app's page, from `/mcp`                  | The server is too old, or the address is wrong. Update it or fix the address.                                                      |
| Connection refused or a timeout                          | The server is down, or the port or address is wrong. Check its health at `/api/health`.                                            |
| Works locally, but 401 or a login page through a proxy   | The proxy must pass `/mcp` with the `Authorization` header and skip its own sign-in.                                               |

If `/api/health` answers but `/mcp` returns 401 without a token, the endpoint itself is fine.
Only the token or header is wrong.

## Rotate a token

Create a new token, run `claude mcp remove yt-dlp-z`, add the server with the new token, then
select **Revoke** on the old one. Resetting the admin password doesn't revoke tokens.
