# Proxies

The proxy pool sends downloads out through HTTP or SOCKS proxies instead of
your server's own address. It's optional; without proxies everything connects
directly.

## Adding proxies

Settings → **Proxies** → **Add a proxy**: a name ("VPN Amsterdam") and an
address. Supported:

`http://`, `https://`, `socks4://`, `socks4a://`, `socks5://`, `socks5h://`,
with `user:password@` when needed, e.g. `socks5h://user:pass@10.0.0.5:1080`.

Passwords are stored in the database but never shown again (the address comes
back as `user:****@…`). Leave the address empty when editing to keep it.

**Test** opens a page through the proxy using yt-dlp's own networking, shows
the IP address sites see (from Cloudflare's `/cdn-cgi/trace`), then checks that
YouTube answers.

## Using the pool

A [preset](presets.md) or a single download chooses its **Proxy** mode:

| Mode                       | Behaviour                                                            |
| -------------------------- | -------------------------------------------------------------------- |
| **Off**                    | Direct connection (default)                                          |
| **Next proxy in turn**     | Round-robin over the free proxies                                    |
| **Random proxy**           | A random free proxy                                                  |
| **Same proxy per channel** | Each subscription keeps the same proxy; one-off downloads take turns |

- The proxy is chosen when a download starts and **kept until it ends**
  (switching mid-download breaks live recordings).
- If yt-dlp fails with YouTube's "confirm you're not a bot", HTTP 429 or a
  proxy connection error, that proxy **cools down for 30 minutes** and the
  download tries the next one (up to 3 times). Recordings aren't retried, but the
  proxy still cools down. A successful **Test** ends a cooldown.
- A download that should use the pool **never falls back to a direct
  connection**: with no free proxy it fails and can be retried. That way your
  server's address is never used by accident.
- Downloads with cookies connect directly unless **Send downloads with cookies
  through proxies** is on: one account seen from many IP addresses can get
  flagged, and the cookies identify it anyway.
- Channel checks (feeds, link checks) don't use the pool yet.

Errors shown in the app and logs have proxy passwords masked.

## VPN exits with gluetun

YouTube often asks VPN and data-centre addresses to sign in, so VPN proxies tend
to work better for other sites than for YouTube. If you still want several exit
IPs, run one [gluetun](https://github.com/qdm12/gluetun) container per VPN
server with its HTTP proxy on, on the same Docker network as yt-dlp-z:

```yaml
services:
  vpn-1:
    image: qmcgaw/gluetun
    cap_add: [NET_ADMIN]
    devices: [/dev/net/tun:/dev/net/tun]
    environment:
      VPN_SERVICE_PROVIDER: your-provider
      SERVER_COUNTRIES: Netherlands
      HTTPPROXY: "on"
      # plus your provider's credentials
  vpn-2:
    # the same, another country or server
```

Then add `http://vpn-1:8888` and `http://vpn-2:8888` as proxies. yt-dlp-z itself
never needs `NET_ADMIN` or a VPN of its own.

If you use [PO tokens](ytdlp.md#po-tokens), the provider makes tokens through
the job's proxy, so it must reach the proxies by the same addresses.
