# API tokens and MCP

API tokens let scripts and AI agents use yt-dlp-z without the admin password. yt-dlp-z
also has a built-in [MCP](https://modelcontextprotocol.io) server at `/mcp`, so agents
such as Claude Code can use it directly.

## Create a token

Go to **Settings → API tokens**, name the token, choose its access and select **Create
token**. It's shown once, so copy it then. yt-dlp-z stores only a hash of it.

- **Full access:** everything the web app can do, including deleting downloaded files,
  except create, list or revoke tokens. Agents and the MCP server need this.
- **Send links only:** list presets, check a link and download it with a preset. Nothing
  else: no queue, settings, files, MCP or live updates. Use it for tokens kept in less
  trusted places, such as a browser extension or a phone shortcut.

Revoking a token takes effect immediately. Changing the admin password does not revoke
tokens.

Tokens are sent with every request, so use HTTPS when they travel over a network you
don't trust.

## Connect an agent

For Claude Code, run this once on the machine it runs on. Settings shows the same command
with your address and token filled in:

```bash
claude mcp add --transport http yt-dlp-z https://your-server/mcp \
  --header "Authorization: Bearer YOUR_TOKEN"
```

Start a new Claude Code session to load the tools, and check the connection with
`claude mcp list`. To disconnect, run `claude mcp remove yt-dlp-z` and revoke the token.
The command saves the token in Claude Code's config file, in plain text.

Other clients need the same two things: the URL, using the streamable HTTP transport,
and the `Authorization` header.

With `YTDLPZ_AUTH_MODE=none` no token is needed. A reverse proxy that handles sign-in
must let `/mcp` through with the header intact.

## Add the skill

The optional `ytdlpz` skill teaches Claude Code when and how to use these tools: which
filter "subscribe to their livestreams" means, what to confirm first, how to debug a
failed download, and how to set up the connection. Install it once, for all your projects:

```bash
git clone --depth 1 https://github.com/ZXY101/yt-dlp-z.git /tmp/yt-dlp-z
mkdir -p ~/.claude/skills
cp -r /tmp/yt-dlp-z/skills/ytdlpz ~/.claude/skills/
rm -rf /tmp/yt-dlp-z
```

If you keep a checkout, link the folder instead, so it updates when you pull:
`ln -s "$PWD/skills/ytdlpz" ~/.claude/skills/ytdlpz`. Start a new session afterwards.

## Use it

Ask for what you want in plain language. For example:

- "Download this video with my Audio preset: <link>"
- "Record this stream when it starts: <link>"
- "Watch this channel and grab its 5 newest uploads."
- "Subscribe to this channel's livestreams: <link>"
- "Stop that download."
- "What failed overnight? Show me the log and retry it."
- "Only allow 2 downloads at the same time."
- "Turn on nightly yt-dlp builds."

Clients can ask before each tool runs. It's worth keeping that on for `remove_download`,
the only tool that can delete files.

## Tools

| Tool                                                            | What it does                                                  |
| --------------------------------------------------------------- | ------------------------------------------------------------- |
| `check_link`                                                    | What a link points at, without downloading                    |
| `start_download`                                                | Download a link, or record a live or upcoming one             |
| `list_downloads`, `get_download`                                | Status, settings and logs                                     |
| `cancel_download`, `retry_download`                             | Stop or rerun a download                                      |
| `rebuild_chat_overlay`                                          | Rebuild a download's live chat overlay from its saved chat    |
| `remove_download`                                               | Remove from history, optionally deleting its files            |
| `list_presets`, `save_preset`                                   | Read, change or create presets                                |
| `list_subscriptions`, `add_subscription`, `update_subscription` | Read, add or change subscriptions, including what they take   |
| `list_subscription_videos`, `check_subscription`                | Why an upload was or wasn't downloaded; look for new ones now |
| `get_settings`, `update_settings`                               | General, notifications, proxies, yt-dlp, PO tokens            |
| `list_cookies`, `get_system_status`                             | Cookies file names, yt-dlp version, ffmpeg and Deno           |
| `update_ytdlp`                                                  | Install the newest yt-dlp                                     |

`start_download` checks the link first and uses the same default presets as the web app.
It refuses a playlist or channel link unless `whole_playlist` is set.

Some things stay in the web app: deleting presets and subscriptions, uploading cookies,
managing the proxy pool, and any secret, such as the ntfy token.

## Use the REST API

Tokens also work on the REST API. Its schema is at `/docs`:

```bash
curl -H "Authorization: Bearer $YTDLPZ_TOKEN" https://your-server/api/jobs
```

### Send a link

`POST /api/jobs/send` downloads a link with a preset, or records it if it's a live or
upcoming stream. The server checks the link and applies the preset as the download form
does, so a client only sends the link. It's the only way a send-only token can start a
download.

```bash
curl -H "Authorization: Bearer $YTDLPZ_TOKEN" -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/watch/123"}' https://your-server/api/jobs/send
```

| Field            | Meaning                                                                                                                    |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `url`            | The link.                                                                                                                  |
| `preset_id`      | A preset's id from `GET /api/presets`. Empty: the default for that kind.                                                   |
| `whole_playlist` | Required for a playlist or channel. For a video opened from a playlist, downloads the playlist instead of the video alone. |

The response holds the new download (`job`) and the name of the preset used (`preset`).

## Troubleshooting

- **401 from `/mcp`:** the token is wrong or revoked, or a proxy dropped the header. A
  browser sign-in isn't enough here: `/mcp` only accepts tokens.
- **401 from `/api/tokens` with a token:** expected. Manage tokens in the web app.
- **401 from `/mcp` or 403 "This token can only send links":** the token is send-only.
  Create a full-access token for agents and scripts that need more.
- **Tools don't appear:** start a new session after adding the server.
- **"Set whole_playlist":** the link is a playlist or channel. Ask for all of it, or use
  a link to one video.
