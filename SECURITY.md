# Security policy

## Supported versions

Only the latest release gets security fixes.

## Reporting a vulnerability

Please **don't open a public issue**. Report it privately through GitHub:
[Security → Report a vulnerability](https://github.com/ZXY101/yt-dlp-z/security/advisories/new).

Include what's affected, how to reproduce it and what an attacker could do.
You'll get an answer within a week. Once a fix is released, the advisory is
published with credit to you, unless you'd rather stay anonymous.

## Scope

In scope: yt-dlp-z itself, e.g. authentication bypass, path traversal out of
the download folders, running commands through yt-dlp options, leaking cookies,
tokens or passwords through the API or logs.

Out of scope: bugs in yt-dlp, FFmpeg or Deno themselves (report them upstream),
and setups with `YTDLPZ_AUTH_MODE=none` or `YTDLPZ_ALLOW_UNSAFE_OPTIONS=true`
exposed to untrusted users, which the docs warn against.

## Hardening tips

- Set `YTDLPZ_ADMIN_PASSWORD` before the first start if others can reach the server.
- Put it behind HTTPS; don't expose it to the internet without a reason.
- Keep the config folder private: `cookies/` holds sign-in sessions.
- More in [configuration → security notes](docs/configuration.md#security-notes).
